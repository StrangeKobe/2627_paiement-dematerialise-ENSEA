import secrets
from decimal import Decimal

from django.contrib.auth import SESSION_KEY
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Affectation, CodeSecuriteAdmin, ProfilUtilisateur


@override_settings(CAS_ENABLED=False)
class AuthenticationBaselineTests(TestCase):
    """Exercise local authentication through the views and security middleware."""

    @classmethod
    def setUpTestData(cls):
        # Fictional identities and generated credentials, only in the test DB.
        cls.password = secrets.token_urlsafe(24)
        cls.security_code = f"{secrets.randbelow(1000000):06d}"
        cls.student = User.objects.create_user(
            username="test_student", email="student@example.invalid",
            password=cls.password,
        )
        cls.admin = User.objects.create_user(
            username="test_school_admin", email="admin@example.invalid",
            password=cls.password,
        )
        # Use the application's school role, without Django superuser bypasses.
        Affectation.objects.create(user=cls.admin, role="ADMIN_ECOLE")
        CodeSecuriteAdmin.objects.create(
            user=cls.admin, code_hash=make_password(cls.security_code),
            definie_par=cls.admin,
        )

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def post_form(self, url_name, data=None):
        return self.client.post(reverse(url_name), {
            **(data or {}),
            "csrfmiddlewaretoken": self.client.cookies["csrftoken"].value,
        })

    def login(self, user, next_url=None):
        url = reverse("login")
        self.assertEqual(self.client.get(url).status_code, 200)
        data = {"username": user.username, "password": self.password}
        if next_url is not None:
            data["next"] = next_url
        response = self.post_form("login", data)
        self.assertRedirects(
            response, next_url or reverse("verifier_code"),
            fetch_redirect_response=False,
        )
        self.assertEqual(self.client.session[SESSION_KEY], str(user.pk))

    def verify_admin_code(self):
        response = self.client.get(reverse("verifier_code"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "caisse/verifier_code.html")
        response = self.post_form("verifier_code", {"code": self.security_code})
        self.assertRedirects(response, reverse("accueil"))
        self.assertTrue(self.client.session.get("code_verifie"))

    def test_student_login_creates_profile_without_code_challenge(self):
        self.assertFalse(ProfilUtilisateur.objects.filter(user=self.student).exists())
        self.login(self.student)

        response = self.client.get(reverse("verifier_code"), follow=True)

        self.assertEqual(response.redirect_chain, [(reverse("accueil"), 302)])
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "caisse/accueil.html")
        profile = ProfilUtilisateur.objects.get(user=self.student)
        self.assertEqual(profile.solde, Decimal("0.00"))
        self.assertEqual(profile.statut_compte, "ACTIF")
        self.assertFalse(self.student.affectations.exists())
        self.assertFalse(self.client.session.get("code_verifie"))

    def test_repeat_student_login_keeps_existing_profile(self):
        self.login(self.student)
        self.assertEqual(self.client.get(reverse("accueil")).status_code, 200)
        profile = ProfilUtilisateur.objects.get(user=self.student)
        original_pk, original_qr = profile.pk, profile.secret_qr
        profile.solde = Decimal("12.50")
        profile.save(update_fields=["solde"])
        self.assertRedirects(self.post_form("logout"), reverse("login"))
        self.assertNotIn(SESSION_KEY, self.client.session)

        self.login(self.student)
        response = self.client.get(reverse("verifier_code"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProfilUtilisateur.objects.filter(user=self.student).count(), 1)
        profile.refresh_from_db()
        self.assertEqual(profile.pk, original_pk)
        self.assertEqual(profile.secret_qr, original_qr)
        self.assertEqual(profile.solde, Decimal("12.50"))

    def test_student_is_denied_school_pages(self):
        self.login(self.student)
        pages = [
            ("espace_ecole", {}), ("ecole_equipe", {}), ("ecole_codes", {}),
            ("ecole_profils", {}), ("ecole_comptes", {}),
            ("ecole_recettes", {}), ("ecole_adherents", {}),
            ("ecole_adherents_pole", {"slug": "fictional-pole"}),
        ]
        for name, kwargs in pages:
            with self.subTest(page=name):
                response = self.client.get(reverse(name, kwargs=kwargs))
                self.assertEqual(response.status_code, 403)

    def test_admin_code_challenge_rejects_wrong_code_then_allows_access(self):
        self.login(self.admin)
        self.assertRedirects(
            self.client.get(reverse("espace_ecole")), reverse("verifier_code")
        )
        wrong_code = f"{(int(self.security_code) + 1) % 1000000:06d}"

        response = self.post_form("verifier_code", {"code": wrong_code})

        self.assertContains(response, "Code erroné.")
        self.assertFalse(self.client.session.get("code_verifie"))
        self.assertRedirects(
            self.client.get(reverse("espace_ecole")), reverse("verifier_code")
        )
        self.verify_admin_code()
        self.assertEqual(self.client.get(reverse("espace_ecole")).status_code, 200)

    def test_login_next_cannot_bypass_admin_code_challenge(self):
        self.login(self.admin, next_url=reverse("espace_ecole"))

        self.assertFalse(self.client.session.get("code_verifie"))
        self.assertRedirects(
            self.client.get(reverse("espace_ecole")), reverse("verifier_code")
        )
        self.assertRedirects(
            self.client.get(reverse("accueil")), reverse("verifier_code")
        )

    def test_logout_requires_code_again_on_next_admin_login(self):
        self.login(self.admin)
        self.verify_admin_code()
        self.assertEqual(self.client.get(reverse("espace_ecole")).status_code, 200)

        self.assertRedirects(self.post_form("logout"), reverse("login"))

        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertNotIn("code_verifie", self.client.session)
        self.assertRedirects(
            self.client.get(reverse("espace_ecole")),
            f"{reverse('login')}?next={reverse('espace_ecole')}",
        )
        self.login(self.admin)
        self.assertFalse(self.client.session.get("code_verifie"))
        self.assertRedirects(
            self.client.get(reverse("espace_ecole")), reverse("verifier_code")
        )
        self.verify_admin_code()
        self.assertEqual(self.client.get(reverse("espace_ecole")).status_code, 200)
