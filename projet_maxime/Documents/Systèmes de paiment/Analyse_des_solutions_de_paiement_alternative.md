# Analyse des solutions de paiement alternatives
### Comparatif Stripe · Lyra · Monetico · Payplug · iRaiser · Wero · HelloAsso

> **Auteur :** Maxime RAMBARANE-BARAT — Stage ENSEA 2026
> **Contexte :** Suite à la réunion du 05 juin 2026 avec Mr Moubêche — investigation des alternatives à Stripe avant de trancher
> **Voir aussi :** `compte-rendu-reunion-paiement.md` · `conformite-monnaie-electronique.md`

---

## ⚠️ Note préalable sur les noms

Lors de la réunion, les solutions « IIRAF » et « PayPlus » ont été mentionnées. Après recherche, aucune plateforme de paiement ne porte exactement ces noms. Les candidats les plus probables sont :

- **IIRAF** → **iRaiser** (plateforme de paiement française dédiée aux associations, fondations et ONG)
- **PayPlus** → **Payplug** (solution de paiement française, groupe BPCE)

**→ À confirmer avec Mr Moubêche lors de la prochaine réunion.** L'analyse ci-dessous porte sur iRaiser et Payplug.

---

## 1. Rappel du besoin

Notre cas d'usage est particulier et ne correspond pas au e-commerce classique. Il faut le garder en tête pour évaluer chaque solution :

1. **Rechargement du portefeuille virtuel** : l'étudiant paie par CB depuis son smartphone → le solde est crédité en base Django. C'est la **seule** opération qui passe par le prestataire de paiement.
2. **Paiement aux caisses** (Kfet, BDE, Epicuria) : débit du solde interne via scan RFID/QR. **Aucun prestataire impliqué** — c'est notre base de données qui fait foi.
3. **Reversement** : l'argent collecté doit in fine être réparti entre les associations.

Conséquences :

- Il nous faut impérativement une **API** appelable depuis Django (création d'un paiement, webhook/notification de confirmation, remboursement).
- Les transactions de rechargement seront **peu nombreuses mais d'un montant moyen correct** (~10–30 €), ce qui est favorable : la part fixe des frais (0,20–0,25 €) pèse moins sur un rechargement de 20 € que sur un café à 0,50 €. C'est l'un des grands avantages du modèle portefeuille par rapport au paiement CB à chaque achat.
- Le client est **toujours un étudiant en France** → quasi exclusivement des cartes CB/Visa/Mastercard françaises de particuliers. Les grilles tarifaires « zone euro / cartes consumer » s'appliquent donc presque systématiquement, et les frais majorés sur cartes hors UE seront marginaux.

---

## 2. Les solutions analysées

### 2.1 Stripe (référence actuelle)

**Origine.** Fintech américano-irlandaise, leader mondial du paiement en ligne pour développeurs. Solution déjà identifiée comme candidat principal dans notre étude initiale.

**Nature.** Prestataire de services de paiement (PSP) full-API : API REST complète, SDK Python officiel, webhooks, mode test (sandbox), documentation considérée comme la meilleure du marché.

**Frais (indicatifs, à vérifier sur stripe.com/fr/pricing).** De l'ordre de 1,5 % + 0,25 € par transaction pour les cartes standard européennes, davantage pour les cartes hors EEE. Pas d'abonnement, pas de frais de mise en service, pas de minimum de facturation.

**Point soulevé en réunion.** Stripe étant un acteur américain, les frais sur certaines cartes (notamment Visa/Mastercard émises hors UE) peuvent être supérieurs à ceux d'un acquéreur français qui bénéficie de l'interchange CB domestique. Dans notre cas (cartes françaises de particuliers à ~99 %), l'écart réel devrait être faible — mais c'est un point à chiffrer précisément.

**Dans notre projet.** ✅ Intégration Django triviale, sandbox gratuite, parfait pour le prototypage du stage. La question ouverte n'est pas la faisabilité mais le coût comparé et la dépendance à un acteur non européen.

---

### 2.2 Lyra (PayZen / Lyra Collect)

**Origine.** Entreprise française fondée à Toulouse en 2001, acteur historique du paiement. Lyra édite la plateforme **PayZen**, utilisée en marque blanche par de nombreuses banques françaises (Banque Populaire, Caisse d'Épargne, Société Générale, La Banque Postale…).

**Nature.** Deux offres distinctes, et la distinction est importante pour nous :

| Offre | Principe | Prérequis |
|-------|----------|-----------|
| **PayZen** | Passerelle technique de paiement | Nécessite un **contrat VAD** (vente à distance) avec sa propre banque — c'est la banque qui encaisse |
| **Lyra Collect** | Solution « tout-en-un » : Lyra est à la fois la passerelle **et** l'acquéreur | Pas de contrat bancaire VAD à négocier — KYC directement chez Lyra (statuts, IBAN, pièce d'identité du représentant) |

Pour une association sans relation bancaire « pro e-commerce » établie, **Lyra Collect** est l'offre pertinente.

**API.** Oui — API REST documentée (docs.lyra.com), formulaire de paiement embarqué ou redirigé, webhooks (IPN), liens de paiement. Documentation en français, support basé en France.

**Frais (indicatifs).** Lyra Collect : environ 1,4 % + 0,20 € par transaction pour les cartes européennes, frais de mise en service (~99 € HT), et surtout un **minimum de facturation mensuel** (~40 € HT/mois constaté par le passé) — tarification finale sur devis. Ce minimum mensuel est un vrai sujet pour nous : avec un volume associatif faible, il pourrait coûter plus cher que les commissions elles-mêmes.

**Dans notre projet.** ✅ Techniquement adapté (API complète, acteur français, frais CB domestiques compétitifs). ⚠️ Le minimum de facturation et les frais d'entrée sont à négocier — demander un devis en présentant le profil associatif.

---

### 2.3 Monetico (Crédit Mutuel / CIC)

**Origine.** Solution de paiement e-commerce des groupes bancaires Crédit Mutuel et CIC. Infrastructure 100 % française, flux hébergés et traités en France, certifiée PCI-DSS et conforme DSP2.

**Nature.** Plateforme de paiement bancaire classique : c'est un **service associé à un compte professionnel Crédit Mutuel ou CIC**. Le parcours est entièrement bancaire :

1. Ouvrir (ou posséder) un compte pro/association au Crédit Mutuel ou CIC
2. Rendez-vous avec le conseiller → contrat VADS (vente à distance sécurisée)
3. Étude du dossier par la banque → proposition tarifaire personnalisée (frais d'installation + abonnement mensuel + taux de commission négocié)

Monetico Online cible explicitement « les e-commerçants et **associations** » — le statut associatif est donc prévu dans leur offre.

**API.** Oui, mais d'une génération plus ancienne que Stripe : interface de type formulaire HMAC (kit Monetico Paiement, modules pour CMS, intégration custom possible). Pas de SDK Python officiel — l'intégration Django demande d'implémenter soi-même la signature/vérification HMAC. Faisable, documenté, mais nettement moins confortable que Stripe.

**Frais.** Non publics — entièrement sur devis via le conseiller bancaire. Avantage structurel : en tant qu'acquéreur CB français, les commissions sur cartes CB domestiques peuvent être très basses (interchange européen plafonné à 0,2–0,3 %), surtout si l'ADE a déjà son compte dans ce réseau bancaire.

**Dans notre projet.** ✅ Pertinent **si et seulement si** l'ADE (ou la fédération) est cliente Crédit Mutuel/CIC ou prête à le devenir. ⚠️ Attention au point soulevé en réunion : ne pas passer par le conseiller bancaire généraliste pour les questions d'architecture — viser directement l'équipe technique Monetico. ⚠️ Vérifier quelle banque détient le compte de l'ADE actuellement : c'est probablement le critère décisif pour cette piste.

---

### 2.4 Payplug

**Origine.** Fintech française fondée en 2012, filiale du **groupe BPCE** (Banque Populaire / Caisse d'Épargne). Positionnée comme l'« anti-Stripe français » pour TPE/PME.

**Nature.** PSP-acquéreur : comme Lyra Collect, Payplug contracte directement avec les réseaux bancaires — **pas besoin de contrat VAD avec sa banque**, juste un compte Payplug (KYC, activation sous ~48 h). Compte de test disponible dès l'inscription.

**API.** Oui — API REST moderne, **SDK Python officiel**, webhooks, liens de paiement, paiement intégré. C'est, avec Stripe, la solution la plus confortable de cette liste pour une intégration Django.

**Frais (indicatifs, grille publique).** Modèle abonnement + commission :
- Carte particulier zone euro : **1,1 % + 0,25 €** en ligne
- Carte business ou hors zone euro : 2,5–2,9 % + 0,25 €
- Abonnement mensuel selon la formule (l'offre Pro est affichée à ~30 €/mois ; vérifier les conditions de l'offre d'entrée de gamme)

Le taux de 1,1 % sur cartes particuliers zone euro est **inférieur à Stripe** (~1,5 %) — cohérent avec l'argument « frais CB franco-français » de Mr Moubêche. Mais l'abonnement mensuel fixe peut annuler cet avantage à faible volume : à 30 €/mois, il faut environ 7 500 €/mois de rechargements pour que l'économie de 0,4 point compense l'abonnement par rapport à Stripe.

**Dans notre projet.** ✅ Très bon candidat : API moderne avec SDK Python, acteur bancaire français, taux domestiques compétitifs. ⚠️ Faire le calcul abonnement vs commission selon le volume réel attendu, et vérifier l'éligibilité du statut associatif.

---

### 2.5 iRaiser (hypothèse pour « IIRAF »)

**Origine.** Entreprise française (Nantes), spécialisée depuis 2009 dans la collecte de fonds en ligne pour les **associations, fondations et ONG**.

**Nature.** Ce n'est pas un PSP généraliste mais une **plateforme métier de fundraising** : formulaires de dons, adhésions, billetterie, ventes, avec un « iRaiser Payment System » qui s'appuie sur… **Stripe** en sous-jacent. Tarification sur devis (modèle SaaS avec abonnement).

**API.** Outils d'export et de synchronisation de données, mais ce n'est pas une API de paiement bas niveau pensée pour piloter des rechargements de portefeuille depuis une app Django.

**Dans notre projet.** ❌ **Inadapté.** iRaiser résout le problème « collecter des dons/adhésions pour une grande asso » — pas « créditer un wallet interne via API ». Comme leur paiement repose sur Stripe, passer par iRaiser reviendrait à ajouter une couche payante au-dessus de la solution qu'on évalue déjà en direct. À écarter, sauf si Mr Moubêche pensait à un autre acteur (d'où l'importance de confirmer le nom).

---

### 2.6 Wero

**Origine.** Portefeuille de paiement **européen** développé par l'EPI (European Payments Initiative), consortium des grandes banques européennes (BPCE, BNP Paribas, Crédit Agricole, Deutsche Bank…). Objectif : une alternative souveraine à Visa/Mastercard/PayPal, basée sur le **virement instantané de compte à compte** (pas de carte du tout).

**État du déploiement (juin 2026).** Le calendrier est le point clé :

| Cas d'usage | Statut en France |
|---|---|
| P2P (entre particuliers) | ✅ Disponible depuis 2024 |
| E-commerce (paiement marchand en ligne) | 🔶 Tout juste lancé — premières transactions BPCE en avril 2026, généralisation aux autres banques fin 2026 |
| Paiement en magasin | ❌ Prévu 2027 |

Il n'existe **pas encore d'offre dédiée aux associations** ni de processus d'onboarding marchand ouvert en libre-service en France — l'acceptation passe pour l'instant par des PSP partenaires (Payplug a d'ailleurs réalisé le premier paiement e-commerce Wero français, Worldline et HiPay suivent).

**Intérêt théorique.** Le paiement compte-à-compte supprime l'interchange carte : à terme, les frais pourraient être inférieurs aux frais CB. Et l'argument souveraineté européenne est réel.

**Dans notre projet.** ❌ **Pas comme solution principale en 2026** : trop tôt, pas d'offre association, pas d'API marchande accessible directement. ✅ **Mais à garder en tête comme moyen de paiement additionnel** : si on retient Payplug (premier PSP compatible Wero en France), on pourrait activer Wero comme option de rechargement quasi gratuitement quand l'offre sera mature. C'est un argument de plus en faveur de Payplug.

---

### 2.7 HelloAsso (proposition complémentaire)

**Origine.** Entreprise sociale française (Bordeaux), leader du numérique associatif : plus de 400 000 associations utilisatrices, 2 Md€ collectés depuis 2009.

**Nature.** Plateforme de paiement **exclusivement réservée aux associations loi 1901** — exactement notre statut. Modèle économique unique : **0 frais, 0 commission, 0 abonnement** pour l'association ; HelloAsso se finance par les pourboires volontaires laissés par les payeurs au moment du paiement.

**API.** Oui — **HelloAsso Checkout**, module de paiement intégrable par API REST, avec sandbox de test, documentation développeur (dev.helloasso.com), notifications de confirmation de paiement. Ils se positionnent explicitement comme une alternative gratuite à « Stripe, PayPal, Payplug » pour les assos. L'argent collecté est reversé sur le compte bancaire de l'association chaque mois ou à la demande.

**Dans notre projet.** ✅ Candidat très sérieux qui mérite d'être ajouté au comparatif : **100 % gratuit** sur un volume de ~350 k€/an, cela représente une économie de l'ordre de 4 000–6 000 €/an par rapport à un PSP classique. ⚠️ Deux points à valider impérativement avec eux :
1. Le cas d'usage « rechargement de portefeuille virtuel » est-il accepté par leurs CGU ? Leur outil est pensé pour dons, adhésions, billetterie et boutique — un wallet rechargeable est un usage atypique.
2. L'expérience utilisateur impose l'écran de pourboire volontaire à chaque rechargement (contournable en mettant 0 €, mais à montrer aux assos).

---

## 3. Tableau comparatif

| Critère | Stripe | Lyra Collect | Monetico | Payplug | iRaiser | Wero | HelloAsso |
|---|---|---|---|---|---|---|---|
| **Nationalité** | 🇺🇸/🇮🇪 | 🇫🇷 | 🇫🇷 | 🇫🇷 (BPCE) | 🇫🇷 | 🇪🇺 | 🇫🇷 |
| **API REST** | ✅ Excellente | ✅ Bonne | 🔶 HMAC, datée | ✅ Bonne + SDK Python | ❌ (métier) | ❌ via PSP | ✅ Checkout |
| **SDK Python** | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ (REST simple) |
| **Sandbox de test** | ✅ | ✅ | 🔶 (TPE test) | ✅ | ❌ | ❌ | ✅ |
| **Commission carte FR particulier** | ~1,5 % + 0,25 € | ~1,4 % + 0,20 € (devis) | Sur devis (potentiellement < 1 %) | 1,1 % + 0,25 € | Devis (Stripe sous-jacent) | N/A | **0 €** |
| **Coûts fixes** | Aucun | Mise en service + min. mensuel ~40 € HT | Installation + abonnement | Abonnement mensuel | Abonnement SaaS | N/A | **Aucun** |
| **Prérequis bancaire** | Aucun | Aucun (KYC Lyra) | **Compte CM/CIC obligatoire** | Aucun (KYC Payplug) | — | Compte bancaire partenaire | Statut asso loi 1901 |
| **Offre association** | Standard | Standard | ✅ Explicite | Standard | ✅ Cœur de cible (dons) | ❌ | ✅ Exclusif |
| **Multi-comptes natif (type Connect)** | ✅ Stripe Connect | 🔶 Offre Marketplace | ❌ | 🔶 Offre Payfac (Entreprise) | ❌ | ❌ | ❌ (1 compte/asso possible) |
| **Verdict pour le projet** | ✅ Référence technique | 🔶 Devis à demander | 🔶 Si banque CM/CIC | ✅ Challenger sérieux | ❌ Écarté | ⏳ Plus tard, via PSP | ✅ À creuser (CGU) |

> Les frais sont donnés à titre indicatif d'après les grilles publiques — **toutes ces solutions pratiquent le devis personnalisé**, et le statut associatif + le volume prévisionnel sont des arguments de négociation. Ne pas comparer définitivement sans devis écrits.

---

## 4. Repenser le multi-assos : le modèle « compte mère »

### 4.1 Le constat qui change tout

L'architecture Stripe Connect (un compte par asso) avait été envisagée pour router automatiquement l'argent vers chaque association. Mais la réunion avec Mr Moubêche a remis en question ce besoin : **la répartition comptable peut être faite par notre propre base Django**, le prestataire de paiement n'a pas besoin de la connaître.

Point technique vérifié qui conforte cette analyse : un compte Stripe standard ne permet d'enregistrer **qu'un seul compte bancaire externe de versement par devise**. Il est donc impossible, même en le voulant, de faire éclater les virements sortants vers 3 IBAN différents depuis un compte Stripe standard — il faudrait Connect pour ça. Autrement dit : **si on abandonne le routage automatique, on abandonne aussi la seule raison d'être de Connect.**

### 4.2 Le modèle compte mère

```
Étudiant ──CB──▶ PSP (Stripe/Payplug/...) ──payout──▶ Compte bancaire ADE (unique)
                                                            │
                                                            │ virements SEPA périodiques
                                                            │ (montants calculés par Django)
                                                            ▼
                                            IBAN Kfet · IBAN BDE · IBAN Epicuria
```

Fonctionnement :

1. **Tous les rechargements** arrivent sur un seul compte PSP standard, versé vers l'IBAN unique de l'ADE.
2. **Chaque transaction en caisse** est enregistrée dans Django avec l'association bénéficiaire (`Transaction.association`). La comptabilité par asso existe déjà implicitement dans notre modèle de données — il suffit de l'agréger.
3. **En fin de mois**, Django génère un rapport de répartition (CA Kfet / BDE / Epicuria, déduction faite des frais PSP au prorata), et le trésorier de l'ADE effectue les virements SEPA correspondants depuis le compte bancaire — virements bancaires classiques, gratuits, hors PSP.

Avantages :

- **Simplicité technique radicale** : un compte standard chez n'importe quel PSP suffit → toutes les solutions du comparatif deviennent éligibles, y compris Monetico et HelloAsso qui n'ont pas d'équivalent de Connect.
- **Un seul KYC** au lieu de trois (un onboarding Connect par asso aurait demandé statuts + IBAN + représentant légal pour chacune).
- **Cohérence réglementaire** : ce modèle matérialise exactement la lecture « l'ADE encaisse pour ses propres membres » défendue dans notre analyse de conformité — plutôt que « le BDE encaisse pour des tiers ».

Inconvénients / points de vigilance :

- **L'argent transite par un compte unique** : la confiance entre assos repose sur la transparence de la compta Django. Le rapport mensuel de répartition doit être consultable par chaque trésorier (feature à prévoir dans l'admin Django).
- **Délai de reversement** : les assos touchent leur argent en fin de mois, pas en temps réel. À valider avec les trésoriers (en pratique, leurs charges sont mensuelles, ça devrait passer).
- **Responsabilité** : le trésorier de l'entité mère porte la responsabilité des fonds en transit — à formaliser (convention entre assos).

### 4.3 Avec ou sans fédération : qu'est-ce que ça change ?

C'est le point juridique central, qui conditionne à la fois la conformité et le choix du PSP.

**Cas A — Une fédération existe (ADE, association loi 1901 regroupant Kfet, BDE, Epicuria).**

- Le compte mère est ouvert au nom de l'ADE. Une seule entité juridique signe le contrat PSP, un seul KYC.
- Juridiquement, l'ADE encaisse **pour ses membres**, pas pour des tiers → le risque « encaissement pour compte de tiers » identifié par Mr Moubêche est fortement atténué.
- Les reversements internes sont des flux entre une fédération et ses membres, ce qui est une pratique associative courante.
- ✅ **C'est la configuration cible.** D'après notre analyse de conformité, l'ADE est bien une association loi 1901 — reste à vérifier que Kfet, BDE et Epicuria en sont **statutairement membres** (lire les statuts de l'ADE), et pas seulement des assos amies.

**Cas B — Pas de fédération (3 assos juridiquement indépendantes).**

Deux sous-options, aucune n'est idéale :

- **B1 : une asso (ex. le BDE) joue le rôle de compte mère.** C'est précisément le scénario d'« encaissement pour compte de tiers » pointé comme risque principal — activité réglementée nécessitant en principe un agrément ou une exemption spécifique. ❌ À éviter.
- **B2 : un contrat PSP par asso** (3 comptes Stripe standard, ou Stripe Connect, ou l'offre Marketplace de Lyra / Payfac de Payplug). Techniquement gérable mais : 3 KYC, 3 contrats, et surtout le portefeuille de l'étudiant devrait être **segmenté par asso** (un solde Kfet ≠ un solde BDE), ce qui détruit l'expérience utilisateur « un seul wallet partout sur le campus ». 🔶 Solution de repli dégradée.

**Conclusion :** la valeur du projet (wallet unique multi-assos) **dépend de l'existence d'une structure fédérative**. Si l'adhésion des trois assos à l'ADE n'est pas statutairement propre, la formaliser (ou créer une convention) est probablement le chantier le plus rentable du projet — plus que n'importe quel choix technique.

### 4.4 Compatibilité du modèle compte mère par solution

| Solution | Compte mère ADE possible ? | Remarque |
|---|---|---|
| Stripe standard | ✅ | Payout vers l'IBAN ADE unique ; répartition hors Stripe |
| Lyra Collect | ✅ | Idem ; demander si le devis change selon le statut fédératif |
| Monetico | ✅ | Naturel : le compte mère = le compte bancaire CM/CIC de l'ADE |
| Payplug | ✅ | Idem Stripe ; bonus Wero à terme |
| HelloAsso | ✅ | Compte HelloAsso au nom de l'ADE ; reversement mensuel vers son IBAN |
| iRaiser | — | Écarté |
| Wero | — | Pas d'offre marchande directe en 2026 |

Le modèle compte mère est **agnostique au PSP** : c'est un argument supplémentaire en sa faveur, puisqu'il préserve la liberté de changer de prestataire plus tard sans toucher à l'architecture.

---

## 5. Synthèse et recommandations pour la réunion

1. **Confirmer les noms** « IIRAF » et « PayPlus » avec Mr Moubêche (hypothèses : iRaiser, Payplug).
2. **Valider le modèle compte mère** : il simplifie tout (technique, KYC, réglementaire) et rend Connect inutile. Pré-requis : confirmer le lien statutaire entre l'ADE et les 3 assos.
3. **Shortlist proposée** :
   - **Stripe** — référence pour le prototypage (sandbox immédiate, SDK Python), décision finale sur les frais à réévaluer ensuite.
   - **Payplug** — challenger français le plus crédible : API moderne + SDK Python, 1,1 % zone euro, compatible Wero à terme. Calcul abonnement vs volume à faire.
   - **HelloAsso** — à contacter en priorité : si le cas d'usage wallet est accepté dans leurs CGU, le 0 % de frais est imbattable pour une asso.
4. **Devis à demander** : Lyra Collect (en négociant le minimum mensuel) et Monetico (uniquement après avoir identifié la banque actuelle de l'ADE).
5. **Écarter** : iRaiser (plateforme de dons, pas une API de paiement — et basée sur Stripe). **Reporter** : Wero (offre marchande française naissante, pas d'offre association — à réévaluer en 2027 comme moyen de paiement additionnel).

---

## 6. Questions ouvertes

- [ ] « IIRAF » et « PayPlus » : confirmation des noms exacts auprès de Mr Moubêche
- [ ] Quelle banque détient le compte de l'ADE ? (conditionne la piste Monetico)
- [ ] Kfet, BDE, Epicuria sont-elles statutairement membres de l'ADE ? (lecture des statuts)
- [ ] Contacter HelloAsso : le rechargement de wallet entre-t-il dans leurs CGU ?
- [ ] Volume mensuel prévisionnel de rechargements (pour le calcul abonnement vs commission Payplug/Lyra)
- [ ] Demander les devis écrits Lyra Collect et Payplug avec le profil « association, ~30 k€/mois »

---

*Document rédigé par Maxime RAMBARANE-BARAT — Stage ENSEA 2026*
*Dernière mise à jour : 10 juin 2026*