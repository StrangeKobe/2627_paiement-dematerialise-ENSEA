# Compte rendu - Réunion GLYPS Education
**Solution :** GLYPS, plateforme de gestion de vie associative étudiante  
**Interlocuteur :** Mathieu Vally (GLYPS)  
**Participants ENSEA :** Maxime RAMBARANE-BARAT, Emilie ZHENG, Céline PLASSART, Marjorie JEHIN, Nicolas PAPAZOGLOU   
**Format :** visio avec démonstration en direct (interfaces étudiant, associative et back-office)  

---

## 1. Présentation générale de la solution

GLYPS est une plateforme web de gestion de la vie associative étudiante. Contrairement aux solutions purement orientées paiement, GLYPS couvre l'ensemble du cycle associatif : présentation des associations, gestion des événements, billetterie, inscriptions avec dossiers, trésorerie et suivi des transactions.

La solution se décline en trois espaces distincts :
- **Interface étudiant** (portail) - consultation et inscription
- **Interface associative** (back-office) - gestion par les responsables d'assos
- **Interface administration école** - supervision globale

Un point central du modèle : chaque association possède son **propre compte HelloAsso**. L'étudiant paie avec sa carte bancaire sans voir la distinction entre les différents comptes HelloAsso - pour lui, l'expérience est unifiée.

---

## 2. Le bracelet NFC et le wallet

- **Bracelet NFC** avec un **wallet alimenté** (porte-monnaie rechargeable)
- **Prévente directement sur le bracelet** - l'étudiant peut acheter à l'avance
- **Authentification et vérification d'identité** : une association peut scanner le bracelet pour vérifier l'identité de l'étudiant
- Sur un **même bracelet**, l'étudiant retrouve ses inscriptions aux différents événements des différentes associations
- Une association qui scanne le bracelet voit la **présence de l'étudiant à son propre événement**, mais **ne voit pas les achats** de l'étudiant dans les autres associations (cloisonnement des données)
- **Perte du bracelet** : on lie un nouveau bracelet qui récupère toutes les données de l'étudiant
- Sur l'application, le bracelet se matérialise sous forme d'une **carte avec le wallet**
- Le bracelet sert **surtout pour le WEI**, où les assos peuvent scanner pour accéder aux infos de l'étudiant

---

## 3. Interface étudiant (portail)

### Tableau de bord
Page d'accueil personnalisée avec photo, ID étudiant, programme (ex. PGE) et campus. Deux blocs principaux : événements « À venir » et « Consos » (consommations).

### Événements
- Liste et **calendrier** des activités et associations étudiantes du campus
- Filtres par recherche, type d'événement et association
- Vue calendrier mensuelle avec les événements positionnés

### Page événement (exemple WEI 2026)
- Bannière, dates, lieu, organisateur (ex. BDE)
- **Billetterie multi-tarifs** : prévente tarif Trésor (89€, offre limitée), prévente tarif Promo (109€), tarif Standard (129€)
- Mention **« Interdit aux mineurs »** affichée clairement
- Description de l'événement

### Process d'inscription (dossier)
Workflow complet d'inscription à un événement avec plusieurs étapes obligatoires :
1. Documents à lire et signer
2. Fiche sanitaire
3. **Vidéos de prévention obligatoires** : prendre soin de ses potes, prévention alcool, prévention sur le consentement (liées aux VSS)
4. Validation et signature avec coordonnées (nom du contact, lien avec le participant, téléphone, adresse)
5. **Caution**
6. **Paiement**

### Associations
- Annuaire des associations, classées par catégorie : **sportif, culturel, professionnel, technologique, loisirs, humanitaire**
- Chaque fiche association comprend une description propre, les réseaux sociaux, le descriptif complet, les événements proposés, et la possibilité de **contacter directement l'association**

---

## 4. Interface associative (back-office)

### Dashboard
Vue rapide avec : utilisateurs en ligne, utilisateurs inscrits (ex. 128), somme récoltée (ex. 15 651 €), événements en cours. Affichage des événements ouverts, validés et en attente.

### Informations de l'association
- Type d'association (ex. Événementiel), campus de rattachement (gestion **multi-campus**)
- Email de contact, RNA, description, bannière
- Réseaux sociaux (X, Instagram, YouTube, LinkedIn, Discord, site web)
- **Documents** : statuts, PV (procès-verbal), récépissé, charte - tous téléchargeables
- **Documents requis par l'école** (ex. dossier de partenariat)
- Système de connexion propre avec **HelloAsso** (« Configurer HelloAsso »)
- **Caution Swikly** : système de caution digitale et sécurisée 

### Notes partagées internes
Notes internes visibles par les membres de l'association ayant accès à cet espace, ainsi que par l'administration de l'école. Exemple d'usage : une association BDS fait un inventaire régulier des stocks de ballons et sauvegarde une note « Inventaire du mois d'avril ».

### Gestion des membres
- Répartition en **Bureau / Staff / Membres / Autres**
- Exemple : une asso de rugby peut avoir 3 personnes au bureau mais 40 membres
- **Export Excel** et **ajout en masse par fichier CSV** (colonne email)
- Rôle principal + appellation libre (ex. Respo Stock, Vice-Trésorière)
- **Historique des membres et des bureaux** conservé - résout le problème de perte d'information au fil des passations (« au bout de 3 ans, compliqué de savoir qui était le responsable partenariat »)

### Événements
- Vue Cartes ou Liste
- États : **ouverts, validés, en attente de validation, brouillons, fermés**
- Filtres par campus et type d'événement (voyage / week-end, événement / soirée)

### Transactions
- Historique détaillé de toutes les transactions de billetterie
- Filtres : événement, tarif payé, association, statut, date, étudiant
- Détail par ligne : étudiant, événement, date, type de place, montant, statut (ex. « Réussi »)
- **Export CSV**

### Trésorerie
Trois onglets : **Journal des transactions, Bilan financier, Statistiques**.
- **Journal des transactions** : entrées automatiques des billetteries + ajout manuel des sorties/recettes. Pour une dépense : montant, date, type de paiement, lien éventuel à un événement, description, et **justificatif obligatoire** (ex. ticket d'essence, facture d'achat d'appareil photo). L'objectif est de **professionnaliser la gestion** et d'éviter la perte des factures.
- **Bilan financier** : recettes et dépenses par événement, avec un **résultat net**.
- **Statistiques** : flux net (recette − dépense) sous forme de graphique mensuel, et **top dépenses** par catégorie (événement, déplacements, décorations, équipe, cohésion)

---

## 5. Gestion d'un événement (exemple WEI)

L'espace événement permet de gérer finement un week-end d'intégration :

- **Dossiers** en attente / validés, revenus propres à l'événement, vue d'ensemble
- **Gestion des billets** : ajout de tarifs en quelques clics, ajout de cautions, consommations incluses, description, **critères de sélection** des personnes ayant accès à un tarif
- **Dossiers étudiants** : filtrage sur de nombreux critères, affichage de colonnes personnalisables
- **Fiche étudiant détaillée** : numéro, coordonnées, tarif payé, documents signés (CGV, droit à l'image), vidéos de prévention VSS visionnées, fiche sanitaire, caution déposée
- **Système d'appels / scan** : possibilité de créer des appels à n'importe quel moment (arrivée au campus, montée du bus, restauration, repas du vendredi…) et de voir qui a été scanné et à quelle heure
- **Demande de modification** : si un document est mal rempli (ex. fiche sanitaire), l'asso supprime le document et envoie automatiquement une demande à l'étudiant, qui reçoit la notification. Listing des étudiants à qui une modification a été demandée.
- **Gestion des bus** : nom du bus, nombre de places, compagnie, responsable, avec système de mailing
- **Mailing ciblé** : choix d'un thème, objet, liens et boutons, **filtrage des destinataires** (ex. uniquement ceux à qui on a demandé une modification), aperçu du mail avant envoi
- **Statistiques de l'événement** : ventes par campus, par genre, par régime (végétarien…)

---

## 6. Création d'événement et workflow de validation

- L'**administration de l'école configure en amont des « thèmes d'événements »** : pour chaque type d'événement, elle définit les informations et documents requis, ainsi que le **process de validation** (plusieurs étapes).
- L'étudiant crée un événement en choisissant le thème correspondant, remplit les informations, enregistre et soumet à validation.
- Le thème **change visuellement à chaque étape** du process de validation, ce qui permet de suivre l'avancement.
- L'école est **totalement autonome** pour configurer ses thèmes et ses process de validation.

---

## 7. Modèle économique et licence

- La licence est calculée sur l'**ensemble de la communauté étudiante**, pas sur le nombre de membres associatifs.
- Exemple donné : un établissement de 11 000 étudiants dont 2 500 associatifs → la licence porte sur les 11 000, car tous les étudiants ont accès à la plateforme (même les responsables d'assos sont d'abord des étudiants).
- Chaque association a son propre **HelloAsso** rattaché ; les étudiants paient avec leur carte bancaire directement.
- **Commission prélevée :** GLYPS indique ne prélever aucune commission sur les paiements (la collecte passe par HelloAsso, gratuit pour les associations).

---

## 8. Application mobile (à venir)

- Une **application mobile** sera mise en place à partir de la rentrée pour tous les étudiants.
- L'application ne permettra **pas** de piloter les inscriptions complexes type WEI (qui nécessitent fiches sanitaires et documents sensibles).
- En revanche, les étudiants pourront depuis l'app : prendre une place pour une soirée, s'inscrire à une conférence, s'inscrire à un match, etc.
- L'application n'a pas encore été totalement développée mais aura une première disposition à la rentrée.

---

## 9. Architecture technique

D'après le récapitulatif technique lu en séance :

- GLYPS reste un **service externe totalement isolé du SI de l'école**, à la seule exception de l'authentification.
- La solution repose sur : une **application mobile**, un back-office, une **API centrale**, une **base de données PostgreSQL** et une authentification, le tout containerisé sous **Kubernetes**.
- **Aucun accès direct** à l'infrastructure de l'école, aucune ouverture de firewall entrante à prévoir.
- Authentification via **SSO compatible OIDC 2.0 / SAML 2.0** (EDP Intra, Azure AD, Google Workspace…), ce qui garantit l'absence de compte local. À la première connexion, l'utilisateur est provisionné avec son rôle ; sa désactivation côté annuaire est immédiate.
- **Hébergement assuré par GLYPS** (serveurs de l'éditeur).
- **Conformité RGPD** : politique de confidentialité rédigée par un cabinet d'avocats spécialisé en droit numérique.

> **Synchronisation des données étudiants :** un démissionnaire ou une modification de statut côté école est automatiquement répercuté côté GLYPS, ce qui évite les coquilles de saisie manuelle.

---

## 10. Points d'intérêt et différences avec notre projet ENSEA

| Aspect | GLYPS | Notre projet ENSEA |
|--------|-------|---------------------|
| Périmètre | Vie associative complète (events, dossiers, trésorerie) | Paiement et portefeuille en caisse |
| Support physique | Bracelet NFC  | Carte étudiante RFID + QR code |
| Paiement | HelloAsso par asso (CB) | Solution à définir |
| Wallet | Oui, alimenté, sur bracelet | Oui, portefeuille rechargeable |
| Cloisonnement par asso | Oui (une asso ne voit pas les achats ailleurs) | À intégrer |
| Caution | Swikly intégré | Non prévu |
| Gestion événementielle | Très poussée (WEI, bus, mailing, appels) | Intéressant dans le cadre MyENSEA |
| Application mobile | À venir (rentrée) | Application MyENSEA |
| Hébergement | GLYPS (externe, Kubernetes) | Serveur ENSEA |

**Ce qui peut nous inspirer :**
- Le **cloisonnement des données par association** (une asso ne voit que ce qui la concerne) - modèle pertinent pour notre hiérarchisation des accès
- La **hiérarchisation des rôles** (bureau / staff / membres) avec historique conservé pour les passations
- Le **système de justificatifs obligatoires** en trésorerie pour professionnaliser la gestion
- La gestion fine des **process de validation d'événements** configurables par l'administration
- L'intégration de la **prévention VSS** dans le parcours d'inscription (vidéos obligatoires)

---

## Glossaire

**NFC (Near Field Communication)** : Technologie de communication sans contact à très courte distance, utilisée ici pour le bracelet et la lecture par les associations.

**Swikly** : Solution de caution digitale et sécurisée, permettant aux associations de sécuriser leurs transactions et leurs biens lors d'événements ou de locations, sans encaisser réellement la caution.

**RNA (Répertoire National des Associations)** - Numéro d'identification officiel d'une association loi 1901.

**SSO / OIDC / SAML** - Mécanismes d'authentification unique permettant aux étudiants de se connecter avec les identifiants de l'école, sans création de compte local.

**Kubernetes** - Système d'orchestration de conteneurs utilisé pour héberger et faire fonctionner la solution de manière isolée.

---

*Compte rendu rédigé par Maxime RAMBARANE-BARAT  
Stage ENSEA 2026*