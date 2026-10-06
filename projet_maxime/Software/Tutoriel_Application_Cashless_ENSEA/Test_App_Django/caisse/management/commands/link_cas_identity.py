from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from caisse.cas_auth import account_allowed, issuer_url, secure_url
from caisse.models import CASIdentity


class Command(BaseCommand):
    help = "Apply one IT-approved CAS subject -> existing User ID mapping; never creates a wallet."

    def add_arguments(self, parser):
        parser.add_argument("--subject", required=True)
        parser.add_argument("--user-id", required=True, type=int)

    def handle(self, *args, **options):
        subject = options["subject"]
        if not secure_url(settings.CAS_SERVER_URL) or not settings.CAS_ID_ATTRIBUTE:
            raise CommandError("Configure CAS_SERVER_URL and the IT-approved CAS_ID_ATTRIBUTE first.")
        if not subject.strip() or len(subject) > 255:
            raise CommandError("Invalid subject.")
        try:
            with transaction.atomic():
                user = User.objects.get(pk=options["user_id"])
                if not account_allowed(user):
                    raise CommandError("Inactive, disabled or anonymized accounts cannot be linked.")
                _, created = CASIdentity.objects.get_or_create(
                    issuer=issuer_url(), subject=subject, user=user,
                )
        except User.DoesNotExist as exc:
            raise CommandError("No such local user.") from exc
        except IntegrityError as exc:
            raise CommandError("Conflicting identity mapping; nothing was changed.") from exc
        self.stdout.write("Identity linked." if created else "Identical mapping already exists.")
