# CAS integration and activation

CAS is **disabled by default**. No ENSEA URL, attribute name, eligibility rule or
existing-account mapping has been assumed. `.env` is private and Git-ignored;
`.env.example` contains only empty values and disabled switches. The existing
local username/password form remains available when CAS is disabled or its core
configuration is incomplete. There is no fake CAS mode.

## Client compatibility evidence

Chosen client: `python-cas==1.7.2`, a framework-independent CAS client.
It was installed into `venv` on Windows with Python 3.13.3 and Django 6.1.
`pip check` reported no broken requirements. Before implementing the integration,
a smoke check ran its real CAS 3 `verify_ticket` request and XML parser after
`django.setup()`, replacing only the external HTTP response with fictional XML.

The integration tests exercise the installed client's request builder and parser,
the application's backend, database writes, Django sessions and middleware.
Only `requests.sessions.Session.send` is mocked, in `caisse/test_cas.py`.
This demonstrates local compatibility, **not connectivity to ENSEA CAS**.

References: https://pypi.org/project/python-cas/1.7.2/ and
https://apereo.github.io/cas/development/protocol/CAS-Protocol-Specification.html

## Values ENSEA IT must supply or approve

| Variable | Required decision/value |
| --- | --- |
| `CAS_ENABLED` | Leave `False` until the core settings and service registration are approved. |
| `CAS_SERVER_URL` | Official HTTPS CAS base URL. Login and `p3/serviceValidate` are resolved under it. |
| `CAS_CALLBACK_URL` | Registered absolute HTTPS application URL ending in `/connexion/cas/retour/`, with no query or fragment. |
| `CAS_PROTOCOL_VERSION` | Set to `3` only after IT confirms CAS 3 attribute release. Other protocols are not implemented. |
| `CAS_ID_ATTRIBUTE` | Exact attribute containing one immutable, unique, non-reassigned identifier. `__principal__` explicitly selects the CAS principal only if IT guarantees those properties. No default, case folding or identity normalization. |
| `CAS_ELIGIBILITY_ATTRIBUTE` | Exact attribute containing the approved affiliations/eligibility values. |
| `CAS_ELIGIBLE_VALUES` | Comma-separated, case-sensitive values permitted to log in. Include staff only if approved; applies to mapped accounts too. Multi-valued CAS attributes are supported. |
| `CAS_STUDENT_VALUE` | One exact value proving that a new account is an eligible student. Must also occur in `CAS_ELIGIBLE_VALUES`. |
| `CAS_AUTO_CREATE_STUDENTS` | Default `False`. Enable only after the student rule and account lifecycle policy are approved. |
| `CAS_EXISTING_ACCOUNTS_RECONCILED` | Default `False`. Enable only after all existing accounts have approved mappings or a reviewed disposition, including disabled/anonymized identities. |

IT must register the callback with its **variable `state` query parameter**.
Each login uses a random, session-bound state, valid for five minutes. The exact
same service URL, including state, is used when requesting and validating the
ticket. Only a single-use pending login from the same browser is accepted. IT
must permit this service-registration pattern; do not remove state protection to
work around a registration mismatch.

Validation always verifies TLS certificates, uses 5-second connect / 10-second
read timeouts, rejects non-200 responses, and does not follow redirects. Obtain
IT's HTTPS development endpoint/service registration or approved HTTPS access
to the local app; HTTP callbacks are intentionally unsupported. For private CAs,
configure the deployment's trusted CA bundle (Requests supports
`REQUESTS_CA_BUNDLE`); never disable certificate verification.

If IT cannot release the stable identifier or eligibility attributes, leave CAS
disabled. If those are available but existing-account reconciliation is not,
only explicitly mapped, eligible accounts may sign in: keep both creation
switches `False`. Missing, malformed or ambiguous attributes never create a user
or wallet. CAS authentication alone does not prove student eligibility.

## Preserve existing users and wallets

`CASIdentity` links `(issuer URL, stable subject)` to one existing Django `User`.
Both that external identity and the local user link have database uniqueness
constraints. There is **no matching by username, name, or email**.

After reviewing an authoritative mapping with IT, apply each approved pair using
the local user primary key (substitute approved values; never commit real mappings):

```powershell
.\venv\Scripts\python.exe manage.py link_cas_identity --subject "<approved-stable-id>" --user-id <existing-user-id>
```

Configure the approved server URL and identity attribute first; CAS may remain
disabled while mapping. The command creates only the link, is idempotent for an
identical mapping, and refuses conflicting or inactive-account mappings. It
does not create a wallet or modify a password, username, balance, role or code.
No mappings have been applied by this implementation.

On a validated login, a mapped account retains its User/Profile primary keys,
username, password, balance, QR secret, RFID, transaction history, Affectation
roles/extra rights and security-code records. Only Django's normal `last_login`
changes. A missing profile is created only for a verified, explicitly linked user.
Names, email and birth dates are not imported or refreshed from CAS.

If both creation switches are approved and enabled, an eligible unmapped student
gets an opaque `cas_<random>` local username, an unusable local password, no staff
or superuser privilege, no Affectation, and a zero-balance profile with normal
defaults. User, identity and profile creation are atomic. A uniqueness conflict
or database lock fails the attempt without a partial wallet; the user can retry
login. Local screens that search by username continue using the local username,
not the CAS principal; a user-facing identifier policy can be agreed separately.

`User.is_active=False` and profile statuses `DESACTIVE`/`ANONYMISE` deny CAS login.
Existing CAS sessions also check local account status on subsequent requests.
Anonymization currently retains the identity link, preventing automatic account
recreation. **IT and the application's data owner must approve retention or a
replacement blocking policy before production.** Unmapped historical anonymized
accounts cannot be reconciled by guessing; keep automatic creation off until
their handling is settled. Do not delete identity links, change the issuer or
identity attribute, or enable reconciliation without reviewing the consequences.

## Security-code challenge and logout

With core CAS configuration complete, `/connexion/` starts CAS login. Only a
server-validated service ticket can establish a CAS Django session. Every fresh
CAS login clears `code_verifie`, even when it is the same user in the same session,
then redirects to the existing `verifier_code` view. Callback/start routes are
narrowly exempted from that middleware so ticket handling can finish first.

Existing semantics are retained: users without codes proceed to home; users with
codes must verify one; any matching code verifies the session globally; local
roles without code records do not automatically acquire a challenge. `next` is
ignored on the CAS path and success goes through the code gate to home.

Logout remains a CSRF-protected POST that clears the local Django session. With
CAS enabled it displays a logged-out page instead of immediately starting SSO
again. **Global CAS logout and CAS Single Logout notifications are not implemented**
pending IT's policy. A remaining CAS SSO session may sign the user in again after
they explicitly click login, but a fresh local security code is still required.
Local Django `/admin/` authentication and its existing code-middleware exemption
are unchanged; IT must decide the production emergency-admin access policy.

Before production, set appropriate Django HTTPS/cookie/host/debug settings and
ensure proxy/application logs redact ticket query parameters. This change does
not turn the project's existing development settings into deployment settings.

## Local commands and verification

Use the Windows `venv`, never the committed Linux `.venv`:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m pip check
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py test --verbosity 2
```

The migration adds only the empty identity-link table; it does not backfill
accounts or change wallets. Tests use fictional accounts and generated passwords
in Django's isolated test database. Existing local accounts and `.env` are not
test fixtures. Tests cover ticket rejection, response errors, state/replay,
eligibility/provisioning gates, approved mappings, repeat login, account status,
wallet/role preservation, local fallback, security codes and logout.

For a complete review including new, untracked files, use the IDE's Source
Control diffs. `git diff` alone omits untracked files; inspect those explicitly.
No production login is verified until ENSEA supplies a registered test service
and fictional IT test identities.
