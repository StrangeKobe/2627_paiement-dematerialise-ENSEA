# Explication de la base de données - ENSEA Cashless

Ce fichier accompagne `bdd_cashless.dbml` (à importer sur [dbdiagram.io](https://dbdiagram.io)). Il explique le rôle de chaque table et pourquoi elles sont reliées ainsi. Généré à partir de `caisse/models.py`, l'état final du projet.

## Vue d'ensemble

La base s'organise autour de trois grands blocs :

1. **Catalogue** : `Pole`, `Categorie`, `Evenement`, `Produit` : ce qui est en vente.
2. **Argent et comptes** : `ProfilUtilisateur`, `Transaction`, `LigneTransaction`, `Recharge`, `Adhesion` : qui possède combien, et chaque mouvement.
3. **Accès et sécurité** : `Affectation`, `CodeSecuriteAdmin`, `JetonPaiement`, `DemandeSuppressionCompte` : qui a le droit de faire quoi, et comment on protège les comptes à pouvoir.

`ParticipantImporte` et `TarifAdhesion` sont deux tables satellites, l'une pour la billetterie externe, l'autre pour les prix d'adhésion.

`auth_user` est la table native de Django (`django.contrib.auth`) : ce n'est pas une table qu'on a créée, mais presque tout pointe vers elle, car c'est elle qui gère la connexion (identifiant, mot de passe).

---

## Bloc Catalogue

### Pole
Un pôle de l'ADE (Kfet, BDE, Epicuria...). C'est la table centrale : presque toutes les autres tables ont une clé étrangère vers `Pole`, car chaque produit, chaque vente, chaque rôle est rattaché à un pôle précis.

- `solde_analytique` : le total encaissé par ce pôle, mis à jour à chaque vente/adhésion/recharge.
- `est_operationnel` : un pôle peut exister sans avoir son propre point de vente (ex. l'ADE, qui vend sous BDE), il reste dans la base mais disparaît des listes actives.

### Categorie
Un rayon d'affichage à la caisse (Boissons, Snacks...). Appartient à un seul `Pole`. Sert uniquement à regrouper des `Produit` à l'écran.

### Evenement
Le dossier qui regroupe les places d'une soirée. Appartient à un `Pole`. `actif` et `date_fin_vente` déterminent ensemble si on peut encore vendre pour cet événement (`est_vendable()`).

### Produit
La table la plus connectée du catalogue. Un produit est **soit** un article permanent (rattaché à une `Categorie`), **soit** un billet/article de soirée (rattaché à un `Evenement`), **soit** un produit technique de vente libre (`est_vente_libre`, utilisé par le Terminal pour un montant saisi à la main, sans catalogue).
- `categorie_id` et `evenement_id` sont tous deux nullables : un produit n'a jamais les deux en même temps dans la pratique.
- `est_billet` distingue, pour un produit d'événement, une vraie entrée (compte comme présence) d'un simple produit vendu ce soir-là (boisson, écocup).

---

## Bloc Argent et comptes

### ProfilUtilisateur
Le prolongement "cashless" d'un compte `auth_user` (relation **one-to-one** : chaque utilisateur a au plus un profil). C'est ici qu'est stocké le `solde` du portefeuille, jamais sur `auth_user`.
- `secret_qr` et les jetons (`JetonPaiement`) servent au paiement par QR code.
- `date_naissance` sert à calculer un âge (jamais affiché brut, sauf à l'admin école).
- `statut_compte` (ACTIF / DESACTIVE / ANONYMISE) reflète le cycle de vie du compte.

### Transaction / LigneTransaction
Une **Transaction** est un achat global (le "ticket") : elle débite le `profil` et crédite le `pole`. Une **LigneTransaction** est le détail (un produit, une quantité, un prix figé au moment de l'achat, jamais recalculé depuis `Produit.prix`, pour que l'historique reste exact même si le prix change ensuite).
- `LigneTransaction.reference_helloasso` est remplie automatiquement si ce billet a été synchronisé vers HelloAsso.

### Recharge
Un rechargement du portefeuille, via HelloAsso ou en espèces (`mode_paiement`). Le champ `pole` n'a de sens que pour une recharge en espèces : il indique depuis quel pôle l'argent liquide a été reçu, pour le suivi de trésorerie, indépendant de qui a le droit de recharger (voir `Affectation`).

### Adhesion
Le paiement d'une cotisation à un pôle, pour une année scolaire donnée. Contrainte d'unicité `(pole, profil, annee)` : impossible de payer deux fois la même adhésion la même année. `mode_paiement` distingue un paiement par portefeuille (immédiat, via l'appli) d'un paiement en espèces (encaissé par un admin, tracé via `encaisse_par`).

### TarifAdhesion
Les tarifs proposés par un pôle pour ses adhésions (ex. "1ère année" à 5€, "Ancien élève" à 10€). Un pôle peut en proposer plusieurs ; une `Adhesion` ne référence pas directement un `TarifAdhesion`, seul le `montant` payé est conservé sur `Adhesion`, figé au moment du paiement.

---

## Bloc Accès et sécurité

### Affectation
La table des rôles. Relie un `auth_user` à un rôle (`VENDEUR`, `ADMIN_POLE`, `ADMIN_ADE`, `ADMIN_ECOLE`), avec un `pole` optionnel :
- `VENDEUR` et `ADMIN_POLE` sont toujours rattachés à un pôle précis.
- `ADMIN_ADE` et `ADMIN_ECOLE` ont `pole = NULL` : ce sont des rôles globaux, valables sur tous les pôles.

Une personne peut avoir plusieurs lignes `Affectation` (donc cumuler plusieurs rôles, sur des pôles différents). Les sept champs `droit_*` sont des droits supplémentaires, accordables au cas par cas à un `VENDEUR` (un admin a déjà tout).

### CodeSecuriteAdmin
La "deuxième serrure" des comptes à pouvoir : un code numérique, propre à un `(user, pole)`, haché comme un mot de passe (jamais relisible). Contrainte d'unicité sur `(user, pole)` : un seul code actif par personne et par périmètre.

### JetonPaiement
Le jeton à usage unique encodé dans le QR code affiché à l'écran de l'étudiant pour payer. Change à chaque rafraîchissement, expire après 2 minutes (`est_valide()`), pour empêcher qu'une capture d'écran soit réutilisée plus tard.

### DemandeSuppressionCompte
Le suivi d'une demande de suppression (anonymisation) d'un compte, déclenchée par un admin école. Relation **one-to-one** avec `ProfilUtilisateur` : un compte a au plus une demande de suppression en cours. Un délai de 90 jours s'écoule avant que la suppression définitive soit possible (`eligible_suppression_definitive`), sauf si le remboursement du solde a déjà été géré manuellement.

### ParticipantImporte
Une ligne de participant importée depuis une billetterie externe (HelloAsso), pour un événement dont l'argent ne transite pas par le portefeuille interne. Purement informatif : jamais liée à un `Transaction` ni à un mouvement d'argent, pour ne jamais fausser les comptes.

---

## Points de lecture utiles sur le diagramme

- **Toutes les flèches partent du `_id` (clé étrangère) vers l'`id` de la table référencée**, c'est la convention `ref: >` de DBML.
- Les relations marquées `ref: -` (`ProfilUtilisateur.user_id`, `DemandeSuppressionCompte.profil_id`) sont des **one-to-one** : au plus une ligne de chaque côté.
- Un champ FK marqué `null` dans le diagramme signifie que la relation est optionnelle (ex. `Produit.categorie_id` et `Produit.evenement_id`, `Affectation.pole_id`).
- `auth_user` n'a que quelques colonnes représentées (les utiles pour comprendre les relations), la vraie table Django en a plus (mot de passe haché, dates de connexion, etc.), non pertinentes ici.
