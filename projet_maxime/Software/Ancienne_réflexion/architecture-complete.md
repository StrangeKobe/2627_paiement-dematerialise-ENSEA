# Architecture complète - Plateforme de paiement dématérialisé ENSEA

> Document de conception V1. Approche « avocat du diable » : pour chaque choix, on
> expose le problème, on compare les scénarios, on recommande pour la V1 et on liste
> les points de vigilance.
>
> **Périmètre V1** : assos pilotes Kfet, BDE, Epicuria (sous l'ADE).  
> **Cible 2027** : extension à toutes les assos, modules avancés ajoutés sans refonte.

---

## Sommaire

1. [Principes directeurs](#0-principes-directeurs)
2. [Authentification et gestion des rôles](#1-authentification-et-gestion-des-rôles)
3. [Étudiants et identité](#2-étudiants-et-identité)
4. [Catalogue produits et tarification](#3-catalogue-produits-et-tarification)
5. [Flux de paiement et encaissement](#4-flux-de-paiement-et-encaissement)
6. [Back-office trésorier et exports](#5-back-office-trésorier-et-exports)
7. [Évolutivité V1 → V2](#6-évolutivité-v1--v2)
8. [Schéma BDD](#7-schéma-bdd) → voir aussi `schema-bdd.dbml`

---

## 0. Principes directeurs

Quelques décisions transverses qui conditionnent tout le reste.

- **Jamais de suppression physique.** Tout modèle métier porte `is_active` (+ `deleted_at`
  nullable si on veut tracer la date). On masque, on archive, on n'efface pas. Les
  historiques de transactions doivent rester lisibles même quand un produit ou un élève
  est désactivé → on duplique au moment de la vente les champs critiques (nom produit,
  prix appliqué) dans la `LigneTransaction` (voir §3 et §4).
- **L'argent est sacré.** Toute écriture touchant un solde passe par une transaction de
  base de données atomique avec verrou de ligne (`select_for_update`). Aucune logique
  monétaire ne vit hors d'une transaction DB. On ne stocke jamais d'euros en `float` :
  centimes en entier (`BigIntegerField`) ou `DecimalField(max_digits, decimal_places=2)`.
- **Cloisonnement par asso dès le départ.** Même en V1 à 3 assos, on filtre toutes les
  données par association. C'est ce qui permet l'extension 2027 sans réécriture.
- **Le RGPD se conçoit, il ne se rajoute pas.** La séparation « qui voit quel nom » est
  une contrainte d'architecture, pas une option d'affichage (voir §2).
- **Modules = apps Django.** Le cœur (auth, wallet, transaction) est stable. Stock avancé,
  prêts, badges, stats arrivent comme apps indépendantes branchées par signaux/clés
  étrangères, jamais par modification du cœur (voir §6).

---

## 1. Authentification et gestion des rôles

### 1.1 Intégration du SSO ENSEA

**Problème.** L'école a un SSO intranet. On veut éviter de gérer des mots de passe nous-mêmes
(surface d'attaque, support, RGPD). Mais on ne connaît pas encore la techno exacte exposée
par la DSI (CAS ? LDAP ? un IdP OAuth2/OIDC ?).

**Scénarios.**

| Option | Avantages | Inconvénients |
|---|---|---|
| **CAS** (`django-cas-ng`) | Standard universitaire, très répandu en France, SSO web propre | Web only ; mal adapté à une app mobile / à une caisse ; pas de notion de scope moderne |
| **LDAP direct** (`django-auth-ldap`) | Simple si annuaire AD/OpenLDAP dispo | On manipule les credentials → on devient responsable de leur transit ; pas de vrai SSO (re-saisie) ; couplage fort à l'annuaire |
| **OAuth2 / OIDC** (`mozilla-django-oidc`) | Standard moderne, tokens, marche pour web **et** mobile, scopes/claims | Nécessite que la DSI expose un IdP OIDC (pas garanti) |

**Recommandation V1.** Cibler **OIDC** si la DSI peut l'exposer, sinon **CAS**. Quelle que
soit la techno, **on ne couple pas le code métier au protocole** : on isole l'auth derrière
une couche d'abstraction.

- Un `AUTHENTICATION_BACKEND` custom qui, après validation SSO, fait du *just-in-time
  provisioning* : à la première connexion, on crée l'`Utilisateur` local à partir des claims
  (numéro étudiant, nom, prénom, mail). Les connexions suivantes mettent à jour.
- On garde un `User` Django local : il porte les rôles, le wallet, les FK. Le SSO ne fait
  qu'**authentifier** (« qui es-tu »), notre base fait l'**autorisation** (« qu'as-tu le
  droit de faire »).

**Points de vigilance.**

- **Quel identifiant pivot ?** Le mail change, le nom change, le numéro ISIC est
  réémis chaque année. Il faut demander à la DSI **un identifiant interne stable et opaque**
  (ex. un `eduPersonUniqueId` / `uid` annuaire) et le stocker dans `Utilisateur.sso_id`. Ne
  **jamais** utiliser le numéro ISIC comme clé d'identité (voir §2).
- **Comptes hors-école.** Intervenants, anciens, partenaires : prévoir dès la V1 un
  *fallback* de comptes locaux (mot de passe géré par nous) pour les non-SSO, même si on les
  désactive par défaut. Sinon on se retrouve bloqué le jour d'un événement avec des externes.
- **La caisse n'a pas de SSO interactif.** Une caisse Raspberry est un poste partagé : ce
  n'est pas « un utilisateur » mais « un poste de vente » authentifié par un secret machine
  (voir 1.3). Ne pas mélanger session SSO d'un humain et identité de la caisse.

### 1.2 Modèle de rôles multi-assos

**Problème.** Un même humain peut être Permanencier au BDE, Trésorier à Epicuria et simple
étudiant à la Kfet. Un modèle de rôle global (un seul rôle par user) est donc faux par nature.

**Scénario rejeté.** `User.role = CharField(choices=...)` → impossible de porter plusieurs
contextes ; casse à la première personne bi-asso.

**Recommandation V1 — table de liaison ternaire.**

```
Membership (Utilisateur × Association × Role)
  - utilisateur  FK
  - association  FK   (null = rôle global, ex. Super Admin / Admin ADE)
  - role         FK ou choices
  - is_active
  - granted_by   FK Utilisateur  (qui a donné ce rôle → audit)
  - granted_at
  - unique_together (utilisateur, association, role)
```

Rôles (du plus large au plus restreint) :

| Rôle | Portée | Peut |
|---|---|---|
| **Super Admin** | global (technique) | tout, maintenance, gère les comptes Admin ADE |
| **Admin ADE** | global métier | crée les assos, crée les Admin Asso, voit tous les pôles |
| **Admin Asso** | une asso | gère son asso, crée ses vendeurs, **voit ses adhérents et exporte leur liste** (cf. §2.4) |
| **Trésorier Asso** | une asso | finances, prix, produits, exports comptables — **sans voir les noms sur les transactions** |
| **Permanencier / Vendeur** | une asso | encaisse, voit le nom au scan uniquement pour vérif physique |
| **Étudiant** | soi-même | recharge, paie, consulte son historique |

> **Note** : Admin Asso et Trésorier ont des visibilités **complémentaires et asymétriques**.
> L'Admin connaît l'annuaire des membres (noms) mais pas forcément le détail comptable ; le
> Trésorier voit le CA et les transactions anonymisées. Ce n'est pas une hiérarchie linéaire,
> c'est une séparation des pouvoirs (voir §2.3 RGPD).

**Choix de contexte à la connexion.** Après login, si l'utilisateur a des rôles dans
plusieurs assos, on lui présente un **sélecteur de contexte** (« Vous vous connectez en tant
que : Trésorier BDE / Vendeur Kfet / … »). Le contexte choisi est stocké en session
(`request.session['active_membership_id']`) et **toute la couche de permission s'appuie
dessus**. Un middleware résout le `Membership` actif et l'attache à `request`.

**Points de vigilance.**

- **Escalade de privilèges.** Un Admin Asso ne doit jamais pouvoir se créer un rôle ADE, ni
  créer un vendeur dans une autre asso. Règle : on ne peut accorder qu'un rôle **strictement
  inférieur ou égal** au sien, et **uniquement dans le périmètre de son `active_membership`**.
  À coder dans une fonction `can_grant(granter_membership, target_role, target_asso)` testée
  unitairement — c'est le genre de faille qui passe en revue de code.
- **Cohérence du contexte.** Si le rôle actif est révoqué pendant la session, le middleware
  doit invalider le contexte au prochain hit, pas attendre l'expiration de session.

### 1.3 Clé d'accès secondaire (second facteur métier)

**Problème.** Un identifiant intranet peut fuiter (post-it, épaule, phishing interne). Pour les
actions sensibles (ouvrir une caisse, valider un virement de répartition, modifier des prix en
masse, exporter des données nominatives), le SSO seul ne suffit pas.

**Scénarios.**

| Option | Avantages | Inconvénients |
|---|---|---|
| **TOTP** (app type Authy/Google Auth) | standard, gratuit, offline | enrôlement à gérer, perte de device |
| **PIN d'asso** (code partagé par équipe de perm) | simple, adapté à un poste partagé | secret partagé = faible, à roter souvent |
| **Clé matérielle / carte admin** | fort | coût, logistique |

**Recommandation V1 — deux niveaux.**

1. **Caisse / poste de vente** : authentifiée par un **secret de poste** (token long stocké
   sur le Raspberry, jamais affiché) + un **PIN d'ouverture de session de perm** saisi par le
   permanencier au début de son service. Le PIN identifie *qui tient la caisse* sans SSO
   interactif. Rotation du secret de poste possible depuis le back-office.
2. **Actions sensibles back-office** (virements, exports nominatifs, gestion de rôles) :
   **TOTP** obligatoire en plus du SSO pour Admin ADE / Admin Asso / Trésorier.

**Points de vigilance.**

- Le secret de poste ne doit **jamais** transiter en clair ni être visible dans une réponse
  d'API. Stockage chiffré côté serveur (hash), affichage unique à la génération.
- Prévoir une **révocation immédiate** d'un poste compromis (Raspberry volé) → liste de
  révocation vérifiée à chaque requête de caisse.

### 1.4 Délégation de création de comptes

Chaîne de création, en miroir de la hiérarchie :

```
Super Admin ──crée──▶ Admin ADE ──crée──▶ Admin Asso ──crée──▶ Vendeur/Trésorier (de SON asso)
```

- Chaque création écrit `granted_by` et `granted_at` → **piste d'audit** complète.
- Un Admin Asso invite un vendeur **par son identité SSO** (numéro étudiant), pas par mail
  libre : on s'assure que la personne existe dans l'annuaire avant de lui donner un pouvoir.
- Garde-fou : `can_grant()` (cf. 1.2) appelé systématiquement côté serveur, jamais une
  vérification seulement côté front.

---

## 2. Étudiants et identité

### 2.1 Données stockées par étudiant

Champs : `nom`, `prenom`, `pseudonyme`, `numero_isic`, `date_naissance` (→ détection mineur),
`sso_id` (pivot stable), `email`. Le statut adhérent et le solde **ne vivent pas** sur
l'étudiant : ils sont portés par `Adhesion` (par asso) et `Wallet` (unique). Raison : un
étudiant a **une** identité mais **plusieurs** adhésions et **un** wallet partagé entre assos.

> **Détection mineur** : calculée à la volée depuis `date_naissance`, jamais stockée comme
> booléen figé (sinon faux le jour de l'anniversaire). Sert à bloquer la vente d'alcool —
> à matérialiser comme un flag `restriction_majeur` sur le `Produit` (voir §3).

### 2.2 Nouveaux arrivants sans carte ISIC (septembre)

**Problème.** En septembre, les 1A n'ont pas encore leur carte ISIC RFID. Il faut quand même
qu'ils puissent payer dès la première soirée d'intégration.

**Scénarios.**

| Option | Avantages | Inconvénients |
|---|---|---|
| **QR code temporaire** généré par l'admin | immédiat, pas de matériel, imprimable/affichable sur le tel | à révoquer quand la vraie carte arrive |
| **Numéro étudiant provisoire** de la scolarité | identité officielle | dépend du calendrier de la scolarité, souvent en retard |
| **Pré-import annuaire** SSO | dès que la DSI fournit la liste, le compte existe | la carte physique RFID manque toujours |

**Recommandation V1 — découpler identité et support.** L'identité (compte `Utilisateur`)
vient du SSO/pré-import dès que possible. Le **moyen de paiement** est un objet séparé
`MoyenIdentification` (carte RFID **ou** QR code), avec un type et un statut. Un étudiant
peut avoir :

- un QR code temporaire actif en septembre (généré par l'admin, affichable dans l'app),
- puis sa carte RFID rattachée quand elle arrive, le QR restant en secours.

Ainsi on n'attend pas la carte pour ouvrir le wallet, et on gère proprement la transition.

**Points de vigilance.** Un QR code temporaire doit avoir une **date d'expiration** et être
**révocable**. Ne jamais réémettre deux fois le même QR pour deux personnes.

### 2.3 Fraude à la carte / au QR code

**Problème.** Rien n'empêche physiquement A de présenter la carte/QR de B. Le wallet de B
serait débité. Quel niveau de friction accepte-t-on au comptoir (file d'attente d'une soirée) ?

**Scénarios.**

| Mécanisme | Sécurité | Friction | Faille |
|---|---|---|---|
| **PIN à la caisse** | moyenne | forte (taper un code à chaque conso, file qui bloque) | observation du PIN, PIN partagé/oublié |
| **Biométrie** | forte | très forte | hors budget, RGPD lourd (donnée sensible), pas sur carte RFID |
| **Confirmation sur l'app du propriétaire** (push « Valider 3,50 € à la Kfet ? ») | forte | moyenne (dépend du réseau/tel chargé) | tel déchargé, pas de réseau, latence en soirée |
| **Photo affichée à la validation** | faible-moyenne | faible (le perm compare visage/écran) | dépend de la vigilance du perm, RGPD (photo) |
| **Nom affiché au scan** (le perm lit « Dupont » et vérifie) | faible | très faible | le perm ne connaît pas tout le monde |

**Recommandation V1 — défense en profondeur, pas une solution miracle.**

- **Par défaut** : affichage du **nom + prénom** au scan, pour vérification visuelle rapide
  par le permanencier (faille assumée mais friction quasi nulle, adaptée à une soirée).
- **Au-dessus d'un seuil** (ex. paiement > 15 €, ou rechargement) : **confirmation push sur
  l'app du propriétaire** obligatoire. Le coût d'une fraude devient borné.
- **Option activable par asso** : PIN à 4 chiffres pour les assos qui veulent plus de
  sécurité, désactivé par défaut pour la fluidité.
- **Garde-fou universel** : **plafond de dépense** et **détection d'anomalie** (15
  transactions en 2 min sur la même carte → alerte). Une carte volée a un impact plafonné.

> On documente explicitement que **le risque zéro n'existe pas** sur un paiement de comptoir
> rapide. L'objectif est de **borner la perte** et de **tracer** pour litige, pas de l'éliminer.

**Points de vigilance.** La photo (option) est une donnée personnelle → base légale, durée de
conservation, accès restreint. La biométrie est écartée pour la V1 (donnée sensible RGPD,
art. 9, + coût).

### 2.4 RGPD — qui voit quel nom

**Problème.** Concilier vérification au comptoir (besoin du nom) et minimisation des données
(le trésorier n'a pas à connaître qui a acheté quoi).

**Règles de visibilité (à implémenter comme permissions, pas comme affichage).**

| Rôle | Voit le nom ? | Voit les transactions ? | Détail |
|---|---|---|---|
| **Permanencier** | **oui, au moment du scan uniquement** | celles qu'il encaisse, en cours | après validation, plus d'accès au lien nom↔transaction |
| **Trésorier Asso** | **non** | oui, **anonymisées** (ID interne) | CA, ventes/produit, montants — jamais l'identité |
| **Admin Asso** | **oui** (annuaire des adhérents) | non (pas le détail comptable) | gère ses membres, **exporte la liste nominative** (cf. ajout) |
| **Admin ADE** | oui (tous pôles) | oui | supervision globale |
| **Étudiant** | son propre nom | ses propres transactions | — |

**Implémentation en BDD/Django.**

- La `Transaction` référence l'étudiant par **FK vers `Wallet`/`Utilisateur`**, mais la
  **couche d'accès trésorier ne SELECT jamais les colonnes nominatives** : on expose au
  trésorier une **vue/serializer restreint** qui ne contient que `utilisateur_id` interne
  opaque, montants, produits, horodatage. Le nom n'est jamais dans la réponse API trésorier.
- Le **permanencier** obtient le nom via un endpoint dédié `scan → renvoie nom+prénom+photo`
  **uniquement pendant la fenêtre de paiement** (le panier ouvert). Une fois la transaction
  validée, l'app caisse n'a plus de route pour re-résoudre l'identité d'une transaction passée.
- On s'appuie sur les **permissions Django par rôle** + un **filtrage systématique par
  `active_membership`** (un trésorier BDE ne voit que les transactions BDE). Pour la robustesse,
  on peut doubler d'un filtrage applicatif via un `Manager`/`QuerySet` custom
  (`Transaction.objects.for_membership(m)`).

> **Row-level security PostgreSQL vs filtrage Django** : voir §5.1. En V1 on privilégie le
> filtrage Django (plus simple, testable), en gardant la RLS comme renfort possible en V2.

### 2.5 Ajout — Annuaire des adhérents et export pour les Admins Asso

**Besoin (ajouté).** Les Admins Asso doivent **connaître leurs adhérents** et pouvoir
**exporter un Excel avec les noms**.

**Recommandation.**

- L'Admin Asso dispose d'un **annuaire** : liste des `Adhesion` actives de son asso, jointe
  à `Utilisateur` → nom, prénom, pseudo, statut adhérent, date d'adhésion. **Pas de solde,
  pas de détail de transactions** (ça reste séparé du rôle Admin) — sauf décision contraire
  à acter.
- **Export Excel nominatif** : bouton + génération `.xlsx` (openpyxl). Comme c'est une
  donnée nominative, l'export est une **action sensible** → protégée par TOTP (cf. 1.3),
  **journalisée** (qui a exporté, quand, combien de lignes) dans un `AuditLog`.
- Distinction nette avec le trésorier : **Admin = identité des membres** ;
  **Trésorier = argent anonymisé**. Si une même personne cumule les deux rôles, elle bascule
  de contexte (cf. 1.2) et ce sont deux vues distinctes — le cloisonnement reste au niveau
  des données, pas de la personne.

**Point de vigilance RGPD.** L'export nominatif doit avoir une **finalité claire**
(gestion associative), une **durée de conservation** et idéalement un **filigrane**
(« exporté par X le … ») pour responsabiliser. À mentionner dans le registre des traitements.

### 2.6 Adhésions multiples et tarifs croisés

**Problème.** Une adhésion BDE peut ouvrir un tarif réduit à la Kfet ; une asso a sa propre
adhésion ; des collaborations ponctuelles créent des réductions temporaires.

**Recommandation — modéliser la règle, pas le cas particulier.**

- `Adhesion` : `(utilisateur, association, is_active, date_debut, date_fin, montant_paye)`.
  Une ligne par adhésion réelle.
- `RegleAdhesion` : exprime « être adhérent de l'asso **source** donne le bénéfice **X** à
  l'asso **cible** ». Champs : `asso_source`, `asso_cible`, `type_benefice`
  (`TARIF_ADHERENT` | `REDUCTION_POURCENT` | `REDUCTION_FIXE`), `valeur`, `date_debut`,
  `date_fin` (null = permanent), `is_active`.
  - Adhésion propre : `asso_source == asso_cible`.
  - Tarif croisé BDE→Kfet : `asso_source=BDE, asso_cible=Kfet, type=TARIF_ADHERENT`.
  - Collaboration ponctuelle : même structure avec `date_debut/date_fin` bornées.

**Résolution du tarif** (au paiement) : pour un produit de l'asso C et un étudiant U, on
cherche s'il existe une `RegleAdhesion` active vers C dont l'étudiant remplit la condition
(adhérent de la source). Le **meilleur bénéfice applicable** gagne (à définir : on prend la
réduction la plus avantageuse pour l'étudiant). Fonction pure `resoudre_tarif(produit, user,
date)` testable unitairement.

**Points de vigilance.** Cumul des réductions → décider explicitement **non cumulables** en
V1 (on garde la meilleure), sinon on ouvre la porte aux prix négatifs. Toujours borner :
`prix_final = max(0, ...)`.

---

## 3. Catalogue produits et tarification

### 3.1 Modèle Produit

Champs : `nom`, `description`, `photo`, `prix_non_adherent`, `prix_adherent`, `stock`,
`seuil_alerte`, `is_active`, `association` (propriétaire), `restriction_majeur` (bool, ex.
alcool), `categorie` (FK optionnelle). Chaque asso gère **son** catalogue → tout produit est
rattaché à une `association`, et le cloisonnement (§5.1) s'applique.

> Les prix sont en **centimes entiers** ou `Decimal(.,2)`. Jamais de `float`.

### 3.2 Application automatique du bon tarif

- **Paiement wallet (QR/RFID)** : le serveur connaît l'identité → il appelle
  `resoudre_tarif(produit, user, now)` (§2.6) et applique le tarif adhérent/croisé
  automatiquement. L'étudiant ne peut pas tricher : c'est le serveur qui tranche.
- **Espèces** : pas d'identité scannée. Le vendeur choisit sur l'écran « adhérent /
  non-adhérent » → l'app applique le prix correspondant. La responsabilité est humaine
  (le perm vérifie la carte). On **journalise** le choix pour cohérence comptable.

### 3.3 Produit libre (montant libre)

**Problème.** Un produit non référencé, un bug catalogue, une vente exceptionnelle ne doivent
**jamais bloquer une vente** en soirée.

**Recommandation.** Une `LigneTransaction` peut référencer **soit** un `Produit`, **soit** être
un **produit libre** (`produit = null`, `libelle_libre`, `montant_libre`). Réservé aux rôles
vendeur+ et **journalisé** (un produit libre est une anomalie comptable potentielle → on veut
pouvoir auditer combien de ventes libres, par qui). Pas de décrément de stock (pas de produit).

### 3.4 Gestion des stocks

- **Décrémentation à la vente** : dans la **même transaction atomique** que le paiement,
  avec `select_for_update` sur la ligne produit. Pas de décrément si paiement échoue.
- **Alerte stock bas** : `stock <= seuil_alerte` → signal → notification au trésorier/admin
  asso. Seuils **définis par asso** (chaque asso sa logique).
- **Inventaire** : le trésorier peut poser un stock absolu (correction d'inventaire), tracé
  dans un `MouvementStock` (`type`, `quantite`, `motif`, `auteur`, `date`) — on **n'écrase pas**
  le stock en silence, on enregistre le mouvement. C'est ce qui permettra les modules avancés
  2027 (prêts de matériel = mouvements typés) **sans toucher au cœur** (§6).

### 3.5 Conflits de panier (concurrence sur le dernier article)

**Problème.** Deux caisses ajoutent le dernier exemplaire en même temps → survente.

**Recommandation V1 — réservation avec expiration.**

- Ajouter au panier = créer une **réservation** de stock (le stock « disponible » =
  `stock - réservé`). La réservation a une **expiration à 5 min** (panier abandonné libéré
  automatiquement).
- La validation du paiement **consomme** la réservation dans une transaction atomique
  (`select_for_update`), convertit réservé → vendu.
- Un job léger (ou un check paresseux à la lecture) **purge les réservations expirées**.

**Points de vigilance.** Le verrou doit être **court** (juste la conversion) pour ne pas
sérialiser toute la caisse. Tester le cas « deux validations simultanées sur le dernier
article » : l'une réussit, l'autre reçoit une erreur stock explicite, pas un crash.

---

## 4. Flux de paiement et encaissement

### 4.1 Machine à états d'une transaction

États : `PANIER_OUVERT` → `EN_ATTENTE_PAIEMENT` → `PAIEMENT_CONFIRME` → `VALIDEE`, avec
branches `ERREUR` et `ANNULEE`. Détail et diagramme : voir `machine-etats-transaction.md`.

Résumé :

- **PANIER_OUVERT** : lignes ajoutées, réservations de stock posées, total recalculé.
- **EN_ATTENTE_PAIEMENT** : mode choisi (wallet/espèces/terminal externe), montant figé.
- **PAIEMENT_CONFIRME** : débit wallet effectué **atomiquement**, ou cash encaissé, ou
  terminal externe OK.
- **VALIDEE** : stock consommé, notification émise, ticket dispo. État terminal.
- **ERREUR / ANNULEE** : libère les réservations, ne touche pas aux soldes (ou rollback).

### 4.2 Atomicité débit/crédit

**Problème.** Débiter le wallet de l'étudiant et créditer le compte de l'asso doivent être
**indissociables**. Une panne au milieu ne doit jamais laisser « débité mais pas crédité ».

**Recommandation.**

```python
with transaction.atomic():
    wallet = Wallet.objects.select_for_update().get(pk=wallet_id)
    if wallet.solde < montant:
        raise SoldeInsuffisant
    wallet.solde -= montant
    wallet.save()
    # écriture comptable asso + lignes + passage d'état, dans la MÊME transaction
    MouvementCompteAsso.objects.create(association=asso, montant=+montant, ...)
    transaction_obj.etat = "VALIDEE"
    transaction_obj.save()
```

- `select_for_update` verrouille la ligne wallet → pas de double dépense concurrente.
- Tout dans **un seul `transaction.atomic()`** → soit tout, soit rien.
- Le solde wallet est **dérivable** d'un journal de mouvements (source de vérité = les
  mouvements, le `solde` est un cache recalculable). Ça permet l'audit et la réconciliation.

### 4.3 Mode hors-ligne

**Problème.** Le WiFi ENSEA tombe en pleine soirée. La caisse doit continuer à encaisser.

**Scénarios & recommandation.**

- La caisse **stocke localement** les transactions hors-ligne (file locale) et **synchronise
  obligatoirement** à la reconnexion.
- **Risque du solde négatif après sync** : hors-ligne, la caisse ne connaît pas le solde
  réel à l'instant T. Deux parades combinées :
  1. **Mode hors-ligne = espèces/terminal externe par défaut** (pas de débit wallet à
     l'aveugle). Le wallet hors-ligne n'est autorisé que si l'asso l'active explicitement.
  2. Si wallet hors-ligne autorisé : on accepte le **risque d'un solde négatif borné** par un
     **plafond hors-ligne par carte**. À la sync, si le solde passe négatif, on **enregistre
     une dette** (`solde` peut être négatif, recouvré au prochain rechargement) et on notifie.
- **Hotspot téléphone** : proposé comme **maintien de liaison** quand le WiFi ENSEA est down
  (partage de connexion d'un perm) → on reste en ligne, on évite tout le mode dégradé. C'est
  la parade préférée ; le mode hors-ligne local est le **dernier recours**.
- **Idempotence de sync** : chaque transaction locale porte un **UUID client**. Le serveur
  déduplique sur cet UUID → rejouer la sync deux fois ne crée pas de doublon.

### 4.4 Encaissement pour assos sans caisse Raspberry

**Recommandation.** Une **interface mobile légère** (web responsive) pour le vendeur : saisie
du montant, choix **espèces / terminal externe**, validation. Elle enregistre la transaction
**sans toucher au wallet** (l'argent circule hors plateforme), pour la **comptabilité** de
l'asso. Le produit libre (§3.3) y est central.

### 4.5 Notifications

- Push/email à l'étudiant **à chaque rechargement** et **à chaque paiement wallet**.
- En hors-ligne, la notif est **différée** : mise en file, envoyée à la sync. Le modèle
  `Notification` porte un état (`EN_ATTENTE`/`ENVOYEE`/`ECHEC`) pour le retry.
- Découplé via **signaux Django** → un module 2027 (badges, stats) peut s'abonner aux mêmes
  événements sans modifier le cœur (§6).

### 4.6 Rechargement du wallet (PSP)

**Problème.** Le webhook du PSP (Stripe) peut arriver **deux fois** → risque de **double
crédit**.

**Recommandation — crédit idempotent piloté par le webhook.**

- Montants proposés **20 / 25 / 30 / 40 / 50 €**, **minimum 20 €**.
- Flux : l'app crée une intention de paiement (`Rechargement` état `INITIE`, avec
  `psp_session_id`). Le **webhook** (`payment_succeeded`) fait passer à `CONFIRME` **et**
  crédite le wallet, **dans une transaction atomique**, **avec contrainte d'unicité** sur
  `psp_event_id`.
- **Idempotence** : si le webhook rejoue le même `psp_event_id`, la contrainte unique
  (ou un `get_or_create` sur l'event) **empêche le second crédit**. On ne crédite **jamais**
  côté front au retour utilisateur (le retour navigateur n'est pas une preuve de paiement) —
  **seul le webhook fait foi**.
- **Vérifier la signature** du webhook (clé secrète Stripe) pour rejeter les faux events.

**Points de vigilance.** Gérer les remboursements/chargebacks (état `REMBOURSE`) → mouvement
wallet négatif tracé. Réconciliation périodique PSP ↔ journal wallet.

---

## 5. Back-office trésorier et exports

### 5.1 Séparation des données entre assos

**Problème.** Un trésorier BDE ne doit **jamais** voir les données d'Epicuria, même par
erreur de requête.

**Scénarios.**

| Option | Avantages | Inconvénients |
|---|---|---|
| **Filtrage Django** (`QuerySet.for_membership()`) | simple, testable, portable | dépend de la discipline du dev (un oubli = fuite) |
| **Row-Level Security PostgreSQL** | la BDD garantit le cloisonnement même en cas d'oubli applicatif | plus complexe à mettre en place, couplage Postgres |

**Recommandation V1.** **Filtrage Django systématique** via un `Manager`/`QuerySet` custom
imposé partout (`Model.objects.for_membership(request.active_membership)`), **+ revue de code**
sur tout endpoint financier. On garde la **RLS Postgres en option V2** comme filet de sécurité.
Tout endpoint sensible part du `active_membership` (§1.2), jamais d'un `asso_id` envoyé par le
client (sinon un trésorier malicieux change l'ID).

### 5.2 Exports Excel/CSV + planification

- **Export manuel** : bouton → génération `.xlsx` (openpyxl) / `.csv`. Pour le trésorier :
  données **anonymisées** (§2.4). Pour l'Admin Asso : annuaire **nominatif** (§2.5), action
  sensible journalisée.
- **Export automatique paramétrable** : `ExportPlanifie` (`association`, `type_export`,
  `frequence` cron-like, `destinataire`, `format`, `is_active`).
- **Tâches planifiées** :

| Option | Avantages | Inconvénients |
|---|---|---|
| **Celery + beat** | robuste, scalable, retcombe sur ses pattes | nécessite un broker (Redis/RabbitMQ) → infra |
| **django-apscheduler** | léger, pas de broker, suffisant à notre échelle | moins scalable, exécution in-process |

**Recommandation V1** : **django-apscheduler** (échelle ENSEA, infra minimale). Migration vers
**Celery** prévue si volume/charge 2027 l'exige — le code des exports est isolé dans des
fonctions appelables par n'importe quel ordonnanceur, donc la bascule ne touche pas la logique.

### 5.3 Rapport de répartition mensuel

Django calcule par asso le **net à reverser** (recettes wallet encaissées au nom de l'asso
moins commissions PSP éventuelles) et génère un **document prêt pour le trésorier ADE**
(`.xlsx` récap + détail). La **validation du virement** est une action sensible (TOTP, §1.3)
et **journalisée**. Le calcul s'appuie sur le journal de mouvements (§4.2), source de vérité.

### 5.4 Modification de prix / désactivation produits

- Le trésorier modifie les prix et **désactive** (jamais supprime) un produit.
- Produit désactivé → **disparaît de la caisse** mais **reste dans l'historique** : c'est
  pourquoi la `LigneTransaction` **copie** `libelle` et `prix_applique` au moment de la vente
  (§0, §3.3). L'historique ne dépend pas de l'état courant du catalogue.
- Tout changement de prix est **horodaté/tracé** (qui, quand, ancien→nouveau) pour l'audit.

---

## 6. Évolutivité V1 → V2

**Principe : le cœur ne bouge pas, les modules s'ajoutent comme apps Django.**

- **Cœur (stable)** : `accounts` (auth/rôles), `students` (identité/adhésions),
  `catalog` (produits/stock), `payments` (wallet/transactions/rechargements),
  `treasury` (exports/répartition).
- **Modules V2 (apps indépendantes)** :
  - **stock avancé / prêts de matériel** → s'appuie sur `MouvementStock` typé déjà prévu (§3.4) ;
  - **badges & récompenses** → s'abonne aux **signaux** de transaction/rechargement (§4.5) ;
  - **stats avancées** → lit en lecture seule, ne modifie rien.
- **Règles d'or** :
  - un module **dépend du cœur**, jamais l'inverse (pas d'import du module dans le cœur) ;
  - communication par **signaux** et **FK sortantes**, pas par modification des modèles cœur ;
  - tout point d'extension futur (tarifs, types de mouvements, modes de paiement) est un
    **`choices` extensible** ou une **table de référence**, pas un `if` en dur.

Cela évite la refonte 2027 : ajouter « prêt de matériel » = nouvelle app + nouveaux types de
`MouvementStock`, sans toucher au paiement.

---

## 7. Schéma BDD

Le schéma complet, prêt à coller sur **dbdiagram.io**, est dans le fichier **`schema-bdd.dbml`**.
Une ébauche concrète des modèles Django est dans **`models_reference.py`**.

Tables principales (détail des champs dans le DBML) :

`Utilisateur`, `Association`, `Membership` (liaison Utilisateur×Association×Role), `Role`,
`Adhesion`, `RegleAdhesion`, `MoyenIdentification` (RFID/QR), `Produit`, `Categorie`,
`MouvementStock`, `Wallet`, `MouvementWallet`, `Rechargement`, `Panier`, `LignePanier`
(réservation stock), `Transaction`, `LigneTransaction`, `MouvementCompteAsso`, `Notification`,
`ExportPlanifie`, `AuditLog`.

> Points clés repris du document : argent en entier/Decimal ; `is_active` partout ;
> `LigneTransaction` copie libellé+prix ; idempotence par UUID (sync) et `psp_event_id`
> (webhook) ; cloisonnement par `Membership`.
