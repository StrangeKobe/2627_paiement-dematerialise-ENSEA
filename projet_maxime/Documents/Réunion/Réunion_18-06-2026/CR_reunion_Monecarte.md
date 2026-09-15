# Compte rendu - Réunion Monecarte (App Campus)
**Société :** Monecarte - groupe CAPMONÉTIQUE  
**Interlocuteur :** Yohann Perromat, directeur commercial (Adcarte et Monecarte)  
**Participants ENSEA :** Maxime RAMBARANE-BARAT, Emilie ZHENG, Céline PLASSART  
**Contexte :** présentation de la solution App Campus et de l'offre logicielle multifonctions

---

## 1. Présentation de la société

Monecarte est une société du groupe CAPMONÉTIQUE, basée à Descartes (37160). L'équipe compte une quinzaine de personnes, majoritairement des ingénieurs et techniciens. Notre interlocuteur, Yohann Perromat, est directeur commercial et cumule plus de 30 ans de métier, avec une présence dans 8 à 10 groupes d'universités parisiennes et en France.

L'entreprise travaille dans les écoles depuis 5 à 6 ans et se concentre de plus en plus sur l'enseignement supérieur. À l'origine, elle équipait les clubs sportifs et les stades pour répondre à un problème de pertes d'argent.

**Point important :** historiquement, la solution de paiement n'est pas encore intégrée à l'application, c'est une brique distincte. Cela n'embête pas notre cas actuel.

---

## 2. L'App Campus - vue d'ensemble

L'App Campus est une application destinée aux étudiants et aux personnels, en production depuis plus de 6 ans. Caractéristiques principales :

- Disponible en **mode SaaS** (hébergement Monecarte) ou **On Premise** (serveur de l'école)
- Compatible **iOS, Android et mode Web** 
- **Mutualisation possible** entre plusieurs établissements
- **Interface personnalisée** à chaque établissement

**Établissements clients cités :** Université d'Orléans, ESSCA, Grenoble INP, ENSAG, ESAIP, Université de Tours, Université de Bourgogne, Sciences Po Grenoble, UGA, Université de Rennes, Université de Perpignan (UPVD).

---

## 3. Fonctionnalités de l'application

### Carte étudiante dématérialisée
- Visuel de la carte, soldes IZLY, copies-impressions (connecté à PaperCut)
- QR Code Carte Européenne, affichage du QR Code pour la délivrance de carte
- Identifiant carte étudiant dématérialisé (code-barres)

### Planning et agenda
- Interfaçage avec **ADE Campus** - pas de problème d'intégration de l'emploi du temps pour eux
- Vue du cours à la semaine ou sous 15 jours (fonction loupe)
- Changement de visuel du planning possible

### Maps
- Plan du campus, des transports, des arrêts
- Possibilité de créer ses propres points de référence (ex. CROUS)
- Recherche de bâtiment depuis l'interface

### Événements
- Interface de gestion des events avec **workflow de validation** pour les assos
- À l'Université de Perpignan, les events sont intégrés au calendrier ADE sous forme de bulles, filtrables selon les centres d'intérêt
- Visuels, descriptifs, réservations d'événements, liens HelloAsso
- Distinction événements à venir / en cours

### Notifications push
- Modification de cours, événements, sondages
- Création de sondages avec notification push (l'étudiant peut répondre ou refuser de répondre)
- Choix entre notification push ou email, activable/désactivable par l'utilisateur
- **Alertes forcées** par l'établissement pour les situations critiques (attentat, fuite de gaz, événement urgent ou dangereux), le site peut forcer les notifications les plus importantes

### Assiduité / émargement
- QR Code dynamique régénéré toutes les 5 secondes, à scanner depuis l'app étudiante
- Une école utilise en complément une balise au plafond pour vérifier instantanément qui est présent dans la salle

### Signalement (exemple Université de Perpignan)
- Page web où les étudiants peuvent signaler un problème sur un site propre à l'établissement
- **Point de vigilance soulevé :** si on propose une fonction de signalement, tous les signalements (du mineur à l'important) doivent être traités, sinon la fonction perd son intérêt
- L'application peut renvoyer vers un site externe via un bouton

### Autres
- Connexion **LDAP**
- Première connexion : page de guide et de paramétrage
- Accessibilité numérique (compatibilité TalkBack)
- Possibilité de connecter la carte ISIC à la solution Monecarte
- Contacts, affluences, notes, réseaux sociaux

---

## 4. Contrôle d'accès et paiement

Plusieurs écoles utilisent la solution pour le **contrôle d'accès physique** via la carte :
- Entrée des résidences étudiantes, laveries, distributeurs, cafétéria
- Gestion des quotas, paiement des impressions, suivi de l'assiduité

**Technologies :** NFC sur terminal Android, QR Code dynamique, et le paiement par carte RFID est une **piste envisagée** (idée, pas encore en place).

**Rechargement de compte :**
- Possibilité de créer des menus et de recharger le compte d'un client qui n'a pas assez
- Exemple : si on veut donner 10 € en espèces à une personne agréée, elle peut recharger le compte à notre place
- **ISEA Marseille** a une solution logicielle pour charger un compte en ligne, depuis la maison ou à l'école

**Frais bancaires** (recharge et consommation) : Yohann Perromat doit se renseigner et revenir vers nous.

**PayPal** : ils pourraient potentiellement travailler avec PayPal, mais pas de réponse concrète, il doit se renseigner.

---

## 5. Hébergement et déploiement

**Hébergement, deux options :**
- Serveur sur datacenter en France géré par Monecarte (mode SaaS)
- Hébergement sur le serveur de l'école (mode On Premise)

**Délais de déploiement :**
- Environ **20 jours** de mise en œuvre technique
- **Point d'attention majeur :** la déclaration sur l'App Store et le Google Play Store peut prendre du temps. Exemple cité : 2 mois pour déployer à une école de commerce d'Angers, en comptant la prise de décision sur la charte graphique, le bon de commande, etc.
- Pour une rentrée de septembre, il reste de la marge mais il faut avancer vite

**Retour d'expérience sur l'adoption :**
- Le déploiement se passe bien quand c'est un **projet d'établissement** et non le projet isolé d'un seul service
- **Contre-exemple :** à la faculté de médecine de Tours, le projet n'a pas fonctionné car les étudiants n'avaient pas vraiment le droit d'utiliser leur téléphone. Leçon : bien prendre en compte le contexte d'usage avant de se lancer.

---

## 6. Devis Monecarte (n° 2600316 - 18/06/2026)

Offre en **mode SaaS**, engagement sur **36 mois**, période du 15 septembre 2026 au 14 septembre 2027.

### Coûts récurrents (annuels)

| Poste | Détail | Montant HT |
|-------|--------|------------|
| Abonnement application mobile | 900 connexions × 3,50 € — tarif annuel par connexion smartphone, maintenance incluse | 3 150,00 € |
| Hébergement serveur SaaS | Tarif annuel | 1 250,00 € |
| Réunions de suivi | 1 réunion bimestrielle de 2h, tarif annuel | 890,00 € |

### Coûts de mise en place (ponctuels)

| Poste | Détail | Montant HT |
|-------|--------|------------|
| Intervention technicien niveau 2 | 20 × 890 €, paramétrage serveur SaaS, gestion de projet, authentification LDAP, fonctionnalités Agenda ADE, Événements, Maps, Contacts | 17 800,00 € |

### Totaux

| | Montant |
|---|---------|
| **Total HT** | 23 090,00 € |
| TVA (20 %) | 4 618,00 € |
| **Total TTC** | **27 708,00 €** |

**À noter :** la mise à jour des stores iOS et Android (obligatoire, 1 à 2 fois par an) n'est **pas incluse** dans cette offre.

### Lecture du devis

Le modèle économique combine un **coût de mise en place** (~17 800 € HT, principalement le paramétrage technique) et un **coût annuel récurrent** d'environ 5 290 € HT (abonnement par connexion + hébergement + réunions de suivi). L'abonnement application est facturé **par connexion smartphone** (3,50 € par étudiant par an, sur une base de 900 étudiants).

---

## 7. Lien avec notre projet de caisse

Point important soulevé en réunion : il serait **potentiellement possible d'intégrer la solution Monecarte avec la caisse enregistreuse que nous développons**. L'App Campus gérerait alors l'identité, l'accès et les fonctionnalités étudiantes, tandis que notre système gérerait l'encaissement et le portefeuille.

Cette piste reste à explorer, elle dépend notamment de la réponse de Monecarte sur les frais bancaires et sur la faisabilité du paiement par carte RFID.

---

## 8. Réflexion : carte vs application téléphone

Un point de fond a été évoqué : il est peut-être plus simple de mettre en place une **carte pour payer** que de forcer les étudiants à installer une application. C'est un arbitrage à garder en tête dans notre conception, d'autant que le contre-exemple de Tours (étudiants sans droit au téléphone) montre que la dépendance au smartphone peut bloquer un projet.



## Glossaire

**SaaS (Software as a Service)** : Modèle où l'application est hébergée par le prestataire sur ses serveurs et accessible en ligne, par abonnement. Par opposition au mode On Premise.

**On Premise** : Modèle où l'application est installée et hébergée sur les serveurs propres de l'établissement.

**LDAP** : Protocole d'annuaire utilisé pour centraliser l'authentification des utilisateurs. Permet aux étudiants de se connecter avec leurs identifiants habituels de l'école.

**ADE Campus** — Logiciel de gestion des emplois du temps utilisé dans l'enseignement supérieur. L'App Campus s'y interface pour afficher les plannings.

---

*Compte rendu rédigé par Maxime RAMBARANE-BARAT  
 Stage ENSEA 2026*