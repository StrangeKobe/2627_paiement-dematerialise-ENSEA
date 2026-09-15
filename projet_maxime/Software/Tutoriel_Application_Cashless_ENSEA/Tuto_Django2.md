# Tutoriel - ENSEA Cashless, de A à Z

Ce document reconstruit, de zéro et dans l'ordre logique, l'application **ENSEA
Cashless** : un système de caisse sans espèces (« cashless ») pour les pôles
associatifs d'une école (Kfet, BDE, Epicuria...), avec gestion des adhésions,
des événements, des rôles et de la sécurité des comptes à pouvoir.

Il remplace le journal chronologique `Tuto_Django.md` (qui racontait le
développement au fil de l'eau, avec ses essais, ses bugs et ses réécritures)
par une version **consolidée et organisée par grand domaine fonctionnel**,
présentant à chaque fois l'état **final** du code, avec le **pourquoi** de
chaque décision de conception. L'objectif : qu'une personne qui n'a jamais vu
le projet puisse le reconstruire entièrement, en comprenant à chaque étape
pourquoi les choses sont faites ainsi et pas autrement.

## Sommaire

- [Partie 0 - Mise en place du projet](#partie-0---mise-en-place-du-projet)
- [Partie 1 - Les modèles de données](#partie-1---les-modèles-de-données)
- [Partie 2 - Rôles et permissions](#partie-2---rôles-et-permissions)
- [Partie 3 - La vente : panier, encaissement, concurrence](#partie-3---la-vente--panier-encaissement-concurrence)
- [Partie 4 - Authentification et sécurité renforcée](#partie-4---authentification-et-sécurité-renforcée)
- [Partie 5 - Espace personnel de l'étudiant](#partie-5---espace-personnel-de-létudiant)
- [Partie 6 - Le catalogue : produits, catégories, événements](#partie-6---le-catalogue--produits-catégories-événements)
- [Partie 7 - Espace Asso (tableau de bord d'un pôle)](#partie-7---espace-asso-tableau-de-bord-dun-pôle)
- [Partie 8 - Adhésions](#partie-8---adhésions)
- [Partie 9 - Espèces (recharges et suivi)](#partie-9---espèces-recharges-et-suivi)
- [Partie 10 - Espace École (administration globale)](#partie-10---espace-école-administration-globale)
- [Partie 11 - Emails](#partie-11---emails)
- [Partie 12 - Exports Excel et confidentialité](#partie-12---exports-excel-et-confidentialité)
- [Partie 13 - Fondations transverses et style](#partie-13---fondations-transverses-et-style)
- [Partie 14 - Ce qu'il reste à faire pour la production](#partie-14---ce-quil-reste-à-faire-pour-la-production)

---

## Partie 0 - Mise en place du projet

### 0.1 Pourquoi Django, et comment démarrer

On part d'un projet vide. Le choix structurant de départ : **un seul projet
(`cashless`) et une seule app (`caisse`)**, tant que le code ne devient pas
trop volumineux pour rester lisible dans une app unique (ce qui a fini par
arriver - voir `vues_ecole.py` en Partie 10, séparé de `views.py` précisément
pour cette raison).

Place-toi dans le dossier de ton repo de stage, puis crée un environnement virtuel. Un venv, c'est une bulle Python propre à ce projet : les librairies que tu installes dedans ne polluent pas le reste de ta machine et restent à la bonne version.

```bash
python3 -m venv venv
source venv/bin/activate     
```

Quand c'est activé, tu vois `(venv)` au début de ta ligne de terminal. Tout ce qu'on installe maintenant reste dans cette bulle.

**2. Installer Django et créer le projet**

```bash
pip install django
django-admin startproject cashless .
python manage.py startapp caisse
```

La première ligne installe Django. La deuxième crée le projet, que j'ai appelé `cashless` (le point à la fin veut dire "ici, dans le dossier courant", ça évite un dossier en trop). La troisième crée une application `caisse` : dans le tuto, tout tient dans une seule app pour rester simple, on fait pareil et on découpera seulement si ça devient gros. Tu peux changer ces deux noms si tu préfères, mais alors adapte les commandes suivantes.

**Règle fixée** dès le départ et jamais transgressée : **on ne touche jamais à
`manage.py`**, c'est un fichier généré, standard, qui n'a aucune raison de
changer.

Ouvre `cashless/settings.py`. D'abord, ajoute ton app à la liste
`INSTALLED_APPS` (ajoute la ligne `"caisse",` à la fin de la liste). Remplace :

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
```
par :

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'caisse',
]
```

`startapp` a bien créé le dossier `caisse/` sur le disque, mais Django ne le
sait pas encore : sans cette ligne, il **ignore complètement** ton
application, aucune de ses vues, aucun de ses modèles ne sera pris en compte,
et ça ne produira **aucune erreur visible** pour te prévenir de l'oubli.

Ensuite, remplace trois réglages pour que tout soit en français et à l'heure
de Paris, sinon tu auras l'interface en anglais et des dates décalées d'une
heure ou deux (un décalage difficile à repérer une fois que la base contient
déjà des données réelles). Remplace :

```python
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True
```
par :

```python
LANGUAGE_CODE = "fr-fr"

TIME_ZONE = "Europe/Paris"

USE_I18N = True

USE_TZ = True
```

`USE_TZ` reste à `True` (c'est déjà la valeur par défaut, on n'y touche pas) :
avec ce réglage, Django stocke toutes les dates en UTC en base, et ne les
convertit à l'heure de Paris qu'au moment de l'affichage. C'est cette
combinaison (`USE_TZ = True` + `TIME_ZONE = "Europe/Paris"`), pas l'une des
deux seule, qui évite les décalages liés au passage heure d'été/heure d'hiver
plus tard dans le projet.

Puis on initialise la base :

```bash
python manage.py migrate
```

Cette commande crée le fichier `db.sqlite3` et y installe les tables dont
Django a besoin pour fonctionner (comptes, sessions...). On n'a encore rien
créé de nous-mêmes : c'est juste le socle technique.

**3. Lancer le serveur et vérifier que ça marche**

```bash
python manage.py runserver
```

Le terminal affiche quelque chose comme `Starting development server at
http://127.0.0.1:8000/`. Ce n'est **pas juste un message d'information** :
c'est l'adresse à laquelle il faut aller. Ouvre un navigateur et tape
`http://127.0.0.1:8000/` (ou `localhost:8000`, ça revient au même) dans la
barre d'adresse - rien ne s'affiche tout seul, la commande ne fait qu'attendre
des requêtes. À ce stade tu dois voir une page Django par défaut (fusée, «
The install worked successfully »), c'est normal : on n'a encore créé aucune
page à nous. `Ctrl+C` dans le terminal arrête le serveur ; on le relance avec
la même commande à chaque fois qu'on veut retester quelque chose.

Par défaut, `runserver` n'écoute que sur ta propre machine
(`127.0.0.1`, dit aussi *localhost*) : personne d'autre sur le réseau ne peut
y accéder, seulement toi, depuis ce même ordinateur. C'est le mode normal de
travail. (Si un jour tu dois tester depuis un téléphone sur le même Wi-Fi, il
existe `python manage.py runserver 0.0.0.0:8000`, qui ouvre l'accès à tout le
réseau local - à n'utiliser que ponctuellement, en connaissance de cause, et à
refermer ensuite en revenant à `runserver` tout court.)

**4. Créer un compte pour toi-même**

```bash
python manage.py createsuperuser
```

Suis les questions (nom, mot de passe). Ce compte, c'est l'admin Django, celui qui a tous les droits. Relance `runserver`, va sur
`http://127.0.0.1:8000/admin/` et connecte-toi : tu es dans le back-office de
Django, encore vide, on le remplira à l'étape des modèles.

Le CAS de l'école (authentification centralisée) et l'export CSV brut sont
délibérément **reportés à la fin** : on développe d'abord avec
l'authentification standard de Django (Partie 4), pour ne pas mélanger deux
sujets différents. Le remplacement par le CAS ne changera qu'un point d'entrée
technique, pas la logique métier qui en dépend.

**5. Sauvegarder proprement sur GitHub (ou tout autre dépôt Git)**

Avant de commiter quoi que ce soit, il faut un fichier `.gitignore` à la
racine du projet, pour ne jamais envoyer sur le dépôt des fichiers inutiles ou
sensibles : ta bulle `venv` (des gigaoctets de librairies, aucun intérêt à les
versionner), la base de données locale `db.sqlite3` (propre à ta machine, elle
contiendrait en plus les données de test au moment du commit), les fichiers
compilés Python (`__pycache__/`, `*.pyc`), et surtout **`.env`**, le fichier
qui contiendra plus tard de vrais secrets (mot de passe email, voir Partie
11) : s'il finit sur GitHub une seule fois, il faut considérer le secret
comme grillé, même après l'avoir supprimé d'un commit suivant (il reste dans
l'historique).

La façon la plus rapide de créer ce fichier est de tout écrire d'un coup
depuis le terminal, avec un « here-document » (`cat > ... << 'EOF'` écrit
tout ce qui suit dans le fichier, jusqu'à la ligne `EOF` finale) :

```bash
cat > .gitignore << 'EOF'
venv/
__pycache__/
*.pyc
db.sqlite3
.env
EOF
```

Ouvre le fichier pour vérifier que ces cinq lignes y sont bien, c'est tout,
`.gitignore` n'a besoin de rien d'autre pour l'instant. (Le dossier `media/`,
qui recevra les photos uploadées par les utilisateurs, viendra s'y ajouter
plus tard, à l'étape où on introduit les images — Partie 1.2.)

Ensuite, fige la liste exacte des librairies installées dans le venv, pour
que n'importe qui (toi sur une autre machine, quelqu'un qui reprend le
projet) puisse recréer exactement le même environnement plutôt que de
deviner :

```bash
pip freeze > requirements.txt
```

Et enfin, le premier commit :

```bash
git add .
git commit -m "Initialisation du projet Django cashless"
git push
```

`git add .` ajoute tous les fichiers du dossier au prochain commit,
**sauf** ceux listés dans `.gitignore`, qui sont ignorés silencieusement,
c'est tout l'intérêt de l'avoir créé avant ce premier `add`. Si tu vérifies
avec `git status` juste avant et que tu vois `venv/` ou `db.sqlite3` dans la
liste des fichiers à ajouter, c'est que le `.gitignore` n'est pas encore pris
en compte (mauvais dossier, faute de frappe) : à corriger avant de continuer,
plutôt que de nettoyer après coup.

Voilà pour la mise en place du projet : à ce stade, `runserver` doit tourner,
la page d'accueil Django par défaut doit s'afficher, `/admin/` doit te
demander de te connecter avec le compte créé plus haut, et le projet doit
être versionné sur Git avec un historique propre. On attaque maintenant le
cœur du projet : les modèles de données.

---

## Partie 1 - Les modèles de données

C'est le cœur du projet : toutes les vues et tous les templates s'appuient
dessus. On les présente ici dans leur **état final**, mais avec le
raisonnement qui a mené à chaque champ, beaucoup de ces champs ont été
ajoutés progressivement, au fil de vrais besoins rencontrés plus tard dans le
projet (adhésions, sécurité, confidentialité...).

### 1.1 Vocabulaire métier et grandes règles

- **Pôle** (`Pole`) : une association (Kfet, BDE, Epicuria...). Toutes les
  transactions, catégories, produits, adhésions lui sont rattachés.
- **`on_delete` : la règle d'or.** Toute donnée qui porte de l'**historique
  comptable ou événementiel** utilise `PROTECT` (interdit de supprimer tant
  que des lignes en dépendent) - c'est le cas de `Pole` (protégé dès qu'un
  événement, une catégorie, un produit, une vente ou une adhésion lui est
  rattaché), de `Produit` (protégé dès qu'une ligne de vente le référence),
  et de `ProfilUtilisateur` (protégé dès qu'une vente, une recharge ou une
  adhésion lui appartient). Seule exception : `LigneTransaction → Transaction`
  utilise `CASCADE`, car une ligne de ticket n'a strictement aucun sens sans
  son ticket parent. À l'inverse, les relations optionnelles et non «
  porteuses d'histoire » (`categorie` et `evenement` sur `Produit`)
  utilisent `SET_NULL`, plus souple : supprimer une catégorie ne doit pas
  empêcher de garder ses anciens produits, ils perdent juste leur
  classement. `Categorie` elle-même n'est donc **pas** protégée par
  `on_delete` contre la suppression si des produits y sont rattachés — ce
  garde-fou-là est ajouté à la main, au niveau de la vue plutôt que du
  modèle (voir Partie 6.2).
- **L'argent est toujours un `DecimalField`**, jamais un `float` (qui
  introduirait des erreurs d'arrondi inacceptables sur de la comptabilité).
- **Une ligne de vente fige (« snapshot ») le nom et le prix du produit au
  moment de l'achat.** Si le prix d'un produit change ensuite, les anciens
  tickets ne bougent jamais. C'est plus simple qu'un système de versioning des
  prix, et suffisant pour le besoin réel.

### 1.2 Le catalogue : `Pole`, `Evenement`, `Categorie`, `Produit`

Tout le code de cette Partie 1 va dans un seul fichier : `caisse/models.py`
(créé vide par `startapp`, avec juste `from django.db import models` dedans).
On va y aller par blocs logiques pour que tu digères, chaque sous-section
(1.2 à 1.6) ajoutant des classes **à la suite**, jamais dans un fichier
séparé.

On commence par le catalogue, parce que c'est le plus concret et le plus
visuel : les pôles, les événements, les catégories et les produits. Ouvre
`caisse/models.py` et remplace son contenu par ceci :

Tu verras tout en haut deux éléments qui ne servent pas encore : l'exception
`EchecEncaissement` (on s'en servira en Partie 3, pour annuler proprement une
vente qui échoue) et la fonction `generer_secret_qr` (utilisée juste en
dessous, dans `Pole`). On les pose maintenant simplement parce qu'il faut
qu'elles existent dans le fichier avant d'être utilisées plus loin, retiens
juste leur nom, on y revient au bon moment.

```python
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
```

Prends un instant pour regarder `Produit`, c'est le modèle le plus riche de ce
premier bloc et quelques-uns de ses champs méritent qu'on s'y arrête.

Tu vois que `Pole`, `Evenement` et `Produit` ont chacun un champ `photo =
models.ImageField(...)`. Pour que Django accepte ce type de champ (et
notamment pour que `makemigrations` plus bas ne plante pas), il a besoin
d'une seule chose à ce stade : la librairie Pillow, qui sait lire et valider
des fichiers image.

```bash
pip install pillow
```

C'est tout ce dont tu as besoin pour l'instant. Pour qu'une photo uploadée
soit vraiment enregistrée quelque part et affichable dans le navigateur, il
manque encore deux réglages (où la stocker, et comment la « servir » à une
page web) — mais ça touche aux URLs du projet, un sujet qu'on n'a pas encore
abordé. On s'en occupe proprement en Partie 3, en même temps qu'on découvre
comment Django route une adresse vers une page. Retiens juste que `pip
install pillow` est fait, le reste attendra son tour.

Regarde aussi `stock = models.IntegerField(null=True, blank=True)`. Le choix
de le rendre `null=True` n'est pas anodin : ça permet à `stock` de valoir
`None`, ce qui veut dire « ce produit n'a pas de stock suivi » (un café qu'on
prépare à la demande, par exemple), une notion complètement différente de
`stock = 0`, qui veut dire « épuisé, plus une seule unité ». Si on avait pris
un `PositiveIntegerField` classique avec une valeur par défaut (0), on aurait
perdu cette distinction : tout produit non renseigné serait apparu comme
épuisé dès sa création, ce qui n'est pas ce qu'on veut.

`retire` et `disponible` se ressemblent mais répondent à deux questions
différentes, et c'est volontaire qu'il y ait deux champs séparés plutôt
qu'un seul. `disponible=False` correspond à une rupture temporaire : le
produit reste visible sur l'écran de vente, juste grisé, avec un badge «
Épuisé ». `retire=True` va plus loin : le produit disparaît complètement de
la vente **et** de la gestion courante, il n'est plus visible que dans un
onglet « Retirés » réservé aux vrais admins (jamais à un simple vendeur, même
s'il a le droit de gérer le catalogue, on verra cette distinction de droits en
Partie 2). Pourquoi ne pas simplement supprimer le produit de la base une
fois qu'on n'en veut plus ? Parce qu'il peut être référencé par de vieilles
lignes de vente (protégées par `PROTECT`, comme expliqué en 1.1), le
supprimer casserait l'historique comptable. On le marque donc « retiré »
plutôt que de le détruire.

Enfin, `est_billet` : ce champ n'a de sens que pour un produit rattaché à un
événement (on détaillera les événements en Partie 6). Il distingue une vraie
entrée, qui compte comme une présence, et qu'on cherchera plus tard à
synchroniser avec HelloAsso, d'un simple produit vendu ce soir-là (une
boisson, un écocup) qui ne représente aucune présence. Ce champ n'existait
pas dans une première version du projet, et son absence avait provoqué une
vraie confusion entre les deux (des boissons comptées comme des entrées) :
on le pose ici dès le départ pour éviter de refaire cette erreur.

**Fais-le vivre en base et dans l'admin.** Ces quatre classes existent pour
l'instant seulement dans le fichier Python, la base de données ne les connaît
pas encore. Deux commandes, à lancer depuis le dossier du projet (celui qui
contient `manage.py`) :

```bash
python manage.py makemigrations
python manage.py migrate
```

`makemigrations` compare `models.py` à l'état de la base et écrit un fichier
de migration dans `caisse/migrations/` (un genre de recette : « crée telle
table, avec telles colonnes ») ; `migrate` exécute réellement cette recette
sur `db.sqlite3`. Les deux commandes sont à relancer **à chaque fois** qu'on
modifie `models.py` dans la suite de ce tutoriel, le réflexe à prendre.

Pour pouvoir les voir et les modifier à la main dans le back-office
(`/admin/`), ouvre `caisse/admin.py` (créé vide par `startapp`) et enregistre
les quatre modèles :

```python
from django.contrib import admin

from .models import Pole, Evenement, Categorie, Produit

admin.site.register(Pole)
admin.site.register(Evenement)
admin.site.register(Categorie)
admin.site.register(Produit)
```

Relance `runserver`, va sur `http://127.0.0.1:8000/admin/`, connecte-toi avec
le compte créé en Partie 0 : les quatre modèles apparaissent maintenant dans
la page d'accueil de l'admin. Crée un premier `Pole` de test directement
depuis cette interface (par exemple « Kfet », slug `kfet`), ça servira dès
la Partie 3 pour tester la vente.

### 1.3 Comptes et argent : `ProfilUtilisateur`, `Recharge`, `Transaction`, `LigneTransaction`

Django a déjà, tout seul, un modèle `User` pour gérer les comptes et la
connexion, c'est lui que tu as utilisé sans le voir en Partie 0 avec
`createsuperuser`, et c'est lui qui gérera plus tard les vrais comptes école
via le CAS (voir Partie 0). Il sait faire l'essentiel (identifiant, mot de
passe, email...), mais il ne connaît rien à notre application : ni solde, ni
carte étudiante, ni QR code. Plutôt que de bricoler un compte parallèle, on
crée un second modèle, `ProfilUtilisateur`, qui vient s'accrocher à chaque
`User` existant et porte tout ce qui est spécifique au portefeuille cashless.

Ce lien « un `User`, et un seul `ProfilUtilisateur` qui lui correspond » est
exactement ce que représente `OneToOneField` (tu verras plus loin, en 1.4,
`ForeignKey`, qui autorise au contraire plusieurs liens vers la même chose,
la nuance entre les deux se clarifiera par l'exemple).

Toujours dans `caisse/models.py`, ajoute ce qui suit à la suite de `Produit`
(tout en bas du fichier, donc) :

```python
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
```

Un détail facile à rater sur `secret_qr = models.CharField(max_length=64,
default=generer_secret_qr)` : on écrit `generer_secret_qr`, **sans les
parenthèses**. Ce n'est pas une coquille, si tu mettais
`default=generer_secret_qr()` (avec les parenthèses), Django appellerait la
fonction **une seule fois**, au moment où il lit le fichier, et donnerait
ensuite ce même résultat comme valeur par défaut à *tous* les profils créés
ensuite : ils partageraient tous le même secret, ce qui casserait
complètement l'intérêt d'un secret propre à chacun. Sans les parenthèses,
Django comprend qu'on lui passe la fonction elle-même, et l'appelle à nouveau
à **chaque** création de profil, un principe à retenir, il revient plusieurs
fois dans ce projet dès qu'un champ a besoin d'une valeur générée
dynamiquement.

`date_naissance` est utilisé dans la page « Infos » de l'étudiant (Partie 5)
et dans plusieurs écrans d'administration (Parties 6, 8, 10).

Enfin, la méthode `anonymiser()` en bas de la classe : c'est elle qui sera
appelée en Partie 10, quand un admin école déclenchera la suppression d'un
compte. Remarque bien ce qu'elle fait, et surtout ce qu'elle **ne fait
pas** : elle ne supprime jamais la ligne dans la base (`self.save()`, pas
`self.delete()`), elle vide seulement les informations personnelles et coupe
l'accès. C'est exactement la même logique que `PROTECT` vue en 1.1 : la ligne
doit survivre pour que l'historique comptable (ventes, recharges, adhésions
liées à ce compte) reste intact et cohérent.

On continue dans le même fichier `caisse/models.py`, toujours à la suite
(sous `ProfilUtilisateur`, donc) : trois modèles de plus, qui représentent
l'argent lui-même — une recharge du portefeuille, un achat, et le détail
d'un ticket d'achat.

```python
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
```

Un dernier mot sur `Recharge.pole`, en bas de cette classe. **Par défaut,
seul un admin ADE peut recharger un portefeuille en espèces**, un simple
admin de pôle ne le peut pas, à moins que l'admin ADE ne lui accorde ce
droit précisément (`droit_recharger_especes`, voir Partie 2). Ce champ n'a
donc rien à voir avec la question « qui a le droit de recharger » : il sert
seulement à savoir **depuis la page de quel pôle** l'argent liquide a été
reçu (l'URL utilisée pour l'opération, ex. `/pole/kfet/especes/`), pour que
la page « Suivi espèces » de chaque pôle (Partie 9) puisse lister tout le
liquide reçu à son guichet.

Sans ce champ, on pourrait être tenté de deviner ce pôle en regardant à quel
pôle est affiliée la personne qui a encaissé. Pour quelqu'un qui a reçu le
droit de recharger sur un seul pôle précis (ex. un admin Kfet autorisé), les
permissions l'empêchent d'utiliser la page d'un autre pôle : deviner via son
affiliation donnerait donc toujours le bon résultat, par construction. Mais
un **admin ADE** peut recharger depuis la page de **n'importe quel** pôle
selon où il se trouve dans la soirée (à la Kfet à un moment, au BDE à un
autre), il manipule bien du vrai liquide, juste à des endroits différents
selon le moment. Comme il n'est affilié à aucun pôle en particulier, deviner
via son affiliation ne fonctionne pas pour lui : chaque recharge qu'il
encaisse se serait mise à apparaître dans le suivi de **tous** les pôles à
la fois, y compris ceux où elle n'a concrètement rien à faire. C'est ce
problème concret (détaillé en Partie 9) qui a motivé d'enregistrer la caisse
**directement** sur la ligne `Recharge`, au moment de l'opération, plutôt
que de la déduire après coup à partir de qui a encaissé.

La leçon à en tirer, utile pour la suite du projet : dès qu'une information
sert de critère de filtrage fiable quelque part, il vaut mieux la stocker
explicitement dans un champ dédié, plutôt que de la déduire indirectement
d'une autre relation.

Comme à la fin de 1.2 :

```bash
python manage.py makemigrations
python manage.py migrate
```

Puis ouvre `caisse/admin.py` et **remplace tout le contenu du fichier** par
ceci (ce n'est pas à ajouter à la suite de ce qui y est déjà : ce bloc
reprend déjà tout ce qu'il y avait avant, plus les quatre nouveaux
modèles) :

```python
from django.contrib import admin

from .models import (
    Pole, Evenement, Categorie, Produit,
    ProfilUtilisateur, Recharge, Transaction, LigneTransaction,
)

admin.site.register(Pole)
admin.site.register(Evenement)
admin.site.register(Categorie)
admin.site.register(Produit)
admin.site.register(ProfilUtilisateur)
admin.site.register(Recharge)
admin.site.register(Transaction)
admin.site.register(LigneTransaction)
```

### 1.4 Rôles : `Affectation`

Toujours le même fichier `caisse/models.py`, à la suite.

```python
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
```

Django propose déjà un système de rôles natif (`django.contrib.auth.models.Group`),
alors pourquoi créer notre propre table `Affectation` plutôt que de l'utiliser
? Parce qu'un rôle dans cette application n'a jamais de sens tout seul : «
vendeur » ne veut rien dire, ce qui compte c'est « vendeur **de la Kfet** ».
Un `Group` Django ne rattache pas nativement un rôle à un objet précis (ici,
un pôle), il aurait fallu bricoler autour. Une table à nous, avec ses propres
champs `user`, `pole` et `role`, colle beaucoup plus naturellement à ce
besoin, et se prête bien au futur système d'attribution par boutons (la page
Équipe, en Partie 7) : donner un droit à quelqu'un revient juste à créer ou
mettre à jour une ligne, le lui retirer revient à la supprimer.

Remarque que `pole` est `null=True, blank=True` : un rôle sans pôle
(`pole=None`) désigne un rôle **global**, celui d'un admin ADE ou d'un admin
école, qui voit et gère tous les pôles à la fois plutôt qu'un seul.

Les sept champs `droit_*` en bas de la classe ne servent à rien pour
l'instant, on ne les utilisera pas avant la Partie 2. Ils sont apparus assez
tard dans le développement réel du projet, une fois qu'un système à seulement
deux niveaux (Vendeur simple / Admin de pôle qui a tout) s'est révélé trop
rigide : il fallait pouvoir accorder un droit précis à un vendeur sans en
faire un admin complet. On les pose ici en même temps que le reste du modèle
pour ne pas avoir à y revenir avec une nouvelle migration plus tard.

Un point à garder en tête pour la Partie 2, où ces champs seront vraiment
utilisés : six d'entre eux (`droit_adhesion_especes`, `droit_gerer_produits`,
`droit_adhesions`, `droit_equipe`, `droit_exporter`, `droit_parametres`) sont
accordables par n'importe quel admin de pôle à ses propres vendeurs. Le
septième, `droit_recharger_especes`, est traité à part : lui seul reste
réservé à l'admin ADE, jamais délégable par un simple admin de pôle, on
verra le pourquoi (une question de qui a le droit de faire confiance à qui
sur la manipulation d'espèces) en Partie 2 et en Partie 7.

Même réflexe qu'à l'étape précédente. D'abord :

```bash
python manage.py makemigrations
python manage.py migrate
```

Puis **remplace tout le contenu** de `caisse/admin.py` (pas ajouter à la
suite) par cette nouvelle version, qui reprend tout ce qui précède plus
`Affectation` :

```python
from django.contrib import admin

from .models import (
    Pole, Evenement, Categorie, Produit,
    ProfilUtilisateur, Recharge, Transaction, LigneTransaction,
    Affectation,
)

admin.site.register(Pole)
admin.site.register(Evenement)
admin.site.register(Categorie)
admin.site.register(Produit)
admin.site.register(ProfilUtilisateur)
admin.site.register(Recharge)
admin.site.register(Transaction)
admin.site.register(LigneTransaction)
admin.site.register(Affectation)
```

### 1.5 Paiement par QR code : `JetonPaiement`

Toujours dans `caisse/models.py`.

```python
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
```

Le principe imite Izly : le QR affiché à l'écran de l'étudiant change à chaque
rafraîchissement et expire en 2 minutes, pour qu'une capture d'écran ne puisse
pas être rejouée plus tard.

```bash
python manage.py makemigrations
python manage.py migrate
```

Puis, encore une fois, **remplace tout le contenu** de `caisse/admin.py`
(pas ajouter à la suite) par :

```python
from django.contrib import admin

from .models import (
    Pole, Evenement, Categorie, Produit,
    ProfilUtilisateur, Recharge, Transaction, LigneTransaction,
    Affectation, JetonPaiement,
)

admin.site.register(Pole)
admin.site.register(Evenement)
admin.site.register(Categorie)
admin.site.register(Produit)
admin.site.register(ProfilUtilisateur)
admin.site.register(Recharge)
admin.site.register(Transaction)
admin.site.register(LigneTransaction)
admin.site.register(Affectation)
admin.site.register(JetonPaiement)
```

À ce stade tu as vu le motif quatre fois de suite : à chaque nouveau modèle,
on relance `makemigrations`/`migrate` et on l'ajoute aux deux listes de
`admin.py`. La dernière section de cette partie (1.6, cinq modèles d'un
coup) regroupera les imports et les enregistrements dans une boucle plutôt
que de tout réécrire une nouvelle fois à la main.

### 1.6 Événements externes, adhésions, sécurité des comptes à pouvoir, suppression de compte, tarifs

Dernière section de la Partie 1 : cinq modèles de plus, toujours à la suite
dans `caisse/models.py`. Comme toujours, `makemigrations`/`migrate` et
enregistrement dans `caisse/admin.py` une fois les cinq classes écrites, les
détails sont donnés une dernière fois juste après le code, pour cette
section.

```python
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
```

Regarde la ligne `unique_together = [("pole", "profil", "annee")]` dans la
`class Meta` d'`Adhesion`. On aurait pu se contenter de vérifier « est-ce que
cette personne a déjà payé cette année ? » dans le code Python de la vue,
avant de créer la ligne. Mais une vérification en Python peut toujours être
contournée par un bug ailleurs dans le code, ou par deux requêtes qui
arrivent en même temps (voir la Partie 3 sur la concurrence). `unique_together`
pose la règle **directement dans la base de données** : même si le code
Python essayait malgré tout de créer une deuxième ligne identique, la base
refuserait purement et simplement l'écriture. C'est le niveau de garantie
qu'on veut pour un invariant aussi important que « pas de double paiement ».
Ce refus remonte côté Python sous la forme d'une erreur `IntegrityError`, que
les vues (Partie 8) attrapent pour afficher un message clair à l'utilisateur
plutôt que de laisser un plantage brut s'afficher.

```python
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
```

Un mot sur `TarifAdhesion`, le dernier modèle de cette partie. Dans une
version antérieure du projet, un pôle n'avait qu'un seul prix d'adhésion,
stocké directement dans un champ `Pole.prix_adhesion`. Le jour où il a fallu
proposer plusieurs tarifs (« 1ère année » à 5€, « Ancien élève » à 10€...),
il a fallu faire évoluer le modèle, mais pas n'importe comment. Si on avait
simplement supprimé `Pole.prix_adhesion` pour le remplacer par ce nouveau
modèle, tous les prix déjà enregistrés pour les pôles existants auraient été
perdus d'un coup, à la première migration. C'est ce genre de situation
(passer d'un champ simple à une relation vers un nouveau modèle, sur des
données qui existent déjà) qui demande une **migration de données**, pas
seulement une migration de schéma : une étape intermédiaire qui recopie
l'information de l'ancien endroit vers le nouveau, avant de supprimer
l'ancien. **Rien à taper ni à exécuter pour ça ici** : dans cette
reconstruction, tu écris `TarifAdhesion` directement comme ci-dessus, tu n'es
jamais passé par un champ `Pole.prix_adhesion` — ce champ n'existera donc
jamais dans ta version du projet. Ce qui suit est juste la démarche à
connaître pour le jour où *toi* tu devras faire évoluer un champ existant
sans perdre de données, à titre de culture générale, pas une étape de ce
tutoriel :

1. Créer le nouveau modèle (`TarifAdhesion`), sans toucher à l'ancien champ.
2. Une migration de **données** (`RunPython`) qui convertit chaque ancienne
   valeur en une nouvelle ligne du nouveau modèle, avec une fonction inverse
   symétrique pour pouvoir revenir en arrière sans perte.
3. Seulement ensuite, une migration de **schéma** qui retire l'ancien champ,
   une fois les données en sécurité ailleurs.

On reprend maintenant la construction normale : les cinq modèles de cette
section sont posés, il ne reste qu'à les faire vivre en base.

```bash
python manage.py makemigrations
python manage.py migrate
```

Une dernière fois, **remplace tout le contenu** de `caisse/admin.py` (pas
ajouter à la suite) par cette version, qui couvre les 15 modèles du
projet :

```python
from django.contrib import admin

from .models import (
    Pole, Evenement, Categorie, Produit,
    ProfilUtilisateur, Recharge, Transaction, LigneTransaction,
    Affectation, JetonPaiement,
    ParticipantImporte, Adhesion, CodeSecuriteAdmin,
    DemandeSuppressionCompte, TarifAdhesion,
)

for modele in (
    Pole, Evenement, Categorie, Produit,
    ProfilUtilisateur, Recharge, Transaction, LigneTransaction,
    Affectation, JetonPaiement,
    ParticipantImporte, Adhesion, CodeSecuriteAdmin,
    DemandeSuppressionCompte, TarifAdhesion,
):
    admin.site.register(modele)
```

(On regroupe ici tous les modèles du projet en une seule boucle plutôt que
quinze lignes `admin.site.register(...)` répétées, les deux fonctionnent
rigoureusement pareil, c'est juste plus court à relire une fois qu'on a
autant de modèles.)

À ce stade, `caisse/models.py` contient les 15 modèles du projet, la base est
à jour, et `/admin/` permet de tous les inspecter et de créer des données de
test à la main. C'est la fin de la Partie 1, le reste du tutoriel (Parties 2
et suivantes) construit les vues et les pages qui utilisent ces modèles, sans
plus jamais revenir modifier `models.py` sauf mention explicite.

---

## Partie 2 - Rôles et permissions

**Nouveau fichier :** crée `caisse/roles.py` (il n'existe pas encore, c'est
un fichier normal à côté de `models.py` et `views.py`, rien de spécial à
faire pour qu'il soit reconnu, un simple fichier `.py` dans le dossier de
l'app est automatiquement importable). Il regroupe **toutes** les fonctions «
que peut faire cet utilisateur ? », pour que les vues restent lisibles et
qu'on ne répète jamais la même logique de permission à deux endroits.

```python
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
    role attribue a une ou deux personnes (Vie de campus, etc.)."""
    return user.is_superuser or user.affectations.filter(role="ADMIN_ECOLE").exists()


def annee_scolaire_courante():
    """L'annee scolaire va d'aout a aout : d'aout a decembre, c'est
    l'annee civile en cours ; de janvier a juillet, c'est encore l'annee
    civile precedente."""
    aujourdhui = timezone.localdate()
    if aujourdhui.month >= 8:
        return aujourdhui.year
    return aujourdhui.year - 1
```

### 2.1 Comment ce système a été pensé (ordre d'introduction)

1. **D'abord un système à trois rôles fixes** : `VENDEUR` / `ADMIN_POLE` /
   `ADMIN_ADE`, chacun rattaché (ou non) à un pôle. `poles_vendables` /
   `poles_gerables` / `peut_vendre` / `peut_gerer` datent de cette étape
   initiale (Partie 0 du développement historique).
2. **Puis un rôle `ADMIN_ECOLE`** séparé, volontairement :
   `est_admin_ecole` (voir Partie 10).
3. **Enfin, les droits à la carte** (les 6 booléens de `Affectation`) :
   passage d'un système binaire (Vendeur simple / Admin complet) à des droits
   accordables individuellement à un vendeur, tuile par tuile, **sans le faire
   passer admin**. `_a_droit_supplementaire` est le point d'entrée commun à
   toutes les fonctions `peut_*` : chacune vérifie d'abord `peut_gerer` (déjà
   tout), puis se rabat sur le droit supplémentaire spécifique.

**Une exception volontaire et documentée : « Équipe » reste spécial.**
`peut_voir_equipe` peut être accordé à un vendeur (voir qui a quels droits),
mais `peut_modifier_equipe` reste **toujours** réservé à un admin, quoi qu'il
arrive. Sans cette règle, un vendeur ayant reçu le droit de voir l'équipe
pourrait s'auto-attribuer (ou attribuer à un collègue) n'importe quel droit,
y compris redevenir admin - un vrai risque d'escalade de privilèges.

**Autre garde-fou serveur (pas seulement dans l'interface) :** dans la vue
`equipe_pole` (Partie 7), `droit_recharger_especes` n'est appliqué que si
`admin_ade` est vrai côté serveur, même si le formulaire est techniquement
accessible à un admin de pôle. Ne jamais faire confiance à ce qui est caché
côté client.

### 2.2 `context_processors.py` : les droits partout, sans répétition

**Le problème que ça résout.** Plus tard dans ce tutoriel (Partie 13), la
barre de navigation en bas de chaque page (dans `base.html`) doit savoir, sur
**n'importe quelle page** de l'application, si l'utilisateur connecté a le
droit de voir les onglets « Asso », « Terminal » et « École ». Sans rien de
spécial, il faudrait que **chaque vue** (`accueil`, `detail_pole`,
`gerer_produits`, et toutes les autres, il y en a des dizaines dans ce
projet) recalcule elle-même `poles_vendables(user).exists()` et la transmette
dans son `render(request, ..., {...})`, un copier-coller répété partout,
avec le risque d'oublier une vue et de casser l'affichage de la barre juste
sur cette page-là.

Un **context processor** Django résout exactement ce problème : c'est une
fonction qui s'exécute automatiquement à **chaque** page rendue, quelle que
soit la vue, et dont le résultat est ajouté au contexte de tous les
templates sans que rien n'ait besoin de le demander explicitement. On
l'écrit une seule fois, on le branche une seule fois dans `settings.py`, et
il s'applique partout.

Crée un nouveau fichier `caisse/context_processors.py` :

```python
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
```

Cette fonction renvoie un dictionnaire : les clés (`a_droits_vente`,
`a_droits_terminal`, `est_admin_ecole`) deviendront directement utilisables
dans **n'importe quel template**, comme `{{ a_droits_vente }}` ou
`{% if est_admin_ecole %}`, sans qu'aucune vue n'ait à les transmettre.

Il reste à dire à Django que cette fonction existe et doit être appelée à
chaque page. Ouvre `cashless/settings.py` et repère le bloc `TEMPLATES`
(déjà présent, généré par `startproject`), à l'intérieur,
`OPTIONS["context_processors"]` est une liste de fonctions de ce type,
Django en fournit déjà quelques-unes par défaut. **Ajoute une seule ligne**,
la dernière, à cette liste existante :

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'caisse.context_processors.droits_navigation',  # <- la seule ligne a ajouter
            ],
        },
    },
]
```

Les autres lignes de ce bloc, tu ne les touches pas : elles étaient déjà là
avant. Le résultat concret de tout ça n'aura vraiment de sens visuellement
qu'en Partie 13, quand `base.html` utilisera ces variables pour décider quels
onglets afficher, pour l'instant, on pose juste la plomberie.

---

## Partie 3 - La vente : panier, encaissement, concurrence

### 3.0 Le trio Vue / URL, et la fin de la config média

Jusqu'ici, on n'a écrit que des modèles (Partie 1) et des fonctions de
permission (Partie 2) : rien qui réponde encore à une page web. Il manque
deux pièces, et elles vont toujours ensemble :

- une **vue** : une fonction Python qui reçoit une requête et renvoie une
  réponse (une page HTML, une redirection...), c'est ce qu'on commence à
  écrire dans cette Partie 3, dans un nouveau fichier `caisse/views.py` (créé
  vide par `startapp`, comme `models.py` l'était) ;
- une **URL** : l'adresse tapée dans le navigateur, associée à la vue qui
  doit y répondre, ça se déclare dans un fichier `urls.py`, qu'on va créer
  ci-dessous.

Crée le fichier `caisse/urls.py`  :

```python
from django.urls import path

from . import views

urlpatterns = [
    path("pole/<slug:slug>/", views.detail_pole, name="detail_pole"),
    path("ajouter/<int:produit_id>/", views.ajouter_au_panier, name="ajouter_au_panier"),
    path("pole/<slug:slug>/encaisser/", views.encaisser, name="encaisser"),
]
```

`urlpatterns` est une liste de correspondances URL → vue. `path("ajouter/<int:produit_id>/",
views.ajouter_au_panier, name="ajouter_au_panier")` se lit : « une adresse
qui ressemble à `/ajouter/12/` doit être traitée par la fonction
`ajouter_au_panier` de `views.py`, et on lui donne le petit nom
`ajouter_au_panier` pour pouvoir la retrouver facilement ailleurs dans le
code (via `reverse(...)` ou `{% url %}` dans un template) sans avoir à
retaper l'adresse en dur ». `<slug:slug>` et `<int:produit_id>` sont des
morceaux variables de l'URL, capturés et transmis à la vue comme arguments.
On ajoutera une ligne à cette liste à chaque nouvelle vue introduite dans la
suite du tutoriel.

Il reste à relier ce fichier au projet. Ouvre `cashless/urls.py` (déjà
modifié en Partie 1.2 pour la config média) et remplace-le par :

```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("caisse.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

La nouveauté par rapport à la Partie 1 : l'import `include`, et la ligne
`path("", include("caisse.urls"))`, qui délègue toutes les adresses (le `""`
au début) au fichier qu'on vient de créer. Cette fois `caisse/urls.py`
existe bel et bien, donc plus de `ModuleNotFoundError`.

Il reste un détail laissé en suspens en Partie 1 : pour qu'une photo
uploadée soit réellement enregistrée quelque part et servie au navigateur en
développement, ajoute dans `cashless/settings.py` (`MEDIA_URL`/`MEDIA_ROOT`
utilisés dans le bloc `if settings.DEBUG` ci-dessus) :

```python
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
```

Une dernière chose avant d'écrire du code de vente : toutes les pages de ce
projet héritent d'un gabarit commun, `base.html` (barre de navigation, style
Bootstrap...). Ce fichier va grossir tout au long du tutoriel — sa version
finale n'apparaît que tout à la fin (Partie 13.5) — mais il doit exister dès
maintenant, sinon rien ne peut s'afficher.

D'abord, une vue minimaliste pour l'accueil, qui sera reprise et détaillée
en Partie 5.3 (pour l'instant, elle se contente d'exister) :

```python
@login_required
def accueil(request):
    return render(request, "caisse/accueil.html", {})
```

Ajoute la route correspondante en tête de `caisse/urls.py` :

```python
path("", views.accueil, name="accueil"),
```

Et deux templates minimalistes, à compléter plus tard. D'abord
`caisse/templates/caisse/accueil.html` :

```html
{% extends "caisse/base.html" %}
{% block titre %}Accueil{% endblock %}
{% block contenu %}
    <h1>Bienvenue</h1>
{% endblock %}
```

Puis `caisse/templates/caisse/base.html`, une version volontairement
réduite : pas encore de barre d'onglets en bas (elle sera ajoutée
progressivement, au fur et à mesure que les pages qu'elle pointe existeront
réellement — Terminal à la fin de cette Partie 3, Payer/Recharger/Info en
Partie 5, Asso en Partie 7, École en Partie 10), juste la structure et la
barre du haut :

```html
{% load static %}
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <title>{% block titre %}Caisse{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {
            --ensea: #C8004B;
            --ensea-dark: #960038;
            --ensea-light: #FFF0F4;
        }
        body { background-color: #F8F9FA; padding-bottom: 80px; }
        .btn-primary { --bs-btn-bg: var(--ensea); --bs-btn-border-color: var(--ensea); --bs-btn-hover-bg: var(--ensea-dark); --bs-btn-hover-border-color: var(--ensea-dark); --bs-btn-active-bg: var(--ensea-dark); --bs-btn-active-border-color: var(--ensea-dark); }
        .bg-primary { background-color: var(--ensea) !important; }
        .text-ensea { color: var(--ensea); }
    </style>
</head>
<body>
    <nav class="navbar bg-white shadow-sm mb-3">
        <div class="container">
            <a class="navbar-brand fw-bold text-ensea" href="{% url 'accueil' %}">Mon portefeuille ENSEA</a>
            {% if user.is_authenticated %}
                <form method="post" action="{% url 'logout' %}" class="d-inline">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-outline-secondary btn-sm">Déconnexion</button>
                </form>
            {% else %}
                <a href="{% url 'login' %}" class="btn btn-outline-secondary btn-sm">Connexion</a>
            {% endif %}
        </div>
    </nav>

    <main class="container">
        {% block contenu %}{% endblock %}
    </main>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

Ce fichier référence `{% url 'login' %}` et `{% url 'logout' %}` — et
celles-ci, contrairement au reste de l'authentification (détaillé en
Partie 4.1), doivent exister **dès maintenant** : dès que tu es connecté
(même juste via `/admin/`, avec le compte créé en Partie 0 — la connexion
Django est partagée entre l'admin et le reste du site), cette barre du haut
s'affiche sur chaque page et a besoin de la route `logout` pour son
formulaire de déconnexion.

Ajoute l'import et les deux routes en tête de `caisse/urls.py` :

```python
from django.contrib.auth import views as auth_views
```

```python
path("connexion/", auth_views.LoginView.as_view(template_name="caisse/login.html"), name="login"),
path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
```

Et le template attendu par `LoginView`, `caisse/templates/caisse/login.html`
(`LogoutView` n'a besoin d'aucun template : elle déconnecte et redirige
directement) :

```html
{% extends "caisse/base.html" %}

{% block titre %}Connexion{% endblock %}

{% block contenu %}
    <div class="row justify-content-center">
        <div class="col-md-4">
            <h1 class="mb-4">Connexion</h1>
            {% if form.errors %}
                <div class="alert alert-danger">Identifiant ou mot de passe incorrect.</div>
            {% endif %}
            <form method="post">
                {% csrf_token %}
                <label class="form-label">Identifiant</label>
                <input type="text" name="username" class="form-control mb-3" autofocus>
                <label class="form-label">Mot de passe</label>
                <input type="password" name="password" class="form-control mb-3">
                <button type="submit" class="btn btn-primary w-100">Se connecter</button>
            </form>
        </div>
    </div>
{% endblock %}
```

(La vraie configuration de la connexion, comme le fait de rediriger vers une
page précise après connexion, arrive juste après en Partie 4.1 — pour
l'instant, ces deux routes suffisent à ce que `base.html` fonctionne.)

Voilà, la mécanique de base est en place. Passe maintenant à `caisse/views.py`
pour écrire la première vraie fonctionnalité : le panier.

### 3.1 Le panier : une session, pas une table

Le panier est stocké dans `request.session["panier"]`, un dictionnaire
`{ "id_produit": quantite }`. Aucune table SQL n'est nécessaire tant que la
vente n'est pas validée : le panier est une donnée **temporaire**, propre à
la session du navigateur.

Ouvre `caisse/views.py` (vide pour l'instant, créé par `startapp`) : c'est le
tout premier code que tu y écris. Commence par ces imports, tout en haut du
fichier, on en ajoutera d'autres au fil du tutoriel à mesure que de
nouvelles fonctionnalités en auront besoin, pas la peine de tout prévoir
d'un coup :

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Produit
```

Puis, à la suite :

```python
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
```

**Le formulaire d'ajout est en POST**, jamais en GET : c'est une modification
d'état (le panier change), la sémantique HTTP l'impose. Le `{% csrf_token %}`
est obligatoire sur tout formulaire POST, Django refuse la requête sinon,
c'est une protection contre les attaques CSRF (un site tiers qui ferait
soumettre un formulaire à l'insu de l'utilisateur connecté).

Après un `POST` réussi, on **redirige** (`redirect(...)`, jamais `render(...)`
directement) : c'est le motif *Post/Redirect/Get*, qui évite qu'un
rafraîchissement de page (F5) ne resoumette accidentellement le même
formulaire une deuxième fois.

`cat_active` transite dans un champ caché du formulaire, pour que
l'utilisateur reste sur l'onglet catégorie qu'il consultait après avoir
ajouté un article, sans ce détail, chaque ajout renvoyait à l'écran de choix
de catégorie, ce qui était pénible pour un vendeur qui enchaîne les ajouts.

Deux petites vues de plus, toujours à la suite dans `caisse/views.py` : voir
le panier sur sa propre page, et le vider d'un coup.

```python
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
```

Il faut maintenant un template pour `voir_panier`. Crée
`caisse/templates/caisse/panier.html` (le dossier `caisse/templates/caisse/`
n'existe pas encore : crée-le aussi, c'est là que vivront tous les templates
de l'app) :

```html
{% extends "caisse/base.html" %}

{% block titre %}Panier{% endblock %}

{% block contenu %}
    <a href="{% url 'detail_pole' pole.slug %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <h1 class="mb-4">Panier - {{ pole.nom }}</h1>

    {% if lignes_panier %}
        <div class="card shadow-sm mb-3">
            <ul class="list-group list-group-flush">
                {% for ligne in lignes_panier %}
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <span>{{ ligne.quantite }} x {{ ligne.produit.nom }}</span>
                        <span class="fw-bold">{{ ligne.sous_total }} EUR</span>
                    </li>
                {% endfor %}
            </ul>
            <div class="card-footer d-flex justify-content-between align-items-center fs-5 fw-bold">
                <span>Total</span>
                <span>{{ total }} EUR</span>
            </div>
        </div>

        <div class="d-flex gap-2">
            <a href="{% url 'vider_panier' pole.slug %}" class="btn btn-outline-danger flex-fill">Vider</a>
            <a href="{% url 'encaisser' pole.slug %}" class="btn btn-success flex-fill">Encaisser</a>
        </div>
    {% else %}
        <p class="text-muted">Le panier est vide.</p>
        <a href="{% url 'detail_pole' pole.slug %}" class="btn btn-primary">Retour aux produits</a>
    {% endif %}
{% endblock %}
```

Enfin, ajoute les deux nouvelles routes dans `caisse/urls.py` (à la suite de
la liste déjà commencée en 3.0) :

```python
path("pole/<slug:slug>/vider/", views.vider_panier, name="vider_panier"),
path("pole/<slug:slug>/panier/", views.voir_panier, name="voir_panier"),
```

### 3.2 Affichage du catalogue par catégories, avec la navigation en deux temps

Toujours dans `caisse/views.py`, à la suite de ce que tu viens
d'écrire (jamais un nouveau fichier, sauf mention explicite contraire,
c'est la règle dans ce tutoriel).

Cette vue a besoin de deux choses que tu n'as pas encore importées : le
modèle `Pole`, et `peut_vendre` (la fonction de permission écrite en Partie
2, dans `caisse/roles.py`). Complète tes imports, en haut du fichier :

```python
from django.core.exceptions import PermissionDenied

from .models import Pole, Produit
from .roles import peut_vendre
```

(`Produit` était déjà importé depuis la Partie 3.1 ; la ligne ci-dessus le
remplace simplement pour inclure `Pole` au passage, inutile de garder les
deux lignes séparées.)

Puis, à la suite du reste du fichier :

```python
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
```

Le fait que **les billets d'un événement actif deviennent leur propre groupe
sélectionnable**, exactement comme une catégorie normale, est un choix
d'architecture délibéré et important : un billet est juste un `Produit`
normal avec `evenement` renseigné, donc **tout le reste du système (panier,
décrément de stock, anti-survente, export Excel) fonctionne sans
modification supplémentaire**. Désactiver un événement (`actif=False`) le
fait disparaître immédiatement de la caisse, sans rien à changer côté vente.

`cat_active is None` (aucun paramètre `?cat=` dans l'URL) affiche uniquement
les cases de catégories, sans liste de produits : un piège classique de
Django est ici évité, un `{% for %}` sur une valeur `None` déclenche
silencieusement le bloc `{% empty %}` du template, ce qui produisait
autrefois un message dupliqué. La solution est de distinguer explicitement
les trois cas côté template (`{% if groupes is None %}` / `{% elif not
groupes %}` / `{% else %}`), jamais de laisser `{% for %}...{% empty %}`
trancher seul.

Il faut maintenant le template que `detail_pole` affiche. Crée
`caisse/templates/caisse/pole.html` :

```html
{% extends "caisse/base.html" %}

{% block titre %}{{ pole.nom }}{% endblock %}

{% block contenu %}
    <div class="d-flex justify-content-between align-items-center mb-3">
        <a href="{% url 'accueil' %}" class="btn btn-outline-secondary btn-sm">&lsaquo; Retour</a>
        <a href="{% url 'voir_panier' pole.slug %}" class="btn btn-success rounded-pill d-flex align-items-center gap-2 px-3 py-2">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/></svg>
            <span class="fw-bold">Panier</span>
            {% if nb_articles %}<span class="badge bg-light text-success rounded-circle">{{ nb_articles }}</span>{% endif %}
        </a>
    </div>
    <h1 class="mb-4">{{ pole.nom }}</h1>

    <div class="row">
        <!-- Colonne des produits -->
        <div class="col-lg-8">
            <div class="row g-2 mb-4">
                <div class="col-4 col-md-3">
                    <a href="?cat=tous" class="text-decoration-none">
                        <div class="card text-center shadow-sm h-100 {% if cat_active == 'tous' %}bg-primary text-white{% endif %}" style="aspect-ratio:1;">
                            <div class="card-body d-flex align-items-center justify-content-center p-2">
                                <span class="fw-bold">Tous</span>
                            </div>
                        </div>
                    </a>
                </div>
                {% for onglet in onglets %}
                    <div class="col-4 col-md-3">
                        <a href="?cat={{ onglet.id }}" class="text-decoration-none">
                            <div class="card text-center shadow-sm h-100 {% if cat_active == onglet.id %}bg-primary text-white{% endif %}" style="aspect-ratio:1;">
                                <div class="card-body d-flex align-items-center justify-content-center p-2">
                                    <span class="fw-bold">{{ onglet.nom }}</span>
                                </div>
                            </div>
                        </a>
                    </div>
                {% endfor %}
            </div>

            {% if groupes is None %}
                <p class="text-muted">Choisis une catégorie ci-dessus.</p>
            {% elif not groupes %}
                <p class="text-muted">Aucun produit dans ce pôle.</p>
            {% else %}
                {% for groupe in groupes %}
                    <h4 class="mt-3 mb-2">{{ groupe.nom }}</h4>
                    <div class="row g-3">
                        {% for produit in groupe.produits %}
                            <div class="col-6 col-md-4">
                                <div class="card h-100 shadow-sm {% if not produit.disponible or produit.stock == 0 %}opacity-50{% endif %}">
                                    {% if produit.photo %}
                                        <img src="{{ produit.photo.url }}" class="card-img-top p-2" style="height:140px; object-fit:contain;" alt="{{ produit.nom }}">
                                    {% endif %}
                                    <div class="card-body text-center">
                                        <h6 class="card-title mb-1">{{ produit.nom }}</h6>
                                        <p class="fw-bold mb-1">{{ produit.prix }} EUR</p>
                                        {% if not produit.disponible or produit.stock == 0 %}
                                            <span class="badge bg-danger">Epuise</span>
                                        {% else %}
                                            {% if produit.stock %}
                                                <p class="small mb-2 {% if produit.stock <= 3 %}text-danger fw-bold{% else %}text-muted{% endif %}">Reste {{ produit.stock }}</p>
                                            {% endif %}
                                            <form method="post" action="{% url 'ajouter_au_panier' produit.id %}">
                                                {% csrf_token %}
                                                <input type="hidden" name="cat_active" value="{{ cat_active|default:'' }}">
                                                <div class="input-group input-group-sm mb-1">
                                                    <button type="button" class="btn btn-outline-secondary" onclick="ajuster(this,-1)">-</button>
                                                    <input type="number" name="quantite" value="1" min="1" {% if produit.stock %}max="{{ produit.stock }}"{% endif %} class="form-control text-center qte">
                                                    <button type="button" class="btn btn-outline-secondary" onclick="ajuster(this,1)">+</button>
                                                </div>
                                                <button type="submit" class="btn btn-primary btn-sm w-100">Ajouter</button>
                                            </form>
                                        {% endif %}
                                    </div>
                                </div>
                            </div>
                        {% endfor %}
                    </div>
                {% endfor %}
            {% endif %}
        </div>

        <!-- Colonne du panier -->
        <div class="col-lg-4 mt-4 mt-lg-0">
            <div class="card shadow-sm">
                <div class="card-body text-center">
                    {% if lignes_panier %}
                        <div class="d-flex justify-content-between fw-bold">
                            <span>Total</span>
                            <span>{{ total }} EUR</span>
                        </div>
                    {% else %}
                        <p class="text-muted mb-0">Panier vide</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
{% endblock %}

{% block scripts %}
<script>
function ajuster(bouton, delta) {
    const input = bouton.parentElement.querySelector('.qte');
    let v = parseInt(input.value) + delta;
    const max = input.getAttribute('max');
    if (v < 1) v = 1;
    if (max && v > parseInt(max)) v = parseInt(max);
    input.value = v;
}
</script>
{% endblock %}
```

(Cette version simplifiée n'affiche pas encore le compte à rebours des
événements à durée limitée ni le badge de quantité sur le bouton Panier,
des détails ajoutés plus tard sans changer la structure — inutile de s'y
arrêter maintenant. Le bouton « Retour » pointe provisoirement vers
`accueil` : il pointera vers `espace_asso` une fois cette page construite,
en Partie 7 — pense à revenir corriger cette ligne à ce moment-là.)

### 3.3 L'encaissement : la seule vraie section « argent »

C'est la partie la plus sensible du projet : toute erreur ici peut créer de
l'argent, en perdre, ou survendre un produit en rupture. Trois règles
absolues :

1. **Toute écriture financière est enveloppée dans `db_transaction.atomic()`**
   : soit toutes les écritures liées (débit étudiant + crédit pôle +
   décrément stock + création du ticket) réussissent ensemble, soit
   **aucune** n'a lieu. Pas d'état intermédiaire incohérent possible.
2. **`select_for_update()` verrouille les lignes concernées** (le profil
   acheteur, chaque produit) le temps de la transaction : si deux caisses
   tentent de vendre en même temps le dernier exemplaire d'un produit, la
   seconde attend son tour au lieu de lire un stock périmé.
3. **On revérifie tout à partir de données fraîches juste avant d'écrire**,
   jamais à partir de ce qui a été lu au moment du remplissage du panier :
   entre-temps, une autre caisse a pu vendre les dernières unités.

Toujours dans `caisse/views.py`, à la suite. Complète d'abord les imports en
haut du fichier :

```python
from django.db import transaction as db_transaction
from django.db.utils import OperationalError

from .models import EchecEncaissement, JetonPaiement, LigneTransaction, Pole, Produit, ProfilUtilisateur, Transaction
from .helloasso import inscrire_sur_helloasso
from .recus import envoyer_recu
```

(La ligne `from .models import ...` remplace celle, plus courte, écrite en
3.2, elle contient maintenant tous les modèles utilisés jusqu'ici.)

Les deux derniers imports pointent vers des fichiers qui n'existent pas
encore : `inscrire_sur_helloasso` (l'intégration avec la billetterie externe,
détaillée en Partie 6.4) et `envoyer_recu` (l'email de reçu, détaillé en
Partie 11). Pour que le code ci-dessous tourne dès maintenant sans attendre
d'avoir construit ces deux fonctionnalités, crée deux fichiers minimaux,
qu'on complétera plus tard :

```python
# caisse/helloasso.py
def inscrire_sur_helloasso(evenement, profil, quantite):
    """Version provisoire : ne fait rien pour l'instant. Sera completee en
    Partie 6.4 pour vraiment pousser l'inscription vers HelloAsso."""
    return None
```

```python
# caisse/recus.py
def envoyer_recu(transaction):
    """Version provisoire : ne fait rien pour l'instant. Sera completee en
    Partie 11 pour envoyer un vrai email de recu."""
    pass
```

Avec ça, tout le code suivant fonctionne dès maintenant, les deux
fonctions seront simplement sans effet visible jusqu'à ce qu'on les
implémente pour de vrai, plus tard dans ce tutoriel.

```python
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
```

**`EchecEncaissement` est une exception métier maison**, pas une exception
Python générique : elle porte un message directement affichable au vendeur,
et son unique rôle est de déclencher proprement l'annulation du bloc
`atomic()` (aucune écriture partielle ne subsiste) puis d'être rattrapée pour
afficher le message.

**SQLite et la concurrence.** SQLite ne verrouille pas ligne par ligne : par
défaut, deux écritures strictement simultanées se percutent avec une erreur
immédiate (`OperationalError`) plutôt que d'attendre. On configure un délai
d'attente pour lisser ce comportement en développement.

Ouvre `cashless/settings.py` et repère le bloc `DATABASES` (déjà présent,
généré par `startproject` avec juste `ENGINE` et `NAME`). Remplace-le par
cette version, qui ajoute `OPTIONS` :

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {"timeout": 20},
    }
}
```

Cette limite de SQLite reste **connue et assumée** : PostgreSQL sera
nécessaire pour une vraie mise en production avec plusieurs caisses
simultanées (voir Partie 14).

**Aucun solde exact n'est jamais montré au vendeur**, ni en cas de succès
(`vente_ok.html` n'affiche pas le nouveau solde), ni en cas d'échec (le
message ne révèle que le montant demandé, une donnée publique, jamais le
solde disponible). Seul le propriétaire du compte voit son propre solde, sur
sa page d'accueil personnelle.

Deux templates encore pour que tout ça s'affiche. D'abord
`caisse/templates/caisse/encaisser.html` :

```html
{% extends "caisse/base.html" %}

{% block titre %}Encaisser{% endblock %}

{% block contenu %}
    <a href="{% url 'detail_pole' pole.slug %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <h1 class="mb-4">Encaisser</h1>

    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card shadow-sm mb-3">
                <div class="card-header fw-bold">Récapitulatif</div>
                <ul class="list-group list-group-flush">
                    {% for ligne in lignes_panier %}
                        <li class="list-group-item d-flex justify-content-between">
                            <span>{{ ligne.quantite }} x {{ ligne.produit.nom }}</span>
                            <span>{{ ligne.sous_total }} EUR</span>
                        </li>
                    {% endfor %}
                </ul>
                <div class="card-footer d-flex justify-content-between fw-bold">
                    <span>Total</span>
                    <span>{{ total }} EUR</span>
                </div>
            </div>

            {% if erreur %}
                <div class="alert alert-danger">{{ erreur }}</div>
            {% endif %}

            <form method="post" id="formEncaisser">
                {% csrf_token %}
                <input type="hidden" name="jeton" id="champJeton">
                <button type="button" class="btn btn-outline-primary w-100 mb-2" id="btnScannerQR">
                    Scanner le QR de l'acheteur
                </button>
                <label class="form-label">Identifiant de l'acheteur</label>
                <input type="text" name="identifiant" class="form-control mb-3" placeholder="compte école" autofocus>
                <button type="submit" class="btn btn-success w-100">Valider le paiement de {{ total }} EUR</button>
            </form>
        </div>
    </div>

    {% include "caisse/_scan_qr.html" %}
{% endblock %}
```

`{% include "caisse/_scan_qr.html" %}` en bas de page fait référence au
fragment de scan QR — tu le crées juste après, en 3.4, mais tu peux déjà
écrire ce fichier maintenant, ça ne posera pas d'erreur tant que tu n'as pas
essayé de scanner (l'`{% include %}` échouerait seulement si le fichier
n'existait vraiment pas au moment du rendu).

Ensuite `caisse/templates/caisse/vente_ok.html`, affiché après un paiement
réussi (que ce soit depuis `encaisser` ou depuis le terminal, en 3.5) :

```html
{% extends "caisse/base.html" %}

{% block titre %}Paiement accepté{% endblock %}

{% block contenu %}
    <div class="row justify-content-center">
        <div class="col-md-6 text-center">
            <div class="card shadow-sm">
                <div class="card-body py-5">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" class="mb-3">
                        <circle cx="12" cy="12" r="10" fill="#ECFDF5"/>
                        <path d="M8 12.5l2.5 2.5L16 9" stroke="#10B981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <div class="display-6 text-success mb-3">
                        Achat effectué par
                        {% if profil.user.first_name or profil.user.last_name %}{{ profil.user.first_name }} {{ profil.user.last_name }}{% else %}{{ profil.user.username }}{% endif %}
                    </div>
                    <p class="fs-4 fw-bold mb-3">{{ vente.montant_total|floatformat:2 }} EUR</p>
                    {% if profil.user.email %}
                        <p class="text-muted small">Un reçu a été envoyé par mail.</p>
                    {% endif %}
                    <a href="{% url 'detail_pole' pole.slug %}" class="btn btn-primary mt-3">Nouvelle vente</a>
                </div>
            </div>
        </div>
    </div>
{% endblock %}
```

Ajoute la route pour `encaisser` si tu ne l'as pas déjà (elle était dans le
squelette initial de `caisse/urls.py` en 3.0) :

```python
path("pole/<slug:slug>/encaisser/", views.encaisser, name="encaisser"),
```

### 3.4 Le scan QR côté vendeur

Le modèle `JetonPaiement` existait dès la Partie 1 mais restait inutilisé
côté vendeur pendant longtemps : le circuit n'était pas fermé. La caméra du
navigateur lit le QR affiché par l'étudiant (Partie 5) et récupère le code du
jeton, transmis dans un champ caché `jeton` du même formulaire que la saisie
manuelle, `_profil_depuis_saisie` privilégie toujours le jeton s'il est
présent.

Crée `caisse/templates/caisse/_scan_qr.html` (le `_` au début du nom est une
simple convention pour marquer que ce fichier n'est jamais affiché tout
seul, seulement inclus dans une autre page) :

```html
{% comment %}
Modale de scan du QR de paiement, partagee entre encaisser.html et
terminal_pole.html. Suppose la presence d'un champ cache
<input type="hidden" name="jeton" id="champJeton"> dans le formulaire de
la page qui l'inclut, et d'un bouton id="btnScannerQR" pour l'ouvrir.
{% endcomment %}
<div class="modal fade" id="modaleScanQR" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Scanner le QR de l'acheteur</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body text-center">
                <video id="videoScanQR" style="width:100%;border-radius:12px;background:#000;" playsinline muted></video>
                <canvas id="canvasScanQR" style="display:none;"></canvas>
                <p id="erreurScanQR" class="text-danger small mt-2 d-none"></p>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js"></script>
<script>
    (function () {
        var boutonScanner = document.getElementById("btnScannerQR");
        if (!boutonScanner) { return; }
        var champJeton = document.getElementById("champJeton");
        var formulaire = champJeton.closest("form");
        var modaleEl = document.getElementById("modaleScanQR");
        var video = document.getElementById("videoScanQR");
        var canvas = document.getElementById("canvasScanQR");
        var contexte = canvas.getContext("2d");
        var messageErreur = document.getElementById("erreurScanQR");
        var flux = null;
        var animation = null;

        function arreterCamera() {
            if (animation) { cancelAnimationFrame(animation); animation = null; }
            if (flux) { flux.getTracks().forEach(function (piste) { piste.stop(); }); flux = null; }
        }

        function analyserImage() {
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                contexte.drawImage(video, 0, 0, canvas.width, canvas.height);
                var image = contexte.getImageData(0, 0, canvas.width, canvas.height);
                var resultat = jsQR(image.data, image.width, image.height);
                if (resultat && resultat.data) {
                    champJeton.value = resultat.data;
                    arreterCamera();
                    bootstrap.Modal.getInstance(modaleEl).hide();
                    formulaire.requestSubmit();
                    return;
                }
            }
            animation = requestAnimationFrame(analyserImage);
        }

        boutonScanner.addEventListener("click", function () {
            messageErreur.classList.add("d-none");
            new bootstrap.Modal(modaleEl).show();
        });
        modaleEl.addEventListener("shown.bs.modal", function () {
            navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
                .then(function (fluxCamera) {
                    flux = fluxCamera;
                    video.srcObject = flux;
                    video.play();
                    animation = requestAnimationFrame(analyserImage);
                })
                .catch(function () {
                    messageErreur.textContent = "Impossible d'accéder à la caméra. Vérifie les autorisations, ou utilise le champ identifiant.";
                    messageErreur.classList.remove("d-none");
                });
        });
        modaleEl.addEventListener("hidden.bs.modal", arreterCamera);
    })();
</script>
```

Ce fragment est **partagé** (`{% include "caisse/_scan_qr.html" %}`) entre
`encaisser.html` et `terminal_pole.html`, plutôt que dupliqué : les deux
pages ont exactement le même besoin (scanner puis soumettre le formulaire
hôte). Point technique important, documenté explicitement dans le
commentaire du template : `getUserMedia` (accès caméra) n'est accessible que
dans un **contexte sécurisé** (HTTPS ou `localhost`), pas sur une IP locale
non chiffrée, une limite à garder en tête pour les tests sur téléphone en
réseau local.

### 3.5 Le terminal (vente hors catalogue, montant libre)

Pour les cas où aucun produit du catalogue ne correspond (dons, ventes
exceptionnelles), un produit technique par pôle sert de support. Toujours
dans `caisse/views.py`, à la suite de tout ce qui précède :

```python
def _produit_vente_libre(pole):
    """Renvoie le produit technique 'Vente libre' du pole, le cree si besoin.
    N'apparait jamais dans les listes normales de produits."""
    produit, _ = Produit.objects.get_or_create(
        pole=pole, est_vente_libre=True,
        defaults={"nom": "Vente libre", "prix": 0, "disponible": False},
    )
    return produit
```

`est_vente_libre = models.BooleanField(default=False, editable=False)` sur
`Produit` : ce champ n'apparaît jamais dans un formulaire (`editable=False`),
et il est systématiquement exclu des requêtes du catalogue normal
(`est_vente_libre=False` partout où on liste les produits vendables/gérables).

Ajoute deux imports (`Decimal` pour manipuler un montant saisi au clavier
sans erreur d'arrondi, `poles_vendables` pour proposer le choix du pôle) :

```python
from decimal import Decimal

from .roles import poles_vendables
```

Puis les deux vues, toujours à la suite dans `caisse/views.py` :

```python
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
```

`terminal_pole` réutilise exactement le même schéma
`atomic`/`select_for_update`/`EchecEncaissement` que `encaisser` (via
`_profil_depuis_saisie`), avec un montant saisi au clavier plutôt qu'un
panier, même rigueur, même garanties.

Deux templates. `caisse/templates/caisse/terminal_choix.html` :

```html
{% extends "caisse/base.html" %}

{% block titre %}Terminal{% endblock %}

{% block contenu %}
    <h1 class="mb-4">Terminal</h1>
    <p class="text-muted small mb-2">Choisis le pôle pour lequel encaisser</p>
    <div class="d-flex flex-column gap-2">
        {% for pole in poles %}
            <a href="{% url 'terminal_pole' pole.slug %}" class="card shadow-sm text-decoration-none">
                <div class="card-body d-flex align-items-center justify-content-between py-3">
                    <div class="d-flex align-items-center gap-3">
                        <span class="fw-bold">{{ pole.nom }}</span>
                    </div>
                    <span class="text-muted">&rsaquo;</span>
                </div>
            </a>
        {% empty %}
            <p class="text-muted">Aucun pôle accessible.</p>
        {% endfor %}
    </div>
{% endblock %}
```

Et `caisse/templates/caisse/terminal_pole.html`, un pavé numérique pur
JavaScript pour saisir le montant sans clavier physique :

```html
{% extends "caisse/base.html" %}

{% block titre %}Terminal {{ pole.nom }}{% endblock %}

{% block contenu %}
    <a href="{% url 'accueil' %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <h1 class="mb-4">Terminal - {{ pole.nom }}</h1>
    <p class="text-muted small">Pour un produit hors catalogue (montant libre).</p>

    {% if erreur %}
        <div class="alert alert-danger">{{ erreur }}</div>
    {% endif %}

    <div class="row justify-content-center">
        <div class="col-md-5">
            <div class="card shadow-sm">
                <div class="card-body">
                    <div class="text-center mb-3">
                        <span class="display-4 fw-bold" id="affichage">0,00</span>
                        <span class="fs-4 text-muted">EUR</span>
                    </div>

                    <div class="row g-2 mb-3">
                        {% for touche in "123456789" %}
                            <div class="col-4">
                                <button type="button" class="btn btn-outline-secondary w-100 py-3 fs-4" onclick="taper('{{ touche }}')">{{ touche }}</button>
                            </div>
                        {% endfor %}
                        <div class="col-4">
                            <button type="button" class="btn btn-outline-secondary w-100 py-3 fs-4" onclick="taper(',')">,</button>
                        </div>
                        <div class="col-4">
                            <button type="button" class="btn btn-outline-secondary w-100 py-3 fs-4" onclick="taper('0')">0</button>
                        </div>
                        <div class="col-4">
                            <button type="button" class="btn btn-outline-danger w-100 py-3 fs-4" onclick="effacer()">&larr;</button>
                        </div>
                    </div>

                    <form method="post" id="formTerminal">
                        {% csrf_token %}
                        <input type="hidden" name="montant" id="champMontant">
                        <input type="hidden" name="jeton" id="champJeton">
                        <button type="button" class="btn btn-outline-primary w-100 mb-2" id="btnScannerQR">
                            Scanner le QR de l'acheteur
                        </button>
                        <label class="form-label">Identifiant de l'acheteur</label>
                        <input type="text" name="identifiant" class="form-control mb-3" placeholder="compte école">
                        <button type="submit" class="btn btn-primary w-100 py-2">Valider le paiement</button>
                    </form>
                </div>
            </div>
        </div>
    </div>

    {% include "caisse/_scan_qr.html" %}
{% endblock %}

{% block scripts %}
<script>
    let saisie = "";
    const affichage = document.getElementById("affichage");
    const champMontant = document.getElementById("champMontant");

    function rafraichir() {
        const valeur = saisie === "" ? "0" : saisie;
        const nombre = parseFloat(valeur.replace(",", ".")) || 0;
        affichage.textContent = nombre.toFixed(2).replace(".", ",");
        champMontant.value = nombre.toFixed(2);
    }

    function taper(caractere) {
        if (caractere === "," && saisie.includes(",")) return;  // une seule virgule
        if (saisie.includes(",") && saisie.split(",")[1].length >= 2) return;  // 2 decimales max
        saisie += caractere;
        rafraichir();
    }

    function effacer() {
        saisie = saisie.slice(0, -1);
        rafraichir();
    }

    rafraichir();
</script>
{% endblock %}
```

Note bien le formulaire `#formTerminal` avec son champ caché `id="champJeton"`
et son bouton `id="btnScannerQR"` : ce sont exactement les identifiants
attendus par `_scan_qr.html` (Partie 3.4), c'est ce qui permet au même
fragment de scan de fonctionner sur cette page aussi, sans rien dupliquer.

Enfin, ajoute les deux routes dans `caisse/urls.py` :

```python
path("terminal/", views.terminal_choix_pole, name="terminal_choix_pole"),
path("pole/<slug:slug>/terminal/", views.terminal_pole, name="terminal_pole"),
```

**Récapitulatif.** À ce stade, `caisse/urls.py` doit ressembler à ceci dans
son ensemble (vérifie que rien ne manque avant de continuer) :

```python
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("connexion/", auth_views.LoginView.as_view(template_name="caisse/login.html"), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("pole/<slug:slug>/", views.detail_pole, name="detail_pole"),
    path("ajouter/<int:produit_id>/", views.ajouter_au_panier, name="ajouter_au_panier"),
    path("pole/<slug:slug>/vider/", views.vider_panier, name="vider_panier"),
    path("pole/<slug:slug>/panier/", views.voir_panier, name="voir_panier"),
    path("pole/<slug:slug>/encaisser/", views.encaisser, name="encaisser"),
    path("terminal/", views.terminal_choix_pole, name="terminal_choix_pole"),
    path("pole/<slug:slug>/terminal/", views.terminal_pole, name="terminal_pole"),
]
```

Et `caisse/templates/caisse/` doit contenir, à ce stade : `base.html`,
`accueil.html`, `login.html`, `panier.html`, `pole.html`, `encaisser.html`,
`vente_ok.html`, `_scan_qr.html`, `terminal_choix.html`, `terminal_pole.html`.

---

## Partie 4 - Authentification et sécurité renforcée

### 4.1 Connexion standard Django (fondation, avant le CAS)

Ouvre `cashless/settings.py` et ajoute ces trois lignes (n'importe où dans le
fichier, par exemple à la fin) :

```python
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "verifier_code"
LOGOUT_REDIRECT_URL = "login"
```

`LOGIN_REDIRECT_URL` pointe vers `"verifier_code"`, une vue qu'on n'a pas
encore écrite (elle arrive en Partie 10, avec le système de code de
sécurité) : ça ne pose aucun problème tant qu'on ne se sert pas encore de
cette redirection, Django ne vérifie l'existence de cette route qu'au moment
où elle est réellement utilisée.

Les routes `login`/`logout` et le template `login.html`, eux, sont déjà en
place depuis la Partie 3.0 (il fallait qu'ils existent dès le début pour que
`base.html` fonctionne), rien à refaire ici.

Toutes les vues sensibles portent `@login_required`. La déconnexion se fait
via un `<form method="post">`, jamais un simple lien `<a>` : une action qui
modifie l'état (ici, la session) ne doit jamais être déclenchable par une
requête GET, encore moins par un lien qu'un robot pourrait suivre.

### 4.2 Le code de sécurité : la deuxième serrure des comptes à pouvoir

Même si les identifiants ENSEA d'un admin sont un jour compromis, un code
supplémentaire, connu **uniquement** de la personne, remis en main propre
par un admin école, protège les comptes à pouvoir (vendeur, admin de pôle,
admin ADE, admin école). Le code est **haché**, exactement comme un mot de
passe (`make_password`/`check_password` de Django) : personne, pas même
l'admin école qui l'a créé, ne peut le relire après coup, seulement le
régénérer.

Cette vue vit dans son propre fichier, séparé de `views.py`, car elle fait
partie d'un domaine à part (la gestion des comptes/rôles/codes, développée
en détail en Partie 10), mais on en a besoin **dès maintenant**, puisque
`LOGIN_REDIRECT_URL` (Partie 4.1) pointe déjà vers `"verifier_code"` : sans
cette route, la toute première connexion planterait. Crée
`caisse/vues_ecole.py` (nouveau fichier, qui restera minuscule jusqu'à la
Partie 10, où il grossira beaucoup) :

```python
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.shortcuts import redirect, render


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
```

Ouvre `caisse/urls.py` et ajoute l'import ainsi que la route (tant qu'il
n'y a que cette seule fonction dans le fichier, un import nommé suffit) :

```python
from . import vues_ecole
```

```python
path("verifier-code/", vues_ecole.verifier_code, name="verifier_code"),
```

Aujourd'hui, personne n'a encore de `CodeSecuriteAdmin` associé (rien ne
permet encore d'en créer, ça arrive en Partie 10), donc `a_des_codes` sera
toujours faux et cette page redirigera immédiatement vers l'accueil sans
rien demander, c'est normal, la fonctionnalité existe mais reste inactive
tant que personne n'a de code.

Il faut enfin le template. Crée `caisse/templates/caisse/verifier_code.html`
(le pavé numérique masque la saisie avec des points `•`, jamais les vrais
chiffres, comme un code carte bancaire) :

```html
{% extends "caisse/base.html" %}
{% block titre %}Code de sécurité{% endblock %}
{% block contenu %}
    <h1 class="mb-4 text-center">Code de sécurité</h1>

    {% if erreur %}
        <div class="alert alert-danger text-center">{{ erreur }}</div>
    {% endif %}

    <div class="row justify-content-center">
        <div class="col-md-5">
            <div class="card shadow-sm">
                <div class="card-body">
                    <div class="text-center mb-3">
                        <span class="display-4 fw-bold" id="affichage">------</span>
                    </div>

                    <div class="row g-2 mb-3">
                        {% for touche in "123456789" %}
                            <div class="col-4">
                                <button type="button" class="btn btn-outline-secondary w-100 py-3 fs-4" onclick="taper('{{ touche }}')">{{ touche }}</button>
                            </div>
                        {% endfor %}
                        <div class="col-4"></div>
                        <div class="col-4">
                            <button type="button" class="btn btn-outline-secondary w-100 py-3 fs-4" onclick="taper('0')">0</button>
                        </div>
                        <div class="col-4">
                            <button type="button" class="btn btn-outline-danger w-100 py-3 fs-4" onclick="effacer()">&larr;</button>
                        </div>
                    </div>

                    <form method="post" id="formCode">
                        {% csrf_token %}
                        <input type="hidden" name="code" id="champCode">
                        <button type="submit" class="btn btn-primary w-100 py-2">Valider</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
{% endblock %}

{% block scripts %}
<script>
    let saisie = "";
    const affichage = document.getElementById("affichage");
    const champCode = document.getElementById("champCode");

    function rafraichir() {
        const masque = "•".repeat(saisie.length) + "-".repeat(6 - saisie.length);
        affichage.textContent = masque;
        champCode.value = saisie;
    }

    function taper(chiffre) {
        if (saisie.length >= 6) return;
        saisie += chiffre;
        rafraichir();
    }

    function effacer() {
        saisie = saisie.slice(0, -1);
        rafraichir();
    }

    rafraichir();
</script>
{% endblock %}
```

### 4.3 Pourquoi un middleware, pas seulement `LOGIN_REDIRECT_URL`

Un premier essai reposait uniquement sur `LOGIN_REDIRECT_URL = "verifier_code"`.
**Insuffisant** : ce réglage ne s'applique que si l'utilisateur arrive sur
l'écran de connexion *sans destination précise*. Un lien profond cliqué
**avant** connexion (ex. un signet vers `/pole/kfet/gerer/`) redirige
directement vers cette destination une fois connecté, court-circuitant
complètement l'étape du code. La correction robuste est un **middleware**,
qui s'exécute à *chaque* requête, pas seulement à la connexion.

Un middleware est une classe Python qui s'intercale entre la requête et
chaque vue : elle peut inspecter ou bloquer la requête avant qu'elle
n'atteigne la vue visée, quelle que soit cette vue. Crée un nouveau fichier
`caisse/middleware.py` :

```python
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
```

Reste à brancher cette classe. Ouvre `cashless/settings.py` et repère la
liste `MIDDLEWARE` (déjà présente, générée par `startproject` avec les 7
premières lignes ci-dessous) : **ajoute une seule ligne**, la dernière, à la
fin de cette liste existante, ne touche à aucune des lignes déjà là :

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "caisse.middleware.VerifierCodeMiddleware",  # <- la seule ligne a ajouter
]
```

L'ordre compte : ce middleware doit venir **après**
`AuthenticationMiddleware` (qui définit `request.user`), sinon il ne pourrait
pas lire `request.user.is_authenticated`. Le placer en dernier, comme ici,
garantit toujours cet ordre.

Quelqu'un **sans** code configuré (un étudiant lambda) ne voit jamais cet
écran : `request.user.codes_securite.exists()` est faux, le middleware laisse
passer directement.

### 4.4 Un bug de sécurité réel, et sa leçon

Régénérer un code pour un rôle **global** (sans pôle, `pole=None`) créait
parfois un **doublon** au lieu de remplacer l'ancien, à cause d'une subtilité
des bases de données : `unique_together` ne détecte pas toujours deux lignes
`pole=NULL` comme identiques pour la contrainte d'unicité (`NULL` n'est égal
à rien, même pas à lui-même, en SQL). Conséquence grave : **l'ancien code
restait valide** en plus du nouveau, annulant l'intérêt même de la
régénération en cas de code divulgué. La correction robuste **supprime
explicitement l'ancien avant de créer le nouveau**, plutôt que de se fier à
`update_or_create` :

```python
CodeSecuriteAdmin.objects.filter(user=utilisateur, pole=pole).delete()
objet = CodeSecuriteAdmin.objects.create(
    user=utilisateur, pole=pole,
    code_hash=make_password(nouveau_code), definie_par=request.user,
)
```

*(Cette leçon, ne pas se fier à `update_or_create`/`unique_together` sur des
champs nullable sans vérifier le comportement réel de la base, vaut pour
n'importe quel champ optionnel utilisé dans une contrainte d'unicité.)*

---

## Partie 5 - Espace personnel de l'étudiant

### 5.1 Le profil et le principe d'« ancrage »

`InfoPersonnelleForm` (nom, prénom, email, date de naissance) applique un
principe simple mais efficace : **un champ déjà rempli est retiré du
formulaire**, pas juste désactivé côté HTML. Un champ désactivé en HTML
(`disabled`) reste contournable en manipulant la requête à la main ; un champ
**absent** du formulaire ne peut physiquement pas être pris en compte par
Django à la sauvegarde, quoi qu'on envoie en POST.

Crée un nouveau fichier `caisse/forms.py` (il n'existe pas encore) :

```python
from django import forms

from .models import ProfilUtilisateur


class InfoPersonnelleForm(forms.ModelForm):
    """Formulaire des informations personnelles, avec un principe
    d'ancrage : un champ deja renseigne est retire du formulaire, donc il
    devient impossible a modifier par l'etudiant lui-meme. Seul un futur
    compte admin ecole pourra corriger une erreur apres coup.

    Nom et prenom vivent sur le compte Django (User), pas sur le profil ;
    on les ajoute donc comme champs "libres" et on les enregistre nous-
    memes dans save()."""

    nom = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    prenom = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control"}))
    date_naissance = forms.DateField(
        required=True, input_formats=["%d/%m/%Y"],
        widget=forms.DateInput(format="%d/%m/%Y", attrs={
            "class": "form-control", "type": "text", "placeholder": "jj/mm/aaaa",
            "pattern": r"\d{2}/\d{2}/\d{4}", "maxlength": "10", "inputmode": "numeric",
        }),
    )

    class Meta:
        model = ProfilUtilisateur
        fields = ["date_naissance"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(["nom", "prenom", "email", "date_naissance"])
        instance = kwargs.get("instance")
        if instance and instance.user.last_name:
            del self.fields["nom"]
        if instance and instance.user.first_name:
            del self.fields["prenom"]
        if instance and instance.user.email:
            del self.fields["email"]
        if instance and instance.date_naissance:
            del self.fields["date_naissance"]

    def save(self, commit=True):
        profil = super().save(commit=False)
        if self.cleaned_data.get("nom"):
            profil.user.last_name = self.cleaned_data["nom"]
        if self.cleaned_data.get("prenom"):
            profil.user.first_name = self.cleaned_data["prenom"]
        if self.cleaned_data.get("email"):
            profil.user.email = self.cleaned_data["email"]
        if commit:
            profil.user.save()
            profil.save()
        return profil
```

**Pourquoi un champ date en texte, pas le widget natif `<input
type="date">` ?** L'affichage natif (ordre jour/mois, séparateurs) dépend de
la **langue du navigateur**, pas de la langue du site, cause racine d'un
vrai bug rencontré (dates en mm/dd/yyyy chez un utilisateur avec un
navigateur en anglais, alors que le site est entièrement en français). Un
champ texte au format `jj/mm/aaaa` fixe l'affichage indépendamment du
navigateur ; `input_formats=["%d/%m/%Y"]` fait que Django l'interprète
correctement côté serveur.

Le formatage automatique (ajout des `/`) et la validation calendrier
(jour/mois/année réellement valides, pas juste une regex) sont dupliqués côté
JavaScript pour l'expérience utilisateur, mais la validation serveur via
`input_formats` reste la protection réelle, jamais contournable — tu verras
ce script dans le template complet ci-dessous, pas la peine de le taper deux
fois.

**Confirmation en deux temps, jamais `confirm()` natif** (voir Partie 13 pour
le motif général), et surtout : le bouton d'envoi est en `type="button"`, pas
`type="submit"`, avec `formulaire.requestSubmit()` déclenché seulement après
les deux confirmations, et une garde `envoiAutorise` sur l'écouteur `submit`
du formulaire. Cette précaution corrige un vrai bug de sécurité rencontré :
un `<button type="submit" form="formInfo">` placé **hors** de la balise
`<form>` (mais lié via l'attribut `form=`) devenait le bouton de soumission
implicite du formulaire, appuyer sur *Entrée* dans n'importe quel champ
soumettait silencieusement le formulaire, **en contournant les deux modales
de confirmation**. Là encore, le code se trouve dans le template complet,
pas besoin de le taper à part.

Le template `info.html` applique tout ce qui précède. Crée
`caisse/templates/caisse/info.html` : chaque champ ancré y affiche sa valeur
en lecture seule avec un badge « Ancré », chaque champ non ancré affiche le
widget de saisie ; le formulaire entier disparaît une fois tout ancré
(`{% if form.fields %}`) :

```html
{% extends "caisse/base.html" %}

{% block titre %}Info{% endblock %}

{% block contenu %}
    <h1 class="mb-4">Mon profil</h1>

    {% if enregistre %}
        <div class="alert alert-success">Tes informations ont bien été enregistrées.</div>
    {% endif %}
    {% if form.errors %}
        <div class="alert alert-danger">Certains champs obligatoires ne sont pas renseignés correctement, corrige-les ci-dessous.</div>
    {% endif %}

    <div class="card shadow-sm">
        <div class="card-body">
            {% if form.fields %}<form method="post" id="formInfo" novalidate>{% csrf_token %}{% endif %}

            <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                <span class="text-muted">Nom{% if form.nom %} <span class="text-danger">*</span>{% endif %}</span>
                {% if profil.user.last_name %}
                    <span class="fw-bold">{{ profil.user.last_name }} <span class="badge bg-secondary">Ancré</span></span>
                {% else %}
                    <div style="max-width:200px;">
                        {{ form.nom }}
                        {% if form.nom.errors %}<div class="text-danger small mt-1">{{ form.nom.errors.0 }}</div>{% endif %}
                    </div>
                {% endif %}
            </div>
            <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                <span class="text-muted">Prénom{% if form.prenom %} <span class="text-danger">*</span>{% endif %}</span>
                {% if profil.user.first_name %}
                    <span class="fw-bold">{{ profil.user.first_name }} <span class="badge bg-secondary">Ancré</span></span>
                {% else %}
                    <div style="max-width:200px;">
                        {{ form.prenom }}
                        {% if form.prenom.errors %}<div class="text-danger small mt-1">{{ form.prenom.errors.0 }}</div>{% endif %}
                    </div>
                {% endif %}
            </div>
            <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                <span class="text-muted">Email ENSEA{% if form.email %} <span class="text-danger">*</span>{% endif %}</span>
                {% if profil.user.email %}
                    <span class="fw-bold">{{ profil.user.email }} <span class="badge bg-secondary">Ancré</span></span>
                {% else %}
                    <div style="max-width:200px;">
                        {{ form.email }}
                        {% if form.email.errors %}<div class="text-danger small mt-1">{{ form.email.errors.0 }}</div>{% endif %}
                    </div>
                {% endif %}
            </div>
            <div class="d-flex justify-content-between align-items-center py-2">
                <span class="text-muted">Date de naissance{% if form.date_naissance %} <span class="text-danger">*</span>{% endif %}</span>
                {% if profil.date_naissance %}
                    <span class="fw-bold">{{ profil.date_naissance|date:"d/m/Y" }} <span class="badge bg-secondary">Ancré</span></span>
                {% else %}
                    <div style="max-width:200px;">
                        {{ form.date_naissance }}
                        {% if form.date_naissance.errors %}<div class="text-danger small mt-1">{{ form.date_naissance.errors.0 }}</div>{% endif %}
                    </div>
                {% endif %}
            </div>

            {% if form.fields %}
                <p class="text-danger small mt-3 mb-1"><span class="text-danger">*</span> Champ obligatoire.</p>
                <p class="text-danger small mb-2">
                    Attention : une fois enregistrées, ces informations ne pourront plus être modifiées par toi-même.<br>
                    Cette action est irréversible.<br>
                    Seul un administrateur école pourra corriger une erreur
                    {% if admins_ecole %}
                        ({% for a in admins_ecole %}{{ a.first_name }} {{ a.last_name }}{% if not forloop.last %}, {% endif %}{% endfor %})
                    {% endif %}.
                </p>
                <button type="button" id="btnEnregistrerInfo" class="btn btn-primary w-100">Enregistrer les modifications</button>
            </form>
            {% endif %}
        </div>
    </div>

    {% if form.fields %}
    <div class="modal fade" id="confirmationInfo" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Confirmer l'enregistrement</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p class="text-danger mb-0">Une fois enregistrées, ces informations ne pourront plus être modifiées par toi-même. Cette action est irréversible.</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Annuler</button>
                    <button type="button" class="btn btn-success" id="btnConfirmerInfo1">Confirmer</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="confirmationInfo2" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Dernière vérification</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p class="mb-0">Vous êtes bien sûr(e) de vouloir enregistrer définitivement ces informations ?</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Annuler</button>
                    <button type="button" id="btnConfirmerInfo2" class="btn btn-success">Oui, enregistrer</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        var champDateNaissance = document.getElementById("id_date_naissance");
        if (champDateNaissance) {
            champDateNaissance.addEventListener("input", function () {
                var chiffres = champDateNaissance.value.replace(/\D/g, "").slice(0, 8);
                var jour = chiffres.slice(0, 2);
                var mois = chiffres.slice(2, 4);
                var annee = chiffres.slice(4);
                if (jour.length === 2 && parseInt(jour, 10) > 31) { jour = "31"; }
                if (mois.length === 2 && parseInt(mois, 10) > 12) { mois = "12"; }
                var formate = jour;
                if (chiffres.length > 2) { formate += "/" + mois; }
                if (chiffres.length > 4) { formate += "/" + annee; }
                champDateNaissance.value = formate;
            });
        }

        function dateNaissanceValide(valeur) {
            var correspondance = valeur.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
            if (!correspondance) { return false; }
            var jour = parseInt(correspondance[1], 10);
            var mois = parseInt(correspondance[2], 10);
            var annee = parseInt(correspondance[3], 10);
            if (mois < 1 || mois > 12 || jour < 1 || jour > 31) { return false; }
            var date = new Date(annee, mois - 1, jour);
            if (date.getFullYear() !== annee || date.getMonth() !== mois - 1 || date.getDate() !== jour) {
                return false;
            }
            if (date > new Date()) { return false; }
            return true;
        }

        var formulaireInfo = document.getElementById("formInfo");
        var envoiAutorise = false;
        formulaireInfo.addEventListener("submit", function (e) {
            if (!envoiAutorise) { e.preventDefault(); }
        });

        document.getElementById("btnEnregistrerInfo").addEventListener("click", function () {
            var champsObligatoires = document.querySelectorAll("#formInfo [required]");
            var toutRempli = true;
            champsObligatoires.forEach(function (champ) {
                var conteneur = champ.closest("div");
                var ancienMessage = conteneur.querySelector(".erreur-client");
                if (ancienMessage) { ancienMessage.remove(); }
                champ.classList.remove("is-invalid");
                if (!champ.value.trim()) {
                    toutRempli = false;
                    champ.classList.add("is-invalid");
                    var message = document.createElement("div");
                    message.className = "text-danger small mt-1 erreur-client";
                    message.textContent = "Ce champ est obligatoire.";
                    conteneur.appendChild(message);
                } else if (champ === champDateNaissance && !dateNaissanceValide(champ.value.trim())) {
                    toutRempli = false;
                    champ.classList.add("is-invalid");
                    var messageDate = document.createElement("div");
                    messageDate.className = "text-danger small mt-1 erreur-client";
                    messageDate.textContent = "Date invalide : vérifie le jour, le mois et l'année (jj/mm/aaaa).";
                    conteneur.appendChild(messageDate);
                }
            });
            if (toutRempli) {
                var modaleConfirmation = new bootstrap.Modal(document.getElementById("confirmationInfo"));
                modaleConfirmation.show();
            } else {
                champsObligatoires[0].focus();
            }
        });

        var modaleInfo1 = document.getElementById("confirmationInfo");
        var modaleInfo2 = document.getElementById("confirmationInfo2");
        var passageVersModale2 = false;
        document.getElementById("btnConfirmerInfo1").addEventListener("click", function () {
            passageVersModale2 = true;
            bootstrap.Modal.getInstance(modaleInfo1).hide();
        });
        modaleInfo1.addEventListener("hidden.bs.modal", function () {
            if (passageVersModale2) {
                passageVersModale2 = false;
                new bootstrap.Modal(modaleInfo2).show();
            }
        });
        document.getElementById("btnConfirmerInfo2").addEventListener("click", function () {
            envoiAutorise = true;
            formulaireInfo.requestSubmit();
        });
    </script>
    {% endif %}
{% endblock %}
```

Il manque la vue elle-même. Dans `caisse/views.py`, ajoute l'import du
formulaire et, si ce n'est pas déjà fait, celui de `User` (utile pour
retrouver les admins école ci-dessous, et pour beaucoup d'autres vues plus
loin dans le tutoriel) :

```python
from django.contrib.auth.models import User

from .forms import InfoPersonnelleForm
```

Puis la vue, à la suite du reste du fichier :

```python
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
```

Cette vue appelle `profil_de`, une fonction qu'on n'écrit qu'en Partie 5.3,
un peu plus loin, ce n'est pas un problème : dans un même fichier Python,
l'ordre des fonctions n'a pas d'importance, seul compte qu'elles existent
toutes au moment où le serveur tourne (`profil_de` n'est réellement
recherchée qu'au moment où `info` est appelée, jamais avant).

Ajoute la route dans `caisse/urls.py` :

```python
path("info/", views.info, name="info"),
```

### 5.2 Le QR de paiement dynamique

Une nouvelle librairie est nécessaire pour générer des QR codes :

```bash
pip install qrcode
```

Toujours dans `caisse/views.py`, ajoute ces imports (en haut du fichier) :

```python
import base64
import io

import qrcode
```

Puis, à la suite du reste du fichier :

```python
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
```

Le QR **change à chaque affichage** : les anciens jetons non utilisés du
même profil sont détruits, un nouveau est créé. Comme pour `info` (5.1),
`mon_qr` appelle `profil_de` avant que cette fonction ne soit définie plus
bas dans le fichier (5.3) — sans conséquence, pour la même raison.

Crée `caisse/templates/caisse/payer.html`, avec un minuteur JavaScript qui
recharge la page en fin de validité, régénérant ainsi automatiquement le QR
avant qu'il n'expire, sans action de l'utilisateur :

```html
{% extends "caisse/base.html" %}

{% block titre %}Payer{% endblock %}

{% block contenu %}
    <div class="row justify-content-center">
        <div class="col-12 col-sm-8 col-md-5">
            <div class="card shadow-sm text-center">
                <div class="card-body p-4">
                    <h4 class="mb-3">Scanner pour payer</h4>
                    <img src="{{ qr_uri }}" alt="QR de paiement" class="img-fluid mb-3 mx-auto d-block" style="width:100%;max-width:300px;">
                    <div class="mb-2">
                        <span class="badge bg-primary fs-6">QR code valable encore <span id="minuteur">--:--</span></span>
                    </div>
                    <p class="text-muted small mb-0">QR code change toutes les deux minutes.</p>
                </div>
            </div>
        </div>
    </div>
{% endblock %}

{% block scripts %}
<script>
    let reste = {{ duree }};
    const el = document.getElementById("minuteur");
    function afficher() {
        const m = Math.floor(reste / 60);
        const s = reste % 60;
        el.textContent = m + ":" + (s < 10 ? "0" + s : s);
    }
    afficher();
    setInterval(function () {
        reste = reste - 1;
        if (reste <= 0) { location.reload(); return; }
        afficher();
    }, 1000);
</script>
{% endblock %}
```

Enfin, ajoute la route dans `caisse/urls.py` :

```python
path("payer/", views.mon_qr, name="payer"),
```

### 5.3 L'accueil : chronologie fusionnée des mouvements

Dans `caisse/views.py`, remplace la **fonction** `accueil` provisoire écrite
en Partie 3.0 (qui se contentait d'un `render` vide) par celle-ci, il
s'agit bien de la vue Python, pas du template `accueil.html` (qu'on met à
jour séparément juste après) :

```python
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
```

Achats (débits) et recharges confirmées (crédits) sont **fusionnés en une
seule chronologie** triée par date, façon relevé de compte, plutôt que deux
listes séparées, plus fidèle à ce qu'attend un utilisateur d'une app
bancaire.

Remplace maintenant le contenu de `caisse/templates/caisse/accueil.html`
(le stub d'une ligne écrit en Partie 3.0) par la vraie page :

```html
{% extends "caisse/base.html" %}

{% block titre %}Accueil{% endblock %}

{% block contenu %}
    {% if profil.user.first_name or profil.user.last_name %}
        <div class="d-flex align-items-center justify-content-between mb-3">
            <div>
                <div class="text-muted small" id="salutation">Bon retour,</div>
                <div class="fw-bold fs-5">{{ profil.user.first_name }} {{ profil.user.last_name }}</div>
            </div>
            <a href="{% url 'info' %}" class="avatar-utilisateur text-decoration-none">
                {{ profil.user.first_name|first|upper }}{{ profil.user.last_name|first|upper }}
            </a>
        </div>
    {% endif %}

    <div class="card carte-solde shadow-sm mb-3">
        <div class="card-body text-center py-4">
            <div class="text-uppercase small" style="opacity:.9;letter-spacing:1px;">Solde disponible</div>
            <div class="display-5 fw-bold my-1">{{ profil.solde|floatformat:2 }} EUR</div>
        </div>
    </div>

    <h6 class="text-muted text-uppercase mb-2">Dernières transactions</h6>
    {% for m in mouvements %}
        <div class="card shadow-sm mb-2">
            <div class="card-body py-2 d-flex align-items-center">
                {% if m.photo %}
                    <img src="{{ m.photo.url }}" class="rounded me-2" style="width:36px;height:36px;object-fit:cover;">
                {% else %}
                    <div class="rounded bg-light me-2 d-flex align-items-center justify-content-center" style="width:36px;height:36px;">
                        {% if m.sens == "credit" %}+{% else %}-{% endif %}
                    </div>
                {% endif %}
                <div class="flex-grow-1">
                    <div class="fw-bold">{{ m.titre }}</div>
                    <div class="text-muted small">{{ m.date|date:"d/m/Y H:i" }}</div>
                </div>
                {% if m.sens == "credit" %}
                    <div class="fw-bold text-success">+{{ m.montant|floatformat:2 }} EUR</div>
                {% else %}
                    <div class="fw-bold text-danger">-{{ m.montant|floatformat:2 }} EUR</div>
                {% endif %}
            </div>
        </div>
    {% empty %}
        <div class="etat-vide">
            <div class="etat-vide-icone">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            </div>
            <span class="text-muted small">Aucune transaction pour le moment.</span>
        </div>
    {% endfor %}
{% endblock %}

{% block scripts %}
<script>
    const heure = new Date().getHours();
    let salutation;
    if (heure < 6) {
        salutation = "Bonne nuit,";
    } else if (heure < 12) {
        salutation = "Bonjour,";
    } else if (heure < 18) {
        salutation = "Bon après-midi,";
    } else {
        salutation = "Bonsoir,";
    }
    const el = document.getElementById("salutation");
    if (el) el.textContent = salutation;
</script>
{% endblock %}
```

Cette version n'a volontairement pas encore le bouton « Devenir adhérent
d'un pôle » : il pointe vers `adherer_liste`, une page qui n'existe qu'en
Partie 8, on l'ajoutera à ce moment-là.

### 5.4 Recharger (page d'attente, avant HelloAsso)

Un vrai rechargement en ligne (via HelloAsso) sort du cadre de ce
tutoriel — c'est un service externe payant, avec ses propres identifiants
par pôle. Pour l'instant, cette page se contente d'exister, avec un bouton
désactivé, pour que l'onglet « Recharger » de la barre de navigation ait
une destination réelle.

Dans `caisse/views.py`, à la suite du reste :

```python
@login_required
def recharger(request):
    return render(request, "caisse/recharger.html", {
        "profil": profil_de(request.user),
    })
```

Crée `caisse/templates/caisse/recharger.html` :

```html
{% extends "caisse/base.html" %}

{% block titre %}Recharger{% endblock %}

{% block contenu %}
    <h1 class="mb-4">Recharger mon compte</h1>
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card shadow-sm text-center">
                <div class="card-body p-4">
                    <div class="fs-4 fw-bold mb-2">Hello<span class="text-dark">Asso</span></div>
                    <p class="text-muted small mb-4">Paiement sécurisé et sans frais.</p>
                    <button class="btn btn-primary w-100" disabled>Recharger (bientôt disponible)</button>
                </div>
            </div>
        </div>
    </div>
{% endblock %}
```

Ajoute la route dans `caisse/urls.py` :

```python
path("recharger/", views.recharger, name="recharger"),
```

### 5.5 La barre d'onglets, enfin complète pour l'espace personnel

Toutes les pages de l'espace personnel existent maintenant : Accueil, Payer,
Recharger, Info (le Terminal, lui, existe depuis la Partie 3.5). C'est le bon
moment pour faire grossir `base.html` (encore réduit depuis la Partie 3.0) et
lui ajouter la vraie barre de navigation en bas de l'écran.

Remplace tout le contenu de `caisse/templates/caisse/base.html` par cette
version :

```html
{% load static %}
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <title>{% block titre %}Caisse{% endblock %}</title>

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {
            --ensea: #C8004B;
            --ensea-dark: #960038;
            --ensea-light: #FFF0F4;
        }
        body { background-color: #F8F9FA; padding-bottom: 80px; }
        .btn-primary { --bs-btn-bg: var(--ensea); --bs-btn-border-color: var(--ensea); --bs-btn-hover-bg: var(--ensea-dark); --bs-btn-hover-border-color: var(--ensea-dark); --bs-btn-active-bg: var(--ensea-dark); --bs-btn-active-border-color: var(--ensea-dark); }
        .bg-primary { background-color: var(--ensea) !important; }
        .text-ensea { color: var(--ensea); }

        .carte-solde { background: linear-gradient(135deg, var(--ensea), var(--ensea-dark)); color: #fff; border: none; border-radius: 18px; }
        .avatar-utilisateur {
            width: 42px; height: 42px; border-radius: 50%;
            background: var(--ensea-light); color: var(--ensea);
            display: flex; align-items: center; justify-content: center;
            font-weight: 800; font-size: 14px;
            border: 2px solid #fff; box-shadow: 0 2px 8px rgba(200,0,75,0.15);
            flex-shrink: 0;
        }
        .etat-vide {
            background: #fff; border: 1px dashed #E2E8F0; border-radius: 16px;
            padding: 30px 16px; display: flex; flex-direction: column; align-items: center;
            justify-content: center; gap: 8px; text-align: center;
        }
        .etat-vide-icone {
            width: 36px; height: 36px; border-radius: 50%; background: #F8F9FA;
            display: flex; align-items: center; justify-content: center; color: #94A3B8;
        }

        .barre-onglets { position: fixed; bottom: 0; left: 0; right: 0; height: 64px; background: #fff; border-top: 1px solid #E2E8F0; display: flex; justify-content: space-around; align-items: center; z-index: 100; }
        .onglet { display: flex; flex-direction: column; align-items: center; gap: 3px; color: #64748B; font-size: 10px; font-weight: 600; text-decoration: none; }
        .onglet.actif { color: var(--ensea); }
        .onglet svg { width: 22px; height: 22px; fill: currentColor; }
    </style>
</head>
<body>
    <nav class="navbar bg-white shadow-sm mb-3">
        <div class="container">
            <a class="navbar-brand fw-bold text-ensea" href="{% url 'accueil' %}">Mon portefeuille ENSEA</a>
            {% if user.is_authenticated %}
                <form method="post" action="{% url 'logout' %}" class="d-inline">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-outline-secondary btn-sm">Déconnexion</button>
                </form>
            {% else %}
                <a href="{% url 'login' %}" class="btn btn-outline-secondary btn-sm">Connexion</a>
            {% endif %}
        </div>
    </nav>

    <main class="container">
        {% block contenu %}{% endblock %}
    </main>

    {% if user.is_authenticated %}
    {% with onglet=request.resolver_match.url_name %}
    <nav class="barre-onglets">
        <a class="onglet {% if onglet == 'accueil' %}actif{% endif %}" href="{% url 'accueil' %}">
            <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
            Accueil
        </a>
        {% if a_droits_vente %}
        <a class="onglet {% if onglet == 'terminal_pole' or onglet == 'terminal_choix_pole' %}actif{% endif %}" href="{% url 'terminal_choix_pole' %}">
            <svg viewBox="0 0 24 24"><path d="M12 19c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm-6 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 12c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm12-12c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/></svg>
            Terminal
        </a>
        {% endif %}
        <a class="onglet {% if onglet == 'payer' %}actif{% endif %}" href="{% url 'payer' %}">
            <svg viewBox="0 0 24 24"><path d="M3 11h8V3H3v8zm2-6h4v4H5V5zm8-2v8h8V3h-8zm6 6h-4V5h4v4zM3 21h8v-8H3v8zm2-6h4v4H5v-4zm13-2h-2v3h-3v2h3v3h2v-3h3v-2h-3z"/></svg>
            Payer
        </a>
        <a class="onglet {% if onglet == 'recharger' %}actif{% endif %}" href="{% url 'recharger' %}">
            <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11h-4v4h-2v-4H7v-2h4V7h2v4h4v2z"/></svg>
            Recharger
        </a>
        <a class="onglet {% if onglet == 'info' %}actif{% endif %}" href="{% url 'info' %}">
            <svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
            Info
        </a>
    </nav>
    {% endwith %}
    {% endif %}

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

Ce qui a changé par rapport à la version de la Partie 3.0 : le bloc `<nav
class="barre-onglets">` en bas (avec Accueil, Terminal si tu as des droits
de vente, Payer, Recharger, Info), et quelques classes CSS utilisées par
`accueil.html` (`carte-solde`, `avatar-utilisateur`, `etat-vide`). L'onglet
« Asso » (Partie 7) et « École » (Partie 10) viendront s'ajouter à cette
même barre plus tard, chacun à son tour.

Relance le serveur et regarde en bas de l'écran : la barre d'onglets doit
maintenant apparaître.

---

## Partie 6 - Le catalogue : produits, catégories, événements

### 6.1 Produits et catégories

Dans `caisse/forms.py`, à la suite de `InfoPersonnelleForm` (Partie 5.1) :

```python
class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ["nom", "categorie", "prix", "stock", "disponible", "photo"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "categorie": forms.Select(attrs={"class": "form-select"}),
            "prix": forms.NumberInput(attrs={"class": "form-control", "step": "0.10"}),
            "stock": forms.NumberInput(attrs={"class": "form-control"}),
            "disponible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, pole=None, **kwargs):
        super().__init__(*args, **kwargs)
        # On ne propose que les categories du pole concerne, jamais celles
        # d'un autre pole.
        if pole is not None:
            self.fields["categorie"].queryset = pole.categories.all()
        self.fields["categorie"].required = False

    def clean_photo(self):
        return _valider_taille_image(self.cleaned_data.get("photo"))
```

Modifie l'import en haut de `caisse/forms.py` pour ajouter `Produit` (à
côté de `ProfilUtilisateur`) :

```python
from .models import Produit, ProfilUtilisateur
```

`clean_photo` appelle `_valider_taille_image`, une fonction qu'on écrit
juste après dans ce même fichier, pas de souci, même raison que pour
`profil_de` en Partie 5 (l'ordre des fonctions dans un fichier Python
n'a pas d'importance).

**La taille max d'image (5 Mo)** est vérifiée côté serveur, réutilisée pour
tous les formulaires avec upload. Toujours dans `caisse/forms.py`, à la
suite de `ProduitForm` :

```python
TAILLE_MAX_IMAGE_MO = 5

def _valider_taille_image(fichier):
    """Refuse une image de plus de TAILLE_MAX_IMAGE_MO. Ne s'applique qu'a
    un fichier fraichement televerse : le fichier deja enregistre (champ
    non touche a l'edition) n'a pas cet attribut et n'est jamais re-verifie."""
    if fichier and hasattr(fichier, "content_type") and fichier.size > TAILLE_MAX_IMAGE_MO * 1024 * 1024:
        raise forms.ValidationError(
            f"Image trop lourde ({fichier.size / 1024 / 1024:.1f} Mo) : {TAILLE_MAX_IMAGE_MO} Mo maximum."
        )
    return fichier
```

`hasattr(fichier, "content_type")` est la façon de distinguer un fichier
**fraîchement uploadé** (un `UploadedFile`, qui porte cet attribut) d'un
fichier **déjà enregistré** (un `FieldFile` existant, quand le champ n'est
pas touché à l'édition) : sans cette distinction, rouvrir un formulaire
d'édition sans changer la photo re-déclencherait la validation sur un fichier
qui n'a jamais quitté le disque.

Avant de créer des produits, il faut une page pour les lister, c'est vers
elle que tout redirige. Ajoute ces imports dans `caisse/views.py` :

```python
from django.core.exceptions import PermissionDenied

from .forms import ProduitForm
from .models import Categorie
from .roles import peut_gerer_produits
```

Puis, à la suite du reste du fichier :

```python
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
```

Le paramètre d'URL `?categorie=` est validé avant d'être utilisé comme
identifiant numérique (`brut.isdigit()`) — un non-admin qui taperait
`?categorie=retires` dans l'URL sans avoir le droit de voir les retirés ne
doit jamais provoquer d'erreur serveur, juste retomber sur la vue normale.

Toujours dans `caisse/views.py`, à la suite du bloc précédent (`gerer_produits`).
**`pole` est toujours assigné par la vue, jamais par le formulaire** :

```python
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
```

`commit=False` construit l'objet sans l'écrire tout de suite, le temps
d'assigner le pôle. C'est la garantie qu'un admin du pôle Kfet ne puisse
**jamais**, même en bidouillant la requête, créer un produit rattaché à un
autre pôle.

Toujours dans `caisse/views.py`, à la suite de `creer_produit`.
**Retirer un produit** (Partie 1.2) est une action séparée, réservée aux
vrais admins :

```python
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
```

(Un bug concret a existé sur ce même point : un non-admin tapant
`?categorie=retires` dans l'URL provoquait un `ValueError`, car le code
retombait dans la branche normale de filtrage par catégorie qui attend un
entier — c'est exactement ce que `brut.isdigit()`, déjà dans le code
ci-dessus, empêche.)

Il reste les templates. `caisse/templates/caisse/produit_form.html`, utilisé
par `creer_produit` et `modifier_produit` :

```html
{% extends "caisse/base.html" %}

{% block titre %}{{ titre }}{% endblock %}

{% block contenu %}
    <a href="{% url 'gerer_produits' pole.slug %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <h1 class="mb-4">{{ titre }}</h1>

    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card shadow-sm">
                <div class="card-body">
                    {% if produit.photo %}
                        <img src="{{ produit.photo.url }}" class="mb-3" style="max-width:120px;border-radius:8px;">
                    {% endif %}
                    <form method="post" enctype="multipart/form-data">
                        {% csrf_token %}
                        <div class="mb-3">
                            <label class="form-label">Nom</label>
                            {{ form.nom }}
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Catégorie</label>
                            {{ form.categorie }}
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Prix (EUR)</label>
                            {{ form.prix }}
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Stock (laisser vide = illimité)</label>
                            {{ form.stock }}
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Photo</label>
                            {{ form.photo }}
                            {% if form.photo.errors %}<div class="text-danger small mt-1">{{ form.photo.errors.0 }}</div>{% endif %}
                            <p class="text-muted small mt-1">5 Mo maximum.</p>
                        </div>
                        <div class="form-check mb-3">
                            {{ form.disponible }}
                            <label class="form-check-label">Disponible à la vente</label>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Enregistrer</button>
                    </form>

                    {% if produit and admin_reel %}
                        <hr class="my-3">
                        {% if produit.retire %}
                            <form method="post">
                                {% csrf_token %}
                                <button type="submit" name="remettre" value="1" class="btn btn-outline-success w-100">Remettre l'article</button>
                            </form>
                        {% else %}
                            <button type="button" class="btn btn-outline-danger w-100" data-bs-toggle="modal" data-bs-target="#modaleRetirerArticle">Retirer l'article</button>
                        {% endif %}
                    {% endif %}
                </div>
            </div>
        </div>
    </div>

    {% if produit and admin_reel and not produit.retire %}
    <div class="modal fade" id="modaleRetirerArticle" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Retirer cet article ?</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p class="mb-0">
                        "{{ produit.nom }}" disparaîtra de la vente et du catalogue normal, et
                        rejoindra l'onglet "Retirés" (visible uniquement des admins). Tu pourras
                        le remettre à tout moment.
                    </p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Annuler</button>
                    <form method="post">
                        {% csrf_token %}
                        <button type="submit" name="retirer" value="1" class="btn btn-danger">Oui, retirer</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    {% endif %}
{% endblock %}
```

Puis un petit fragment partagé, `caisse/templates/caisse/_onglets_gerer.html`
(pour l'instant un seul onglet ; celui « Événements » s'ajoutera en 6.3) :

```html
<a href="{% url 'gerer_produits' pole.slug %}" class="onglet-gerer {% if actif == 'catalogue' %}active{% endif %}">Catalogue</a>
```

Et `caisse/templates/caisse/gerer_produits.html` :

```html
{% extends "caisse/base.html" %}

{% block titre %}Gérer {{ pole.nom }}{% endblock %}

{% block contenu %}
    <div class="d-flex align-items-center gap-2 mb-3 flex-wrap">
        <a href="{% url 'accueil' %}" class="btn btn-outline-secondary btn-sm">&lsaquo; Retour</a>
        {% include "caisse/_onglets_gerer.html" with actif="catalogue" %}
    </div>

    <h1 class="mb-3">Produits - {{ pole.nom }}</h1>

    <div class="d-flex gap-2 mb-3">
        <a href="{% url 'gerer_categories' pole.slug %}" class="btn btn-outline-secondary btn-sm">Catégories</a>
        <a href="{% url 'creer_produit' pole.slug %}" class="btn btn-primary btn-sm">+ Nouveau produit</a>
    </div>

    <div class="puces-categories mb-3">
        <a href="{% url 'gerer_produits' pole.slug %}" class="puce-categorie {% if not categorie_active and not voir_retires %}active{% endif %}">Tous ({{ nb_total }})</a>
        {% for c in categories_comptes %}
            <a href="?categorie={{ c.id }}" class="puce-categorie {% if categorie_active == c.id %}active{% endif %}">{{ c.nom }} ({{ c.nb }})</a>
        {% endfor %}
        {% if admin_reel %}
            <a href="?categorie=retires" class="puce-categorie {% if voir_retires %}active{% endif %}">Retirés ({{ nb_retires }})</a>
        {% endif %}
    </div>

    <div class="d-flex flex-column gap-2">
        {% for produit in produits %}
            <a href="{% url 'modifier_produit' pole.slug produit.id %}" class="ligne-produit shadow-sm">
                <div class="d-flex align-items-center gap-2">
                    <div class="miniature-produit">
                        {% if produit.photo %}
                            <img src="{{ produit.photo.url }}">
                        {% endif %}
                    </div>
                    <div>
                        <div class="fw-bold small">{{ produit.nom }}</div>
                        <div class="text-muted" style="font-size:11px;">
                            {{ produit.categorie.nom|default:"Sans categorie" }}
                            {% if produit.stock is not None %}
                                <span class="etiquette-stock ms-1">Stock : {{ produit.stock }}</span>
                            {% endif %}
                        </div>
                    </div>
                </div>
                <div class="text-end">
                    <div class="fw-bold">{{ produit.prix|floatformat:2 }} EUR</div>
                    {% if voir_retires %}
                        <span class="badge bg-secondary">Retiré</span>
                    {% elif not produit.disponible %}
                        <span class="badge bg-secondary">Masqué</span>
                    {% elif produit.stock == 0 %}
                        <span class="badge bg-danger">Épuisé</span>
                    {% else %}
                        <span class="badge bg-success">En vente</span>
                    {% endif %}
                </div>
            </a>
        {% empty %}
            {% if voir_retires %}
                <p class="text-muted text-center py-3">Aucun produit retiré.</p>
            {% else %}
                <p class="text-muted text-center py-3">Aucun produit pour ce pôle.</p>
            {% endif %}
        {% endfor %}
    </div>
{% endblock %}
```

Ce template ajoute deux classes CSS pas encore présentes dans `base.html`
(`.puces-categories`/`.puce-categorie`, `.ligne-produit`/`.miniature-produit`/
`.etiquette-stock`, `.onglet-gerer`) : ajoute-les dans le `<style>` de
`caisse/templates/caisse/base.html` :

```css
.puces-categories { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 4px; }
.puces-categories::-webkit-scrollbar { display: none; }
.puce-categorie {
    padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600;
    background: #fff; border: 1px solid #E2E8F0; color: #64748B;
    white-space: nowrap; text-decoration: none; display: inline-block;
}
.puce-categorie.active { background: var(--ensea-light); border-color: var(--ensea); color: var(--ensea); font-weight: 700; }

.ligne-produit {
    background: #fff; border: 1px solid #E2E8F0; border-radius: 14px; padding: 12px;
    display: flex; align-items: center; justify-content: space-between; gap: 10px;
    text-decoration: none; color: inherit;
}
.miniature-produit {
    width: 44px; height: 44px; border-radius: 10px; background: #F1F5F9;
    display: flex; align-items: center; justify-content: center; overflow: hidden;
    border: 1px solid #E2E8F0; flex-shrink: 0;
}
.miniature-produit img { width: 100%; height: 100%; object-fit: cover; }
.etiquette-stock { background: #EFF6FF; color: #2563EB; padding: 2px 6px; border-radius: 6px; font-size: 10px; font-weight: 600; }

.onglet-gerer {
    padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 700;
    text-decoration: none; background: #fff; border: 1px solid #E2E8F0;
    color: #64748B; display: inline-block;
}
.onglet-gerer.active { background: var(--ensea); border-color: var(--ensea); color: #fff; }
```

Enfin, ajoute les routes dans `caisse/urls.py` :

```python
path("pole/<slug:slug>/gerer/", views.gerer_produits, name="gerer_produits"),
path("pole/<slug:slug>/gerer/nouveau/", views.creer_produit, name="creer_produit"),
path("pole/<slug:slug>/gerer/<int:produit_id>/", views.modifier_produit, name="modifier_produit"),
```

### 6.2 Catégories : création/modification/suppression

D'abord le formulaire, dans `caisse/forms.py` (ajoute `Categorie` à l'import
`.models` existant) :

```python
class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ["nom"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
        }
```

Puis, dans `caisse/views.py`, la vue de création (ajoute `CategorieForm` à
l'import `.forms` existant) :

```python
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
```

Et la vue de modification/suppression, à la suite :

```python
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
```

La suppression est **refusée** (erreur claire, pas un plantage de contrainte
SQL) si des produits sont encore rattachés - cohérent avec `on_delete=SET_NULL`
sur `Produit.categorie` : techniquement la suppression serait possible (les
produits perdraient juste leur catégorie), mais on préfère forcer un geste
explicite (déplacer ou retirer les produits d'abord) plutôt qu'une perte de
classement silencieuse.

Les deux templates. `caisse/templates/caisse/gerer_categories.html` :

```html
{% extends "caisse/base.html" %}

{% block titre %}Catégories {{ pole.nom }}{% endblock %}

{% block contenu %}
    <a href="{% url 'gerer_produits' pole.slug %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <h1 class="mb-4">Catégories - {{ pole.nom }}</h1>

    <div class="card shadow-sm mb-4">
        <div class="card-body">
            <h6 class="mb-3">Nouvelle catégorie</h6>
            <form method="post" class="d-flex gap-2">
                {% csrf_token %}
                <input type="text" name="nom" class="form-control" placeholder="Nom de la catégorie" required>
                <button type="submit" class="btn btn-primary text-nowrap">Ajouter</button>
            </form>
        </div>
    </div>

    <h6 class="text-muted text-uppercase mb-2">Catégories existantes</h6>
    <ul class="list-group shadow-sm">
        {% for c in categories %}
            <li class="list-group-item d-flex justify-content-between align-items-center">
                {{ c.nom }}
                <a href="{% url 'modifier_categorie' pole.slug c.id %}" class="btn btn-sm btn-outline-primary">Modifier</a>
            </li>
        {% empty %}
            <li class="list-group-item text-muted">Aucune catégorie pour le moment.</li>
        {% endfor %}
    </ul>
{% endblock %}
```

`caisse/templates/caisse/modifier_categorie.html` :

```html
{% extends "caisse/base.html" %}

{% block titre %}Modifier catégorie{% endblock %}

{% block contenu %}
    <a href="{% url 'gerer_categories' pole.slug %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <h1 class="mb-4">Modifier la catégorie</h1>

    {% if erreur %}
        <div class="alert alert-danger">{{ erreur }}</div>
    {% endif %}

    <div class="card shadow-sm">
        <div class="card-body">
            <form method="post">
                {% csrf_token %}
                <div class="mb-3">
                    <label class="form-label">Nom</label>
                    {{ form.nom }}
                </div>
                <button type="submit" class="btn btn-primary w-100 mb-2">Enregistrer</button>
            </form>
            <form method="post" id="formSupprimerCategorie">
                {% csrf_token %}
                <button type="submit" name="supprimer" value="1" class="btn btn-outline-danger w-100">Supprimer la catégorie</button>
            </form>
        </div>
    </div>
{% endblock %}
```

(Le bouton « Supprimer » n'a volontairement pas de confirmation JavaScript
ici, contrairement au motif habituel du projet — Partie 13.1 : c'est une
suppression déjà protégée côté serveur, qui échoue proprement avec un
message clair tant que des produits sont rattachés, jamais destructive par
accident.)

Enfin, ajoute les routes dans `caisse/urls.py` :

```python
path("pole/<slug:slug>/gerer/categories/", views.gerer_categories, name="gerer_categories"),
path("pole/<slug:slug>/gerer/categories/<int:categorie_id>/", views.modifier_categorie, name="modifier_categorie"),
```

### 6.3 Événements et billets

Un événement (`Evenement`) est le dossier qui regroupe les places d'une
soirée ; ses « billets » sont de simples `Produit` rattachés (`evenement=...`).

D'abord le formulaire, dans `caisse/forms.py` (ajoute `Evenement` à
l'import `.models` existant) — il utilise le même motif de champ date texte
français que `InfoPersonnelleForm` :

```python
class EvenementForm(forms.ModelForm):
    date_evenement = forms.DateTimeField(
        input_formats=["%d/%m/%Y %H:%M"],
        widget=forms.DateTimeInput(format="%d/%m/%Y %H:%M", attrs={
            "class": "form-control", "type": "text", "placeholder": "jj/mm/aaaa hh:mm",
        }),
    )
    date_fin_vente = forms.DateTimeField(
        required=False, input_formats=["%d/%m/%Y %H:%M"],
        widget=forms.DateTimeInput(format="%d/%m/%Y %H:%M", attrs={
            "class": "form-control", "type": "text", "placeholder": "jj/mm/aaaa hh:mm",
        }),
    )

    class Meta:
        model = Evenement
        fields = ["nom", "date_evenement", "lieu", "photo", "date_fin_vente", "actif"]

    def clean_photo(self):
        return _valider_taille_image(self.cleaned_data.get("photo"))
```

`est_vendable()` (Partie 1.2) combine `actif` et `date_fin_vente` : un
événement peut être coupé automatiquement à une heure précise même si «
actif » reste coché, ce qui évite d'avoir à revenir décocher manuellement à
la fin de chaque soirée.

Dans `caisse/views.py`, ajoute `EvenementForm` à l'import `.forms` existant
et `Evenement` à l'import `.models` existant. La liste des événements
d'abord :

```python
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
```

Puis la page « Modifier un événement », qui **fusionne** la fiche de
l'événement et la gestion de ses billets/catalogue de soirée sur un seul
écran (plus simple que deux pages séparées) :

```python
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
```

Les billets eux-mêmes sont de simples `Produit`, avec un formulaire dédié
dans `caisse/forms.py`, à la suite d'`EvenementForm` (pas de champ
catégorie : un événement n'a pas de rayons ; pas de champ pôle/événement
non plus, toujours fixés par la vue) :

```python
class BilletForm(forms.ModelForm):
    """Comme ProduitForm, mais pour un produit rattache a un evenement.
    Le champ est_billet distingue une vraie entree (compte comme une
    presence) d'un simple produit vendu ce soir-la (boisson, ecocup...)."""

    class Meta:
        model = Produit
        fields = ["nom", "prix", "stock", "disponible", "photo", "est_billet"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "prix": forms.NumberInput(attrs={"class": "form-control", "step": "0.10"}),
            "stock": forms.NumberInput(attrs={"class": "form-control"}),
            "disponible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "est_billet": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_photo(self):
        return _valider_taille_image(self.cleaned_data.get("photo"))
```

Et dans `caisse/views.py`, à la suite de `modifier_evenement` (ajoute
`BilletForm` à l'import `.forms`) :

```python
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
```

Trois templates. D'abord, mets à jour `caisse/templates/caisse/_onglets_gerer.html`
(créé en 6.1) pour ajouter le second onglet :

```html
<a href="{% url 'gerer_produits' pole.slug %}" class="onglet-gerer {% if actif == 'catalogue' %}active{% endif %}">Catalogue</a>
<a href="{% url 'gerer_evenements' pole.slug %}" class="onglet-gerer {% if actif == 'evenements' %}active{% endif %}">Événements</a>
```

`caisse/templates/caisse/gerer_evenements.html` (le bouton « Retour »
pointe provisoirement vers `accueil`, comme pour `gerer_produits.html` en
6.1 — il pointera vers `espace_asso` une fois cette page construite, en
Partie 7) :

```html
{% extends "caisse/base.html" %}

{% block titre %}Événements {{ pole.nom }}{% endblock %}

{% block contenu %}
    <div class="d-flex align-items-center gap-2 mb-3 flex-wrap">
        <a href="{% url 'accueil' %}" class="btn btn-outline-secondary btn-sm">&lsaquo; Retour</a>
        {% include "caisse/_onglets_gerer.html" with actif="evenements" %}
    </div>
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="mb-0">Événements - {{ pole.nom }}</h1>
        <a href="{% url 'creer_evenement' pole.slug %}" class="btn btn-primary">+ Nouvel événement</a>
    </div>

    {% for evenement in evenements %}
        <a href="{% url 'modifier_evenement' pole.slug evenement.id %}" class="text-decoration-none">
            <div class="card shadow-sm mb-3 overflow-hidden {% if not evenement.actif %}opacity-50{% endif %}">
                <div class="position-relative">
                    {% if evenement.photo %}
                        <img src="{{ evenement.photo.url }}" style="width:100%;height:160px;object-fit:cover;">
                    {% else %}
                        <div style="width:100%;height:160px;background:linear-gradient(135deg,#1E1B4B,#431407);display:flex;align-items:center;justify-content:center;">
                            <span class="text-white fw-bold text-uppercase" style="letter-spacing:2px;">{{ evenement.nom }}</span>
                        </div>
                    {% endif %}
                    <span class="position-absolute top-0 start-0 m-2 badge {% if evenement.actif %}bg-success{% else %}bg-secondary{% endif %}">
                        {% if evenement.actif %}Actif{% else %}Terminé{% endif %}
                    </span>
                </div>
                <div class="card-body">
                    <h5 class="card-title mb-2 text-dark">{{ evenement.nom }}</h5>
                    <div class="text-muted small mb-1">
                        {% if evenement.date_evenement %}{{ evenement.date_evenement|date:"l d F Y, H:i" }}{% else %}Date non définie{% endif %}
                    </div>
                    {% if evenement.lieu %}
                        <div class="text-muted small">{{ evenement.lieu }}</div>
                    {% endif %}
                </div>
            </div>
        </a>
    {% empty %}
        <p class="text-muted">Aucun événement pour ce pôle.</p>
    {% endfor %}
{% endblock %}
```

`caisse/templates/caisse/evenement_form.html` (le lien « Participants » ne
fonctionnera qu'une fois la Partie 6.4 construite, mais avoir le lien dès
maintenant ne casse rien) :

```html
{% extends "caisse/base.html" %}

{% block titre %}{{ titre }}{% endblock %}

{% block contenu %}
    <a href="{% url 'gerer_evenements' pole.slug %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>

    <div class="d-flex justify-content-between align-items-start mb-4 flex-wrap gap-2">
        <h1 class="mb-0">{{ titre }}</h1>
        {% if evenement %}
            <div class="d-flex gap-2">
                <a href="{% url 'participants_evenement' pole.slug evenement.id %}" class="btn btn-primary btn-sm">Participants</a>
            </div>
        {% endif %}
    </div>

    <div class="row justify-content-center mb-4">
        <div class="col-md-6">
            <div class="card shadow-sm">
                <div class="card-body">
                    {% if evenement.photo %}
                        <img src="{{ evenement.photo.url }}" class="mb-3" style="max-width:160px;border-radius:8px;">
                    {% endif %}
                    <form method="post" enctype="multipart/form-data">
                        {% csrf_token %}
                        <div class="mb-3">
                            <label class="form-label">Nom</label>
                            {{ form.nom }}
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Date et heure</label>
                            {{ form.date_evenement }}
                            {% if form.date_evenement.errors %}<div class="text-danger small mt-1">{{ form.date_evenement.errors.0 }}</div>{% endif %}
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Lieu</label>
                            {{ form.lieu }}
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Photo</label>
                            {{ form.photo }}
                            {% if form.photo.errors %}<div class="text-danger small mt-1">{{ form.photo.errors.0 }}</div>{% endif %}
                            <p class="text-muted small mt-1">5 Mo maximum.</p>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Fin de vente (optionnel)</label>
                            {{ form.date_fin_vente }}
                            {% if form.date_fin_vente.errors %}<div class="text-danger small mt-1">{{ form.date_fin_vente.errors.0 }}</div>{% endif %}
                            <p class="text-muted small mb-0">À partir de cette date/heure, plus rien n'est vendable pour cet événement, même si "Actif" reste coché.</p>
                        </div>
                        <div class="form-check mb-3">
                            {{ form.actif }}
                            <label class="form-check-label">Actif (visible et vendable à la caisse)</label>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Enregistrer</button>
                    </form>
                </div>
            </div>
        </div>
    </div>

    {% if evenement %}
        <ul class="nav nav-tabs mb-3" id="catalogueTab" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="billets-tab" data-bs-toggle="tab" data-bs-target="#billets" type="button" role="tab" aria-controls="billets" aria-selected="true">
                    Billets (entrées)
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="catalogue-tab" data-bs-toggle="tab" data-bs-target="#catalogue" type="button" role="tab" aria-controls="catalogue" aria-selected="false">
                    Catalogue de la soirée
                </button>
            </li>
        </ul>

        <div class="tab-content" id="catalogueTabContent">
            <div class="tab-pane fade show active" id="billets" role="tabpanel" aria-labelledby="billets-tab">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="mb-0">Billets</h5>
                    <a href="{% url 'creer_billet' pole.slug evenement.id %}?type=billet" class="btn btn-primary btn-sm">+ Ajouter un billet</a>
                </div>
                <div class="table-responsive">
                    <table class="table align-middle bg-white shadow-sm">
                        <thead>
                            <tr><th>Photo</th><th>Nom</th><th>Prix</th><th>Stock</th><th>Disponible</th><th></th></tr>
                        </thead>
                        <tbody>
                            {% for billet in billets %}
                                <tr>
                                    <td>
                                        {% if billet.photo %}
                                            <img src="{{ billet.photo.url }}" style="width:40px;height:40px;object-fit:cover;border-radius:6px;">
                                        {% else %}<span class="text-muted small">Aucune</span>{% endif %}
                                    </td>
                                    <td>{{ billet.nom }}</td>
                                    <td>{{ billet.prix|floatformat:2 }} EUR</td>
                                    <td>
                                        {% if billet.stock is None %}<span class="text-muted">illimité</span>
                                        {% elif billet.stock == 0 %}<span class="badge bg-danger">0</span>
                                        {% else %}{{ billet.stock }}{% endif %}
                                    </td>
                                    <td>{% if billet.disponible %}<span class="badge bg-success">Oui</span>{% else %}<span class="badge bg-secondary">Non</span>{% endif %}</td>
                                    <td><a href="{% url 'modifier_billet' pole.slug evenement.id billet.id %}" class="btn btn-sm btn-outline-primary">Modifier</a></td>
                                </tr>
                            {% empty %}
                                <tr><td colspan="6" class="text-muted text-center py-3">Aucun billet pour le moment.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="tab-pane fade" id="catalogue" role="tabpanel" aria-labelledby="catalogue-tab">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="mb-0">Catalogue de la soirée</h5>
                    <a href="{% url 'creer_billet' pole.slug evenement.id %}?type=catalogue" class="btn btn-primary btn-sm">+ Ajouter un produit</a>
                </div>
                <div class="table-responsive">
                    <table class="table align-middle bg-white shadow-sm">
                        <thead>
                            <tr><th>Photo</th><th>Nom</th><th>Prix</th><th>Stock</th><th>Disponible</th><th></th></tr>
                        </thead>
                        <tbody>
                            {% for produit in catalogue %}
                                <tr>
                                    <td>
                                        {% if produit.photo %}
                                            <img src="{{ produit.photo.url }}" style="width:40px;height:40px;object-fit:cover;border-radius:6px;">
                                        {% else %}<span class="text-muted small">Aucune</span>{% endif %}
                                    </td>
                                    <td>{{ produit.nom }}</td>
                                    <td>{{ produit.prix|floatformat:2 }} EUR</td>
                                    <td>
                                        {% if produit.stock is None %}<span class="text-muted">illimité</span>
                                        {% elif produit.stock == 0 %}<span class="badge bg-danger">0</span>
                                        {% else %}{{ produit.stock }}{% endif %}
                                    </td>
                                    <td>{% if produit.disponible %}<span class="badge bg-success">Oui</span>{% else %}<span class="badge bg-secondary">Non</span>{% endif %}</td>
                                    <td><a href="{% url 'modifier_billet' pole.slug evenement.id produit.id %}" class="btn btn-sm btn-outline-primary">Modifier</a></td>
                                </tr>
                            {% empty %}
                                <tr><td colspan="6" class="text-muted text-center py-3">Aucun produit dans le catalogue de la soirée.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    {% else %}
        <p class="text-muted small">Le catalogue de la soirée (billets, écocups...) pourra être ajouté une fois l'événement enregistré.</p>
    {% endif %}

    <script>
        function formaterDateHeure(champ) {
            var chiffres = champ.value.replace(/\D/g, "").slice(0, 12);
            var jour = chiffres.slice(0, 2);
            var mois = chiffres.slice(2, 4);
            var annee = chiffres.slice(4, 8);
            var heure = chiffres.slice(8, 10);
            var minute = chiffres.slice(10, 12);
            if (jour.length === 2 && parseInt(jour, 10) > 31) { jour = "31"; }
            if (mois.length === 2 && parseInt(mois, 10) > 12) { mois = "12"; }
            if (heure.length === 2 && parseInt(heure, 10) > 23) { heure = "23"; }
            if (minute.length === 2 && parseInt(minute, 10) > 59) { minute = "59"; }
            var formate = jour;
            if (chiffres.length > 2) { formate += "/" + mois; }
            if (chiffres.length > 4) { formate += "/" + annee; }
            if (chiffres.length > 8) { formate += " " + heure; }
            if (chiffres.length > 10) { formate += ":" + minute; }
            champ.value = formate;
        }
        ["id_date_evenement", "id_date_fin_vente"].forEach(function (id) {
            var champ = document.getElementById(id);
            if (champ) {
                champ.addEventListener("input", function () { formaterDateHeure(champ); });
            }
        });
    </script>
{% endblock %}
```

Et `caisse/templates/caisse/billet_form.html` :

```html
{% extends "caisse/base.html" %}

{% block titre %}{{ titre }}{% endblock %}

{% block contenu %}
    <a href="{% url 'modifier_evenement' pole.slug evenement.id %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <h1 class="mb-4">{{ titre }}</h1>

    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card shadow-sm">
                <div class="card-body">
                    {% if billet.photo %}
                        <img src="{{ billet.photo.url }}" class="mb-3" style="max-width:120px;border-radius:8px;">
                    {% endif %}
                    <form method="post" enctype="multipart/form-data">
                        {% csrf_token %}
                        <div class="mb-3">
                            <label class="form-label">Nom</label>
                            {{ form.nom }}
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Prix (EUR)</label>
                            {{ form.prix }}
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Stock (laisser vide = illimité)</label>
                            {{ form.stock }}
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Photo</label>
                            {{ form.photo }}
                            {% if form.photo.errors %}<div class="text-danger small mt-1">{{ form.photo.errors.0 }}</div>{% endif %}
                            <p class="text-muted small mt-1">5 Mo maximum.</p>
                        </div>
                        <div class="form-check mb-2">
                            {{ form.est_billet }}
                            <label class="form-check-label">
                                Compte comme une entrée (apparaît dans la liste des
                                participants et se synchronise avec HelloAsso).
                                Décoche pour un simple produit du catalogue (boisson, écocup...).
                            </label>
                        </div>
                        <div class="form-check mb-3">
                            {{ form.disponible }}
                            <label class="form-check-label">Disponible à la vente</label>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Enregistrer</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
{% endblock %}
```

Enfin, ajoute les routes dans `caisse/urls.py` :

```python
path("pole/<slug:slug>/gerer/evenements/", views.gerer_evenements, name="gerer_evenements"),
path("pole/<slug:slug>/gerer/evenements/nouveau/", views.creer_evenement, name="creer_evenement"),
path("pole/<slug:slug>/gerer/evenements/<int:evenement_id>/", views.modifier_evenement, name="modifier_evenement"),
path("pole/<slug:slug>/gerer/evenements/<int:evenement_id>/billets/nouveau/", views.creer_billet, name="creer_billet"),
path("pole/<slug:slug>/gerer/evenements/<int:evenement_id>/billets/<int:produit_id>/", views.modifier_billet, name="modifier_billet"),
```

### 6.4 Participants : vue interne, import HelloAsso, export nominatif

Certains événements ont leur billetterie/argent géré **hors** de
l'application (HelloAsso) : `ParticipantImporte` permet de lister
nominativement qui a réservé, **sans jamais créer le moindre mouvement
d'argent**.

Dans `caisse/views.py`, à la suite du reste (ajoute `LigneTransaction` à
l'import `.models` s'il n'y est pas déjà, et `csv`, `io` en imports
standards en tête de fichier, `io` est déjà là depuis la Partie 5.2) :

```python
import csv
```

```python
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
```

L'import CSV détecte automatiquement le délimiteur (`;` généralement utilisé
par les exports français) et les noms de colonnes, avec une marge de
tolérance car aucun vrai export HelloAsso n'a pu être testé pendant le
développement. Toujours dans `caisse/views.py`, à la suite (ajoute
`ParticipantImporte` à l'import `.models`) :

```python
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
```

Deux templates. `caisse/templates/caisse/participants_evenement.html` — le
bouton « Exporter Excel » pointe vers `exporter_participants`, une vue
construite bien plus tard (Partie 12.3) : laisse ce bouton de côté pour
l'instant, on l'ajoutera à ce moment-là :

```html
{% extends "caisse/base.html" %}

{% block titre %}Participants - {{ evenement.nom }}{% endblock %}

{% block contenu %}
    <a href="{% url 'modifier_evenement' pole.slug evenement.id %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>

    <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="mb-0">{{ evenement.nom }}</h1>
        <div class="d-flex gap-2">
            <a href="{% url 'importer_participants' pole.slug evenement.id %}" class="btn btn-primary">
                Importer depuis HelloAsso
            </a>
        </div>
    </div>

    <div class="card shadow-sm mb-3">
        <div class="card-body text-center">
            <span class="text-muted">Total billets</span>
            <div class="display-6 fw-bold">{{ total_billets }}</div>
        </div>
    </div>

    <div class="card shadow-sm">
        <div class="card-body p-0">
            <table class="table table-hover mb-0">
                <thead class="table-light">
                    <tr>
                        <th>Nom</th>
                        <th>Quantité</th>
                        <th>Date</th>
                        <th>Source</th>
                        <th>HelloAsso</th>
                    </tr>
                </thead>
                <tbody>
                    {% for p in participants %}
                        <tr>
                            <td>{{ p.nom }}</td>
                            <td>{{ p.quantite }}</td>
                            <td>{{ p.date|date:"d/m/Y H:i" }}</td>
                            <td>
                                {% if p.source == "Interne" %}
                                    <span class="badge bg-success">Interne</span>
                                {% else %}
                                    <span class="badge bg-primary">HelloAsso</span>
                                {% endif %}
                            </td>
                            <td>
                                {% if p.reference_helloasso %}
                                    <span class="badge bg-primary" title="{{ p.reference_helloasso }}">Synchronisé</span>
                                {% elif p.source == "Interne" %}
                                    <span class="text-muted small">-</span>
                                {% endif %}
                            </td>
                        </tr>
                    {% empty %}
                        <tr><td colspan="5" class="text-muted text-center py-3">Personne n'a encore pris de billet.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
{% endblock %}
```

Et `caisse/templates/caisse/importer_participants.html` :

```html
{% extends "caisse/base.html" %}

{% block titre %}Importer des participants - {{ evenement.nom }}{% endblock %}

{% block contenu %}
    <a href="{% url 'participants_evenement' pole.slug evenement.id %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>

    <h1 class="mb-4">Importer des participants</h1>

    <div class="card shadow-sm">
        <div class="card-body">
            <h5 class="card-title">{{ evenement.nom }}</h5>
            <p class="text-muted">
                Importe ici le fichier CSV téléchargé depuis le back-office HelloAsso.
                Les colonnes <strong>Nom</strong> et <strong>Prénom</strong> seront
                automatiquement détectées. Aucun mouvement d'argent n'est associé :
                il s'agit uniquement d'un suivi opérationnel des participants.
            </p>

            {% if erreur %}
                <div class="alert alert-danger">{{ erreur }}</div>
            {% endif %}

            <form method="post" enctype="multipart/form-data">
                {% csrf_token %}
                <div class="mb-3">
                    <label for="fichier" class="form-label">Fichier CSV</label>
                    <input type="file" class="form-control" id="fichier" name="fichier" accept=".csv" required>
                </div>
                <button type="submit" class="btn btn-primary">Importer</button>
            </form>
        </div>
    </div>
{% endblock %}
```

Ajoute les routes dans `caisse/urls.py` :

```python
path("pole/<slug:slug>/gerer/evenements/<int:evenement_id>/participants/importer/", views.importer_participants, name="importer_participants"),
path("pole/<slug:slug>/gerer/evenements/<int:evenement_id>/participants/", views.participants_evenement, name="participants_evenement"),
```

**Synchronisation automatique inverse vers HelloAsso.** Cette partie est
**déjà en place** : le code ci-dessous a été écrit dans `encaisser` en
Partie 3.3 (avec le fichier provisoire `caisse/helloasso.py`), rien à
retaper, seul le contenu du fichier `helloasso.py` change ici. Plutôt qu'un import
ponctuel après coup, chaque vente d'un vrai billet (`est_billet=True`) pousse
automatiquement l'inscription vers HelloAsso, via une fonction isolée dans un
module dédié. Remplace le contenu provisoire de `caisse/helloasso.py` (écrit
en Partie 3.3, qui se contentait de renvoyer `None`) par cette version :

```python
# caisse/helloasso.py
def inscrire_sur_helloasso(evenement, profil, quantite):
    """Pousse l'inscription vers HelloAsso. Isole entierement l'appel API
    reel (a implementer selon les identifiants HelloAsso du pole) pour que
    l'appel de vente ne puisse jamais echouer a cause d'un probleme reseau
    ou d'API : toute erreur ici est absorbee silencieusement."""
    try:
        # TODO : appel reel a l'API HelloAsso, retourne une reference si succes
        return None
    except Exception:
        return None
```

Pour rappel, cette fonction est appelée dans `encaisser` uniquement pour les
vrais billets, jamais pour un produit du catalogue de soirée (code déjà en
place depuis la Partie 3.3, rien à modifier ici) :

```python
if produit.evenement_id and produit.est_billet:
    ref = inscrire_sur_helloasso(produit.evenement, profil, quantite)
    if ref:
        ligne_tx.reference_helloasso = ref
        ligne_tx.save(update_fields=["reference_helloasso"])
```

Le fait d'isoler cet appel dans son propre module, avec un `try/except` qui
ne laisse **jamais** une erreur d'API distante remonter jusqu'à l'échec
d'une vraie vente en espèces réelles, est un principe transposable à toute
intégration externe non critique : un service tiers indisponible ne doit
jamais bloquer une transaction financière interne déjà validée.

### 6.5 `est_billet` : un vrai bug de fond corrigé

Au départ, aucune distinction n'existait entre une vraie entrée (compte
comme présence, se synchronise avec HelloAsso) et un simple produit du
catalogue de soirée (boisson, écocup) vendu ce soir-là mais qui ne représente
aucune présence. Le champ `est_billet` (Partie 1.2) corrige cette confusion,
et `evenement_form.html` sépare visuellement les deux catégories en onglets
(« Billets » / « Catalogue de la soirée »), avec deux points d'entrée
distincts pour créer l'un ou l'autre :

```python
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
    return render(request, "caisse/billet_form.html", {"pole": pole, "evenement": evenement, "form": form, "titre": titre})
```

`exporter_participants` (Partie 12) et `participants_evenement` filtrent
systématiquement `produit__est_billet=True`, pour que le catalogue de soirée
n'apparaisse jamais dans la liste des présences.

---

## Partie 7 - Espace Asso (tableau de bord d'un pôle)

### 7.1 Le sélecteur et le tableau de bord

Dans `caisse/views.py`, ajoute ces imports (beaucoup de fonctions de
permission d'un coup, toutes déjà écrites dans `caisse/roles.py` en Partie
2, jamais encore utilisées jusqu'ici) :

```python
from django.db.models import Sum
from django.utils import timezone

from .models import Transaction
from .roles import (
    peut_encaisser_adhesion_especes, peut_exporter, peut_gerer_adhesions,
    peut_modifier_parametres, peut_recharger_especes, peut_voir_equipe,
    peut_voir_suivi_especes, poles_gerables,
)
```

(`Transaction`, `Pole`, `timezone` sont peut-être déjà importés chez toi
selon l'ordre dans lequel tu as suivi le tutoriel — n'ajoute que ce qui
manque réellement, `python manage.py check` te dira s'il reste un import en
double ou manquant.)

Puis, à la suite du reste du fichier :

```python
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
```

Le template `espace_asso.html` rend chaque carte-bouton conditionnellement à
son droit précis - jamais un seul `{% if peut_gerer %}` englobant, ce qui
permettrait à un vendeur avec des droits supplémentaires d'accéder aux
bonnes actions sans jamais voir celles qui ne le concernent pas.

**Attention avant de coller ce template : sa version finale contient neuf
boutons, dont six pointent vers des pages qui n'existent pas encore**
(`recharger_especes`, `payer_adhesion_especes`, `gerer_especes` → Partie 9 ;
`gerer_adherents` → Partie 8 ; `export_pole` → Partie 12 ; `modifier_pole` →
Partie 7.3). Comme `{% url %}` est évalué à l'affichage de la page (pas
seulement au clic), et que ces blocs s'afficheraient tous pour un compte
superuser (`peut_gerer` renvoie vrai pour lui), coller la version finale
maintenant ferait planter la page dès que tu l'ouvres. Crée
`caisse/templates/caisse/espace_asso.html` avec seulement ce qui existe
déjà (Vendre, Gérer) :

```html
{% extends "caisse/base.html" %}

{% block titre %}Asso - {{ pole.nom }}{% endblock %}

{% block contenu %}
    {% if plusieurs_poles %}
        <a href="{% url 'asso_choix' %}" class="btn btn-outline-secondary btn-sm mb-3">&lsaquo; Retour</a>
    {% else %}
        <a href="{% url 'accueil' %}" class="btn btn-outline-secondary btn-sm mb-3">&lsaquo; Retour</a>
    {% endif %}

    <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="mb-0">Espace Asso</h1>
        <span class="badge" style="background:var(--ensea-light);color:var(--ensea);">{{ pole.nom }} ENSEA</span>
    </div>

    <div class="card shadow-sm text-center mb-4">
        <div class="card-body py-4">
            <div class="display-5 fw-bold" style="color:var(--ensea);">{{ recette_mois|floatformat:2 }} EUR</div>
            {% now "F Y" as mois_courant %}
            <div class="fw-bold">Recette de {{ mois_courant|capfirst }}</div>
            <div class="text-muted small mt-1">Mise à jour à l'instant</div>
        </div>
    </div>

    <div class="d-flex flex-column gap-2">

        {% if peut_vendre %}
        <a href="{% url 'detail_pole' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Vendre</div>
                        <div class="text-muted small">Interface caisse et encaissement</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}

        {% if peut_gerer_produits %}
        <a href="{% url 'gerer_produits' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Gérer</div>
                        <div class="text-muted small">Catalogue, prix et stocks</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}

    </div>
{% endblock %}
```

On complètera ce fichier morceau par morceau, exactement comme `base.html` :
- le bouton **Équipe** juste après la Partie 7.2 (juste en dessous, ça
  arrive tout de suite) ;
- le bouton **Paramètres** après la Partie 7.3 ;
- le bouton **Adhésions** après la Partie 8.2 ;
- le bouton **Adhésion en espèces** après la Partie 8.3 ;
- les boutons **Recharger en espèces** et **Suivi espèces** après la Partie 9 ;
- le bouton **Exporter** après la Partie 12.

**Un bug d'apparence anodine à retenir**, pour quand tu ajouteras les
boutons espèces en Partie 9 : une condition trop large comme `{% if
peut_vendre and not peut_gerer %}` sur ces tuiles excluait par erreur *tout*
admin de pôle, y compris ceux qui devraient légitimement les voir. La bonne
condition, `{% if peut_recharger %}` (comme ci-dessus pour les deux autres
boutons), est pensée droit par droit, jamais par déduction combinatoire
hâtive.

Il reste `caisse/templates/caisse/asso_choix.html`, affiché quand
l'utilisateur a accès à plusieurs pôles :

```html
{% extends "caisse/base.html" %}

{% block titre %}Espace Asso{% endblock %}

{% block contenu %}
    <h1 class="mb-4">Espace Asso</h1>

    <div class="card shadow-sm text-center mb-4">
        <div class="card-body py-4">
            <div class="display-5 fw-bold" style="color:var(--ensea);">{{ recette_totale|floatformat:2 }} EUR</div>
            {% now "F Y" as mois_courant %}
            <div class="fw-bold">Recette de {{ mois_courant|capfirst }}</div>
            <div class="text-muted small mt-1">Toutes assos confondues</div>
        </div>
    </div>

    <p class="text-muted small mb-2">Choisis le pôle à ouvrir</p>
    <div class="d-flex flex-column gap-2">
        {% for pole in poles %}
            <a href="{% url 'espace_asso' pole.slug %}" class="card shadow-sm text-decoration-none">
                <div class="card-body d-flex align-items-center justify-content-between py-3">
                    <div class="d-flex align-items-center gap-3">
                        {% if pole.logo %}
                            <img src="{{ pole.logo.url }}" style="width:44px;height:44px;object-fit:cover;border-radius:12px;">
                        {% else %}
                            <div class="icone-action">
                                <svg viewBox="0 0 24 24"><path d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10z"/></svg>
                            </div>
                        {% endif %}
                        <span class="fw-bold">{{ pole.nom }}</span>
                    </div>
                    <span class="text-muted">&rsaquo;</span>
                </div>
            </a>
        {% empty %}
            <p class="text-muted">Aucun pôle accessible.</p>
        {% endfor %}
    </div>
{% endblock %}
```

Ce template utilise `.icone-action`, déjà présent dans `base.html` depuis la
Partie 5.5.

Enfin, ajoute les routes dans `caisse/urls.py` :

```python
path("asso/", views.asso_choix, name="asso_choix"),
path("pole/<slug:slug>/asso/", views.espace_asso, name="espace_asso"),
```

Maintenant que `espace_asso` existe, tu peux corriger les boutons "Retour"
laissés provisoirement sur `accueil` : dans `pole.html` (Partie 3.2),
`gerer_produits.html` (6.1) et `gerer_evenements.html` (6.3), remplace
`{% url 'accueil' %}` par `{% url 'espace_asso' pole.slug %}`.

Sans plus, rien ne permet d'atteindre `espace_asso` depuis l'interface : la
barre d'onglets en bas de l'écran (`base.html`, Partie 5.5) ne connaît que
Accueil/Terminal/Payer/Recharger/Info. Ajoute un onglet « Asso », juste
après le bloc `{% if a_droits_vente %}...Terminal...{% endif %}` de
`caisse/templates/caisse/base.html` :

```html
        {% if a_droits_vente %}
        <a class="onglet {% if onglet == 'asso_choix' or onglet == 'espace_asso' or onglet == 'detail_pole' or onglet == 'gerer_produits' or onglet == 'equipe_pole' %}actif{% endif %}" href="{% url 'asso_choix' %}">
            <svg viewBox="0 0 24 24"><path d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10z"/></svg>
            Asso
        </a>
        {% endif %}
```

`a_droits_vente` vient du context processor `droits_navigation` (Partie
2.2) et vaut vrai dès que l'utilisateur a un droit de vente ou de gestion
sur au moins un pôle - exactement la même condition que pour l'onglet
Terminal, donc rien à changer côté vue. Relance le serveur : l'onglet
« Asso » doit apparaître en bas de l'écran.

### 7.2 Équipe et droits (le formulaire de gestion complet)

D'abord, dans `caisse/views.py`, complète l'import de `.roles` ajouté en
7.1 : il manque `est_admin_ade` et `peut_modifier_equipe`. Remplace la ligne
`from .roles import (...)` par :

```python
from .roles import (
    est_admin_ade, peut_encaisser_adhesion_especes, peut_exporter,
    peut_gerer_adhesions, peut_modifier_equipe, peut_modifier_parametres,
    peut_recharger_especes, peut_voir_equipe, peut_voir_suivi_especes,
    poles_gerables,
)
```

Puis, toujours dans `caisse/views.py`, à la suite du reste du fichier (donc
après `espace_asso`), ajoute `DROITS_SUPPLEMENTAIRES` et la vue
`equipe_pole` :

```python
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
```

Une checkbox HTML **non cochée n'est jamais envoyée dans le POST** - c'est un
comportement natif du navigateur, pas un bug Django. C'est pourquoi
`setattr(affectation, champ, champ in request.POST)` fonctionne
correctement : sa présence dans `request.POST` signifie coché, son absence
signifie décoché - jamais l'inverse d'un `request.POST.get(champ, False)`
qui donnerait un résultat identique dans les deux cas (`None` ou `""`, tous
deux falsy).

Le template `equipe_pole.html` enchaîne deux modales de confirmation avant
tout retrait - y compris quand le retrait est déclenché **depuis
l'intérieur** de la modale des droits, ce qui demande un petit relais JS
entre la fermeture de la première modale et l'ouverture de la seconde
(`hidden.bs.modal` → ouverture de la modale de confirmation). Crée le
fichier `caisse/templates/caisse/equipe_pole.html` :

```html
{% extends "caisse/base.html" %}

{% block titre %}Équipe {{ pole.nom }}{% endblock %}

{% block contenu %}
    <a href="{% url 'espace_asso' pole.slug %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <h1 class="mb-4">Équipe - {{ pole.nom }}</h1>
    {% if erreur %}
        <div class="alert alert-danger">{{ erreur }}</div>
    {% endif %}

    {% if peut_modifier %}
    <div class="card shadow-sm mb-4">
        <div class="card-body">
            <h6 class="mb-3">Ajouter un droit</h6>
            <form method="post" class="row g-2">
                {% csrf_token %}
                <div class="col-12 col-sm-6">
                    <input type="text" name="identifiant" class="form-control" placeholder="identifiant école" required>
                </div>
                <div class="col-8 col-sm-4">
                    <select name="role" class="form-select">
                        <option value="VENDEUR">Vendeur</option>
                        <option value="ADMIN_POLE">Admin de pôle</option>
                    </select>
                </div>
                <div class="col-4 col-sm-2">
                    <button type="submit" name="ajouter" value="1" class="btn btn-primary w-100">Ajouter</button>
                </div>
            </form>
        </div>
    </div>
    {% endif %}

    <h6 class="text-muted text-uppercase mb-2">Membres actuels</h6>
    {% for a in affectations %}
        <div class="card shadow-sm mb-2">
            <div class="card-body d-flex justify-content-between align-items-center py-2">
                <div>
                    <span class="fw-bold">
                        {% if a.user.first_name or a.user.last_name %}
                            {{ a.user.first_name }} {{ a.user.last_name }}
                        {% else %}
                            {{ a.user.username }} <span class="badge bg-secondary">Identifiant</span>
                        {% endif %}
                    </span>
                    <span class="badge bg-secondary ms-2">{{ a.get_role_display }}</span>
                </div>
                {% if peut_modifier %}
                    {% if a.role == "VENDEUR" %}
                        <button type="button" class="btn btn-sm btn-outline-primary" data-bs-toggle="modal" data-bs-target="#modaleDroits{{ a.id }}">Modifier</button>
                    {% elif a.role == "ADMIN_POLE" and admin_ade %}
                        <button type="button" class="btn btn-sm btn-outline-primary" data-bs-toggle="modal" data-bs-target="#modaleDroits{{ a.id }}">Modifier</button>
                    {% else %}
                        <button type="button" class="btn btn-sm btn-outline-danger"
                                data-affectation-id="{{ a.id }}"
                                data-nom="{% if a.user.first_name or a.user.last_name %}{{ a.user.first_name }} {{ a.user.last_name }}{% else %}{{ a.user.username }}{% endif %}"
                                onclick="declencherRetrait(this)">Retirer</button>
                    {% endif %}
                {% endif %}
            </div>
        </div>

        {% if peut_modifier and a.role == "VENDEUR" or peut_modifier and a.role == "ADMIN_POLE" and admin_ade %}
        <div class="modal fade" id="modaleDroits{{ a.id }}" tabindex="-1">
            <div class="modal-dialog modal-dialog-scrollable">
                <div class="modal-content">
                    <div class="modal-header">
                        <div class="d-flex align-items-center gap-2">
                            <div class="avatar-utilisateur" style="width:32px;height:32px;font-size:11px;">
                                {% if a.user.first_name or a.user.last_name %}{{ a.user.first_name|first|upper }}{{ a.user.last_name|first|upper }}{% else %}{{ a.user.username|slice:":2"|upper }}{% endif %}
                            </div>
                            <h5 class="modal-title mb-0">
                                Droits de
                                {% if a.user.first_name or a.user.last_name %}{{ a.user.first_name }} {{ a.user.last_name }}{% else %}{{ a.user.username }}{% endif %}
                            </h5>
                        </div>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <form method="post">
                        {% csrf_token %}
                        <input type="hidden" name="affectation" value="{{ a.id }}">
                        <div class="modal-body">
                            {% if a.role == "VENDEUR" %}
                            <p class="text-muted small">
                                Un vendeur peut encaisser les ventes par défaut. Active ici les accès
                                supplémentaires autorisés.
                            </p>
                            <label class="d-flex justify-content-between align-items-center py-2 border-bottom">
                                <span>
                                    <span class="d-block fw-bold small">Adhésion en espèces</span>
                                    <span class="d-block text-muted" style="font-size:11px;">Encaisser une cotisation en liquide</span>
                                </span>
                                <span class="form-check form-switch mb-0">
                                    <input class="form-check-input" type="checkbox" role="switch" name="droit_adhesion_especes" {% if a.droit_adhesion_especes %}checked{% endif %}>
                                </span>
                            </label>
                            <label class="d-flex justify-content-between align-items-center py-2 border-bottom">
                                <span>
                                    <span class="d-block fw-bold small">Gérer</span>
                                    <span class="d-block text-muted" style="font-size:11px;">Catalogue, prix et stocks</span>
                                </span>
                                <span class="form-check form-switch mb-0">
                                    <input class="form-check-input" type="checkbox" role="switch" name="droit_gerer_produits" {% if a.droit_gerer_produits %}checked{% endif %}>
                                </span>
                            </label>
                            <label class="d-flex justify-content-between align-items-center py-2 border-bottom">
                                <span>
                                    <span class="d-block fw-bold small">Adhésions</span>
                                    <span class="d-block text-muted" style="font-size:11px;">Prix, liste des adhérents et export</span>
                                </span>
                                <span class="form-check form-switch mb-0">
                                    <input class="form-check-input" type="checkbox" role="switch" name="droit_adhesions" {% if a.droit_adhesions %}checked{% endif %}>
                                </span>
                            </label>
                            <label class="d-flex justify-content-between align-items-center py-2 border-bottom">
                                <span>
                                    <span class="d-block fw-bold small">Équipe</span>
                                    <span class="d-block text-muted" style="font-size:11px;">Voir qui a quels droits, jamais modifier</span>
                                </span>
                                <span class="form-check form-switch mb-0">
                                    <input class="form-check-input" type="checkbox" role="switch" name="droit_equipe" {% if a.droit_equipe %}checked{% endif %}>
                                </span>
                            </label>
                            <label class="d-flex justify-content-between align-items-center py-2 border-bottom">
                                <span>
                                    <span class="d-block fw-bold small">Exporter</span>
                                    <span class="d-block text-muted" style="font-size:11px;">Ventes au format Excel</span>
                                </span>
                                <span class="form-check form-switch mb-0">
                                    <input class="form-check-input" type="checkbox" role="switch" name="droit_exporter" {% if a.droit_exporter %}checked{% endif %}>
                                </span>
                            </label>
                            <label class="d-flex justify-content-between align-items-center py-2 border-bottom">
                                <span>
                                    <span class="d-block fw-bold small">Paramètres</span>
                                    <span class="d-block text-muted" style="font-size:11px;">Logo du pôle</span>
                                </span>
                                <span class="form-check form-switch mb-0">
                                    <input class="form-check-input" type="checkbox" role="switch" name="droit_parametres" {% if a.droit_parametres %}checked{% endif %}>
                                </span>
                            </label>
                            {% else %}
                            <p class="text-muted small">
                                Un admin de pôle a déjà accès à tout sur son pôle. Seul "Recharger en
                                espèces" reste à accorder au cas par cas, réservé à l'admin ADE.
                            </p>
                            {% endif %}
                            {% if admin_ade %}
                            <label class="d-flex justify-content-between align-items-center py-2">
                                <span>
                                    <span class="d-block fw-bold small">Recharger en espèces</span>
                                    <span class="d-block text-muted" style="font-size:11px;">Créditer un compte contre du liquide (donne aussi accès au suivi espèces)</span>
                                </span>
                                <span class="form-check form-switch mb-0">
                                    <input class="form-check-input" type="checkbox" role="switch" name="droit_recharger_especes" {% if a.droit_recharger_especes %}checked{% endif %}>
                                </span>
                            </label>
                            {% else %}
                            <p class="text-muted small mt-2 mb-0">
                                "Recharger en espèces" ne peut être accordé que par un admin ADE.
                            </p>
                            {% endif %}
                        </div>
                        <div class="modal-footer d-flex gap-2">
                            <button type="button" class="btn btn-outline-danger flex-fill"
                                    data-affectation-id="{{ a.id }}"
                                    data-nom="{% if a.user.first_name or a.user.last_name %}{{ a.user.first_name }} {{ a.user.last_name }}{% else %}{{ a.user.username }}{% endif %}"
                                    data-modale-actuelle="modaleDroits{{ a.id }}"
                                    onclick="declencherRetrait(this)">Retirer le rôle</button>
                            <button type="submit" name="modifier_droits" value="1" class="btn btn-primary flex-fill">Enregistrer</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        {% endif %}
    {% empty %}
        <p class="text-muted">Personne pour le moment.</p>
    {% endfor %}

    <form method="post" id="formRetirer" class="d-none">
        {% csrf_token %}
        <input type="hidden" name="retirer" id="champRetirerId">
    </form>

    <div class="modal fade" id="modaleConfirmerRetrait" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Retirer de l'équipe</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p class="mb-0" id="texteConfirmerRetrait"></p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Annuler</button>
                    <button type="button" class="btn btn-danger" id="btnConfirmerRetrait">Oui, retirer</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        var modaleConfirmerRetraitEl = document.getElementById("modaleConfirmerRetrait");

        function declencherRetrait(bouton) {
            document.getElementById("champRetirerId").value = bouton.dataset.affectationId;
            document.getElementById("texteConfirmerRetrait").textContent =
                "Vous êtes sûr(e) de vouloir retirer " + bouton.dataset.nom + " de l'équipe ?";

            var idModaleActuelle = bouton.dataset.modaleActuelle;
            if (idModaleActuelle) {
                var modaleActuelleEl = document.getElementById(idModaleActuelle);
                modaleActuelleEl.addEventListener("hidden.bs.modal", function surAttente() {
                    modaleActuelleEl.removeEventListener("hidden.bs.modal", surAttente);
                    new bootstrap.Modal(modaleConfirmerRetraitEl).show();
                });
                bootstrap.Modal.getInstance(modaleActuelleEl).hide();
            } else {
                new bootstrap.Modal(modaleConfirmerRetraitEl).show();
            }
        }

        document.getElementById("btnConfirmerRetrait").addEventListener("click", function () {
            document.getElementById("formRetirer").submit();
        });
    </script>
{% endblock %}
```

Enfin, ajoute la route dans `caisse/urls.py` :

```python
path("pole/<slug:slug>/equipe/", views.equipe_pole, name="equipe_pole"),
```

`equipe_pole` existe maintenant : retourne dans
`caisse/templates/caisse/espace_asso.html` (Partie 7.1) et ajoute le bouton
« Équipe », juste après le bloc `{% if peut_gerer_produits %}` et avant la
fermeture du `</div>` :

```html
        {% if peut_equipe %}
        <a href="{% url 'equipe_pole' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Équipe</div>
                        <div class="text-muted small">Vendeurs et droits d'accès</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}
```

Le contexte `espace_asso` (7.1) passe déjà `"peut_equipe":
peut_voir_equipe(request.user, pole)`, donc rien d'autre à changer côté vue.

### 7.3 Paramètres du pôle (logo)

Toujours dans `caisse/forms.py`, ajoute à la suite `PoleForm` :

```python
class PoleForm(forms.ModelForm):
    class Meta:
        model = Pole
        fields = ["logo"]
        widgets = {"logo": forms.ClearableFileInput(attrs={"class": "form-control"})}

    def clean_logo(self):
        return _valider_taille_image(self.cleaned_data.get("logo"))
```

Puis, dans `caisse/views.py`, ajoute l'import de `PoleForm` à la ligne où tu
importes déjà les autres formulaires (`from .forms import ...`), et ajoute
la vue `modifier_pole` à la suite du fichier :

```python
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
```

Avant cette page, seul l'admin Django (non accessible aux admins de pôle)
permettait de déposer un logo. `PoleForm` comble ce manque, réservé au droit
`peut_modifier_parametres` (donc accordable ponctuellement à un vendeur via
`droit_parametres`).

Crée le fichier `caisse/templates/caisse/pole_parametres.html` :

```html
{% extends "caisse/base.html" %}
{% block titre %}Paramètres {{ pole.nom }}{% endblock %}
{% block contenu %}
    <a href="{% url 'espace_asso' pole.slug %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <h1 class="mb-4">Paramètres - {{ pole.nom }}</h1>
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card shadow-sm">
                <div class="card-body">
                    {% if pole.logo %}
                        <img src="{{ pole.logo.url }}" class="mb-3" style="max-width:120px;border-radius:12px;">
                    {% endif %}
                    <form method="post" enctype="multipart/form-data">
                        {% csrf_token %}
                        <div class="mb-3">
                            <label class="form-label">Logo du pôle</label>
                            {{ form.logo }}
                            {% if form.logo.errors %}<div class="text-danger small mt-1">{{ form.logo.errors.0 }}</div>{% endif %}
                            <p class="text-muted small mt-1">Affiché sur l'Espace Asso et la liste d'adhésion. 5 Mo maximum.</p>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Enregistrer</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
{% endblock %}
```

Enfin, ajoute la route dans `caisse/urls.py` :

```python
path("pole/<slug:slug>/parametres/", views.modifier_pole, name="modifier_pole"),
```

`modifier_pole` existe maintenant : retourne dans
`caisse/templates/caisse/espace_asso.html` (Partie 7.1) et ajoute le
bouton « Paramètres », après le bloc `{% if peut_equipe %}` ajouté en 7.2 :

```html
        {% if peut_parametres %}
        <a href="{% url 'modifier_pole' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm8.94 3a8.994 8.994 0 000-2l2.03-1.58a.5.5 0 00.12-.63l-1.92-3.32a.5.5 0 00-.6-.22l-2.39.96a7.03 7.03 0 00-1.72-1l-.36-2.54a.5.5 0 00-.5-.42h-3.84a.5.5 0 00-.5.42l-.36 2.54c-.62.25-1.2.6-1.72 1l-2.39-.96a.5.5 0 00-.6.22L1.28 8.79a.5.5 0 00.12.63L3.43 11a8.994 8.994 0 000 2l-2.03 1.58a.5.5 0 00-.12.63l1.92 3.32a.5.5 0 00.6.22l2.39-.96c.52.4 1.1.75 1.72 1l.36 2.54a.5.5 0 00.5.42h3.84a.5.5 0 00.5-.42l.36-2.54c.62-.25 1.2-.6 1.72-1l2.39.96a.5.5 0 00.6-.22l1.92-3.32a.5.5 0 00-.12-.63L20.94 13z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Paramètres</div>
                        <div class="text-muted small">Logo du pôle</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}
```

Le contexte `espace_asso` (7.1) passe déjà `"peut_parametres":
peut_modifier_parametres(request.user, pole)`, donc rien d'autre à changer
côté vue.

---

## Partie 8 - Adhésions

### 8.1 Tarifs multiples par pôle

Maintenant que cette page va exister, ajoute le bouton laissé de côté en
Partie 5.3 dans `caisse/templates/caisse/accueil.html`, juste après la carte
solde et avant « Dernières transactions » :

```html
<a href="{% url 'adherer_liste' %}" class="bouton-adhesion mb-4">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>
    <span>Devenir adhérent d'un pôle</span>
</a>
```

La classe `bouton-adhesion` n'est pas encore stylée à ce stade (elle
arrivera avec le reste du style visuel commun en Partie 13.5) : ce lien
s'affichera provisoirement comme du texte brut, ce n'est pas un bug, juste
une étape pas encore atteinte.

Puis, dans `caisse/views.py`, ajoute les imports manquants :

```python
from django.db.models import Min
from django.db.utils import IntegrityError
from django.http import Http404

from .models import Adhesion
from .roles import annee_scolaire_courante
```

(`Pole`, `ProfilUtilisateur`, `EchecEncaissement`, `db_transaction` et
`profil_de` sont déjà importés depuis les Parties précédentes. On importe
`annee_scolaire_courante` dès maintenant : elle ne sera présentée en détail
qu'en Partie 8.2, mais on en a besoin ici, tout de suite, voir plus bas
pourquoi.)

Puis la vue elle-même, à la suite du reste du fichier :

```python
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
```

Même schéma `atomic`/`select_for_update`/`EchecEncaissement` que
l'encaissement (Partie 3.3) : payer une adhésion débite le portefeuille tout
comme un achat, il n'y a aucune raison de traiter cette opération
différemment côté fiabilité. L'`IntegrityError` levée par la contrainte
`unique_together` (Partie 1.6) est capturée pour transformer une erreur SQL
brute en message clair.

**Pourquoi `annee_scolaire_courante()` ici, et pas simplement
`timezone.now().year` ?** Parce que l'adhésion espèces (Partie 8.2, plus
loin) utilise elle aussi `annee_scolaire_courante()` pour écrire dans ce même
champ `Adhesion.annee`, avec la même contrainte d'unicité `(pole, profil,
annee)`. Si le chemin portefeuille utilisait l'année civile brute, une
adhésion payée en septembre 2026 par carte serait enregistrée sous « 2026 »
alors qu'une adhésion payée en espèces le même jour serait enregistrée sous
« 2025-2026 » (l'année scolaire n'a basculé qu'en août) : deux paiements pour
la même adhésion réelle ne seraient plus détectés comme un doublon par la
contrainte d'unicité. Les deux chemins de paiement doivent utiliser la même
notion d'année dès le départ, pas seulement celui qui gère l'affichage
administratif.

Le template affiche une confirmation avant paiement (irréversible), avec les
couleurs Bootstrap **volontairement inversées** par rapport à l'intuition
naïve dans une première version, corrigé pour respecter la convention du
reste de l'app (`btn-danger` = Annuler, `btn-success` = Confirmer,
cohérent avec toutes les autres modales de confirmation du projet).

Crée `caisse/templates/caisse/adherer_liste.html` :

```html
{% extends "caisse/base.html" %}

{% block titre %}Adhérer{% endblock %}

{% block contenu %}
    <h1 class="mb-4">Devenir adhérent</h1>
    <div class="d-flex flex-column gap-2">
        {% for pole in poles %}
            <a href="{% url 'adherer_pole' pole.slug %}" class="card shadow-sm text-decoration-none">
                <div class="card-body d-flex align-items-center justify-content-between py-3">
                    <div class="d-flex align-items-center gap-3">
                        {% if pole.logo %}
                            <img src="{{ pole.logo.url }}" style="width:40px;height:40px;object-fit:cover;border-radius:12px;">
                        {% else %}
                            <div class="icone-action">
                                <svg viewBox="0 0 24 24"><path d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10z"/></svg>
                            </div>
                        {% endif %}
                        <div>
                            <div class="fw-bold">{{ pole.nom }}</div>
                            <div class="text-muted small">Adhésion à partir de {{ pole.prix_min|floatformat:2 }} EUR / an</div>
                        </div>
                    </div>
                    <span class="text-muted">&rsaquo;</span>
                </div>
            </a>
        {% empty %}
            <p class="text-muted">Aucun pôle ne propose d'adhésion payante pour le moment.</p>
        {% endfor %}
    </div>
{% endblock %}
```

Puis `caisse/templates/caisse/adherer_pole.html` :

```html
{% extends "caisse/base.html" %}

{% block titre %}Adhérer à {{ pole.nom }}{% endblock %}

{% block contenu %}
<a href="{% url 'adherer_liste' %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>

<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card shadow-sm text-center">
            <div class="card-body p-4">
                <h4>Adhésion {{ pole.nom }}</h4>
                <p class="text-muted">Année {{ annee }}-{{ annee|add:1 }}</p>
                {% if deja_adherent %}
                    <div class="alert alert-success">Tu es déjà adhérent pour cette année.</div>
                {% else %}
                    <div class="d-flex flex-column gap-2 text-start mb-3">
                        {% for t in tarifs %}
                            <label class="d-flex justify-content-between align-items-center border rounded p-2" style="cursor:pointer;">
                                <span>
                                    <input type="radio" name="tarifChoisi" value="{{ t.id }}" data-description="{{ t.description }}" data-prix="{{ t.prix|floatformat:2 }}" class="form-check-input me-2" {% if forloop.first %}checked{% endif %}>
                                    {{ t.description }}
                                </span>
                                <span class="fw-bold">{{ t.prix|floatformat:2 }} EUR</span>
                            </label>
                        {% endfor %}
                    </div>
                    <button type="button" id="btnPayer" class="btn btn-primary w-100 py-2" data-bs-toggle="modal" data-bs-target="#confirmationAdhesion">Payer avec mon portefeuille</button>
                {% endif %}
                {% if erreur %}
                    <div class="alert alert-danger mt-3">{{ erreur }}</div>
                {% endif %}
            </div>
        </div>
    </div>
</div>

    <div class="modal fade" id="confirmationAdhesion" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Confirmer l'adhésion</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>Es-tu sûr de vouloir devenir adhérent de <strong>{{ pole.nom }}</strong> pour {{ annee }}-{{ annee|add:1 }}, au tarif "<span id="descriptionChoisie"></span>" ?</p>
                    <p class="text-danger small mb-0">Attention, cette action est irréversible : <span id="prixChoisi"></span> EUR seront débités immédiatement de ton portefeuille.</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Annuler</button>
                    <form method="post">
                        {% csrf_token %}
                        <input type="hidden" name="tarif" id="champTarifCache">
                        <button type="submit" class="btn btn-success">Confirmer le paiement</button>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <script>
        var btnPayer = document.getElementById("btnPayer");
        if (btnPayer) {
            btnPayer.addEventListener("click", function () {
                var radio = document.querySelector('input[name="tarifChoisi"]:checked');
                document.getElementById("descriptionChoisie").textContent = radio.dataset.description;
                document.getElementById("prixChoisi").textContent = radio.dataset.prix;
                document.getElementById("champTarifCache").value = radio.value;
            });
        }
    </script>
{% endblock %}
```

Enfin, ajoute les deux routes dans `caisse/urls.py` :

```python
path("adherer/", views.adherer_liste, name="adherer_liste"),
path("adherer/<slug:slug>/", views.adherer_pole, name="adherer_pole"),
```

### 8.2 Gestion des adhérents (admin de pôle) et année scolaire

`peut_gerer_adhesions` et `peut_encaisser_adhesion_especes` sont déjà
importés depuis la Partie 7.2, et `annee_scolaire_courante` l'a été dès la
Partie 8.1 : aucun nouvel import à ajouter ici.

À la suite du reste du fichier :

```python
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
```

**Pourquoi une année scolaire (août → août) plutôt que l'année civile ?**
Une cotisation « 2026 » payée en septembre doit rester valide jusqu'en
juillet 2027 - l'année civile brute romprait la continuité pédagogique. La
fonction centralisée `annee_scolaire_courante()` (Partie 2) est utilisée
partout où une année scolaire est nécessaire, jamais recalculée localement.

**Le sélecteur d'année consulte l'historique sans jamais l'altérer** : la
variable affichée (`annee`, pilotée par `?annee=` en GET) et celle utilisée
pour enregistrer un nouveau paiement (`annee_defaut`, toujours l'année
scolaire réelle) sont **délibérément distinctes** - consulter une année
passée ne doit jamais risquer d'enregistrer un paiement dessus par erreur.

Crée `caisse/templates/caisse/gerer_adherents.html`. **Attention, un lien de
ce template pointe vers `exporter_adherents`, qui n'existe qu'à partir de la
Partie 12** : laisse-le de côté pour l'instant, on le rajoutera à ce
moment-là.

```html
{% extends "caisse/base.html" %}

{% block titre %}Adhérents {{ pole.nom }}{% endblock %}

{% block contenu %}
    <div class="d-flex justify-content-between align-items-center mb-3">
        <a href="{% url 'espace_asso' pole.slug %}" class="btn btn-outline-secondary btn-sm">&lsaquo; Retour</a>
        <form method="get" class="d-inline">
            <select name="annee" class="form-select form-select-sm" onchange="this.form.submit()">
                {% for a in annees_disponibles %}
                    <option value="{{ a }}" {% if a == annee %}selected{% endif %}>{{ a }}-{{ a|add:1 }}</option>
                {% endfor %}
            </select>
        </form>
    </div>

    <h1 class="mb-3">Adhérents - {{ pole.nom }}</h1>

    {% if erreur %}
        <div class="alert alert-danger">{{ erreur }}</div>
    {% endif %}

    <div class="card shadow-sm mb-3">
        <div class="card-body">
            <div class="text-muted small text-uppercase mb-2">Tarifs d'adhésion</div>
            {% for t in tarifs %}
                <div class="d-flex justify-content-between align-items-center py-1 border-bottom">
                    <span>{{ t.description }} — <span class="fw-bold">{{ t.prix|floatformat:2 }} EUR</span></span>
                    <form method="post" class="d-inline">
                        {% csrf_token %}
                        <button type="submit" name="retirer_tarif" value="{{ t.id }}" class="btn btn-sm btn-outline-danger">Retirer</button>
                    </form>
                </div>
            {% empty %}
                <p class="text-muted small mb-2">Aucun tarif pour le moment.</p>
            {% endfor %}
            <form method="post" class="d-flex gap-2 mt-2">
                {% csrf_token %}
                <input type="text" name="description" class="form-control" placeholder="Ex. 1ère année">
                <input type="number" step="0.10" name="prix" class="form-control" placeholder="EUR" style="max-width:110px;">
                <button type="submit" name="ajouter_tarif" value="1" class="pilule-action pilule-primaire text-nowrap">Ajouter</button>
            </form>
        </div>
    </div>

    {% if peut_adhesion_especes %}
    <div class="card shadow-sm mb-3">
        <div class="card-body">
            <h6 class="mb-2">Encaisser une adhésion espèces</h6>
            <form method="post" class="d-flex gap-2">
                {% csrf_token %}
                <input type="text" name="identifiant" class="form-control" placeholder="Identifiant étudiant">
                <select name="tarif" class="form-select" style="max-width:200px;">
                    {% for t in tarifs %}
                        <option value="{{ t.id }}">{{ t.description }} — {{ t.prix|floatformat:2 }} EUR</option>
                    {% endfor %}
                </select>
                <button type="submit" name="especes" value="1" class="pilule-action pilule-primaire text-nowrap">Ajouter</button>
            </form>
        </div>
    </div>
    {% endif %}

    <div class="card shadow-sm">
        <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 class="mb-0">Liste des adhérents <span class="badge bg-secondary">{{ adherents|length }}</span></h6>
            </div>
            <p class="text-muted small bg-light rounded p-2">Le détail complet (mode de règlement, date, encaissement) est disponible dans l'export Excel.</p>

            <input type="text" id="rechercheAdherents" class="form-control mb-2" placeholder="Rechercher un adhérent..." oninput="filtrerAdherentsListe()">

            <ul class="list-group list-group-flush" id="listeAdherents">
                {% for a in adherents %}
                    <li class="list-group-item" data-recherche="{% if a.profil.user.first_name or a.profil.user.last_name %}{{ a.profil.user.first_name|lower }} {{ a.profil.user.last_name|lower }}{% else %}{{ a.profil.user.username|lower }}{% endif %}">
                        {% if a.profil.user.first_name or a.profil.user.last_name %}
                            {{ a.profil.user.first_name }} {{ a.profil.user.last_name }}
                        {% else %}
                            {{ a.profil.user.username }} <span class="badge bg-secondary">Identifiant</span>
                        {% endif %}
                    </li>
                {% empty %}
                    <li class="list-group-item text-muted">Aucun adhérent pour {{ annee }}-{{ annee|add:1 }}.</li>
                {% endfor %}
            </ul>
        </div>
    </div>
{% endblock %}

{% block scripts %}
<script>
    function filtrerAdherentsListe() {
        const recherche = document.getElementById('rechercheAdherents').value.trim().toLowerCase();
        document.querySelectorAll('#listeAdherents li[data-recherche]').forEach(function (ligne) {
            ligne.classList.toggle('d-none', !ligne.dataset.recherche.includes(recherche));
        });
    }
</script>
{% endblock %}
```

Enfin, ajoute la route dans `caisse/urls.py` :

```python
path("pole/<slug:slug>/adherents/", views.gerer_adherents, name="gerer_adherents"),
```

`gerer_adherents` existe maintenant : retourne dans
`caisse/templates/caisse/espace_asso.html` et ajoute le bouton
« Adhésions », après le bloc `{% if peut_parametres %}` ajouté en 7.3 :

```html
        {% if peut_adhesions %}
        <a href="{% url 'gerer_adherents' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M20 6h-4V4c0-1.1-.9-2-2-2h-4c-1.1 0-2 .9-2 2v2H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zM10 4h4v2h-4V4zm10 15H4V8h16v11z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Adhésions</div>
                        <div class="text-muted small">Prix, liste des adhérents et export</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}
```

Le contexte `espace_asso` (7.1) passe déjà `"peut_adhesions":
peut_gerer_adhesions(request.user, pole)`, donc rien d'autre à changer côté
vue.

### 8.3 Adhésion en espèces séparée (page dédiée pour les vendeurs)

Un vendeur autorisé à encaisser une adhésion en espèces (`droit_adhesion_especes`)
n'a **aucune raison** de voir la liste complète des adhérents, le prix
modifiable, ou l'export, ces informations relèvent de la gestion complète du
pôle. Plutôt que de complexifier `gerer_adherents.html` avec des blocs
conditionnels par sous-droit (risque de fuite d'information constaté ailleurs
dans le projet), une page **dédiée à une seule action** est plus sûre :
physiquement, elle ne peut rien montrer d'autre que ce pour quoi elle existe.

Dans `caisse/views.py`, à la suite du reste du fichier :

```python
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
```

Crée `caisse/templates/caisse/payer_adhesion_especes.html` :

```html
{% extends "caisse/base.html" %}

{% block titre %}Adhésion en espèces{% endblock %}

{% block contenu %}
    <a href="{% url 'espace_asso' pole.slug %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <h1 class="mb-4">Adhésion en espèces - {{ pole.nom }}</h1>

    {% if erreur %}
        <div class="card border-danger shadow-sm mb-3">
            <div class="card-body text-center py-4">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" class="mb-2">
                    <circle cx="12" cy="12" r="10" fill="#FEF2F2"/>
                    <path d="M9 9l6 6M15 9l-6 6" stroke="#DC2626" stroke-width="2.5" stroke-linecap="round"/>
                </svg>
                <div class="fw-bold text-danger fs-5">Impossible</div>
                <p class="text-muted mb-0">{{ erreur }}</p>
            </div>
        </div>
    {% endif %}

    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card shadow-sm">
                <div class="card-body text-center py-4">
                    <p class="text-muted mb-3">Cotisation</p>
                    <form method="post">
                        {% csrf_token %}
                        <select name="tarif" class="form-select mb-3">
                            {% for t in tarifs %}
                                <option value="{{ t.id }}">{{ t.description }} — {{ t.prix|floatformat:2 }} EUR</option>
                            {% endfor %}
                        </select>
                        <input type="text" name="identifiant" class="form-control mb-3" placeholder="identifiant de l'étudiant" required>
                        <button type="submit" class="btn btn-primary w-100 py-2">Encaisser l'adhésion</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
{% endblock %}
```

Puis `caisse/templates/caisse/adhesion_especes_ok.html` :

```html
{% extends "caisse/base.html" %}

{% block titre %}Adhésion encaissée{% endblock %}

{% block contenu %}
    <div class="row justify-content-center">
        <div class="col-md-6 text-center">
            <div class="card shadow-sm">
                <div class="card-body py-5">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" class="mb-3">
                        <circle cx="12" cy="12" r="10" fill="#ECFDF5"/>
                        <path d="M8 12.5l2.5 2.5L16 9" stroke="#10B981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <div class="display-6 text-success mb-3">Adhésion encaissée</div>
                    <p class="text-muted mb-1">
                        {% if profil.user.first_name or profil.user.last_name %}
                            {{ profil.user.first_name }} {{ profil.user.last_name }}
                        {% else %}
                            {{ profil.user.username }}
                        {% endif %}
                    </p>
                    <a href="{% url 'payer_adhesion_especes' pole.slug %}" class="btn btn-primary mt-3">Nouvelle adhésion</a>
                </div>
            </div>
        </div>
    </div>
{% endblock %}
```

Enfin, ajoute la route dans `caisse/urls.py` :

```python
path("pole/<slug:slug>/adhesion-especes/", views.payer_adhesion_especes, name="payer_adhesion_especes"),
```

`payer_adhesion_especes` existe maintenant : retourne dans
`caisse/templates/caisse/espace_asso.html` et ajoute le bouton
« Adhésion en espèces », après le bloc `{% if peut_adhesions %}` ajouté en
8.2 :

```html
        {% if peut_adhesion_especes %}
        <a href="{% url 'payer_adhesion_especes' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M20 6h-4V4c0-1.1-.9-2-2-2h-4c-1.1 0-2 .9-2 2v2H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zM10 4h4v2h-4V4zm10 15H4V8h16v11z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Adhésion en espèces</div>
                        <div class="text-muted small">Encaisser une cotisation en liquide</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}
```

Le contexte `espace_asso` (7.1) passe déjà `"peut_adhesion_especes":
peut_encaisser_adhesion_especes(request.user, pole)`, donc rien d'autre à
changer côté vue.

---

## Partie 9 - Espèces (recharges et suivi)

### 9.1 Recharger un portefeuille en espèces

Dans `caisse/views.py`, ajoute l'import du modèle `Recharge` (`peut_recharger_especes`
est déjà importé depuis la Partie 7.2) :

```python
from .models import Recharge
```

Puis, à la suite du reste du fichier :

```python
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
```

**`Recharge.pole` est renseigné explicitement** (voir Partie 1.3) : c'est ce
qui garantit qu'une recharge apparaisse dans le suivi du **bon** pôle et
d'aucun autre, sans avoir à déduire quoi que ce soit de l'affiliation de la
personne qui encaisse.

Crée `caisse/templates/caisse/recharger_especes.html` :

```html
{% extends "caisse/base.html" %}

{% block titre %}Rechargement espèces{% endblock %}

{% block contenu %}
<a href="{% url 'espace_asso' pole.slug %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>

<div class="row justify-content-center">
    <div class="col-md-5">
        <div class="card shadow-sm">
            <div class="card-body p-4">
                <h4 class="mb-3">Rechargement en espèces</h4>
                {% if erreur %}
                    <div class="alert alert-danger">{{ erreur }}</div>
                {% endif %}
                <form method="post">
                    {% csrf_token %}
                    <div class="mb-3">
                        <label class="form-label">Identifiant de l'étudiant</label>
                        <input type="text" name="identifiant" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Montant (EUR)</label>
                        <input type="text" name="montant" class="form-control" placeholder="ex: 10,00" required>
                    </div>
                    <button type="submit" class="btn btn-success w-100">Valider le rechargement</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

Puis `caisse/templates/caisse/recharge_especes_ok.html` :

```html
{% extends "caisse/base.html" %}

{% block titre %}Rechargement effectué{% endblock %}

{% block contenu %}
<div class="text-center py-5">
    <div class="display-5 text-success mb-3">&#10003;</div>
    <h2>Rechargement de {{ montant|floatformat:2 }} EUR</h2>
    <p class="text-muted mb-1">
        {% if profil.user.first_name or profil.user.last_name %}
            {{ profil.user.first_name }} {{ profil.user.last_name }}
        {% else %}
            {{ profil.user.username }} <span class="badge bg-secondary">Identifiant</span>
        {% endif %}
    </p>
    <a href="{% url 'recharger_especes' pole.slug %}" class="btn btn-primary">Nouveau rechargement</a>
</div>
{% endblock %}
```

Enfin, ajoute la route dans `caisse/urls.py` :

```python
path("pole/<slug:slug>/recharger-especes/", views.recharger_especes, name="recharger_especes"),
```

`recharger_especes` existe maintenant : retourne dans
`caisse/templates/caisse/espace_asso.html` et ajoute le bouton
« Recharger en espèces », après le bloc `{% if peut_adhesion_especes %}`
ajouté en 8.3 :

```html
        {% if peut_recharger %}
        <a href="{% url 'recharger_especes' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M19 14V6c0-1.1-.9-2-2-2H3c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-4h4v-2h-4zm-2 4H3V6h14v12zm-7-7c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Recharger en espèces</div>
                        <div class="text-muted small">Encaisser un rechargement en liquide</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}
```

Le contexte `espace_asso` (7.1) passe déjà `"peut_recharger":
peut_recharger_especes(request.user, pole)`, donc rien d'autre à changer
côté vue. **Un bug d'apparence anodine à retenir** : une condition trop
large comme `{% if peut_vendre and not peut_gerer %}` sur cette tuile
excluait par erreur *tout* admin de pôle, y compris ceux qui devraient
légitimement la voir. La bonne condition, `{% if peut_recharger %}` comme
ci-dessus, est pensée droit par droit, jamais par déduction combinatoire
hâtive.

### 9.2 Suivi consolidé (recharges + adhésions espèces), par année scolaire

Dans `caisse/views.py`, ajoute cet import (`Adhesion`, `Recharge` et
`annee_scolaire_courante` sont déjà importés) :

```python
from datetime import datetime
```

Puis, à la suite du reste du fichier :

```python
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
```

**Le rattachement des recharges/adhésions consolidées** dans un unique écran
(Partie 9.2) est apparu après un vrai constat : les adhésions payées en
espèces étaient invisibles du suivi (qui ne regardait alors que les
`Recharge`), alors que l'objectif de la page est de connaître **tout** le
liquide encaissé par le pôle, quelle qu'en soit la nature.

L'export Excel correspondant (`exporter_especes`) suit le même principe
d'**archivage permanent** que le reste de la comptabilité : aucune donnée
n'est jamais supprimée automatiquement (conservation légale de 10 ans), la
base elle-même **est** l'archive ; l'export peut couvrir n'importe quelle
année scolaire passée à la demande, avec un onglet « Récapitulatif » (totaux
mois par mois) et un onglet par mois **ayant eu au moins une opération**
(jamais d'onglet vide inutile) - voir le code complet en Partie 12.

Crée `caisse/templates/caisse/gerer_especes.html`. **Attention, un bouton de
ce template pointe vers `exporter_especes`, qui n'existe qu'à partir de la
Partie 12** : laisse-le de côté pour l'instant, on le rajoutera à ce
moment-là.

```html
{% extends "caisse/base.html" %}

{% block titre %}Suivi espèces {{ pole.nom }}{% endblock %}

{% block contenu %}
    <a href="{% url 'espace_asso' pole.slug %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <div class="d-flex align-items-center gap-2">
            <h1 class="mb-0">Suivi espèces</h1>
            <form method="get" class="d-inline">
                <select name="annee" class="form-select form-select-sm" onchange="this.form.submit()">
                    {% for a in annees_disponibles %}
                        <option value="{{ a }}" {% if a == annee %}selected{% endif %}>{{ a }}-{{ a|add:1 }}</option>
                    {% endfor %}
                </select>
            </form>
        </div>
    </div>

    <h6 class="text-muted text-uppercase mb-2">Detail des opérations</h6>
    <input type="text" id="rechercheRecharges" class="form-control mb-3" placeholder="Rechercher un nom, une date..." oninput="filtrerRecharges()">
    <div class="table-responsive">
        <table class="table align-middle bg-white shadow-sm">
            <thead>
                <tr><th>Date</th><th>Personne</th><th>Type</th><th>Montant</th><th>Encaisse par</th></tr>
            </thead>
            <tbody id="corpsRecharges">
                {% for op in operations %}
                    <tr data-recherche="{{ op.personne|lower }} {{ op.date|date:'d/m/Y' }} {{ op.encaisse_par|lower }} {{ op.type|lower }}">
                        <td>{{ op.date|date:"d/m/Y H:i" }}</td>
                        <td>{{ op.personne }}</td>
                        <td>
                            {% if op.type == "Adhesion" %}
                                <span class="badge bg-primary">Adhésion</span>
                            {% else %}
                                <span class="badge bg-success">Rechargement</span>
                            {% endif %}
                        </td>
                        <td>{{ op.montant|floatformat:2 }} EUR</td>
                        <td>{{ op.encaisse_par }}</td>
                    </tr>
                {% empty %}
                    <tr><td colspan="5" class="text-muted text-center py-3">Aucune opération en espèces.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
{% endblock %}

{% block scripts %}
<script>
    function filtrerRecharges() {
        const recherche = document.getElementById('rechercheRecharges').value.trim().toLowerCase();
        document.querySelectorAll('#corpsRecharges tr[data-recherche]').forEach(function (ligne) {
            ligne.classList.toggle('d-none', !ligne.dataset.recherche.includes(recherche));
        });
    }
</script>
{% endblock %}
```

Enfin, ajoute la route dans `caisse/urls.py` :

```python
path("pole/<slug:slug>/especes/", views.gerer_especes, name="gerer_especes"),
```

`gerer_especes` existe maintenant : retourne dans
`caisse/templates/caisse/espace_asso.html` et ajoute le bouton
« Suivi espèces », après le bloc `{% if peut_recharger %}` ajouté en 9.1 :

```html
        {% if peut_suivi_especes %}
        <a href="{% url 'gerer_especes' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Suivi espèces</div>
                        <div class="text-muted small">Voir les rechargements du pôle</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}
```

Le contexte `espace_asso` (7.1) passe déjà `"peut_suivi_especes":
peut_voir_suivi_especes(request.user, pole)`, donc rien d'autre à changer
côté vue. Tous les boutons de `espace_asso.html` sont maintenant en place,
sauf « Exporter » (Partie 12).

---

## Partie 10 - Espace École (administration globale)

`caisse/vues_ecole.py` est **volontairement séparé** de `views.py` : ce
dernier avait grossi au point de nuire à la lisibilité, et l'espace école
forme un domaine fonctionnel cohérent et autonome (gestion des comptes, des
rôles, des codes, jamais des prix ni de la gestion commerciale).

Tu as déjà ce fichier depuis la Partie 4.2 (avec juste `verifier_code`
dedans) : on le complète maintenant avec tout le reste. D'abord, remplace
l'import `from django.contrib.auth.hashers import check_password` (Partie
4.2) par celui-ci, qui ajoute `make_password` :

```python
from django.contrib.auth.hashers import check_password, make_password
```

Puis ajoute ces imports en plus, à la suite de ceux déjà présents :

```python
import secrets
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone

from .forms import CorrectionProfilForm
from .models import (
    Adhesion, Affectation, CodeSecuriteAdmin, DemandeSuppressionCompte,
    LigneTransaction, Pole, ProfilUtilisateur,
)
from .recus import envoyer_email_code, envoyer_email_suppression
from .roles import annee_scolaire_courante, est_admin_ecole
```

Puis, à la suite de `verifier_code`, dans le même fichier
`caisse/vues_ecole.py` :

```python
def _verifier_acces(request):
    if not est_admin_ecole(request.user):
        raise PermissionDenied


@login_required
def espace_ecole(request):
    _verifier_acces(request)
    return render(request, "caisse/espace_ecole.html", {})
```

Chaque vue de ce module commence par l'appel à `_verifier_acces`, le même
garde-fou partout, jamais une variation locale. `espace_ecole` est le
tableau de bord d'entrée de tout l'espace école, l'équivalent de
`espace_asso` (Partie 7.1) mais pour l'admin école.

Crée `caisse/templates/caisse/espace_ecole.html`. **Comme pour
`espace_asso.html` en Partie 7.1, ne garde que ce qui existe déjà** : les
liens vers Recettes, Adhérents, Codes de sécurité et Comptes pointent vers
des vues qui n'existent pas encore (Parties 10.2 à 10.5) :

```html
{% extends "caisse/base.html" %}
{% block titre %}Espace École{% endblock %}
{% block contenu %}
    <h1 class="mb-4">Espace École</h1>
    <div class="d-flex flex-column gap-2">
        <a href="{% url 'ecole_equipe' %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div>
                    <div class="fw-bold">Équipes</div>
                    <div class="text-muted small">Qui compose chaque pôle</div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
    </div>
{% endblock %}
```

On y ajoutera une carte à chaque nouvelle section : Codes de sécurité après
la Partie 10.2, Comptes après la 10.4, puis Recettes et Adhérents après la
10.5, exactement comme pour `espace_asso.html`.

Ajoute les deux premières routes dans `caisse/urls.py` (le module
`vues_ecole` y est déjà importé depuis la Partie 4.2, via `from . import
vues_ecole`) :

```python
path("ecole/", vues_ecole.espace_ecole, name="espace_ecole"),
path("ecole/equipe/", vues_ecole.ecole_equipe, name="ecole_equipe"),
```

Enfin, ajoute un onglet « École » à la barre de navigation, dans
`caisse/templates/caisse/base.html`, après le bloc `{% if a_droits_vente %}...Asso...{% endif %}`
ajouté en Partie 7.1 :

```html
        {% if est_admin_ecole %}
        <a class="onglet {% if onglet == 'espace_ecole' or onglet == 'ecole_equipe' %}actif{% endif %}" href="{% url 'espace_ecole' %}">
            <svg viewBox="0 0 24 24"><path d="M12 3L1 9l11 6 9-4.91V17h2V9L12 3zm0 13.5L3.74 12 12 7.5 20.26 12 12 16.5z"/></svg>
            École
        </a>
        {% endif %}
```

`est_admin_ecole` vient déjà du context processor `droits_navigation`
(Partie 2.2), rien à changer côté vue.

### 10.1 Équipes globales : voir et attribuer des rôles

Toujours dans `caisse/vues_ecole.py`, à la suite du fichier :

```python
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
```

`ADMIN_ECOLE` et `ADMIN_ADE` ont tous deux `pole=None` : sans distinction
explicite de la **clé de regroupement** selon le rôle (et pas seulement selon
la présence d'un pôle), les deux étaient mélangés à tort dans le même groupe
d'affichage alors que ce sont deux rôles aux pouvoirs très différents.

```python
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
```

**Deux garde-fous serveur importants**, ni l'un ni l'autre déductible du seul
modèle de données :

1. **Impossible de retirer le dernier admin école.** Une simple confirmation
   JavaScript ne suffirait pas - sans cette règle *serveur*, il serait
   possible de bloquer *totalement* le système : plus personne ne pourrait
   ensuite distribuer de rôles ni de codes de sécurité.
2. **Un vendeur ou un admin de pôle doit obligatoirement être rattaché à un
   pôle.** Sans cette validation, un rôle sans pôle et sans effet réel (aucun
   droit nulle part) pourrait être créé par erreur.

Crée `caisse/templates/caisse/ecole_equipe.html` :

```html
{% extends "caisse/base.html" %}
{% block titre %}Équipes{% endblock %}
{% block contenu %}
    <a href="{% url 'espace_ecole' %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <h1 class="mb-4">Équipes par pôle</h1>

    {% if erreur %}
        <div class="alert alert-danger">{{ erreur }}</div>
    {% endif %}

    <div class="card shadow-sm mb-4">
        <div class="card-body">
            <h6 class="mb-3">Attribuer un rôle</h6>
            <form method="post" class="row g-2">
                {% csrf_token %}
                <div class="col-12 col-sm-4">
                    <input type="text" name="identifiant" class="form-control" placeholder="identifiant école" required>
                </div>
                <div class="col-6 col-sm-3">
                    <select name="pole" class="form-select">
                        <option value="">Aucun (rôle global uniquement)</option>
                        {% for p in poles %}
                            <option value="{{ p.id }}">{{ p.nom }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-6 col-sm-3">
                    <select name="role" class="form-select">
                        <option value="VENDEUR">Vendeur</option>
                        <option value="ADMIN_POLE">Admin de pôle</option>
                        <option value="ADMIN_ADE">Admin ADE</option>
                        <option value="ADMIN_ECOLE">Admin école</option>
                    </select>
                </div>
                <div class="col-12 col-sm-2">
                    <button type="submit" name="ajouter" value="1" class="btn btn-primary w-100">Ajouter</button>
                </div>
            </form>
        </div>
    </div>

    {% for nom_pole, affectations in groupes %}
        <div class="card shadow-sm mb-3">
            <div class="card-body">
                <h6 class="mb-2">{{ nom_pole }}</h6>
                <ul class="list-unstyled mb-0">
                    {% for a in affectations %}
                        <li class="d-flex justify-content-between align-items-center border-bottom py-1">
                            <span>
                                {% if a.user.first_name or a.user.last_name %}
                                    {{ a.user.first_name }} {{ a.user.last_name }}
                                {% else %}
                                    {{ a.user.username }} <span class="badge bg-secondary">Identifiant</span>
                                {% endif %}
                                <span class="badge bg-secondary ms-1">{{ a.get_role_display }}</span>
                            </span>
                            <button type="button" class="btn btn-sm btn-outline-danger" data-bs-toggle="modal" data-bs-target="#confirmationRetrait" data-affectation-id="{{ a.id }}" data-nom="{% if a.user.first_name or a.user.last_name %}{{ a.user.first_name }} {{ a.user.last_name }}{% else %}{{ a.user.username }}{% endif %}">Retirer</button>
                        </li>
                    {% endfor %}
                </ul>
            </div>
        </div>
    {% empty %}
        <p class="text-muted">Aucune affectation.</p>
    {% endfor %}

    <div class="modal fade" id="confirmationRetrait" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Retirer ce rôle ?</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    Tu es sur le point de retirer le rôle de <strong id="nomConcerne"></strong>.
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-success" data-bs-dismiss="modal">Annuler</button>
                    <form method="post" id="formConfirmationRetrait">
                        {% csrf_token %}
                        <input type="hidden" name="retirer" id="idConcerne">
                        <button type="submit" class="btn btn-danger">Confirmer le retrait</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
{% endblock %}

{% block scripts %}
<script>
    document.getElementById('confirmationRetrait').addEventListener('show.bs.modal', function (event) {
        const bouton = event.relatedTarget;
        document.getElementById('nomConcerne').textContent = bouton.dataset.nom;
        document.getElementById('idConcerne').value = bouton.dataset.affectationId;
    });
</script>
{% endblock %}
```

La route `ecole_equipe` a déjà été ajoutée juste avant la 10.1, en même
temps que `espace_ecole` : rien d'autre à faire côté `urls.py`. Relance le
serveur et clique sur l'onglet « École » : tu dois arriver sur le tableau de
bord, puis sur la page Équipes.

### 10.2 Codes de sécurité et alerte « personnes sans code »

Toujours dans `caisse/vues_ecole.py`, à la suite du fichier :

```python
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
```

**Étendre la protection aux vendeurs** (pas seulement les rôles à pouvoir)
est un choix assumé de cohérence : chaque nouveau vendeur, même ponctuel,
doit recevoir un code en main propre. **L'alerte regroupe par `(personne,
pôle)`, pas par affectation individuelle** : quelqu'un cumulant plusieurs
rôles sur le même pôle (vendeur + admin de pôle) n'a besoin que d'un seul
code pour ce pôle, il n'apparaît donc qu'une seule fois dans la liste, avec
tous ses rôles listés.

Crée `caisse/templates/caisse/ecole_codes.html` :

```html
{% extends "caisse/base.html" %}
{% block titre %}Codes de sécurité{% endblock %}
{% block contenu %}
    <a href="{% url 'espace_ecole' %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <h1 class="mb-4">Codes de sécurité</h1>

    {% if a_traiter %}
        <div class="alert alert-warning">
            <strong>{{ a_traiter|length }} personne{{ a_traiter|length|pluralize }} avec un rôle a pouvoir sans code :</strong>
            <ul class="list-unstyled mb-0 mt-2">
                {% for a in a_traiter %}
                    <li class="d-flex justify-content-between align-items-center py-1">
                        <span>
                            {% if a.user.first_name or a.user.last_name %}
                                {{ a.user.first_name }} {{ a.user.last_name }}
                            {% else %}
                                {{ a.user.username }}
                            {% endif %}
                            &mdash; {{ a.roles|join:", " }} ({{ a.pole.nom|default:"ADE/Ecole" }})
                        </span>
                        <form method="post" class="d-inline">
                            {% csrf_token %}
                            <input type="hidden" name="identifiant" value="{{ a.user.username }}">
                            <input type="hidden" name="pole" value="{{ a.pole.id|default:'' }}">
                            <button type="submit" name="generer" value="1" class="btn btn-sm btn-warning">Générer le code</button>
                        </form>
                    </li>
                {% endfor %}
            </ul>
        </div>
    {% endif %}

    {% if nouveau_code %}
        <div class="alert alert-success">
            <strong>Nouveau code généré : {{ nouveau_code }}</strong><br>
            <span class="small">Note-le et remets-le en main propre maintenant : il ne sera plus jamais affiché.</span>
        </div>
    {% endif %}
    {% if erreur %}
        <div class="alert alert-danger">{{ erreur }}</div>
    {% endif %}

    <div class="card shadow-sm mb-4">
        <div class="card-body">
            <form method="post" class="row g-2">
                {% csrf_token %}
                <div class="col-12 col-sm-5">
                    <input type="text" name="identifiant" class="form-control" placeholder="identifiant école" required>
                </div>
                <div class="col-8 col-sm-5">
                    <select name="pole" class="form-select">
                        <option value="">ADE (global)</option>
                        {% for p in poles %}
                            <option value="{{ p.id }}">{{ p.nom }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-4 col-sm-2">
                    <button type="submit" name="generer" value="1" class="btn btn-primary w-100">Générer</button>
                </div>
            </form>
        </div>
    </div>

    <h6 class="text-muted text-uppercase mb-2">Codes existants</h6>
    <table class="table align-middle bg-white shadow-sm">
        <thead><tr><th>Personne</th><th>Pôle</th><th>Défini par</th><th>Date</th><th></th></tr></thead>
        <tbody>
            {% for c in codes %}
                <tr>
                    <td>
                        {% if c.user.first_name or c.user.last_name %}
                            {{ c.user.first_name }} {{ c.user.last_name }}
                        {% else %}
                            {{ c.user.username }} <span class="badge bg-secondary">Identifiant</span>
                        {% endif %}
                    </td>
                    <td>{{ c.pole.nom|default:"ADE" }}</td>
                    <td>
                        {% if c.definie_par.first_name or c.definie_par.last_name %}
                            {{ c.definie_par.first_name }} {{ c.definie_par.last_name }}
                        {% else %}
                            {{ c.definie_par.username }}
                        {% endif %}
                    </td>
                    <td>{{ c.date_maj|date:"d/m/Y" }}</td>
                    <td>
                        <form method="post">
                            {% csrf_token %}
                            <button type="submit" name="retirer" value="{{ c.id }}" class="btn btn-sm btn-outline-danger">Retirer</button>
                        </form>
                    </td>
                </tr>
            {% empty %}
                <tr><td colspan="5" class="text-muted text-center py-3">Aucun code généré.</td></tr>
            {% endfor %}
        </tbody>
    </table>
{% endblock %}
```

Ajoute la route dans `caisse/urls.py` :

```python
path("ecole/codes/", vues_ecole.ecole_codes, name="ecole_codes"),
```

`ecole_codes` existe maintenant : retourne dans
`caisse/templates/caisse/espace_ecole.html` (Partie 10.1) et ajoute la
carte « Codes de sécurité », après la carte « Équipes » :

```html
        <a href="{% url 'ecole_codes' %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div>
                    <div class="fw-bold">Codes de sécurité</div>
                    <div class="text-muted small">Générer le code d'un admin</div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
```

### 10.3 Corriger un profil (admin école, contrairement à l'étudiant)

Contrairement à `InfoPersonnelleForm` (Partie 5), qui verrouille chaque champ
une fois rempli, `CorrectionProfilForm` laisse **tous** les champs toujours
modifiables - cette page n'existe que pour l'admin école, précisément pour
pouvoir corriger une erreur de saisie signalée.

Toujours dans `caisse/forms.py`, ajoute à la suite :

```python
class CorrectionProfilForm(forms.ModelForm):
    """Reservee a l'admin ecole : contrairement a InfoPersonnelleForm, tous
    les champs restent toujours modifiables, y compris deja ancres."""

    nom = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    prenom = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    date_naissance = forms.DateField(
        required=False, input_formats=["%d/%m/%Y"],
        widget=forms.DateInput(format="%d/%m/%Y", attrs={
            "class": "form-control", "type": "text", "placeholder": "jj/mm/aaaa",
            "pattern": r"\d{2}/\d{2}/\d{4}", "maxlength": "10", "inputmode": "numeric",
        }),
    )

    class Meta:
        model = ProfilUtilisateur
        fields = ["date_naissance"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        if instance:
            self.fields["nom"].initial = instance.user.last_name
            self.fields["prenom"].initial = instance.user.first_name
            self.fields["email"].initial = instance.user.email

    def save(self, commit=True):
        profil = super().save(commit=False)
        profil.user.last_name = self.cleaned_data.get("nom", "")
        profil.user.first_name = self.cleaned_data.get("prenom", "")
        profil.user.email = self.cleaned_data.get("email", "")
        if commit:
            profil.user.save()
            profil.save()
        return profil
```

Toujours dans `caisse/vues_ecole.py`, à la suite du fichier :

```python
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
```

(L'import de `date` est fait **localement**, dans la fonction, plutôt qu'en
tête de fichier avec le `datetime` déjà importé en 10.1 - un choix
délibéré ici puisque c'est la seule fonction du module à en avoir besoin.)

Crée `caisse/templates/caisse/ecole_profils.html` :

```html
{% extends "caisse/base.html" %}
{% block titre %}Corriger un profil{% endblock %}
{% block contenu %}
    <a href="{% url 'ecole_comptes' %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <h1 class="mb-4">Corriger un profil</h1>

    <form method="get" class="mb-4">
        <div class="input-group">
            <input type="text" name="identifiant" class="form-control" placeholder="identifiant école" value="{{ identifiant }}" required>
            <button type="submit" class="btn btn-primary">Rechercher</button>
        </div>
    </form>

    {% if erreur %}
        <div class="alert alert-danger">{{ erreur }}</div>
    {% endif %}

    {% if profil %}
        <div class="card shadow-sm">
            <div class="card-body">
                <div class="d-flex align-items-center gap-2 mb-3">
                    <div class="avatar-utilisateur">
                        {% if profil.user.first_name or profil.user.last_name %}{{ profil.user.first_name|first|upper }}{{ profil.user.last_name|first|upper }}{% else %}{{ profil.user.username|slice:":2"|upper }}{% endif %}
                    </div>
                    <div>
                        <div class="fw-bold">
                            {% if profil.user.first_name or profil.user.last_name %}{{ profil.user.first_name }} {{ profil.user.last_name }}{% else %}{{ profil.user.username }}{% endif %}
                        </div>
                        <div class="text-muted small">
                            <span class="fw-bold">{{ profil.user.username }}</span>
                            {% if age is not None %} · <span class="fw-bold">{{ age }} ans</span>{% endif %}
                        </div>
                    </div>
                </div>
                <p class="text-muted small">
                    Ces champs sont normalement verrouillés après la première saisie
                    par l'étudiant. En tant qu'admin école, tu peux les corriger ici
                    a tout moment, par exemple suite a une erreur signalee.
                </p>
                <form method="post">
                    {% csrf_token %}
                    <input type="hidden" name="identifiant" value="{{ identifiant }}">
                    <div class="mb-3">
                        <label class="form-label">Nom</label>
                        {{ form.nom }}
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Prénom</label>
                        {{ form.prenom }}
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Email</label>
                        {{ form.email }}
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Date de naissance</label>
                        {{ form.date_naissance }}
                        {% if form.date_naissance.errors %}<div class="text-danger small mt-1">{{ form.date_naissance.errors.0 }}</div>{% endif %}
                    </div>
                    <button type="submit" name="enregistrer" value="1" class="btn btn-primary w-100">Enregistrer les corrections</button>
                </form>
            </div>
        </div>
    {% endif %}

    <script>
        var champDateNaissanceCorrection = document.getElementById("id_date_naissance");
        if (champDateNaissanceCorrection) {
            champDateNaissanceCorrection.addEventListener("input", function () {
                var chiffres = champDateNaissanceCorrection.value.replace(/\D/g, "").slice(0, 8);
                var jour = chiffres.slice(0, 2);
                var mois = chiffres.slice(2, 4);
                var annee = chiffres.slice(4);
                if (jour.length === 2 && parseInt(jour, 10) > 31) { jour = "31"; }
                if (mois.length === 2 && parseInt(mois, 10) > 12) { mois = "12"; }
                var formate = jour;
                if (chiffres.length > 2) { formate += "/" + mois; }
                if (chiffres.length > 4) { formate += "/" + annee; }
                champDateNaissanceCorrection.value = formate;
            });
        }
    </script>
{% endblock %}
```

**Attention, le bouton « Retour » pointe vers `ecole_comptes`, qui n'existe
qu'à partir de la Partie 10.4** : laisse-le tel quel, il fonctionnera de
lui-même dès que tu auras fait la 10.4 - `{% url %}` n'est évalué qu'à
l'affichage de *cette* page, pas au chargement des autres.

Ajoute la route dans `caisse/urls.py` :

```python
path("ecole/profils/", vues_ecole.ecole_profils, name="ecole_profils"),
```

Cette page n'a **volontairement pas** de carte dans `espace_ecole.html` :
elle a besoin d'un identifiant pour afficher quoi que ce soit, ce qui n'a
de sens qu'en y arrivant **depuis** une liste déjà filtrée. Pour l'instant,
tu peux la tester en tapant l'URL à la main
(`/ecole/profils/?identifiant=...`) ; elle sera ensuite **fusionnée**
avec la page « Comptes » (10.4) : le bouton « Modifier » de chaque ligne y
renverra directement, ce qui évite de ressaisir l'identifiant alors qu'il
est déjà dans la liste.

### 10.4 Comptes : demande de suppression, délai de 3 mois, remboursement

Toujours dans `caisse/vues_ecole.py`, à la suite du fichier :

```python
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
```

**Le checkbox « Remboursement effectué » qui ne se décochait jamais** est un
bug classique lié au comportement HTML des checkboxes (déjà rencontré Partie
7.2) : une checkbox **non cochée** n'envoie **rien** dans le POST - sans
champ caché toujours présent portant l'action, il devient impossible de
distinguer « décocher » de « ne rien envoyer du tout ». Correction :

```html
<form method="post" class="mt-1">
    {% csrf_token %}
    <input type="hidden" name="profil_id" value="{{ p.id }}">
    <input type="hidden" name="basculer_remboursement" value="1">
    <label class="small">
        <input type="checkbox" onchange="this.form.submit()" {% if p.demande_suppression.remboursement_effectue %}checked{% endif %}>
        Remboursement effectué
    </label>
</form>
```

L'action (`basculer_remboursement`) est portée par un **champ caché
toujours envoyé**, la checkbox elle-même n'a **pas** d'attribut `name` - sa
seule fonction est de déclencher `this.form.submit()` à chaque clic, l'état
réel étant *inversé* côté serveur (`not demande.remboursement_effectue`), pas
lu depuis la checkbox.

`eligible_suppression_definitive` (Partie 1.6) autorise la suppression
anticipée **dès que le remboursement est marqué fait**, sans attendre les 3
mois complets - le délai n'a de sens que pour laisser le temps de réclamer un
remboursement ; une fois celui-ci géré, plus rien ne s'y oppose.

Le template `ecole_comptes.html` illustre le motif général de
**confirmation en chaîne** appliqué à trois actions irréversibles distinctes
(suppression, annulation, suppression définitive), toutes réutilisant les
**mêmes** deux modales génériques (`modaleAction1` → `modaleAction2`) plutôt
que d'en dupliquer une paire par action - voir Partie 13.1 pour le motif
détaillé. Crée `caisse/templates/caisse/ecole_comptes.html` (les classes
`.puces-categories`/`.puce-categorie` utilisées ici sont déjà dans
`base.html` depuis la Partie 6.1) :

```html
{% extends "caisse/base.html" %}
{% block titre %}Comptes{% endblock %}
{% block contenu %}
    <a href="{% url 'espace_ecole' %}" class="btn btn-outline-secondary btn-sm mb-3">&lsaquo; Retour</a>
    <h1 class="mb-4">Comptes</h1>

    {% if nb_a_supprimer %}
        <div class="alert alert-danger">
            {{ nb_a_supprimer }} compte{{ nb_a_supprimer|pluralize }} {{ nb_a_supprimer|pluralize:"est,sont" }} à supprimer.
        </div>
    {% endif %}

    <div class="puces-categories mb-3">
        <button type="button" class="puce-categorie active" data-filtre-btn="tous" onclick="filtrerComptes('tous')">Tous ({{ profils|length }})</button>
        <button type="button" class="puce-categorie" data-filtre-btn="bientot" onclick="filtrerComptes('bientot')">Bientôt supprimé ({{ nb_bientot }})</button>
        <button type="button" class="puce-categorie" data-filtre-btn="pret" onclick="filtrerComptes('pret')">À supprimer ({{ nb_a_supprimer }})</button>
    </div>

    <input type="text" id="rechercheComptes" class="form-control mb-3" placeholder="Rechercher un compte..." oninput="filtrerRecherche()">

    <ul class="list-group" id="listeComptes">
        {% for p in profils %}
            <li class="list-group-item" data-filtre="{% if p.demande_suppression %}{% if p.demande_suppression.eligible_suppression_definitive %}pret{% else %}bientot{% endif %}{% else %}actif{% endif %}"
                data-recherche="{% if p.user.first_name or p.user.last_name %}{{ p.user.first_name|lower }} {{ p.user.last_name|lower }}{% endif %} {{ p.user.username|lower }}">
                <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
                    <div class="d-flex align-items-center gap-2">
                        <div class="avatar-utilisateur">
                            {% if p.user.first_name or p.user.last_name %}{{ p.user.first_name|first|upper }}{{ p.user.last_name|first|upper }}{% else %}{{ p.user.username|slice:":2"|upper }}{% endif %}
                        </div>
                        <div>
                        <div class="fw-bold">
                            {% if p.user.first_name or p.user.last_name %}{{ p.user.first_name }} {{ p.user.last_name }}{% else %}{{ p.user.username }}{% endif %}
                        </div>
                        <div class="small {% if p.solde > 0 %}fw-bold text-ensea{% else %}text-muted{% endif %}">Solde : {{ p.solde|floatformat:2 }} EUR</div>
                        {% if p.demande_suppression %}
                            {% if p.user.email %}<div class="text-muted small">{{ p.user.email }}</div>{% endif %}
                            {% if p.demande_suppression.eligible_suppression_definitive %}
                                <span class="badge bg-danger mt-1">À supprimer</span>
                            {% else %}
                                <span class="badge bg-warning text-dark mt-1">
                                    Bientôt supprimé — dans {{ p.demande_suppression.jours_restants }} j
                                    (le {{ p.demande_suppression.date_suppression_prevue|date:"d/m/Y" }})
                                </span>
                            {% endif %}
                            <form method="post" class="mt-1">
                                {% csrf_token %}
                                <input type="hidden" name="profil_id" value="{{ p.id }}">
                                <input type="hidden" name="basculer_remboursement" value="1">
                                <label class="small">
                                    <input type="checkbox" onchange="this.form.submit()" {% if p.demande_suppression.remboursement_effectue %}checked{% endif %}>
                                    Remboursement effectué
                                </label>
                            </form>
                        {% endif %}
                        </div>
                    </div>
                    {% if not p.demande_suppression %}
                    <div class="d-flex align-items-center gap-2">
                        <a href="{% url 'ecole_profils' %}?identifiant={{ p.user.username }}" class="btn btn-outline-secondary btn-sm rounded-pill px-3">Modifier</a>
                        <button type="button" class="btn btn-outline-danger btn-sm rounded-circle d-flex align-items-center justify-content-center p-0"
                                style="width:34px;height:34px;"
                                data-profil-id="{{ p.id }}"
                                data-nom="{% if p.user.first_name or p.user.last_name %}{{ p.user.first_name }} {{ p.user.last_name }}{% else %}{{ p.user.username }}{% endif %}"
                                onclick="declencherSuppression(this)" aria-label="Supprimer">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                        </button>
                    </div>
                    {% else %}
                    <div class="d-flex flex-column gap-1">
                        <a href="{% url 'ecole_profils' %}?identifiant={{ p.user.username }}" class="btn btn-outline-secondary btn-sm rounded-pill px-3">Modifier</a>
                        <button type="button" class="btn btn-outline-success btn-sm"
                                data-profil-id="{{ p.id }}"
                                data-nom="{% if p.user.first_name or p.user.last_name %}{{ p.user.first_name }} {{ p.user.last_name }}{% else %}{{ p.user.username }}{% endif %}"
                                onclick="declencherAnnulation(this)">Annuler la suppression</button>
                        {% if p.demande_suppression.eligible_suppression_definitive %}
                            <button type="button" class="btn btn-danger btn-sm"
                                    data-profil-id="{{ p.id }}"
                                    data-nom="{% if p.user.first_name or p.user.last_name %}{{ p.user.first_name }} {{ p.user.last_name }}{% else %}{{ p.user.username }}{% endif %}"
                                    onclick="declencherSuppressionDefinitive(this)">Supprimer définitivement</button>
                        {% endif %}
                        {% endif %}
                    </div>
                </div>
            </li>
        {% empty %}
            <li class="list-group-item text-muted text-center py-3">Aucun compte.</li>
        {% endfor %}
    </ul>
    <p id="aucunResultatComptes" class="text-muted text-center py-3 d-none">Aucun résultat pour cette recherche.</p>

    <form method="post" id="formActionCompte" class="d-none">
        {% csrf_token %}
        <input type="hidden" name="profil_id" id="champProfilId">
        <input type="hidden" id="champAction" value="1">
    </form>

    <div class="modal fade" id="modaleAction1" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="titreModaleAction1">Confirmer</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p class="text-danger mb-0" id="corpsModaleAction1"></p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Annuler</button>
                    <button type="button" class="btn btn-success" id="btnModaleAction1Confirmer">Confirmer</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="modaleAction2" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Dernière vérification</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p class="mb-0">Vous êtes bien sûr(e) ?</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Annuler</button>
                    <button type="button" class="btn btn-success" id="btnModaleAction2Confirmer">Oui, confirmer</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="modaleAnnulation" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Annuler la suppression</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p class="mb-0" id="corpsModaleAnnulation"></p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Non</button>
                    <button type="button" class="btn btn-success" id="btnModaleAnnulationConfirmer">Oui, annuler la suppression</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        function filtrerComptes(filtre) {
            document.querySelectorAll('[data-filtre-btn]').forEach(function (bouton) {
                bouton.classList.toggle('active', bouton.dataset.filtreBtn === filtre);
            });
            document.querySelectorAll('#listeComptes li[data-filtre]').forEach(function (ligne) {
                ligne.classList.toggle('d-none', filtre !== 'tous' && ligne.dataset.filtre !== filtre);
            });
        }
        filtrerComptes('tous');

        function filtrerRecherche() {
            var recherche = document.getElementById('rechercheComptes').value.trim().toLowerCase();
            var auMoinsUn = false;
            document.querySelectorAll('#listeComptes li[data-recherche]').forEach(function (ligne) {
                var correspond = ligne.dataset.recherche.includes(recherche);
                ligne.classList.toggle('d-none', !correspond);
                if (correspond) { auMoinsUn = true; }
            });
            document.getElementById('aucunResultatComptes').classList.toggle('d-none', auMoinsUn || !recherche);
        }

        var formActionCompte = document.getElementById('formActionCompte');
        var champProfilId = document.getElementById('champProfilId');
        var champAction = document.getElementById('champAction');
        var modaleAction1El = document.getElementById('modaleAction1');
        var modaleAction2El = document.getElementById('modaleAction2');
        var titreModaleAction1 = document.getElementById('titreModaleAction1');
        var corpsModaleAction1 = document.getElementById('corpsModaleAction1');

        function ouvrirChaineConfirmation(action, profilId, titre, corps) {
            champProfilId.value = profilId;
            champAction.name = action;
            titreModaleAction1.textContent = titre;
            corpsModaleAction1.textContent = corps;
            new bootstrap.Modal(modaleAction1El).show();
        }

        var passageVersModale2 = false;
        document.getElementById('btnModaleAction1Confirmer').addEventListener('click', function () {
            passageVersModale2 = true;
            bootstrap.Modal.getInstance(modaleAction1El).hide();
        });
        modaleAction1El.addEventListener('hidden.bs.modal', function () {
            if (passageVersModale2) {
                passageVersModale2 = false;
                new bootstrap.Modal(modaleAction2El).show();
            }
        });
        document.getElementById('btnModaleAction2Confirmer').addEventListener('click', function () {
            formActionCompte.submit();
        });

        function declencherSuppression(bouton) {
            ouvrirChaineConfirmation(
                'demander_suppression', bouton.dataset.profilId,
                'Supprimer ce compte ?',
                'Le compte de ' + bouton.dataset.nom + ' sera anonymisé dans 3 mois. Un email va lui être envoyé pour l\'en informer.'
            );
        }

        function declencherSuppressionDefinitive(bouton) {
            ouvrirChaineConfirmation(
                'supprimer_definitivement', bouton.dataset.profilId,
                'Supprimer définitivement ce compte ?',
                'Le compte de ' + bouton.dataset.nom + ' va être anonymisé immédiatement. Cette action est irréversible.'
            );
        }

        var modaleAnnulationEl = document.getElementById('modaleAnnulation');
        var corpsModaleAnnulation = document.getElementById('corpsModaleAnnulation');
        function declencherAnnulation(bouton) {
            champProfilId.value = bouton.dataset.profilId;
            champAction.name = 'annuler_suppression';
            corpsModaleAnnulation.textContent = 'Annuler la suppression prévue du compte de ' + bouton.dataset.nom + ' ?';
            new bootstrap.Modal(modaleAnnulationEl).show();
        }
        document.getElementById('btnModaleAnnulationConfirmer').addEventListener('click', function () {
            formActionCompte.submit();
        });
    </script>
{% endblock %}
```

Ajoute la route dans `caisse/urls.py` :

```python
path("ecole/comptes/", vues_ecole.ecole_comptes, name="ecole_comptes"),
```

`ecole_comptes` existe maintenant : retourne dans
`caisse/templates/caisse/espace_ecole.html` (Partie 10.1) et ajoute la
carte « Comptes », après « Codes de sécurité » (ajoutée en 10.2) :

```html
        <a href="{% url 'ecole_comptes' %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div>
                    <div class="fw-bold">Comptes</div>
                    <div class="text-muted small">Liste, modification des profils et suppressions</div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
```

Le bouton « Retour » de `ecole_profils.html` (Partie 10.3), laissé en
suspens faute de page cible, pointe justement vers `ecole_comptes` : il
fonctionne désormais lui aussi.

### 10.5 Recettes et adhérents, en lecture seule sans jamais les prix unitaires

Toujours dans `caisse/vues_ecole.py`, à la suite du fichier :

```python
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
```

Le détail par **grande catégorie** (événements / produits / autre) est
montré, jamais le **prix unitaire d'un article précis** : l'admin école a
besoin de suivre la santé financière globale des pôles, jamais leur
politique tarifaire produit par produit - cohérent avec le principe « admin
école ne voit jamais les prix ».

Crée `caisse/templates/caisse/ecole_recettes.html` :

```html
{% extends "caisse/base.html" %}
{% block titre %}Recettes{% endblock %}
{% block contenu %}
    <a href="{% url 'espace_ecole' %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <h1 class="mb-3">Recettes</h1>
    <div class="d-flex justify-content-between align-items-center mb-4">
        <a href="?annee={{ annee_prec }}&mois={{ mois_prec }}" class="btn btn-outline-secondary btn-sm">&lsaquo;</a>
        <span class="fw-bold">{{ debut_mois|date:"F Y"|capfirst }}</span>
        <a href="?annee={{ annee_suiv }}&mois={{ mois_suiv }}" class="btn btn-outline-secondary btn-sm">&rsaquo;</a>
    </div>
    {% for r in resultats %}
        <div class="card shadow-sm mb-2">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="fw-bold">{{ r.pole.nom }}</span>
                    <span class="fs-5 fw-bold">{{ r.total|floatformat:2 }} EUR</span>
                </div>
                <div class="d-flex justify-content-between text-muted small">
                    <span>Événements : {{ r.evenements|floatformat:2 }} EUR</span>
                    <span>Produits : {{ r.produits|floatformat:2 }} EUR</span>
                    <span>Autre : {{ r.autre|floatformat:2 }} EUR</span>
                </div>
            </div>
        </div>
    {% endfor %}
{% endblock %}
```

Ajoute la route dans `caisse/urls.py` :

```python
path("ecole/recettes/", vues_ecole.ecole_recettes, name="ecole_recettes"),
```

`ecole_recettes` existe maintenant : retourne dans
`caisse/templates/caisse/espace_ecole.html` et ajoute la carte
« Recettes », après « Comptes » (ajoutée en 10.4) :

```html
        <a href="{% url 'ecole_recettes' %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div>
                    <div class="fw-bold">Recettes</div>
                    <div class="text-muted small">Recette de chaque pôle, mois par mois</div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
```

`ecole_adherents_pole` calcule l'**âge**, jamais la date de naissance brute
affichée telle quelle, avec un filtre en direct côté JavaScript (même motif
que Partie 13.3). Elle est précédée d'un sélecteur de pôle (`ecole_adherents`)
puisque, contrairement à un vendeur ou un admin de pôle, l'admin école n'est
attaché à aucun pôle en particulier - il doit d'abord choisir lequel
consulter. Toujours dans `caisse/vues_ecole.py`, à la suite du fichier :

```python
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
```

(Comme en Partie 10.3, l'import de `date` est fait **localement** : c'est
la seule fonction du fichier à en avoir besoin.)

Crée `caisse/templates/caisse/ecole_adherents.html` :

```html
{% extends "caisse/base.html" %}
{% block titre %}Adhérents{% endblock %}
{% block contenu %}
    <a href="{% url 'espace_ecole' %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <h1 class="mb-4">Adhérents {{ annee }}-{{ annee|add:1 }}</h1>
    <div class="d-flex flex-column gap-2">
        {% for pole in poles %}
            <a href="{% url 'ecole_adherents_pole' pole.slug %}" class="card shadow-sm text-decoration-none">
                <div class="card-body d-flex justify-content-between align-items-center py-3">
                    <span class="fw-bold">{{ pole.nom }}</span>
                    <span class="text-muted">&rsaquo;</span>
                </div>
            </a>
        {% empty %}
            <p class="text-muted">Aucun pôle ne propose d'adhésion.</p>
        {% endfor %}
    </div>
{% endblock %}
```

Puis `caisse/templates/caisse/ecole_adherents_pole.html` :

```html
{% extends "caisse/base.html" %}
{% block titre %}Adhérents {{ pole.nom }}{% endblock %}
{% block contenu %}
    <a href="{% url 'ecole_adherents' %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <h1 class="mb-4">{{ pole.nom }} - {{ annee }}-{{ annee|add:1 }}</h1>

    <input type="text" id="rechercheAdherents" class="form-control mb-3" placeholder="Rechercher un nom..." oninput="filtrerAdherents()">

    <table class="table align-middle bg-white shadow-sm">
        <thead><tr><th>Nom</th><th>Âge</th></tr></thead>
        <tbody id="corpsTableau">
            {% for item in liste %}
                <tr data-nom="{{ item.user.first_name|lower }} {{ item.user.last_name|lower }} {{ item.user.username|lower }}">
                    <td>
                        {% if item.user.first_name or item.user.last_name %}
                            {{ item.user.first_name }} {{ item.user.last_name }}
                        {% else %}
                            {{ item.user.username }} <span class="badge bg-secondary">Identifiant</span>
                        {% endif %}
                    </td>
                    <td>
                        {% if item.age %}{{ item.age }} ans{% else %}<span class="text-muted">-</span>{% endif %}
                    </td>
                </tr>
            {% empty %}
                <tr><td colspan="2" class="text-muted text-center py-3">Aucun adhérent.</td></tr>
            {% endfor %}
        </tbody>
    </table>
    <p id="aucunResultat" class="text-muted text-center py-3 d-none">Aucun résultat pour cette recherche.</p>
{% endblock %}

{% block scripts %}
<script>
    function filtrerAdherents() {
        const recherche = document.getElementById('rechercheAdherents').value.trim().toLowerCase();
        const lignes = document.querySelectorAll('#corpsTableau tr[data-nom]');
        let visibles = 0;
        lignes.forEach(function (ligne) {
            const correspond = ligne.dataset.nom.includes(recherche);
            ligne.classList.toggle('d-none', !correspond);
            if (correspond) visibles++;
        });
        document.getElementById('aucunResultat').classList.toggle('d-none', visibles > 0 || lignes.length === 0);
    }
</script>
{% endblock %}
```

Ajoute les deux routes dans `caisse/urls.py` :

```python
path("ecole/adherents/", vues_ecole.ecole_adherents, name="ecole_adherents"),
path("ecole/adherents/<slug:slug>/", vues_ecole.ecole_adherents_pole, name="ecole_adherents_pole"),
```

`ecole_adherents` existe maintenant : retourne dans
`caisse/templates/caisse/espace_ecole.html` et ajoute la carte
« Adhérents », après « Recettes ». C'est la **dernière** carte : toutes les
cartes de `espace_ecole.html` sont maintenant en place.

```html
        <a href="{% url 'ecole_adherents' %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div>
                    <div class="fw-bold">Adhérents</div>
                    <div class="text-muted small">Liste par pôle (année en cours)</div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
```

### 10.6 Pôle « ADE » désactivé comme point de vente

`Pole.est_operationnel` (Partie 1.2) répond à un cas réel : l'ADE supervise
Kfet/BDE/Epicuria mais ne doit **plus** apparaître comme point de vente
séparé, car elle vend en réalité *sous* BDE. On ne supprime jamais la ligne
`Pole` correspondante (pour préserver un éventuel historique), on la
**désactive** simplement : `poles_vendables`/`poles_gerables` (Partie 2)
filtrent systématiquement `est_operationnel=True`, et `ecole_recettes`
n'affiche plus de ligne vide pour ce pôle.

---

## Partie 11 - Emails

### 11.1 Configuration : de la console au vrai SMTP, sans casser le développement

Installe d'abord le paquet qui lit le fichier `.env` :

```bash
pip install python-dotenv
```

N'oublie pas de mettre à jour `requirements.txt` (Partie 0) :

```bash
pip freeze > requirements.txt
```

Dans `cashless/settings.py`, ajoute `import os` avec les autres imports en
tête de fichier, puis, juste après la ligne `BASE_DIR = Path(__file__)...`
(pour que `BASE_DIR` existe déjà quand on l'utilise) :

```python
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")
```

Chargé depuis un `.env` **jamais committé** (dans `.gitignore` dès la
Partie 0), crée ce fichier à la racine du projet (à côté de `manage.py`),
pas besoin d'éditeur graphique, directement depuis le terminal, avec tes
propres valeurs :

```bash
cat > .env <<'ENV'
EMAIL_HOST=smtpi.ensea.fr
EMAIL_PORT=25
EMAIL_USE_TLS=False
DEFAULT_FROM_EMAIL=cashless@ensea.fr
ENV
```

Vérifie ensuite avec `cat .env` que le contenu est correct, et avec `git
status` qu'il n'apparaît **pas** dans les fichiers à committer (il doit
être filtré par `.gitignore`).

**Si tu n'as pas de serveur SMTP sous la main pour l'instant**, ne crée pas
de fichier `.env` du tout (ou laisse-le vide) : le bloc `else` ci-dessous
bascule automatiquement en mode console (les emails s'affichent dans le
terminal au lieu d'être réellement envoyés), donc rien ne bloque.

Enfin, toujours dans `cashless/settings.py`, ajoute à la suite du fichier :

```python
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "").replace(" ", "")

if os.environ.get("EMAIL_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ["EMAIL_HOST"]
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
    EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False") == "True"
    # Sans timeout, une connexion SMTP qui ne repond pas (reseau qui bloque
    # le port, par exemple) bloque la page indefiniment.
    EMAIL_TIMEOUT = 10
else:
    # Aucun identifiant configure : mode console (les emails s'affichent
    # dans le terminal au lieu d'etre reellement envoyes).
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL") or "cashless@ensea.fr"
```

**Décisions techniques et leur pourquoi** :

- **`EMAIL_HOST_PASSWORD.replace(" ", "")`** : Gmail affiche un mot de passe
  d'application avec des espaces de lisibilité ; les retirer accepte le
  copier-coller tel quel, avec ou sans espaces.
- **`EMAIL_TIMEOUT = 10`** : sans lui, une tentative de connexion SMTP vers
  un port bloqué par le réseau (rencontré concrètement avec le port 587
  depuis le réseau de l'école) fait **geler la page indéfiniment** - le
  timeout transforme un blocage silencieux en échec propre et rapide.
- **Le mot de passe reste optionnel** : le relais interne de l'ENSEA
  (`smtpi.ensea.fr:25`) accepte l'envoi **sans authentification** depuis le
  réseau de l'école, contrairement à Gmail qui en exige une. La condition
  d'activation du SMTP réel repose donc uniquement sur la présence de
  `EMAIL_HOST`, jamais sur celle d'un mot de passe.
- **Toujours un `try/except` autour de `send_mail`/`message.send`**, avec
  `fail_silently=True` : un email qui échoue à partir (mauvaise adresse,
  serveur temporairement injoignable) ne doit **jamais** faire échouer
  l'opération métier qui le déclenche (une vente, une suppression de compte).

### 11.2 Trois emails, trois contextes

`caisse/recus.py` centralise tous les envois. **Remplace tout le contenu**
de ce fichier (celui-ci contenait juste un `envoyer_recu` provisoire depuis
la Partie 3.3, qui ne faisait rien) par la version complète :

```python
from email.mime.image import MIMEImage

from django.core.mail import EmailMultiAlternatives, send_mail


def envoyer_email_code(code_admin, code_clair):
    """Previent la personne qu'un code de securite vient de lui etre
    attribue, avec le code en clair (jamais ni stocke ni reaffiche apres
    coup) et le contact de l'admin ecole qui l'a defini."""
    from .models import Affectation

    utilisateur = code_admin.user
    destinataire = utilisateur.email
    if not destinataire:
        return
    civilite = utilisateur.first_name or utilisateur.username
    roles = Affectation.objects.filter(user=utilisateur, pole=code_admin.pole)
    noms_roles = ", ".join(r.get_role_display() for r in roles) or "un rôle à pouvoir"
    cible = code_admin.pole.nom if code_admin.pole else "l'ADE"
    admin = code_admin.definie_par
    if admin.first_name or admin.last_name:
        nom_admin = f"{admin.first_name} {admin.last_name}".strip()
    else:
        nom_admin = admin.username
    corps = (
        f"Bonjour {civilite},\n\n"
        f"Un code de sécurité vient de t'être attribué sur ton compte ENSEA "
        f"Cashless, pour ton rôle de {noms_roles} ({cible}).\n\n"
        f"Ce code te sera demandé à chaque connexion, en plus de ton identifiant "
        f"habituel :\n\n"
        f"    {code_clair}\n\n"
        f"Garde-le précieusement et ne le communique à personne.\n\n"
        f"Pour toute question, contacte {nom_admin}, qui te l'a attribué.\n\n"
        f"Bien cordialement,\n"
        f"{nom_admin}\n"
        f"Administration ENSEA Cashless"
    )
    try:
        send_mail(
            subject="Ton code de sécurité ENSEA Cashless",
            message=corps, from_email=None, recipient_list=[destinataire],
            fail_silently=True,
        )
    except Exception:
        pass


def envoyer_email_suppression(demande):
    """Previent l'etudiant que son compte va etre supprime (anonymise)
    dans 3 mois, et l'invite a demander le remboursement de son solde
    aupres de l'admin ecole avant cette echeance."""
    profil = demande.profil
    destinataire = profil.user.email
    if not destinataire:
        return
    civilite = profil.user.first_name or profil.user.username
    admin = demande.demande_par
    if admin.first_name or admin.last_name:
        nom_admin = f"{admin.first_name} {admin.last_name}".strip()
    else:
        nom_admin = admin.username
    corps = (
        f"Bonjour {civilite},\n\n"
        f"Nous vous informons que votre compte sur le portefeuille ENSEA Cashless "
        f"a été signalé pour suppression par {nom_admin}, de l'administration de "
        f"l'école.\n\n"
        f"Conformément à ce délai, votre compte sera définitivement supprimé "
        f"(anonymisé) le {demande.date_suppression_prevue:%d/%m/%Y}, soit dans "
        f"{demande.jours_restants} jours.\n\n"
        f"Si votre portefeuille dispose encore d'un solde, nous vous invitons à "
        f"vous rapprocher au plus vite de {nom_admin} pour en demander le "
        f"remboursement. Passé ce délai, tout solde restant sera considéré comme "
        f"reversé à l'association.\n\n"
        f"Si vous pensez qu'il s'agit d'une erreur, contactez sans attendre "
        f"{nom_admin}, qui pourra annuler cette suppression avant l'échéance.\n\n"
        f"Nous vous remercions pour votre confiance et vous souhaitons une "
        f"excellente continuation.\n\n"
        f"Bien cordialement,\n"
        f"{nom_admin}\n"
        f"Administration ENSEA Cashless"
    )
    try:
        send_mail(
            subject="Suppression prochaine de votre compte ENSEA Cashless",
            message=corps, from_email=None, recipient_list=[destinataire],
            fail_silently=True,
        )
    except Exception:
        pass


def envoyer_recu(transaction):
    """Envoie le recu d'achat : un email HTML avec la photo de chaque
    produit a cote de sa ligne, plus une version texte simple en repli
    pour les clients mail qui n'affichent pas le HTML."""
    destinataire = transaction.profil.user.email
    if not destinataire:
        return
    lignes = list(transaction.lignes.all())

    corps_texte = (
        f"Recu d'achat - {transaction.pole.nom}\n\n"
        f"Date : {transaction.date_operation.strftime('%d/%m/%Y %H:%M')}\n\n"
        + "\n".join(
            f"  {ligne.quantite} x {ligne.libelle} .... {ligne.prix_unitaire} EUR"
            for ligne in lignes
        )
        + f"\n\nTotal paye : {transaction.montant_total} EUR\n"
    )

    images_a_joindre = []
    lignes_html = ""
    for i, ligne in enumerate(lignes):
        cid = f"produit{i}"
        photo_disponible = bool(ligne.produit.photo) and ligne.produit.photo.storage.exists(ligne.produit.photo.name)
        if photo_disponible:
            vignette = (
                f'<img src="cid:{cid}" width="48" height="48" alt="" '
                f'style="border-radius:8px;object-fit:cover;vertical-align:middle;'
                f'margin-right:10px;display:inline-block;">'
            )
            images_a_joindre.append((cid, ligne.produit.photo))
        else:
            vignette = (
                '<span style="width:48px;height:48px;border-radius:8px;background:#FFF0F4;'
                'display:inline-block;vertical-align:middle;margin-right:10px;"></span>'
            )
        sous_total = ligne.prix_unitaire * ligne.quantite
        lignes_html += (
            '<tr>'
            f'<td style="padding:8px 0;border-bottom:1px solid #F1F5F9;">{vignette}'
            f'<span style="vertical-align:middle;color:#0F172A;">{ligne.quantite} x {ligne.libelle}</span></td>'
            f'<td style="padding:8px 0;border-bottom:1px solid #F1F5F9;text-align:right;'
            f'vertical-align:middle;color:#0F172A;">{sous_total:.2f} EUR</td>'
            '</tr>'
        )

    corps_html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;">
        <h2 style="color:#C8004B;margin-bottom:4px;">Reçu d'achat</h2>
        <p style="color:#64748B;font-size:13px;margin-top:0;">
            {transaction.pole.nom} — {transaction.date_operation.strftime('%d/%m/%Y à %H:%M')}
        </p>
        <table style="width:100%;border-collapse:collapse;">
            {lignes_html}
        </table>
        <p style="font-size:18px;font-weight:bold;text-align:right;margin-top:12px;color:#0F172A;">
            Total payé : {transaction.montant_total:.2f} EUR
        </p>
        <p style="color:#94A3B8;font-size:12px;">Merci pour ton achat !</p>
    </div>
    """

    try:
        message = EmailMultiAlternatives(
            subject=f"Reçu d'achat - {transaction.pole.nom}",
            body=corps_texte, from_email=None, to=[destinataire],
        )
        message.attach_alternative(corps_html, "text/html")
        for cid, photo in images_a_joindre:
            try:
                with photo.open("rb") as fichier:
                    image = MIMEImage(fichier.read())
                image.add_header("Content-ID", f"<{cid}>")
                image.add_header("Content-Disposition", "inline", filename=cid)
                message.attach(image)
            except Exception:
                continue
        message.send(fail_silently=True)
    except Exception:
        pass
```

`envoyer_email_code` et `envoyer_email_suppression` sont utilisées plus loin
(Partie 10), ce n'est pas un souci de les écrire ici avant d'avoir construit
les vues qui les appellent, une fonction inutilisée ne gêne jamais Django.

**Images intégrées via `Content-ID` / `cid:`.** Chaque photo produit est
jointe au message avec un en-tête `Content-ID` (`<produit0>`, `<produit1>`,
...) et référencée dans le HTML par `src="cid:produit0"`, technique
standard qui fonctionne même quand le client mail bloque le chargement
d'images distantes (l'image est **dans** l'email, pas chargée depuis une
URL).

**Un piège de version rencontré** : `EmailMultiAlternatives.mixed_subtype =
"related"` (attribut non documenté, utilisé pour forcer le bon type MIME
`multipart/related`) a été **supprimé dans Django 6.0**, provoquant un
`AttributeError`. La correction est de simplement retirer cette ligne les en-têtes `Content-ID` + `Content-Disposition: inline` suffisent en pratique à
faire fonctionner l'affichage inline sans ce réglage explicite.

---

## Partie 12 - Exports Excel et confidentialité

### 12.1 La règle de confidentialité centrale : jamais de nom sur un export financier

`caisse/exports.py` construit le classeur de ventes d'un pôle, avec une règle
énoncée explicitement en tête de fichier : **l'acheteur n'est jamais nommé**.
Le classeur (fonction `construire_classeur(pole, date_debut, date_fin)`,
bornes demi-ouvertes, `date_debut` incluse, `date_fin` exclue) contient
trois onglets :

- **Transactions** : une ligne par vente (date, identifiant anonyme, type,
  montant), avec un tableau récapitulatif (recette événements / produits /
  vente libre / total) décalé à droite.
- **Événements** : un tableau **distinct par événement** ayant eu des ventes
  sur la période, chacun avec son propre sous-total, choix délibéré plutôt
  qu'un unique tableau continu trié par événement, pour ne pas produire une
  feuille interminable.
- **Produits** : le détail des ventes du catalogue normal (hors événements,
  hors terminal), regroupées par produit avec sous-total par produit et total
  général.

Une nouvelle librairie est nécessaire pour générer des fichiers Excel :

```bash
pip install openpyxl
```

Le code complet, dans un nouveau fichier `caisse/exports.py` :

```python
"""
Construction du classeur Excel d'export des ventes d'un pole.

Regle de confidentialite : l'acheteur n'est jamais nomme. Chaque ligne ne
porte qu'un identifiant technique (ETU-00042), jamais le nom ni l'email,
pour qu'on ne puisse pas relier une ligne a une personne a la simple
lecture du fichier.
"""

from collections import defaultdict
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from .models import LigneTransaction, Transaction

_POLICE_ENTETE = Font(color="FFFFFF", bold=True)
_REMPLISSAGE_ENTETE = PatternFill("solid", fgColor="C8004B")
_POLICE_TOTAL = Font(bold=True)


def _anonymiser(profil):
    """Identifiant technique stable, jamais le nom."""
    return f"ETU-{profil.pk:05d}"


def _ecrire_entetes(feuille, ligne, colonnes):
    for i, texte in enumerate(colonnes, start=1):
        cellule = feuille.cell(row=ligne, column=i, value=texte)
        cellule.font = _POLICE_ENTETE
        cellule.fill = _REMPLISSAGE_ENTETE


def _largeurs(feuille, largeurs):
    for i, largeur in enumerate(largeurs, start=1):
        feuille.column_dimensions[get_column_letter(i)].width = largeur


def _type_transaction(tx):
    """Classe une transaction pour l'affichage : Evenement (avec son nom),
    Vente libre, ou Produit. Une transaction qui melangerait plusieurs
    types (rare, ex. un panier avec une place ET un cafe) est classee sur
    le premier type rencontre, evenement d'abord."""
    lignes = list(tx.lignes.all())
    for ligne in lignes:
        if ligne.produit.evenement_id:
            return f"Evenement : {ligne.produit.evenement.nom}"
    for ligne in lignes:
        if ligne.produit.est_vente_libre:
            return "Vente libre"
    return "Produit"


def construire_classeur(pole, date_debut, date_fin):
    """date_debut incluse, date_fin EXCLUE (bornes demi-ouvertes), toutes
    deux des datetime ou date compatibles avec un filtre Django."""
    transactions = (
        Transaction.objects.filter(
            pole=pole, date_operation__gte=date_debut, date_operation__lt=date_fin
        )
        .select_related("profil")
        .prefetch_related("lignes__produit__evenement")
        .order_by("date_operation")
    )
    lignes = list(
        LigneTransaction.objects.filter(transaction__in=transactions)
        .select_related("produit__evenement", "transaction__profil")
    )

    recette_evenements = Decimal("0")
    recette_produits = Decimal("0")
    recette_autre = Decimal("0")
    for ligne in lignes:
        montant = ligne.prix_unitaire * ligne.quantite
        if ligne.produit.evenement_id:
            recette_evenements += montant
        elif ligne.produit.est_vente_libre:
            recette_autre += montant
        else:
            recette_produits += montant
    recette_totale = recette_evenements + recette_produits + recette_autre

    classeur = Workbook()

    # ------------------------------------------------------------------
    # Onglet 1 : Transactions (liste + recapitulatif a cote)
    # ------------------------------------------------------------------
    feuille = classeur.active
    feuille.title = "Transactions"
    _ecrire_entetes(feuille, 1, ["Date", "Acheteur", "Type", "Montant (EUR)"])
    row = 2
    for tx in transactions:
        feuille.cell(row=row, column=1, value=tx.date_operation.strftime("%d/%m/%Y %H:%M"))
        feuille.cell(row=row, column=2, value=_anonymiser(tx.profil))
        feuille.cell(row=row, column=3, value=_type_transaction(tx))
        feuille.cell(row=row, column=4, value=float(tx.montant_total))
        row += 1
    if row == 2:
        feuille.cell(row=2, column=1, value="Aucune transaction sur cette periode.")
    _largeurs(feuille, [18, 14, 30, 16])

    # Tableau recapitulatif, decale a droite pour ne pas gener la liste.
    col = 6
    for i, texte in enumerate(["Recapitulatif", "Montant (EUR)"]):
        cellule = feuille.cell(row=1, column=col + i, value=texte)
        cellule.font = _POLICE_ENTETE
        cellule.fill = _REMPLISSAGE_ENTETE
    lignes_recap = [
        ("Recette evenements", recette_evenements),
        ("Recette produits", recette_produits),
        ("Recette vente libre", recette_autre),
        ("Total", recette_totale),
    ]
    for i, (libelle, montant) in enumerate(lignes_recap, start=2):
        c1 = feuille.cell(row=i, column=col, value=libelle)
        c2 = feuille.cell(row=i, column=col + 1, value=float(montant))
        if libelle == "Total":
            c1.font = _POLICE_TOTAL
            c2.font = _POLICE_TOTAL
    feuille.column_dimensions[get_column_letter(col)].width = 22
    feuille.column_dimensions[get_column_letter(col + 1)].width = 16

    # ------------------------------------------------------------------
    # Onglet 2 : Evenements (un tableau distinct par evenement)
    # ------------------------------------------------------------------
    feuille_evt = classeur.create_sheet("Evenements")
    lignes_par_evenement = defaultdict(list)
    for ligne in lignes:
        if ligne.produit.evenement_id:
            lignes_par_evenement[ligne.produit.evenement].append(ligne)

    row = 1
    if not lignes_par_evenement:
        feuille_evt.cell(row=1, column=1, value="Aucune vente d'evenement sur cette periode.")
    for evenement, lignes_evt in lignes_par_evenement.items():
        feuille_evt.cell(row=row, column=1, value=evenement.nom).font = Font(bold=True, size=13)
        row += 1
        _ecrire_entetes(feuille_evt, row, ["Date", "Acheteur", "Produit", "Quantite", "Montant (EUR)"])
        row += 1
        total_evt = Decimal("0")
        for ligne in sorted(lignes_evt, key=lambda l: l.transaction.date_operation):
            montant = ligne.prix_unitaire * ligne.quantite
            total_evt += montant
            feuille_evt.cell(row=row, column=1, value=ligne.transaction.date_operation.strftime("%d/%m/%Y %H:%M"))
            feuille_evt.cell(row=row, column=2, value=_anonymiser(ligne.transaction.profil))
            feuille_evt.cell(row=row, column=3, value=ligne.libelle)
            feuille_evt.cell(row=row, column=4, value=ligne.quantite)
            feuille_evt.cell(row=row, column=5, value=float(montant))
            row += 1
        c1 = feuille_evt.cell(row=row, column=4, value="Total")
        c2 = feuille_evt.cell(row=row, column=5, value=float(total_evt))
        c1.font = _POLICE_TOTAL
        c2.font = _POLICE_TOTAL
        row += 2  # ligne vide entre deux evenements
    _largeurs(feuille_evt, [18, 14, 28, 10, 16])

    # ------------------------------------------------------------------
    # Onglet 3 : Produits (catalogue normal, hors evenements/terminal)
    # ------------------------------------------------------------------
    feuille_prod = classeur.create_sheet("Produits")
    lignes_par_produit = defaultdict(list)
    for ligne in lignes:
        if not ligne.produit.evenement_id and not ligne.produit.est_vente_libre:
            lignes_par_produit[ligne.produit.nom].append(ligne)

    row = 1
    _ecrire_entetes(
        feuille_prod, row,
        ["Date", "Acheteur", "Produit", "Quantite", "Prix unitaire (EUR)", "Montant (EUR)"],
    )
    row += 1
    if not lignes_par_produit:
        feuille_prod.cell(row=row, column=1, value="Aucune vente de produit sur cette periode.")
        row += 1
    total_general = Decimal("0")
    for nom_produit in sorted(lignes_par_produit):
        lignes_p = lignes_par_produit[nom_produit]
        sous_total = Decimal("0")
        for ligne in sorted(lignes_p, key=lambda l: l.transaction.date_operation):
            montant = ligne.prix_unitaire * ligne.quantite
            sous_total += montant
            feuille_prod.cell(row=row, column=1, value=ligne.transaction.date_operation.strftime("%d/%m/%Y %H:%M"))
            feuille_prod.cell(row=row, column=2, value=_anonymiser(ligne.transaction.profil))
            feuille_prod.cell(row=row, column=3, value=ligne.libelle)
            feuille_prod.cell(row=row, column=4, value=ligne.quantite)
            feuille_prod.cell(row=row, column=5, value=float(ligne.prix_unitaire))
            feuille_prod.cell(row=row, column=6, value=float(montant))
            row += 1
        c1 = feuille_prod.cell(row=row, column=3, value=f"Sous-total {nom_produit}")
        c2 = feuille_prod.cell(row=row, column=6, value=float(sous_total))
        c1.font = _POLICE_TOTAL
        c2.font = _POLICE_TOTAL
        total_general += sous_total
        row += 2
    c1 = feuille_prod.cell(row=row, column=3, value="Total general")
    c2 = feuille_prod.cell(row=row, column=6, value=float(total_general))
    c1.font = _POLICE_TOTAL
    c2.font = _POLICE_TOTAL
    _largeurs(feuille_prod, [18, 14, 28, 10, 16, 16])

    return classeur
```

Il est appelé depuis la vue `export_pole`, dans `caisse/views.py`, qui gère
le choix de période (mois / année / personnalisé) puis déclenche un
téléchargement direct. Ajoute d'abord ces imports dans `caisse/views.py` (`Decimal` est déjà
importé depuis la Partie 3.5, `datetime` depuis la 9.2, `peut_exporter` et
`est_admin_ade` depuis la 7.1/7.2) :

```python
import calendar
from datetime import date, timedelta

from django.http import HttpResponse

from .exports import construire_classeur
```

Puis, à la suite du reste du fichier :

```python
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
```

La même réponse `HttpResponse` avec ce
`content_type` (le type MIME officiel des fichiers `.xlsx`) et cet en-tête
`Content-Disposition: attachment` revient dans tous les exports Excel du
projet (Partie 8, Partie 9) : c'est ce qui déclenche un vrai téléchargement
côté navigateur plutôt qu'un affichage brut.

Crée `caisse/templates/caisse/export_pole.html`. **Attention, sa version
finale contient un lien vers `rechercher_identifiant`, qui n'existe qu'à
partir de la Partie 12.2** : laisse-le de côté pour l'instant, on le
rajoutera à ce moment-là.

```html
{% extends "caisse/base.html" %}

{% block titre %}Export {{ pole.nom }}{% endblock %}

{% block contenu %}
    <a href="{% url 'espace_asso' pole.slug %}" class="btn btn-outline-secondary btn-sm mb-3">Retour</a>
    <h1 class="mb-4">Exporter les ventes - {{ pole.nom }}</h1>

    <div class="card shadow-sm">
        <div class="card-body">
            <form method="get">
                <label class="form-label d-block">Période</label>
                <div class="btn-group mb-3" role="group">
                    <input type="radio" class="btn-check" name="periode" id="p-mois" value="mois" checked onchange="basculer()">
                    <label class="btn btn-outline-primary" for="p-mois">Mois</label>
                    <input type="radio" class="btn-check" name="periode" id="p-annee" value="annee" onchange="basculer()">
                    <label class="btn btn-outline-primary" for="p-annee">Année</label>
                    <input type="radio" class="btn-check" name="periode" id="p-perso" value="personnalise" onchange="basculer()">
                    <label class="btn btn-outline-primary" for="p-perso">Personnalisé</label>
                </div>

                <div id="bloc-annee-wrapper" class="mb-3">
                    <label class="form-label">Année</label>
                    <select name="annee" class="form-select">
                        {% for a in annees %}
                            <option value="{{ a }}" {% if a == aujourdhui.year %}selected{% endif %}>{{ a }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div id="bloc-mois" class="mb-3">
                    <label class="form-label">Mois</label>
                    <select name="mois" class="form-select">
                        {% for valeur, nom in mois_liste %}
                            <option value="{{ valeur }}" {% if valeur == aujourdhui.month %}selected{% endif %}>{{ nom }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div id="bloc-perso" class="row g-2 mb-3 d-none">
                    <div class="col-6">
                        <label class="form-label">Du</label>
                        <input type="date" name="debut" class="form-control">
                    </div>
                    <div class="col-6">
                        <label class="form-label">Au</label>
                        <input type="date" name="fin" class="form-control">
                    </div>
                </div>

                <button type="submit" class="btn btn-primary w-100">Télécharger le fichier Excel</button>
            </form>
        </div>
    </div>
{% endblock %}

{% block scripts %}
<script>
    function basculer() {
        const val = document.querySelector('input[name="periode"]:checked').value;
        document.getElementById('bloc-annee-wrapper').classList.toggle('d-none', val === 'personnalise');
        document.getElementById('bloc-mois').classList.toggle('d-none', val !== 'mois');
        document.getElementById('bloc-perso').classList.toggle('d-none', val !== 'personnalise');
    }
    basculer();
</script>
{% endblock %}
```

Ajoute la route dans `caisse/urls.py` :

```python
path("pole/<slug:slug>/export/", views.export_pole, name="export_pole"),
```

`export_pole` existe maintenant : retourne dans
`caisse/templates/caisse/espace_asso.html` (Partie 7.1) et ajoute le
bouton « Exporter », après le bloc `{% if peut_suivi_especes %}` ajouté en
9.2, **c'est le dernier bouton en attente**, `espace_asso.html` est
maintenant complet :

```html
        {% if peut_exporter %}
        <a href="{% url 'export_pole' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M5 20h14v-2H5v2zM19 9h-4V3H9v6H5l7 7 7-7z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Exporter</div>
                        <div class="text-muted small">Ventes au format Excel</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}
```

Le contexte `espace_asso` (7.1) passe déjà `"peut_exporter":
peut_exporter(request.user, pole)`, donc rien d'autre à changer côté vue.

### 12.2 Un identifiant anonyme, mais retrouvable dans un cas exceptionnel

L'anonymisation systématique des exports crée un besoin ponctuel légitime :
un litige, une fraude suspectée, nécessitant d'identifier qui se cache
derrière `ETU-00042`. Plutôt que de lever l'anonymisation par défaut, un
outil **séparé, tracé et réservé à l'admin ADE** répond à ce besoin.
`est_admin_ade` et `ProfilUtilisateur` sont déjà importés dans
`caisse/views.py`, à la suite du reste du fichier :

```python
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
```

Crée `caisse/templates/caisse/rechercher_identifiant.html` :

```html
{% extends "caisse/base.html" %}
{% block titre %}Rechercher un identifiant{% endblock %}
{% block contenu %}
    <h1 class="mb-4">Rechercher un identifiant</h1>
    <p class="text-muted small">
        Les exports de ventes affichent un identifiant anonyme (ex. "ETU-00042") au lieu du
        nom, pour protéger les habitudes d'achat de chacun. Cet outil permet de retrouver, au
        cas par cas, la personne derrière un identifiant précis — à n'utiliser que si c'est
        réellement nécessaire.
    </p>

    <div class="card shadow-sm mb-3">
        <div class="card-body">
            <form method="post" class="d-flex gap-2">
                {% csrf_token %}
                <input type="text" name="identifiant" class="form-control" placeholder="ETU-00042" autofocus>
                <button type="submit" class="btn btn-primary text-nowrap">Rechercher</button>
            </form>
        </div>
    </div>

    {% if erreur %}
        <div class="alert alert-danger">{{ erreur }}</div>
    {% endif %}

    {% if resultat %}
        <div class="card shadow-sm">
            <div class="card-body">
                {% if resultat.statut_compte == "ANONYMISE" %}
                    <p class="text-muted mb-0">Ce compte a été supprimé (anonymisé) : aucune identification n'est plus possible.</p>
                {% else %}
                    <div class="fw-bold fs-5">
                        {% if resultat.user.first_name or resultat.user.last_name %}
                            {{ resultat.user.first_name }} {{ resultat.user.last_name }}
                        {% else %}
                            {{ resultat.user.username }}
                        {% endif %}
                    </div>
                    <div class="text-muted small">{{ resultat.user.username }}{% if resultat.user.email %} · {{ resultat.user.email }}{% endif %}</div>
                {% endif %}
            </div>
        </div>
    {% endif %}
{% endblock %}
```

Ajoute la route dans `caisse/urls.py` :

```python
path("ade/rechercher-identifiant/", views.rechercher_identifiant, name="rechercher_identifiant"),
```

`rechercher_identifiant` existe maintenant : retourne dans
`caisse/templates/caisse/export_pole.html` (Partie 12.1) et ajoute, juste
avant `{% endblock %}` (donc après le `</div>` qui ferme la `card`), le lien
laissé de côté :

```html
    {% if admin_ade %}
        <p class="text-center mt-3">
            <a href="{% url 'rechercher_identifiant' %}" class="small">Retrouver le nom derrière un identifiant (ETU-...) &rsaquo;</a>
        </p>
    {% endif %}
```

Le contexte de `export_pole` (Partie 12.1) passe déjà `"admin_ade":
est_admin_ade(request.user)`, donc rien d'autre à changer côté vue. **Un
compte déjà anonymisé** (Partie 10.4, `anonymiser()`) ne peut en revanche
plus jamais être retrouvé - l'anonymisation efface réellement l'identité,
pas seulement son affichage.

### 12.3 Exports nominatifs (participants, adhérents) : l'exception assumée

Contrairement à l'export financier des transactions, deux exports affichent
volontairement les **vrais noms**, parce que leur usage est opérationnel et
non comptable :

- `exporter_participants` : savoir qui a réservé un billet, avec une
  vérification à l'entrée. La colonne « Majeur » est un **Oui/Non/Inconnu**
  calculé, jamais l'âge exact (réservé à l'admin école - voir Partie 1.6 et
  10.5).

  Un essai a d'abord utilisé une vraie liste déroulante Oui/Non (via
  `DataValidation` d'openpyxl) pour la colonne « Présent » à l'entrée, avant
  de **revenir à une case vide à remplir à la main** : `openpyxl` ne sait pas
  poser de vraie case à cocher cliquable façon Excel 365 (`showDropDown=True`
  masque en réalité la flèche - un nom trompeur hérité du format Excel), et
  changer de bibliothèque pour ce seul export a été jugé disproportionné.

  Dans `caisse/views.py`, à la suite du reste du fichier :

```python
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
```

  (`date` est déjà importé depuis la Partie 12.1 ; `Evenement`,
  `LigneTransaction`, `peut_gerer_produits` le sont depuis les Parties 6.3
  et 6.1.)

  Ajoute la route dans `caisse/urls.py` :

```python
path("pole/<slug:slug>/gerer/evenements/<int:evenement_id>/participants/exporter/", views.exporter_participants, name="exporter_participants"),
```

  `exporter_participants` existe maintenant : retourne dans
  `caisse/templates/caisse/participants_evenement.html` (Partie 6.4) et
  remets le bouton « Exporter » laissé de côté à l'époque :

```html
    <a href="{% url 'exporter_participants' pole.slug evenement.id %}" class="btn btn-success btn-sm">Exporter Excel</a>
```

- `exporter_adherents` : nom, prénom, email, montant, mode de paiement et
  encaisseur - utile pour la trésorerie du pôle, avec deux totaux
  (espèces / portefeuille) en bas de feuille. Toujours dans
  `caisse/views.py`, à la suite du fichier :

```python
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
```

  Ajoute la route dans `caisse/urls.py` :

```python
path("pole/<slug:slug>/adherents/exporter/", views.exporter_adherents, name="exporter_adherents"),
```

  `exporter_adherents` existe maintenant : retourne dans
  `caisse/templates/caisse/gerer_adherents.html` (Partie 8.2) et remets le
  bouton « Excel » laissé de côté à l'époque, dans l'en-tête de la liste des
  adhérents :

```html
                <a href="{% url 'exporter_adherents' pole.slug %}?annee={{ annee }}" class="pilule-action pilule-excel d-inline-flex align-items-center gap-1">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Excel
                </a>
```

**Un troisième export, promis depuis la Partie 9.2, trouve aussi sa place
ici** : `exporter_especes`, qui produit un onglet « Récapitulatif » (totaux
mois par mois de l'année scolaire) puis un onglet **par mois ayant eu au
moins une opération** (jamais d'onglet vide). Toujours dans
`caisse/views.py`, à la suite du fichier :

```python
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
```

(`MOIS_FR` est déjà défini depuis la Partie 12.1, `Recharge` depuis la
9.1.)

Ajoute la route dans `caisse/urls.py` :

```python
path("pole/<slug:slug>/especes/exporter/", views.exporter_especes, name="exporter_especes"),
```

`exporter_especes` existe maintenant : retourne dans
`caisse/templates/caisse/gerer_especes.html` (Partie 9.2) et remets le
bouton « Exporter Excel » laissé de côté à l'époque, dans l'en-tête de la
page :

```html
        <a href="{% url 'exporter_especes' pole.slug %}?annee={{ annee }}" class="btn btn-success btn-sm">Exporter Excel</a>
```

Le principe qui unifie ces choix : **la confidentialité n'est jamais un
réglage global, elle dépend de l'usage réel de chaque écran ou export**. Le
même profil peut être anonyme dans un contexte (export financier) et nommé
dans un autre (liste opérationnelle de présence), tant que chaque exception
est justifiée et délibérée.

**Tous les boutons d'`espace_asso.html` existent maintenant.** Ils ont été
ajoutés au fil des Parties 7 à 12, chacun à la suite du précédent, donc dans
l'ordre où les fonctionnalités ont été construites - pas forcément l'ordre
le plus logique pour l'utilisateur final. Rien n'empêche de réordonner les
blocs `{% if %}...{% endif %}` maintenant qu'ils sont tous là : remplace
tout le contenu de `caisse/templates/caisse/espace_asso.html` par cette
version, avec les cartes dans l'ordre Vendre → Adhésion en espèces →
Recharger en espèces → Équipe → Adhésions → Gérer → Suivi espèces →
Exporter → Paramètres (chaque bloc est strictement identique à celui déjà
écrit plus tôt, seul l'ordre change) :

```html
{% extends "caisse/base.html" %}

{% block titre %}Asso - {{ pole.nom }}{% endblock %}

{% block contenu %}
    {% if plusieurs_poles %}
        <a href="{% url 'asso_choix' %}" class="btn btn-outline-secondary btn-sm mb-3">&lsaquo; Retour</a>
    {% else %}
        <a href="{% url 'accueil' %}" class="btn btn-outline-secondary btn-sm mb-3">&lsaquo; Retour</a>
    {% endif %}

    <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="mb-0">Espace Asso</h1>
        <span class="badge" style="background:var(--ensea-light);color:var(--ensea);">{{ pole.nom }} ENSEA</span>
    </div>

    <div class="card shadow-sm text-center mb-4">
        <div class="card-body py-4">
            <div class="display-5 fw-bold" style="color:var(--ensea);">{{ recette_mois|floatformat:2 }} EUR</div>
            {% now "F Y" as mois_courant %}
            <div class="fw-bold">Recette de {{ mois_courant|capfirst }}</div>
            <div class="text-muted small mt-1">Mise à jour à l'instant</div>
        </div>
    </div>

    <div class="d-flex flex-column gap-2">

        {% if peut_vendre %}
        <a href="{% url 'detail_pole' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Vendre</div>
                        <div class="text-muted small">Interface caisse et encaissement</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}

        {% if peut_adhesion_especes %}
        <a href="{% url 'payer_adhesion_especes' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M20 6h-4V4c0-1.1-.9-2-2-2h-4c-1.1 0-2 .9-2 2v2H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zM10 4h4v2h-4V4zm10 15H4V8h16v11z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Adhésion en espèces</div>
                        <div class="text-muted small">Encaisser une cotisation en liquide</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}

        {% if peut_recharger %}
        <a href="{% url 'recharger_especes' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M19 14V6c0-1.1-.9-2-2-2H3c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-4h4v-2h-4zm-2 4H3V6h14v12zm-7-7c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Recharger en espèces</div>
                        <div class="text-muted small">Encaisser un rechargement en liquide</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}

        {% if peut_equipe %}
        <a href="{% url 'equipe_pole' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Équipe</div>
                        <div class="text-muted small">Vendeurs et droits d'accès</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}

        {% if peut_adhesions %}
        <a href="{% url 'gerer_adherents' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M20 6h-4V4c0-1.1-.9-2-2-2h-4c-1.1 0-2 .9-2 2v2H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zM10 4h4v2h-4V4zm10 15H4V8h16v11z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Adhésions</div>
                        <div class="text-muted small">Prix, liste des adhérents et export</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}

        {% if peut_gerer_produits %}
        <a href="{% url 'gerer_produits' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Gérer</div>
                        <div class="text-muted small">Catalogue, prix et stocks, évènements</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}

        {% if peut_suivi_especes %}
        <a href="{% url 'gerer_especes' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Suivi espèces</div>
                        <div class="text-muted small">Voir les rechargements du pôle</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}

        {% if peut_exporter %}
        <a href="{% url 'export_pole' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M5 20h14v-2H5v2zM19 9h-4V3H9v6H5l7 7 7-7z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Exporter</div>
                        <div class="text-muted small">Ventes au format Excel</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}

        {% if peut_parametres %}
        <a href="{% url 'modifier_pole' pole.slug %}" class="card shadow-sm text-decoration-none">
            <div class="card-body d-flex align-items-center justify-content-between py-3">
                <div class="d-flex align-items-center gap-3">
                    <div class="icone-action">
                        <svg viewBox="0 0 24 24"><path d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm8.94 3a8.994 8.994 0 000-2l2.03-1.58a.5.5 0 00.12-.63l-1.92-3.32a.5.5 0 00-.6-.22l-2.39.96a7.03 7.03 0 00-1.72-1l-.36-2.54a.5.5 0 00-.5-.42h-3.84a.5.5 0 00-.5.42l-.36 2.54c-.62.25-1.2.6-1.72 1l-2.39-.96a.5.5 0 00-.6.22L1.28 8.79a.5.5 0 00.12.63L3.43 11a8.994 8.994 0 000 2l-2.03 1.58a.5.5 0 00-.12.63l1.92 3.32a.5.5 0 00.6.22l2.39-.96c.52.4 1.1.75 1.72 1l.36 2.54a.5.5 0 00.5.42h3.84a.5.5 0 00.5-.42l.36-2.54c.62-.25 1.2-.6 1.72-1l2.39.96a.5.5 0 00.6-.22l1.92-3.32a.5.5 0 00-.12-.63L20.94 13z"/></svg>
                    </div>
                    <div>
                        <div class="fw-bold">Paramètres</div>
                        <div class="text-muted small">Logo du pôle</div>
                    </div>
                </div>
                <span class="text-muted">&rsaquo;</span>
            </div>
        </a>
        {% endif %}

    </div>
{% endblock %}
```

---

## Partie 13 - Fondations transverses et style

### 13.1 Confirmation en chaîne : jamais `confirm()` natif

Toute action irréversible (suppression de compte, retrait d'un membre
d'équipe, paiement d'adhésion) suit le **même motif** dans ce projet : deux
modales Bootstrap enchaînées, jamais la boîte de dialogue native du
navigateur (`confirm()`), pour rester dans le thème visuel de l'application.

**Rien à coder ici** : ce n'est pas un nouveau fichier ni un bloc à ajouter
quelque part, c'est un schéma récapitulatif (remarque les `...` à
l'intérieur, un vrai fichier n'en contiendrait jamais) qui explique un motif
que tu as **déjà écrit deux fois sans le nommer** : dans
`caisse/templates/caisse/equipe_pole.html` (Partie 7.2, pour le retrait
d'un membre d'équipe) et dans `caisse/templates/caisse/ecole_comptes.html`
(Partie 10.4, pour les suppressions de compte). Relis ces deux fichiers en
te référant au schéma ci-dessous si tu veux revoir comment le relais
JavaScript s'articule :

```html
<form method="post" id="formAction" class="d-none">
    {% csrf_token %}
    <input type="hidden" name="cible_id" id="champCibleId">
</form>

<div class="modal fade" id="modaleAction1" tabindex="-1"> ... </div>
<div class="modal fade" id="modaleAction2" tabindex="-1"> ... </div>

<script>
    var passageVersModale2 = false;
    document.getElementById("btnModaleAction1Confirmer").addEventListener("click", function () {
        passageVersModale2 = true;
        bootstrap.Modal.getInstance(modaleAction1El).hide();
    });
    modaleAction1El.addEventListener("hidden.bs.modal", function () {
        if (passageVersModale2) {
            passageVersModale2 = false;
            new bootstrap.Modal(modaleAction2El).show();
        }
    });
    document.getElementById("btnModaleAction2Confirmer").addEventListener("click", function () {
        document.getElementById("formAction").submit();
    });
</script>
```

Le relais `hidden.bs.modal` → ouverture de la modale suivante est
nécessaire : Bootstrap ne permet pas d'avoir deux modales ouvertes
simultanément sans conflit visuel, il faut attendre que la première ait fini
de se fermer avant d'ouvrir la seconde.

### 13.2 Commentaires de template multi-lignes : le piège `{# #}`

```
{# Ceci est un commentaire Django #}          <- OK, une seule ligne

{# Ceci
   est un commentaire
   sur plusieurs lignes #}                     <- BUG : s'affiche en clair !

{% comment %}
Ceci est un commentaire
sur plusieurs lignes, correctement masque.
{% endcomment %}                                <- OK
```

`{# ... #}` ne supporte **que** les commentaires sur une seule ligne dans
Django. Un commentaire multi-lignes écrit avec cette syntaxe fuit
silencieusement comme texte visible sur la page rendue - toujours utiliser
`{% comment %}...{% endcomment %}` dès qu'un commentaire dépasse une ligne.

### 13.3 Filtrage en direct côté client (sans rechargement de page)

Motif répété sur toutes les listes consultables (comptes, adhérents,
espèces) : chaque ligne porte un attribut `data-recherche` contenant les
champs de recherche pertinents en minuscules, et un script JS masque/affiche
au fil de la frappe, sans aller-retour serveur.

**Rien à coder ici non plus** : comme en 13.1, c'est un schéma (le `...`
dans le `<li>` ne serait jamais dans un vrai fichier), pas un fichier à
créer. Tu as déjà écrit ce motif trois fois : dans
`caisse/templates/caisse/gerer_adherents.html` (Partie 8.2),
`caisse/templates/caisse/gerer_especes.html` (Partie 9.2) et
`caisse/templates/caisse/ecole_comptes.html` (Partie 10.4).

```html
<input type="text" id="rechercheComptes" class="form-control mb-3" oninput="filtrerRecherche()">
<ul id="listeComptes">
    {% for p in profils %}
        <li data-recherche="{{ p.user.first_name|lower }} {{ p.user.last_name|lower }} {{ p.user.username|lower }}">...</li>
    {% endfor %}
</ul>
<p id="aucunResultat" class="d-none">Aucun résultat pour cette recherche.</p>

<script>
function filtrerRecherche() {
    var recherche = document.getElementById('rechercheComptes').value.trim().toLowerCase();
    var auMoinsUn = false;
    document.querySelectorAll('#listeComptes li[data-recherche]').forEach(function (ligne) {
        var correspond = ligne.dataset.recherche.includes(recherche);
        ligne.classList.toggle('d-none', !correspond);
        if (correspond) { auMoinsUn = true; }
    });
    document.getElementById('aucunResultat').classList.toggle('d-none', auMoinsUn || !recherche);
}
</script>
```

### 13.4 Le motif « repli identifiant + badge »

Une règle appliquée systématiquement dans toute l'interface : **afficher
Nom Prénom si disponible, sinon l'identifiant technique avec un badge visible
« Identifiant »**, jamais silencieusement l'un ou l'autre sans distinction.
Cet équilibre a été ajusté plusieurs fois pendant le développement (retirer
l'identifiant totalement, l'utilisateur a jugé cela peu pratique quand les
comptes de test n'ont pas encore de nom renseigné ; le réintroduire en repli
visible a été le compromis final).

**Rien à créer ici non plus** : contrairement à 13.1 et 13.3, ce bloc-ci est
du vrai code complet (pas de `...`), mais c'est le motif exact que tu as
déjà collé un très grand nombre de fois depuis la Partie 7.2, partout où un
nom d'utilisateur s'affiche (`equipe_pole.html`, `ecole_equipe.html`,
`gerer_adherents.html`, `ecole_comptes.html`, et bien d'autres). Cette
section nomme juste le motif après coup, elle ne te demande pas de le
réécrire :

```html
{% if p.user.first_name or p.user.last_name %}
    {{ p.user.first_name }} {{ p.user.last_name }}
{% else %}
    {{ p.user.username }} <span class="badge bg-secondary">Identifiant</span>
{% endif %}
```

### 13.5 Style visuel commun (`base.html`)

Toutes les pages héritent de `base.html`, qui centralise :

- Les couleurs ENSEA (`--ensea: #C8004B`) réinjectées dans les variables
  internes de Bootstrap (`--bs-btn-bg`, etc.) pour que **tous** les
  composants `btn-primary`/`bg-primary`/`text-primary` héritent
  automatiquement du thème, sans surcharge répétée page par page.
- Un retour visuel tactile générique (`transform: scale(0.97)` à l'activation
  d'un `.btn` ou d'une `.card` cliquable), pour donner une sensation
  d'application native même en étant une page web.
- Les motifs réutilisables : `.avatar-utilisateur` (initiales dans un
  cercle), `.puces-categories`/`.puce-categorie` (filtres pilule), `.icone-action`
  (icône ronde des cartes Espace Asso), `.pilule-action`/`.pilule-modifier`/`.pilule-excel`
  (boutons pilule discrets).
- La barre de navigation fixée en bas (`.barre-onglets`), condition
  d'affichage des onglets Asso/Terminal/École pilotée par le context
  processor `droits_navigation` (Partie 2.2), l'onglet actif détecté via
  `request.resolver_match.url_name`.
- La configuration PWA (`manifest.json`, icônes, meta `apple-mobile-web-app-*`)
  permettant d'ajouter l'application à l'écran d'accueil d'un téléphone,
  en plein écran, sans barre d'adresse.

Voici le fichier complet, à l'état final — celui que toutes les pages du
projet étendent via `{% extends "caisse/base.html" %}`. Tu l'as déjà écrit
plusieurs fois en cours de route (une version minimale en Partie 3.0, la
barre d'onglets ajoutée en Partie 5.5, l'onglet Asso ajouté en Partie 7.1) :
**remplace tout son contenu** une dernière fois par cette version, qui
ajoute l'onglet École resté en attente :

```html
{% load static %}
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <title>{% block titre %}Caisse{% endblock %}</title>

    <!-- PWA : permet d'ajouter l'appli a l'ecran d'accueil, en plein ecran -->
    <link rel="manifest" href="{% static 'manifest.json' %}">
    <link rel="apple-touch-icon" href="{% static 'icone-192.png' %}">
    <meta name="theme-color" content="#C8004B">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="ENSEA Cashless">

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {
            --ensea: #C8004B;
            --ensea-dark: #960038;
            --ensea-light: #FFF0F4;
        }
        body { background-color: #F8F9FA; padding-bottom: 80px; }

        /* Couleur ENSEA sur les composants Bootstrap "primary" */
        .btn-primary { --bs-btn-bg: var(--ensea); --bs-btn-border-color: var(--ensea); --bs-btn-hover-bg: var(--ensea-dark); --bs-btn-hover-border-color: var(--ensea-dark); --bs-btn-active-bg: var(--ensea-dark); --bs-btn-active-border-color: var(--ensea-dark); }
        .btn-outline-primary { --bs-btn-color: var(--ensea); --bs-btn-border-color: var(--ensea); --bs-btn-hover-bg: var(--ensea); --bs-btn-hover-border-color: var(--ensea); --bs-btn-active-bg: var(--ensea); }
        .bg-primary { background-color: var(--ensea) !important; }
        .text-primary { color: var(--ensea) !important; }
        .border-primary { border-color: var(--ensea) !important; }
        .text-ensea { color: var(--ensea); }

        /* Carte solde avec cercle decoratif en relief */
        .carte-solde { background: linear-gradient(135deg, var(--ensea), var(--ensea-dark)); color: #fff; border: none; border-radius: 18px; position: relative; overflow: hidden; }
        .carte-solde::after {
            content: '';
            position: absolute;
            top: -30px;
            right: -30px;
            width: 100px;
            height: 100px;
            background: rgba(255,255,255,0.08);
            border-radius: 50%;
        }
        .pastille-statut {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
        }
        .point-statut { width: 6px; height: 6px; border-radius: 50%; background: #4ADE80; }

        /* Avatar rond avec initiales */
        .avatar-utilisateur {
            width: 42px; height: 42px; border-radius: 50%;
            background: var(--ensea-light); color: var(--ensea);
            display: flex; align-items: center; justify-content: center;
            font-weight: 800; font-size: 14px;
            border: 2px solid #fff; box-shadow: 0 2px 8px rgba(200,0,75,0.15);
            flex-shrink: 0;
        }

        /* Bouton adhesion en forme de carte plutot que bouton plein */
        .bouton-adhesion {
            background: #fff; color: var(--ensea); border: 1.5px solid var(--ensea);
            padding: 13px 16px; border-radius: 14px; font-size: 13px; font-weight: 700;
            display: flex; align-items: center; justify-content: center; gap: 8px;
            text-decoration: none; box-shadow: 0 2px 6px rgba(200,0,75,0.06);
        }
        .bouton-adhesion:active { transform: scale(0.98); background: var(--ensea-light); }

        /* Etat vide (aucune transaction) */
        .etat-vide {
            background: #fff; border: 1px dashed #E2E8F0; border-radius: 16px;
            padding: 30px 16px; display: flex; flex-direction: column; align-items: center;
            justify-content: center; gap: 8px; text-align: center;
        }
        .etat-vide-icone {
            width: 36px; height: 36px; border-radius: 50%; background: #F8F9FA;
            display: flex; align-items: center; justify-content: center; color: #94A3B8;
        }

        /* Puces de filtrage par categorie (page Gerer > Catalogue) */
        .puces-categories { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 4px; }
        .puces-categories::-webkit-scrollbar { display: none; }
        .puce-categorie {
            padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600;
            background: #fff; border: 1px solid #E2E8F0; color: #64748B;
            white-space: nowrap; text-decoration: none; display: inline-block;
        }
        .puce-categorie.active { background: var(--ensea-light); border-color: var(--ensea); color: var(--ensea); font-weight: 700; }

        /* Carte produit (page Gerer > Catalogue) */
        .ligne-produit {
            background: #fff; border: 1px solid #E2E8F0; border-radius: 14px; padding: 12px;
            display: flex; align-items: center; justify-content: space-between; gap: 10px;
            text-decoration: none; color: inherit;
        }
        .miniature-produit {
            width: 44px; height: 44px; border-radius: 10px; background: #F1F5F9;
            display: flex; align-items: center; justify-content: center; overflow: hidden;
            border: 1px solid #E2E8F0; flex-shrink: 0;
        }
        .miniature-produit img { width: 100%; height: 100%; object-fit: cover; }
        .etiquette-stock { background: #EFF6FF; color: #2563EB; padding: 2px 6px; border-radius: 6px; font-size: 10px; font-weight: 600; }

        /* Onglets Catalogue/Evenements : meme taille dans les deux etats,
           seule la couleur change, pour eviter tout effet de "saut" au clic. */
        .onglet-gerer {
            padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 700;
            text-decoration: none; background: #fff; border: 1px solid #E2E8F0;
            color: #64748B; display: inline-block;
        }
        .onglet-gerer.active { background: var(--ensea); border-color: var(--ensea); color: #fff; }

        /* Bouton pilule discret (Modifier, Excel...) */
        .pilule-action {
            padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 700;
            border: none; text-decoration: none; display: inline-block; cursor: pointer;
        }
        .pilule-modifier { background: var(--ensea-light); color: var(--ensea); }
        .pilule-excel { background: #ECFDF5; color: #107C41; border: 1px solid rgba(16,124,65,0.2); }
        .pilule-primaire { background: var(--ensea); color: #fff; }

        /* Masquer les fleches natives du champ nombre */
        input[type=number]::-webkit-inner-spin-button,
        input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
        input[type=number] { -moz-appearance: textfield; appearance: textfield; }

        /* Cercle d'icone des boutons d'action (espace asso) */
        .icone-action { width: 40px; height: 40px; border-radius: 12px; background: var(--ensea-light); color: var(--ensea); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
        .icone-action svg { width: 20px; height: 20px; fill: currentColor; }

        /* Retour visuel quand on survole/touche une carte ou un bouton cliquable */
        a .card, .btn { transition: background-color .12s ease, border-color .12s ease, transform .08s ease; }
        a .card:hover:not(.bg-primary), a .card:active:not(.bg-primary) {
            background-color: var(--ensea-light);
            border-color: var(--ensea);
        }
        .btn:active, a .card:active { transform: scale(0.97); }

        /* Barre d'onglets fixee en bas */
        .barre-onglets { position: fixed; bottom: 0; left: 0; right: 0; height: 64px; background: #fff; border-top: 1px solid #E2E8F0; display: flex; justify-content: space-around; align-items: center; z-index: 100; }
        .onglet { display: flex; flex-direction: column; align-items: center; gap: 3px; color: #64748B; font-size: 10px; font-weight: 600; text-decoration: none; }
        .onglet.actif { color: var(--ensea); }
        .onglet svg { width: 22px; height: 22px; fill: currentColor; }
    </style>
</head>
<body>
    <nav class="navbar bg-white shadow-sm mb-3">
        <div class="container">
            <a class="navbar-brand fw-bold text-ensea" href="{% url 'accueil' %}">Mon portefeuille ENSEA</a>
            {% if user.is_authenticated %}
                <form method="post" action="{% url 'logout' %}" class="d-inline">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-outline-secondary btn-sm">Déconnexion</button>
                </form>
            {% else %}
                <a href="{% url 'login' %}" class="btn btn-outline-secondary btn-sm">Connexion</a>
            {% endif %}
        </div>
    </nav>

    <main class="container">
        {% block contenu %}{% endblock %}
    </main>

    {% if user.is_authenticated %}
    {% with onglet=request.resolver_match.url_name %}
    <nav class="barre-onglets">
        <a class="onglet {% if onglet == 'accueil' %}actif{% endif %}" href="{% url 'accueil' %}">
            <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
            Accueil
        </a>
        {% if est_admin_ecole %}
        <a class="onglet {% if onglet == 'espace_ecole' or onglet == 'ecole_equipe' or onglet == 'ecole_recettes' or onglet == 'ecole_adherents' or onglet == 'ecole_codes' %}actif{% endif %}" href="{% url 'espace_ecole' %}">
            <svg viewBox="0 0 24 24"><path d="M12 3L1 9l11 6 9-4.91V17h2V9L12 3zm0 13.5L3.74 12 12 7.5 20.26 12 12 16.5z"/></svg>
            École
        </a>
        {% endif %}
        {% if a_droits_vente %}
        <a class="onglet {% if onglet == 'asso_choix' or onglet == 'espace_asso' or onglet == 'detail_pole' or onglet == 'gerer_produits' or onglet == 'equipe_pole' %}actif{% endif %}" href="{% url 'asso_choix' %}">
            <svg viewBox="0 0 24 24"><path d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10z"/></svg>
            Asso
        </a>
        <a class="onglet {% if onglet == 'terminal_pole' or onglet == 'terminal_choix_pole' %}actif{% endif %}" href="{% url 'terminal_choix_pole' %}">
            <svg viewBox="0 0 24 24"><path d="M12 19c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm-6 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 12c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm12-12c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/></svg>
            Terminal
        </a>
        {% endif %}
        <a class="onglet {% if onglet == 'payer' %}actif{% endif %}" href="{% url 'payer' %}">
            <svg viewBox="0 0 24 24"><path d="M3 11h8V3H3v8zm2-6h4v4H5V5zm8-2v8h8V3h-8zm6 6h-4V5h4v4zM3 21h8v-8H3v8zm2-6h4v4H5v-4zm13-2h-2v3h-3v2h3v3h2v-3h3v-2h-3z"/></svg>
            Payer
        </a>
        <a class="onglet {% if onglet == 'recharger' %}actif{% endif %}" href="{% url 'recharger' %}">
            <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11h-4v4h-2v-4H7v-2h4V7h2v4h4v2z"/></svg>
            Recharger
        </a>
        <a class="onglet {% if onglet == 'info' %}actif{% endif %}" href="{% url 'info' %}">
            <svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
            Info
        </a>
    </nav>
    {% endwith %}
    {% endif %}

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

Note pour la construction pas à pas : ce fichier grossit **au fur et à
mesure** du projet (chaque nouvelle classe CSS listée ci-dessus, chaque
nouvel onglet de la barre du bas, est ajoutée à ce même fichier à l'étape où
la fonctionnalité correspondante apparaît, Partie 3 pour la structure de
base et les onglets Vendre/Payer/Recharger/Info, Partie 6 pour
`.puces-categories`/`.onglet-gerer`, Partie 7 pour `.icone-action`, Partie
10 pour l'onglet École, etc.). La version montrée ici est l'**état final**,
avec tout accumulé, c'est elle qu'il faut avoir en tête comme référence,
sans avoir besoin de rejouer chaque ajout dans l'ordre.

### 13.6 Masquage systématique du solde

Récapitulatif d'une règle de confidentialité qui traverse toute
l'application, introduite après un vrai constat de fuite (Partie 3.3) :
**aucune page ni aucun message d'erreur ne montre le solde d'un compte à
quelqu'un d'autre que son propriétaire**. Ni sur la confirmation de vente
(`vente_ok.html`), ni sur la confirmation de recharge
(`recharge_especes_ok.html`), ni dans les messages « solde insuffisant »
(qui n'affichent que le montant demandé, une donnée publique). Seule la page
d'accueil personnelle de l'utilisateur affiche son propre solde.

---

## Partie 14 - Ce qu'il reste à faire pour la production

Ce document décrit l'état fonctionnel complet du projet en développement.
Plusieurs points sont **explicitement reportés**, documentés au fil du texte
au moment où ils sont apparus :

1. **Authentification CAS de l'école**, à la place de l'authentification
   Django standard (Partie 4.1). Le remplacement ne touchera qu'un point
   d'entrée technique (`LoginView`) ; toute la logique de rôles et de droits
   qui en dépend (basée sur `request.user`) reste inchangée.
2. **PostgreSQL en production**, à la place de SQLite (Partie 3.3). SQLite
   ne verrouille pas ligne par ligne et reste fruste pour une vraie
   concurrence entre plusieurs caisses simultanées - le réglage `timeout`
   actuel est un palliatif de développement, pas une solution de production.
3. **API réelle HelloAsso**, actuellement isolée dans une fonction unique
   marquée TODO (`caisse/helloasso.py`, Partie 6.4), à brancher selon les
   identifiants réels du pôle concerné.
4. **Fichiers statiques (CSS/JS Bootstrap, jsQR) servis localement**, à la
   place du CDN actuellement utilisé en développement - nécessaire pour un
   fonctionnement hors ligne fiable et pour ne pas dépendre de la
   disponibilité d'un service tiers en production.
5. **`ALLOWED_HOSTS = ["*"]`** (si tu l'as réglé pour tester sur le réseau
   local, voir l'annexe ci-dessous) est sans risque uniquement parce que
   `DEBUG=True` et que le serveur de développement n'est jamais exposé
   au-delà du réseau local : à restreindre à une vraie liste de domaines le
   jour du déploiement.
6. **`SECRET_KEY`** doit être régénérée et déplacée dans `.env` (jamais dans
   le dépôt) avant toute mise en production.

---

## Annexe - Ouvrir le serveur de développement sur le réseau local

Par défaut, `python manage.py runserver` n'écoute que sur `127.0.0.1`
(localhost) : seul l'ordinateur qui fait tourner le serveur peut accéder au
site, via `http://127.0.0.1:8000`. C'est volontaire et c'est la bonne valeur
par défaut pour développer (Partie 0).

Pour tester l'application **depuis un autre appareil** sur le même réseau
Wi-Fi (ton téléphone, l'ordinateur d'un camarade), il faut explicitement
demander à `runserver` d'écouter sur toutes les interfaces réseau, pas
seulement `127.0.0.1` :

```bash
python manage.py runserver 0.0.0.0:8000
```

Trouve ensuite l'adresse IP locale de ta machine sur le réseau :

```bash
hostname -I
```

(la première adresse affichée, généralement de la forme `192.168.x.x` ou
`10.x.x.x`).

**Une étape supplémentaire est nécessaire ici** : par défaut, Django
n'accepte que les requêtes dont l'en-tête `Host` vaut `localhost`,
`127.0.0.1` ou `[::1]`, même avec `runserver 0.0.0.0:8000`, une requête
arrivant via ton IP réseau (ex. `192.168.1.42:8000`) est **rejetée** avec
une erreur `DisallowedHost` tant que cette IP n'est pas explicitement
autorisée. Ouvre `cashless/settings.py` et remplace la ligne `ALLOWED_HOSTS`
existante par :

```python
ALLOWED_HOSTS = ["*"]
```

Depuis l'autre appareil, connecté au **même réseau Wi-Fi**, va sur
`http://<cette-adresse-ip>:8000` (remplace par la tienne, par exemple
`http://192.168.1.42:8000`).

**Pourquoi `["*"]` est sans risque ici, mais pas à garder en production** :
cette valeur autorise n'importe quelle IP d'origine, ce qui n'est acceptable
que parce que `DEBUG=True` et que l'exposition reste limitée au réseau local
(personne à l'extérieur du Wi-Fi ne peut y accéder) - exactement le point 5
de la liste ci-dessus, à durcir avant toute mise en production réelle.

---
# Bravo tu as fini ce "PETIT" tutoriel