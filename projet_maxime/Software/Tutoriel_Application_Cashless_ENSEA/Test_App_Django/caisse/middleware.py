from django.shortcuts import redirect
from django.urls import reverse

URLS_EXEMPTEES = {"verifier_code", "login", "logout"}


class VerifierCodeMiddleware:
    """Oblige toute personne ayant un code de securite a le saisir avant
    d'acceder a n'importe quelle page, quel que soit le chemin par lequel
    elle est arrivee sur l'ecran de connexion."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.session.get("code_verifie"):
            chemins_exemptes = {reverse(nom) for nom in URLS_EXEMPTEES}
            hors_perimetre = (
                request.path.startswith("/admin/")
                or request.path.startswith("/static/")
                or request.path.startswith("/media/")
            )
            if request.path not in chemins_exemptes and not hors_perimetre:
                if request.user.codes_securite.exists():
                    return redirect("verifier_code")
        return self.get_response(request)
