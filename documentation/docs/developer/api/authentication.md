---
title: Authentication
author: Dr Simon Chapman
---

## Authentication

The NPDA API uses Oauth2 authentication. Each Paediatric Diabetes Unit can create a single oauth application. By default this is named `PDU-*pz_code*-API`. Each application is associated with an email address which has an expiry date and a user. An application can only be created and associated with a user who has an existing record in the NPDAUser table.

### Application and Token Creation

Within the django shell:

```console
python manage.py oauth_token \
    --user-email "incubator@rcpch.ac.uk" \
    --pz-code "PZ999" \
    --create-application \
    --description "Admin access for PDU PZ999" \
    --access-level "admin" \
    --scopes "patient:read patient:write"
```

Note that a user with the email `incubator@rcpch.ac.uk` must exist or an error will result:
`❌ User with email 'incubator@rcpch.ac.uk' not found`
Note also that the `--create-application` must be provided without a name if a new application is being created. If an `--application-name` is provided, this will be used to add subsequent users.

If successful, the following message will show in the console:

```console
Console Log Level: DEBUG
File Log Level: DEBUG
✅ Found user: incubator@rcpch.ac.uk
✅ Found PDU: ROYAL COLLEGE OF PAEDIATRICS AND CHILD HEALTH (PZ999)
✅ Created new application: PDU-PZ999-API
   Client ID: 22W6YMZ4BdOvkDUbGPNAKU8hfS27oSdAUxQXILQD
   Client Secret: pbkdf2_sha256$1000000$g9ImDO7R8nswNTzVXXHjoA$WO17U+bxgeOBXMHx0JLuBDeygQTxKp61E/WWmF7gJIM=
   ⚠️  Save these credentials securely!

🎉 Token created successfully!
Token: tElXV0xhmtXBZFHSFJNxB0DtZMv-0SItjqKgWPod1Z0
Expires: 2025-05-23 22:19:22.851623+00:00
Scopes: patient:read patient:write

📋 For Postman:
Authorization: Bearer tElXV0xhmtXBZFHSFJNxB0DtZMv-0SItjqKgWPod1Z0

📊 Total active tokens for this PDU: 1
```

To add extra users, again in the console:

```console
python manage.py oauth_token \
    --user-email "incubator+reader@rcpch.ac.uk" \
    --pz-code "PZ999" \
    --application-name "PDU-PZ999-API" \
    --description "Trust managment staff readonly token" \
    --access-level "readonly" \
    --scopes "patient:read"
```

This should yield:

```console
Console Log Level: DEBUG
File Log Level: DEBUG
✅ Found user: incubator+reader@rcpch.ac.uk
✅ Found PDU: ROYAL COLLEGE OF PAEDIATRICS AND CHILD HEALTH (PZ999)
✅ Found application: PDU-PZ999-API

🎉 Token created successfully!
Token: 9yWxnyYif8BiJN9BZPFFoCTvjh_a-yZHabmSathOqTM
Expires: 2025-05-23 23:10:58.129734+00:00
Scopes: patient:read
PDU: ROYAL COLLEGE OF PAEDIATRICS AND CHILD HEALTH (PZ999)
Access Level: readonly
Application: PDU-PZ999-API

📋 For Postman:
Authorization: Bearer 9yWxnyYif8BiJN9BZPFFoCTvjh_a-yZHabmSathOqTM

📊 Total active tokens for this PDU: 2
```

#### Scope

Options include:
`'readonly', 'readwrite', 'admin'`
They should be space separated

#### How to use

When making an API request, the Oauth2 token must be included.

*Postman*

Authorization > Bearer Token **Token goes here**

or

1. OAuth2 > Configure New Token > Grant Type -> Client Credentials
2. Fill in Access Token URL: `{{baseurl}}/api/o/token/`
3. Add Client ID and Client Secret from the application
4. Scope > `"patient:read patient:write"`
5. Click "Get New Access Token"
6. After receiving the token, click "Use Token"

then use the token generated as above.

*cURL*

```bash
# Using Bearer token directly
curl -X GET \
  "{{baseurl}}/api/v1/patients/" \
  -H "Authorization: Bearer tElXV0xhmtXBZFHSFJNxB0DtZMv-0SItjqKgWPod1Z0" \
  -H "Content-Type: application/json"

# Example with actual endpoint
curl -X GET \
  "http://localhost:8008/api/v1/patients/" \
  -H "Authorization: Bearer tElXV0xhmtXBZFHSFJNxB0DtZMv-0SItjqKgWPod1Z0" \
  -H "Content-Type: application/json"

# POST example (creating a new patient record)
curl -X POST \
  "http://localhost:8008/api/v1/patients/" \
  -H "Authorization: Bearer tElXV0xhmtXBZFHSFJNxB0DtZMv-0SItjqKgWPod1Z0" \
  -H "Content-Type: application/json" \
  -d '{
    "nhs_number": "1234567890",
    "date_of_birth": "2010-01-15",
    "diagnosis_date": "2010-06-01"
  }'

# Alternative: Using Client Credentials flow
curl -X POST \
  "{{baseurl}}/api/o/token/" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=22W6YMZ4BdOvkDUbGPNAKU8hfS27oSdAUxQXILQD" \
  -d "client_secret=pbkdf2_sha256$1000000$g9ImDO7R8nswNTzVXXHjoA$WO17U+bxgeOBXMHx0JLuBDeygQTxKp61E/WWmF7gJIM=" \
  -d "scope=patient:read patient:write"

# Then use the returned access_token in subsequent requests
curl -X GET \
  "{{baseurl}}/api/v1/patients/" \
  -H "Authorization: Bearer {access_token_from_previous_response}" \
  -H "Content-Type: application/json"
```

The tokens last 24 hours and so will need refreshing on the client side.