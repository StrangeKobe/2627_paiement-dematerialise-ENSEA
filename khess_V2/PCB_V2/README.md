# PCB ENSEA — correction V2

Révision du 20 octobre 2026, réalisée à partir de `2627_paiment-demat-ralis-ENSEA.zip` et du retour d'expérience `Hardware/PROBLEMES_MATERIEL.md`.

Cette archive contient les **deux projets matériels KiCad corrigés**. Ouvrir avec **KiCad 9.0 ou ultérieur** :

| Carte | Projet à ouvrir |
|---|---|
| Caisse fixe, Raspberry Pi 5 | `Hardware/Caisse_Fixe/PCB_Caisse_Enregistreuse.kicad_pro` |
| Terminal mobile, Raspberry Pi Zero 2 W | `Hardware/Terminal_Mobile/PCB_Caisse_Dématérialisée.kicad_pro` |

Lire **MODIFICATIONS.md** pour la liste des corrections et **Hardware/README.md** pour le câblage et les choix de composants. La nomenclature est dans **NOMENCLATURE.md**.

Les contrôles KiCad 9.0.9 donnent, pour chaque carte : **0 anomalie ERC, 0 anomalie DRC, 0 liaison non routée et 0 écart schéma/PCB**, selon les règles du projet d'origine. Les fichiers de preuve sont dans `Validation/` ; `revalider.py` permet de relancer les contrôles avec `kicad-cli` installé.

## Contenu

- `Hardware/` : schémas, PCB, paramètres et bibliothèques locales de symboles/empreintes.
- `Fabrication_prototype/` : nouveaux Gerber quatre couches, perçages et positions CMS.
- `Apercus/` : schémas et vues des cartes en SVG ; vues principales également en PNG.
- `Validation/` : rapports ERC/DRC, netlists et contrôle des connexions.
- `Documentation_origine/` : documents V1 conservés pour traçabilité ; leurs prescriptions peuvent être contredites par la V2.
- `Licences/` : licence des éléments des bibliothèques KiCad et attribution.

## État de validation

Il s'agit d'une **révision de conception destinée à un prototype**, pas d'une validation sur carte assemblée. Les erreurs de brochage, de réseau d'alimentation et de valeurs détaillées dans le rapport sont corrigées dans les fichiers natifs et dans le routage.

Le lecteur QR exact reste à identifier : le connecteur J1 du terminal transporte de l'UART logique 3,3 V. Pour un lecteur USB, utiliser le port USB du Pi et l'adaptateur approprié. Le buzzer retenu est le **CMI-1295-0585T actif 5 V**, compatible avec l'empreinte déjà présente ; le PS1720P02 passif cité dans le retour d'expérience n'est pas une substitution directe.

Avant une fabrication en série, les essais du tiroir, de sa diode D6, du convertisseur sous charge et de l'assemblage mécanique restent à effectuer. **D8 de la caisse fixe est montée au dessous du PCB.** Les modèles 3D standard nécessitent les bibliothèques 3D KiCad installées ; ils ne sont pas embarqués dans cette archive.

Le dossier logiciel, l'environnement Python, l'historique Git et les anciens fichiers de fabrication ne sont pas reproduits. Les documents et les mentions de l'auteur d'origine, Maxime RAMBARANE-BARAT, sont conservés.
