"""The only mocked boundary is the external CAS server's HTTP response."""

import io
import secrets
from decimal import Decimal
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from xml.etree import ElementTree as ET

import requests
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management import call_command, CommandError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Affectation, CASIdentity, CodeSecuriteAdmin, ProfilUtilisateur


CAS_SETTINGS = dict(
    CAS_ENABLED=True,
    CAS_PROTOCOL_VERSION="3",
    CAS_SERVER_URL="https://sso.example.invalid/cas/",
    CAS_CALLBACK_URL="https://wallet.example.invalid/connexion/cas/retour/",
    CAS_ID_ATTRIBUTE="immutable_id",
    CAS_ELIGIBILITY_ATTRIBUTE="affiliation",
    CAS_ELIGIBLE_VALUES=("student", "staff"),
    CAS_STUDENT_VALUE="student",
    CAS_AUTO_CREATE_STUDENTS=True,
    CAS_EXISTING_ACCOUNTS_RECONCILED=True,
)


def server_response(subject="fictional-001", affiliation="student", principal="fictional-login"):
    namespace = "{http://www.yale.edu/tp/cas}"
    root = ET.Element(namespace + "serviceResponse")
    success = ET.SubElement(root, namespace + "authenticationSuccess")
    ET.SubElement(success, namespace + "user").text = principal
    attributes = ET.SubElement(success, namespace + "attributes")
    if subject is not None:
        ET.SubElement(attributes, namespace + "immutable_id").text = subject
    if affiliation is not None:
        ET.SubElement(attributes, namespace + "affiliation").text = affiliation
    # Deliberately resembles an existing account; these fields must never link it.
    ET.SubElement(attributes, namespace + "email").text = "existing@example.invalid"
    ET.SubElement(attributes, namespace + "displayName").text = "Fictional Existing"
    response = requests.Response()
    response.status_code = 200
    response._content = ET.tostring(root)
    response._content_consumed = True
    return response


@override_settings(**CAS_SETTINGS)
class CASLoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = secrets.token_urlsafe(24)
        cls.code = f"{secrets.randbelow(1000000):06d}"
        cls.existing = User.objects.create_user(
            username="fictional-login", email="existing@example.invalid",
            first_name="Fictional", last_name="Existing", password=cls.password,
        )
        cls.profile = ProfilUtilisateur.objects.create(
            user=cls.existing, solde=Decimal("42.50"), uid_rfid="fictional-rfid",
        )
        cls.role = Affectation.objects.create(
            user=cls.existing, role="ADMIN_ECOLE", droit_exporter=True,
        )
        cls.security = CodeSecuriteAdmin.objects.create(
            user=cls.existing, code_hash=make_password(cls.code), definie_par=cls.existing,
        )

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.http_patch = patch("requests.sessions.Session.send", return_value=server_response())
        self.http = self.http_patch.start()
        self.addCleanup(self.http_patch.stop)

    def start_login(self):
        self.assertRedirects(
            self.client.get(reverse("login")), reverse("cas_login"),
            fetch_redirect_response=False,
        )
        response = self.client.get(reverse("cas_login"))
        self.assertEqual(response.status_code, 302)
        target = urlsplit(response.url)
        self.assertEqual(target.netloc, "sso.example.invalid")
        self.assertEqual(target.path, "/cas/login")
        self.service = parse_qs(target.query)["service"][0]
        return parse_qs(urlsplit(self.service).query)["state"][0]

    def finish_login(self, state):
        return self.client.get(reverse("cas_callback"), {"state": state, "ticket": "ST-fictional"})

    def cas_login(self):
        response = self.finish_login(self.start_login())
        self.assertRedirects(response, reverse("verifier_code"), fetch_redirect_response=False)
        return User.objects.get(pk=self.client.session[SESSION_KEY])

    def post_form(self, name, data=None):
        return self.client.post(reverse(name), {
            **(data or {}), "csrfmiddlewaretoken": self.client.cookies["csrftoken"].value,
        })

    def link_existing(self):
        CASIdentity.objects.create(
            issuer=CAS_SETTINGS["CAS_SERVER_URL"], subject="fictional-001", user=self.existing,
        )

    def verify_code(self):
        self.assertEqual(self.client.get(reverse("verifier_code")).status_code, 200)
        self.assertRedirects(
            self.post_form("verifier_code", {"code": self.code}), reverse("accueil")
        )

    def assert_denied_without_creation(self, response):
        self.assertEqual(response.status_code, 403)
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(ProfilUtilisateur.objects.count(), 1)

    def test_valid_ticket_creates_student_and_uses_exact_service(self):
        user = self.cas_login()
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertFalse(user.affectations.exists())
        self.assertEqual(user.profil.solde, Decimal("0"))
        self.assertEqual(user.cas_identity.subject, "fictional-001")
        self.assertEqual(user.cas_identity.issuer, CAS_SETTINGS["CAS_SERVER_URL"])
        self.assertRedirects(self.client.get(reverse("verifier_code")), reverse("accueil"))
        self.assertEqual(self.client.get(reverse("espace_ecole")).status_code, 403)
        prepared = self.http.call_args.args[0]
        url = urlsplit(prepared.url)
        self.assertEqual(url.path, "/cas/p3/serviceValidate")
        self.assertEqual(parse_qs(url.query), {"ticket": ["ST-fictional"], "service": [self.service]})
        self.assertTrue(self.http.call_args.kwargs["verify"])
        self.assertEqual(self.http.call_args.kwargs["timeout"], (5, 10))

    def test_repeat_login_preserves_one_user_and_wallet(self):
        user = self.cas_login()
        profile = user.profil
        profile.solde = Decimal("9.25")
        profile.save(update_fields=["solde"])
        second = self.cas_login()
        self.assertEqual(second.pk, user.pk)
        self.assertEqual(second.profil.pk, profile.pk)
        self.assertEqual(second.profil.solde, Decimal("9.25"))
        self.assertEqual(second.profil.secret_qr, profile.secret_qr)
        self.assertEqual(CASIdentity.objects.count(), 1)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(ProfilUtilisateur.objects.count(), 2)

    def test_approved_existing_account_preserves_balance_roles_and_codes(self):
        self.link_existing()
        before_user = User.objects.values().get(pk=self.existing.pk)
        before_profile = ProfilUtilisateur.objects.values().get(pk=self.profile.pk)
        before_role = Affectation.objects.values().get(pk=self.role.pk)
        before_code = CodeSecuriteAdmin.objects.values().get(pk=self.security.pk)
        self.assertEqual(self.cas_login().pk, self.existing.pk)
        after_user = User.objects.values().get(pk=self.existing.pk)
        before_user.pop("last_login")
        after_user.pop("last_login")
        self.assertEqual(before_user, after_user)
        self.assertEqual(before_profile, ProfilUtilisateur.objects.values().get(pk=self.profile.pk))
        self.assertEqual(before_role, Affectation.objects.values().get(pk=self.role.pk))
        self.assertEqual(before_code, CodeSecuriteAdmin.objects.values().get(pk=self.security.pk))
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(ProfilUtilisateur.objects.count(), 1)

    def test_security_code_blocks_access_and_rejects_wrong_code(self):
        self.link_existing()
        self.cas_login()
        self.assertRedirects(self.client.get(reverse("espace_ecole")), reverse("verifier_code"))
        wrong = f"{(int(self.code) + 1) % 1000000:06d}"
        self.assertContains(self.post_form("verifier_code", {"code": wrong}), "Code erroné.")
        self.assertFalse(self.client.session.get("code_verifie"))
        self.verify_code()
        self.assertEqual(self.client.get(reverse("espace_ecole")).status_code, 200)

    def test_logout_and_fresh_cas_login_require_code_again(self):
        self.link_existing()
        self.cas_login()
        self.verify_code()
        response = self.post_form("logout")
        self.assertTemplateUsed(response, "caisse/cas_logged_out.html")
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertNotIn("code_verifie", self.client.session)
        self.cas_login()
        self.assertRedirects(self.client.get(reverse("espace_ecole")), reverse("verifier_code"))

    def test_same_user_reauthentication_clears_verified_code(self):
        self.link_existing()
        self.cas_login()
        self.verify_code()
        self.cas_login()
        self.assertFalse(self.client.session.get("code_verifie"))
        self.assertRedirects(self.client.get(reverse("accueil")), reverse("verifier_code"))

    def test_rejected_ticket_creates_nothing(self):
        self.http.return_value._content = b'<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas"><cas:authenticationFailure code="INVALID_TICKET">Rejected</cas:authenticationFailure></cas:serviceResponse>'
        self.assert_denied_without_creation(self.finish_login(self.start_login()))

    def test_missing_or_ambiguous_stable_identity_creates_nothing(self):
        for subject in (None, "", "x" * 256):
            with self.subTest(subject=subject):
                self.http.return_value = server_response(subject=subject)
                self.assert_denied_without_creation(self.finish_login(self.start_login()))
        response = server_response()
        root = ET.fromstring(response.content)
        ET.SubElement(root[0][-1], "{http://www.yale.edu/tp/cas}immutable_id").text = "another-id"
        response._content = ET.tostring(root)
        self.http.return_value = response
        self.assert_denied_without_creation(self.finish_login(self.start_login()))

    def test_missing_or_ineligible_affiliation_creates_nothing(self):
        for value in (None, "", "unapproved", "staff"):
            with self.subTest(affiliation=value):
                self.http.return_value = server_response(affiliation=value)
                self.assert_denied_without_creation(self.finish_login(self.start_login()))

    def test_provisioning_requires_both_explicit_switches(self):
        for setting in ("CAS_AUTO_CREATE_STUDENTS", "CAS_EXISTING_ACCOUNTS_RECONCILED"):
            with self.subTest(setting=setting), self.settings(**{setting: False}):
                self.assert_denied_without_creation(self.finish_login(self.start_login()))
                self.assertEqual(CASIdentity.objects.count(), 0)

    def test_does_not_link_matching_username_name_or_email(self):
        with self.settings(CAS_AUTO_CREATE_STUDENTS=False):
            self.assert_denied_without_creation(self.finish_login(self.start_login()))
            self.assertEqual(CASIdentity.objects.count(), 0)

    def test_existing_mapping_works_with_provisioning_disabled(self):
        self.link_existing()
        self.http.return_value = server_response(affiliation="staff")
        with self.settings(CAS_AUTO_CREATE_STUDENTS=False, CAS_EXISTING_ACCOUNTS_RECONCILED=False):
            self.assertEqual(self.cas_login().pk, self.existing.pk)

    def test_disabled_and_anonymized_accounts_are_not_recreated(self):
        self.link_existing()
        for status in ("DESACTIVE", "ANONYMISE"):
            with self.subTest(status=status):
                self.profile.statut_compte = status
                self.profile.save(update_fields=["statut_compte"])
                self.assert_denied_without_creation(self.finish_login(self.start_login()))
        self.profile.statut_compte = "ACTIF"
        self.profile.save(update_fields=["statut_compte"])
        self.existing.is_active = False
        self.existing.save(update_fields=["is_active"])
        self.assert_denied_without_creation(self.finish_login(self.start_login()))

    def test_network_http_and_malformed_responses_fail_closed(self):
        self.http.side_effect = requests.Timeout()
        self.assert_denied_without_creation(self.finish_login(self.start_login()))
        self.http.side_effect = None
        for status, content in ((500, b"error"), (302, b"redirect"), (200, b"not XML"), (200, b"<wrong/>")):
            with self.subTest(status=status, content=content):
                response = server_response()
                response.status_code, response._content = status, content
                self.http.return_value = response
                self.assert_denied_without_creation(self.finish_login(self.start_login()))

    def test_unsolicited_expired_and_wrong_state_callbacks_do_not_contact_cas(self):
        self.assert_denied_without_creation(self.finish_login("unsolicited"))
        self.start_login()
        self.assert_denied_without_creation(self.finish_login("wrong-state"))
        self.start_login()
        self.assert_denied_without_creation(self.finish_login("état-invalide"))
        state = self.start_login()
        session = self.client.session
        pending = session["cas_pending"]
        pending["time"] = 0
        session["cas_pending"] = pending
        session.save()
        self.assert_denied_without_creation(self.finish_login(state))
        self.http.assert_not_called()

    def test_missing_duplicate_and_proxy_tickets_do_not_contact_cas(self):
        for tickets in ([], [""], ["PT-fictional"], ["ST-one", "ST-two"]):
            with self.subTest(tickets=tickets):
                state = self.start_login()
                response = self.client.get(reverse("cas_callback"), {"state": state, "ticket": tickets})
                self.assert_denied_without_creation(response)
        self.http.assert_not_called()

    def test_principal_is_used_only_when_explicitly_configured(self):
        self.http.return_value = server_response(subject=None)
        with self.settings(CAS_ID_ATTRIBUTE="__principal__"):
            user = self.cas_login()
            self.assertEqual(user.cas_identity.subject, "fictional-login")
            self.assertNotEqual(user.pk, self.existing.pk)

    def test_anonymization_keeps_link_and_blocks_recreation(self):
        self.link_existing()
        self.profile.anonymiser()
        self.assert_denied_without_creation(self.finish_login(self.start_login()))
        self.assertEqual(CASIdentity.objects.get(subject="fictional-001").user_id, self.existing.pk)

    def test_cas_session_loses_access_when_local_account_is_disabled(self):
        self.link_existing()
        self.cas_login()
        self.verify_code()
        self.profile.statut_compte = "DESACTIVE"
        self.profile.save(update_fields=["statut_compte"])
        response = self.client.get(reverse("espace_ecole"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))

    def test_callback_cannot_be_reused(self):
        state = self.start_login()
        self.assertEqual(self.finish_login(state).status_code, 302)
        self.assertEqual(self.finish_login(state).status_code, 403)
        self.assertEqual(self.http.call_count, 1)
        self.assertEqual(CASIdentity.objects.count(), 1)

    def test_next_cannot_redirect_around_security_gate_or_off_site(self):
        self.link_existing()
        state = self.start_login()
        response = self.client.get(reverse("cas_callback"), {
            "state": state, "ticket": "ST-fictional", "next": "https://evil.example.invalid/",
        })
        self.assertRedirects(response, reverse("verifier_code"))
        self.assertFalse(self.client.session.get("code_verifie"))

    def test_disabled_or_incomplete_cas_keeps_local_password_login(self):
        for config in ({"CAS_ENABLED": False}, {"CAS_SERVER_URL": ""},
                       {"CAS_ID_ATTRIBUTE": ""}, {"CAS_ELIGIBLE_VALUES": ()},
                       {"CAS_PROTOCOL_VERSION": "2"}):
            with self.subTest(config=config), self.settings(**config):
                self.client = Client(enforce_csrf_checks=True)
                self.assertTemplateUsed(self.client.get(reverse("login")), "caisse/login.html")
                response = self.post_form("login", {
                    "username": self.existing.username, "password": self.password,
                })
                self.assertRedirects(response, reverse("verifier_code"))
                self.assertEqual(self.client.session[SESSION_KEY], str(self.existing.pk))
        self.http.assert_not_called()

    def test_mapping_command_is_explicit_idempotent_and_does_not_create_wallet(self):
        target = User.objects.create_user(username="fictional-unmapped")
        for _ in range(2):
            call_command("link_cas_identity", subject="approved-subject", user_id=target.pk, stdout=io.StringIO())
        self.assertEqual(CASIdentity.objects.get(subject="approved-subject").user_id, target.pk)
        self.assertFalse(ProfilUtilisateur.objects.filter(user=target).exists())
        with self.assertRaises(CommandError):
            call_command("link_cas_identity", subject="approved-subject", user_id=self.existing.pk, stdout=io.StringIO())
        with self.assertRaises(CommandError):
            call_command("link_cas_identity", subject="different-subject", user_id=target.pk, stdout=io.StringIO())
        self.assertEqual(CASIdentity.objects.count(), 1)
