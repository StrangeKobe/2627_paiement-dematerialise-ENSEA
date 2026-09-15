"""
Un context processor Django s'execute automatiquement pour CHAQUE page et
ajoute des variables au contexte de tous les templates, sans avoir a les
repeter dans chaque vue. On s'en sert ici pour savoir, sur n'importe quelle
page (pas seulement l'accueil), si l'utilisateur connecte a au moins un
droit de vente ou de gestion : c'est ce qui decide si les onglets "Vendre"
et "Terminal" apparaissent dans la barre du bas.
"""

from .roles import est_admin_ecole, poles_gerables, poles_vendables


def droits_navigation(request):
    if not request.user.is_authenticated:
        return {}
    a_des_droits = (
        poles_vendables(request.user).exists()
        or poles_gerables(request.user).exists()
    )
    return {
        "a_droits_vente": a_des_droits,
        "a_droits_terminal": a_des_droits,
        "est_admin_ecole": est_admin_ecole(request.user),
    }
