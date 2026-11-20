---
title: Microsoft Entra ID sign in
---

## Microsoft Entra ID sign in

Superusers and members of the RCPCH Audit Team can sign in with their RCPCH Microsoft account ("Sign in with Microsoft" on the login page). A setting can make this the **only** way they can sign in, in place of the email, password and one-time code login.

Everyone else (Editors, Readers and Coordinators) always signs in with their email, password and one-time code. "Sign in with Microsoft" refuses them.

### Settings

| Environment variable | Purpose |
| --- | --- |
| `ENTRA_ID_TENANT_ID` | Directory (tenant) id of the RCPCH Entra ID tenant. Only accounts in this tenant can sign in. |
| `ENTRA_ID_CLIENT_ID` | Application (client) id of the Entra ID app registration. |
| `ENTRA_ID_CLIENT_SECRET` | A client secret of the app registration. |
| `ENTRA_ID_LOGIN_REQUIRED_FOR_RCPCH_STAFF` | `"True"` makes Entra ID sign in compulsory for superusers and the RCPCH Audit Team. Defaults to `"False"`. |

"Sign in with Microsoft" is shown once all three app registration values are set. The app will not start if `ENTRA_ID_LOGIN_REQUIRED_FOR_RCPCH_STAFF` is `"True"` without them, rather than lock every superuser out.

### App registration

In the RCPCH Entra ID tenant, register a single tenant web application with redirect URIs of `https://<site domain>/account/entra-id/callback/` for each deployment (and your local development address, e.g. `https://npda.localhost/account/entra-id/callback/`), and create a client secret. No API permissions beyond the default `User.Read` are needed: only the ID token's claims are used.

### What happens when it is required

When `ENTRA_ID_LOGIN_REQUIRED_FOR_RCPCH_STAFF` is `"True"`:

- the email and password login refuses superusers and RCPCH Audit Team members, and logs a failed login against their account
- any of their sessions that was not started with Entra ID (for example one already open when the setting was turned on) is ended at its next request

**No passwords or two-factor devices are changed or deleted.** Setting it back to `"False"` and restarting the app restores the old login immediately. Use this if Entra ID is unavailable and superusers need to get in.

### How the sign in works

1. `entra_id_login` starts an OAuth 2.0 authorisation code flow with PKCE (via [msal](https://github.com/AzureAD/microsoft-authentication-library-for-python)) and sends the browser to Microsoft.
2. Microsoft applies RCPCH's own sign in and multi-factor authentication policy, then returns to `entra_id_callback`, which redeems the code and checks the state, nonce, tenant (`tid`) and object id (`oid`).
3. The Microsoft account is matched to an NPDA user by email address (the `email`, `preferred_username` or `upn` claim, case insensitive). It must match exactly one user, who must be an active superuser or RCPCH Audit Team member.
4. On the first sign in the Microsoft account's immutable object id is stored on a new `EntraIDDevice` for the user. Later sign ins must come from the same Microsoft account.
5. The user is logged in against that `EntraIDDevice`. It is a [django-otp](https://django-otp-official.readthedocs.io/) device, so `user.is_verified()` is true and every existing two-factor check works unchanged. The device can never verify a typed one-time code.

Inactivity deactivation applies to Entra ID sign in as it does to the password login.

### Changing a user's Microsoft account

If a user's email now belongs to a different Microsoft account, sign in is refused ("does not match the one previously used"). To allow it, remove the old binding with **Reset two-factor authentication** on the user's page (this also removes any authenticator app, which they would need to set up again if the setting is turned off), or delete their row under "Entra ID sign ins" in the Django admin.

### Audit trail

Successful sign ins are logged as "Successful login". Refusals are logged against the user, where one was matched, as "Microsoft Entra ID login failed" with the reason in the details.
