"""
Fonctions qui repondent a "que peut faire cet utilisateur ?".

Note : le superuser Django represente l'equipe technique (maintenance),
il a acces a tout pour developper et debuguer. Le role "admin ecole" est
different : il gere les comptes et les codes.
"""

from .models import Pole
from django.utils import timezone


def poles_vendables(user):
    """Les poles ou l'utilisateur a le droit de tenir la caisse."""
    if user.is_superuser or user.affectations.filter(role="ADMIN_ADE").exists():
        qs = Pole.objects.all()
    else:
        ids = user.affectations.filter(
            role__in=["VENDEUR", "ADMIN_POLE"]
        ).values_list("pole_id", flat=True)
        qs = Pole.objects.filter(id__in=ids)
    return qs.filter(est_operationnel=True)


def poles_gerables(user):
    """Les poles que l'utilisateur peut administrer."""
    if user.is_superuser or user.affectations.filter(role="ADMIN_ADE").exists():
        qs = Pole.objects.all()
    else:
        ids = user.affectations.filter(role="ADMIN_POLE").values_list("pole_id", flat=True)
        qs = Pole.objects.filter(id__in=ids)
    return qs.filter(est_operationnel=True)


def peut_vendre(user, pole):
    return poles_vendables(user).filter(pk=pole.pk).exists()


def peut_gerer(user, pole):
    """Vrai si l'utilisateur est admin (de pole ou ADE) sur ce pole, tous
    droits confondus. Sert aussi a determiner qui peut distribuer des
    droits supplementaires a un vendeur."""
    return poles_gerables(user).filter(pk=pole.pk).exists()


def est_admin_ade(user):
    return user.is_superuser or user.affectations.filter(role="ADMIN_ADE").exists()


def _a_droit_supplementaire(user, pole, champ):
    """Vrai si l'utilisateur est vendeur ou admin de pole sur ce pole
    precis avec ce droit supplementaire coche (accorde depuis la page
    Equipe). Pour un admin de pole, seul "recharger en especes" a un
    effet reel : les autres droits ne changent rien puisqu'il les a deja
    tous via peut_gerer."""
    return user.affectations.filter(
        pole=pole, role__in=["VENDEUR", "ADMIN_POLE"], **{champ: True}
    ).exists()


def peut_recharger_especes(user, pole):
    """Recharger le portefeuille de quelqu'un en especes est reserve a
    l'admin ADE par defaut ; il peut aussi accorder ce droit precisement
    a un vendeur ou un admin de pole, pole par pole."""
    if est_admin_ade(user):
        return True
    return _a_droit_supplementaire(user, pole, "droit_recharger_especes")


def peut_encaisser_adhesion_especes(user, pole):
    """Encaisser une adhesion en especes est different de recharger un
    portefeuille : un admin de pole peut deja le faire sur son propre
    pole (comme tout le reste de sa gestion), pas besoin d'etre admin
    ADE. Il peut aussi accorder ce droit precisement a un vendeur."""
    if peut_gerer(user, pole):
        return True
    return _a_droit_supplementaire(user, pole, "droit_adhesion_especes")


def peut_voir_suivi_especes(user, pole):
    """Voir les rechargements especes du pole : n'a de sens que pour
    quelqu'un qui peut lui-meme recharger en especes."""
    return peut_recharger_especes(user, pole)


def peut_gerer_produits(user, pole):
    if peut_gerer(user, pole):
        return True
    return _a_droit_supplementaire(user, pole, "droit_gerer_produits")


def peut_gerer_adhesions(user, pole):
    if peut_gerer(user, pole):
        return True
    return _a_droit_supplementaire(user, pole, "droit_adhesions")


def peut_voir_equipe(user, pole):
    """Voir l'onglet Equipe. Ne donne jamais le droit de modifier quoi que
    ce soit : voir peut_modifier_equipe pour ca."""
    if peut_gerer(user, pole):
        return True
    return _a_droit_supplementaire(user, pole, "droit_equipe")


def peut_modifier_equipe(user, pole):
    """Ajouter/retirer quelqu'un ou modifier ses droits supplementaires :
    reserve aux admins (de pole ou ADE), jamais delegable a un vendeur,
    meme s'il a le droit de voir l'onglet Equipe. Sans cette regle, un
    vendeur pourrait s'accorder (ou accorder a un autre vendeur) tous les
    droits, y compris redevenir admin."""
    return peut_gerer(user, pole)


def peut_exporter(user, pole):
    if peut_gerer(user, pole):
        return True
    return _a_droit_supplementaire(user, pole, "droit_exporter")


def peut_modifier_parametres(user, pole):
    if peut_gerer(user, pole):
        return True
    return _a_droit_supplementaire(user, pole, "droit_parametres")


def est_admin_ecole(user):
    """Le compte technique de maintenance (superuser) est traite comme
    admin ecole pour le developpement ; en usage reel, ce sera un vrai
    role attribue a une ou deux personnes (Campus Life, etc.)."""
    return user.is_superuser or user.affectations.filter(role="ADMIN_ECOLE").exists()


def annee_scolaire_courante():
    """L'annee scolaire va d'aout a aout : d'aout a decembre, c'est
    l'annee civile en cours ; de janvier a juillet, c'est encore l'annee
    civile precedente."""
    aujourdhui = timezone.localdate()
    if aujourdhui.month >= 8:
        return aujourdhui.year
    return aujourdhui.year - 1
