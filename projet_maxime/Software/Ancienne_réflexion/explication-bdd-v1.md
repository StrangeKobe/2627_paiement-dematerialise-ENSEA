# Explication de la base de données - Plateforme paiement ENSEA V1

> Document de référence pour comprendre chaque table et chaque champ.
> À lire en parallèle de `schema-bdd-v1.dbml` (à coller sur https://dbdiagram.io).

---

## Pourquoi cette version ?

On s'appuie sur ce que Django fournit déjà (authentification, groupes) pour éviter de
réinventer des tables. Règle simple : si Django le fait nativement, on l'utilise ; si c'est
une fonctionnalité avancée, on la garde seulement si elle est utile dès la rentrée.

Cette version contient **17 tables** réparties en 11 blocs (dont 3 tables Django natives
qu'on ne code pas soi-même : `auth_user`, `auth_group`, `auth_user_groups`). Par rapport à la première
ébauche, on a ajouté les catégories, les notifications et les événements, et on a clarifié la hiérarchie Super Admin / Admin ADE / Admin Asso.

---

## Vue d'ensemble

```
BLOC 1 — AUTH DJANGO (natif)        BLOC 7 — CATALOGUE
  auth_user                           categorie
  auth_group                          produit
  auth_user_groups                    mouvement_stock

BLOC 2 — PROFIL                     BLOC 8 — ARGENT
  profil_utilisateur                  wallet
                                      rechargement
BLOC 3 — ASSOS
  association                       BLOC 9 — TRANSACTIONS
                                      transaction
BLOC 4 — ADHÉSIONS                    ligne_transaction
  adhesion
                                    BLOC 10 — NOTIFICATIONS
BLOC 5 — IDENTIFICATION               notification
  moyen_identification
                                    BLOC 11 — AUDIT
BLOC 6 — ÉVÉNEMENTS                   audit_log
  evenement
```

---

## Bloc 1 - Auth Django (tables natives)

Ces tables sont créées automatiquement par Django avec `python manage.py migrate`.
On ne les écrit pas nous-mêmes, on les utilise.

### `auth_user`

Le compte de connexion. Tout le monde qui se connecte a une ligne ici.

| Champ | Rôle |
|---|---|
| `id` | numéro unique du compte, généré automatiquement. C'est l'identifiant stable de la personne |
| `username` | login de connexion, ce sera le login CAS de l'ENSEA |
| `first_name` | prénom |
| `last_name` | nom |
| `email` | adresse email |
| `password` | mot de passe haché par Django, jamais lisible en clair |
| `is_staff` | si `true`, la personne peut accéder à l'interface `/admin/` de Django |
| `is_active` | si `false`, le compte est désactivé (ex: étudiant parti) |
| `is_superuser` | si `true`, c'est le Super Admin technique (accès total) |
| `date_joined` | date de création du compte |
| `last_login` | date de dernière connexion |

### `auth_group`

Un groupe rassemble un ensemble de permissions. On nomme les groupes pour encoder le rôle
ET l'asso à la fois.

| Champ | Rôle |
|---|---|
| `id` | numéro unique du groupe |
| `name` | nom du groupe, ex: `vendeur_kfet`, `tresorier_bde`, `admin_asso_epicuria`, `admin_ade` |

### `auth_user_groups`

Table de liaison automatique entre utilisateurs et groupes.

| Champ | Rôle |
|---|---|
| `id` | numéro unique de la ligne |
| `user_id` | quel utilisateur |
| `group_id` | quel groupe |

Une personne dans plusieurs groupes = plusieurs lignes. Pierre trésorier BDE et vendeur
Kfet = deux lignes.

---

## Bloc 2 - Profil utilisateur

### `profil_utilisateur`

Django `auth_user` ne stocke que le strict nécessaire à la connexion. On ajoute le reste
ici, dans une table liée **1-pour-1** (une ligne profil par compte).

| Champ | Rôle |
|---|---|
| `id` | numéro unique du profil |
| `user_id` | lien vers le compte `auth_user` correspondant (1-pour-1) |
| `date_naissance` | date de naissance, utilisée pour calculer si la personne est mineure au moment d'un achat |
| `pseudonyme` | surnom affiché |
| `numero_isic` | numéro de la carte ISIC, stocké pour info mais jamais utilisé comme identifiant car réémis chaque année |
| `is_active` | `false` quand l'étudiant quitte l'ENSEA |
| `deleted_at` | `null` tant que le profil est vivant ; rempli avec la date d'anonymisation RGPD |

On ne stocke pas un booléen `est_mineur` car il deviendrait faux le jour de l'anniversaire.
On calcule l'âge à la volée depuis `date_naissance`.

---

## Bloc 3 - Associations

### `association`

| Champ | Rôle |
|---|---|
| `id` | numéro unique de l'asso |
| `nom` | nom complet affiché, ex: "Bureau Des Étudiants" |
| `slug` | version courte sans espaces ni accents, ex: `bde` (voir encadré ci-dessous) |
| `est_ade` | `true` pour la structure faîtière ADE |
| `is_active` | si l'asso est active |

> **C'est quoi un slug ?** Un slug est une version d'un nom pensée pour le code : minuscules,
> sans espaces, sans accents. "Bureau Des Étudiants" devient `bde`, "Épicuria" devient
> `epicuria`. On s'en sert pour nommer les groupes de façon automatique et sans faute :
> l'asso de slug `kfet` a les groupes `vendeur_kfet`, `tresorier_kfet`, `admin_asso_kfet`.
> Quand on ajoute une asso en 2027, on définit son slug et ses groupes en découlent.

---

## Bloc 4 - Adhésions

### `adhesion`

Attention à la différence entre **adhésion** (avoir payé sa cotisation, donne droit au tarif
réduit) et **rôle** (être vendeur ou trésorier, donne un accès). Ce sont deux choses séparées.

| Champ | Rôle |
|---|---|
| `id` | numéro unique de l'adhésion |
| `user_id` | qui est adhérent |
| `asso_id` | de quelle asso |
| `date_debut` | début de l'adhésion |
| `date_fin` | fin de l'adhésion ; `null` = en cours |
| `montant_paye` | combien payé, en centimes (10€ = 1000) |
| `is_active` | si l'adhésion est active |

Un étudiant peut être adhérent de plusieurs assos : une ligne par couple (utilisateur, asso).

---

## Bloc 5 - Moyen d'identification

### `moyen_identification`

Ce que la caisse utilise pour reconnaître l'étudiant : carte RFID ou QR code dynamique.

| Champ | Rôle |
|---|---|
| `id` | numéro unique du moyen |
| `user_id` | à qui il appartient |
| `type` | `RFID` ou `QR_CODE` |
| `valeur` | pour une carte RFID : l'UID de la puce (ex: `A3F2C891`). Pour un QR : `null`, car le QR est dynamique (généré à la volée, jamais stocké) |
| `actif_etudiant` | l'étudiant active/désactive lui-même ce moyen depuis son app |
| `actif_admin` | l'admin peut désactiver ce moyen ; l'étudiant le voit (ce n'est pas caché) |

**Un moyen fonctionne uniquement si `actif_etudiant = true` ET `actif_admin = true`.**
Les deux états sont indépendants : l'un vient de l'étudiant, l'autre de l'admin.

> **Le QR code est toujours dynamique.** Il n'y a pas de QR statique stocké en base. Quand
> l'étudiant ouvre son app, le serveur génère un token temporaire lié à son wallet, valable
> environ 10 minutes, qui n'est jamais enregistré durablement. La caisse le scanne, le
> serveur vérifie qu'il est valide et pas expiré. La ligne `QR_CODE` dans la table représente
> donc le **droit d'utiliser le QR dynamique**, pas un code figé. C'est le même principe
> qu'Izly.

> **Les deux états en pratique.** Dans son app, l'étudiant voit ses moyens avec leur état réel :
> ```
> Carte RFID    ●  Actif              [désactiver]
> QR Code       ○  Désactivé par l'administration
> ```
> S'il désactive un moyen lui-même, il est grisé et il peut le réactiver quand il veut. Si
> c'est l'admin qui a désactivé, c'est affiché clairement et l'étudiant ne peut pas le
> réactiver seul, mais il sait pourquoi ça ne marche pas. L'admin désactive en cas de
> problème (carte volée, compte compromis), sans jamais cacher l'information à l'étudiant.

> **Les nouveaux 1A en septembre.** Un 1A arrive sans carte RFID physique. Sa ligne RFID
> existe mais avec `actif_admin = false` tant que l'admin n'a pas enregistré sa vraie carte.
> En attendant, il paie avec le QR dynamique (qui, lui, est actif). Quand sa carte arrive,
> l'admin l'enregistre (remplit la `valeur` avec l'UID) et passe `actif_admin = true`. Pas
> de QR temporaire à gérer, c'est plus simple.

---

## Bloc 6 - Événements

### `evenement`

Un catalogue temporaire lié à une occasion (une soirée, un gala). Permet de créer des
produits spécifiques à l'événement (billets, consommations) et de regrouper ses ventes.

| Champ | Rôle |
|---|---|
| `id` | numéro unique de l'événement |
| `asso_id` | quelle asso l'organise |
| `nom` | nom de l'événement, ex: "Soirée Karaoké" |
| `date_event` | date de l'événement |
| `etat` | `OUVERT` (en vente), `FERME` ou `EPUISE` (caché aux vendeurs) |
| `is_active` | si l'événement existe encore |
| `created_at` | date de création |

> **Le scénario des deux soirées.** L'asso crée la Soirée 1 (`etat = OUVERT`). Les vendeurs
> jusqu'à l'admin asso peuvent vendre les places. Après la soirée, l'admin asso la passe en
> `FERME` ou `EPUISE` : les vendeurs ne la voient plus dans leur interface, mais l'admin
> asso continue de la voir (avec son état). Quand la Soirée 2 est créée (`OUVERT`), tout le
> monde la voit. Les ventes de la Soirée 1 restent consultables dans l'historique, taguées
> avec son `id`.

---

## Bloc 7 - Catalogue produits

### `categorie`

Regroupe les produits (Boissons, Snacks, Alcool…). Propre à chaque asso.

| Champ | Rôle |
|---|---|
| `id` | numéro unique de la catégorie |
| `asso_id` | quelle asso |
| `nom` | nom de la catégorie |
| `is_active` | si la catégorie est active |

### `produit`

| Champ | Rôle |
|---|---|
| `id` | numéro unique du produit |
| `asso_id` | à quelle asso appartient le produit |
| `categorie_id` | sa catégorie ; `null` si non catégorisé |
| `evenement_id` | `null` si produit du catalogue général ; rempli si produit spécifique à un événement |
| `nom` | nom affiché à la caisse |
| `description` | texte optionnel |
| `photo` | chemin vers l'image |
| `prix_non_adherent` | prix en centimes pour un non-adhérent |
| `prix_adherent` | prix en centimes pour un adhérent |
| `stock` | nombre d'unités disponibles |
| `seuil_alerte` | quand le stock passe en dessous, alerte au trésorier |
| `restriction_majeur` | `true` = alcool, vente bloquée pour un mineur |
| `is_active` | `false` = caché en caisse mais conservé dans l'historique |

### `mouvement_stock`

Chaque changement de stock laisse une trace ici, avec sa raison.

| Champ | Rôle |
|---|---|
| `id` | numéro unique du mouvement |
| `produit_id` | quel produit est concerné |
| `type` | `VENTE`, `REAPPRO`, `INVENTAIRE`, `CORRECTION` |
| `quantite` | de combien, signé : `-1` pour une vente, `+10` pour une réappro |
| `motif` | texte d'explication (surtout pour inventaire et correction) |
| `auteur_id` | qui a fait le mouvement |
| `created_at` | quand |

> **Pourquoi `mouvement_stock` est lié à `produit` par l'`id` ?** Chaque mouvement doit
> dire à quel produit il s'applique. On le relie par le numéro `id` du produit (c'est une
> clé étrangère, `produit_id`). C'est le principe d'une base de données relationnelle : on
> relie les tables par leurs identifiants numériques, jamais par les noms (qui peuvent
> changer ou se répéter). Pour avoir tous les mouvements de la canette Orangina (`id` 42),
> on cherche toutes les lignes où `produit_id = 42`. Le champ `stock` sur `produit` est un
> raccourci pratique (un cache) ; la vérité c'est la somme de tous ses mouvements.

---

## Bloc 8 — Wallet et rechargement

### `wallet`

Le porte-monnaie virtuel. Un seul par étudiant, partagé entre toutes les assos.

| Champ | Rôle |
|---|---|
| `id` | numéro unique du wallet |
| `user_id` | à qui il appartient (1-pour-1 avec `auth_user`) |
| `solde` | solde actuel en centimes |
| `is_active` | si le wallet est actif |
| `updated_at` | date de dernière modification |

### `rechargement`

Une ligne par recharge par carte bancaire.

| Champ | Rôle |
|---|---|
| `id` | numéro unique du rechargement |
| `wallet_id` | quel wallet est rechargé |
| `montant` | combien en centimes (minimum 2000 = 20€) |
| `etat` | `INITIE`, `CONFIRME`, `ECHEC`, `REMBOURSE` |
| `psp` | prestataire de paiement, Stripe ici |
| `psp_session_id` | identifiant de la session côté Stripe |
| `psp_event_id` | identifiant de l'événement de confirmation, unique pour empêcher le double crédit |
| `created_at` | date d'initiation |
| `confirmed_at` | date de confirmation par Stripe ; `null` si pas encore confirmé |

---

## Bloc 9 — Transactions

### `transaction`

Panier et transaction fusionnés en une seule table. Un panier en cours est une transaction
à l'état `OUVERT` ; un panier abandonné est une transaction `ANNULEE`.

| Champ | Rôle |
|---|---|
| `id` | numéro unique de la transaction |
| `uuid_client` | identifiant généré par la caisse, sert à éviter les doublons en cas de hors-ligne |
| `asso_id` | dans quelle asso a eu lieu la vente |
| `evenement_id` | `null` si vente du catalogue général ; rempli si vente liée à un événement |
| `vendeur_id` | qui a encaissé |
| `acheteur_id` | qui a payé ; `null` si espèces anonymes |
| `wallet_id` | quel wallet a été débité ; `null` si pas de paiement wallet |
| `mode_paiement` | `WALLET`, `ESPECES`, `TERMINAL_EXTERNE` |
| `etat` | avancement de la transaction (voir ci-dessous) |
| `montant_total` | total en centimes, calculé depuis les lignes |
| `nom_caisse` | texte identifiant la caisse, ex: "Caisse principale Kfet" |
| `est_hors_ligne` | si la transaction a été créée sans réseau |
| `created_at` | quand le panier a été ouvert |
| `validated_at` | quand le paiement a été validé ; `null` tant que pas `VALIDEE` |

Les états :
```
OUVERT     → le vendeur ajoute des articles (= panier en cours)
EN_ATTENTE → mode de paiement choisi, on attend la confirmation
CONFIRME   → paiement reçu
VALIDEE    → terminé : stock consommé, wallet débité, ticket dispo
ANNULEE    → abandon : stock libéré, rien débité
ERREUR     → problème (solde insuffisant, réseau)
```

### `ligne_transaction`

Chaque article de la transaction.

| Champ | Rôle |
|---|---|
| `id` | numéro unique de la ligne |
| `transaction_id` | à quelle transaction elle appartient |
| `produit_id` | quel produit ; `null` si produit libre |
| `libelle` | copie du nom du produit au moment de la vente |
| `prix_applique` | copie du prix en centimes au moment de la vente |
| `quantite` | nombre d'unités |
| `tarif_type` | `ADHERENT`, `NON_ADHERENT` ou `LIBRE` |

> **Pourquoi copier le nom et le prix ?** Si demain le trésorier change le prix d'une canette
> de 1,50€ à 1,80€ et la renomme, l'historique de juin doit toujours montrer "Canette à
> 1,50€" — la vérité du moment de la vente. La copie garantit que l'historique ne change
> jamais, même si le produit évolue.

---

## Bloc 10 — Notifications

### `notification`

Chaque message envoyé à un étudiant.

| Champ | Rôle |
|---|---|
| `id` | numéro unique de la notification |
| `user_id` | destinataire |
| `type` | `RECHARGEMENT`, `PAIEMENT`, `STOCK_BAS` |
| `canal` | `EMAIL` ou `PUSH` |
| `contenu` | texte du message |
| `etat` | `EN_ATTENTE`, `ENVOYEE`, `ECHEC` (permet de réessayer après un hors-ligne) |
| `created_at` | quand elle a été créée |
| `sent_at` | quand elle a été envoyée ; `null` tant que pas envoyée |

---

## Bloc 11 — Audit log

### `audit_log`

La boîte noire. Toute action sensible laisse une trace, jamais effacée.

| Champ | Rôle |
|---|---|
| `id` | numéro unique de l'entrée |
| `acteur_id` | qui a fait l'action |
| `asso_id` | dans quelle asso ; `null` si action globale |
| `action` | `EXPORT_ADHERENTS`, `PRIX_MODIFIE`, `ROLE_ACCORDE`, `VIREMENT_VALIDE`, `ANONYMISATION`… |
| `details` | JSON avec le contexte (ancien prix, nouveau prix, nombre de lignes exportées…) |
| `created_at` | quand |

---

## La hiérarchie des rôles

Du plus haut au plus bas, avec ce que chacun voit et peut faire.

### Super Admin (`is_superuser = true`)

Niveau technique, au-dessus de tout. Maintenance Django, configuration, création des comptes.
Il peut voir **qui est admin asso, vendeur, trésorier** dans chaque asso (la structure des
accès). Il **ne voit pas les ventes détaillées** de chaque asso (ça ne le concerne pas).
Il distribue les codes d'accès. **Pas d'encaissement** (rattaché à aucune asso). Fait un peu
de maintenance technique.

### Admin ADE (groupe `admin_ade`)

Niveau financier global. Il voit **les totaux générés par chaque asso** (la Kfet a fait
1500€ cette semaine) pour organiser les **reversements**. Il **ne voit pas le détail des
produits vendus** ni les transactions individuelles : seulement les montants agrégés par
asso. Il valide les virements. Il fait le lien entre les assos et la banque.

### Admin Asso (groupe `admin_asso_{slug}`)

Niveau gestion d'une asso. Il voit et gère **tout ce qui concerne son asso** : adhérents
(liste nominative), produits, prix, stocks, ventes, événements, vendeurs. Il peut **gérer
les rôles de son asso** (ajouter/retirer un vendeur ou trésorier de ses groupes), via une
vue custom de l'application, **uniquement pour son asso**. Il exporte la liste nominative
de ses adhérents (action tracée dans l'audit).

### Trésorier Asso (groupe `tresorier_{slug}`)

Finances de l'asso : CA, ventes par produit, stocks, transactions **anonymisées** (sans les
noms). Gère les prix et les produits. Exporte les données comptables.

### Vendeur (groupe `vendeur_{slug}`)

Encaisse. Voit les produits avec leurs prix pour faire payer. Accès au paiement libre. Peut
rechercher un étudiant par son nom (utile pour appliquer le bon tarif en espèces).

> **Note importante** : la frontière Admin ADE / Super Admin tient à la **finalité**. L'ADE
> gère l'argent (combien reverser à qui) mais pas la technique ni le détail produit. Le
> Super Admin gère la technique et les accès mais pas l'argent. Aucun des deux n'encaisse,
> aucun des deux ne fouille le détail des ventes d'une asso.

### Vérifier les rôles dans le code

```python
# Vendeur à la Kfet ?
user.groups.filter(name='vendeur_kfet').exists()

# Admin d'une asso quelconque ?
user.groups.filter(name__startswith='admin_asso_').exists()

# Retrouver le slug de l'asso d'un vendeur
g = user.groups.filter(name__startswith='vendeur_').first()
slug = g.name.replace('vendeur_', '')  # → 'kfet'
```

---

## RGPD : conservation et anonymisation

C'est un point clé pour faire approuver le projet. La logique repose sur une distinction.

**Deux finalités différentes, deux durées différentes :**

- La **donnée comptable** (il y a eu une vente, telle date, tel montant, tel produit) doit
  être conservée **10 ans** par obligation légale. Elle n'a pas besoin du nom de l'acheteur
  pour être valable.
- La **donnée personnelle** (le lien entre une vente et l'identité réelle) relève du RGPD et
  doit pouvoir être **effacée**.

**Le cycle de vie d'un étudiant :**

1. **Pendant sa scolarité** : données complètes, tout fonctionne normalement.
2. **Il quitte l'ENSEA** : `is_active = false` sur le profil et le compte. Il disparaît des
   interfaces. Ses transactions restent (avec son `user_id`).
3. **Un an après son départ** (ou sur demande de droit à l'effacement) : **anonymisation**.
   On écrase définitivement `nom`, `prenom`, `email`, `date_naissance`, `pseudonyme`,
   `numero_isic` par des valeurs neutres ("Anonyme", "anonyme@supprime.fr"). On efface la
   `valeur` des moyens d'identification (l'UID RFID est une donnée personnelle). On remplit
   `deleted_at`. L'action est tracée dans `audit_log`.

**Après anonymisation, les transactions deviennent de simples lignes comptables anonymes.**

**Question : un étudiant anonymisé peut-il réclamer son historique d'achats d'il y a 5 ans ?**

Non, et c'est légal. Le droit d'accès RGPD s'applique tant qu'on détient des données
**identifiantes**. Une fois la donnée vraiment anonymisée — c'est-à-dire qu'il n'existe plus
aucun moyen de relier une transaction à la personne — **ce ne sont juridiquement plus des
données personnelles**, et le RGPD ne s'y applique plus. L'étudiant ne peut donc pas exiger
son historique, car il n'existe plus de moyen de prouver que telle transaction était la
sienne.

C'est la différence entre :
- **Anonymisation** (notre choix) : irréversible, on ne peut plus jamais relier. La donnée
  sort du RGPD. Définitif.
- **Pseudonymisation** : on remplace le nom par un code mais on garde une table de
  correspondance. Le lien existe encore, donc le RGPD continue de s'appliquer.

**Point de vigilance à documenter pour la CNIL** : pour que ce soit une vraie anonymisation,
il faut qu'on ne puisse pas ré-identifier la personne par recoupement (ex: une seule
transaction à une heure très précise avec un seul vendeur de permanence). Pour une cafét
avec des centaines de transactions, le risque est négligeable, mais le mentionner dans
l'analyse de conformité montre le sérieux de la démarche.

---

## Exemple complet : une vente du début à la fin

Pour comprendre comment les tables s'articulent, suivons une vente réelle.

**Le contexte.** Marie (`auth_user` id=7) est vendeuse à la Kfet. Elle est dans le groupe
`vendeur_kfet`. Paul (`auth_user` id=42) est étudiant adhérent de la Kfet, il a un wallet
avec 5€ dessus.

**Les données de départ :**

```
auth_user        : id=42, username="paudupXX", first_name="Paul", last_name="Dupont"
profil_utilisateur: user_id=42, date_naissance=2005-03-12 (donc majeur)
adhesion         : user_id=42, asso_id=1 (Kfet), is_active=true → Paul est adhérent Kfet
wallet           : user_id=42, solde=500 (5,00€)
moyen_identification: user_id=42, type=RFID, valeur="A3F2C891", actif_etudiant=true, actif_admin=true
produit          : id=10, asso_id=1, nom="Café", prix_adherent=80, prix_non_adherent=100, stock=50
```

**Étape 1 — Marie ouvre une vente.** Une transaction est créée :

```
transaction: id=1001, uuid_client="abc-123", asso_id=1, vendeur_id=7,
             etat="OUVERT", nom_caisse="Caisse Kfet", created_at=14:30
```

**Étape 2 — Marie ajoute un café.** Une ligne est créée. Le stock du café est réservé
(il passe visuellement de 50 à 49) mais aucun `mouvement_stock` définitif n'est encore écrit :

```
ligne_transaction: id=1, transaction_id=1001, produit_id=10, quantite=1
```

**Étape 3 — Paul scanne sa carte RFID.** La caisse lit `A3F2C891`, cherche dans
`moyen_identification`, trouve `user_id=42`. Le serveur vérifie dans `adhesion` que Paul est
adhérent Kfet → tarif adhérent. Le café est donc à 80 centimes. La transaction se complète :

```
transaction: ...acheteur_id=42, wallet_id=(celui de Paul), mode_paiement="WALLET",
             etat="EN_ATTENTE", montant_total=80
ligne_transaction: ...libelle="Café", prix_applique=80, tarif_type="ADHERENT"
```

Note : `libelle` et `prix_applique` sont **copiés** maintenant. Même si le café change de
nom ou de prix demain, cette ligne restera "Café à 80 centimes".

**Étape 4 — Validation.** Paul a 500 centimes, le café coûte 80. Tout se passe **en même
temps, ou rien** :

```
wallet           : solde passe de 500 à 420
mouvement_stock  : produit_id=10, type="VENTE", quantite=-1, auteur_id=7 (maintenant écrit)
transaction      : etat="VALIDEE", validated_at=14:31
notification     : user_id=42, type="PAIEMENT", canal="PUSH", contenu="Paiement de 0,80€ à la Kfet"
```

Si le serveur avait planté entre le débit du wallet et l'écriture du stock, Django aurait
**tout annulé** : le solde serait resté à 500. On ne peut pas avoir un wallet débité sans
vente enregistrée.

**Et si Paul avait annulé avant de payer ?** La transaction serait passée à `ANNULEE`, la
réservation de stock libérée (le café revient à 50), et le wallet **jamais touché**. Le stock
réel n'est consommé qu'à la validation finale.

**Ce qu'on peut faire ensuite avec ces données :**

- Le **trésorier Kfet** voit "1 café vendu à 0,80€ à 14h31" — sans le nom de Paul.
- L'**admin asso Kfet** voit la même vente et peut relier à Paul s'il consulte l'annuaire.
- L'**admin ADE** voit juste "Kfet : +0,80€" dans le total de la semaine.
- Paul voit dans son app "Café 0,80€ — solde restant 4,20€".

---

## Ce qui reste pour plus tard (V2)

| Élément | Pourquoi reporté |
|---|---|
| `RegleAdhesion` (tarifs croisés entre assos) | codé en dur en V1, table dédiée en 2027 |
| Journal détaillé du wallet | le solde sur `wallet` suffit en V1 |
| Exports planifiés automatiques | export manuel suffisant au lancement |
| Prêts de matériel | réutilisera `mouvement_stock` avec de nouveaux types |
| Badges et récompenses | s'abonnera aux événements de transaction |
