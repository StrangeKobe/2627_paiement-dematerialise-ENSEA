import secrets
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class EchecEncaissement(Exception):
    """Erreur metier levee pendant l'encaissement, pour annuler proprement
    la transaction SQL et afficher un message clair au vendeur."""

    def __init__(self, message):
        self.message = message


def generer_secret_qr():
    return secrets.token_hex(16)


class Pole(models.Model):
    """Un pole de l'ADE : Kfet, BDE, Epicuria."""
    nom = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    solde_analytique = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    est_operationnel = models.BooleanField(
        default=True,
        help_text="Décoche pour un pôle qui n'a pas son propre point de "
                  "vente (ex. ADE, qui vend sous BDE) : il disparaît des "
                  "listes de vente et de gestion, mais le rôle Admin ADE "
                  "reste intact et continue de superviser les autres pôles.",
    )
    logo = models.ImageField(
        upload_to="poles/", null=True, blank=True,
        help_text="Logo affiché sur les listes de pôles (adhésion, etc.). Optionnel.",
    )

    def __str__(self):
        return self.nom


class Evenement(models.Model):
    """Le dossier qui regroupe les places d'une soiree."""
    pole = models.ForeignKey(Pole, on_delete=models.PROTECT, related_name="evenements")
    nom = models.CharField(max_length=200)
    date_evenement = models.DateTimeField(null=True, blank=True)
    lieu = models.CharField(max_length=200, blank=True)
    photo = models.ImageField(upload_to="evenements/", null=True, blank=True)
    actif = models.BooleanField(default=True)
    date_fin_vente = models.DateTimeField(
        null=True, blank=True,
        help_text="À partir de cette date et heure, plus rien ne peut être "
                  "vendu pour cet événement, même si 'actif' reste coché. "
                  "Laisser vide pour ne pas fixer de coupure automatique.",
    )

    def est_vendable(self):
        if not self.actif:
            return False
        if self.date_fin_vente and timezone.now() >= self.date_fin_vente:
            return False
        return True

    def __str__(self):
        return self.nom


class Categorie(models.Model):
    """Rayon d'affichage sur la caisse (Boissons, Snacks...)."""
    pole = models.ForeignKey(Pole, on_delete=models.PROTECT, related_name="categories")
    nom = models.CharField(max_length=100)
    ordre = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.nom


class Produit(models.Model):
    """Un produit en vente. Permanent si evenement vide, sinon place d'event."""
    pole = models.ForeignKey(Pole, on_delete=models.PROTECT, related_name="produits")
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, blank=True, related_name="produits")
    evenement = models.ForeignKey(Evenement, on_delete=models.SET_NULL, null=True, blank=True, related_name="produits")
    nom = models.CharField(max_length=200)
    prix = models.DecimalField(max_digits=6, decimal_places=2)
    disponible = models.BooleanField(default=True)
    stock = models.IntegerField(null=True, blank=True)
    est_billet = models.BooleanField(
        default=True,
        help_text="Uniquement pour un produit rattaché à un événement : "
                  "coché si ce produit représente une entrée (compte dans "
                  "la liste des participants et se synchronise avec "
                  "HelloAsso), décoché pour un produit du catalogue de la "
                  "soirée (boisson, écocup...) qui ne compte pas comme une "
                  "présence.",
    )
    photo = models.ImageField(upload_to="produits/", null=True, blank=True)
    est_vente_libre = models.BooleanField(
        default=False, editable=False,
        help_text="Produit technique utilisé par le terminal (montant libre), "
                  "jamais affiché dans le catalogue.",
    )
    retire = models.BooleanField(
        default=False,
        help_text="Produit qui n'est plus vendu du tout : disparaît de la "
                  "vente et de la gestion normale, déplacé dans l'onglet "
                  "\"Retirés\" (visible uniquement des admins, jamais des "
                  "vendeurs). Différent de \"Disponible\", qui reste visible "
                  "mais grisé sur l'écran de vente.",
    )

    def __str__(self):
        return f"{self.nom} ({self.prix} EUR)"


class ProfilUtilisateur(models.Model):
    """Le profil cashless, rattache a un compte ecole (auth_user)."""
    STATUTS = [
        ("ACTIF", "Actif"),
        ("DESACTIVE", "Désactivé"),
        ("ANONYMISE", "Anonymisé"),
    ]
    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name="profil")
    solde = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    uid_rfid = models.CharField(max_length=32, unique=True, null=True, blank=True)
    secret_qr = models.CharField(max_length=64, default=generer_secret_qr)
    statut_compte = models.CharField(max_length=10, choices=STATUTS, default="ACTIF")
    date_naissance = models.DateField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

    def anonymiser(self):
        """Anonymise le compte : les informations personnelles disparaissent
        et la connexion est coupee, mais la ligne reste en base pour que
        l'historique comptable (ventes, recharges, adhesions) reste intact,
        comme l'exige la conservation des pieces comptables."""
        self.user.first_name = ""
        self.user.last_name = ""
        self.user.email = ""
        self.user.username = f"compte-supprime-{self.user.id}"
        self.user.is_active = False
        self.user.save()
        self.date_naissance = None
        self.statut_compte = "ANONYMISE"
        self.save()

class Recharge(models.Model):
    """Un rechargement du portefeuille (via HelloAsso ou en especes)."""
    STATUTS = [
        ("EN_ATTENTE", "En attente"),
        ("CONFIRMEE", "Confirmée"),
        ("ECHOUEE", "Échouée"),
    ]
    profil = models.ForeignKey(ProfilUtilisateur, on_delete=models.PROTECT, related_name="recharges")
    montant = models.DecimalField(max_digits=6, decimal_places=2)
    statut = models.CharField(max_length=10, choices=STATUTS, default="EN_ATTENTE")
    reference_helloasso = models.CharField(max_length=100, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_confirmation = models.DateTimeField(null=True, blank=True)
    mode_paiement = models.CharField(
        max_length=12,
        choices=[("HELLOASSO", "HelloAsso"), ("ESPECES", "Espèces")],
        default="HELLOASSO",
    )
    encaisse_par = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True,
        related_name="recharges_encaissees",
    )
    pole = models.ForeignKey(
        "Pole", on_delete=models.PROTECT, null=True, blank=True,
        related_name="recharges_especes",
        help_text="Le pôle depuis lequel la recharge a été faite (uniquement "
                  "pour les recharges en espèces ; une recharge HelloAsso "
                  "n'est rattachée à aucun pôle en particulier).",
    )

    def __str__(self):
        return f"Recharge {self.montant} EUR - {self.profil}"


class Transaction(models.Model):
    """Un achat : debite l'etudiant, credite le pole."""
    profil = models.ForeignKey(ProfilUtilisateur, on_delete=models.PROTECT, related_name="transactions")
    pole = models.ForeignKey(Pole, on_delete=models.PROTECT, related_name="transactions")
    montant_total = models.DecimalField(max_digits=8, decimal_places=2)
    date_operation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Achat {self.montant_total} EUR - {self.profil}"


class LigneTransaction(models.Model):
    """Le detail d'un ticket : un produit, une quantite, un prix fige."""
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="lignes")
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name="lignes")
    libelle = models.CharField(max_length=200)
    prix_unitaire = models.DecimalField(max_digits=6, decimal_places=2)
    quantite = models.PositiveSmallIntegerField(default=1)
    reference_helloasso = models.CharField(
        max_length=100, blank=True,
        help_text="Renseignée automatiquement si ce billet a été poussé "
                  "vers une inscription HelloAsso au moment de l'achat.",
    )

class Affectation(models.Model):
    """Un role d'une personne sur un pole (ou sur l'ADE entiere).

    - VENDEUR / ADMIN_POLE : rattaches a un pole precis.
    - ADMIN_ADE : role global (pole laisse vide), voit tous les poles.
    Une personne peut avoir plusieurs affectations (donc plusieurs roles).
    """
    ROLES = [
        ("VENDEUR", "Vendeur"),
        ("ADMIN_POLE", "Admin de pôle"),
        ("ADMIN_ADE", "Admin ADE"),
        ("ADMIN_ECOLE", "Admin école"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="affectations")
    pole = models.ForeignKey(Pole, on_delete=models.CASCADE, null=True, blank=True, related_name="affectations")
    role = models.CharField(max_length=20, choices=ROLES)

    # Droits supplementaires, pertinents uniquement pour un Vendeur (un
    # Admin de pole ou Admin ADE a deja tout, ces cases ne changent rien
    # pour eux). Accordes au cas par cas depuis la page Equipe.
    droit_recharger_especes = models.BooleanField(default=False)
    droit_adhesion_especes = models.BooleanField(default=False)
    droit_gerer_produits = models.BooleanField(default=False)
    droit_adhesions = models.BooleanField(default=False)
    droit_equipe = models.BooleanField(
        default=False,
        help_text="Voir l'onglet Equipe (qui a quels droits). N'autorise "
                  "jamais a modifier les droits de qui que ce soit : "
                  "cette action reste toujours reservee aux admins.",
    )
    droit_exporter = models.BooleanField(default=False)
    droit_parametres = models.BooleanField(default=False)

    def __str__(self):
        cible = self.pole.nom if self.pole else "ADE"
        return f"{self.user.username} - {self.get_role_display()} ({cible})"


def generer_code_jeton():
    return secrets.token_urlsafe(16)


class JetonPaiement(models.Model):
    """Un jeton de paiement a usage unique, encode dans le QR de l'etudiant.

    Le QR est dynamique : chaque affichage cree un nouveau jeton qui expire
    vite. Un jeton deja utilise ou trop vieux n'est plus valable, ce qui
    empeche de rejouer une capture d'ecran du QR."""
    profil = models.ForeignKey(ProfilUtilisateur, on_delete=models.CASCADE, related_name="jetons")
    code = models.CharField(max_length=64, unique=True, default=generer_code_jeton)
    date_creation = models.DateTimeField(auto_now_add=True)
    utilise = models.BooleanField(default=False)

    def est_valide(self):
        age = timezone.now() - self.date_creation
        return (not self.utilise) and age < timedelta(seconds=120)

    def __str__(self):
        return f"Jeton {self.profil} ({'utilise' if self.utilise else 'actif'})"

class ParticipantImporte(models.Model):
    """Un participant importe depuis une billetterie externe (HelloAsso),
    pour un evenement dont l'argent ne transite pas par notre portefeuille
    interne. Purement informatif : aucun mouvement d'argent associe, ne
    doit jamais entrer dans les comptes ni dans l'export financier."""
    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name="participants_importes")
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    quantite = models.PositiveSmallIntegerField(default=1)
    date_import = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.prenom} {self.nom}".strip()


class Adhesion(models.Model):
    pole = models.ForeignKey(Pole, on_delete=models.PROTECT, related_name="adhesions")
    profil = models.ForeignKey(ProfilUtilisateur, on_delete=models.PROTECT, related_name="adhesions")
    annee = models.PositiveSmallIntegerField(help_text="Année de début de l'année scolaire, ex. 2026 pour 2026-2027.")
    montant = models.DecimalField(max_digits=6, decimal_places=2)
    mode_paiement = models.CharField(
        max_length=12,
        choices=[("PORTEFEUILLE", "Portefeuille"), ("ESPECES", "Espèces")],
        default="PORTEFEUILLE",
    )
    encaisse_par = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True,
        related_name="adhesions_encaissees",
    )
    reference_helloasso = models.CharField(max_length=100, blank=True)
    date_paiement = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("pole", "profil", "annee")]
        verbose_name = "adhésion"

    def __str__(self):
        return f"{self.profil} - {self.pole} - {self.annee}"

class CodeSecuriteAdmin(models.Model):
    """La deuxieme serrure des comptes a pouvoir (admin de pole, admin
    ADE). Meme si les identifiants ENSEA de la personne sont voles, elle
    seule connait ce code, defini et remis en main propre par un admin
    ecole. Le code est stocke HACHE, exactement comme un mot de passe :
    personne, pas meme un admin ecole, ne peut le relire apres coup."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="codes_securite")
    pole = models.ForeignKey(
        Pole, on_delete=models.CASCADE, null=True, blank=True,
        related_name="codes_securite",
        help_text="Le pôle concerné. Vide pour un admin ADE (portée globale).",
    )
    code_hash = models.CharField(max_length=128)
    definie_par = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="codes_definis",
        help_text="L'admin école qui a généré ce code.",
    )
    date_maj = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user", "pole")]
        verbose_name = "code de sécurité admin"

    def __str__(self):
        cible = self.pole.nom if self.pole else "ADE"
        return f"Code de {self.user.username} ({cible})"


class DemandeSuppressionCompte(models.Model):
    """Suivi d'une demande de suppression d'un compte, declenchee par un
    admin ecole. Le compte n'est jamais anonymise immediatement : un delai
    de 3 mois s'ecoule d'abord, pendant lequel l'etudiant peut reclamer le
    remboursement de son solde aupres de l'admin ecole (en dehors de
    l'application), et pendant lequel la demande peut toujours etre annulee."""

    DUREE_DELAI_JOURS = 90

    profil = models.OneToOneField(
        ProfilUtilisateur, on_delete=models.CASCADE, related_name="demande_suppression"
    )
    demande_par = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="suppressions_demandees",
        help_text="L'admin école qui a déclenché cette demande de suppression.",
    )
    date_demande = models.DateTimeField(auto_now_add=True)
    remboursement_effectue = models.BooleanField(
        default=False,
        help_text="Coché par l'admin école une fois le remboursement du solde géré en dehors de l'application.",
    )

    @property
    def date_suppression_prevue(self):
        return self.date_demande + timedelta(days=self.DUREE_DELAI_JOURS)

    @property
    def jours_restants(self):
        return max((self.date_suppression_prevue - timezone.now()).days, 0)

    @property
    def suppression_possible(self):
        return timezone.now() >= self.date_suppression_prevue

    @property
    def eligible_suppression_definitive(self):
        """Le delai de 3 mois est ecoule, OU le remboursement a deja ete
        gere par l'admin ecole : dans les deux cas, plus rien ne s'oppose
        a l'anonymisation definitive du compte."""
        return self.suppression_possible or self.remboursement_effectue

    def __str__(self):
        return f"Suppression de {self.profil} prévue le {self.date_suppression_prevue:%d/%m/%Y}"


class TarifAdhesion(models.Model):
    """Un tarif d'adhesion propose par un pole (ex. "1ere annee" a 5 EUR,
    "Autre filiere" a 10 EUR). Un pole peut en proposer plusieurs a la
    fois."""
    pole = models.ForeignKey(Pole, on_delete=models.CASCADE, related_name="tarifs_adhesion")
    description = models.CharField(
        max_length=200,
        help_text="Ce que l'etudiant lit pour choisir, ex. '1ere annee' ou 'Ancien eleve'.",
    )
    prix = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        ordering = ["prix"]
        verbose_name = "tarif d'adhésion"

    def __str__(self):
        return f"{self.description} - {self.prix} EUR ({self.pole})"

 