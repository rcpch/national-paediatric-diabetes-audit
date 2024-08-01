---
title: National Paediatric Diabetes Audit database
reviewers: Dr Simon Chapman
---

## Frameworks

The platform has been written in Django 4.0 with a [Postgresql Database backend](manual-setup.md).

## Structure

Database structure has few tables. The models are as follows:

### Base Tables

- **Patient**: There is one record for each child in the audit
- **Visit**: There are multiple records for each patient. In NPDA, children are seen 4 times a year in clinic and have additional contacts. During these visits details regarding care processes and diabetes management are captured.

### Reporting tables

Tables also track the progress of each child through the audit, as well how they are scoring with regard to their key performance indicators (KPIs). These KPIs are aggregated periodically to feed reports on KPIs at different levels of abstractions (organisational, trust-level or health board, integrated care board, NHS England region and country level)

- **KPI**: scores each individual child against the national KPI standards. It stores information on whether a given measure has been passed, failed, has yet to be completed, or whether the child in not eligible to be scored.
- **KPIAggregation**: This base model stores results of aggregations of each measure. The base model is subclassed for models representing each geographical level of abstraction. Aggregations are run at scheduled intervals asynchronously and pulled into the dashboards.
- **OrganisationEmployer**: This model serves the middle model between NPDAUser and PaediatricDiabetesUnit. It tracks the number of organisations/PDUs a user is a member of and which is the primary organisation.
- **Submission**: This tracks all csv upload submissions and allocates them to audit years and quarters thereof. Only one active submission at a time can exist. New ones will overwrite the previous ones.
- **Transfer**: This tracks any transfers between paediatric diabetes units. It stores the reason for transferring and the date of transfer. It provide the middle table between Patient and Paediatric Diabetes Unit
- **VisitActivity**: Stores user access/visit activity, including number of login attempts and ISP address as well as timestamp

### Lookup Tables

The RCPCH NHS Organisation repository maintains the primary source list and these models are kept up to date against this periodically.

- **NPDAUser**: The User base model in Django is too basic for the requirements of NPDA and therefore a custom class has been created to describe the different users who either administer or deliver the audit, either on behalf of RCPCH, or the hospital trusts.

### Schema / ERD

<div style="width: 640px; height: 480px; margin: 10px; position: relative;"><iframe allowfullscreen frameborder="0" style="width:640px; height:480px" src="https://lucid.app/documents/embedded/c09d5aa7-3b32-49b0-a704-ede60f8141f7" id="DJQYgxoCtQxo"></iframe></div>

#### Boundary files and geography extension pack

We have included the Django GIS extension allowing geographic data to be stored. This allowed for `.shp` files for the different regions to be stored and mapping therefore to be possible. The `.shp` files are stored in the following models:

- **IntegratedCareBoard**
- **LocalHealthBoard**
- **NHSEnglandRegion**
- **Country**

## Migrations

Any changes to the database structure are captured in the migrations, and this is run at each deploy, with any fresh migrations being applied if present at that point. They are stored in the ```migrations``` folder and these files should not be altered and should be checked into version control. The initial migrations contain seed functions to seed the database on creation with data required for the lookup tables listed above.
