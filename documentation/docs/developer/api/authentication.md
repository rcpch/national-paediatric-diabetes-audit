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

#### Scope and Access-Level

Options for access_level include:
`'readonly', 'readwrite', 'admin'`
Options for scopes are more granular and should be space separated
`patient:read patient:write admin:cross-pdu`

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

The tokens last 7 days and so will need refreshing on the client side. This can be changed in the oauth settings in `settings.py`.

### Token Renewal

The renewal process requires the unhashed `client_secret` and `client_id`. Be aware that the secret is hashed on save so must be stored before creation. To be converted to a token as above it needs first to be base64 encoded and can then be passed as a bearer token in the header. For token renewal though the secret and the id are required.

!!! Important
  **The `client_secret` in the request must not be hashed in the request**

#### Client Credentials Grant Type: Token Renewal (/o/token/)

When an access token obtained via the Client Credentials Grant Type expires, you simply request a new one by making the same POST call to the /o/token/ endpoint. There is no "refresh token" for this grant type.

You can authenticate your client either by sending the client_id and client_secret in the Authorization header (Basic Auth) or directly in the request body (form data).

1. Using Basic Authentication (Recommended for Security)

This method sends your client_id and client_secret in a Base64 encoded Authorization header.

- Endpoint: /o/token/
- Method: POST
- Content-Type: application/x-www-form-urlencoded
- Authorization Header: Basic <base64_encoded_client_id:client_secret>
- Body (Form Data): grant_type=client_credentials&scope=<your_scopes>

curl Command:

Bash

```bash
curl -X POST \
  {{ baseURL }}/o/token/ \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H 'Authorization: Basic <base64_encoded_client_id:client_secret>' \
  -d 'grant_type=client_credentials&scope=patient:read'
```

How to get <base64_encoded_client_id:client_secret>:

Replace YOUR_CLIENT_ID and YOUR_UNHASHED_CLIENT_SECRET with your actual values.

Bash

```bash
# Example (replace with your actual client_id and client_secret)
# client_id="4X5N7gkZ83IXtZVR2paHv8phtLtk62twp3ZcWD9g"
# client_secret="V-0bcNrRBQObeBIFRdSyKwpVRA9vD6_6dfbZlFrnheE"

# Encode them using Python (or a similar tool)
# python -c "import base64; print(base64.b64encode(b'YOUR_CLIENT_ID:YOUR_UNHASHED_CLIENT_SECRET').decode('utf-8'))"

# Example output of encoding:
# NFg1Tjdna1o4M0lYdFpWUjJwYUh2OHBodEx0azYydHdwM1pjV0Q5ZzpwYmtkZjJfc2hhMjU2JDEwMDAwMDAkcG9FYW1DcDRiNndYZnFxeDg3emNTUSR2N042RzlCdHE5bWxvc05rZVlzQVJLbml0aFFhM2RHWktadGtKdDlUWmxvPQ==
# (Use the actual base64 encoded string you get)
```

Example curl with placeholder encoded credentials:

Bash

```bash
curl -X POST \
  {{ baseURL }}/o/token/ \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H 'Authorization: Basic NFg1Tjdna1o4M0lYdFpWUjJwYUh2OHBodEx0azYydHdwM1pjV0Q5ZzpwYmtkZjJfc2hhMjU2JDEwMDAwMDAkcG9FYW1DcDRiNndYZnFxeDg3emNTUSR2N042RzlCdHE5bWxvc05rZVlzQVJLbml0aFFhM2RHWktadGtKdDlUWmxvPQ==' \
  -d 'grant_type=client_credentials&scope=patient:read'
```

2. Using Client Credentials in the Request Body (Less Secure, but supported)

This method sends your client_id and client_secret directly as form parameters in the request body.

- Endpoint: `/o/token/`
- Method: POST
- Content-Type: application/x-www-form-urlencoded
- Body (Form Data): grant_type=client_credentials&client_id=<your_client_id>& client_secret=<your_unhashed_client_secret>&scope=<your_scopes>

curl Command:

Bash

```bash
curl -X POST \
  {{ baseURL }}/o/token/ \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_UNHASHED_CLIENT_SECRET&scope=patient:read'
```

Example curl with placeholder values:

Bash

```bash
curl -X POST \
  {{ baseURL }}/o/token/ \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=client_credentials&client_id=4X5N7gkZ83IXtZVR2paHv8phtLtk62twp3ZcWD9g&client_secret=V-0bcNrRBQObeBIFRdSyKwpVRA9vD6_6dfbZlFrnheE&scope=patient:read'
  ```

Expected Successful Response:

A successful response will return a JSON object containing the new access token and its metadata:

JSON

```json
{
    "access_token": "YOUR_NEW_ACCESS_TOKEN_HERE",
    "expires_in": 86400,
    "token_type": "Bearer",
    "scope": "patient:read"
}
```
