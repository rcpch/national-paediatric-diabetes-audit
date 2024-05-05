---
title: Users
author: Dr Simon Chapman
---

### Users

There are 5 user types:

- Lead clinician
- Clinician
- Administrator
- RCPCH Audit Team
- Children, Young People and Families

The last group has no real implementation at the moment but in time it is hoped families will have accounts and can sanction inclusion of children/young people's data.

#### Permissions

|      Group       | Model   | View | Change | Delete | Create | Custom |
| ---------------- | ------- | ---- | ------ | ------ | ------ | ------ |
| Lead             | Patient |   X  |    X   |    X   |    X   | CAN_LOCK_CHILD_PATIENT_DATA_FROM_EDITING, CAN_OPT_OUT_CHILD_FROM_INCLUSION_IN_AUDIT |
| Clinician        | Patient |   X  |    X   |    -   |    X   | ------ |
| Administrator    | Patient |   X  |    X   |    -   |    X   | ------ |
| RCPCH Audit Team | Patient |   X  |    X   |    X   |    X   | CAN_UNLOCK_CHILD_PATIENT_DATA_FROM_EDITING, CAN_LOCK_CHILD_PATIENT_DATA_FROM_EDITING, CAN_OPT_OUT_CHILD_FROM_INCLUSION_IN_AUDIT |
| Lead             | Visit |   X  |    X   |    X   |    X   | ------- |
| Clinician        | Visit |   X  |    X   |    -   |    X   |  ------ |
| Administrator    | Visit |   X  |    -   |    -   |    -   |  ------ |
| RCPCH Audit Team | Visit |   X  |    X   |    X   |    X   |  ------ |
| Lead             | Site    |   -  |    -   |    -   |    -   | ------ |
| Clinician        | Site    |   -  |    -   |    -   |    -   | ------ |
| Administrator    | Site    |   -  |    -   |    -   |    -   | ------ |
| RCPCH Audit Team | Site    |   X  |    X   |    X   |    X   | CAN_EDIT_NPDA_LEAD_CENTRE, CAN_ALLOCATE_NPDA_LEAD_CENTRE, CAN_TRANSFER_NPDA_LEAD_CENTRE, CAN_DELETE_NPDA_LEAD_CENTRE, CAN_PUBLISH_NPDA_DATA |
| |

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