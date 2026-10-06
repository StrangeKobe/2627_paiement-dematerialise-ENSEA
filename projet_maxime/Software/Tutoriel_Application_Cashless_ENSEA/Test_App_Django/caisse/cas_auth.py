"""CAS 3 validation and explicit local identity resolution."""

from urllib.parse import urlsplit
from uuid import uuid4
from xml.etree import ElementTree

from cas import CASClientV3
import requests
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db import IntegrityError, OperationalError, transaction
from django.urls import reverse

from .models import CASIdentity, ProfilUtilisateur


def secure_url(value):
    try:
        url = urlsplit(value)
        return bool(
            url.scheme == "https" and url.hostname and url.port != 0
            and not url.username and not url.password and not url.query and not url.fragment
        )
    except ValueError:
        return False


def cas_ready():
    """An incomplete configuration leaves the existing local login available."""
    return bool(
        settings.CAS_ENABLED
        and settings.CAS_PROTOCOL_VERSION == "3"
        and secure_url(settings.CAS_SERVER_URL)
        and secure_url(settings.CAS_CALLBACK_URL)
        and urlsplit(settings.CAS_CALLBACK_URL).path == reverse("cas_callback")
        and settings.CAS_ID_ATTRIBUTE
        and settings.CAS_ELIGIBILITY_ATTRIBUTE
        and settings.CAS_ELIGIBLE_VALUES
    )


def issuer_url():
    return settings.CAS_SERVER_URL.rstrip("/") + "/"


class ValidationSession(requests.Session):
    """Bound validation requests; never follow a redirect carrying a ticket."""

    def request(self, method, url, **kwargs):
        kwargs.update(timeout=(5, 10), allow_redirects=False, verify=True)
        response = super().request(method, url, **kwargs)
        if response.status_code != 200:
            response.close()
            raise requests.RequestException("CAS validation failed")
        return response


def validate_ticket(ticket, service):
    with ValidationSession() as session:
        client = CASClientV3(
            server_url=issuer_url(), service_url=service, session=session,
            verify_ssl_certificate=True,
        )
        # Check the envelope before the library parses identity attributes.
        response = client.get_verification_response(ticket)
        root = ElementTree.fromstring(response)
        namespace = "{http://www.yale.edu/tp/cas}"
        if root.tag != namespace + "serviceResponse" or len(root) != 1:
            return None, {}
        success = root[0]
        if success.tag != namespace + "authenticationSuccess":
            return None, {}
        if len(success.findall(namespace + "user")) != 1:
            return None, {}
        if len(success.findall(namespace + "attributes")) > 1:
            return None, {}
        # The library's verify_response logs the full attribute payload at DEBUG.
        # Call its parser directly so personal attributes never reach that logger.
        user, attributes, _ = client.parse_response_xml(response)
        return user, attributes


def account_allowed(user):
    return user.is_active and not ProfilUtilisateur.objects.filter(user=user).exclude(
        statut_compte="ACTIF"
    ).exists()


class CASBackend(ModelBackend):
    def authenticate(self, request, cas_ticket_secret=None, cas_service=None, **kwargs):
        # 'secret' makes Django redact this credential in user_login_failed signals.
        if not cas_ready() or not cas_ticket_secret or not cas_service:
            return None
        try:
            principal, attributes = validate_ticket(cas_ticket_secret, cas_service)
        except (requests.RequestException, ElementTree.ParseError, ValueError,
                AttributeError, IndexError, TypeError):
            return None
        if not isinstance(principal, str) or not principal.strip():
            return None
        subject = (principal if settings.CAS_ID_ATTRIBUTE == "__principal__"
                   else attributes.get(settings.CAS_ID_ATTRIBUTE))
        if not isinstance(subject, str) or not subject.strip() or len(subject) > 255:
            return None
        # Do not normalize case or trim identifiers: only IT can define equivalence.
        values = attributes.get(settings.CAS_ELIGIBILITY_ATTRIBUTE)
        values = [values] if isinstance(values, str) else values
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            return None
        if not set(values).intersection(settings.CAS_ELIGIBLE_VALUES):
            return None
        try:
            with transaction.atomic():
                identity = CASIdentity.objects.select_related("user").filter(
                    issuer=issuer_url(), subject=subject,
                ).first()
                if identity:
                    user = identity.user
                    if not account_allowed(user):
                        return None
                else:
                    if not (
                        settings.CAS_AUTO_CREATE_STUDENTS
                        and settings.CAS_EXISTING_ACCOUNTS_RECONCILED
                        and settings.CAS_STUDENT_VALUE
                        and settings.CAS_STUDENT_VALUE in settings.CAS_ELIGIBLE_VALUES
                        and settings.CAS_STUDENT_VALUE in values
                    ):
                        return None
                    # Opaque local username: no name/email/username-based linking.
                    user = User.objects.create_user(username="cas_" + uuid4().hex)
                    CASIdentity.objects.create(user=user, issuer=issuer_url(), subject=subject)
                ProfilUtilisateur.objects.get_or_create(user=user)
                return user
        except (IntegrityError, OperationalError):
            # A racing login cannot leave an orphan wallet; a new login may retry.
            return None

    def get_user(self, user_id):
        user = super().get_user(user_id)
        if (user and cas_ready() and account_allowed(user)
                and CASIdentity.objects.filter(user=user, issuer=issuer_url()).exists()):
            return user
        return None
