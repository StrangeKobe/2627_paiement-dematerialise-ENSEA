# Compte rendu - Réunion solutions de paiement
**Date :** 11 juin 2026 | **Avec :** Mr Moubêche (alumni, expert paiements)

---

## 1. Paiement en espèces - à anticiper

> *Point identifié en amont de la réunion, non abordé - à prévoir pour une version future.*

Il faudra implémenter un moyen pour qu'un étudiant puisse recharger son wallet **en espèces** directement auprès d'un membre du BDE ou d'un responsable de la fédération. Ce cas d'usage est important pour les étudiants qui n'ont pas de carte bancaire ou qui préfèrent ce mode de paiement.

**À concevoir :** une interface dans l'application permettant à un « opérateur » (bureau BDE, trésorier) de créditer manuellement un wallet contre remise d'espèces, avec traçabilité de l'opération.

---

## 2. Business model - comparatif des solutions

Construire un **tableau comparatif chiffré** des solutions de paiement en se basant sur un volume réaliste d'étudiants et de transactions, afin de comparer :

- Les solutions sans abonnement mais avec frais par transaction (ex. Stripe)
- Les solutions avec abonnement mensuel fixe mais frais réduits (ex. Payplug, Lyra, SogeCommerce)

L'objectif est de trouver le **point d'équilibre** : à partir de quel volume mensuel de rechargements une solution avec abonnement devient-elle moins chère qu'une solution sans abonnement ?

**Action :** réaliser ce calcul sur la base d'hypothèses de volume (nombre d'étudiants actifs, fréquence et montant moyen de rechargement).

---

## 3. Contacts à établir

### ECAM LaSalle Lyon
Madame Plassart a déjà envoyé un email de prise de contact à **Cyrielle** (ECAM LaSalle), qui avait présenté leur système de bar dématérialisé lors du séminaire CGE 2024. L'objectif est d'organiser une visio rapidement pour échanger sur leur architecture, leur business model et leurs retours d'expérience.


**Action :** relancer si pas de réponse d'ici une semaine et préparer une liste de questions pour la visio.

### Monecarte
Prendre contact avec Monecarte pour comprendre leur offre, leur business model et les conditions d'accès pour une école de la taille de l'ENSEA.

**Action :** identifier le bon interlocuteur et envoyer un email de présentation du projet.

---

## 4. Données étudiants - réunion à organiser

Établir la **liste des informations nécessaires par étudiant** dans la base de données (nom, prénom, numéro de carte, date de naissance pour la détection des mineurs, statut adhérent, etc.) et identifier les questions de sécurité associées.

**Action :** organiser une réunion avec **Mr Bares** pour valider les choix de sécurité (stockage, accès, RGPD).

---

## 5. Lancement du développement applicatif - réunion avec Mr Papazoglou

Organiser une réunion avec **Mr Papazoglou** pour :
- Valider ce qu'on met dans la base de données étudiants
- Cadrer le développement de l'application (fonctionnalités prioritaires, architecture)
- Commencer à lancer la machine côté logiciel en parallèle du hardware

**Action :** planifier cette réunion d'ici la semaine prochaine

---

## 6. Idée future - système de badges et récompenses

> *Idée intéressante soulevée en réunion, à garder pour une V2 - on est encore en V1.*

Envisager un système de **paliers** avec badges et/ou récompenses pour les étudiants (fidélité, nombre de rechargements, etc.). À ne pas prioriser maintenant mais à documenter pour ne pas perdre l'idée.

---

## Actions récapitulatives

| Action | Responsable | Priorité |
|--------|-------------|----------|
| Réaliser le business model comparatif des solutions | Maxime | 🔴 Urgent |
| Relancer ECAM LaSalle pour visio | Maxime / Mme Plassart | 🔴 Urgent |
| Contacter Monecarte | Maxime | 🟠 Dès que possible |
| Réunion avec Mr Bares (données étudiants + sécurité) | Maxime | 🟠 Dès que possible |
| Réunion avec Mr Papazoglou (lancement application) | Maxime | 🟠 Dès que possible |
| Concevoir le flux paiement en espèces | Maxime | 🟡 V1 ou V2 |
| Documenter l'idée badges/récompenses | Maxime | 🟡 V2 |

---

*Compte rendu rédigé par Maxime RAMBARANE-BARAT — Stage ENSEA 2026*  
*Dernière mise à jour : juin 2026*