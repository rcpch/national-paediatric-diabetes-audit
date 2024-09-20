---
title: Users
author: Dr Simon Chapman
---


### Users

There are 5 user types:

- Editor
- Reader
- Coordinator
- RCPCH Audit Team
- Children, Young People and Families

The last group has no real implementation at the moment but in time it is hoped families will have accounts and can sanction inclusion of children/young people's data.

#### Permissions

### Reader

| Model    | View | Change | Delete | Create | Custom |
| -------- | ---- | ------ | ------ | ------ | ------ |
| Patient  | ✔️   |    -   |    -   |    -   | ------ |
| Visit    | ✔️   |    -   |    -   |    -   | ------ |
| Site     | ✔️   |    -   |    -   |    -   | ------ |
| NPDAUser | ✔️   |    -   |    -   |    -   | ------ |

### Editor

| Model    | View | Change | Delete | Create | Custom |
| -------- | ---- | ------ | ------ | ------ | ------ |
| Patient  | ✔️   |    ✔️   |    -   |    ✔️   | ------ |
| Visit    | ✔️   |    ✔️   |    -   |    ✔️   | ------ |
| Site     | -    |    -   |    -   |    -   | ------ |
| NPDAUser | ✔️   |    -   |    -   |    -   | ------ |

### Coordinator

| Model    | View | Change | Delete | Create | Custom |
| -------- | ---- | ------ | ------ | ------ | ------ |
| Patient  | ✔️   |    ✔️   |    -   |    ✔️   | CAN_LOCK_CHILD_PATIENT_DATA_FROM_EDITING, CAN_OPT_OUT_CHILD_FROM_INCLUSION_IN_AUDIT |
| Visit    | ✔️   |    ✔️   |    -   |    ✔️   | ------- |
| Site     | -    |    -   |    -   |    -   | ------ |
| NPDAUser | ✔️   |    ✔️   |    ✔️   |    ✔️   | ------ |


### RCPCH Audit Team

| Model    | View | Change | Delete | Create | Custom |
| -------- | ---- | ------ | ------ | ------ | ------ |
| Patient  | ✔️   |    ✔️   |    ✔️   |    ✔️   | CAN_UNLOCK_CHILD_PATIENT_DATA_FROM_EDITING, CAN_LOCK_CHILD_PATIENT_DATA_FROM_EDITING, CAN_OPT_OUT_CHILD_FROM_INCLUSION_IN_AUDIT |
| Visit    | ✔️   |    ✔️   |    ✔️   |    ✔️   | ------ |
| Site     | ✔️   |    ✔️   |    ✔️   |    ✔️   | CAN_EDIT_NPDA_LEAD_CENTRE, CAN_ALLOCATE_NPDA_LEAD_CENTRE, CAN_TRANSFER_NPDA_LEAD_CENTRE, CAN_DELETE_NPDA_LEAD_CENTRE, CAN_PUBLISH_NPDA_DATA |
| NPDAUser | ✔️   |    ✔️   |    ✔️   |    ✔️   | ------ |


#### NPDAUser model

The NPDAUser model subclasses the AbstractUser
This has the basic django user functions but has the following extra custome fields

- `is_active`: boolean
- `is_staff`: boolean - this is a django field which defines access to the Django Admin
- `is_superuser`: boolean - this is a django field which give access to all models, including the admin
- `is_rcpch_audit_team_member`: boolean - a custom field that defines the user is an RCPCH audit team member
- `is_rcpch_staff`: boolean - a custom field that defines the user is an RCPCH staff member. This is as opposed to a clinician who may be a member of the audit team, but not an RCPCH employee
- `is_patient_or_carer`: boolean - a custom field that defines the user is a patient or carer
- `role` - user type as above
- `organisation_employer` - this is a relational field with an Organisation. Only applies to clinicians and therefore is None for RCPCH employees.

#### Passwords and Two factor authentication

Password access is required to access all areas of the NPDA platform apart from the documentation/user guide. Rules for passwords are:
Minimum of 10 characters (minimum 16 for RCPCH Audit team)
Must contain ONE capital
Must contain ONE number
Must contain ONE symbol from !@£$%^&*()_-+=|~
Must NOT be exclusively numbers
Must NOT be same as your email, name, surname

User accounts allow a maximum of 5 consecutive attempts after which the account is locked for 5 minutes.

Two Factor authentication is required for all login access. This is set up only once at first login. A user can change their 2 Factor Authentication settings once logged in by clicking on the their name in the top right of the screen and navigating to Two Factor Authentication.

Two Factor Authentication is either by email or Microsoft Authenticator on a mobile phone. If a user successfully logs in with their passwords, they must either check their email for a Token or generate one on their Microsoft Authenticator app.

#### Captcha

In addition to the above methods of authentication, a rotating image of numbers or letters is used to ensure only humans can gain access.
