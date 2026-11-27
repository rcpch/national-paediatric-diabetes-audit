---
title: Microsoft Entra ID sign in
---

## Microsoft Entra ID sign in

Superusers and members of the **RCPCH Audit Team** role can sign in with their RCPCH Microsoft account ("Sign in with Microsoft" on the login page) instead of the email address, password and one-time code login.

A setting can make this **compulsory** for them. It is off by default and can be switched off again at any time.

This mirrors the Epilepsy12 implementation ([rcpch/rcpch-audit-engine#1513](https://github.com/rcpch/rcpch-audit-engine/pull/1513)).

### Who it applies to

A user is covered if they are a superuser (`is_superuser`) **or** have the role `RCPCH_AUDIT_TEAM`. Everyone else (Editors, Readers and Coordinators) keeps the email, password and one-time code login and cannot use Sign in with Microsoft.

### The login page

The Sign in with Microsoft button is hidden until an email address on `ENTRA_ID_EMAIL_DOMAIN` (e.g. `@rcpch.ac.uk`) is typed into the email field. The password login stays available alongside it, so the audit team's lower-permission test accounts (e.g. `firstname.lastname+editor@rcpch.ac.uk`) still sign in with a password and one-time code.

Whether the button shows is decided from the typed address alone: in the browser, or by the server when the login page is shown again after a failed attempt, so it also works without JavaScript. It reveals nothing about whether an account exists or what kind it is.

The typed address is passed to Microsoft so the right account is pre-selected.

New RCPCH Audit Team members do not need a password: they type their email and click Sign in with Microsoft.

### Environment variables

| Variable | Purpose |
|---|---|
| `ENTRA_ID_TENANT_ID` | Directory (tenant) id of the RCPCH Entra ID tenant. Only accounts from this tenant are accepted. |
| `ENTRA_ID_CLIENT_ID` | Application (client) id of the app registration. |
| `ENTRA_ID_EMAIL_DOMAIN` | e.g. `rcpch.ac.uk`. The button is shown for this domain, and only Microsoft accounts with an email on it are accepted. |
| `ENTRA_ID_CLIENT_SECRET` | A client secret of the app registration. Use for local development. |
| `ENTRA_ID_USE_MANAGED_IDENTITY` | `"True"` to authenticate as the container app's managed identity instead of with a client secret. Use for deployed environments. Defaults to `"False"`. |
| `ENTRA_ID_MANAGED_IDENTITY_CLIENT_ID` | Optional. Client id of the user-assigned managed identity to use. Defaults to `AZURE_CLIENT_ID` (the identity the database connection uses), else the system-assigned identity. |
| `ENTRA_ID_LOGIN_REQUIRED_FOR_RCPCH_STAFF` | `"True"` to make Sign in with Microsoft compulsory for superusers and the RCPCH Audit Team. Defaults to `"False"`. |

Sign in with Microsoft is enabled when the tenant id, client id and email domain are set, plus **one** credential: `ENTRA_ID_CLIENT_SECRET` or `ENTRA_ID_USE_MANAGED_IDENTITY="True"`. Setting both makes the app refuse to start, so it is never ambiguous which is in use. If `ENTRA_ID_LOGIN_REQUIRED_FOR_RCPCH_STAFF` is `"True"` but sign in is not fully configured, the app also refuses to start rather than lock every superuser out.

### Setting up the app registration

1. In the Entra admin centre, create an app registration for **accounts in this organisational directory only** (single tenant). Keep it separate from the app registration used for GitHub Actions deployment: it needs no Azure role assignments.
2. Add a **Web** redirect URI of `https://<site domain>/account/entra-id/callback/` for each environment (for example the live and staging domains, and `https://npda.localhost/account/entra-id/callback/` for local development).
3. No API permissions are needed beyond the default `openid` / `profile` sign in.
4. Give the app a credential, as below.

#### Deployed environments: managed identity (no secret)

The container app's managed identity is trusted by the app registration as a **federated credential**. There is then no secret to store, rotate or let expire.

1. On the app registration, go to **Certificates & secrets → Federated credentials → Add credential** and choose the **Managed identity** scenario.
2. Select the managed identity the container app runs as (the one already used for the database connection).
3. Set `ENTRA_ID_USE_MANAGED_IDENTITY="True"` and leave `ENTRA_ID_CLIENT_SECRET` unset. If the container app has more than one user-assigned identity and `AZURE_CLIENT_ID` is not the one you added, set `ENTRA_ID_MANAGED_IDENTITY_CLIENT_ID` to its client id.

At sign in, NPDA gets a token for the managed identity (audience `api://AzureADTokenExchange`) and presents it to Entra ID in place of a client secret.

#### Local development: client secret

A local machine has no managed identity, so use a client secret: create one under **Certificates & secrets → Client secrets** and set `ENTRA_ID_CLIENT_SECRET` in `envs/.env`. Note its expiry date: when it expires, Sign in with Microsoft stops working locally.

### Multi-factor authentication

A successful Sign in with Microsoft counts as the second factor, so there is no NPDA one-time code. It is recorded against an "Entra ID" device on the user (an `EntraIDDevice`, a [django-otp](https://django-otp-official.readthedocs.io/) device), so `user.is_verified()` is true and every existing two-factor check works unchanged. The device appears in the user's two-factor devices on their page, and can never verify a typed one-time code.

MFA is enforced across RCPCH's Entra ID tenant by Conditional Access policy, and NPDA relies on that policy. The app cannot check it from the token: the v2.0 ID tokens it receives do not include the `amr` (authentication methods) claim. If the policy changes (for example, an exclusion for trusted or office networks), Microsoft sign ins to NPDA would no longer be guaranteed to use MFA.

### How accounts are matched

The Microsoft account's email (`email`, `preferred_username` or `upn` claim) must be on `ENTRA_ID_EMAIL_DOMAIN` and match exactly one NPDA user's email address. Addresses on other domains are ignored, because a guest account in the tenant can carry an outside address.

On the first successful sign in, the Microsoft account's immutable object id is stored on the user's Entra ID device (one per user, enforced by the database). Later sign ins must come from the same Microsoft account. If an RCPCH email address is ever reassigned to a different person, sign in is refused until the binding is removed with **Reset two-factor authentication** on the user's page, or by deleting their row under "Entra ID sign ins" in the Django admin. Note that Reset two-factor authentication also removes any authenticator app, which they would need to set up again if the setting is later switched off.

A successful sign in also sets `email_confirmed`, which is otherwise only set when a password is first set.

Inactivity deactivation applies to Entra ID sign in as it does to the password login.

Failed sign ins are recorded in the user's visit activity, where one was matched, as "Login failed", with details starting "Microsoft Entra ID sign in failed:" and the reason. Failures once Microsoft has returned a valid ID token, and configuration errors returned by Microsoft when redeeming a code (e.g. an expired client secret or a missing federated credential), are logged at error level, so the admins are emailed. Failures anyone can trigger anonymously (no sign in in progress, state mismatch, user cancelled, made-up code, or any error put in the callback's own query string) are logged as warnings, so the public callback cannot flood the admins' inboxes.

### Switching it on

1. Set the Entra ID variables above (with the managed identity credential) and deploy. Sign in with Microsoft now appears for `@rcpch.ac.uk` addresses but is optional.
2. Ask every superuser and RCPCH Audit Team member to sign in with Microsoft once to check their account matches.
3. Set `ENTRA_ID_LOGIN_REQUIRED_FOR_RCPCH_STAFF="True"` and deploy. From then on, their email and password login is refused with the same "incorrect email or password" error as a wrong password, so a correct password is never revealed. The real reason is recorded in their visit activity. Sessions already open when the setting is switched on carry on until they log out or are automatically logged out.

### Switching it off

Set `ENTRA_ID_LOGIN_REQUIRED_FOR_RCPCH_STAFF="False"` (or remove it) and deploy. Nothing about anyone's account is changed when the setting is switched on: passwords, authenticator apps, email codes and backup codes are all kept. So once it is off, superusers and the RCPCH Audit Team can sign in with their email, password and one-time code again straight away.

Remove the Entra ID variables as well to hide Sign in with Microsoft completely.
