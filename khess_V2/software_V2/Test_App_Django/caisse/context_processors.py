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
