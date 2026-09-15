# Compte rendu - Réunion solutions de paiement
**Date :** 05 juin 2026 | **Avec :** Mr Moubêche (alumni, expert paiements)

---

## 1. Réglementation & conformité juridique

**Point soulevé : risque de "rétention de monnaie électronique"**

Le système de portefeuille virtuel interne pourrait être qualifié juridiquement d'**émission de monnaie électronique**, activité réglementée en France par l'ACPR (Autorité de Contrôle Prudentiel et de Résolution). Avant tout déploiement, il faut vérifier si l'ADE entre dans ce cadre ou si le statut d'école/association étudiante permet d'en être exempté.

**Actions :**
- Mr Moubêche se renseigne auprès de contacts 
- Vérifier si un dossier de conformité doit être déposé
- Hypothèse favorable : le cadre scolaire et associatif pourrait exempter le projet de ces obligations

> Voir `conformite-monnaie-electronique.md` pour l'analyse détaillée de la réglementation applicable.

---

## 2. Solutions de paiement alternatives à étudier

Mr Moubêche a mentionné plusieurs solutions à investiguer avant de trancher sur Stripe :

| Solution | Nature | À vérifier |
|----------|--------|-----------|
| **Lyra** | Plateforme de paiement française | Documentation et frais |
| **Monetico** | Solution CB du Crédit Mutuel/CIC | Documentation en ligne disponible |
| **IIRAF / PayPlus** | Plateforme de paiement | Documentation et frais |
| **Wero** | Paiement instantané P2P | Cas d'usage particulier à particulier - voir si applicable |

**Point important sur les frais :** les frais varient selon l'origine de la carte. Une solution francophone comme Monetico ou Lyra applique les frais CB franco-français (interchange européen plafonné à 0,2-0,3%), tandis que Stripe/PayPal (américains) peuvent appliquer des frais Visa/Mastercard plus élevés sur certaines cartes. À comparer précisément.

**Actions :**
- Analyser les différentes solutions

---

## 3. Wero - cas particulier

Wero est actuellement un système de paiement de **particulier à particulier (P2P)**, développé par les banques européennes. Il n'est pas conçu nativement pour les paiements marchands ou associatifs.

**Actions :**
- Vérifier si Wero propose une offre pour les associations ou un mode "collecte"
- Voir si une intégration API est disponible

---

## 4. Repenser le multi-assos - simplification possible

**Idée soulevée par Mr Moubêche :** le modèle multi-comptes n'est peut-être pas nécessaire.

Au lieu d'un compte Stripe par asso, on pourrait :
- Centraliser tout l'argent sur **un seul compte ADE**
- Gérer la comptabilité par asso **uniquement en base de données Django**
- En fin de mois, faire des virements manuels ou automatiques depuis ce compte unique vers les IBAN de chaque asso

Ce modèle pourrait être beaucoup plus simple techniquement - pas besoin de Stripe Connect, un compte standard suffit. La répartition se fait via notre propre logique Django, pas via l'API Stripe ou celle ci doit simplement rediriger via un seule compte et pas plusieurs. 

**Actions :**
- Vérifier si Stripe standard (sans Connect) permet les virements sortants vers plusieurs IBAN
- Comparer la complexité de ce modèle vs Connect
- Voir si d'autres solutions (Monetico, Lyra) supportent ce modèle plus facilement et à quel frais

---

## 5. Benchmark - autres écoles

**Idée soulevée :** d'autres écoles font peut-être la même chose, autant s'en inspirer.

**Piste concrète : l'ECAM Lyon**

Ils ont un système de paiement pour leur bar avec deux fonctionnalités intéressantes :
- Vérification de minorité avant validation d'un achat d'alcool
- Limitation à 1 achat par personne sur certains produits

C'est exactement le type de contraintes qu'on pourrait avoir à gérer à terme.

**Actions :**
- Voir l'application de l'ECAM Lyon pour comprendre leur architecture technique
- Chercher d'autres écoles ayant des systèmes similaires (BDE avec caisse dématérialisée)

---

## 6. Interlocuteurs à éviter / à privilégier

**Ne pas contacter :** le conseiller bancaire classique - il n'aura pas les réponses sur ce type d'architecture de paiement programmatique.

**À privilégier :**
- Les contacts techniques de Mr Moubêche dans le domaine des paiements
- Les équipes techniques des solutions (Monetico, Lyra) directement
- Les référents techniques d'autres écoles



---

*Compte rendu rédigé par Maxime RAMBARANE-BARAT — Stage ENSEA 2026*