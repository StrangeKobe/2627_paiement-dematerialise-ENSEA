import secrets
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import CorrectionProfilForm
from .models import (
    Adhesion, Affectation, CodeSecuriteAdmin, DemandeSuppressionCompte,
    LigneTransaction, Pole, ProfilUtilisateur,
)
from .recus import envoyer_email_code, envoyer_email_suppression
from .roles import annee_scolaire_courante, est_admin_ecole


@login_required
def verifier_code(request):
    """La porte d'entree juste apres la connexion : si l'utilisateur a au
    moins un code de securite, on le lui demande avant de le laisser
    poursuivre."""
    a_des_codes = request.user.codes_securite.exists()
    if not a_des_codes or request.session.get("code_verifie"):
        return redirect("accueil")

    erreur = None
    if request.method == "POST":
        code_saisi = request.POST.get("code", "").strip()
        codes = request.user.codes_securite.all()
        if any(check_password(code_saisi, c.code_hash) for c in codes):
            request.session["code_verifie"] = True
            return redirect("accueil")
        erreur = "Code erroné."

    return render(request, "caisse/verifier_code.html", {"erreur": erreur})


def _verifier_acces(request):
    if not est_admin_ecole(request.user):
        raise PermissionDenied


@login_required
def espace_ecole(request):
    _verifier_acces(request)
    return render(request, "caisse/espace_ecole.html", {})


def _construire_groupes():
    affectations = Affectation.objects.select_related("user", "pole")
    poids_role = {"ADMIN_ECOLE": 0, "ADMIN_ADE": 1, "ADMIN_POLE": 2, "VENDEUR": 3}
    par_pole = {}
    for a in affectations:
        if a.pole:
            cle = a.pole.nom
        elif a.role == "ADMIN_ECOLE":
            cle = "École (global)"
        else:
            cle = "ADE (global)"
        par_pole.setdefault(cle, []).append(a)
    for cle in par_pole:
        par_pole[cle].sort(key=lambda a: (poids_role.get(a.role, 9), a.user.username))
    groupes = []
    if "École (global)" in par_pole:
        groupes.append(("École (global)", par_pole.pop("École (global)")))
    if "ADE (global)" in par_pole:
        groupes.append(("ADE (global)", par_pole.pop("ADE (global)")))
    for nom in sorted(par_pole):
        groupes.append((nom, par_pole[nom]))
    return groupes


@login_required
def ecole_equipe(request):
    _verifier_acces(request)
    erreur = None
    if request.method == "POST":
        if "ajouter" in request.POST:
            identifiant = request.POST.get("identifiant", "").strip()
            role = request.POST.get("role")
            pole_id = request.POST.get("pole") or None
            utilisateur = User.objects.filter(username=identifiant).first()
            if utilisateur is None:
                erreur = "Aucun compte trouvé pour cet identifiant."
            elif role not in dict(Affectation.ROLES):
                erreur = "Rôle invalide."
            elif role in ("VENDEUR", "ADMIN_POLE") and not pole_id:
                erreur = "Un vendeur ou un admin de pôle doit obligatoirement être rattaché a un pôle précis. Choisis un pôle dans la liste."
            else:
                pole = Pole.objects.filter(id=pole_id).first() if pole_id else None
                Affectation.objects.get_or_create(user=utilisateur, pole=pole, role=role)
                return redirect("ecole_equipe")
        elif "retirer" in request.POST:
            a_retirer = Affectation.objects.filter(id=request.POST.get("retirer")).first()
            if a_retirer and a_retirer.role == "ADMIN_ECOLE":
                nb_admins_ecole = Affectation.objects.filter(role="ADMIN_ECOLE").count()
                if nb_admins_ecole <= 1:
                    erreur = (
                        "Impossible de retirer ce rôle : ce serait le dernier "
                        "admin école, plus personne ne pourrait distribuer de "
                        "rôles ni de codes ensuite. Attribue d'abord ce rôle a "
                        "quelqu'un d'autre avant de retirer celui-ci."
                    )
                    return render(request, "caisse/ecole_equipe.html", {
                        "groupes": _construire_groupes(), "poles": Pole.objects.all(), "erreur": erreur,
                    })
            if a_retirer:
                a_retirer.delete()
            return redirect("ecole_equipe")
    return render(request, "caisse/ecole_equipe.html", {
        "groupes": _construire_groupes(), "poles": Pole.objects.all(), "erreur": erreur,
    })


@login_required
def ecole_codes(request):
    _verifier_acces(request)
    nouveau_code = None
    erreur = None
    if request.method == "POST":
        if "generer" in request.POST:
            identifiant = request.POST.get("identifiant", "").strip()
            pole_id = request.POST.get("pole") or None
            utilisateur = User.objects.filter(username=identifiant).first()
            if utilisateur is None:
                erreur = "Aucun compte trouvé pour cet identifiant."
            else:
                pole = Pole.objects.filter(id=pole_id).first() if pole_id else None
                nouveau_code = f"{secrets.randbelow(1000000):06d}"
                # On supprime l'ancien code puis on en cree un nouveau,
                # plutot que update_or_create : sur un role global
                # (pole=None), unique_together ne detecte pas toujours
                # deux lignes pole=NULL comme identiques (voir Partie 4.4),
                # et update_or_create risquerait de laisser l'ancien code
                # valide en plus du nouveau.
                CodeSecuriteAdmin.objects.filter(user=utilisateur, pole=pole).delete()
                objet = CodeSecuriteAdmin.objects.create(
                    user=utilisateur, pole=pole,
                    code_hash=make_password(nouveau_code), definie_par=request.user,
                )
                envoyer_email_code(objet, nouveau_code)
        elif "retirer" in request.POST:
            CodeSecuriteAdmin.objects.filter(id=request.POST.get("retirer")).delete()
            return redirect("ecole_codes")

    codes = CodeSecuriteAdmin.objects.select_related("user", "pole", "definie_par").order_by("user__username")

    # Alerte : tout role (vendeur compris) sans code associe a ce pole -
    # la fenetre de temps entre attribution d'un role et remise du code.
    privilegiees = Affectation.objects.filter(
        role__in=["VENDEUR", "ADMIN_POLE", "ADMIN_ADE", "ADMIN_ECOLE"]
    ).select_related("user", "pole")
    codes_existants = set(CodeSecuriteAdmin.objects.values_list("user_id", "pole_id"))
    a_traiter_par_cle = {}
    for a in privilegiees:
        cle = (a.user_id, a.pole_id)
        if cle in codes_existants:
            continue
        entree = a_traiter_par_cle.setdefault(cle, {"user": a.user, "pole": a.pole, "roles": []})
        entree["roles"].append(a.get_role_display())
    a_traiter = list(a_traiter_par_cle.values())

    return render(request, "caisse/ecole_codes.html", {
        "codes": codes, "poles": Pole.objects.all(), "nouveau_code": nouveau_code,
        "erreur": erreur, "a_traiter": a_traiter,
    })


@login_required
def ecole_profils(request):
    _verifier_acces(request)
    identifiant = (request.GET.get("identifiant") or request.POST.get("identifiant") or "").strip()
    profil = None
    form = None
    erreur = None
    if identifiant:
        utilisateur = User.objects.filter(username=identifiant).first()
        if utilisateur is None:
            erreur = "Aucun compte trouvé pour cet identifiant."
        else:
            profil, _ = ProfilUtilisateur.objects.get_or_create(user=utilisateur)
            if request.method == "POST" and "enregistrer" in request.POST:
                form = CorrectionProfilForm(request.POST, instance=profil)
                if form.is_valid():
                    form.save()
                    return redirect(f"{reverse('ecole_profils')}?identifiant={identifiant}")
            else:
                form = CorrectionProfilForm(instance=profil)

    age = None
    if profil and profil.date_naissance:
        from datetime import date
        aujourdhui = date.today()
        dn = profil.date_naissance
        age = aujourdhui.year - dn.year - ((aujourdhui.month, aujourdhui.day) < (dn.month, dn.day))
    return render(request, "caisse/ecole_profils.html", {
        "profil": profil, "form": form, "erreur": erreur, "identifiant": identifiant, "age": age,
    })


@login_required
def ecole_comptes(request):
    """Liste de tous les comptes, avec la possibilite de declencher (ou
    d'annuler) une demande de suppression. La suppression reelle
    (anonymisation) ne peut se faire qu'une fois le delai de 3 mois ecoule."""
    _verifier_acces(request)
    if request.method == "POST":
        profil = get_object_or_404(ProfilUtilisateur, id=request.POST.get("profil_id"))
        if "demander_suppression" in request.POST:
            demande, cree = DemandeSuppressionCompte.objects.get_or_create(
                profil=profil, defaults={"demande_par": request.user}
            )
            if cree:
                envoyer_email_suppression(demande)
        elif "annuler_suppression" in request.POST:
            DemandeSuppressionCompte.objects.filter(profil=profil).delete()
        elif "basculer_remboursement" in request.POST:
            demande = DemandeSuppressionCompte.objects.filter(profil=profil).first()
            if demande:
                demande.remboursement_effectue = not demande.remboursement_effectue
                demande.save(update_fields=["remboursement_effectue"])
        elif "supprimer_definitivement" in request.POST:
            demande = DemandeSuppressionCompte.objects.filter(profil=profil).first()
            if demande and demande.eligible_suppression_definitive:
                profil.anonymiser()
                demande.delete()
        return redirect("ecole_comptes")

    recherche = request.GET.get("q", "").strip()
    profils = ProfilUtilisateur.objects.exclude(statut_compte="ANONYMISE").select_related("user", "demande_suppression")
    if recherche:
        profils = profils.filter(
            Q(user__first_name__icontains=recherche) | Q(user__last_name__icontains=recherche) | Q(user__username__icontains=recherche)
        )
    profils = sorted(profils, key=lambda p: (p.user.last_name or p.user.username).lower())

    nb_a_supprimer = nb_bientot = 0
    for p in profils:
        if hasattr(p, "demande_suppression"):
            if p.demande_suppression.eligible_suppression_definitive:
                nb_a_supprimer += 1
            else:
                nb_bientot += 1

    return render(request, "caisse/ecole_comptes.html", {
        "profils": profils, "nb_a_supprimer": nb_a_supprimer, "nb_bientot": nb_bientot, "recherche": recherche,
    })


@login_required
def ecole_recettes(request):
    _verifier_acces(request)
    aujourdhui = timezone.localdate()
    annee = int(request.GET.get("annee", aujourdhui.year))
    mois = int(request.GET.get("mois", aujourdhui.month))
    tz = timezone.get_current_timezone()
    debut_mois = datetime(annee, mois, 1, tzinfo=tz)
    fin_mois = datetime(annee + 1, 1, 1, tzinfo=tz) if mois == 12 else datetime(annee, mois + 1, 1, tzinfo=tz)

    resultats = []
    for pole in Pole.objects.filter(est_operationnel=True):
        lignes = LigneTransaction.objects.filter(
            transaction__pole=pole, transaction__date_operation__gte=debut_mois, transaction__date_operation__lt=fin_mois,
        ).select_related("produit")
        recette_evenements = sum((l.prix_unitaire * l.quantite for l in lignes if l.produit.evenement_id), start=Decimal("0"))
        recette_autre = sum((l.prix_unitaire * l.quantite for l in lignes if l.produit.est_vente_libre), start=Decimal("0"))
        recette_produits = sum((l.prix_unitaire * l.quantite for l in lignes if not l.produit.evenement_id and not l.produit.est_vente_libre), start=Decimal("0"))
        resultats.append({"pole": pole, "evenements": recette_evenements, "produits": recette_produits, "autre": recette_autre, "total": recette_evenements + recette_produits + recette_autre})

    mois_prec, annee_prec = (12, annee - 1) if mois == 1 else (mois - 1, annee)
    mois_suiv, annee_suiv = (1, annee + 1) if mois == 12 else (mois + 1, annee)
    return render(request, "caisse/ecole_recettes.html", {
        "resultats": resultats, "debut_mois": debut_mois,
        "mois_prec": mois_prec, "annee_prec": annee_prec, "mois_suiv": mois_suiv, "annee_suiv": annee_suiv,
    })


@login_required
def ecole_adherents(request):
    _verifier_acces(request)
    poles = Pole.objects.filter(tarifs_adhesion__isnull=False).distinct()
    annee = annee_scolaire_courante()
    return render(request, "caisse/ecole_adherents.html", {"poles": poles, "annee": annee})


@login_required
def ecole_adherents_pole(request, slug):
    _verifier_acces(request)
    pole = get_object_or_404(Pole, slug=slug)
    annee = annee_scolaire_courante()
    adherents = Adhesion.objects.filter(pole=pole, annee=annee).select_related("profil__user", "profil")
    from datetime import date
    aujourdhui = date.today()
    liste = []
    for a in adherents:
        u = a.profil.user
        dn = a.profil.date_naissance
        age = aujourdhui.year - dn.year - ((aujourdhui.month, aujourdhui.day) < (dn.month, dn.day)) if dn else None
        liste.append({"user": u, "age": age})
    liste.sort(key=lambda x: (x["user"].last_name or x["user"].username))
    return render(request, "caisse/ecole_adherents_pole.html", {"pole": pole, "liste": liste, "annee": annee})
