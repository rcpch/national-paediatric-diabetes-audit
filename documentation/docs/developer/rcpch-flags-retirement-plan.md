# Retiring `is_rcpch_audit_team_member` and `is_rcpch_staff`

This is the plan for replacing the two `NPDAUser` boolean flags with permissions attached to the `npda_audit_team_full_access` group, which every user with the **RCPCH Audit Team** role belongs to. Code checks those permissions with `has_perm`, never group membership.

## How the code works now

- **Two separate systems.** The `RCPCH_AUDIT_TEAM` role (4) puts a user in the `npda_audit_team_full_access` group (`general_functions/group_for_group.py`). The two booleans are set on their own, and about 70 non-test call sites check them directly.
- **They can disagree.** The model comments say an audit team member can also be a clinician. So a Coordinator with `is_rcpch_audit_team_member=True` gets national access without the role or group. **This is the main migration risk** (see Phase 0).
- **Group membership is derived from role.** `NPDAUserUpdateView.form_valid` clears a user's groups and re-adds `group_for_role(role)`. Any extra group is lost on the next edit, so role must be the single source of truth.
- **Superuser checks get simpler.** `has_perm()` is always True for an active superuser, so every `is_superuser or flag` becomes a single `has_perm(...)`.

## Decisions

- **Flagged users without the role:** their role is changed to RCPCH Audit Team.
- **`is_rcpch_staff`-only users:** they gain full audit team access. This is accepted.
- **Alert on joining the audit team:** add an `m2m_changed` handler on `NPDAUser.groups` that sends the existing admin notification when a user is added to `npda_audit_team_full_access`. This replaces the email currently sent when a flag changes.

## New permissions

Define each in `project/constants/user.py`, add it to `PERMISSIONS` and to the model's `Meta.permissions`, and attach it only to the audit team group.

| Permission | Model | Replaces the flag checks in |
|---|---|---|
| `can_access_all_pdus` | `PaediatricDiabetesUnit` | `PaediatricDiabetesUnitManager.get_pdu_for_request`, `mixins.py` patient/visit PK check, `organisations_adapter.py`, `home.new_home` inactive PDUs, `get_user_home_page`, `NPDAUserListView.get_queryset`, `submissions.py` list and `get_submission_checking_permission`, the `employer_match` and `include_admin_users` template tags, `submission_history.html`, `submission_employer_selector.html`, `submissions_list.html`, `NPDAUpdatePasswordForm.is_admin` (16-character passwords) |
| `can_manage_inactive_pdus` | `PaediatricDiabetesUnit` | Adding users or employers to inactive PDUs (`npda_users.py`) |
| `can_view_hidden_audit_periods` | `AuditPeriod` | `AuditPeriodManager.get_audit_period_for_request`, `home.new_home`, `context_processors.get_audit_periods_user_can_see` |
| `can_edit_closed_audit_periods` | `AuditPeriod` | `CheckCurrentAuditYearMixin`, `AuditPeriod.is_allowed_to_edit`, the CSV upload closed check |
| `can_override_data_upload_rules` | `Submission` | `QuestionnaireContextMixin`, `CheckCanCompleteQuestionnaireMixin`, switch-to-questionnaire / switch-to-csv, `patient_table_actions.html` |
| `can_manage_users_in_any_pdu` | `NPDAUser` | Cross-PDU user creation, `npda_user_employers`, activate/deactivate, `get_readonly_fields` |
| `can_assign_rcpch_audit_team_role` | `NPDAUser` | The `role == RCPCH_AUDIT_TEAM` guards on create/update, `show_rcpch_team` |
| `can_reset_user_two_factor` | `NPDAUser` | The `reset-two-factor` branch |
| `can_preview_features` | `NPDAUser` | `home.feature_flags`, `avatar_dropdown.html` |

**No new permission needed for banners:** use Django's built-in `view_banner` permission in place of the flag check in the `context_processors` banner targeting, and add `view_banner` to the audit team group in Phase 1.

Keep the existing protections for superusers: an audit team member still can't change a superuser's email or reset their 2FA. Write these as `has_perm(...) and not target.is_superuser`.

## Phases

### Phase 0 – data audit (before any code change)

Run the read-only report:

```bash
python manage.py audit_rcpch_user_flags
python manage.py audit_rcpch_user_flags --active-only
python manage.py audit_rcpch_user_flags --csv --output rcpch_flags_report.csv
```

It lists users with any of these findings:

- `flag_without_role`: a flag is set but the role is not RCPCH Audit Team. Phase 1 changes their role. Check each one is meant to have national access, and remove the flag instead if not.
- `staff_flag_only`: `is_rcpch_staff` is set without `is_rcpch_audit_team_member`. These users **gain** full audit team access.
- `role_without_flag`: the role is RCPCH Audit Team but a flag is False. These users **gain** whatever that flag gates.
- `group_mismatch`: the user's groups are not exactly `group_for_role(role)`.

The command never writes to the database.

### Phase 1 – add the permissions and fix the data (additive, safe to deploy)

- Add the constants and `Meta.permissions` entries (migration `0047_rcpch_audit_team_permissions`).
- Add the new permissions, and the built-in `view_banner`, to `RCPCH_AUDIT_TEAM_ONLY_PERMISSIONS` in `groups_seeder` (`create_groups.py`).
- Make `groups_seeder` idempotent, like E12's: it creates any missing group and adds any missing permission to every group. `s/start-prod` already runs it on every deploy (`seed --mode=seed_groups_and_permissions`), but until now it only gave permissions to groups it created, so new permissions never reached existing groups. It never removes a permission.
- The inconsistent users found by Phase 0 were fixed by hand, so no data migration is needed to change roles or re-sync groups.
- Log and email the admins when a user joins `npda_audit_team_full_access` (`signals.notify_joined_rcpch_audit_team`). Group syncs use `groups.set()` so re-saving an existing member doesn't trigger it.
- Django admin: changing a user's role syncs their group and flags (`NPDAUserAdmin.save_model`). `groups` is no longer editable there, because the admin saves m2m fields after `save_model` and would undo the sync.

**Why some Coordinators were only in the Editor group:** until April 2025 (437a926d) the edit-user view changed `role` without changing `groups`, so users promoted from Editor (many created by the March 2025 user import) kept the Editor group. The view has synced groups since; a regression test now covers it. The Django admin could still cause it until this phase.

### Phase 2 – switch the checks

- Replace each call site in the table with `user.has_perm("npda.<codename>")`, or `perms.npda.<codename>` in templates.
- Where code needs to know *what a user is* rather than *what they may do* (for example the user table badges and `user_roles()`), use `user.role == RCPCH_AUDIT_TEAM`.

### Phase 3 – remove the fields

- Drop both fields from `NPDAUser` and run `makemigrations`.
- Remove them from `REQUIRED_FIELDS`, `create_or_update_user` and `create_superuser`.
- Remove them from:
    - `NPDAUserForm` fields and widgets, and the `exclude_admin_user_field` tag (also fix its `"id_is_staffid_is_rcpch_staff"` typo);
    - the "can't set this flag" guards in `npda_users.py` and `show_rcpch_staff_box`;
    - `signals.py` (`EMAIL_TRIGGER_FIELDS`, `LOGGED_FIELDS`, `ADMIN_FLAGS`, the role-change notification list and the deletion email). Role changes already trigger both notifications;
    - `npda_user_table.html` badges.
- Update `create_dev_users`, `documentation/docs/developer/users.md`, `testing.md`, `manual-setup.md` and `tests/misc_py_shell_code.py`.
- Delete the `audit_rcpch_user_flags` command and its tests.

### Phase 4 – tests

- Update the factories and fixtures (`NPDAUserFactory`, `seed_users`, `UserDataClasses`, `tests/utils.py`), which set the flags directly.
- Update `test_patient_model_actions.py`, `test_mixins_against_session.py`, `test_npda_user_model_actions.py`, `test_meta_tests.py` and `test_download_template.py`.
- Add a test per new permission: the audit team group has it, the other groups don't.
- Run the full suite.

## Behaviour changes to sign off

- **Inactive superusers** lose implicit access, because `has_perm` returns False for inactive users. The current flag checks don't look at `is_active`.
- **`is_rcpch_staff`-only users** gain full audit team access (accepted).

## Suggested PRs

1. Phase 0 (this command).
2. Phase 1.
3. Phase 2.
4. Phases 3–4, after Phase 2 has run in production.
