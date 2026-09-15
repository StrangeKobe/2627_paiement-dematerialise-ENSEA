# Compte rendu - Réunion ECAM Lyon
**Sujet :** Échange sur leur système de paiement dématérialisé pour le foyer étudiant  
**Contexte :** Visio d'échange - ECAM Lyon

---

## 1. Vue d'ensemble de leur système

L'ECAM Lyon utilise une **application développée en interne pour le foyer**, dont la logique est **différente de notre projet ENSEA**. Point essentiel à retenir :

> **Leur application ne gère pas l'encaissement.** Elle sert à vérifier l'identité et les droits de l'étudiant, et à tracer les flux. Le paiement lui-même passe par un terminal externe (Zettle).

Leurs objectifs initiaux étaient :
- Vérifier que la personne est bien un étudiant du campus
- Vérifier qu'elle est autorisée à consommer (majeure, adhérente, non bannie)
- Tracer les flux de consommation via Zettle

---

## 2. Fonctionnement concret d'une transaction

Exemple : un étudiant veut payer une pinte à 4 €.

1. L'étudiant présente sa **carte étudiante**
2. L'application vérifie : est-il de l'école ? majeur ? adhérent ? non banni ?
3. Si tout est OK, le **barman encaisse** via le terminal, l'étudiant choisit **CB ou espèces**
4. La transaction de consommation est tracée

**L'étudiant ne gère aucune partie de l'encaissement via l'application.** Il n'y a pas de portefeuille rechargeable de leur côté, c'est la grande différence avec notre projet.

---

## 3. Architecture technique

- L'application **interroge le CRM** de l'école (côté vie étudiante) pour récupérer les informations étudiant
- Elle tourne sur un **ordinateur prêté par l'école**, installé au foyer
- Elle gère aussi l'**accès physique au foyer** sur le campus
- Le paiement passe par **Zettle**
- **Même application, même base de données pour toutes les associations** de l'école
- **Pas d'application téléphone**, **pas de limite de rechargement** (puisqu'il n'y a pas de portefeuille)

---

## 4. Données étudiant et CRM

Les informations sont stockées dans le **back-office du CRM**, côté vie étudiante :
- Date de début / date de fin d'adhésion
- Portefeuille (le cas échéant)

**Mise à jour des données :** en début d'année, le **BDE collecte les cotisations**, puis transmet les noms à la **vie étudiante**, qui les transmet au **service informatique**, qui met à jour l'application.

---

## 5. Gestion des rôles et statistiques

Deux niveaux d'accès :
- **Statut senior / administrateur** : accès aux informations de trésorerie
- **Statut barman** : scanne la carte étudiante et sert

Côté **vision admin** :
- Statistiques de consommation
- Possibilité de voir tout ce qui a été consommé
- Différenciation **par association** et **gestion des stocks**

---

## 6. Modèle associatif

- C'est **une association qui exploite l'outil**
- Le **BDE fédère les autres associations**, un rôle équivalent à celui d'une fédération. À l'ECAM, les associations sont appelées **"clubs"**.
- C'est le même fonctionnement que ce qu'une fédération ferait chez nous (l'ADE)
- Les élèves paient une fois les cotisations au BDE pour l'ensemble de leur cursus pour l'ensemble des associations 

---

## 7. Cadre réglementaire

- L'application aurait été **lancée vers 2019**, en lien avec la **loi sur les cercles privés**
- Conséquence directe : **pour vendre de l'alcool, il faut être adhérent**, d'où la vérification systématique de l'adhésion
- L'usage est **limité au campus** : impossible d'utiliser l'application à l'extérieur. Lors des soirées sur le campus, l'application est présente.

---

## 9. Différences clés avec notre projet ENSEA

| Aspect | ECAM Lyon | Notre projet ENSEA |
|--------|-----------|---------------------|
| Rôle de l'application | Vérification identité + traçabilité | Paiement + portefeuille virtuel |
| Encaissement | Terminal Zettle (CB/espèces) | Portefeuille rechargeable + RFID/QR |
| Portefeuille étudiant | Non | Oui, solde rechargeable |
| Support utilisateur | Carte étudiante | Carte étudiante RFID + QR code |
| Application téléphone | Non | Oui (rechargement, solde) |
| Matériel | Ordinateur prêté + Zettle | PCB custom (Raspberry Pi) |

**Notre approche va plus loin** : on intègre le portefeuille virtuel et l'encaissement, là où l'ECAM se limite à la vérification et à la traçabilité avec un terminal de paiement classique.

---

## 10. Points à retenir / pistes pour notre projet

- **Le BDE/fédération comme point central** : confirme notre choix de fédérer sous l'ADE
- **Différenciation par association + gestion des stocks** : fonctionnalités validées par leur retour d'expérience
- **Idée à creuser** : prévoir un système de **remontée de bugs** et de mise à jour de l'application


---

## Glossaire

**Zettle (anciennement iZettle)** : Solution de terminal de paiement créée en Suède en 2010, rachetée par PayPal en 2018. C'est un terminal de paiement mobile qui permet d'accepter les paiements par carte bancaire sans abonnement, avec une commission d'environ 1,75 % par transaction. Le terminal fonctionne avec une application de point de vente et nécessite une connexion réseau (WiFi ou cellulaire). C'est la branche "point de vente physique" de PayPal. Dans le cas de l'ECAM, Zettle gère l'encaissement CB pendant que leur application maison gère la vérification et la traçabilité.

**CRM (Customer Relationship Management)** : Logiciel de gestion qui centralise les informations sur les personnes. À l'ECAM, le CRM côté vie étudiante stocke les données des étudiants (adhésion, dates, portefeuille) que l'application du foyer vient interroger.

**Loi sur les cercles privés** : Cadre réglementaire qui encadre la vente d'alcool dans un espace réservé aux membres d'une association. Conséquence : seuls les adhérents peuvent consommer de l'alcool, d'où la vérification systématique de l'adhésion.

---

*Compte rendu rédigé par Maxime RAMBARANE-BARAT  
Stage ENSEA 2026*