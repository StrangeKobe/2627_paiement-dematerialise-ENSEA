# PCB — Module de Paiement Dématérialisé RFID
### Plateforme Paiement Dématérialisé RFID ENSEA - Documentation technique v1.0

> **Auteur :** Maxime RAMBARANE-BARAT - Stage ENSEA 2026 (18/05 au 28/08)  
> **Encadrants :** Nicolas Papazoglou, Céline Plassart

---

## 1. Contexte et rôle de ce PCB

Ce module est le **terminal de paiement portable** du système Paiement Dématérialisé de l'ENSEA. Il permet à n'importe quelle association (BDE, Kfet, Epicuria…) d'encaisser un paiement RFID ou QR code sans avoir besoin de la caisse physique fixe.

Le fonctionnement est simple : le vendeur ouvre l'application sur son téléphone, saisit le montant et valide. Le montant est envoyé au boîtier via WiFi. L'écran OLED affiche alors le montant et invite l'étudiant à poser sa carte étudiante RFID ou à présenter un QR code. Le débit est effectué instantanément depuis le portefeuille virtuel de l'étudiant.

> Ce module fonctionne de manière **totalement autonome**, aucune connexion filaire requise, communication uniquement via WiFi sur le réseau local ENSEA.


---

## 2. Architecture générale

```
Chargeur USB-C 5V/3A (prise murale)
        │
        └──> X306 UPS HAT (via USB-C)
                │
                ├──pogo pins──> Raspberry Pi Zero 2W
                │                       │
                │               SPI0 ───┤──> RC522 (lecteur RFID)
                │               I2C ────┤──> OLED SSD1327 128×128
                │               UART ───┤──> Lecteur QR code
                │               GPIO ───┤──> Buzzer actif (via SQ2310ES)
                │
                └──> Batterie 18650
```

> Le X306 dispose d'un capteur de luminosité BH1750 intégré, inutile d'en ajouter un séparé.

---

## 3. Composants - Description détaillée

---

### 3.1 Raspberry Pi Zero 2W

**Rôle :** cerveau du module. Il orchestre toutes les interactions : écoute les ordres via WiFi, pilote l'écran OLED, attend le scan RFID ou QR code, envoie la confirmation de paiement au backend, et gère le buzzer.

**Pourquoi ce modèle :** le Zero 2W est le plus compact des Raspberry Pi tout en embarquant le WiFi natif, indispensable pour communiquer avec le backend sans câble. Sa connectique GPIO 2×20 standard permet d'y connecter tous les périphériques nécessaires.

#### Brochage utilisé

| GPIO | Pin physique | Net KiCad | Fonction |
|------|-------------|-----------|----------|
| GPIO2 (SDA) | 3 | OLED_SDA | I2C — OLED SSD1327 |
| GPIO3 (SCL) | 5 | OLED_SCL | I2C — OLED SSD1327 |
| GPIO7 (CE1) | 26 | RFID_NSS | SPI0 CE1 — RC522 Chip Select |
| GPIO9 (MISO) | 21 | RFID_MISO | SPI0 — RC522 |
| GPIO10 (MOSI) | 19 | RFID_MOSI | SPI0 — RC522 |
| GPIO11 (SCLK) | 23 | RFID_SCK | SPI0 — RC522 |
| GPIO14 (TXD) | 8 | Lecteur_QR_RX | UART TX → RX lecteur QR |
| GPIO15 (RXD) | 10 | Lecteur_QR_TX | UART RX ← TX lecteur QR |
| GPIO18 | 12 | Buzzer_PWM | Buzzer via SQ2303ES P-MOSFET |
| GPIO24 | 18 | RFID_IRQ | RC522 IRQ (interruption lecture carte) |
| GPIO25 | 22 | RFID_RST | RC522 RST (reset) |
| GPIO26 | 37 | OLED_RST | Reset OLED (optionnel en I2C) |

---

### 3.2 Module RFID RC522 

**Rôle :** lecteur de carte étudiante RFID. Quand un étudiant pose sa carte sur le module, le RC522 lit l'UID (identifiant unique) de la carte et le transmet au Pi via SPI. Le Pi envoie ensuite cet UID au backend pour effectuer le débit.

- Fréquence : **13,56 MHz** - protocole Mifare
- Interface : **SPI 3,3V** - compatible direct avec le Pi Zero 2W
- Dimensions module : 60 × 40 × 8 mm
- Livré avec une carte RFID et un badge porte-clé de test

> Ce module **ne supporte PAS** la communication NFC avec les téléphones (mode HCE). Le paiement par téléphone passe par le lecteur QR code.

#### Brochage RC522 → Raspberry Pi

| Pin RC522 | Nom signal | Net KiCad | GPIO Pi | Pin physique |
|-----------|-----------|-----------|---------|-------------|
| 1 (VCC) | +3,3V | — | 3,3V | 1 |
| 2 (RST) | Reset | RFID_RST | GPIO25 | 22 |
| 3 (GND) | Masse | GND | GND | 6 |
| 4 (IRQ) | Interruption | RFID_IRQ | GPIO24 | 18 |
| 5 (MISO) | SPI MISO | RFID_MISO | GPIO9 | 21 |
| 6 (MOSI) | SPI MOSI | RFID_MOSI | GPIO10 | 19 |
| 7 (SCK) | SPI Clock | RFID_SCK | GPIO11 | 23 |
| 8 (NSS/SDA) | Chip Select | RFID_NSS | GPIO7 (CE1) | 26 |

---

### 3.3 Écran OLED SSD1327 - 128×128 pixels 1,5"

**Rôle :** afficher les instructions et le montant à payer. Le passage du Grove LCD 16×2 à l'OLED SSD1327 apporte une résolution bien supérieure (128×128 vs 16 caractères par ligne) et la possibilité d'afficher des icônes ou des graphiques simples.

Exemples d'affichage :
```
// En attente :          // Montant affiché :
┌────────────────┐       ┌────────────────┐
│   KFET ENSEA   │       │  Total: 4.50€  │
│  Posez carte   │       │ Posez la carte │
│   ou QR Code   │       │                │
└────────────────┘       └────────────────┘
```

- Contrôleur : **SSD1327**
- Résolution : **128×128 pixels**, 16 niveaux de gris
- Interface retenue : **I2C** (adresse `0x3C`)
- Alimentation : **3,3V**
- Pins I2C : SDA → GPIO2 (pin 3), SCL → GPIO3 (pin 5)

> ⚠️ L'écran dispose également de pins SPI (`OLED_DC`, `OLED_CS`, `OLED_RST`) visibles sur le schéma KiCad. Ces pins sont présentes **à titre de référence uniquement**, elles ne sont pas câblées activement en mode I2C.

#### Mapping I2C - vérification des conflits d'adresses

| Composant | Adresse I2C | Conflit ? |
|-----------|-------------|-----------|
| OLED SSD1327 | 0x3C | Non |

Un seul composant sur le bus I2C - aucun risque de conflit.

---

### 3.4 Lecteur QR code - Interface UART

**Rôle :** permettre aux étudiants de payer via un QR code dynamique affiché sur leur téléphone, en complément du RFID. Le QR code change à chaque transaction, il ne peut pas être copié ou rejoué.

Le lecteur QR code communique via **UART (liaison série)** avec le Pi. Quand un code est scanné, le module envoie la donnée décodée sur sa pin TX, que le Pi reçoit sur son RX (GPIO15).

#### Brochage - Connecteur J1 (Conn_01x04)

| Pin connecteur | Signal | Net KiCad | GPIO Pi | Pin physique |
|----------------|--------|-----------|---------|-------------|
| 1 | +5V | +5V | 5V | 2 |
| 2 | GND | GND | GND | 6 |
| 3 | RX module | Lecteur_QR_RX | GPIO14 (TXD) | 8 |
| 4 | TX module | Lecteur_QR_TX | GPIO15 (RXD) | 10 |


> Le lecteur QR utilise le port UART matériel du Pi (`ttyS0`). Dans `raspi-config → Interface Options → Serial Port` : **désactiver le login shell**, **activer le port matériel**.

---

### 3.5 Buzzer actif + MOSFET SQ2310ES 

**Rôle :** émettre un bip sonore à l'allumage de la caisse pour confirmer que le système est prêt.


La caisse dispose d'un écran tactile qui fournit tout le feedback visuel nécessaire pendant les transactions. Le buzzer se limite à la confirmation de démarrage.

#### Schéma de principe

> R7 (1kΩ) limite le courant de grille. R3 (1kΩ) tire la grille vers GND quand le GPIO est en haute impédance au démarrage du Pi, évitant un déclenchement intempestif du buzzer au boot.

---

### 3.6 Geekworm X306 UPS HAT

**Rôle :** module d'alimentation avec batterie de secours. Il alimente le Raspberry Pi via des pogo pins et maintient le système sous tension même si l'alimentation secteur est coupée.

- Spécifiquement conçu pour le Pi Zero 2W, fixation directe sans câble via pogo pins
- Entrée USB-C 5,1V - sortie stable 5,1V au Pi
- Batterie : 1× 18650 Li-ion 3,7V
- Lecture du niveau de batterie via le firmware du X306 

---

## 4. Flux de paiement complet

```
1. Vendeur saisit le montant sur l'app téléphone
        │
        └──> Backend reçoit l'ordre via HTTPS
                │
                └──> WebSocket/polling ──> Pi Zero 2W (WiFi)
                                                │
                                    OLED affiche le montant
                                    "Posez carte ou QR code"
                                                │
                              ┌─────────────────┴──────────────────┐
                           RFID                                  QR Code
                              │                                      │
                    Étudiant pose carte                  Étudiant montre QR
                              │                                      │
                    RC522 lit l'UID                    Lecteur QR décode
                              │                                      │
                              └──────────────┬───────────────────────┘
                                             │
                                  Pi envoie données au backend
                                             │
                                  Backend vérifie le solde
                                             │
                          ┌──────────────────┴──────────────────────┐
                       Solde OK                              Solde insuffisant
                          │                                          │
                    Débit effectué                       OLED : "Solde insuffisant"
                    OLED : "Paiement OK"                 Buzzer : 2 bips courts
                    Buzzer : 1 bip long
```

---


*Documentation rédigée par Maxime RAMBARANE-BARAT — Stage ENSEA 2026*  
*Dernière mise à jour : juin 2026*