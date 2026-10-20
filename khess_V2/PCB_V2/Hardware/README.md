# Hardware — projets corrigés V2

Les deux projets sont indépendants et possèdent leurs propres bibliothèques locales. Conserver tous les fichiers de chaque dossier ensemble, puis ouvrir le `.kicad_pro` avec KiCad 9. Le schéma de la caisse comporte une feuille hiérarchique `Power_supply.kicad_sch` : conserver ce nom et son emplacement.

## Alimentation et commandes

| Carte / signal | GPIO BCM | Broche physique du Pi | Remarque |
|---|---:|---:|---|
| Caisse : Ouv_Tiroir | 18 | 12 | Q3, actif HIGH, impulsion limitée |
| Caisse : Buzzer_PWM | 23 | 16 | Q1, actif HIGH ; nom de net historique |
| Terminal : Buzzer_PWM | **19** | **35** | Q1, actif HIGH ; pas GPIO18 |
| Terminal : RFID_NSS | **8 / CE0** | **24** | Pas CE1 / broche26 |
| Terminal : OLED_CS | 7 / CE1 | 26 | Brochage existant conservé |
| Terminal : sortie UART du Pi | 14 / TXD0 | 8 | Vers l'entrée RX du lecteur |
| Terminal : entrée UART du Pi | 15 / RXD0 | 10 | Depuis la sortie TX du lecteur |

Ces affectations proviennent des schémas et netlists livrés. Le logiciel n'est pas modifié dans cette archive : vérifier sa configuration GPIO avec ce tableau et initialiser les commandes MOSFET à LOW au démarrage.

### Caisse fixe

- J2 : entrée jack 12 V ; J3 : interrupteur externe entre +12V_RAW (broche1) et +12V_SW (broche2).
- J1 : tiroir, broche1 = +12V_SW, broche2 = drain Q3 / anode D6.
- D6 : cathode sur +12V_SW, anode sur le drain. Contrôler la soudure et le courant réel du solénoïde.
- D8 protège la grille de Q1, **au dessous du PCB** ; D9 protège Q3, au dessus.
- La source d'alimentation 12 V / 2 A mentionnée dans la documentation initiale limite la puissance disponible ; qualifier le fonctionnement du Pi 5 sous sa charge réelle.

### Terminal mobile

J1, connecteur QR à 4 broches :

| Broche | Signal | Sens |
|---:|---|---|
| 1 | +5 V | Alimentation du lecteur, vérifier sa consommation |
| 2 | GND | Masse commune |
| 3 | Lecteur_QR_RX | Pi TX GPIO14 → lecteur RX |
| 4 | Lecteur_QR_TX | Lecteur TX → Pi RX GPIO15 |

Les signaux des broches 3/4 doivent être compatibles **logique 3,3 V**. L'alimentation 5 V de la broche1 ne signifie pas que les GPIO tolèrent 5 V. Ce connecteur n'est ni USB ni RS232. Un lecteur USB se branche sur le port USB du Pi avec la connectique appropriée.

L'alimentation du terminal reste celle du montage Pi Zero 2 W / HAT X306. Cette révision ne modifie pas le chargeur de batterie externe.

### Buzzer des deux cartes

La V2 retient le **CMI-1295-0585T**, buzzer magnétique actif 5 V, polarisé, boîtier 12 × 9,5 mm et entraxe 7,6 mm. Un niveau HIGH sur la commande MOSFET l'alimente ; LOW l'arrête. Le nom historique `Buzzer_PWM` est conservé pour éviter une modification inutile de l'interface logicielle, mais ne prescrit pas un PWM audio.

Le **PS1720P02 passif** cité dans le retour d'expérience V1 est un autre composant : ne pas le monter comme équivalent direct. Voir les limites et les essais restants dans `../MODIFICATIONS.md`.

## Bibliothèques et fabrication

Les empreintes locales sont des copies de la géométrie embarquée dans chaque carte ; les noms correspondent aux références (Q1, D8, etc.). Les symboles locaux dérivent des symboles embarqués d'origine et des bibliothèques KiCad. Leur présence empêche une mise à jour depuis un ancien symbole NMOS incorrect.

Les cartes conservent leurs **quatre couches cuivre**, leur contour et leurs découpes. Les Gerber à utiliser pour examiner le prototype sont dans `../Fabrication_prototype/`. Ne pas mélanger ces exports avec ceux de la V1. Les modèles 3D standard restent référencés par la variable KiCad `KICAD9_3DMODEL_DIR` et sont facultatifs pour éditer les schémas et PCB.
