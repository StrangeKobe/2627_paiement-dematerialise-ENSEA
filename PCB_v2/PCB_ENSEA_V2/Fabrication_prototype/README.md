# Exports pour prototype V2

Exports régénérés avec KiCad 9.0.9 à partir des PCB présents dans `Hardware/`. Aucun ancien Gerber n'est repris.

Chaque carte utilise quatre couches cuivre, dans cet ordre : **F.Cu → In1.Cu (In1_PWR.Cu) → In2.Cu (In2_GND.Cu) → B.Cu**. Les perçages métallisés PTH et non métallisés NPTH sont fournis séparément en Excellon, en millimètres. Les Gerber et perçages utilisent les mêmes coordonnées absolues du PCB.

| Extension | Usage |
|---|---|
| `.gtl`, `.g1`, `.g2`, `.gbl` | Cuivres dessus, internes 1/2, dessous |
| `.gts`, `.gbs` | Vernis épargne dessus/dessous |
| `.gto`, `.gbo` | Sérigraphie dessus/dessous |
| `.gtp`, `.gbp` | Pâte à braser dessus/dessous |
| `.gm1` | Contour et découpes Edge.Cuts |
| `-PTH.drl`, `-NPTH.drl` | Perçages métallisés et non métallisés |
| `Placement_CMS.pos` | Position/rotation des CMS, faces indiquées par KiCad |

**D8 de la caisse fixe se trouve au verso.** Les vues `Apercus/*/Dessous.svg` montrent les coordonnées par transparence, sans miroir ; la face réelle doit être prise en compte à l'assemblage. Vérifier le sens cathode/anode des diodes dans les fichiers natifs et la sérigraphie.

La largeur de piste, l'empilage, l'épaisseur de cuivre, les tolérances de perçage et les ouvertures de masque doivent être acceptés par le fabricant choisi. Lire les points de qualification électrique et mécanique de `../MODIFICATIONS.md` avant de lancer une série.
