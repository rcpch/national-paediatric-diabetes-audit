---
title: API Response
author: Dr Simon Chapman
---

In addition to the standard response, extra metadata is returned in the header.

Keys include:

| Key | Value | 
| -- | -- |
| X-Npda-Advisory | Patient added to existing submission 1 for current audit period |
| X-Npda-Advisory-Type | info |
| X-Npda-Timestamp |  2025-05-24T13:01:21.835342+00:00 |
| X-Npda-Version | 1.0 |
| X-Request-Id | 843f67fb-8a8b-4cd3-8d87-c2ab7671d3c8 |

The advisory message relates to any extra information that might be relevant to the response but does not influence its validity. For example, if a patient is created on the 1st April, this would create a new submission. While the POST request would be successful (assuming all data were valid), the advisory message would inform the user that a new submission had now been created.

For user reassurance, a unique identifier for each response is provided. 