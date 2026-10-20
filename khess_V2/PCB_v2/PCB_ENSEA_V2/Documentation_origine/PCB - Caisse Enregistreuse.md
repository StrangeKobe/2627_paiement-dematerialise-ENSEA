# PCB - Caisse Enregistreuse
### Plateforme Paiement Dématérialisé RFID ENSEA - Documentation technique v1.0

> **Auteur :** Maxime RAMBARANE-BARAT - Stage ENSEA 2026 (18/05 au 28/08)  
> **Encadrants :** Nicolas Papazoglou, Céline Plassart

---

## 1. Contexte et rôle de ce PCB

Ce PCB est au cœur de la **caisse enregistreuse physique de la Kfet**. Il centralise l'alimentation, la conversion 12V → 5V, la commande du tiroir-caisse, et l'interface avec le Raspberry Pi 5 qui fait tourner l'application vendeur sur l'écran tactile.

Contrairement au module paiement dématérialisé, ce PCB est **alimenté en permanence par le secteur** via une alimentation externe 12V. Le vendeur utilise un interrupteur à bascule pour allumer et éteindre la caisse.

La caisse n'a **pas de lecteur RFID**, c'est le module terminal portable qui gère les transactions. Les deux communiquent via **WiFi** sur le réseau local ENSEA : le vendeur sélectionne les articles sur l'écran tactile, choisit le mode de paiement (cash ou RFID), et si RFID, la caisse envoie l'ordre au terminal via le backend.

---

## 2. Architecture générale

```
Alimentation externe 12V/2A AC/DC 
        │
        └──> DC Jack Barrel 5.5/2.1mm 
                    │
             [Interrupteur ON/OFF — câblé via J3 Conn_01x02]
                    │
             [Fusible F1]
                    │
        ┌───────────┴──────────────────────────┐
        │                                      │
   TPS54560BDDA (12V → 5V / 5A)           +12V direct
   + composants externes                       │
        │                              [MOSFET IRLZ44N]
        │                              + diode D6 (flyback)
        │                                      │
        ├──> Header 2x20 — Raspberry Pi 5      │
        │        │                      Connecteur J1 tiroir VEVOR
        │        ├──> GPIO18 → Ouv_Tiroir → Gate MOSFET Q1
        │        └──> GPIO23 → Buzzer_PWM → Gate SQ2303ES Q2
        │
        │
        ├──> LED verte — indicateur 5V
        ├──> LED orange — indicateur +3,3V Pi
        └──> LED orange — indicateur +12V
```

---

## 3. Composants - Description détaillée

---

### 3.1 Alimentation externe - PRO ELEC PELL0223

**Rôle :** fournir le 12V DC au PCB depuis le secteur 230V AC.

- Fabricant : PRO ELEC - référence Farnell **4161200**
- Sortie : **12V / 2A** - 24W
- Format : alimentation murale certifiée CE

> L'alimentation externe gère la conversion 230V → 12V dans son propre boîtier certifié. Ne jamais intégrer le 230V AC directement sur un PCB.

---

### 3.2 DC Jack Barrel - Cliff FC681465S 

**Rôle :** point d'entrée du 12V DC depuis l'alimentation externe sur le PCB.

- Format : **5.5/2.1mm** - standard industriel 
- Package : **SMD** (Barrel_Jack_Switch)
- 4 pins sur l'empreinte - la dernière (pin 4) est non connectée

**Câblage :**
- Pin 1 → +12V
- Pin 2 / Pin 3 → GND
- Pin 4 → NC

---

### 3.3 Filtrage entrée + Interrupteur + Fusible

**Condensateurs de filtrage entrée :**

Placés directement après le DC Jack pour filtrer les parasites et absorber les appels de courant au démarrage.

| Réf. | Valeur | Rôle |
|------|--------|------|
| C9 | 220µF | Filtrage basse fréquence entrée |
| C11 | 220µF | Filtrage basse fréquence entrée |
| C12 | 100n | Filtrage haute fréquence entrée |

**Interrupteur à bascule :**

Allume et éteint la caisse sans débrancher l'alimentation. Il coupe le 12V en amont de tout le reste du PCB, tout s'éteint en une bascule.

```
DC Jack (+12V) → condensateurs filtrage → Conn_01x02 pin 1 (Interrupteur +)
                                                      ↓
                                          Conn_01x02 pin 2 (Interrupteur −) → Fusible → TPS54560BDDA
```

> ⚠️ L'interrupteur coupe l'alimentation sans shutdown logiciel. Configurer le système de fichiers du Pi en **read-only (overlayfs)** via `raspi-config` pour protéger la carte SD contre les coupures brutales.

**Fusible F1 :**

Protection contre les surintensités - placé immédiatement après l'interrupteur, avant le régulateur.

---

### 3.4 Régulateur TPS54560BDDA - 12V → 5V / 5A 

**Rôle :** convertir le 12V DC en 5V stable pour alimenter le Raspberry Pi 5, l'écran HDMI, et les autres éléments du PCB.

Le TPS54560B est un régulateur abaisseur (buck) 60V, 5A avec MOSFET haute tension intégré. Il fonctionne en mode pulse-skip (Eco-mode) à faible charge pour minimiser la consommation, et la fréquence de découpage est ajustable de 100 kHz à 2,5 MHz. La référence de tension interne est de 0,8V à 1% de précision.

**LEDs indicateurs VOUT 5V :**
- D5 (Green LED) + R14 (5k) → indicateur VOUT 5V présent
- D1 (Green LED) + R3 (5k) → indicateur +3,3V Pi présent
- D4 (Amber LED) + R6 (5k) → indicateur +3,3V rail
- D3 (Amber LED) + R8 (5k) → indicateur +12V présent

---

### 3.5 Raspberry Pi 5 - Header 2x20

**Rôle :** connecteur qui reçoit le Raspberry Pi 5 directement sur le PCB. Le Pi s'enfiche dessus et récupère le 5V ainsi que toutes ses connexions GPIO.

**Brochage GPIO utilisé :**

| GPIO | Pin physique | Net KiCad | Fonction |
|------|-------------|-----------|----------|
| GPIO18 | 12 | Ouv_Tiroir | Commande Gate MOSFET Q1 → ouverture tiroir |
| GPIO23 | 16 | Buzzer_PWM | Commande Gate SQ2303ES Q2 → buzzer |

---

### 3.6 MOSFET SQ2310ES-T1_BE3 - Commande tiroir-caisse

**Rôle :** interrupteur de puissance commandant l'ouverture du tiroir-caisse VEVOR. Quand le vendeur appuie sur "Ouvrir le tiroir", GPIO18 passe LOW → le MOSFET laisse passer le 12V → le solénoïde reçoit l'impulsion → le tiroir s'ouvre.

**Pourquoi le SQ2310ES :** le SQ2310ES permet de bien contenir le courant retour instantané générer par la caisse 

> ⚠️ **LOGIQUE INVERSÉE** : le SQ2310ES est un P-Channel MOSFET. **GPIO LOW = tiroir actif, GPIO HIGH = tiroir coupé.** Adapter le code en conséquence.

**Diode flyback D6 :**

Le solénoïde du tiroir est une charge inductive. À la coupure du courant, la bobine génère une surtension inverse pouvant détruire le MOSFET. La diode D6 en antiparallèle court-circuite ce pic 

---

### 3.7 Buzzer actif + MOSFET SQ2310ES

**Rôle :** émettre un bip sonore à l'allumage de la caisse pour confirmer que le système est prêt.


La caisse dispose d'un écran tactile qui fournit tout le feedback visuel nécessaire pendant les transactions. Le buzzer se limite à la confirmation de démarrage.

---

## 4. Mapping GPIO complet

| GPIO | Pin physique | Net KiCad | Fonction |
|------|-------------|-----------|----------|
| GPIO18 | 12 | Ouv_Tiroir | Gate SQ2310ES - ouverture tiroir-caisse |
| GPIO23 | 16 | Buzzer_PWM | Gate SQ2310ES - buzzer démarrage |

---

## 5. Flux d'ouverture du tiroir

```
Vendeur appuie sur "Ouvrir le tiroir" (interface écran tactile)
        │
        └──> Code Python : GPIO18 = HIGH pendant 150ms
                    │
             Gate MOSFET SQ2310ES activée (VGS > 2V)
                    │
             12V traverse Drain → Source → pin 2
                    │
             Solénoïde tiroir VEVOR reçoit l'impulsion
                    │
             Tiroir s'ouvre mécaniquement
                    │
             GPIO18 = LOW → MOSFET se ferme
                    │
             Diode D6 absorbe le pic inductif de la bobine
```

---

## 6. Notes pour la reproduction

- **Alimentation externe 12V/2A** - éviter d'intégrer le 230V AC sur le PCB.
- **Identifier les fils du tiroir VEVOR au multimètre** avant câblage - mesurer 10 à 50Ω entre les deux fils confirme le solénoïde.
- **Configurer overlayfs** sur la carte SD via `raspi-config` pour protéger contre les coupures brutales via l'interrupteur.
- **Câble mini HDMI → HDMI externe** entre Pi 5 et écran, ne passe pas par le PCB.
- **SQ2303ES logique inversée** - LOW = buzzer actif.

---

*Documentation rédigée par Maxime RAMBARANE-BARAT — Stage ENSEA 2026*  
*Dernière mise à jour : juin 2026*