---
title: API Endpoints
author: Dr Simon Chapman
---

This is not a replacement for the OpenAPI spec. 

| HTTP Method	| URL | Pattern	Action | Description |
| -- | -- | -- | -- |
| GET |	/patients/ | list | Get all patients |
| POST | /patients/	| create | Create new patient |
| GET |	/patients/{id}/	| retrieve | Get specific patient |
| PUT |	/patients/{id}/	| update | Full update of patient |
| PATCH |	/patients/{id}/ |	partial_update | Partial update of patient |
| DELETE |	/patients/{id}/ | destroy | Delete patient |