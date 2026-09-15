import base64
import calendar
import csv
import io
from datetime import date, datetime, timedelta
from decimal import Decimal

import qrcode
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Min, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.db import transaction as db_transaction
from django.db.utils import IntegrityError, OperationalError
from django.utils import timezone

from .exports import construire_classeur
from .forms import BilletForm, CategorieForm, EvenementForm, InfoPersonnelleForm, PoleForm, ProduitForm
from .models import Adhesion, Affectation, Categorie, EchecEncaissement, Evenement, JetonPaiement, LigneTransaction, ParticipantImporte, Pole, Produit, ProfilUtilisateur, Recharge, Transaction
from .helloasso import inscrire_sur_helloasso
from .recus import envoyer_recu
from .roles import (
    annee_scolaire_courante, est_admin_ade, peut_encaisser_adhesion_especes, peut_exporter,
    peut_gerer, peut_gerer_adhesions, peut_gerer_produits, peut_modifier_equipe,
    peut_modifier_parametres, peut_recharger_especes, peut_vendre, peut_voir_equipe,
    peut_voir_suivi_especes, poles_gerables, poles_vendables,
)


def profil_de(user):
    """Recupere le profil cashless de l'utilisateur, le cree s'il n'existe pas.
    (Avec le CAS, le profil sera cree a la premiere connexion de l'etudiant.)"""
    profil, _ = ProfilUtilisateur.objects.get_or_create(user=user)
    return profil


@login_required
def accueil(request):
    profil = profil_de(request.user)
    mouvements = []
    for tx in profil.transactions.order_by("-date_operation")[:10]:
        premiere_ligne = tx.lignes.first()
        mouvements.append({
            "date": tx.date_operation, "titre": tx.pole.nom, "montant": tx.montant_total,
            "sens": "debit",
            "photo": premiere_ligne.produit.photo if premiere_ligne and premiere_ligne.produit.photo else None,
        })
    for rc in profil.recharges.filter(statut="CONFIRMEE").order_by("-date_confirmation")[:10]:
        mouvements.append({"date": rc.date_confirmation, "titre": "Rechargement", "montant": rc.montant, "sens": "credit", "photo": None})
    mouvements.sort(key=lambda m: m["date"], reverse=True)
    return render(request, "caisse/accueil.html", {"profil": profil, "mouvements": mouvements[:5]})


def _lignes_du_panier(panier):
    """Transforme le panier de la session en lignes detaillees + total.
    Une quantite tombee a 0 ou moins (stock epuise entre-temps) est ignoree :
    elle ne doit jamais devenir une ligne de vente fantome."""
    lignes = []
    total = 0
    for produit_id, quantite in panier.items():
        if quantite <= 0:
            continue
        produit = Produit.objects.get(id=produit_id)
        sous_total = produit.prix * quantite
        total += sous_total
        lignes.append({"produit": produit, "quantite": quantite, "sous_total": sous_total})
    return lignes, total


@login_required
def ajouter_au_panier(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)
    quantite = int(request.POST.get("quantite", 1))
    if quantite < 1:
        quantite = 1
    panier = request.session.get("panier", {})
    cle = str(produit_id)
    nouvelle_quantite = panier.get(cle, 0) + quantite
    # On ne peut jamais mettre dans le panier plus que le stock disponible.
    if produit.stock is not None:
        nouvelle_quantite = min(nouvelle_quantite, produit.stock)
    if nouvelle_quantite <= 0:
        panier.pop(cle, None)
    else:
        panier[cle] = nouvelle_quantite
    request.session["panier"] = panier
    url = reverse("detail_pole", kwargs={"slug": produit.pole.slug})
    cat_active = request.POST.get("cat_active")
    if cat_active:
        url += f"?cat={cat_active}"
    return redirect(url)


@login_required
def vider_panier(request, slug):
    request.session["panier"] = {}
    return redirect("detail_pole", slug=slug)


@login_required
def voir_panier(request, slug):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_vendre(request.user, pole):
        raise PermissionDenied
    panier = request.session.get("panier", {})
    lignes_panier, total = _lignes_du_panier(panier)
    return render(request, "caisse/panier.html", {
        "pole": pole, "lignes_panier": lignes_panier, "total": total,
    })


@login_required
def detail_pole(request, slug):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_vendre(request.user, pole):
        raise PermissionDenied
    cat_active = request.GET.get("cat")

    tous_groupes = []
    for categorie in pole.categories.all():
        produits_cat = categorie.produits.filter(retire=False)
        if produits_cat:
            tous_groupes.append({"id": str(categorie.id), "nom": categorie.nom, "produits": produits_cat})

    # Les billets d'un evenement actif forment leur propre groupe, au meme
    # titre qu'une categorie.
    for evenement in pole.evenements.filter(actif=True):
        if not evenement.est_vendable():
            continue
        billets_evt = evenement.produits.filter(retire=False)
        if billets_evt:
            tous_groupes.append({
                "id": f"evt-{evenement.id}", "nom": evenement.nom, "produits": billets_evt,
                "evenement": evenement,
            })

    sans_categorie = pole.produits.filter(
        categorie__isnull=True, est_vente_libre=False, evenement__isnull=True, retire=False
    )
    if sans_categorie:
        tous_groupes.append({"id": "autres", "nom": "Autres", "produits": sans_categorie})

    onglets = [{"id": g["id"], "nom": g["nom"]} for g in tous_groupes]

    # Sans choix, on n'affiche que les cases (groupes = None) ; "tous" montre
    # tout ; un id precis montre une seule categorie.
    if cat_active is None:
        groupes = None
    elif cat_active == "tous":
        groupes = tous_groupes
    else:
        groupes = [g for g in tous_groupes if g["id"] == cat_active]

    panier = request.session.get("panier", {})
    lignes_panier, total = _lignes_du_panier(panier)

    return render(request, "caisse/pole.html", {
        "pole": pole, "groupes": groupes, "onglets": onglets, "cat_active": cat_active,
        "lignes_panier": lignes_panier, "total": total,
    })

def _profil_depuis_saisie(identifiant, jeton_code):
    """Retrouve le profil de l'acheteur pour l'encaissement, soit via le
    jeton scanne dans son QR de paiement (prioritaire, a usage unique et
    expire au bout de 2 minutes), soit via l'identifiant saisi a la main."""
    if jeton_code:
        jeton = JetonPaiement.objects.select_for_update().filter(code=jeton_code).first()
        if jeton is None or not jeton.est_valide():
            raise EchecEncaissement("QR code invalide ou expiré, redemande-le à l'acheteur.")
        jeton.utilise = True
        jeton.save(update_fields=["utilise"])
        profil = ProfilUtilisateur.objects.select_for_update().filter(pk=jeton.profil_id).first()
    else:
        profil = (
            ProfilUtilisateur.objects.select_for_update()
            .filter(user__username=identifiant)
            .first()
        )
    if profil is None:
        raise EchecEncaissement("Aucun compte trouvé pour cet identifiant.")
    return profil


@login_required
def encaisser(request, slug):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_vendre(request.user, pole):
        raise PermissionDenied
    panier = request.session.get("panier", {})
    lignes_panier, total = _lignes_du_panier(panier)
    if not lignes_panier:
        return redirect("detail_pole", slug=slug)

    erreur = None
    if request.method == "POST":
        identifiant = request.POST.get("identifiant", "").strip()
        jeton_code = request.POST.get("jeton", "").strip()
        try:
            with db_transaction.atomic():
                profil = _profil_depuis_saisie(identifiant, jeton_code)

                total_verifie = 0
                lignes_verifiees = []
                for ligne in lignes_panier:
                    quantite = ligne["quantite"]
                    if quantite <= 0:
                        continue
                    produit = Produit.objects.select_for_update().get(pk=ligne["produit"].pk)
                    if produit.evenement_id and not produit.evenement.est_vendable():
                        raise EchecEncaissement(f"Les ventes pour {produit.evenement.nom} sont terminées.")
                    if produit.stock is not None and quantite > produit.stock:
                        raise EchecEncaissement(f"Stock insuffisant pour {produit.nom} (reste {produit.stock}).")
                    total_verifie += produit.prix * quantite
                    lignes_verifiees.append((produit, quantite))

                if not lignes_verifiees:
                    raise EchecEncaissement("Plus aucun produit disponible dans le panier, réessaie.")
                if profil.solde < total_verifie:
                    # Le solde exact disponible n'est jamais revele au
                    # vendeur : seul le montant demande (donnee publique)
                    # apparait dans le message d'erreur.
                    raise EchecEncaissement(f"Solde insuffisant pour cet achat de {total_verifie} EUR.")

                vente = Transaction.objects.create(profil=profil, pole=pole, montant_total=total_verifie)
                for produit, quantite in lignes_verifiees:
                    ligne_tx = LigneTransaction.objects.create(
                        transaction=vente, produit=produit, libelle=produit.nom,
                        prix_unitaire=produit.prix, quantite=quantite,
                    )
                    if produit.evenement_id and produit.est_billet:
                        ref = inscrire_sur_helloasso(produit.evenement, profil, quantite)
                        if ref:
                            ligne_tx.reference_helloasso = ref
                            ligne_tx.save(update_fields=["reference_helloasso"])
                    if produit.stock is not None:
                        produit.stock -= quantite
                        produit.save(update_fields=["stock"])
                profil.solde -= total_verifie
                profil.save(update_fields=["solde"])
                pole.solde_analytique += total_verifie
                pole.save(update_fields=["solde_analytique"])
        except EchecEncaissement as echec:
            erreur = echec.message
        except OperationalError:
            erreur = "Une autre vente est en cours sur ce produit, réessaie dans un instant."
        else:
            request.session["panier"] = {}
            envoyer_recu(vente)
            return render(request, "caisse/vente_ok.html", {"vente": vente, "profil": profil, "pole": pole})

    return render(request, "caisse/encaisser.html", {
        "pole": pole, "lignes_panier": lignes_panier, "total": total, "erreur": erreur,
    })


def _produit_vente_libre(pole):
    """Renvoie le produit technique 'Vente libre' du pole, le cree si besoin.
    N'apparait jamais dans les listes normales de produits."""
    produit, _ = Produit.objects.get_or_create(
        pole=pole, est_vente_libre=True,
        defaults={"nom": "Vente libre", "prix": 0, "disponible": False},
    )
    return produit


@login_required
def terminal_choix_pole(request):
    """Si l'utilisateur ne peut vendre que sur un seul pole, on y va
    directement ; sinon on lui demande de choisir."""
    poles = poles_vendables(request.user)
    if poles.count() == 1:
        return redirect("terminal_pole", slug=poles.first().slug)
    return render(request, "caisse/terminal_choix.html", {"poles": poles})


@login_required
def terminal_pole(request, slug):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_vendre(request.user, pole):
        raise PermissionDenied

    erreur = None
    if request.method == "POST":
        identifiant = request.POST.get("identifiant", "").strip()
        jeton_code = request.POST.get("jeton", "").strip()
        montant_saisi = request.POST.get("montant", "").strip()
        try:
            montant = Decimal(montant_saisi.replace(",", "."))
        except Exception:
            montant = Decimal("0")

        if montant <= 0:
            erreur = "Montant invalide."
        else:
            try:
                with db_transaction.atomic():
                    profil = _profil_depuis_saisie(identifiant, jeton_code)
                    if profil.solde < montant:
                        raise EchecEncaissement(
                            f"Solde insuffisant pour ce montant de {montant} EUR."
                        )
                    produit_libre = _produit_vente_libre(pole)
                    vente = Transaction.objects.create(
                        profil=profil, pole=pole, montant_total=montant
                    )
                    LigneTransaction.objects.create(
                        transaction=vente,
                        produit=produit_libre,
                        libelle="Vente libre",
                        prix_unitaire=montant,
                        quantite=1,
                    )
                    profil.solde -= montant
                    profil.save(update_fields=["solde"])
                    pole.solde_analytique += montant
                    pole.save(update_fields=["solde_analytique"])
            except EchecEncaissement as echec:
                erreur = echec.message
            except OperationalError:
                erreur = "Une autre opération est en cours, réessaie dans un instant."
            else:
                envoyer_recu(vente)
                return render(request, "caisse/vente_ok.html", {
                    "vente": vente, "profil": profil, "pole": pole,
                })

    return render(request, "caisse/terminal_pole.html", {"pole": pole, "erreur": erreur})


@login_required
def info(request):
    profil = profil_de(request.user)
    enregistre = False
    if request.method == "POST":
        form = InfoPersonnelleForm(request.POST, instance=profil)
        if form.is_valid():
            form.save()
            enregistre = True
            form = InfoPersonnelleForm(instance=profil)
    else:
        form = InfoPersonnelleForm(instance=profil)
    admins_ecole = User.objects.filter(
        affectations__role="ADMIN_ECOLE"
    ).distinct()
    return render(request, "caisse/info.html", {
        "profil": profil, "form": form, "enregistre": enregistre,
        "admins_ecole": admins_ecole,
    })


DUREE_JETON = 120  # duree de validite d'un QR de paiement, en secondes

def _qr_data_uri(texte):
    """Genere un QR code (image PNG) encode en data URI, affichable direct
    dans une balise <img> sans fichier a servir."""
    image = qrcode.make(texte, box_size=10, border=2)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


@login_required
def mon_qr(request):
    profil = profil_de(request.user)
    profil.jetons.filter(utilise=False).delete()
    jeton = JetonPaiement.objects.create(profil=profil)
    return render(request, "caisse/payer.html", {
        "qr_uri": _qr_data_uri(jeton.code),
        "duree": DUREE_JETON,
    })


@login_required
def recharger(request):
    return render(request, "caisse/recharger.html", {
        "profil": profil_de(request.user),
    })


@login_required
def gerer_produits(request, slug):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_gerer_produits(request.user, pole):
        raise PermissionDenied
    admin_reel = peut_gerer(request.user, pole)

    produits_actifs = pole.produits.filter(
        est_vente_libre=False, evenement__isnull=True, retire=False
    ).select_related("categorie")

    # Onglet "Retires" : uniquement pour un vrai admin (jamais un vendeur,
    # meme avec le droit de gerer le catalogue).
    voir_retires = admin_reel and request.GET.get("categorie") == "retires"

    if voir_retires:
        produits = pole.produits.filter(
            est_vente_libre=False, evenement__isnull=True, retire=True
        ).order_by("nom")
        categorie_id = None
    else:
        brut = request.GET.get("categorie")
        categorie_id = brut if brut and brut.isdigit() else None
        produits = produits_actifs.filter(categorie_id=categorie_id) if categorie_id else produits_actifs
        produits = produits.order_by("categorie__ordre", "nom")

    categories_comptes = []
    for c in pole.categories.all().order_by("ordre", "nom"):
        n = produits_actifs.filter(categorie=c).count()
        if n:
            categories_comptes.append({"id": c.id, "nom": c.nom, "nb": n})

    return render(request, "caisse/gerer_produits.html", {
        "pole": pole, "produits": produits,
        "categories_comptes": categories_comptes,
        "categorie_active": int(categorie_id) if categorie_id else None,
        "nb_total": produits_actifs.count(),
        "voir_retires": voir_retires,
        "admin_reel": admin_reel,
        "nb_retires": pole.produits.filter(
            est_vente_libre=False, evenement__isnull=True, retire=True
        ).count(),
    })


@login_required
def creer_produit(request, slug):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_gerer_produits(request.user, pole):
        raise PermissionDenied
    if request.method == "POST":
        form = ProduitForm(request.POST, request.FILES, pole=pole)
        if form.is_valid():
            produit = form.save(commit=False)
            produit.pole = pole  # jamais depuis le formulaire
            produit.save()
            return redirect("gerer_produits", slug=pole.slug)
    else:
        form = ProduitForm(pole=pole)
    return render(request, "caisse/produit_form.html", {"pole": pole, "form": form, "titre": "Nouveau produit"})


@login_required
def modifier_produit(request, slug, produit_id):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_gerer_produits(request.user, pole):
        raise PermissionDenied
    produit = get_object_or_404(Produit, id=produit_id, pole=pole)
    if request.method == "POST":
        if "retirer" in request.POST or "remettre" in request.POST:
            if not peut_gerer(request.user, pole):  # jamais un simple droit_gerer_produits
                raise PermissionDenied
            produit.retire = "retirer" in request.POST
            produit.save(update_fields=["retire"])
            return redirect("gerer_produits", slug=pole.slug)
        form = ProduitForm(request.POST, request.FILES, instance=produit, pole=pole)
        if form.is_valid():
            form.save()
            return redirect("gerer_produits", slug=pole.slug)
    else:
        form = ProduitForm(instance=produit, pole=pole)
    return render(request, "caisse/produit_form.html", {
        "pole": pole, "form": form, "titre": produit.nom, "produit": produit,
        "admin_reel": peut_gerer(request.user, pole),
    })


@login_required
def gerer_categories(request, slug):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_gerer_produits(request.user, pole):
        raise PermissionDenied

    if request.method == "POST":
        form = CategorieForm(request.POST)
        if form.is_valid():
            categorie = form.save(commit=False)
            categorie.pole = pole
            categorie.ordre = 0
            categorie.save()
            return redirect("gerer_categories", slug=pole.slug)
    else:
        form = CategorieForm()

    categories = pole.categories.all().order_by("ordre", "nom")
    return render(request, "caisse/gerer_categories.html", {
        "pole": pole, "categories": categories, "form": form,
    })


@login_required
def modifier_categorie(request, slug, categorie_id):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_gerer_produits(request.user, pole):
        raise PermissionDenied
    categorie = get_object_or_404(Categorie, id=categorie_id, pole=pole)
    if request.method == "POST":
        if "supprimer" in request.POST:
            if categorie.produits.exists():
                return render(request, "caisse/modifier_categorie.html", {
                    "pole": pole, "categorie": categorie,
                    "erreur": "Impossible de supprimer : des produits sont encore rattachés à cette catégorie.",
                })
            categorie.delete()
            return redirect("gerer_categories", slug=pole.slug)
        form = CategorieForm(request.POST, instance=categorie)
        if form.is_valid():
            form.save()
            return redirect("gerer_categories", slug=pole.slug)
    else:
        form = CategorieForm(instance=categorie)
    return render(request, "caisse/modifier_categorie.html", {"pole": pole, "categorie": categorie, "form": form})


@login_required
def gerer_evenements(request, slug):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_gerer_produits(request.user, pole):
        raise PermissionDenied
    evenements = pole.evenements.all().order_by("-date_evenement")
    return render(request, "caisse/gerer_evenements.html", {
        "pole": pole, "evenements": evenements,
    })


@login_required
def creer_evenement(request, slug):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_gerer_produits(request.user, pole):
        raise PermissionDenied
    if request.method == "POST":
        form = EvenementForm(request.POST, request.FILES)
        if form.is_valid():
            evenement = form.save(commit=False)
            evenement.pole = pole
            evenement.save()
            return redirect("gerer_evenements", slug=pole.slug)
    else:
        form = EvenementForm()
    return render(request, "caisse/evenement_form.html", {
        "pole": pole, "form": form, "titre": "Nouvel événement",
    })


@login_required
def modifier_evenement(request, slug, evenement_id):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_gerer_produits(request.user, pole):
        raise PermissionDenied
    evenement = get_object_or_404(Evenement, id=evenement_id, pole=pole)
    if request.method == "POST":
        form = EvenementForm(request.POST, request.FILES, instance=evenement)
        if form.is_valid():
            form.save()
            return redirect("modifier_evenement", slug=pole.slug, evenement_id=evenement.id)
    else:
        form = EvenementForm(instance=evenement)
    produits_evt = Produit.objects.filter(pole=pole, evenement=evenement).order_by("nom")
    billets = produits_evt.filter(est_billet=True)
    catalogue = produits_evt.filter(est_billet=False)
    return render(request, "caisse/evenement_form.html", {
        "pole": pole, "form": form, "titre": evenement.nom,
        "evenement": evenement, "billets": billets, "catalogue": catalogue,
    })


@login_required
def creer_billet(request, slug, evenement_id):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_gerer_produits(request.user, pole):
        raise PermissionDenied
    evenement = get_object_or_404(Evenement, id=evenement_id, pole=pole)
    # Les deux boutons "+ Ajouter un billet" et "+ Ajouter un produit" de
    # la page Modifier pre-remplissent ce type via ?type=billet|catalogue.
    est_billet_defaut = request.GET.get("type", "billet") != "catalogue"
    titre = "Nouveau billet" if est_billet_defaut else "Nouveau produit"
    if request.method == "POST":
        form = BilletForm(request.POST, request.FILES)
        if form.is_valid():
            billet = form.save(commit=False)
            billet.pole = pole
            billet.evenement = evenement
            billet.save()
            return redirect("modifier_evenement", slug=pole.slug, evenement_id=evenement.id)
    else:
        form = BilletForm(initial={"est_billet": est_billet_defaut})
    return render(request, "caisse/billet_form.html", {
        "pole": pole, "evenement": evenement, "form": form, "titre": titre,
    })


@login_required
def modifier_billet(request, slug, evenement_id, produit_id):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_gerer_produits(request.user, pole):
        raise PermissionDenied
    evenement = get_object_or_404(Evenement, id=evenement_id, pole=pole)
    billet = get_object_or_404(Produit, id=produit_id, pole=pole, evenement=evenement)
    if request.method == "POST":
        form = BilletForm(request.POST, request.FILES, instance=billet)
        if form.is_valid():
            form.save()
            return redirect("modifier_evenement", slug=pole.slug, evenement_id=evenement.id)
    else:
        form = BilletForm(instance=billet)
    return render(request, "caisse/billet_form.html", {
        "pole": pole, "evenement": evenement, "form": form, "titre": billet.nom, "billet": billet,
    })


@login_required
def participants_evenement(request, slug, evenement_id):
    """Liste NOMINATIVE des personnes ayant pris un billet pour cet
    evenement, ventes internes et import HelloAsso confondus. A la
    difference de l'export Excel (anonymise, usage comptable), cette page
    sert un usage operationnel."""
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_gerer_produits(request.user, pole):
        raise PermissionDenied
    evenement = get_object_or_404(Evenement, id=evenement_id, pole=pole)

    participants = []
    lignes = LigneTransaction.objects.filter(
        produit__evenement=evenement, produit__est_billet=True
    ).select_related("transaction__profil__user", "produit")
    for ligne in lignes:
        u = ligne.transaction.profil.user
        participants.append({
            "nom": f"{u.first_name} {u.last_name}".strip() or u.username,
            "quantite": ligne.quantite, "date": ligne.transaction.date_operation,
            "source": "Interne", "reference_helloasso": ligne.reference_helloasso,
        })
    for imp in evenement.participants_importes.all():
        participants.append({
            "nom": f"{imp.prenom} {imp.nom}".strip(), "quantite": imp.quantite,
            "date": imp.date_import, "source": "HelloAsso",
        })
    participants.sort(key=lambda p: p["nom"].lower())
    total_billets = sum(p["quantite"] for p in participants)
    return render(request, "caisse/participants_evenement.html", {
        "pole": pole, "evenement": evenement, "participants": participants, "total_billets": total_billets,
    })


_COLONNES_NOM = ["nom", "last name", "lastname", "last_name"]
_COLONNES_PRENOM = ["prenom", "prénom", "first name", "firstname", "first_name"]
_COLONNES_EMAIL = ["email", "e-mail", "adresse email", "adresse e-mail"]
_COLONNES_QUANTITE = ["quantite", "quantité", "qty", "nombre"]

def _trouver_colonne(entetes, candidats):
    entetes_normalisees = {e.strip().lower(): e for e in entetes}
    for candidat in candidats:
        if candidat in entetes_normalisees:
            return entetes_normalisees[candidat]
    return None

@login_required
def importer_participants(request, slug, evenement_id):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_gerer_produits(request.user, pole):
        raise PermissionDenied
    evenement = get_object_or_404(Evenement, id=evenement_id, pole=pole)
    erreur = None
    if request.method == "POST" and request.FILES.get("fichier"):
        contenu = request.FILES["fichier"].read().decode("utf-8-sig", errors="replace")
        delimiteur = ";" if contenu.count(";") > contenu.count(",") else ","
        lecteur = csv.DictReader(io.StringIO(contenu), delimiter=delimiteur)
        entetes = lecteur.fieldnames or []
        col_nom = _trouver_colonne(entetes, _COLONNES_NOM)
        col_prenom = _trouver_colonne(entetes, _COLONNES_PRENOM)
        col_email = _trouver_colonne(entetes, _COLONNES_EMAIL)
        col_qte = _trouver_colonne(entetes, _COLONNES_QUANTITE)
        if col_nom is None:
            erreur = "Impossible de trouver une colonne 'Nom' dans ce fichier. Colonnes détectées : " + ", ".join(entetes)
        else:
            for ligne in lecteur:
                nom = (ligne.get(col_nom) or "").strip()
                if not nom:
                    continue
                ParticipantImporte.objects.create(
                    evenement=evenement, nom=nom,
                    prenom=(ligne.get(col_prenom) or "").strip() if col_prenom else "",
                    email=(ligne.get(col_email) or "").strip() if col_email else "",
                    quantite=int(ligne.get(col_qte) or 1) if col_qte else 1,
                )
            return redirect("participants_evenement", slug=pole.slug, evenement_id=evenement.id)
    return render(request, "caisse/importer_participants.html", {"pole": pole, "evenement": evenement, "erreur": erreur})


@login_required
def asso_choix(request):
    """Si l'utilisateur n'est concerne que par un seul pole, on y va
    directement ; sinon on lui montre le recapitulatif des recettes et la
    liste des poles."""
    poles = (poles_vendables(request.user) | poles_gerables(request.user)).distinct()
    if poles.count() == 1:
        return redirect("espace_asso", slug=poles.first().slug)
    debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    recette_totale = Transaction.objects.filter(
        pole__in=poles, date_operation__gte=debut_mois
    ).aggregate(total=Sum("montant_total"))["total"] or 0
    return render(request, "caisse/asso_choix.html", {"poles": poles, "recette_totale": recette_totale})


@login_required
def espace_asso(request, slug):
    """Le tableau de bord d'un pole : recette du mois, puis les actions
    disponibles selon les droits."""
    pole = get_object_or_404(Pole, slug=slug)
    if not (peut_vendre(request.user, pole) or peut_gerer(request.user, pole)):
        raise PermissionDenied
    debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    recette_mois = pole.transactions.filter(date_operation__gte=debut_mois).aggregate(total=Sum("montant_total"))["total"] or 0
    # Si plusieurs poles sont accessibles, le "retour" logique est le
    # selecteur ; sinon (un seul pole) ce selecteur nous renverrait
    # immediatement ici (boucle sans fin) : le retour va alors a l'accueil.
    nb_poles_accessibles = (poles_vendables(request.user) | poles_gerables(request.user)).distinct().count()
    return render(request, "caisse/espace_asso.html", {
        "pole": pole, "recette_mois": recette_mois,
        "peut_vendre": peut_vendre(request.user, pole), "peut_gerer": peut_gerer(request.user, pole),
        "peut_recharger": peut_recharger_especes(request.user, pole),
        "peut_adhesion_especes": peut_encaisser_adhesion_especes(request.user, pole),
        "peut_suivi_especes": peut_voir_suivi_especes(request.user, pole),
        "peut_gerer_produits": peut_gerer_produits(request.user, pole),
        "peut_adhesions": peut_gerer_adhesions(request.user, pole),
        "peut_equipe": peut_voir_equipe(request.user, pole),
        "peut_exporter": peut_exporter(request.user, pole),
        "peut_parametres": peut_modifier_parametres(request.user, pole),
        "plusieurs_poles": nb_poles_accessibles > 1,
    })


DROITS_SUPPLEMENTAIRES = [
    "droit_adhesion_especes", "droit_gerer_produits", "droit_adhesions",
    "droit_equipe", "droit_exporter", "droit_parametres",
]


@login_required
def equipe_pole(request, slug):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_voir_equipe(request.user, pole):
        raise PermissionDenied
    admin_ade = est_admin_ade(request.user)

    erreur = None
    if request.method == "POST":
        if not peut_modifier_equipe(request.user, pole):
            raise PermissionDenied
        if "ajouter" in request.POST:
            identifiant = request.POST.get("identifiant", "").strip()
            role = request.POST.get("role")
            utilisateur = User.objects.filter(username=identifiant).first()
            if utilisateur is None:
                erreur = "Aucun compte trouvé pour cet identifiant."
            elif role not in ("VENDEUR", "ADMIN_POLE"):
                erreur = "Rôle invalide."
            else:
                Affectation.objects.get_or_create(user=utilisateur, pole=pole, role=role)
                return redirect("equipe_pole", slug=pole.slug)
        elif "retirer" in request.POST:
            Affectation.objects.filter(id=request.POST.get("retirer"), pole=pole).delete()
            return redirect("equipe_pole", slug=pole.slug)
        elif "modifier_droits" in request.POST:
            roles_modifiables = ["VENDEUR", "ADMIN_POLE"] if admin_ade else ["VENDEUR"]
            affectation = Affectation.objects.filter(
                id=request.POST.get("affectation"), pole=pole, role__in=roles_modifiables
            ).first()
            if affectation:
                if affectation.role == "VENDEUR":
                    for champ in DROITS_SUPPLEMENTAIRES:
                        setattr(affectation, champ, champ in request.POST)
                # "Recharger en especes" reste reserve a l'admin ADE, meme
                # si un admin de pole a techniquement acces a ce formulaire.
                if admin_ade:
                    affectation.droit_recharger_especes = "droit_recharger_especes" in request.POST
                affectation.save()
            return redirect("equipe_pole", slug=pole.slug)

    affectations = Affectation.objects.filter(pole=pole).select_related("user").order_by("role", "user__username")
    return render(request, "caisse/equipe_pole.html", {
        "pole": pole, "affectations": affectations, "erreur": erreur,
        "peut_modifier": peut_modifier_equipe(request.user, pole), "admin_ade": admin_ade,
    })


@login_required
def modifier_pole(request, slug):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_modifier_parametres(request.user, pole):
        raise PermissionDenied
    if request.method == "POST":
        form = PoleForm(request.POST, request.FILES, instance=pole)
        if form.is_valid():
            form.save()
            return redirect("modifier_pole", slug=pole.slug)
    else:
        form = PoleForm(instance=pole)
    return render(request, "caisse/pole_parametres.html", {"pole": pole, "form": form})


@login_required
def adherer_liste(request):
    poles = (
        Pole.objects.filter(tarifs_adhesion__isnull=False)
        .distinct()
        .annotate(prix_min=Min("tarifs_adhesion__prix"))
    )
    return render(request, "caisse/adherer_liste.html", {"poles": poles})


@login_required
def adherer_pole(request, slug):
    pole = get_object_or_404(Pole, slug=slug)
    tarifs = list(pole.tarifs_adhesion.all())
    if not tarifs:
        raise Http404("Ce pôle ne propose pas d'adhésion payante.")
    profil = profil_de(request.user)
    annee = annee_scolaire_courante()
    deja_adherent = Adhesion.objects.filter(pole=pole, profil=profil, annee=annee).first()

    erreur = None
    if request.method == "POST" and not deja_adherent:
        tarif = pole.tarifs_adhesion.filter(id=request.POST.get("tarif")).first()
        if tarif is None:
            erreur = "Choisis un tarif."
        else:
            try:
                with db_transaction.atomic():
                    p = ProfilUtilisateur.objects.select_for_update().get(pk=profil.pk)
                    if p.solde < tarif.prix:
                        raise EchecEncaissement(f"Solde insuffisant pour cette adhesion de {tarif.prix} EUR.")
                    p.solde -= tarif.prix
                    p.save(update_fields=["solde"])
                    pole.solde_analytique += tarif.prix
                    pole.save(update_fields=["solde_analytique"])
                    try:
                        Adhesion.objects.create(pole=pole, profil=p, annee=annee, montant=tarif.prix, mode_paiement="PORTEFEUILLE")
                    except IntegrityError:
                        raise EchecEncaissement("Adhésion déjà payée pour cette année.")
            except EchecEncaissement as echec:
                erreur = echec.message
            else:
                return redirect("adherer_pole", slug=pole.slug)

    return render(request, "caisse/adherer_pole.html", {
        "pole": pole, "annee": annee, "tarifs": tarifs, "deja_adherent": deja_adherent, "erreur": erreur,
    })


@login_required
def gerer_adherents(request, slug):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_gerer_adhesions(request.user, pole):
        raise PermissionDenied
    erreur = None
    annee_defaut = annee_scolaire_courante()
    annee = int(request.GET.get("annee", annee_defaut))
    if request.method == "POST":
        if "ajouter_tarif" in request.POST:
            description = request.POST.get("description", "").strip()
            try:
                prix = Decimal(request.POST.get("prix", "0").replace(",", "."))
                if not description or prix <= 0:
                    raise ValueError
                pole.tarifs_adhesion.create(description=description, prix=prix)
            except Exception:
                erreur = "Tarif invalide : renseigne une description et un prix positif."
        elif "retirer_tarif" in request.POST:
            pole.tarifs_adhesion.filter(id=request.POST.get("retirer_tarif")).delete()
        elif "especes" in request.POST:
            if not peut_encaisser_adhesion_especes(request.user, pole):
                raise PermissionDenied
            identifiant = request.POST.get("identifiant", "").strip()
            utilisateur = User.objects.filter(username=identifiant).first()
            tarif = pole.tarifs_adhesion.filter(id=request.POST.get("tarif")).first()
            if utilisateur is None:
                erreur = "Aucun compte trouvé pour cet identifiant."
            elif tarif is None:
                erreur = "Choisis un tarif d'adhésion valide."
            else:
                p = profil_de(utilisateur)
                try:
                    # Un paiement en especes est toujours attribue a l'annee
                    # scolaire REELLE en cours, jamais a l'annee historique
                    # eventuellement consultee via le selecteur.
                    Adhesion.objects.create(
                        pole=pole, profil=p, annee=annee_defaut, montant=tarif.prix,
                        mode_paiement="ESPECES", encaisse_par=request.user,
                    )
                except IntegrityError:
                    erreur = "Cette personne a déjà payé son adhésion pour cette année."
        return redirect("gerer_adherents", slug=pole.slug)

    adherents = Adhesion.objects.filter(pole=pole, annee=annee).select_related("profil__user", "encaisse_par").order_by("profil__user__last_name")
    annees_disponibles = sorted(
        set(Adhesion.objects.filter(pole=pole).values_list("annee", flat=True)) | {annee_defaut}, reverse=True,
    )
    return render(request, "caisse/gerer_adherents.html", {
        "pole": pole, "adherents": adherents, "annee": annee,
        "annee_defaut": annee_defaut, "annees_disponibles": annees_disponibles,
        "erreur": erreur, "peut_adhesion_especes": peut_encaisser_adhesion_especes(request.user, pole),
        "tarifs": pole.tarifs_adhesion.all(),
    })


@login_required
def payer_adhesion_especes(request, slug):
    """Un admin de pole (ou ADE) encaisse une adhesion en especes, sans
    jamais voir la liste complete des adherents ni pouvoir changer le
    prix : cette page ne fait qu'ajouter, elle ne montre rien d'autre."""
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_encaisser_adhesion_especes(request.user, pole):
        raise PermissionDenied
    tarifs = list(pole.tarifs_adhesion.all())
    if not tarifs:
        raise Http404("Ce pôle ne propose pas d'adhésion payante.")
    erreur = None
    if request.method == "POST":
        identifiant = request.POST.get("identifiant", "").strip()
        utilisateur = User.objects.filter(username=identifiant).first()
        tarif = pole.tarifs_adhesion.filter(id=request.POST.get("tarif")).first()
        if utilisateur is None:
            erreur = "Aucun compte trouvé pour cet identifiant."
        elif tarif is None:
            erreur = "Choisis un tarif d'adhésion valide."
        else:
            profil = profil_de(utilisateur)
            annee = annee_scolaire_courante()
            try:
                Adhesion.objects.create(
                    pole=pole, profil=profil, annee=annee, montant=tarif.prix,
                    mode_paiement="ESPECES", encaisse_par=request.user,
                )
            except IntegrityError:
                erreur = "Cette personne a déjà payé son adhésion pour cette année."
            else:
                return render(request, "caisse/adhesion_especes_ok.html", {"pole": pole, "profil": profil})
    return render(request, "caisse/payer_adhesion_especes.html", {"pole": pole, "erreur": erreur, "tarifs": tarifs})


@login_required
def recharger_especes(request, slug):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_recharger_especes(request.user, pole):
        raise PermissionDenied
    erreur = None
    if request.method == "POST":
        identifiant = request.POST.get("identifiant", "").strip()
        montant_saisi = request.POST.get("montant", "").strip()
        try:
            montant = Decimal(montant_saisi.replace(",", "."))
        except Exception:
            montant = Decimal("0")
        if montant <= 0:
            erreur = "Montant invalide."
        else:
            utilisateur = User.objects.filter(username=identifiant).first()
            profil = profil_de(utilisateur) if utilisateur else None
            if profil is None:
                erreur = "Aucun compte trouvé pour cet identifiant."
            else:
                with db_transaction.atomic():
                    p = ProfilUtilisateur.objects.select_for_update().get(pk=profil.pk)
                    p.solde += montant
                    p.save(update_fields=["solde"])
                    Recharge.objects.create(
                        profil=p, montant=montant, statut="CONFIRMEE", mode_paiement="ESPECES",
                        encaisse_par=request.user, date_confirmation=timezone.now(), pole=pole,
                    )
                return render(request, "caisse/recharge_especes_ok.html", {"profil": p, "montant": montant, "pole": pole})
    return render(request, "caisse/recharger_especes.html", {"pole": pole, "erreur": erreur})


@login_required
def gerer_especes(request, slug):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_voir_suivi_especes(request.user, pole):
        raise PermissionDenied

    def nom_affiche(utilisateur):
        if utilisateur is None:
            return "Inconnu"
        if utilisateur.first_name or utilisateur.last_name:
            return f"{utilisateur.first_name} {utilisateur.last_name}"
        return f"{utilisateur.username} (identifiant)"

    annee_defaut = annee_scolaire_courante()
    annee = int(request.GET.get("annee", annee_defaut))
    tz = timezone.get_current_timezone()
    debut_annee = datetime(annee, 8, 1, tzinfo=tz)
    fin_annee = datetime(annee + 1, 8, 1, tzinfo=tz)

    recharges = Recharge.objects.filter(
        mode_paiement="ESPECES", pole=pole, date_confirmation__gte=debut_annee, date_confirmation__lt=fin_annee,
    ).select_related("profil__user", "encaisse_par")
    adhesions = Adhesion.objects.filter(mode_paiement="ESPECES", pole=pole, annee=annee).select_related("profil__user", "encaisse_par")

    operations = []
    for r in recharges:
        operations.append({"date": r.date_confirmation, "personne": nom_affiche(r.profil.user), "montant": r.montant, "encaisse_par": nom_affiche(r.encaisse_par), "type": "Rechargement"})
    for a in adhesions:
        operations.append({"date": a.date_paiement, "personne": nom_affiche(a.profil.user), "montant": a.montant, "encaisse_par": nom_affiche(a.encaisse_par), "type": "Adhesion"})
    operations.sort(key=lambda o: o["date"] or timezone.now(), reverse=True)

    totaux_par_personne = {}
    for op in operations:
        cle = op["encaisse_par"]
        totaux_par_personne[cle] = totaux_par_personne.get(cle, Decimal("0")) + op["montant"]

    # Annees disponibles : celles ou il y a eu au moins une recharge, plus
    # l'annee scolaire en cours au minimum.
    toutes_dates = Recharge.objects.filter(
        mode_paiement="ESPECES", pole=pole
    ).values_list("date_confirmation", flat=True)
    annees_avec_donnees = set()
    for d in toutes_dates:
        if d:
            annees_avec_donnees.add(d.year if d.month >= 8 else d.year - 1)
    annees_avec_donnees |= set(
        Adhesion.objects.filter(mode_paiement="ESPECES", pole=pole).values_list("annee", flat=True)
    )
    annees_disponibles = sorted(annees_avec_donnees | {annee_defaut}, reverse=True)

    return render(request, "caisse/gerer_especes.html", {
        "pole": pole, "operations": operations, "totaux": totaux_par_personne,
        "annee": annee, "annees_disponibles": annees_disponibles,
    })


MOIS_FR = [
    (1, "Janvier"), (2, "Février"), (3, "Mars"), (4, "Avril"),
    (5, "Mai"), (6, "Juin"), (7, "Juillet"), (8, "Août"),
    (9, "Septembre"), (10, "Octobre"), (11, "Novembre"), (12, "Décembre"),
]


@login_required
def export_pole(request, slug):
    """Formulaire de choix de periode, puis telechargement direct du
    classeur Excel une fois la periode soumise (parametres dans l'URL)."""
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_exporter(request.user, pole):
        raise PermissionDenied

    aujourdhui = timezone.localdate()
    type_periode = request.GET.get("periode")

    if type_periode:
        if type_periode == "mois":
            annee = int(request.GET.get("annee", aujourdhui.year))
            mois = int(request.GET.get("mois", aujourdhui.month))
            date_debut = date(annee, mois, 1)
            dernier_jour = calendar.monthrange(annee, mois)[1]
            date_fin = date(annee, mois, dernier_jour) + timedelta(days=1)
            nom_fichier = f"{pole.slug}_{annee}-{mois:02d}.xlsx"
        elif type_periode == "annee":
            annee = int(request.GET.get("annee", aujourdhui.year))
            date_debut = date(annee, 1, 1)
            date_fin = date(annee + 1, 1, 1)
            nom_fichier = f"{pole.slug}_{annee}.xlsx"
        else:  # personnalise
            date_debut = datetime.strptime(request.GET.get("debut"), "%Y-%m-%d").date()
            date_fin_incluse = datetime.strptime(request.GET.get("fin"), "%Y-%m-%d").date()
            date_fin = date_fin_incluse + timedelta(days=1)
            nom_fichier = f"{pole.slug}_{date_debut}_au_{date_fin_incluse}.xlsx"

        classeur = construire_classeur(pole, date_debut, date_fin)
        reponse = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        reponse["Content-Disposition"] = f'attachment; filename="{nom_fichier}"'
        classeur.save(reponse)
        return reponse

    annees_disponibles = list(range(aujourdhui.year - 1, aujourdhui.year + 1))
    return render(request, "caisse/export_pole.html", {
        "pole": pole,
        "aujourdhui": aujourdhui,
        "annees": annees_disponibles,
        "mois_liste": MOIS_FR,
        "admin_ade": est_admin_ade(request.user),
    })


@login_required
def rechercher_identifiant(request):
    """Outil reserve a l'admin ADE : relie un identifiant anonyme au vrai
    nom, pour les rares cas ou une identification est reellement
    necessaire. L'export reste anonyme par defaut ; cette identification
    est une action volontaire et ciblee, jamais automatique."""
    if not est_admin_ade(request.user):
        raise PermissionDenied
    resultat = None
    erreur = None
    if request.method == "POST":
        saisie = request.POST.get("identifiant", "").strip().upper().replace("ETU-", "").lstrip("0")
        if saisie.isdigit():
            profil = ProfilUtilisateur.objects.select_related("user").filter(pk=int(saisie)).first()
            if profil is None:
                erreur = "Aucun compte ne correspond à cet identifiant."
            else:
                resultat = profil
        else:
            erreur = "Identifiant invalide : attendu sous la forme ETU-00042."
    return render(request, "caisse/rechercher_identifiant.html", {"resultat": resultat, "erreur": erreur})


@login_required
def exporter_participants(request, slug, evenement_id):
    """Export Excel de la liste NOMINATIVE des participants (vrais noms,
    contrairement a l'export financier des transactions qui reste
    anonymise). Reserve aux admins du pole."""
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_gerer_produits(request.user, pole):
        raise PermissionDenied
    evenement = get_object_or_404(Evenement, id=evenement_id, pole=pole)

    def _majeur_depuis_naissance(date_naissance):
        """True/False/None (None si la date de naissance n'est pas connue).
        Jamais l'age exact : seul l'admin ecole y a acces, un admin de pole
        gerant un evenement n'a besoin que de savoir oui/non."""
        if date_naissance is None:
            return None
        aujourdhui = date.today()
        age = aujourdhui.year - date_naissance.year - (
            (aujourdhui.month, aujourdhui.day) < (date_naissance.month, date_naissance.day)
        )
        return age >= 18

    participants = []
    lignes = LigneTransaction.objects.filter(
        produit__evenement=evenement, produit__est_billet=True
    ).select_related("transaction__profil__user")
    for ligne in lignes:
        u = ligne.transaction.profil.user
        participants.append({
            "nom": f"{u.first_name} {u.last_name}".strip() or u.username,
            "quantite": ligne.quantite,
            "date": ligne.transaction.date_operation,
            "source": "Achat via l'appli",
            "majeur": _majeur_depuis_naissance(ligne.transaction.profil.date_naissance),
        })
    for imp in evenement.participants_importes.all():
        participants.append({
            "nom": f"{imp.prenom} {imp.nom}".strip(),
            "quantite": imp.quantite,
            "date": imp.date_import,
            "source": "HelloAsso",
            "majeur": None,
        })
    participants.sort(key=lambda p: p["nom"].lower())

    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    classeur = Workbook()
    feuille = classeur.active
    feuille.title = "Participants"
    # "Presente" reste une case vide a remplir a la main (ex. une croix) a
    # l'entree : openpyxl ne sait pas poser de vraie case a cocher cliquable.
    entetes = ["Nom", "Quantité", "Date", "Source", "Majeur", "Présent"]
    for i, texte in enumerate(entetes, start=1):
        cellule = feuille.cell(row=1, column=i, value=texte)
        cellule.font = Font(color="FFFFFF", bold=True)
        cellule.fill = PatternFill("solid", fgColor="C8004B")
    for row, p in enumerate(participants, start=2):
        feuille.cell(row=row, column=1, value=p["nom"])
        feuille.cell(row=row, column=2, value=p["quantite"])
        feuille.cell(row=row, column=3, value=p["date"].strftime("%d/%m/%Y %H:%M"))
        feuille.cell(row=row, column=4, value=p["source"])
        # Jamais l'age exact ici (reserve a l'admin ecole) : juste
        # oui/non, colore pour reperer d'un coup d'oeil a l'entree.
        if p["majeur"] is True:
            cellule_majeur = feuille.cell(row=row, column=5, value="Oui")
            cellule_majeur.fill = PatternFill("solid", fgColor="C6EFCE")
        elif p["majeur"] is False:
            cellule_majeur = feuille.cell(row=row, column=5, value="Non")
            cellule_majeur.fill = PatternFill("solid", fgColor="FFC7CE")
        else:
            feuille.cell(row=row, column=5, value="Inconnu")
    for i, largeur in enumerate([28, 12, 18, 20, 10, 12], start=1):
        feuille.column_dimensions[chr(64 + i)].width = largeur

    reponse = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    nom_fichier = f"participants_{evenement.nom.replace(' ', '_')}.xlsx"
    reponse["Content-Disposition"] = f'attachment; filename="{nom_fichier}"'
    classeur.save(reponse)
    return reponse


@login_required
def exporter_adherents(request, slug):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_gerer_adhesions(request.user, pole):
        raise PermissionDenied
    annee = int(request.GET.get("annee", annee_scolaire_courante()))
    adherents = Adhesion.objects.filter(pole=pole, annee=annee).select_related(
        "profil__user", "encaisse_par"
    )

    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    classeur = Workbook()
    feuille = classeur.active
    feuille.title = "Adherents"
    entetes = ["Nom", "Prénom", "Email", "Montant (EUR)", "Mode", "Encaissé par", "Date"]
    for i, texte in enumerate(entetes, start=1):
        cellule = feuille.cell(row=1, column=i, value=texte)
        cellule.font = Font(color="FFFFFF", bold=True)
        cellule.fill = PatternFill("solid", fgColor="C8004B")

    total_especes = Decimal("0")
    total_portefeuille = Decimal("0")
    row = 2
    for a in adherents:
        u = a.profil.user
        feuille.cell(row=row, column=1, value=u.last_name or "")
        feuille.cell(row=row, column=2, value=u.first_name or "")
        feuille.cell(row=row, column=3, value=u.email or "")
        feuille.cell(row=row, column=4, value=float(a.montant))
        feuille.cell(row=row, column=5, value=a.get_mode_paiement_display())
        feuille.cell(row=row, column=6, value=a.encaisse_par.username if a.encaisse_par else "-")
        feuille.cell(row=row, column=7, value=a.date_paiement.strftime("%d/%m/%Y %H:%M"))
        if a.mode_paiement == "ESPECES":
            total_especes += a.montant
        else:
            total_portefeuille += a.montant
        row += 1

    row += 1
    c1 = feuille.cell(row=row, column=1, value="Total espèces")
    c2 = feuille.cell(row=row, column=4, value=float(total_especes))
    c1.font = Font(bold=True); c2.font = Font(bold=True)
    row += 1
    c1 = feuille.cell(row=row, column=1, value="Total portefeuille")
    c2 = feuille.cell(row=row, column=4, value=float(total_portefeuille))
    c1.font = Font(bold=True); c2.font = Font(bold=True)

    for i, largeur in enumerate([18, 18, 26, 16, 14, 16, 18], start=1):
        feuille.column_dimensions[chr(64 + i)].width = largeur

    reponse = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    reponse["Content-Disposition"] = f'attachment; filename="adherents_{pole.slug}_{annee}.xlsx"'
    classeur.save(reponse)
    return reponse


def _entete_feuille(feuille, colonnes):
    from openpyxl.styles import Font, PatternFill
    for i, texte in enumerate(colonnes, start=1):
        cellule = feuille.cell(row=1, column=i, value=texte)
        cellule.font = Font(color="FFFFFF", bold=True)
        cellule.fill = PatternFill("solid", fgColor="C8004B")


@login_required
def exporter_especes(request, slug):
    pole = get_object_or_404(Pole, slug=slug)
    if not peut_voir_suivi_especes(request.user, pole):
        raise PermissionDenied
    annee = int(request.GET.get("annee", annee_scolaire_courante()))

    def nom_affiche(utilisateur):
        if utilisateur is None:
            return "Inconnu"
        if utilisateur.first_name or utilisateur.last_name:
            return f"{utilisateur.first_name} {utilisateur.last_name}"
        return f"{utilisateur.username} (identifiant)"

    # Les 12 mois de l'annee scolaire, dans l'ordre aout -> juillet.
    mois_annee_scolaire = [(annee, m) for m in range(8, 13)] + [(annee + 1, m) for m in range(1, 8)]

    from openpyxl import Workbook
    from openpyxl.styles import Font

    classeur = Workbook()
    feuille_recap = classeur.active
    feuille_recap.title = "Récapitulatif"
    _entete_feuille(feuille_recap, ["Mois", "Total (EUR)"])

    tz = timezone.get_current_timezone()
    total_annee = Decimal("0")
    row = 2
    for an, mois in mois_annee_scolaire:
        debut = datetime(an, mois, 1, tzinfo=tz)
        fin = datetime(an + 1, 1, 1, tzinfo=tz) if mois == 12 else datetime(an, mois + 1, 1, tzinfo=tz)

        recharges_mois = Recharge.objects.filter(
            mode_paiement="ESPECES", pole=pole,
            date_confirmation__gte=debut, date_confirmation__lt=fin,
        ).select_related("profil__user", "encaisse_par")
        adhesions_mois = Adhesion.objects.filter(
            mode_paiement="ESPECES", pole=pole,
            date_paiement__gte=debut, date_paiement__lt=fin,
        ).select_related("profil__user", "encaisse_par")

        operations_mois = []
        for r in recharges_mois:
            operations_mois.append((r.date_confirmation, nom_affiche(r.profil.user), r.montant, nom_affiche(r.encaisse_par), "Rechargement"))
        for a in adhesions_mois:
            operations_mois.append((a.date_paiement, nom_affiche(a.profil.user), a.montant, nom_affiche(a.encaisse_par), "Adhesion"))
        operations_mois.sort(key=lambda o: o[0])

        nom_mois = dict(MOIS_FR)[mois]
        total_mois = sum((o[2] for o in operations_mois), start=Decimal("0"))
        total_annee += total_mois

        feuille_recap.cell(row=row, column=1, value=f"{nom_mois} {an}")
        feuille_recap.cell(row=row, column=2, value=float(total_mois))
        row += 1

        # Un onglet par mois, cree seulement s'il y a eu au moins une
        # recharge ce mois-la : pas d'onglets vides pour rien.
        if operations_mois:
            feuille_mois = classeur.create_sheet(f"{nom_mois} {an}"[:31])
            _entete_feuille(feuille_mois, ["Date", "Personne", "Type", "Montant (EUR)", "Encaissé par"])
            r_row = 2
            for date_op, personne, montant, encaisseur, type_op in operations_mois:
                feuille_mois.cell(row=r_row, column=1, value=date_op.strftime("%d/%m/%Y %H:%M") if date_op else "")
                feuille_mois.cell(row=r_row, column=2, value=personne)
                feuille_mois.cell(row=r_row, column=3, value=type_op)
                feuille_mois.cell(row=r_row, column=4, value=float(montant))
                feuille_mois.cell(row=r_row, column=5, value=encaisseur)
                r_row += 1
            for i, largeur in enumerate([18, 22, 14, 16, 22], start=1):
                feuille_mois.column_dimensions[chr(64 + i)].width = largeur

    c1 = feuille_recap.cell(row=row + 1, column=1, value="Total année")
    c2 = feuille_recap.cell(row=row + 1, column=2, value=float(total_annee))
    c1.font = Font(bold=True)
    c2.font = Font(bold=True)
    feuille_recap.column_dimensions["A"].width = 22
    feuille_recap.column_dimensions["B"].width = 16

    reponse = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    reponse["Content-Disposition"] = f'attachment; filename="especes_{pole.slug}_{annee}-{annee+1}.xlsx"'
    classeur.save(reponse)
    return reponse
