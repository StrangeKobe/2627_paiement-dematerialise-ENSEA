# Software - ENSEA Cashless

Ce dossier contient tout le développement logiciel du projet : le code
Django réel, le tutoriel qui le reconstruit pas à pas, et la documentation
technique à jour. `Ancienne_réflexion/` et `First_Test_Appli_Django/`
gardent une trace de la réflexion initiale et du premier essai, mais **ne
décrivent pas le code actuel**.

## Où regarder en premier

| Je veux... | Aller dans... |
|---|---|
| Voir le code Django qui tourne réellement | `Tutoriel_Application_Cashless_ENSEA/Test_App_Django/` |
| Comprendre le projet pas à pas, partie par partie | `Tutoriel_Application_Cashless_ENSEA/Tuto_Django2.md` |
| Avoir une vue d'ensemble de l'architecture actuelle | `Diagramme_BDD/Architecture_complete_explication.md` |
| Voir le schéma de base de données | `Diagramme_BDD/bdd_cashless.dbml` + `Diagramme_BDD/bdd_cashless_explication.md` |
| Voir les flux d'exécution (qui appelle quoi) | `Diagramme_BDD/Diagramme_de_flux_explication.md` |
| Voir les cycles de vie à plusieurs états | `Diagramme_BDD/Machine_a_etats_explication.md` |
| Préparer un Raspberry Pi (caisse/terminal) | `Raspberry/RaspberryPi_Tuto.md` |
| Voir l'état des tests périphériques (tiroir, buzzer, RFID, OLED, QR) | `Raspberry/TESTS_CAISSE.md` + `Raspberry/TESTS_TERMINAL.md` |

## Lancer l'application

Le détail complet (création du projet, des modèles, de chaque page) est
expliqué dans `Tuto_Django2.md`, à côté.

## Préparer un Raspberry Pi

Tout ce qui concerne les deux cartes est regroupé dans `Raspberry/` :

- `Raspberry/RaspberryPi_Tuto.md` couvre tout le flashage et la mise en
  réseau d'un Raspberry (Pi 5 pour la caisse, Pi Zero 2 W pour le terminal) :
  écrire la carte avec Raspberry Pi Imager, créer un compte à la main si la
  personnalisation automatique échoue, retrouver le Raspberry sur le réseau
  (`nmap`), s'y connecter en SSH, et déboguer en dernier recours via la
  console série (adaptateur USB-UART CH340). Il se termine par un tableau
  récapitulatif de tous les pièges déjà rencontrés et un aide-mémoire des
  commandes utiles. Les photos référencées sont dans `../Images/Raspberry/`.
- `Raspberry/TESTS_CAISSE.md` et `Raspberry/TESTS_TERMINAL.md` : état réel des
  tests logiciels des périphériques sur chaque carte (ce qui est validé, ce
  qui bloque, comment relancer). Les blocages matériels renvoient vers
  `../../Hardware/PROBLEMES_MATERIEL.md`.

## Structure du dossier

```
Software/
├── Raspberry/                        ← mise en service et tests des 2 cartes
│   ├── RaspberryPi_Tuto.md           ← flasher et configurer un Raspberry Pi
│   ├── TESTS_CAISSE.md               ← tests périphériques Pi 5 (tiroir, buzzer)
│   └── TESTS_TERMINAL.md             ← tests périphériques Pi Zero 2 W (RFID, OLED, QR)
├── Tutoriel_Application_Cashless_ENSEA/
│   ├── Tuto_Django2.md              ← le tutoriel complet (14 parties)
│   └── Test_App_Django/             ← le code Django réel
├── Diagramme_BDD/
│   ├── Architecture_complete_explication.md
│   ├── bdd_cashless.dbml
│   ├── bdd_cashless_explication.md
│   ├── Diagramme_de_flux_explication.md
│   └── Machine_a_etats_explication.md
├── Ancienne_réflexion/               ← vision initiale, historique
│   ├── architecture-complete.md
│   ├── explication-bdd-v1.md
│   ├── machine-etats-transaction.md
│   ├── Diagramme_de_flux_ancien_materiel.md
│   └── schema-bdd-v1 (2).dbml
└── First_Test_Appli_Django/          ← premier essai, historique
    ├── Tuto_Django.md
    └── Django/
```
