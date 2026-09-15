# Tests code - Terminal (Raspberry Pi Zero 2W)

Ce document décrit la mise en service et les tests du **terminal de paiement
portable** (Raspberry Pi Zero 2W), avec un focus sur la partie qui a demandé le
plus de temps : l'accès réseau et la configuration WiFi. Il sert de guide à la
personne qui reprend le projet.

---

## Contexte technique

- **Carte** : Raspberry Pi Zero 2W (ARM Cortex-A53, 64 bits)
- **OS** : Raspberry Pi OS Lite 64 bits (pas de bureau)
- **Alimentation** : HAT UPS Geekworm X306 + batterie 18650
- **Périphériques prévus** :
  - Lecteur RFID RC522 via SPI (GPIO 7/9/10/11/24/25)
  - Écran OLED SSD1327 128×128 via I2C à l'adresse 0x3C (GPIO 2/3)
  - Lecteur QR code via UART (GPIO 14/15)
  - Capteur de luminosité BH1750 (intégré au X306)
  - Buzzer via MOSFET sur GPIO18

> Sur le X306, la **LED rouge** signifie que la batterie 18650 **se charge**.
> Elle passe au vert une fois chargée. Ce n'est pas une erreur.

---

## 1. Flash de la carte SD (Raspberry Pi Imager)

### Étapes
1. **Choose Device** → Raspberry Pi Zero 2 W
2. **Choose OS** → Raspberry Pi OS (Other) → Raspberry Pi OS Lite (64-bit)
3. **Choose Storage** → la carte microSD
4. **Roue crantée ⚙️ (OS Customization)** - étape à ne surtout pas sauter :
   - Hostname : `terminal-kfet`
   - Utilisateur : **`terminal`**
   - Mot de passe : (le noter précisément)
   - WiFi SSID : **`TechTinkerers`** (voir section WiFi ci-dessous)
   - WiFi password : (celui du réseau)
   - Pays : `FR`, Clavier : `fr`, Timezone : `Europe/Paris`
   - Enable SSH : coché, avec authentification par mot de passe
5. **SAVE** puis **Write**

### ⚠️ Piège critique rencontré
Après « Write », l'Imager pose une question du type
**« Appliquer les réglages de personnalisation ? »**. Si on ne clique pas
explicitement **« Yes »**, l'image est flashée **sans** compte utilisateur,
**sans** WiFi et avec le hostname par défaut `raspberrypi`. C'est ce qui a causé
des heures de blocage (aucune connexion possible). **Toujours confirmer « Yes ».**

---

## 2. Trouver le Pi sur le réseau

Le `.local` (mDNS) ne fonctionne pas toujours. Méthode fiable via **nmap**
depuis le PC (les Raspberry Pi ont des adresses MAC commençant par `BC:24:11`) :

```bash
sudo nmap -p 22 192.168.0.0/24 | grep -i "BC:24:11"
```

Repérer la nouvelle IP apparue, puis :

```bash
ssh terminal@<IP_du_terminal>
```

---

## 3. Problème WiFi et accès série (le principal blocage)

### Symptômes rencontrés
- WiFi non détecté / Pi injoignable.
- Impossible de se connecter en SSH (pas de compte, WiFi absent).

### Deux causes racines identifiées

**a) Personnalisation Imager non appliquée** (voir piège ci-dessus) : image sans
compte ni WiFi.

**b) Confusion de modèle de carte** : une des cartes était en réalité un
**Pi Zero W v1** (ARMv6), et non un Pi Zero 2W. L'image 64 bits est
**incompatible** avec l'ARMv6. Confirmé par les logs de boot série :
`Machine model: Raspberry Pi Zero W Rev 1.1`.
→ Pour un Pi Zero W v1, il faut une image **32 bits**.

### Prise de contrôle par console série (méthode de secours)
Quand le WiFi est mort, on reprend la main **par UART série** avec un adaptateur
USB-UART (type CH340) et `minicom`. Un **shield UART** pour les TP de 1re année
est disponible dans un tiroir de la **D265** et fait le même travail.

Cette console série permet de lire les logs de boot (donc d'identifier le modèle
exact de la carte) et de reconfigurer le WiFi via `sudo raspi-config`.

### Configuration WiFi manuelle (contournement retenu)
Quand la personnalisation Imager échoue, on écrit les fichiers **directement sur
la partition `bootfs`** de la carte SD depuis le PC :

- Créer un compte utilisateur : fichier `userconf.txt` contenant
  `utilisateur:<hash>`, le hash étant généré par
  ```bash
  openssl passwd -6
  ```
- La configuration WiFi se fait ensuite via `raspi-config` sur la console série,
  ou via le fichier de configuration réseau approprié à la version de l'OS.

> Note : l'utilitaire de gestion du WiFi a changé dans les dernières versions de
> l'OS (passage à NetworkManager). Vérifier quelle méthode s'applique à la
> version flashée.

### Point réseau important
Le WiFi du Pi Zero 2W est **faible et en 2,4 GHz uniquement**. Se connecter au
réseau **`TechTinkerers`** de la salle (2,4 GHz), **pas** à `eduroam` ni au WiFi
ENSEA (réseaux non classiques et potentiellement éloignés).
Sur certains Pi Zero, une antenne externe (connecteur SMA soudé au bon endroit)
améliore la portée, mais ce n'est pas nécessaire ici - le problème était software.

### État : RÉSOLU
Accès au terminal rétabli en modifiant directement les fichiers de la carte SD
et en reprenant la main via le shield UART. Problème purement logiciel.

---

## 4. Tests des périphériques du terminal

Une fois l'accès rétabli, activer les interfaces via `sudo raspi-config`
(SPI pour le RC522, I2C pour l'OLED et le BH1750, UART pour le lecteur QR).

| Périphérique | Interface | Adresse / GPIO | État | Remarque |
|---|---|---|---|---|
| RFID RC522 | SPI | GPIO 7/9/10/11/24/25 | à tester | - |
| OLED SSD1327 | I2C | 0x3C | à tester | `i2cdetect -y 1` pour vérifier la présence |
| BH1750 (luminosité) | I2C | intégré X306 | à tester | - |
| Lecteur QR | UART | GPIO 14/15 | ⚠️ bloqué | module non TTL, voir ci-dessous |
| Buzzer | GPIO18 | - | à tester | même réserve MOSFET que la caisse |

### Vérification I2C rapide
```bash
sudo apt install i2c-tools
i2cdetect -y 1
```
L'OLED doit apparaître à l'adresse `0x3C`.

### Lecteur QR - bloqué
Le module de lecteur QR disponible **ne sort pas en TTL série**, alors que le
câblage prévoyait une liaison **UART** sur GPIO 14/15. Il faut soit un modèle à
sortie TTL confirmée, soit un convertisseur d'interface.
Voir `../../Hardware/PROBLEMES_MATERIEL.md` point 6.

---

## Résumé de l'état des tests - Terminal

| Élément | État | Blocage |
|---|---|---|
| Flash SD + personnalisation | ✅ OK | (attention au piège « Yes ») |
| Accès réseau / WiFi | ✅ Résolu | était software |
| Accès SSH | ✅ OK | - |
| Console série de secours (UART) | ✅ OK | shield en D265 |
| RC522 / OLED / BH1750 | ⏳ À tester | - |
| Lecteur QR | ❌ Bloqué | module non TTL (matériel) |
| Buzzer | ⏳ À tester | réserve MOSFET (voir caisse) |

---

## Rappels utiles pour la reprise

- **Deux Pi, deux utilisateurs** : `caisse` (Pi 5) et `terminal` (Pi Zero 2W).
  Ne pas les confondre lors des connexions SSH.
- **Vérifier le modèle exact** de chaque Pi Zero avant de flasher (v1 ARMv6 =
  image 32 bits ; 2W = image 64 bits).
- **Toujours confirmer « Yes »** à la question de personnalisation de l'Imager.
- **Réseau `TechTinkerers`** (2,4 GHz) pour les Pi Zero.
- En cas de perte d'accès réseau, **le shield UART de la D265** est la solution
  de secours pour reprendre la main.

---

*Document rédigé en fin de stage - Maxime RAMBARANE-BARAT.*
