# Flowcharts - Système de paiement dématérialisé ENSEA


> **Acteurs**
> - 📱 **Navigateur étudiant** : le téléphone (ou ordinateur) de l'étudiant
> - 🧑‍💼 **Navigateur vendeur/admin** : le téléphone, la tablette ou le poste de caisse du vendeur/admin, dans le même navigateur web
> - 🖥️ **Serveur Django** : seul composant serveur, tout y transite
> - 💳 **HelloAsso** : PSP prévu pour les recharges en ligne, **pas encore branché** (voir Flux 5)
>
> Généré à partir du code réel de `caisse/models.py`, `caisse/views.py`,
> `caisse/vues_ecole.py`, `caisse/roles.py`, `caisse/middleware.py` et
> `caisse/helloasso.py` (état du projet au 25/08/2026).

---

## Flux 1 - Vente catalogue et encaissement

> Le vendeur constitue un panier depuis le catalogue du pôle (stocké en session,
> pas en base tant que la vente n'est pas validée), puis encaisse : soit
> l'acheteur présente son QR code (Flux 2), soit le vendeur saisit son
> identifiant à la main.

```mermaid
flowchart TD

    START([▶ Début - Vente catalogue])
    START --> V1

    subgraph VENDEUR["🧑‍💼 Navigateur vendeur"]
        V1{"Connecté et autorisé\nà vendre sur ce pôle ?\npeut_vendre()"}
        V1 -->|Non| V1E["❌ 403 Permission refusée"]
        V1 -->|Oui| V2["Parcourir le catalogue du pôle\n(catégories, événements)"]
        V2 --> V3["Ajouter des produits au panier\nPOST /ajouter/produit_id/"]
        V3 --> V4["Panier en session :\n{produit_id: quantite}\nquantité plafonnée au stock connu"]
        V4 --> V5{"Continuer les achats\nou encaisser ?"}
        V5 -->|Continuer| V2
        V5 -->|Encaisser| V6["Page /pole/slug/encaisser/"]
        V6 --> V7{"Panier vide ?"}
        V7 -->|Oui| V2
        V7 -->|Non| V8["Saisir l'identifiant du client\nOU scanner son QR - voir Flux 2"]
        V8 --> V9["Valider l'encaissement"]
    end

    subgraph SRV["🖥️ Serveur Django - encaisser() - tout dans une transaction atomique"]
        V9 --> S1{"Un jeton QR\na été soumis ?"}
        S1 -->|Oui| S2["JetonPaiement verrouillé\n(select_for_update) par code"]
        S2 --> S3{"Jeton trouvé,\nnon utilisé,\nâge inférieur à 120s ?"}
        S3 -->|Non| S3E["❌ QR code invalide ou expiré,\nredemande-le à l'acheteur"]
        S3 -->|Oui| S4["jeton.utilise = True\n- usage unique, anti-rejeu"]
        S1 -->|Non - identifiant saisi| S5{"Compte trouvé\npar identifiant ?"}
        S5 -->|Non| S5E["❌ Aucun compte trouvé\npour cet identifiant"]
        S5 -->|Oui| S4B["profil = compte trouvé"]
        S4 --> S6
        S4B --> S6["Reverrouiller chaque produit du panier\n(select_for_update)"]
        S6 --> S7{"Événement lié\nencore vendable ?\nest_vendable()"}
        S7 -->|Non| S7E["❌ Les ventes pour cet événement\nsont terminées"]
        S7 -->|Oui| S8{"Stock suffisant\npour chaque ligne ?"}
        S8 -->|Non| S8E["❌ Stock insuffisant\npour ce produit (reste N)"]
        S8 -->|Oui| S9{"Il reste au moins\nune ligne valide ?"}
        S9 -->|Non| S9E["❌ Plus aucun produit disponible\ndans le panier, réessaie"]
        S9 -->|Oui| S10{"solde du profil ≥\ntotal recalculé ?"}
        S10 -->|Non| S10E["❌ Solde insuffisant\npour cet achat de X €\n- le solde exact n'est jamais affiché"]
        S10 -->|Oui| S11["Créer Transaction (profil, pôle, total)\n+ une LigneTransaction par produit\nlibellé et prix figés à l'instant t"]
        S11 --> S12["Débit profil.solde\nCrédit pole.solde_analytique\nDécrément du stock, produit par produit"]
        S12 --> S13{"Produit rattaché\nà un événement\nbillet ?"}
        S13 -->|Oui| S14["inscrire_sur_helloasso()\n- stub actuel : ne fait rien,\nn'échoue jamais"]
        S13 -->|Non| S15
        S14 --> S15["Commit - vente validée"]
    end

    subgraph FIN["🧑‍💼 Retour vendeur"]
        S15 --> F1["Panier vidé\nReçu envoyé par email - best effort, échec silencieux\nPage vente_ok"]
        V1E --> FE
        S3E --> FE
        S5E --> FE
        S7E --> FE
        S8E --> FE
        S9E --> FE
        S10E --> FE
        LOCK["❌ Une autre vente est en cours\nsur ce produit, réessaie\n(verrou base de données concurrent)"] --> FE
        FE["❌ Message d'erreur affiché\nsur la page d'encaissement\nPanier conservé"]
    end

    F1 --> END1([🔴 Fin])
    FE --> END1
```

---

## Flux 2 - Scan QR côté vendeur

> Il n'y a **aucun lecteur RFID ni terminal matériel** : le scan se fait par la
> caméra du navigateur du vendeur, en JavaScript pur, sans aller-retour serveur
> pour la lecture elle-même.

```mermaid
flowchart TD

    START2([▶ Scan QR - côté vendeur])
    START2 --> Q1

    subgraph CAM["🧑‍💼 Navigateur vendeur - JavaScript, aucun appel serveur pour scanner"]
        Q1["Clic sur Scanner un QR"]
        Q1 --> Q2{"Autorisation caméra\naccordée par le navigateur ?"}
        Q2 -->|Non| Q2E["❌ Impossible d'accéder\nà la caméra"]
        Q2 -->|Oui| Q3["Flux vidéo analysé en direct\npar la librairie jsQR"]
        Q3 --> Q4{"QR code détecté\ndans l'image ?"}
        Q4 -->|Non| Q3
        Q4 -->|Oui| Q5["Code décodé inséré dans\nle champ caché du formulaire"]
        Q5 --> Q6["Soumission automatique\ndu formulaire d'encaissement\nou de terminal"]
    end

    Q6 --> Q7["→ suite du traitement :\nFlux 1 Vente catalogue\nou Flux 3 Terminal"]
    Q2E --> END2
    Q7 --> END2([🔴 Fin de l'étape scan])
```

---

## Flux 3 - Terminal (vente hors catalogue, montant libre)

> Malgré son nom, le « Terminal » n'est pas un boîtier physique : c'est une page
> Django pour encaisser un montant libre, sans passer par le catalogue
> (pourboire, article non référencé...).

```mermaid
flowchart TD

    START3([▶ Début - Terminal, vente libre])
    START3 --> T1

    subgraph VENDEUR3["🧑‍💼 Navigateur vendeur"]
        T1["/terminal/ - redirection automatique\nsi un seul pôle vendable,\nsinon sélecteur de pôle"]
        T1 --> T2{"Autorisé à vendre\nsur ce pôle ?\npeut_vendre()"}
        T2 -->|Non| T2E["❌ 403 Permission refusée"]
        T2 -->|Oui| T3["Saisir un montant\nex : 1,00 €"]
        T3 --> T4["Saisir l'identifiant du client\nOU scanner son QR - voir Flux 2"]
        T4 --> T5["Valider"]
    end

    subgraph SRV3["🖥️ Serveur Django - terminal_pole() - transaction atomique"]
        T5 --> S31{"Montant > 0 ?\n(parsing virgule/point)"}
        S31 -->|Non| S31E["❌ Montant invalide"]
        S31 -->|Oui| S32["Identification du profil\n- même logique jeton/identifiant\nque le Flux 1"]
        S32 --> S33{"Profil trouvé\net jeton valide\nsi utilisé ?"}
        S33 -->|Non| S33E["❌ Erreur d'identification\n- mêmes messages que Flux 1"]
        S33 -->|Oui| S34{"solde du profil\n≥ montant ?"}
        S34 -->|Non| S34E["❌ Solde insuffisant\npour ce montant de X €"]
        S34 -->|Oui| S35["Récupère ou crée le produit\ntechnique Vente libre du pôle\nprix=0, jamais visible au catalogue"]
        S35 --> S36["Créer Transaction\n+ une LigneTransaction\nlibellé=Vente libre, prix=montant saisi"]
        S36 --> S37["Débit profil.solde\nCrédit pole.solde_analytique"]
    end

    subgraph FIN3["🧑‍💼 Retour vendeur"]
        S37 --> F31["Reçu envoyé par email - best effort\nPage vente_ok"]
        T2E --> FE3
        S31E --> FE3
        S33E --> FE3
        S34E --> FE3
        FE3["❌ Message d'erreur affiché"]
    end

    F31 --> END3([🔴 Fin])
    FE3 --> END3
```

---

## Flux 4 - QR de paiement dynamique côté étudiant

> Un jeton à usage unique, régénéré à chaque affichage de page, expire au bout
> de **2 minutes**.

```mermaid
flowchart TD

    START4([▶ L'étudiant affiche son QR de paiement])
    START4 --> E1

    subgraph ETU4["📱 Navigateur étudiant"]
        E1{"Connecté ?"}
        E1 -->|Non| E1E["❌ Redirection vers la connexion"]
        E1 -->|Oui| E2["Ouvre /payer/"]
    end

    subgraph SRV4["🖥️ Serveur Django - mon_qr()"]
        E2 --> S41["Supprime tous les jetons\nnon utilisés de ce profil"]
        S41 --> S42["Crée un nouveau JetonPaiement\ncode = jeton aléatoire cryptographique"]
        S42 --> S43["Génère l'image QR\nencodant ce code"]
    end

    S43 --> E3["QR affiché à l'écran\n+ compte à rebours 2:00"]
    E3 --> E4{"Un vendeur scanne\navant expiration ?"}
    E4 -->|"Oui, à temps"| E5["Jeton consommé côté serveur\nvoir Flux 1 - usage unique"]
    E4 -->|"Non, 2 min écoulées"| E6["Compte à rebours à 0\n→ rechargement automatique\nde la page"]
    E6 --> E2
    E1E --> END4
    E5 --> END4([🔴 Fin])
```

---

## Flux 5 - Recharge en ligne (HelloAsso) - **non implémenté**

> ⚠️ **Cette fonctionnalité n'existe pas encore dans le
> code**. C'est ce que montre le flux réel actuel :

```mermaid
flowchart TD

    START5([▶ L'étudiant clique sur Recharger])
    START5 --> R1

    subgraph ETU5["📱 Navigateur étudiant"]
        R1["Page /recharger/"]
        R1 --> R2["Bouton Recharger\naffiché mais désactivé\nbientôt disponible"]
    end

    R2 --> END5(["🟡 Fin - aucune action possible\nHelloAsso n'est pas encore branché"])
```

Ce qui existe déjà en préparation, mais n'est pas encore relié :
- Le modèle `Recharge` a des champs `statut` (`EN_ATTENTE` / `CONFIRMEE` /
  `ECHOUEE`), `reference_helloasso`, `mode_paiement="HELLOASSO"`, prêts à être
  utilisés, mais rien dans le code ne les écrit encore.
- `caisse/helloasso.py` ne contient que `inscrire_sur_helloasso()`, utilisée
  uniquement pour synchroniser des billets vendus au catalogue (Flux 1), pas
  pour des paiements. C'est un stub qui ne fait rien et n'échoue jamais.
- Il n'existe **aucune route de webhook** dans `caisse/urls.py`, ni de champ
  d'identifiant d'événement PSP pour empêcher un double crédit (pas de
  `psp_event_id` en base).

---

## Flux 6 - Recharge en espèces

```mermaid
flowchart TD

    START6([▶ Début - Recharge espèces])
    START6 --> C1

    subgraph OP6["🧑‍💼 Navigateur vendeur/admin"]
        C1{"Autorisé à recharger en espèces ?\nadmin ADE, ou droit_recharger_especes\naccordé par un admin ADE uniquement"}
        C1 -->|Non| C1E["❌ 403 Permission refusée"]
        C1 -->|Oui| C2["Page /pole/slug/recharger-especes/"]
        C2 --> C3["Saisir l'identifiant du compte\net le montant reçu en espèces"]
        C3 --> C4{"Montant > 0 ?"}
        C4 -->|Non| C4E["❌ Montant invalide"]
        C4 -->|Oui| C5["Confirmer"]
    end

    subgraph SRV6["🖥️ Serveur Django - recharger_especes() - transaction atomique"]
        C5 --> S61{"Compte trouvé\npar identifiant ?"}
        S61 -->|Non| S61E["❌ Aucun compte trouvé\npour cet identifiant"]
        S61 -->|Oui| S62["Verrouille le profil\nCrédit profil.solde += montant"]
        S62 --> S63["Créer Recharge :\nstatut=CONFIRMEE, mode_paiement=ESPECES\nencaisse_par=opérateur connecté, pole=pôle courant\ndate_confirmation=maintenant"]
    end

    S63 --> C6["✅ Page de confirmation"]
    C1E --> CE6
    C4E --> CE6
    S61E --> CE6
    CE6["❌ Message d'erreur affiché"]
    C6 --> END6([🔴 Fin])
    CE6 --> END6
```

> ⚠️ **Point d'attention** : Il n'y a pas de plafonds par recharge et de solde max, il faudra y penser au titre du code monétaire et financier)
>, ni ici ni pour l'adhésion en espèces (Flux 7). Seul un montant
> strictement positif est exigé. À garder en tête si cette conformité doit être
> assurée avant mise en production.

---

## Flux 7 - Adhésion à un pôle

> Deux chemins bien distincts : l'étudiant paie lui-même par portefeuille, ou
> un vendeur/admin encaisse des espèces à sa place. Les deux écrivent dans le
> même champ `Adhesion.annee`, avec la même contrainte d'unicité `(pole,
> profil, annee)`, il est donc essentiel qu'ils utilisent la même notion
> d'« année ».

```mermaid
flowchart TD

    START7([▶ Adhésion à un pôle])
    START7 --> A0
    A0{"Qui initie ?"}
    A0 -->|"Étudiant, portefeuille"| A1
    A0 -->|"Vendeur/admin, espèces"| B1

    subgraph WALLET["📱 Adhésion portefeuille - adherer_pole()"]
        A1["Étudiant ouvre /adherer/slug/"]
        A1 --> A2{"Le pôle propose\ndes tarifs d'adhésion ?"}
        A2 -->|Non| A2E["❌ 404"]
        A2 -->|Oui| A3{"Déjà adhérent\ncette année scolaire ?"}
        A3 -->|Oui| A3E["Page : déjà adhérent,\naucune action possible"]
        A3 -->|Non| A4["Choisir un tarif"]
        A4 --> A5{"Tarif sélectionné ?"}
        A5 -->|Non| A5E["❌ Choisis un tarif"]
        A5 -->|Oui| A6["Verrouille le profil\n- transaction atomique"]
        A6 --> A7{"solde ≥ prix\ndu tarif ?"}
        A7 -->|Non| A7E["❌ Solde insuffisant\npour cette adhésion de X €"]
        A7 -->|Oui| A8["Débit solde, crédit pôle\nCréer Adhesion\nannée = année scolaire courante\ncoupure début août — annee_scolaire_courante()\nmode_paiement=PORTEFEUILLE"]
        A8 --> A9{"Contrainte unique\n(pole, profil, année)\nrespectée ?"}
        A9 -->|"Non - IntegrityError"| A9E["❌ Adhésion déjà payée\npour cette année\n- garde-fou anti double-clic"]
        A9 -->|Oui| A10["✅ Adhésion enregistrée"]
    end

    subgraph CASH["🧑‍💼 Adhésion espèces - payer_adhesion_especes() / gerer_adherents()"]
        B1{"Autorisé à encaisser\nune adhésion espèces ?\nadmin du pôle/ADE,\nou droit_adhesion_especes"}
        B1 -->|Non| B1E["❌ 403 Permission refusée"]
        B1 -->|Oui| B2["Saisir identifiant du compte\net tarif"]
        B2 --> B3["Créer Adhesion :\nannée = année scolaire courante\ncoupure début août — annee_scolaire_courante()\nmode_paiement=ESPECES, encaisse_par=opérateur"]
        B3 --> B4{"Contrainte unique\nrespectée ?"}
        B4 -->|"Non - IntegrityError"| B4E["❌ Cette personne a déjà payé\nson adhésion pour cette année"]
        B4 -->|Oui| B5["✅ Adhésion enregistrée"]
    end

    A10 --> END7([🔴 Fin])
    B5 --> END7
    A2E --> END7
    A3E --> END7
    A5E --> END7
    A7E --> END7
    A9E --> END7
    B1E --> END7
    B4E --> END7
```

> Les deux chemins utilisent la même fonction `annee_scolaire_courante()`
> (coupure début août) pour calculer l'année d'adhésion : une adhésion payée
> par portefeuille ou en espèces le même jour tombe donc toujours dans la
> même case, et la contrainte d'unicité `(pole, profil, annee)` détecte bien
> un doublon quel que soit le mode de paiement utilisé.

---

## Flux 8 - Sécurité des comptes à pouvoir (code de sécurité)

> La « deuxième serrure » : un code à 6 chiffres, propre à chaque `(personne,
> pôle)`, exigé une fois par session pour toute personne détenant au moins un
> rôle protégé par un code.

```mermaid
flowchart TD

    START8([▶ Connexion d'un compte à pouvoir])
    START8 --> M1

    subgraph MW["🖥️ VerifierCodeMiddleware - sur chaque requête authentifiée"]
        M1{"Chemin exempté ?\n/admin/, /static/, /media/,\nlogin, logout, verifier_code"}
        M1 -->|Oui| M1P["Requête traitée normalement"]
        M1 -->|Non| M2{"session code_verifie\n= True ?"}
        M2 -->|Oui| M1P
        M2 -->|Non| M3{"L'utilisateur possède\nau moins un CodeSecuriteAdmin ?"}
        M3 -->|Non| M1P
        M3 -->|Oui| M4["Redirection vers\n/verifier-code/"]
    end

    subgraph VERIF["🖥️ verifier_code()"]
        M4 --> VV1["Formulaire de saisie du code"]
        VV1 --> VV2["Comparaison avec TOUS les codes\nde l'utilisateur - un seul valide suffit"]
        VV2 --> VV3{"Code correct ?"}
        VV3 -->|Non| VV3E["❌ Code erroné\n- aucune limite de tentatives"]
        VV3 -->|Oui| VV4["session code_verifie = True\nvalable toute la durée de la session"]
    end

    VV3E --> VV1
    VV4 --> END8([🟢 Accès débloqué\njusqu'à déconnexion])

    subgraph ADMIN8["🖥️ Création du code - admin école uniquement"]
        D1["Admin école ouvre /ecole/codes/"]
        D1 --> D2["Génère un code à 6 chiffres aléatoire\npour (user, pôle),\nou pôle=None pour une portée ADE globale"]
        D2 --> D3["Remplace l'éventuel ancien code\nHaché - jamais stocké ni relisible en clair"]
        D3 --> D4["Envoi par email, une seule fois\nnon re-consultable ensuite"]
    end
```

---

## Flux 9 - Suppression (anonymisation) de compte

```mermaid
flowchart TD

    START9([▶ Gestion d'un compte - admin école, /ecole/comptes/])
    START9 --> D1
    D1{"Action demandée ?"}

    D1 -->|"Demander suppression"| D2["DemandeSuppressionCompte créée\nsi elle n'existe pas déjà\nEmail envoyé à l'étudiant"]
    D1 -->|"Annuler suppression"| D3["Demande supprimée\naucun historique conservé"]
    D1 -->|"Basculer remboursement effectué"| D4["remboursement_effectue = True/False\nattestation manuelle,\naucun virement géré par l'application"]
    D1 -->|"Supprimer définitivement"| D5{"Éligible ?\n90 jours écoulés\nOU remboursement_effectue=True"}
    D5 -->|Non| D5E["❌ Action refusée,\npas encore éligible"]
    D5 -->|Oui| D6["profil.anonymiser() :\nnom/prénom/email effacés\nusername → compte-supprime-id\nuser.is_active=False, date_naissance=None\nstatut_compte=ANONYMISE"]
    D6 --> D7["Historique financier CONSERVÉ\nTransaction, Recharge, Adhesion, LigneTransaction\n- comptabilité intacte\nDemandeSuppressionCompte supprimée"]

    D2 --> END9A([🟡 En attente - délai 90 jours])
    D3 --> END9B([🔴 Fin - demande annulée])
    D4 --> END9C([🔴 Fin - attestation mise à jour])
    D5E --> END9D([🔴 Fin - refusé])
    D7 --> END9E([🔴 Fin - compte anonymisé])
```

---

## Récapitulatif des contraintes réellement appliquées dans le code

| Contrainte | Flux concerné | Comportement si non respectée |
|---|---|---|
| `peut_vendre` / `peut_gerer` / droits `droit_*` | Tous les flux de vente et gestion | 403 Permission refusée |
| Jeton QR valide (< 120 s, non utilisé) | Flux 1, 2, 3 | « QR code invalide ou expiré » |
| Événement `est_vendable()` | Flux 1 | « Les ventes pour cet événement sont terminées » |
| Stock suffisant | Flux 1 | « Stock insuffisant » |
| `solde ≥ montant` | Flux 1, 3, 7 (portefeuille) | « Solde insuffisant », montant exact du solde jamais révélé |
| Transaction atomique + verrous SQL (`select_for_update`) | Flux 1, 3, 6, 7 | Rollback complet si erreur, aucun débit partiel |
| Contrainte unique `(pole, profil, annee)` | Flux 7 | « Adhésion déjà payée pour cette année » |
| `droit_recharger_especes` réservé à l'admin ADE, non délégable par un admin de pôle | Flux 6 | 403 Permission refusée |
| Code de sécurité requis pour tout rôle protégé | Flux 8 | Blocage total de la navigation tant que non validé |
| Délai de 90 jours (ou remboursement attesté) avant anonymisation définitive | Flux 9 | Action refusée avant échéance |
| ~~Plafond de recharge / solde max~~ | Flux 6, 7 | **Non implémenté actuellement** |
| ~~Recharge en ligne via HelloAsso~~ | Flux 5 | **Non implémenté actuellement** - page avec bouton désactivé uniquement |
