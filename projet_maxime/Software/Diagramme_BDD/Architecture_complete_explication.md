# Architecture complète - ENSEA Cashless (état réel du code)

> Document d'architecture **descriptif** : il décrit ce qui existe
> réellement dans le code aujourd'hui, reconstruit pas à pas dans
> `Tutoriel_Application_Cashless_ENSEA/Tuto_Django2.md`. Chaque section
> renvoie à une Partie précise du tutoriel.

---

## Sommaire

1. [Principes directeurs](#0-principes-directeurs)
2. [Authentification et rôles](#1-authentification-et-rôles)
3. [Étudiants et comptes](#2-étudiants-et-comptes)
4. [Catalogue et événements](#3-catalogue-et-événements)
5. [Vente et encaissement](#4-vente-et-encaissement)
6. [Espèces et adhésions](#5-espèces-et-adhésions)
7. [Espace École et confidentialité](#6-espace-école-et-confidentialité)
8. [Exports Excel](#7-exports-excel)
9. [Emails](#8-emails)
10. [Ce qui n'est pas fait, assumé](#9-ce-qui-nest-pas-fait-assumé)
11. [Schéma BDD](#10-schéma-bdd)

---

## 0. Principes directeurs

Décisions transverses qui traversent tout le code, posées dès la Partie 1 du
tutoriel et jamais transgressées ensuite :

- **`on_delete` reflète la valeur comptable de la donnée.** Tout ce qui porte
  de l'historique (`Pole`, `Produit`, `ProfilUtilisateur`) est `PROTECT` :
  interdit de supprimer tant que des lignes en dépendent. Seule
  `LigneTransaction → Transaction` est `CASCADE` (une ligne de ticket n'a pas
  de sens sans son ticket). Les relations non porteuses d'histoire
  (`Produit.categorie`, `Produit.evenement`) sont `SET_NULL`.
- **Jamais de suppression physique d'un compte.** `ProfilUtilisateur.anonymiser()`
  vide les champs personnels et coupe l'accès (`is_active=False`), mais ne
  supprime jamais la ligne : l'historique financier (ventes, recharges,
  adhésions) doit rester lisible même après suppression du compte.
- **L'argent est toujours un `DecimalField`**, jamais un `float`.
- **Une ligne de vente fige (« snapshot ») le libellé et le prix** au moment
  de l'achat (`LigneTransaction.libelle`/`prix_unitaire`), indépendamment du
  `Produit` source, qui peut changer de prix ou disparaître ensuite.
- **Toute écriture financière est atomique et verrouillée.** Chaque flux qui
  touche un solde (`encaisser`, `terminal_pole`, `adherer_pole`,
  `recharger_especes`) passe par `db_transaction.atomic()` +
  `select_for_update()` sur le profil et les produits concernés, avec
  revérification des données **juste avant** l'écriture (jamais depuis ce qui
  a été lu au remplissage du panier). Voir §4.
- **Une seule app tant que c'est lisible.** Le choix de départ (Partie 0) est
  un projet unique et une app unique (`caisse`) ; le seul découpage réel est
  `vues_ecole.py`, séparé de `views.py` quand ce dernier a grossi au point de
  nuire à la lecture (Partie 10).

---

## 1. Authentification et rôles

### 1.1 Connexion : Django standard aujourd'hui, CAS prévu

L'authentification actuelle est **le système Django natif**
(`django.contrib.auth`), posée dès
la Partie 0 (`createsuperuser`) et câblée en Partie 3.0/4.1
(`LoginView`/`LogoutView`, `LOGIN_URL`, `LOGIN_REDIRECT_URL`). Le
remplacement par le CAS de l'école est **délibérément reporté** (Partie 0 et
Partie 14) : c'est un point d'entrée technique isolé (`LoginView`), la
logique de rôles qui en dépend (basée sur `request.user`) n'a pas besoin de
changer le jour où ça arrivera.

### 1.2 Rôles : `Affectation`

Le modèle réel est `Affectation(user, pole, role, droit_*)` (`caisse/models.py`,
Partie 1.4), une seule table qui relie un `User` à un rôle **sur un pôle
précis** (ou `pole=None` pour un rôle global) :

| Rôle | Portée | Particularité |
|---|---|---|
| `VENDEUR` | un pôle | droits supplémentaires accordables au cas par cas |
| `ADMIN_POLE` | un pôle | a déjà tous les droits sur son pôle |
| `ADMIN_ADE` | global (`pole=None`) | voit et gère tous les pôles |
| `ADMIN_ECOLE` | global (`pole=None`) | gère comptes/rôles/codes, jamais les prix |

Une personne peut cumuler plusieurs `Affectation` (plusieurs rôles, sur des
pôles différents), sans sélecteur de contexte en session : les fonctions de
`caisse/roles.py` (`poles_vendables`, `poles_gerables`, `peut_vendre`,
`peut_gerer`, ...) recalculent à chaque requête l'ensemble des pôles
accessibles.

**Droits à la carte.** Sept booléens `droit_*` sur `Affectation`, ajoutés
après qu'un système à deux niveaux (Vendeur simple / Admin complet) s'est
révélé trop rigide (Partie 2.1) : six sont accordables par n'importe quel
admin de pôle à ses vendeurs (`droit_gerer_produits`, `droit_adhesions`,
`droit_adhesion_especes`, `droit_equipe`, `droit_exporter`,
`droit_parametres`) ; le septième, `droit_recharger_especes`, reste
**réservé à l'admin ADE**, jamais délégable par un admin de pôle (question de
confiance sur la manipulation d'espèces, Partie 2.1/7).

**Garde-fou anti-escalade.** `peut_voir_equipe` (voir qui a quels droits) est
accordable à un vendeur ; `peut_modifier_equipe` (les changer) reste
**toujours** réservé à un admin, sans exception, sinon un vendeur avec accès
à l'onglet Équipe pourrait s'auto-attribuer n'importe quel droit (Partie
2.1). De même, `ecole_equipe` refuse de retirer le **dernier** `ADMIN_ECOLE`
(Partie 10.1) : sans ce garde-fou serveur, il serait possible de bloquer tout
le système (plus personne pour distribuer rôles et codes).

### 1.3 Code de sécurité : la deuxième serrure

`CodeSecuriteAdmin` (Partie 1.6/4.2) est un code à 6 chiffres, propre à
`(user, pole)`, **haché** comme un mot de passe, généré par un admin école et
remis en main propre. `VerifierCodeMiddleware` (Partie 4.3) l'exige à
**chaque** requête authentifiée tant que `session["code_verifie"]` n'est pas
posé, pas seulement `LOGIN_REDIRECT_URL`, qui laissait un lien profond
cliqué avant connexion court-circuiter l'étape (bug réel corrigé, Partie
4.3). Étendu à **tout** rôle, vendeur compris (Partie 10.2), pas seulement
aux rôles à pouvoir.

**Piège corrigé (Partie 4.4)** : sur un rôle global (`pole=NULL`),
`unique_together` ne détecte pas toujours deux lignes `pole=NULL` comme
identiques (NULL n'égale rien en SQL), régénérer un code avec
`update_or_create` pouvait laisser l'ancien valide en plus du nouveau. La
correction supprime explicitement l'ancien avant de créer le nouveau.

Il n'y a pas de notion de poste de caisse authentifié par un secret machine
séparé : une caisse est juste un navigateur connecté avec un compte `User`
humain, comme n'importe quelle page de l'app.

---

## 2. Étudiants et comptes

### 2.1 `ProfilUtilisateur` : un compte, un profil, un statut

`ProfilUtilisateur` (Partie 1.3) prolonge `User` en `OneToOneField` (`solde`,
`uid_rfid`, `secret_qr`, `statut_compte`, `date_naissance`). Le solde ne vit
**que** sur le profil, directement débité/crédité dans la même transaction
atomique que la vente ou la recharge (§4), sans journal de mouvements séparé.

Cycle de vie réel (voir `Machine_a_etats_explication.md`, §1) :

```
ACTIF ──anonymiser()──▶ ANONYMISE   (irréversible)
ACTIF ──(prévu)──▶ DESACTIVE ──(prévu)──▶ ACTIF   (réversible, pas encore câblé)
```

`DESACTIVE` existe dans les `choices` du modèle mais **aucun code ne
l'écrit ni ne le lit** aujourd'hui. L'usage visé : un blocage **temporaire et
réversible** du compte ou du QR de paiement (connexion et paiement bloqués,
historique conservé), déclenchable par l'étudiant lui-même ou par un admin
école en cas de fuite de données (identifiant ou QR compromis) — à
distinguer nettement de la suppression définitive (§2.3), qui reste
irréversible après le délai.

### 2.2 Identification au comptoir : QR dynamique ou identifiant saisi

Le moyen de paiement réellement câblé est le **QR dynamique**
(`JetonPaiement`, Partie 1.5/5.2) : un jeton à usage unique, régénéré à
chaque affichage, expire à 120 secondes (`est_valide()`). Le champ
`uid_rfid` existe sur `ProfilUtilisateur` mais n'est utilisé nulle part dans
le flux d'encaissement actuel — c'est un identifiant saisi manuellement
(`identifiant`) qui sert de repli quand le scan n'est pas possible, jamais
une carte physique lue par un lecteur dédié.

Aucune protection anti-fraude au-delà de la fenêtre de validité de 120
secondes du jeton QR : le solde exact n'est **jamais affiché** au vendeur, ni
en succès ni en échec (seul le montant demandé, une donnée publique,
apparaît dans « Solde insuffisant », Partie 3.3, principe rappelé en Partie
13.6). Un compte qui présente son identifiant à la main (sans QR) n'a aucune
vérification visuelle équivalente.

### 2.3 Suppression : délai de 90 jours

`DemandeSuppressionCompte` (Partie 1.6/10.4) modélise un délai de 90 jours
avant anonymisation définitive, avec sortie anticipée si
`remboursement_effectue` est coché. Il n'y a qu'**un seul objet** porteur à
la fois de l'identité et du paiement (`ProfilUtilisateur`) : pas de moyen
d'identification temporaire séparé pour un nouvel arrivant sans carte, le
compte existe ou n'existe pas.

---

## 3. Catalogue et événements

`Pole` → `Categorie`/`Evenement` → `Produit` (Partie 1.2/6). Un `Produit` est
**soit** un article permanent (`categorie` renseignée), **soit** un billet
ou article de soirée (`evenement` renseignée), **soit** un produit technique
de vente libre (`est_vente_libre`, utilisé par le Terminal, jamais visible au
catalogue), les deux premiers cas sont mutuellement exclusifs en pratique,
mais rien en base ne l'impose formellement (les deux FK sont nullables
indépendamment).

Chaque pôle a ses propres `TarifAdhesion` (Partie 1.6/8.1), sans mécanisme de
réduction croisée entre associations. Le panier vit en session (Partie 3.1,
pas en base) : le stock n'est vérifié et décrémenté qu'**au moment de
l'encaissement réel**, sous verrou (`select_for_update`), jamais réservé à
l'ajout au panier — au pire, l'acheteur voit une erreur claire « stock
insuffisant » au moment de payer, jamais une vente qui dépasse le stock réel.

`retire` (Partie 1.2) distingue un produit qui n'est plus vendu **du tout**
(disparaît même de la gestion courante) de `disponible=False` (rupture
temporaire, reste visible et grisé), deux champs séparés, pas un seul état
combiné.

---

## 4. Vente et encaissement

### 4.1 Pas de machine à états pour `Transaction`

`Transaction` n'a **aucun champ `statut`** dans le code réel. Une vente
n'existe en base que dans un seul état, tout-ou-rien : le résultat d'un bloc `atomic()` exécuté en
une fois (`encaisser()`/`terminal_pole()`, Partie 3.3/3.5). Détail complet
dans `Machine_a_etats_explication.md`, en préambule.

### 4.2 Le motif d'encaissement, répété partout où de l'argent bouge

```python
with db_transaction.atomic():
    profil = ProfilUtilisateur.objects.select_for_update().get(pk=...)
    # revérifications sur donnees fraiches : solde, stock, evenement vendable...
    if condition_invalide:
        raise EchecEncaissement("message clair")
    # écritures : débit profil, crédit pôle, décrément stock, création Transaction/LigneTransaction
```

`EchecEncaissement` (Partie 1.2/3.3) est une exception métier maison, pas une
exception Python générique : son rôle est d'annuler proprement le bloc
`atomic()` (rollback complet, aucune écriture partielle) et de porter un
message directement affichable. Ce motif exact revient dans `encaisser`
(catalogue), `terminal_pole` (montant libre), `adherer_pole` (adhésion
portefeuille) et `recharger_especes`, jamais de variante locale.

**SQLite, pas PostgreSQL.** `select_for_update()` verrouille les lignes
concernées, mais SQLite ne verrouille pas ligne par ligne : deux écritures
strictement simultanées se percutent avec une `OperationalError` immédiate,
lissée par un `timeout=20` dans `DATABASES["OPTIONS"]` (Partie 3.3). Cette
limite est **connue et assumée** pour le développement — PostgreSQL est
listé comme prérequis de production (§9 ci-dessous), pas un choix définitif.

### 4.3 Pas de PSP branché, pas de mode hors-ligne

- **Aucun mode hors-ligne.** La caisse est une page web classique, sans file
  locale ni synchronisation différée. Une coupure réseau bloque simplement
  l'usage, comme n'importe quelle app web.
- **Aucun PSP réellement branché.** `Recharge.statut`/`mode_paiement`
  prévoient déjà `HELLOASSO`/`EN_ATTENTE`/`ECHOUEE`, mais rien ne les écrit :
  `/recharger/` affiche un bouton désactivé (Flux 5 de
  `Diagramme_de_flux_explication.md`), et il n'existe **aucune route de
  webhook** dans `caisse/urls.py`. Le seul chemin de recharge réellement
  câblé est `recharger_especes` (Partie 9.1), qui écrit directement
  `statut="CONFIRMEE"` sans jamais passer par `EN_ATTENTE`.
- **HelloAsso, sens inverse seulement.** `inscrire_sur_helloasso()`
  (`caisse/helloasso.py`, Partie 3.3/6.4) pousse une inscription vers
  HelloAsso après une vente de billet interne (`est_billet=True`), isolée
  dans un `try/except` qui absorbe toute erreur réseau/API, jamais l'inverse
  (recevoir un paiement HelloAsso). C'est un stub marqué TODO, sans
  identifiants réels.

---

## 5. Espèces et adhésions

### 5.1 `Recharge.pole` stocké explicitement, jamais déduit

Un vrai bug évité (Partie 1.3) : le pôle d'une recharge espèces est écrit
**directement** sur la ligne au moment de l'opération, jamais déduit de
l'affiliation de la personne qui encaisse. Un admin de pôle affecté à un seul
pôle donnerait le même résultat par déduction, mais un admin ADE peut
recharger depuis n'importe quel pôle selon la soirée — sans ce champ
explicite, chacune de ses recharges se serait mise à apparaître dans le
suivi de **tous** les pôles à la fois.

### 5.2 Année scolaire unique, deux chemins de paiement

`annee_scolaire_courante()` (`caisse/roles.py`, coupure début août) est
utilisée par **les deux** chemins de paiement d'une adhésion (portefeuille
`adherer_pole`, espèces `payer_adhesion_especes`/`gerer_adherents`), pour que
la contrainte d'unicité `(pole, profil, annee)` détecte bien un doublon quel
que soit le mode de paiement (Partie 8.1).

### 5.3 Adhésion espèces : page dédiée, pas un sous-écran conditionnel

`payer_adhesion_especes` (Partie 8.3) est une page **séparée** de
`gerer_adherents`, réservée à une seule action, plutôt qu'un bloc
conditionnel de plus dans l'écran de gestion complète : un vendeur avec
`droit_adhesion_especes` ne doit **jamais** voir la liste complète des
adhérents ni pouvoir changer un prix. Une page physiquement incapable de
montrer autre chose que son unique action est jugée plus sûre qu'une
condition d'affichage supplémentaire dans un écran déjà riche.

---

## 6. Espace École et confidentialité

`caisse/vues_ecole.py` regroupe tout ce qui relève de l'admin école (comptes,
rôles, codes), séparé de `views.py` une fois ce dernier devenu trop
volumineux (Partie 10) le seul vrai découpage de fichiers du projet, motivé
par la lisibilité.

**Séparation des pouvoirs :**

| Rôle | Voit les noms ? | Voit l'argent ? | Où |
|---|---|---|---|
| Admin école | oui (comptes, correction de profil) | recettes **agrégées par grande catégorie** | `ecole_recettes`, Partie 10.5 |
| Admin de pôle / vendeur avec droit | oui (identifiant saisi/scanné, le temps de l'encaissement) | oui, dans le détail de son pôle | Partie 3.3, 9.2 |
| Export financier (n'importe quel rôle `peut_exporter`) | **jamais** | oui, détaillé | `caisse/exports.py`, `_anonymiser()` → `ETU-00042` |
| `rechercher_identifiant` | oui, **exceptionnellement**, réservé à l'admin ADE | — | Partie 12.2 |

Le filtrage se fait directement dans chaque vue (`pole.transactions.filter(...)`,
`Adhesion.objects.filter(pole=pole, ...)`), sans couche d'abstraction
partagée, cohérent avec une base à quelques pôles, pas conçu pour
s'étendre automatiquement à une fédération d'associations.

**Un compte anonymisé est réellement irrécupérable** : `rechercher_identifiant`
refuse explicitement de résoudre un `ETU-xxxxx` dont le `statut_compte` est
`ANONYMISE` (Partie 12.2), l'anonymisation efface l'identité, pas seulement
son affichage.

---

## 7. Exports Excel

Trois familles distinctes, avec une même règle de fond (« la confidentialité
dépend de l'usage de l'écran, pas d'un réglage global », Partie 12.3) :

- **Financier, anonyme** (`export_pole`, `caisse/exports.py`) : un
  identifiant technique stable `ETU-{pk:05d}` remplace systématiquement le
  nom, sur trois onglets (Transactions / Événements / Produits).
- **Opérationnel, nominatif** (`exporter_participants`) : vrais noms, colonne
  « Majeur » en Oui/Non/Inconnu calculée (jamais l'âge exact, réservé à
  l'admin école), case « Présent » laissée vide à cocher à la main,
  `openpyxl` ne sait pas poser de vraie case à cocher Excel 365.
- **Trésorerie, nominatif** (`exporter_adherents`, `exporter_especes`) : nom,
  montant, mode de paiement, encaisseur, utile à la gestion du pôle, avec
  totaux en bas de feuille.

Tous les exports sont **déclenchés manuellement**, un téléchargement direct (`HttpResponse` + `Content-Disposition: attachment`),
jamais un envoi programmé.

---

## 8. Emails

`caisse/recus.py` (Partie 11) centralise trois envois (`envoyer_recu`,
`envoyer_email_code`, `envoyer_email_suppression`), tous protégés par un
`try/except` autour de `send_mail`/`message.send(fail_silently=True)` : un
échec d'envoi ne doit **jamais** faire échouer l'opération métier qui le
déclenche.

**Bascule automatique console/SMTP** selon la présence de `EMAIL_HOST` dans
`.env` (Partie 11.1) : rien ne bloque en développement sans serveur SMTP
configuré. Le mot de passe reste optionnel (le relais interne de l'école
accepte l'envoi sans authentification), avec `EMAIL_TIMEOUT=10` pour éviter
qu'un port bloqué ne gèle la page indéfiniment, bug réellement rencontré.

---

## 9. Ce qui n'est pas fait

Repris et regroupé depuis la Partie 14 du tutoriel :

1. **CAS de l'école**, à la place de l'auth Django standard (§1.1).
2. **PostgreSQL**, à la place de SQLite (§4.2), vraie concurrence entre
   plusieurs caisses simultanées.
3. **API réelle HelloAsso**, isolée dans une fonction unique marquée TODO
   (§4.3).
4. **Fichiers statiques servis localement**, à la place du CDN Bootstrap/jsQR
   actuel.
5. **`ALLOWED_HOSTS = ["*"]`**, sans risque uniquement parce que `DEBUG=True`
   et l'exposition limitée au réseau local (voir l'annexe du tutoriel).
6. **`SECRET_KEY`** à régénérer et déplacer en `.env` avant mise en
   production.
7. **Blocage réversible de compte (`DESACTIVE`)** - voir §2.1 : état
   présent dans le schéma, aucun code ne l'écrit ni ne le lit ; feature
   envisagée mais pas encore implémentée.
8. **Tarif différencié adhérent / non-adhérent sur les produits**, billets
   compris, selon que l'acheteur a payé ou non l'adhésion du pôle concerné
   (`Adhesion` existe déjà, voir §5.2, mais `Produit` n'a qu'un seul champ
   `prix` — pas de `prix_adherent`/`prix_non_adherent`, ni de résolution
   automatique du bon tarif à l'encaissement).
9. **Caméra accessible en HTTPS**, condition déjà documentée pour le scan QR
   (`getUserMedia`, Partie 3.4) : fonctionne sur `localhost` en développement,
   mais nécessitera un vrai certificat HTTPS pour être testée et utilisée
   depuis un téléphone en dehors de ce cas particulier.
10. **Notifications push lors d'un achat** (et d'une recharge) : seul un
    reçu par email existe aujourd'hui (`envoyer_recu`, Partie 11) ; pas de
    notification push.
11. **Carte RFID réellement utilisée à l'encaissement** — voir §2.2 : le
    champ `uid_rfid` existe sur `ProfilUtilisateur` mais rien ne l'écrit ni
    ne le lit dans le flux de vente actuel, seul le QR dynamique et
    l'identifiant saisi à la main sont câblés.
12. **Code de sécurité étendu à tous les comptes** (pas seulement aux rôles à
    pouvoir) — à évaluer : `CodeSecuriteAdmin` (§1.3) protège aujourd'hui les
    comptes vendeur/admin, l'étendre à chaque étudiant renforcerait la
    protection du portefeuille mais ajoute de la friction à chaque connexion,
    à peser avant de généraliser.

Le projet reste volontairement une app unique tant qu'elle n'est pas devenue
illisible, sans plan de migration vers des apps Django indépendantes ; le
seul vrai précédent de découpage (`vues_ecole.py`) a été motivé après coup
par la taille réelle du fichier, pas anticipé à l'avance.

---

## 10. Schéma BDD

Le schéma réel (15 modèles + `auth_user`), généré depuis `caisse/models.py`
à l'état final, est dans `bdd_cashless.dbml` (à coller sur dbdiagram.io),
expliqué table par table dans `bdd_cashless_explication.md`. Les flux
d'exécution (qui appelle quoi, dans quel ordre, avec quelles erreurs
possibles) sont dans `Diagramme_de_flux_explication.md`. Les cycles de vie à
plusieurs états réels (compte étudiant, jeton QR, recharge, demande de
suppression) sont dans `Machine_a_etats_explication.md`.

Le schéma réel n'a **ni** table de mouvements séparée du solde (le solde est
débité/crédité directement, §4.2), **ni** table d'audit générique (la
traçabilité passe par des champs dédiés — `encaisse_par`, `definie_par`,
`demande_par` — pas par un journal centralisé), **ni** table de liaison
ternaire pour les rôles (`Affectation` porte directement `pole` et `role`,
§1.2).
