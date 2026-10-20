# Hardware - Caisse ENSEA

Ce dossier contient la conception électronique des **deux PCB** du projet, leurs
datasheets, et le retour d'expérience matériel du stage. Tout ce qui concerne la
mise en service logicielle des Raspberry Pi (flashage, réseau, tests des
périphériques) est dans `../Software/Raspberry/`.

## Les deux cartes

| Carte | Rôle | Raspberry | Alimentation |
|---|---|---|---|
| **Caisse enregistreuse** | Poste fixe Kfet : interface vendeur plein écran + tiroir-caisse | Pi 5 | Secteur, jack 12 V, buck TPS54560 → 5 V |
| **Module de paiement dématérialisé** | Terminal portable : lecture RFID / QR, écran OLED | Pi Zero 2 W | Batterie 18650 + HAT UPS X306 |

## Où regarder en premier

| Je veux... | Aller dans... |
|---|---|
| Comprendre le rôle et le câblage de la carte caisse | `PCB_Caisse_Enregistreuse/PCB - Caisse Enregistreuse.md` |
| Comprendre le rôle et le câblage du terminal portable | `PCB_Caisse_Dématérialisée/PCB_Module_Paiement_Dématérialisé.md` |
| Savoir ce qui n'a pas marché et ce qu'il faut corriger en V2 | `PROBLEMES_MATERIEL.md` |
| Voir l'état des tests des périphériques | `../Software/Raspberry/TESTS_CAISSE.md` et `TESTS_TERMINAL.md` |
| Ouvrir les fichiers KiCad / récupérer les Gerber | voir « Structure » ci-dessous |

## À lire avant de refaire un PCB

`PROBLEMES_MATERIEL.md` recense tous les défauts rencontrés (empreinte SOT-23 des
MOSFET erronée, interrupteur mal placé sur le rail 12 V, valeur de R12 du diviseur
UVLO, lecteur QR non compatible UART...) au format *symptôme → cause → correction*,
et se termine par un tableau récapitulatif des corrections à apporter à la **V2 des
cartes**. C'est le point de départ obligatoire pour la personne qui reprend la
partie électronique.

## Structure du dossier

```
Hardware/
├── README.md                       ← ce fichier
├── PROBLEMES_MATERIEL.md            ← retour d'expérience + corrections V2
│
├── PCB_Caisse_Enregistreuse/
│   ├── PCB - Caisse Enregistreuse.md    ← doc de conception
│   ├── DataSheets/                      ← TPS54560, MOSFET, passifs...
│   └── PCB_Caisse_Enregistreuse/        ← projet KiCad (.kicad_pro/_sch/_pcb),
│       ├── gerber_caisse_enregistreuse/     Gerber, .step, iBOM
│       └── PCB_Caisse_Enregistreuse-backups/
│
└── PCB_Caisse_Dématérialisée/
    ├── PCB_Module_Paiement_Dématérialisé.md    ← doc de conception
    └── PCB_Module_Paiement_Principal/
        ├── Datasheet/                          ← RC522, PN532, SSD1327, MAX17043...
        └── PCB_Caisse_Dématérialisée/          ← projet KiCad, Gerber, .step, iBOM
```

> Note : le dossier `PCB_Caisse_Dématérialisée/` correspond au **terminal
> portable** (module de paiement), pas à la caisse fixe. Le nom vient d'une
> première version du vocabulaire du projet.
