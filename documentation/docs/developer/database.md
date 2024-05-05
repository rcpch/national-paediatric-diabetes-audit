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
- **Site**: There is only one active site at any one time, but more than one site might be responsible for the care of a patient over the audit year.

### Reporting tables

Tables also track the progress of each child through the audit, as well how they are scoring with regard to their key performance indicators (KPIs). These KPIs are aggregated periodically to feed reports on KPIs at different levels of abstractions (organisational, trust-level or health board, integrated care board, NHS England region and country level)

- **AuditProgress**: Has a one to one relationship with Registration. Stores information on how many fields in each form have been completed.
- **KPI**: scores each individual child against the national KPI standards. It stores information on whether a given measure has been passed, failed, has yet to be completed, or whether the child in not eligible to be scored.
- **KPIAggregation**: This base model stores results of aggregations of each measure. The base model is subclassed for models representing each geographical level of abstraction. Aggregations are run at scheduled intervals asynchronously and pulled into the dashboards.
- **VisitActivity**: Stores user access/visit activity, including number of login attempts and ISP address as well as timestamp

### Link Tables

There are some many to many relationships. Django normally handles this for you, but the development team chose to implement the link tables in these cases separately to be able to store information about the relationship between the tables.

- **Site**: The relationships here are complicated since one child may have their diabetes care  in different Organisations across a year, though only one centre can be active in the care of a child at any one time. Each Case therefore can have a many to many relationship with the Organisation trust model (since one Organisation can have multiple Cases and one Case can have multiple Organisations). The Site model therefore is a link model between the two. It is used in this way, rather than relying on the Django built-in many-to-many solution, because additional information relating to the organisation can be stored per Case, for example whether the site is actively involved in diabetes care.

### Lookup Tables

These classes are used as look up tables throughout the NPDA application. They are seeded in the first migrations, either pulling content from the the ```constants``` folder, or from SNOMED CT. Note that the RCPCH NHS Organisation repository maintains the primary source list and these models are kept up to date against this periodically.

- **Organisation**: This model stores information about each Organisation in England, Scotland and Wales. It is used as a lookup for clinicians as well as children in Epilepsy12. It has a many to many relationship with Case and a many to one relationship with Epilepsy12User. It is seeded from the ```constants``` folder with a ```JSON`` list of hospital trusts.
- **NPDAUser**: The User base model in Django is too basic for the requirements of NPDA and therefore a custom class has been created to describe the different users who either administer or deliver the audit, either on behalf of RCPCH, or the hospital trusts.
- **Group**: Not strictly an Epilepsy12 model, but a Django model tied to the User class. There are 6 custom groups (3 RCPCH, 3 hospital trust) with differing levels of access depending on status. The permissions, which are granular and relate to the individual model fields, can then be allocated to groups, allowing admin staff to ensure that permissions are granted in a systematic way.
- **IntegratedCareBoard**: Seeded from ```constants``` provides a list of Integrated Care Boards and identifiers
- **OpenUKNetwork**: Seeded from ```constants``` provides a list of OPENUK Networks and identifiers
- **LocalHealthBoard**: Seeded from ```constants``` provides a list of Local Health Boards in Wales and identifiers
- **NHSEnglandRegion**: Seeded from ```constants``` provides a list of NHS England regions and identifiers
- **Country**: Seeded from ```constants``` provides a list of country identifiers

#### Boundary files and geography extension pack

We have included the Django GIS extension allowing geographic data to be stored. This allowed for `.shp` files for the different regions to be stored and mapping therefore to be possible. The `.shp` files are stored in the following models:

- **IntegratedCareBoard**
- **LocalHealthBoard**
- **NHSEnglandRegion**
- **Country**

## Migrations

Any changes to the database structure are captured in the migrations, and this is run at each deploy, with any fresh migrations being applied if present at that point. They are stored in the ```migrations``` folder and these files should not be altered and should be checked into version control. The initial migrations contain seed functions to seed the database on creation with data required for the lookup tables listed above.
