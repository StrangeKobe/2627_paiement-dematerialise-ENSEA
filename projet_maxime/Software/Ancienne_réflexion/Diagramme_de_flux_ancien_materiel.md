# Flowcharts - Système de paiement dématérialisé ENSEA (ancienne version, avec terminal matériel)

> Archive de la version précédente de ce document, conservée telle quelle
> pour mémoire. Elle décrivait une cible avec un terminal matériel dédié
> (Raspberry Pi, lecteur RFID, écran OLED, buzzer), qui n'a **pas** été
> implémentée dans l'application actuelle (voir `Diagramme_de_flux_explication.md`
> pour l'état réel du code). Peut servir de point de départ si cette direction
> matérielle est reprise plus tard.
>
> **Acteurs**
> - 📱 **Interface vendeur** : téléphone du vendeur (ou Raspberry Pi 5 en poste fixe)
> - 📟 **Terminal portable** : Raspberry Pi Zero 2W (écran OLED + lecteur RFID + lecteur QR)
> - 🖥️ **Serveur Django** : hébergé sur le réseau ENSEA (intranet uniquement)
> - 💳 **PSP** : Stripe ou HelloAsso, à titre d'exemple 
>
> ⚠️ **Contrainte réseau** : le serveur Django est hébergé en local ENSEA.
> Le terminal portable doit être connecté au WiFi ENSEA (ou un réseau avec accès à ce serveur).
> Hors réseau ENSEA (événement extérieur, hotspot mobile), le terminal **ne peut pas joindre le serveur**.

---

## Flux 1 — Vente catalogue

> Le vendeur sélectionne les produits depuis son interface, le montant s'affiche sur le terminal,
> l'étudiant présente sa carte RFID ou son QR code.

```mermaid
flowchart TD

    START([▶ Début — Vente catalogue])
    START --> W1

    subgraph VENDEUR["📱 Interface vendeur — téléphone ou RPi 5"]
        W1{"WiFi ENSEA\nconnecté ?"}
        W1 -->|Non| W1E["❌ Pas de réseau\nImpossible de vendre\nVérifier le WiFi ENSEA"]
        W1 -->|Oui| AUTH{"Vendeur connecté\nSSO ENSEA ?"}
        AUTH -->|Non| LOGIN["Se connecter\nSSO ENSEA"]
        LOGIN --> AUTH2{"Authentification\nréussie ?"}
        AUTH2 -->|Non| AUTH2E["❌ Identifiants invalides\nContactez l'admin"]
        AUTH2 -->|Oui| SEL
        AUTH -->|Oui| SEL["Sélectionner les produits\ndans le catalogue\nex : 2 cafés, 1 sandwich"]
        SEL --> EMPTY{"Panier\nnon vide ?"}
        EMPTY -->|Non| SEL
        EMPTY -->|Oui| VALID["✅ Valider le panier\n→ envoi au serveur"]
    end

    subgraph SRV_CREATE["🖥️ Serveur Django - Création de la transaction"]
        VALID --> PING{"Serveur Django\njoignable ?"}
        PING -->|Non| PING_E["❌ Serveur hors ligne\nVérifier le réseau ENSEA"]
        PING -->|Oui| STOCK{"Stock suffisant\npour chaque article ?"}
        STOCK -->|Non| STOCK_E["❌ Stock insuffisant\nMessage au vendeur\nAjuster le panier"]
        STOCK -->|Oui| CREATE["Créer transaction en base\nstatut = EN_ATTENTE\nhorodatage = maintenant"]
        CREATE --> PUSH["Envoyer le montant\nau terminal portable"]
    end

    subgraph TERM_WAIT["📟 Terminal portable RPi Zero 2W — Attente paiement"]
        PUSH --> TERM_UP{"Terminal\nconnecté WiFi ?"}
        TERM_UP -->|Non| TERM_E["❌ Terminal hors ligne\nVérifier WiFi du terminal\nRedémarrer si nécessaire"]
        TERM_UP -->|Oui| OLED["Affichage OLED :\n💶 Montant total\n« Présenter carte ou QR »"]
        OLED --> WAIT{"Étudiant présente\nquelque chose ?"}
        WAIT -->|"⏱️ Timeout 60s"| TIMEOUT["❌ Timeout\nstatut = ANNULEE\nOLED : Transaction expirée\nTerminal réinitialisé"]
        WAIT -->|"Carte RFID"| RFID["Lecture carte RFID\n(SPI — RC522)"]
        WAIT -->|"QR code"| QR["Lecture QR code\n(UART)"]
        RFID --> READ{"Lecture\nréussie ?"}
        QR --> READ
        READ -->|"Non — essai ≤ 3"| OLED
        READ -->|"Non — 3 essais épuisés"| READ_E["❌ Lecture impossible\nBuzzer ❌ court\nOLED : Réessayer\nou changer de moyen"]
        READ -->|Oui| SEND["Envoi au serveur :\nidentifiant + type RFID ou QR"]
    end

    subgraph SRV_CHECK["🖥️ Serveur Django — Validation"]
        SEND --> ID_OK{"Identifiant\nexiste en base ?"}
        ID_OK -->|Non| ID_E["❌ Carte inconnue\nNon enregistrée dans le système"]
        ID_OK -->|Oui| ADM{"actif_admin\n= true ?"}
        ADM -->|Non| ADM_E["❌ Carte bloquée\npar l'administration\nContacter un admin"]
        ADM -->|Oui| ETU{"actif_etudiant\n= true ?"}
        ETU -->|Non| ETU_E["❌ Carte désactivée\npar l'étudiant lui-même\nRéactiver dans l'app"]
        ETU -->|Oui| QR_TYPE{"Type = QR code ?"}
        QR_TYPE -->|Oui| QR_AGE{"QR émis\nil y a moins de 10 min ?"}
        QR_AGE -->|Non| QR_E["❌ QR expiré\nDemander un nouveau QR\ndepuis l'application"]
        QR_AGE -->|Oui| SOLDE
        QR_TYPE -->|"Non — RFID"| SOLDE{"Solde étudiant\n≥ montant à payer ?"}
        SOLDE -->|Non| SOLDE_E["❌ Solde insuffisant\nSolde actuel : X €\nMontant requis : Y €\nRecharger le compte"]
        SOLDE -->|Oui| ATOMIC["Transaction atomique SQL\n\n① Débit wallet étudiant\n② Crédit wallet association\n③ Écriture en table transaction\n④ Copie libellé + prix à l'instant t\n⑤ Écriture ligne_transaction\n⑥ Décrément stock produit\n⑦ Horodatage validation\n\n→ Tout ou rien"]
        ATOMIC --> DB_OK{"Toutes les\nécritures SQL\nréussies ?"}
        DB_OK -->|Non| DB_E["❌ Erreur base de données\nRollback complet automatique\nAucun débit effectué\nstatut = ECHEC"]
        DB_OK -->|Oui| VALID2["✅ statut = VALIDEE\nRéponse OK envoyée\nau terminal"]
    end

    subgraph TERM_RESP["📟 Terminal portable — Retour visuel et sonore"]
        VALID2 --> BUZ_OK["🔊 Buzzer long ✅\nOLED : Paiement OK !\nSolde restant : Z €"]
        ID_E --> FAIL
        ADM_E --> FAIL
        ETU_E --> FAIL
        QR_E --> FAIL
        SOLDE_E --> FAIL
        DB_E --> FAIL
        FAIL["🔊 Buzzer court ❌\nOLED : motif du refus"]
        BUZ_OK --> RESET["Terminal revient à l'état initial\nPrêt pour le paiement suivant"]
        FAIL --> RESET
    end

    RESET --> END1([🔴 Fin])
```

---

## Flux 2 — Vente libre

> Le vendeur saisit directement un montant sur le terminal (produit hors catalogue).
> L'étudiant présente sa carte RFID ou son QR code.

```mermaid
flowchart TD

    START2([▶ Début — Vente libre])
    START2 --> VL1

    subgraph TERM_LIBRE["📟 Terminal portable RPi Zero 2W — Saisie vendeur"]
        VL1{"Terminal connecté\nau WiFi ENSEA ?"}
        VL1 -->|Non| VL1_E["❌ Terminal hors ligne\nImpossible de vendre\nVérifier WiFi terminal"]
        VL1 -->|Oui| VL2["Vendeur bascule\nen mode Vente libre\nsur le terminal"]
        VL2 --> VL3["Vendeur saisit\nle montant au clavier\nex : 1,00 €"]
        VL3 --> VL4{"Montant\n> 0 € ?"}
        VL4 -->|Non| VL3
        VL4 -->|Oui| VL5["Affichage OLED :\n💶 Montant saisi\n« Présenter carte ou QR »"]
        VL5 --> VL6{"Étudiant présente\nquelque chose ?"}
        VL6 -->|"⏱️ Timeout 60s"| VL_TO["❌ Timeout\nRetour à la saisie"]
        VL6 -->|"Carte RFID"| VL_RFID["Lecture carte RFID"]
        VL6 -->|"QR code"| VL_QR["Lecture QR code"]
        VL_RFID --> VL_READ{"Lecture\nréussie ?"}
        VL_QR --> VL_READ
        VL_READ -->|"Non ≤ 3"| VL5
        VL_READ -->|"Non — 3 essais"| VL_READ_E["❌ Lecture impossible\nBuzzer ❌"]
        VL_READ -->|Oui| VL_SEND["Envoi au serveur :\nidentifiant + montant libre\ntype = PAIEMENT_LIBRE"]
    end

    subgraph SRV_LIBRE["🖥️ Serveur Django — Validation vente libre"]
        VL_SEND --> VL_ID{"Identifiant\nexiste en base ?"}
        VL_ID -->|Non| VL_ID_E["❌ Carte inconnue"]
        VL_ID -->|Oui| VL_ADM{"actif_admin = true\nET actif_etudiant = true ?"}
        VL_ADM -->|Non| VL_ADM_E["❌ Carte bloquée ou désactivée\nmotif renvoyé au terminal"]
        VL_ADM -->|Oui| VL_QR_CHECK{"Type = QR ?"}
        VL_QR_CHECK -->|Oui| VL_QR_AGE{"QR < 10 min ?"}
        VL_QR_AGE -->|Non| VL_QR_E["❌ QR expiré"]
        VL_QR_AGE -->|Oui| VL_SOLDE
        VL_QR_CHECK -->|"Non — RFID"| VL_SOLDE{"Solde ≥ montant ?"}
        VL_SOLDE -->|Non| VL_SOLDE_E["❌ Solde insuffisant\nSolde : X € — Requis : Y €"]
        VL_SOLDE -->|Oui| VL_ATOMIC["Transaction atomique SQL\n\n① Débit wallet étudiant\n② Crédit wallet association\n③ Écriture transaction\n   type = PAIEMENT_LIBRE\n   libellé = Vente libre + montant\n   pas de produit associé\n   stock non impacté\n④ Horodatage validation\n\n→ Tout ou rien"]
        VL_ATOMIC --> VL_DB{"SQL réussi ?"}
        VL_DB -->|Non| VL_DB_E["❌ Rollback complet\nAucun débit"]
        VL_DB -->|Oui| VL_OK["✅ statut = VALIDEE"]
    end

    subgraph TERM_LIBRE_RESP["📟 Terminal — Retour"]
        VL_OK --> VL_BUZ_OK["🔊 Buzzer long ✅\nOLED : Paiement OK !\nSolde restant : Z €"]
        VL_ID_E --> VL_FAIL
        VL_ADM_E --> VL_FAIL
        VL_QR_E --> VL_FAIL
        VL_SOLDE_E --> VL_FAIL
        VL_DB_E --> VL_FAIL
        VL_FAIL["🔊 Buzzer court ❌\nOLED : motif du refus"]
        VL_BUZ_OK --> VL_RESET["Retour état initial\nPrêt pour vente suivante"]
        VL_FAIL --> VL_RESET
    end

    VL_RESET --> END2([🔴 Fin])
```

---

## Flux 3 — Rechargement en ligne (CB via Stripe ou HelloAsso)

> L'étudiant recharge son wallet depuis son téléphone en payant par carte bancaire.

```mermaid
flowchart TD

    START3([▶ Début — Rechargement en ligne])
    START3 --> R1

    subgraph ETU_PHONE["📱 Téléphone étudiant"]
        R1{"Connexion\nSSO ENSEA ?"}
        R1 -->|Non| R1_E["❌ Connexion impossible\nVérifier identifiants ENSEA"]
        R1 -->|Oui| R2["Accéder à la page\nRechargement"]
        R2 --> R3["Saisir le montant\nsouhaité"]
        R3 --> R4{"Montant valide ?\n≥ 10 € (min recommandé)\n≤ 150 € (plafond légal)\nSolde résultant ≤ 100 €"}
        R4 -->|Non| R4_E["❌ Montant invalide\nMessage explicatif affiché\nex : solde max 100 € atteint"]
        R4 -->|Oui| R5["Clic sur Recharger\n→ redirection vers le PSP"]
    end

    subgraph PSP_BLOCK["💳 PSP — Stripe ou HelloAsso"]
        R5 --> PSP1{"PSP\njoignable ?"}
        PSP1 -->|Non| PSP1_E["❌ PSP hors ligne\nEssayer plus tard"]
        PSP1 -->|Oui| PSP2["Page de paiement CB\nsécurisée PSP"]
        PSP2 --> PSP3["Étudiant saisit\nses coordonnées CB"]
        PSP3 --> PSP4{"3D Secure\nrequis ?"}
        PSP4 -->|Oui| PSP5["Validation 3D Secure\n(SMS ou app bancaire)"]
        PSP5 --> PSP6{"3DS\nvalidé ?"}
        PSP6 -->|Non| PSP6_E["❌ 3DS échoué\nPaiement refusé\nEssayer une autre CB"]
        PSP6 -->|Oui| PSP_OK
        PSP4 -->|Non| PSP_OK{"CB\nacceptée ?"}
        PSP_OK -->|Non| PSP_OK_E["❌ CB refusée\nMotif : provision insuffisante\ncarte expirée etc.\nEssayer une autre CB"]
        PSP_OK -->|Oui| WEBHOOK_SEND["PSP envoie un webhook\nau serveur Django\névénement = payment_intent.succeeded"]
    end

    subgraph SRV_RECHARGE["🖥️ Serveur Django — Traitement webhook"]
        WEBHOOK_SEND --> WH1{"Webhook\nreçu et signé\ncorrectement ?"}
        WH1 -->|Non| WH1_E["⚠️ Webhook invalide\nIgnoré — log d'erreur\n(faux webhook ou attaque)"]
        WH1 -->|Oui| WH2{"psp_event_id\ndéjà en base ?"}
        WH2 -->|Oui| WH2_DUP["⚠️ Doublon détecté\nWebhook ignoré silencieusement\n(protection double-crédit)"]
        WH2 -->|Non| WH3["Crédit wallet étudiant\n+ écriture en table rechargement :\n— montant\n— date\n— psp_event_id UNIQUE\n— type = CB\n— statut = REUSSI"]
        WH3 --> WH4{"Écriture SQL\nréussie ?"}
        WH4 -->|Non| WH4_E["❌ Erreur base de données\nRollback\nPSP notifié en erreur"]
        WH4 -->|Oui| WH5["Nouveau solde disponible\nNotification envoyée\nà l'étudiant"]
    end

    subgraph ETU_RESP["📱 Téléphone étudiant — Retour"]
        WH5 --> R_OK["✅ Page de confirmation\nNouveausolde affiché\nHistorique mis à jour"]
        PSP_OK_E --> R_FAIL
        PSP6_E --> R_FAIL
        WH4_E --> R_FAIL
        R_FAIL["❌ Page d'erreur\nmotif affiché\nAucun débit si erreur serveur"]
    end

    R_OK --> END3([🔴 Fin])
    R_FAIL --> END3
    WH2_DUP --> END3
```

---

## Flux 4 — Rechargement en espèces (via trésorier)

> L'étudiant apporte des espèces à un trésorier,
> qui crédite manuellement le wallet depuis l'interface Django.

```mermaid
flowchart TD

    START4([▶ Début — Rechargement espèces])
    START4 --> T1

    subgraph TRES["🖥️ Interface trésorier — Django"]
        T1{"Trésorier\nauthentifié\nSSO ENSEA ?"}
        T1 -->|Non| T1_E["❌ Connexion impossible\nContactez un admin"]
        T1 -->|Oui| T2{"Rôle trésorier\nvérifié ?\n(groupe tresorier_asso)"}
        T2 -->|Non| T2_E["❌ Accès refusé\nPas les droits nécessaires"]
        T2 -->|Oui| T3["Rechercher l'étudiant\npar nom ou numéro étudiant"]
        T3 --> T4{"Étudiant\ntrouvé en base ?"}
        T4 -->|Non| T4_E["❌ Étudiant inconnu\nVérifier l'orthographe\nou demander sa carte"]
        T4 -->|Oui| T5["Afficher la fiche étudiant\n— Nom prénom\n— Solde actuel\n— Dernières transactions"]
        T5 --> T6["Saisir le montant\ndes espèces reçues"]
        T6 --> T7{"Montant valide ?\n> 0 €\nSolde résultant ≤ 100 €\n≤ 150 € (plafond légal)"}
        T7 -->|Non| T7_E["❌ Montant invalide\nex : solde max 100 € atteint\nEspèces en trop à rendre"]
        T7 -->|Oui| T8["Trésorier confirme\nle rechargement\n(clic Confirmer)"]
    end

    subgraph SRV_ESPECES["🖥️ Serveur Django — Écriture"]
        T8 --> E1["Crédit wallet étudiant\n+ écriture en table rechargement :\n— montant\n— date\n— type = ESPECES\n— psp_event_id = null\n— opérateur = trésorier connecté\n— statut = REUSSI"]
        E1 --> E2{"Écriture SQL\nréussie ?"}
        E2 -->|Non| E2_E["❌ Erreur base de données\nRollback complet\nAucun crédit effectué"]
        E2 -->|Oui| E3["Écriture audit_log :\n— action = RECHARGE_ESPECES\n— opérateur = trésorier\n— montant crédité\n— étudiant concerné\n— horodatage\n\n→ Traçabilité comptable garantie"]
    end

    subgraph TRES_RESP["🖥️ Interface trésorier — Confirmation"]
        E3 --> C1["✅ Message de confirmation\nNouveausolde affiché\nà côté de la fiche étudiant"]
        E2_E --> C2["❌ Message d'erreur\nAucun crédit effectué\nRéessayer ou contacter l'admin"]
        C1 --> C3["Trésorier peut\nenchaîner un autre rechargement\nou revenir au menu"]
    end

    C3 --> END4([🔴 Fin])
    C2 --> END4
```

---

## Récapitulatif des contraintes critiques

| Contrainte | Flux concerné | Comportement si non respectée |
|---|---|---|
| WiFi ENSEA requis | Tous | Blocage dès le début, message explicite |
| Serveur Django local ENSEA | Tous | Hors réseau ENSEA = terminal injoignable |
| `actif_admin = true` | Paiement 1 et 2 | Refus carte, message « bloquée par admin » |
| `actif_etudiant = true` | Paiement 1 et 2 | Refus carte, message « désactivée par étudiant » |
| QR code valide < 10 min | Paiement 1 et 2 | Refus, demande nouveau QR |
| Solde ≥ montant | Paiement 1 et 2 | Refus, solde affiché |
| Transaction atomique SQL | Paiement 1 et 2 | Rollback complet si erreur — aucun débit partiel |
| Montant recharge ≤ 150 € | Rechargement 3 et 4 | Bloqué côté Django (plafond légal CMF D.525-1) |
| Solde résultant ≤ 100 € | Rechargement 3 et 4 | Bloqué côté Django |
| `psp_event_id` unique | Rechargement 3 | Webhook doublon ignoré silencieusement |
| Timeout terminal 60s | Paiement 1 et 2 | Transaction annulée, terminal réinitialisé |
| 3 essais lecture max | Paiement 1 et 2 | Buzzer ❌, affichage erreur |
