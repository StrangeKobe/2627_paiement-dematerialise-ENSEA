# Documents - Étude et cadrage du projet

Ce dossier rassemble tout le travail d'**analyse, de comparaison et de cadrage** qui a
précédé et accompagné le développement : réglementation, choix du prestataire de paiement,
comparaison avec d'autres écoles, et comptes rendus des réunions.

La conception technique est ailleurs : [../Software/](../Software/) (application) et
[../Hardware/](../Hardware/) (PCB).

## Où regarder en premier

| Je veux… | Aller dans… |
|---|---|
| Savoir si on a le droit de faire ça (monnaie électronique, ACPR) | `conformite_reglementaire/Conformite_reglementaire.md` |
| Voir la réponse de l'ACPR et ce qu'il reste à leur fournir | `conformite_reglementaire/Conformite_reglementaire.md` §6 + `conformite_reglementaire/Réglementation/` |
| Comprendre un terme (PSP, webhook, interchange, KYC, DSP2…) | `conformite_reglementaire/glossaire_paiement.md` |
| Choisir / justifier le prestataire de paiement (coûts chiffrés) | `Systèmes de paiment/Analyse_comparative_des_solutions_de_paiement_business_model*.md` |
| Comparer Stripe / HelloAsso / Monetico / Payplug / Lyra / Wero… | `Systèmes de paiment/Analyse_des_solutions_de_paiement_alternative.md` |
| Voir ce que font les autres écoles (Note Kfet, Izly, TiBillet…) | `Systèmes de paiment/Benchmark_Systemese_de_paiement_étudiants_existants.md` |
| Retrouver ce qui s'est dit en réunion et avec qui | `Réunion/` |

## Contenu

```
Documents/
├── conformite_reglementaire/
│   ├── Conformite_reglementaire.md          ← analyse monnaie électronique + exemption L.521-3 / L.525-5,
│   │                                           retour ACPR (§6), points ouverts, RGPD
│   ├── glossaire_paiement.md                ← tous les termes techniques et réglementaires
│   ├── CGU_draft.md                         ← ⚠️ brouillon des CGU : encore vide, à rédiger
│   ├── Analyse_des_solutions_de_paiement_alternative.md   (copie — voir « Systèmes de paiment »)
│   ├── Benchmark_Systemese_de_paiement_étudiants_existants.md  (copie — voir « Systèmes de paiment »)
│   └── Réglementation/                      ← textes de référence
│       ├── Reponse_ACPR_procedure_exemption.md   ← le message de l'ACPR, verbatim
│       ├── Avis de la Banque de France sur la sécurité des paiements.docx
│       ├── 20230726_position_2022-p-01.pdf       ← Position ACPR « réseau limité »
│       ├── Article L525-5.pdf
│       └── tracfin_2014.pdf
│
├── Systèmes de paiment/
│   ├── Analyse_des_solutions_de_paiement_alternative.md   ← comparatif qualitatif des PSP
│   ├── Analyse_comparative_des_solutions_de_paiement_business_model.md      ← modèle annuel (pleine capacité)
│   ├── Analyse_comparative_des_solutions_de_paiement_business_model_ADE.md  ← modèle pilote ADE (9 mois)
│   ├── Benchmark_Systemese_de_paiement_étudiants_existants.md
│   ├── Business_model_solutions_paiement.xlsx
│   └── Business_model_pilote_ADE.xlsx
│
└── Réunion/                                 ← un dossier par réunion (CR .md + slides .pdf)
    ├── Réunion_05-06-26/   M. Moubêche — réglementation, alternatives à Stripe, idée compte unique ADE
    ├── Réunion_11-06-26/   M. Moubêche — recharge espèces, business model, contacts à établir
    ├── Réunion_16-06-26/   ECAM Lyon — leur système (vérif identité + Zettle, pas de portefeuille)
    ├── Réunion_18-06-2026/ Monecarte — App Campus, devis ~23 k€ HT
    └── Réunion_19-06-2026/ GLYPS Education — plateforme vie associative, un HelloAsso par asso
```

## À retenir

- **Cadre légal** : le portefeuille est de la monnaie électronique, mais entre dans l'**exemption** de l'article L. 521-3 / L. 525-5 CMF (réseau limité + plafonds bas + volume < 1 M€/an). L'ACPR a confirmé la procédure : sous 1 M€ la déclaration n'est pas obligatoire, mais une présentation du projet est attendue si on veut la confirmation officielle. Détail et check-list : `Conformite_reglementaire.md` §6.
- **Prestataire retenu** : **HelloAsso** (0 % de commission). Stripe / solutions bancaires en plan B, chiffrés dans les business models.
- **Prérequis juridique** : formaliser le rattachement statutaire des pôles (Kfet, BDE, Epicuria) à l'ADE.
- **À rédiger** : les CGU (`CGU_draft.md` est vide).

> Note : `Analyse_des_solutions_de_paiement_alternative.md` et
> `Benchmark_Systemese_de_paiement_étudiants_existants.md` sont présents en double
> (dans `conformite_reglementaire/` et `Systèmes de paiment/`). La version de référence est
> celle de `Systèmes de paiment/`.
