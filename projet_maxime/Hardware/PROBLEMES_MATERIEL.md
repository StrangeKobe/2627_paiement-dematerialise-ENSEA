# Problèmes matériel et PCB - Retour d'expérience

Ce document recense tous les défauts matériels rencontrés sur les deux PCB
(caisse Raspberry Pi 5 et terminal Raspberry Pi Zero 2W) pendant le stage.
Il est destiné à la personne qui reprendra le projet, notamment pour la
conception de la **V2 des cartes**.

Chaque entrée suit le format : **symptôme observé → cause identifiée → potentielle correction**.

---

## Table des matières

1. [Empreinte SOT-23 des MOSFET (défaut critique)](#1-empreinte-sot-23-des-mosfet--défaut-critique)
2. [Interrupteur mal placé sur le rail 12 V](#2-interrupteur-mal-placé-sur-le-rail-12-v)
3. [Résistance R12 du diviseur UVLO (90R9 au lieu de 90k9)](#3-résistance-r12-du-diviseur-uvlo)
4. [Buzzer non fonctionnel](#4-buzzer-non-fonctionnel)
5. [Lecteur QR code incompatible (UART vs USB)](#5-lecteur-qr-code-incompatible)
6. [Mauvaises soudures récurrentes](#6-mauvaises-soudures-récurrentes)
7. [Récapitulatif des corrections V2](#7-récapitulatif-des-corrections-pour-la-v2)

---

## 1. Empreinte SOT-23 des MOSFET - défaut critique

**C'est le défaut le plus grave. Il a détruit plusieurs MOSFET.**

### Symptôme
- Le tiroir-caisse ne s'ouvre pas malgré une commande correcte.
- Mesures : au repos Vgs = 0 V et Vds = 12 V (cohérent), mais pendant
  l'impulsion Vgs monte à 3,3 V **sans que Vds ne chute**, le MOSFET ne commute pas.
- Trois MOSFET Q3 successivement grillés (mesure Gate-Drain à quelques kΩ
  au lieu de l'infini = oxyde de grille percé).

### Cause
L'empreinte KiCad utilisée pour le SOT-23 **ne correspond pas au brochage réel**
du SQ2310ES. D'après la datasheet Vishay officielle :

| Pin physique | Fonction réelle (datasheet) | Ce que le PCB envoie |
|---|---|---|
| 1 | Gate | `Net-(D6-A)` = Drain |
| 2 | Source | `Net-(Q3-G)` = Gate |
| 3 | Drain | `GND` = Source |

Les trois signaux sont **décalés d'un cran** (permutation circulaire).
Conséquence directe : le Gate recevait le +12 V du solénoïde, très au-delà de
la limite absolue **VGS = ±8 V** de la datasheet → percement immédiat de l'oxyde.

### Correction (V2)
Refaire l'empreinte KiCad avec le mapping correct **Gate = 1, Source = 2, Drain = 3**.
Vérifier systématiquement toute empreinte de transistor contre la datasheet du
fabricant avant routage (ne jamais se fier au nom générique de l'empreinte).

### Attention
Le circuit **buzzer (Q1)** utilise le même composant et très probablement la
même empreinte erronée. Corriger les deux.

---

## 2. Interrupteur mal placé sur le rail 12 V

### Symptôme
- Même interrupteur ouvert, le tiroir peut toujours s'ouvrir et la LED ambre
  reste allumée.
- Le rail 12 V du solénoïde reste sous tension en permanence dès que le jack
  est branché.

### Cause
L'interrupteur (J3, `Conn_01x02`) est câblé **entre le rail +12 V et le
régulateur buck TPS54560 uniquement**. Il ne coupe donc que l'alimentation du
5 V (le Pi). Le net `+12V` qui alimente le solénoïde et la LED ambre est
prélevé **en amont** de l'interrupteur.

### Conséquence indirecte (dangereuse)
Cette erreur a rendu les manipulations dangereuses : on travaille sur le circuit
tiroir en croyant l'avoir mis hors tension via l'interrupteur, alors que le
12 V est toujours présent sur le Drain du MOSFET. C'est un facteur aggravant
dans la destruction des MOSFET.

### Correction (V2)
Deux options :
1. **Recommandée** : déplacer l'interrupteur **en amont de tout le rail 12 V**,
   juste après le jack J2, pour qu'il coupe l'ensemble de la carte.
2. Créer deux nets distincts `+12V_RAW` (avant interrupteur) et `+12V_SW`
   (après), et alimenter le solénoïde depuis `+12V_SW`.

### Règle de sécurité en attendant
Pour toute intervention sur le circuit tiroir, **débrancher le jack**, pas
seulement basculer l'interrupteur.

---

## 3. Résistance R12 du diviseur UVLO

### Symptôme
- Le régulateur buck 12 V → 5 V ne démarre pas.
- 12 V corrects en entrée (VIN) mais **0 V sur la broche EN** du TPS54560.
- Mesure 0 Ω entre EN et GND.

### Cause
Erreur de valeur sur R12 du diviseur UVLO (undervoltage lockout), saisie
comme **90R9 (= 90,9 Ω)** au lieu de **90k9 (= 90,9 kΩ)**.

Vérification par le calcul :
- Avec 90,9 Ω : `V_EN ≈ 12 × 90,9 / (442 000 + 90,9) ≈ 2,5 mV` → jamais assez
  pour dépasser le seuil de 1,2 V. Le buck ne démarre jamais.
- Avec 90,9 kΩ : `V_EN ≈ 12 × 90 900 / (442 000 + 90 900) ≈ 2,05 V` → au-dessus
  du seuil, le buck démarre.

A savoir que la valeur sur ce datasheet était erronée.

### Correction
Remplacer physiquement R12 par une **90,9 kΩ** (ou 91 kΩ standard E96).
**Corrigé et validé : le buck démarre, VOUT 5 V confirmé.**
Corriger aussi la valeur sur le schéma KiCad (`90R9` → `90k9`).

---


## 4. Buzzer non fonctionnel

### Symptôme
- Aucun son lors des tests, ni en tout-ou-rien ni en PWM.

### Éléments identifiés
- Le buzzer **PS1720P02** (ø17 mm, 70 dB) est un buzzer **piézo passif** :
  il ne sonne **que** s'il reçoit un signal carré (PWM), jamais en tension
  continue. Fréquence de résonance nominale **~2 kHz** pour ce modèle.
- Il ne doit **jamais** recevoir de tension DC (risque de dégradation de la
  résistance d'isolement, cf. datasheet).
- Le buzzer est **non polarisé** : pas de sens à respecter à la soudure.

### Cause probable
Le circuit buzzer (Q1) partage très probablement le **même défaut d'empreinte
SOT-23** que le tiroir (voir point 1), ce qui empêche le MOSFET de commuter et
donc le buzzer de recevoir son signal.

### À faire
1. Corriger l'empreinte du MOSFET Q1 (V2).
2. Piloter `Buzzer_PWM` à **~2 kHz** dans le firmware (pas une fréquence
   arbitraire), pour obtenir le son maximal.
3. Retester une fois l'empreinte corrigée.

### Note
La confirmation de paiement en caisse doit rester **visuelle (écran)** tant que
le buzzer n'est pas fonctionnel. Ne pas dépendre du signal sonore.

---

## 5. Lecteur QR code incompatible

### Symptôme
- Le lecteur de QR code ne communique pas avec le Pi.

### Cause
Le lecteur prévu dans le design devait sortir en **TTL série (UART)** sur les
GPIO 14/15 du Pi. Le module effectivement disponible **ne sort pas en TTL** :
il n'est pas compatible avec le câblage UART prévu.

### Correction
- Soit prévoir un modèle de lecteur avec **sortie TTL série** confirmée.
- Soit ajouter un **convertisseur d'interface** (selon l'interface réelle du
  lecteur : USB HID, RS232…).
- Vérifier l'interface **avant commande** sur la V2.

---


## 6. Mauvaises soudures récurrentes

Plusieurs pannes ont été causées ou aggravées par des soudures défectueuses.
À surveiller systématiquement :

- **Diode D6** (roue libre) : une soudure non connectée a laissé le Drain du
  MOSFET flottant, faussant tout le diagnostic. Toujours vérifier D6 en
  continuité avant de conclure sur le MOSFET.
- **Réflexe** : après chaque soudure sur un composant critique, vérifier au
  multimètre (continuité + valeur attendue) **avant** de remettre sous tension.

---

## 7. Récapitulatif des corrections pour la V2

Liste consolidée des modifications à apporter au PCB :

| # | Correction | Priorité |
|---|---|---|
| 1 | Empreinte SOT-23 corrigée (Gate=1, Source=2, Drain=3) sur Q1 et Q3 | **Critique** |
| 2 | Interrupteur déplacé en amont de tout le rail 12 V (après le jack) | **Critique** |
| 3 | R12 : `90R9` → `90k9` (90,9 kΩ) sur le schéma | Haute |
| 4 | R15 et R4 : 1 kΩ → 10 kΩ (éviter le diviseur par 2) | Haute |
| 5 | Ajout Zener 12 V ou 15 V entre Gate et Source de Q1 et Q3 (protection pics) | Haute |
| 6 | Lecteur QR : modèle TTL série confirmé, ou convertisseur | Haute |
| 7 | Vérifier le dimensionnement / la soudure de la diode de roue libre D6 | Moyenne |
| 8 | Ajouter le MPN (référence fabricant) sur tous les composants de la BOM | Moyenne |

### Piste d'amélioration de fond
Le pilotage des MOSFET par simple GPIO 3,3 V avec pull-down est fragile.
Pour la V2, envisager un **driver de MOSFET dédié** (type IR2104 ou équivalent)
pour le solénoïde et le buzzer, qui garantirait une commande de grille propre
et une protection intégrée.

---

*Document rédigé en fin de stage - Maxime RAMBARANE-BARAT.*
