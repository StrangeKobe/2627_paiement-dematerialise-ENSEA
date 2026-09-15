# Conformité réglementaire — Monnaie électronique
### Analyse de la situation du projet Paiement Dématérialisé RFID ENSEA

> **Auteur :** Maxime RAMBARANE-BARAT — Stage ENSEA 2026  
> **Contexte :** Sujet soulevé lors de la réunion avec Mr Moubêche (alumni, expert paiements)  
> **Sources :** Rapport Tracfin/DGT « L'encadrement des monnaies virtuelles » (juin 2014) — economie.gouv.fr · Position ACPR 2022-P-01 (mise à jour juillet 2023) · Article L.525-5 du Code monétaire et financier

---

## 1. Le problème identifié

Notre système crée un **portefeuille virtuel rechargeable via CB** (Exemple Stripe). L'étudiant dépose de l'argent réel sur un solde numérique, qu'il dépense ensuite à la Kfet, au BDE ou à Epicuria en scannant sa carte étudiante RFID ou un QR code.

Ce mécanisme ressemble à de la **monnaie électronique** au sens juridique français, une valeur monétaire stockée électroniquement, émise contre la remise de fonds, acceptée par des tiers. En principe, émettre de la monnaie électronique requiert un **agrément ACPR** (Autorité de Contrôle Prudentiel et de Résolution), ce qui serait rédhibitoire pour une association étudiante.

---

## 2. Ce que dit la réglementation

### 2.1 La définition de la monnaie électronique

Le rapport Tracfin (2014) distingue clairement deux notions qu'il ne faut pas confondre :

- **Monnaie virtuelle** (Bitcoin, etc.) : créée sans backing en monnaie légale, non réglementée comme monnaie électronique
- **Monnaie électronique** : valeur monétaire stockée électroniquement, émise **contre la remise de fonds**, représentant une créance sur l'émetteur — c'est cette catégorie qui nous concerne

Notre système est de la monnaie électronique au sens strict : l'étudiant donne des euros réels (via Stripe par exemple), reçoit un solde virtuel équivalent, et peut le dépenser auprès de tiers (les assos).

La **directive européenne monnaie électronique 2009/110/CE** (DME2), reprise dans le Code monétaire et financier français, définit la monnaie électronique comme :
> *une valeur monétaire stockée électroniquement, représentant une créance sur l'émetteur, émise contre remise de fonds et acceptée comme moyen de paiement par des tiers.*

Dans notre cas : l'étudiant remet 20 € → un solde de 20 € apparaît → ce solde est accepté par plusieurs associations distinctes. La qualification de monnaie électronique s'applique.

### 2.2 La notion d'encaissement pour compte de tiers

Mr Moubêche soulève un point supplémentaire : notre système pourrait aussi être qualifié d'**encaissement pour compte de tiers**. Le BDE encaisserait de l'argent pour le compte des autres associations - ce qui est une activité réglementée à part entière.

La donne change légèrement si les associations ne sont pas indépendantes mais membres d'une fédération commune (l'ADE). Dans ce cas, l'ADE encaisse pour ses propres membres, ce qui est moins problématique.

### 2.3 L'exemption d'agrément - Article L.525-5 du Code monétaire et financier

La loi prévoit explicitement une **exemption d'agrément** pour les systèmes qui répondent à toutes les conditions suivantes :

| Condition | Texte légal |
|-----------|-------------|
| **Réseau limité** | Utilisable uniquement dans les locaux de l'émetteur ou dans un réseau limité de personnes acceptant ce moyen de paiement |
| **Éventail limité** | Ou utilisable pour un éventail limité de biens ou de services |
| **Plafond de chargement** | La capacité maximale de chargement du support n'excède pas **250 €** |

La Position ACPR 2022-P-01 (mise à jour juillet 2023) précise et encadre ces conditions.  
→ Document de référence : [Position ACPR 2022-P-01](https://acpr.banque-france.fr/system/files/import/acpr/media/2023/07/26/20230726_position_2022-p-01.pdf)

### 2.4 Le seuil de déclaration obligatoire

Même sous exemption, une déclaration à l'ACPR devient obligatoire si le volume de paiements dépasse **1 million d'euros sur 12 mois glissants**.

En dessous de ce seuil, et si les conditions de réseau limité / éventail limité / plafond sont respectées, **aucune démarche d'agrément n'est requise**.

---

## 3. Positionnement du projet ENSEA

### 3.1 Analyse condition par condition

**Condition 1 — Réseau limité d'accepteurs ✅**

Le système n'est accepté que par trois entités : Kfet, BDE, Epicuria - toutes situées sur le campus de l'ENSEA, toutes membres de l'ADE. Il n'est pas question d'ouvrir ce moyen de paiement à des commerçants extérieurs ou à d'autres établissements. C'est un réseau fermé, géographiquement et institutionnellement borné.

**Condition 2 — Éventail limité de biens et services ✅**

Les achats possibles sont strictement limités à :
- Boissons et nourriture (Kfet)
- Événements et cotisations associatives (BDE)
- Restauration / traiteur (Epicuria)

Il n'est pas possible de retirer du cash, de payer des prestations externes, ni de transférer son solde à un tiers.

**Condition 3 — Plafond de chargement ✅**

Un plafond de rechargement est prévu dans l'architecture (valeur envisagée : **30 €** par rechargement, ou un plafond de solde maximal à définir). Ce montant est très largement en dessous du seuil légal de 250 €.

**Condition 4 — Volume annuel < 1 million d'euros ✅**

Les trois assos réunies ne généreront pas un million d'euros de transactions sur 12 mois. L'ENSEA est une école d'environ 700 étudiants. Même en estimant 5 transactions par étudiant par semaine à 2 € en moyenne, le volume annuel serait d'environ 350 000 € — on reste bien en dessous du seuil. Le même raisonnement s'applique si le système est étendu à l'ensemble des assos de l'école.

### 3.2 Conclusion de l'analyse

**Le projet ENSEA entre dans le cadre de l'exemption d'agrément prévue par la loi.** Aucun agrément ACPR n'est requis, et aucune déclaration n'est nécessaire tant que le volume reste sous 1M€/an.

Le **risque principal identifié par Mr Moubêche** est l'encaissement par le BDE pour des associations juridiquement indépendantes. Ce risque est atténué si l'on considère les assos comme des membres d'une même fédération (l'ADE) plutôt que comme des tiers distincts. Ce point mérite une clarification juridique avant déploiement.

Mr Moubêche recommande de solliciter le **pôle fintech-innovation de l'ACPR** pour valider officiellement que le projet tombe bien sous le régime carte campus / scope limité.

---

## 4. Ce que l'exemption implique malgré tout

L'exemption ne signifie pas l'absence totale d'obligations. La position ACPR 2022-P-01 impose aux systèmes exemptés plusieurs bonnes pratiques :

### 4.1 Obligation d'information dans les CGU

Les Conditions Générales d'Utilisation doivent mentionner explicitement que :
- Le système opère dans le cadre d'une exemption d'agrément
- Les utilisateurs ne bénéficient **pas** des protections prévues par le Code monétaire et financier pour les services de paiement agréés (garantie des fonds, recours ACPR, etc.)
- Le solde virtuel n'est pas remboursable de droit (sauf clause contraire définie dans les CGU)

### 4.2 Mesures de protection des utilisateurs

Même sans agrément, l'ACPR vérifie dans les dossiers d'exemption qu'un minimum de protection des utilisateurs est mis en œuvre. Pour nous cela signifie :
- Pas de perte de solde en cas de bug ou de coupure - les données sont sauvegardées en base
- Procédure claire si un étudiant quitte l'école avec un solde restant
- Traçabilité complète des transactions

### 4.3 Séparation des activités

Si l'ADE exerce d'autres activités réglementées (collecte de cotisations, billetterie), elle doit s'assurer qu'il n'y a pas de confusion pour les utilisateurs entre le portefeuille virtuel (exempté) et d'autres instruments de paiement.

---

## 5. Points encore à clarifier

### Résolus ✅

- **Qualification exacte de l'ADE** : association loi 1901 - confirmé.
- **Volume annuel** : estimé à ~350 000 €/an pour les 3 assos pilotes, largement sous le seuil de 1M€. Le même raisonnement s'applique à l'échelle de toutes les assos de l'école.
- **Retour de Mr Moubêche** : reçu. Il confirme que le projet qualifie probablement d'encaissement pour compte de tiers, avec un risque principal sur l'indépendance juridique des assos. Il recommande de contacter le pôle fintech-innovation de l'ACPR. Voir les questions clés qu'il soulève en section 5.2.
- **Contact ACPR pris** : l'ACPR a répondu et détaillé la procédure d'exemption (déclaration préalable au titre de l'article L. 521-3 CMF, formulaire, réunion de présentation). **Voir la section 6** pour le détail et la liste des livrables à préparer.

### En cours / à traiter 🔲

- **Responsable de traitement désigné** : qui signe officiellement comme responsable du système — l'ADE, l'ENSEA, ou les deux conjointement ? Un troisième acteur possible est la fédération des assos. À clarifier avec l'administration.
- **Rédaction des CGU** : à faire avant tout déploiement public. Doit mentionner explicitement le cadre d'exemption. À traiter ultérieurement.
- **Plafond de solde maximal** : valeur suggérée de **30 €** à confirmer et à intégrer dans les CGU.
- **Procédure de remboursement solde résiduel** : à définir en fonction de la solution de paiement retenue (Stripe, Monetico, Lyra…). À traiter en même temps que le choix de solution.
- **Contacter le pôle fintech-innovation de l'ACPR** : recommandé par Mr Moubêche pour validation officielle du cadre d'exemption appliqué à notre cas.

### 5.2 Questions soulevées par Mr Moubêche (à répondre pour la suite)

Mr Moubêche a listé les questions juridiques clés auxquelles il faudra répondre, notamment si on sollicite l'ACPR :

- Qui détient juridiquement les fonds ?
- Qui est créancier des soldes étudiants ?
- Que devient un solde inutilisé après 1 an ?
- Que se passe-t-il si le BDE est dissous ?
- Pourquoi le dispositif relève de l'exemption de réseau limité ? (ACPR)
- Quel est l'encours maximal pouvant être stocké ?
- Qui supporte le risque de fraude ?
- Qui rembourse en cas d'erreur de débit ?

---

## 6. Retour de l'ACPR — procédure d'exemption d'établissement de paiement

L'ACPR a répondu à notre demande d'information. Le message complet est archivé dans
`Réglementation/Reponse_ACPR_procedure_exemption.md`. Points à retenir :

### 6.1 Le cadre juridique

- Fondement : **I de l'article L. 521-3 du Code monétaire et financier** — une entreprise peut fournir des services de paiement fondés sur des moyens de paiement acceptés uniquement dans ses locaux ou, dans le cadre d'un accord commercial, **dans un réseau limité de personnes** ou **pour un éventail limité de biens ou de services**.
- **Déclaration préalable** : dans ce cas, l'entreprise adresse une déclaration à l'ACPR **avant** de commencer son activité. L'ACPR dispose alors de **3 mois** à réception pour notifier au déclarant qu'il remplit bien les conditions.
- **Seuil de 1 M€** (II de l'article L. 521-3) : la déclaration préalable n'est **obligatoire** que si la valeur totale des opérations de paiement (les flux) dépasse **1 million d'euros sur 12 mois**. En dessous, les conditions du I doivent quand même être respectées, mais **aucune déclaration n'est requise**.

> **Notre situation** : volume estimé ~350 k€/an → **sous le seuil de 1 M€** → la déclaration préalable n'est pas juridiquement obligatoire aujourd'hui. Faire malgré tout la démarche apporterait une **confirmation officielle** du cadre d'exemption (sécurise le projet, utile vis-à-vis de l'école et des assos).

### 6.2 Documents et liens fournis par l'ACPR

- **Formulaire de demande d'exemption / d'enregistrement** (établissement de paiement et prestataire de service d'information sur les comptes) :
  https://acpr.banque-france.fr/autoriser/procedures-secteur-banque/agrement-autorisation-ou-enregistrement/etablissement-de-paiement-et-prestataire-de-service-dinformation-sur-les-comptes
- **Position ACPR** sur les notions de « réseau limité d'accepteurs » et d'« éventail limité de biens et services » :
  https://acpr.banque-france.fr/sites/default/files/media/2022/07/21/20220721_projet_modification_position_2017-p-01.pdf
- **Exigences de sécurité des moyens de paiement (Banque de France)** : document joint, archivé dans `Réglementation/Avis de la Banque de France sur la sécurité des paiements.docx`.

### 6.3 Livrable à préparer avant la réunion de présentation ACPR

L'ACPR demande une **présentation du projet** (support type PowerPoint), préalable à une réunion, couvrant :

- [ ] **Présentation de la structure** : gouvernance envisagée (dirigeants effectifs + organe de surveillance) et actionnariat / composition (ici : l'ADE, ses statuts, son bureau, le lien avec l'ENSEA).
- [ ] **Motifs de l'exemption** : argumentaire « réseau limité » + « éventail limité », en s'appuyant sur la Position ACPR (§6.2). Reprendre l'analyse de la section 3 de ce document.
- [ ] **Activité envisagée** : description du service, **typologie de la clientèle** (étudiants ENSEA), **tarification envisagée** (frais à la charge des assos, gratuité pour l'étudiant, pourboire HelloAsso).
- [ ] **Prestations essentielles externalisées** : fonctions concernées et prestataires pressentis — a minima **HelloAsso** (encaissement CB), hébergement, éventuellement banque de l'ADE.
- [ ] **Business plan sur 3 ans** : évolution des volumes de paiement et des comptes, avec les **hypothèses** retenues (les business models de `../Systèmes de paiment/` fournissent la base).
- [ ] **Structure et modalités de financement du projet**.
- [ ] **Dispositif de sécurité des moyens de paiement** : s'appuyer sur les exigences de la Banque de France (document joint) — QR à usage unique et courte durée, écritures atomiques, code de sécurité, plafonds, anonymisation, pas de stockage des données carte.

### 6.4 Prochaines étapes

1. Formaliser le **rattachement statutaire** des pôles à l'ADE (prérequis à tout le reste).
2. Rédiger le support de présentation ci-dessus.
3. Répondre aux questions de Mr Moubêche (§5.2), qui recoupent largement la demande ACPR.
4. Renseigner le formulaire d'exemption si la déclaration est décidée.
5. Finaliser les **CGU** (cadre d'exemption, absence des protections du CMF, plafonds, remboursement).

---

*Document rédigé par Maxime RAMBARANE-BARAT — Stage ENSEA 2026*  
*Dernière mise à jour : août 2026*