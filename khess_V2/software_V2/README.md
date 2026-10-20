# Application Cashless ENSEA — version V2

L’application se trouve dans [`Test_App_Django/`](Test_App_Django/).
Cette copie reprend les fichiers applicatifs du commit
[`74b5b43`](https://github.com/StrangeKobe/2627_paiement-dematerialise-ENSEA/commit/74b5b43bd2f72db6c0ca7d0c20a5d0a4166fca00) de `feature/cas-auth`, avec les tests de référence
ajoutés par `733ef2d`. Le code de `projet_maxime` sur `main` n’est pas modifié.
Les environnements Python, `.env`, bases SQLite, caches et sauvegardes sont exclus.

## Lancer localement (PowerShell)

Python 3.13 est utilisé ; les dépendances incluent Django 6.1 et python-cas 1.7.2.
Depuis ce dépôt, réutiliser le **venv Windows existant** :

```powershell
$repo = (git rev-parse --show-toplevel).Trim()
$python = Join-Path $repo 'projet_maxime\Software\Tutoriel_Application_Cashless_ENSEA\Test_App_Django\venv\Scripts\python.exe'
Set-Location (Join-Path $repo 'khess_V2\software_V2\Test_App_Django')
$env:CLE_SECRETE = & $python -c "import secrets; print(secrets.token_urlsafe(48))"
$env:CAS_ENABLED = 'False'
$env:EMAIL_HOST = ''
& $python manage.py migrate
& $python manage.py createsuperuser --username dev_admin --email dev_admin@example.invalid
& $python manage.py runserver 127.0.0.1:8000
```

Choisir un mot de passe local pour ce compte fictif. Ouvrir
<http://127.0.0.1:8000/connexion/> ; arrêter le serveur avec `Ctrl+C`.
La clé aléatoire reste dans ce terminal, les courriels sont affichés en console,
et `migrate` crée une base locale vide dans V2. Aucun compte local n’est livré.
Sur une autre machine, fournir à `$python` le chemin de son environnement Python
3.13 et installer les dépendances avec `& $python -m pip install -r requirements.txt`.
Ne pas utiliser le `.venv` Linux du projet historique.

## Changements par rapport à l’application d’origine

Résumé du document « ENSEA Cashless — bilan des modifications » préparé le
20 octobre 2026 : **7 fichiers modifiés et 10 ajoutés**, base d’origine `ee9063b`.
Les chemins ci-dessous sont relatifs à `Test_App_Django/`.

| Fichier(s) | Ajout ou modification et objectif |
| --- | --- |
| `.env.example`, `cashless/settings.py` | Variables CAS et backend d’authentification ; CAS et création automatique désactivés par défaut. |
| `requirements.txt` | Ajout de `python-cas==1.7.2`. |
| `caisse/cas_auth.py` | Validation des tickets via HTTPS, contrôle de l’identité et de l’éligibilité, association ou création encadrée des comptes. |
| `caisse/cas_views.py`, `caisse/urls.py` | Départ/retour CAS, session Django et déconnexion locale ; connexion classique si CAS est désactivé ou incomplet. |
| `caisse/models.py`, `caisse/migrations/0003_casidentity.py` | Table `CASIdentity` reliant un identifiant CAS stable à un utilisateur local, sans déplacer son portefeuille. |
| `caisse/management/commands/link_cas_identity.py` et les deux `__init__.py` de gestion | Commande pour appliquer une correspondance explicitement approuvée, jamais déduite du nom ou de l’email. |
| `caisse/middleware.py` | Laisse terminer le retour CAS avant d’appliquer le contrôle du code de sécurité. |
| `caisse/templates/caisse/cas_error.html`, `cas_logged_out.html` dans le même dossier | Pages d’échec et de déconnexion CAS locale. |
| `caisse/tests.py` | Remplace le fichier vide par 6 tests du fonctionnement local initial. |
| `caisse/test_cas.py` | Ajoute 23 tests CAS ; seule la réponse HTTP du serveur externe est simulée. |
| `CAS_SETUP.md` | Guide complet de configuration, correspondances de comptes et décisions attendues d’ENSEA IT. |

La logique de caisse, les rôles `Affectation`, les utilisateurs, soldes et codes
existants sont conservés. Le transfert V2 n’intègre aucune donnée de la base locale.

## Vérifications locales sur cette copie V2

<!-- V2_TEST_RESULTS -->
Vérifications exécutées sur **cette copie V2** avec le venv Windows existant
(Python 3.13.3, Django 6.1), CAS désactivé et clé temporaire non enregistrée :

- `git diff --cached --check` : aucune erreur après retrait des deux espaces/lignes superflus dans les copies de `models.py` et `settings.py`.
- `manage.py check` : `System check identified no issues (0 silenced).`
- `manage.py test --verbosity 2` : `Ran 29 tests in 30.845s` — `OK`.

Les 29 tests réussissent (6 tests de référence et 23 tests CAS). La base de
tests est temporaire et en mémoire ; aucune base ni aucun compte local réel
n’est copié ou publié. Les réponses CAS sont simulées uniquement dans les tests.
<!-- END_V2_TEST_RESULTS -->

Pour reproduire les vérifications avec les variables locales ci-dessus :

```powershell
& $python -B manage.py check
& $python -B manage.py test --verbosity 2
```

Les tests utilisent une base temporaire et des identités fictives. Ils couvrent
la connexion locale, les profils sans doublon, les refus d’accès, les tickets CAS
acceptés/refusés, les correspondances approuvées, la conservation des soldes/rôles,
les comptes désactivés, le code de sécurité et sa remise à zéro après déconnexion.

## Fonctionnement actuel et limites

**Testé localement :** connexion locale si CAS est inactif ; traitement CAS et
création de session avec réponse serveur simulée ; création étudiante uniquement
après activation des règles ; préservation des comptes liés ; code de sécurité.
La bibliothèque CAS a été exécutée avec Python 3.13.3 et Django 6.1.

**Pas encore testé avec le vrai CAS ENSEA :** connexion réseau, tickets réels,
attributs effectivement délivrés, éligibilité et correspondances institutionnelles.
La réussite des tests simulés ne valide pas ces points.

ENSEA IT doit fournir/confirmer les URL HTTPS, CAS 3, le retour autorisé avec
paramètre `state`, l’identifiant stable non réattribué, les valeurs d’éligibilité
et le mapping des comptes existants. La création automatique reste bloquée tant
que les deux options d’activation/réconciliation ne sont pas approuvées.
La déconnexion globale CAS/Single Logout n’est pas implémentée ; la politique
d’anonymisation et d’accès technique à `/admin/` reste à valider.

Voir [`CAS_SETUP.md`](Test_App_Django/CAS_SETUP.md) pour chaque variable et chaque
condition d’activation. Aucun serveur, identifiant ou secret réel n’est fourni.
