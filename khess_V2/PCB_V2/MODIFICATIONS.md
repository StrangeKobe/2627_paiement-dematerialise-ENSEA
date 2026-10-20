# Liste des modifications — V2 du 20 octobre 2026

## Corrections réalisées

| Élément | Carte | Modification appliquée | Motif |
|---|---|---|---|
| Q1, Q3 | Caisse fixe | Symbole SQ2310ES corrigé : **1 = Gate, 2 = Source, 3 = Drain** ; pistes et vias correspondants reroutés. | Le symbole NMOS de simulation utilisait D=1, G=2, S=3. L'empreinte physique SOT-23 garde sa numérotation standard. |
| Q1 | Terminal | Même correction du symbole et du routage. | Même erreur de brochage que sur la caisse. |
| Alimentation et J3 | Caisse fixe | Séparation des réseaux **+12V_RAW** et **+12V_SW** ; chemin d'entrée refait sur la couche interne d'alimentation. | L'interrupteur commande maintenant le buck, le tiroir, la LED 12 V et les condensateurs d'entrée. |
| R12 | Caisse fixe | **90R9 → 90k9** ; MPN `RC0603FR-0790K9L`. | Rétablissement du diviseur d'activation du convertisseur. |
| R4, R15 | Caisse fixe | **1 kΩ → 10 kΩ**, MPN `RC0603FR-0710KL`. | Les résistances de rappel ne divisent plus par deux la commande GPIO avec les résistances série de 1 kΩ. |
| R3 | Terminal | **1 kΩ → 10 kΩ**, même MPN. | Correction du même diviseur sur le buzzer du terminal. |
| D8, D9 | Caisse fixe | Ajout de Zener **BZT52H-C5V1**, 5,1 V, SOD-123F. D8 protège Q1 ; D9 protège Q3. Cathode à la grille, anode à GND/source. | Protection de la grille. D8 est placée sur **B.Cu**, D9 sur F.Cu. |
| D8 | Terminal | Même Zener 5,1 V sur Q1, sur F.Cu. | Protection de la grille du buzzer. |
| C15 | Caisse fixe | **4u7 → 4n7** ; MPN `CC0805JRNPO9BN472`, C0G 5 %, 50 V, 0805. | Correction supplémentaire : le réseau de compensation repris du schéma TI utilise 4 700 pF avec 16,9 kΩ et 47 pF. La valeur initiale était 1 000 fois supérieure. |
| D2 | Caisse fixe | Valeur affichée **B650C → B560C** ; MPN `B560C-13-F`. | Alignement de la désignation avec la diode du montage et la référence du convertisseur. Brochage de diode conservé. |
| Résistances de LED | Deux cartes | **5 kΩ → 4,99 kΩ**, MPN `RC0603FR-074K99L`. Caisse : R3/R6/R8/R14 ; terminal : R4/R6. | Choix d'une valeur normalisée avec une référence fabricant explicite ; écart de −0,2 %. |
| BZ1 | Deux cartes | Valeur explicite **CMI-1295-0585T**, fiche fabricant renseignée ; fonctionnement actif 5 V documenté. | Résolution de la contradiction entre la BOM KiCad et le buzzer passif PS1720P02 décrit dans le retour d'expérience. |
| Nomenclature | Deux cartes | MPN/fabricants complétés ; préfixes de distributeurs retirés ; références des connecteurs distinguées des modules externes. | Permettre une nomenclature exploitable. Les nouvelles sélections et les références reprises sont distinguées dans NOMENCLATURE.md. |
| Bibliothèques | Deux cartes | Symboles et empreintes fournis localement avec `sym-lib-table` et `fp-lib-table`, chemins relatifs au projet. | Ouverture et modification sans les bibliothèques personnelles manquantes de l'auteur. Les symboles MOSFET corrigés sont conservés. |
| Éléments non achetés | Deux cartes | Points de test et trous exclus de la BOM ; contours auxiliaires du terminal nommés EDGE1/EDGE2 et déclarés propres au PCB. | Éviter les achats fictifs et les écarts de synchronisation. Les contours mécaniques sont conservés. |
| Finition et contrôle | Deux cartes | Vias devenus inutiles retirés, sérigraphie débordante/chevauchante corrigée, marquage V2, plans de cuivre recalculés. | DRC sans anomalie selon les règles existantes. |
| Livrables | Deux cartes | Netlists, rapports ERC/DRC, nomenclature, aperçus, Gerber et perçages régénérés. | Tous les exports correspondent à la V2 livrée. |

## Choix techniques importants

### Protection de grille

La proposition « Zener 12 V ou 15 V » du retour d'expérience n'est pas reprise : la limite absolue du SQ2310ES est **VGS = ±8 V**. Une Zener nominale de **5,1 V** a été choisie. Elle complète le brochage correct et les diodes de roue libre ; elle ne constitue pas une protection contre toute erreur de câblage ou tout transitoire. La limitation réelle dépend du courant et de la forme du pic.

Le SQ2310ES est un **MOSFET N en commutation côté masse**, actif lorsque le GPIO est à l'état HIGH. Les mentions de transistor P, de SQ2303ES, d'IRLZ44N ou de logique inversée dans certains documents V1 ne décrivent pas le montage livré. Avec 1 kΩ en série et 10 kΩ de rappel, la grille reçoit environ **3,0 V pour 3,3 V GPIO** en régime établi. La fiche Vishay caractérise ce transistor à VGS = 2,5 V. Aucun driver supplémentaire n'a été ajouté.

### Coupure 12 V

La netlist finale vérifie que `+12V_RAW` ne relie que **J2.1 et J3.1**. `+12V_SW` part de **J3.2** et alimente notamment **U5.2, J1.1, D6.1, R8.1 et TP1.1**. Les indicateurs PWR_FLAG du schéma ont été ajustés pour décrire les nouvelles alimentations sans conflits ERC.

Le tronçon principal RAW est routé en largeur **1,5 mm** sur In1.Cu ; les connexions aux groupes de vias du jack sont reprises. Les autres circuits conservent leur affectation initiale. La coupure électrique du 12 V ne remplace pas un arrêt logiciel du Raspberry Pi et n'empêche pas une éventuelle réalimentation par un périphérique externe.

### Compensation du convertisseur

La correction de C15 est fondée sur la comparaison du montage avec la figure 32 et la section 8.2.2.11 du TPS54560B : même résistance de compensation de 16,9 kΩ, condensateur parallèle de 47 pF, diviseur de sortie et inductance de 7,2 µH. **L'interprétation est que 4u7 était une erreur d'unité lors de la reprise du circuit de référence.** C15 devient donc 4,7 nF. La réponse dynamique du convertisseur devra encore être mesurée avec les condensateurs réellement montés et la charge Pi.

## Points nécessitant encore le matériel réel

| Sujet | État de la V2 et vérification restante |
|---|---|
| Lecteur QR | J1 du terminal reste une interface UART 3,3 V, avec alimentation 5 V sur une broche distincte. L'interface et le modèle exacts du lecteur disponible ne sont pas établis. Un lecteur USB utilise l'USB du Pi ; un lecteur RS232 exige une conversion adaptée. Aucun convertisseur arbitraire n'est ajouté. |
| Buzzer | Monter le CMI-1295-0585T actif, polarisé, diamètre 12 mm et entraxe 7,6 mm. Son oscillateur interne permet une commande marche/arrêt ; ne pas lui appliquer systématiquement le PWM 2 kHz prévu pour le PS1720P02. Pour conserver ce dernier, une adaptation mécanique et une commande appropriée restent à concevoir. |
| D6 et tiroir | La polarité et la continuité électrique sont vérifiées dans les fichiers. Le courant, l'inductance et la durée d'impulsion du solénoïde ne sont pas fournis : tenue de D6 SS19, échauffement de Q3 et limitation des surtensions restent à mesurer. Une soudure défectueuse ne peut pas être corrigée dans un fichier PCB. |
| Alimentation | La documentation V1 cite 12 V / 2 A, soit 24 W. Cela ne permet pas de garantir 5 V / 5 A en sortie, en plus du tiroir et des pertes. La mention « 5 A » du composant TPS54560B ne constitue pas le courant garanti du système. |
| Protection d'entrée | Aucun F1 n'existe dans les fichiers sources, contrairement au schéma bloc du document V1. Cette V2 ne prétend pas en ajouter ; une protection d'entrée doit être dimensionnée avec le budget de courant retenu. |
| Assemblage | Vérifier la hauteur des connecteurs, le montage Pi/HAT/boîtier et les faisceaux. D8 de la caisse est au verso. Les nouvelles références de connecteurs sont des sélections compatibles avec les empreintes nominales, à contrôler avec les câbles réels. |

## Validation effectuée

- KiCad **9.0.9** : ERC des deux schémas, DRC des deux cartes, contrôle de parité schéma/PCB et contrôle de toutes les pistes.
- Résultat : **0 erreur, 0 avertissement, 0 liaison non routée, 0 écart schéma/PCB** dans les rapports livrés.
- Comparaison des netlists V1/V2 : toutes les connexions existantes correspondent aux changements prévus ; aucune modification de connexion supplémentaire détectée.
- Comparaison directe des nets des pastilles au schéma : **170 pastilles sur la caisse**, **98 sur le terminal**.
- Les paramètres et sévérités de contrôle du projet d'origine sont **inchangés** ; aucune exclusion ajoutée. La classe de nets par défaut impose une isolation de 0,2 mm. Ces résultats ne constituent pas une qualification des règles d'un fabricant particulier.
- Contrôle visuel des schémas et des exports de couches ; bibliothèque locale cohérente avec les empreintes embarquées.

À réaliser sur prototype : continuité hors tension, polarités, montée du 5 V avec alimentation limitée en courant, essais en charge/transitoires et thermiques, vérification des commandes au démarrage, essais courts du tiroir, puis tests RFID/OLED/QR et buzzer.

## Sources de référence

- Retour d'expérience et projets KiCad de l'archive fournie, conservés pour la partie documentaire dans `Documentation_origine/`.
- Vishay, **SQ2310ES**, brochage et VGS : https://www.vishay.com/docs/67036/sq2310es.pdf
- Nexperia, **BZT52H series**, Zener 5,1 V : https://assets.nexperia.com/documents/data-sheet/BZT52H_SER.pdf
- Texas Instruments, **TPS54560B**, schéma 5 V et compensation, figure 32 / section 8.2.2.11 : https://www.ti.com/lit/ds/symlink/tps54560b.pdf
- Yageo, **CC0805JRNPO9BN472**, 4 700 pF C0G 0805 : https://yageogroup.com/download/specsheet/CC0805JRNPO9BN472
- Yageo, **RC0603FR-074K99L** : https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-074K99L
- Same Sky, **CMI-1295-0585T** : https://www.sameskydevices.com/product/audio/buzzers/audio-indicators/cmi-1295-0585t
- KiCad, commandes de validation et d'export : https://docs.kicad.org/9.0/en/cli/cli.html
