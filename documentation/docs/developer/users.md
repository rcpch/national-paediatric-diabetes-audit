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

Note that users cannot be deleted once created, only inactivated. This prevents them from logging in or gaining access in any way to the platform or its data. By retaining their email and record, an audit trail of their activity while using the platform can be retained.

#### Permissions

### Reader

| Model    | View | Change | Delete | Create | Custom |
| -------- | ---- | ------ | ------ | ------ | ------ |
| Patient  | ✔️   |    -   |    -   |    -   | ------ |
| Visit    | ✔️   |    -   |    -   |    -   | ------ |
| Site     | ✔️   |    -   |    -   |    -   | ------ |
| NPDAUser | ✔️   |    -   |    -   |    -   | ------ |
| Submission | ✔️   |    -   |   -    |    -   | ------ |

### Editor

| Model    | View | Change | Delete | Create | Custom |
| -------- | ---- | ------ | ------ | ------ | ------ |
| Patient  | ✔️   |    ✔️   |    -   |    ✔️   | ------ |
| Visit    | ✔️   |    ✔️   |    -   |    ✔️   | ------ |
| Site     | -    |    -   |    -   |    -   | ------ |
| NPDAUser | ✔️   |    -   |    -   |    -   | CAN_DOWNLOAD_CSV, CAN_SUBMIT_CSV |
| Submission | ✔️   |    -   |   -    |    -   | ------ |

### Coordinator

| Model    | View | Change | Delete | Create | Custom |
| -------- | ---- | ------ | ------ | ------ | ------ |
| Patient  | ✔️   |    ✔️   |    -   |    ✔️   | CAN_LOCK_CHILD_PATIENT_DATA_FROM_EDITING, CAN_OPT_OUT_CHILD_FROM_INCLUSION_IN_AUDIT |
| Visit    | ✔️   |    ✔️   |    -   |    ✔️   | ------- |
| Site     | -    |    -   |    -   |    -   | ------ |
| NPDAUser | ✔️   |    ✔️   |    ✔️   |    ✔️   | CAN_SUBMIT_CSV, CAN_DOWNLOAD_CSV |
| Submission | ✔️   |    -   |   -    |    -   | ------ |


### RCPCH Audit Team

| Model    | View | Change | Delete | Create | Custom |
| -------- | ---- | ------ | ------ | ------ | ------ |
| Patient  | ✔️   |    ✔️   |    ✔️   |    ✔️   | CAN_UNLOCK_CHILD_PATIENT_DATA_FROM_EDITING, CAN_LOCK_CHILD_PATIENT_DATA_FROM_EDITING, CAN_OPT_OUT_CHILD_FROM_INCLUSION_IN_AUDIT |
| Visit    | ✔️   |    ✔️   |    ✔️   |    ✔️   | ------ |
| Site     | ✔️   |    ✔️   |    ✔️   |    ✔️   | CAN_EDIT_NPDA_LEAD_CENTRE, CAN_ALLOCATE_NPDA_LEAD_CENTRE, CAN_TRANSFER_NPDA_LEAD_CENTRE, CAN_DELETE_NPDA_LEAD_CENTRE, CAN_PUBLISH_NPDA_DATA |
| NPDAUser | ✔️   |    ✔️   |    ✔️   |    ✔️   | CAN_SUBMIT_CSV, CAN_DOWNLOAD_CSV |
| Submission | ✔️   |    ✔️   |    ✔️   |    ✔️   | ------ |

#### National access (RCPCH Audit Team)

National access comes only from these permissions, which only the `npda_audit_team_full_access` group holds. Users are in that group because their role is RCPCH Audit Team. Check them with `user.has_perm("npda.<codename>")`, or `perms.npda.<codename>` in templates. Never check group membership. `has_perm` is True for any active superuser and False for any inactive user.

| Permission | Model | Allows |
| --- | --- | --- |
| `can_access_all_pdus` | PaediatricDiabetesUnit | View any PDU, and its users, patients and submissions. Also requires the 16-character password. |
| `can_manage_inactive_pdus` | PaediatricDiabetesUnit | Add users and employers to inactive PDUs |
| `can_view_hidden_audit_periods` | AuditPeriod | View audit periods that aren't visible yet |
| `can_edit_closed_audit_periods` | AuditPeriod | Create, edit and delete data, and upload CSVs, in a closed audit period |
| `can_override_data_upload_rules` | Submission | Switch between CSV and questionnaire submissions, and use the questionnaire on a CSV submission |
| `can_manage_users_in_any_pdu` | NPDAUser | Create, edit, activate and deactivate users, and change their employers, in any PDU |
| `can_assign_rcpch_audit_team_role` | NPDAUser | Give a user the RCPCH Audit Team role |
| `can_reset_user_two_factor` | NPDAUser | Reset another user's two-factor authentication |
| `can_preview_features` | NPDAUser | Turn on feature previews |
| `view_banner` (built-in) | Banner | See banners targeted at any role |

An audit team member still can't change a superuser's email or reset their two-factor authentication.

To check *what a user is* rather than *what they may do* (for example to badge them, or when the check is about a user being edited, who may be inactive), use `user.has_rcpch_audit_team_role`.

The permissions are attached to the group by `groups_seeder`, which `s/start-prod` runs on every deploy. It creates any missing group and adds any missing permission, but never removes one. Changing a user's role in the app or the Django admin moves them to the role's group, and joining `npda_audit_team_full_access` logs the change and emails `CHANGE_NOTIFICATION_EMAILS`.


#### NPDAUser model

The NPDAUser model subclasses the AbstractUser
This has the basic django user functions but has the following extra custom fields

- `is_active`: boolean - not that if this is `False`, the user cannot login, and is automatically logged out if actively in a session: this is default django behaviour.
- `is_staff`: boolean - this is a django field which defines access to the Django Admin
- `is_superuser`: boolean - this is a django field which give access to all models, including the admin
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

#### Importing Users

For first use, a command line script can be used to import all users from a spreadsheet.

key fields include:

- first_name
- surname
- title
- email
- role
- pz_code

title can be blank. If provided it must be an integer - one of:

1. Mr
2. Mrs
3. Ms
4. Dr
5. Professor

role cannot be blank. It must be an integer - one of:

1. Coordinator
2. Editor
3. Reader
4. RCPCH Audit Team
7. RCPCH Audit Children and Family

from the command line:
`python manage.py import_users --file path`

#### Logging

Logging settings are in the `logging_settings.py` file and specify what level of logging is required for which event.

In addition to logging, there are also signals set up in `signals.py` which listen for changes to the NPDAUser model, users logging in and out as well as using or setting up 2FA. For more important events, such as changing users, an email step is included.

| Logging Triggers | Email Triggers |
| --- | --- |
| 'role' | 'role' |
| 'is_active' | 'is_active' |
| 'is_staff' | 'is_staff' |
| 'email' | 'email' |
| 'first_name' | 'is_superuser' |
| 'surname' | joining `npda_audit_team_full_access` |

The retired `is_rcpch_audit_team_member` and `is_rcpch_staff` flags have no fields any more, but their history is kept in `VisitActivity`:

- Changes to either flag from July 2025 onwards, with the old and new value, who made them and when. Find them by the flag name in `details`, not by activity code. A save that changed the role as well was logged as activity 12 ("User role changed"), which the Django admin did whenever it changed a role. Any other flag change was logged as activity 13 ("Superuser or admin status changed").
- One "RCPCH flags at removal: …" entry (activity 13) per user who had either flag set when the fields were removed (migration `0048`). Work backwards from it through the logged changes to find a user's flags at any point since July 2025.
