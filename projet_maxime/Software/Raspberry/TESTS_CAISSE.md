# Tests code - Caisse (Raspberry Pi 5)

Ce document décrit les tests logiciels effectués sur la **caisse enregistreuse**
(Raspberry Pi 5) et l'état de chaque périphérique. Il sert de point de départ à
la personne qui reprend le projet pour savoir ce qui a été validé, ce qui bloque,
et comment relancer les tests.

---

## Contexte technique

- **Carte** : Raspberry Pi 5
- **OS** : Raspberry Pi OS 64 bits
- **Bibliothèque GPIO** : `gpiozero` (backend `lgpio`).
  ⚠️ Sur Pi 5, l'ancienne `RPi.GPIO` **ne fonctionne pas**, utiliser `gpiozero`.
- **Périphériques pilotés** :
  - Tiroir-caisse VEVOR (solénoïde 12 V) via MOSFET Q3 sur **GPIO18**
  - Buzzer piézo via MOSFET Q1 sur **GPIO23**

### Vérification de l'environnement

```bash
python3 -c "import gpiozero, fastapi; print('OK')"
```

Si `OK` s'affiche, les dépendances sont présentes.

---

## Mapping GPIO de la caisse

| Fonction | GPIO | Broche | Logique | Remarque |
|---|---|---|---|---|
| Tiroir-caisse | GPIO18 | 12 | voir ci-dessous | via MOSFET Q3 + solénoïde |
| Buzzer | GPIO23 | 16 | voir ci-dessous | via MOSFET Q1, PWM ~2 kHz |

> **Note importante sur la logique** : les scripts d'origine ont été écrits en
> logique inversée (`active_high=False`) sur l'hypothèse d'un MOSFET canal P.
> Or le **SQ2310ES est un MOSFET canal N** (vérifié sur datasheet Vishay).
> La logique correcte est donc **normale** : `active_high=True`, GPIO HAUT = actif.
> Adapter les scripts en conséquence lors de la reprise.

---

## Test 1 - Tiroir-caisse

### But
Envoyer une impulsion courte sur le solénoïde pour ouvrir le tiroir.

### Sécurité
Le solénoïde **ne supporte pas** une alimentation continue (il chauffe et
grille). On envoie une **impulsion de 300 ms maximum**, évitez plus. La durée
est bornée dans le code.

### Script de référence

```python
#!/usr/bin/env python3
import time
from gpiozero import DigitalOutputDevice

GPIO_TIROIR = 18

# SQ2310ES = canal N -> logique normale : HAUT = solénoïde alimenté
tiroir = DigitalOutputDevice(GPIO_TIROIR, active_high=True, initial_value=False)

input("Tiroir fermé, alim 12 V branchée, diode D6 vérifiée. Entrée pour ouvrir...")
tiroir.on()
time.sleep(0.3)   # 300 ms 
tiroir.off()
print("Le tiroir doit avoir claqué et s'être ouvert.")
```

### État : NON FONCTIONNEL (bloqué matériel)

En l'état des choses, le test échoue à cause de défauts **matériels**, pas logiciels :
1. Empreinte SOT-23 du MOSFET erronée → le Gate reçoit le 12 V, MOSFET détruit.
2. Interrupteur qui ne coupe pas le rail 12 V du solénoïde.

Voir `../../Hardware/PROBLEMES_MATERIEL.md` points 1 et 2 pour le détail.

### Procédure de diagnostic au multimètre (validée)

Pointe noire sur la **Source** (GND), alimentation branchée :

| Mesure | Pointe rouge | Au repos | Sous impulsion |
|---|---|---|---|
| Vgs | Gate | 0 V | ~3 V |
| Vds | Drain | 12 V | proche de 0 V |

Vérifications **alim débranchée** (mode Ω / continuité) **avant** de mettre sous tension :

| Mesure | Attendu | Si anormal |
|---|---|---|
| Gate ↔ +12 V | ne bipe pas | bipe = Gate relié au 12 V, **ne pas alimenter** |
| Gate ↔ Drain | ∞ | quelques kΩ = MOSFET percé, à remplacer |
| Gate ↔ Source | ~1 kΩ (R15) | ∞ = pull-down non connecté |
| Source ↔ GND | bipe | - |
| Drain ↔ solénoïde (J1) | bipe | - |

### Solution de contournement retenue (MVP)
Compte tenu des délais, l'ouverture se fait par **clé manuelle**.
L'ouverture électrique est documentée comme fonctionnalité **à valider en V2**.

### Piste pour la reprise (Ce n'est qu'une piste)
Un **module relais 5 V** (avec opto-coupleur intégré) piloté par GPIO18 permet
de contourner entièrement le MOSFET Q3 et son empreinte défectueuse. Câblage :
VCC→5 V, GND→GND, IN→GPIO18, COM→+12 V, NO→solénoïde. L'opto-coupleur isole le
Pi du 12 V et beaucoup de modules intègrent la diode de roue libre.

---

## Test 2 - Buzzer

### But
Émettre des bips de confirmation.

### Script de référence (PWM)

```python
#!/usr/bin/env python3
import time
from gpiozero import PWMOutputDevice

GPIO_BUZZER = 23
FREQ = 2000   # Hz - fréquence de résonance du PS1720P02

buzzer = PWMOutputDevice(GPIO_BUZZER, frequency=FREQ, initial_value=0)

print("Test buzzer : 3 bips...")
for i in range(3):
    buzzer.value = 0.5   # rapport cyclique 50 %
    time.sleep(0.15)
    buzzer.value = 0
    time.sleep(0.35)
    print(f"  bip {i + 1}/3")
print("OK si 3 bips nets.")
```

### État : NON FONCTIONNEL (bloqué matériel)

Aucun son obtenu. Deux points à retenir :
- Le **PS1720P02 est un buzzer passif** : il faut impérativement un signal
  **PWM ~2 kHz**, jamais du continu.
- Le MOSFET Q1 partage très probablement le **même défaut d'empreinte SOT-23**
  que Q3, ce qui empêche le signal d'atteindre le buzzer.

Voir `../../Hardware/PROBLEMES_MATERIEL.md` point 5.

### Pour la reprise
1. Corriger l'empreinte de Q1 (V2) ou contourner avec un petit transistor
   correctement câblé.
2. Garder la fréquence PWM à **2 kHz**.
3. En attendant, la confirmation de paiement reste **visuelle (écran)**.

---

## Test 3 - Accès SSH à la caisse

### Configuration
- Utilisateur : **`caisse`** (défini dans Raspberry Pi Imager)
- Connexion : `ssh caisse@<IP_de_la_caisse>`

### Point d'attention : clé d'hôte modifiée
Après un reflash de la carte SD, SSH peut refuser la connexion avec
« REMOTE HOST IDENTIFICATION HAS CHANGED ». C'est **normal** (nouvelle clé
générée). Corriger côté PC :

```bash
ssh-keygen -f '/home/<user>/.ssh/known_hosts' -R '<IP_de_la_caisse>'
ssh caisse@<IP_de_la_caisse>
```

### Point d'attention : « Permission denied, please try again »
Ce message signifie que SSH joint le Pi mais **rejette l'identifiant** :
- Vérifier le **nom d'utilisateur** exact (`caisse` pour la caisse,
  `terminal` pour le terminal - ne pas confondre les deux Pi).
- Vérifier le **mot de passe** (attention aux différences clavier AZERTY/QWERTY
  lors de la création dans l'Imager).
- Vérifier que `PasswordAuthentication yes` est actif dans
  `/etc/ssh/sshd_config` **sur le Pi**.

---

## Résumé de l'état des tests - Caisse

| Test | État | Blocage |
|---|---|---|
| Environnement Python / GPIO | ✅ OK | - |
| Accès SSH | ✅ OK | - |
| Tiroir-caisse | ❌ Bloqué | matériel (empreinte MOSFET + interrupteur) |
| Buzzer | ❌ Bloqué | matériel (empreinte MOSFET) |

Les deux blocages sont **matériels** et documentés dans `../../Hardware/PROBLEMES_MATERIEL.md`.
Le code de test est prêt et correct ; il fonctionnera une fois la V2 du PCB
corrigée, ou avec les contournements proposés (module relais pour le tiroir).

---

*Document rédigé en fin de stage - Maxime RAMBARANE-BARAT.*
