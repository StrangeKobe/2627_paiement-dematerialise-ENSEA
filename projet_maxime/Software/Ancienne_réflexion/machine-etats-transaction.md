# Machine à états — Transaction de paiement

Source de vérité du cycle de vie d'une vente. Diagramme rendu directement sur GitHub
(Mermaid) ou collable sur https://mermaid.live.

```mermaid
stateDiagram-v2
    [*] --> PANIER_OUVERT : création du panier
    PANIER_OUVERT --> PANIER_OUVERT : ajout/retrait ligne (réserve stock)
    PANIER_OUVERT --> EN_ATTENTE_PAIEMENT : choix du mode + montant figé
    PANIER_OUVERT --> ANNULEE : abandon / expiration 5 min

    EN_ATTENTE_PAIEMENT --> PAIEMENT_CONFIRME : débit wallet OK / cash encaissé / TPE OK
    EN_ATTENTE_PAIEMENT --> ERREUR : solde insuffisant / refus / panne
    EN_ATTENTE_PAIEMENT --> ANNULEE : annulation vendeur

    PAIEMENT_CONFIRME --> VALIDEE : stock consommé + notif émise
    PAIEMENT_CONFIRME --> ERREUR : échec post-paiement (rollback)

    ERREUR --> PANIER_OUVERT : reprise possible (réservations conservées si non expirées)
    ERREUR --> ANNULEE : abandon (libère réservations)

    VALIDEE --> [*]
    ANNULEE --> [*]
```

## Description des états

| État | Sens | Effets de bord | Sorties |
|---|---|---|---|
| **PANIER_OUVERT** | lignes en cours d'ajout | réserve le stock (expire à 5 min) | EN_ATTENTE_PAIEMENT, ANNULEE |
| **EN_ATTENTE_PAIEMENT** | mode choisi, montant figé | aucun débit encore | PAIEMENT_CONFIRME, ERREUR, ANNULEE |
| **PAIEMENT_CONFIRME** | l'argent est pris | débit wallet **atomique** / cash / TPE | VALIDEE, ERREUR |
| **VALIDEE** | terminal, vente actée | stock consommé, notif, ligne comptable asso | — |
| **ERREUR** | échec récupérable | rien de monétaire engagé (ou rollback) | PANIER_OUVERT, ANNULEE |
| **ANNULEE** | terminal, abandon | libère toutes les réservations | — |

## Invariants à garantir

1. **Atomicité** : le passage `EN_ATTENTE_PAIEMENT → PAIEMENT_CONFIRME → VALIDEE` qui touche
   le wallet et le compte asso se fait dans **une seule** `transaction.atomic()` avec
   `select_for_update` sur le wallet. Jamais « débité mais pas validé ».
2. **Idempotence** : `uuid_client` unique → rejouer une sync hors-ligne ne crée pas de doublon.
3. **Réservation bornée** : un panier non payé en 5 min → `ANNULEE`, stock libéré
   automatiquement.
4. **Pas de solde négatif silencieux** : hors-ligne, le wallet n'est débité que si l'asso
   l'autorise, avec plafond ; sinon mode espèces/TPE.
5. **Historique stable** : à `VALIDEE`, on a déjà copié `libelle` + `prix_applique` dans
   `LigneTransaction` (indépendant du catalogue courant).

## Flux hors-ligne (résumé)

```mermaid
flowchart LR
    A[Caisse hors-ligne] --> B[Transaction stockée localement<br/>+ uuid_client]
    B --> C{Réseau revenu ?}
    C -- non --> B
    C -- oui --> D[Sync vers serveur]
    D --> E{uuid_client déjà vu ?}
    E -- oui --> F[Ignorer doublon]
    E -- non --> G[Créer transaction + mouvements<br/>atomique]
    G --> H[Notifs différées envoyées]
```
