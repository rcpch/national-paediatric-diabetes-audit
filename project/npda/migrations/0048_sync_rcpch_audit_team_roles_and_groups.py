"""
Phase 1 of retiring is_rcpch_audit_team_member and is_rcpch_staff.
See documentation/docs/developer/rcpch-flags-retirement-plan.md

1. Give the RCPCH audit team group the permissions that replace the flags.
   Deploys don't run the group seeder, so this can't be left to it.
2. Give every user with either flag the RCPCH Audit Team role, and set both
   flags for everyone with that role, so role and flags agree until the flags
   are removed.
3. Put every user in exactly the group for their role. This also repairs users
   whose role was changed before the edit-user view synced groups (April 2025).

Historical models don't fire signals, so this sends no emails.
"""

from django.contrib.auth.management import create_permissions
from django.contrib.contenttypes.management import create_contenttypes
from django.db import migrations

# Copied rather than imported: migrations must not depend on code that changes.
RCPCH_AUDIT_TEAM = 4

ROLE_GROUPS = {
    1: "trust_audit_team_coordinator_access",
    2: "trust_audit_team_edit_access",
    3: "trust_audit_team_view_only",
    RCPCH_AUDIT_TEAM: "npda_audit_team_full_access",
    7: "patient_access",
}
# group_for_role's fallback for any other role
DEFAULT_GROUP = "trust_audit_team_view_only"

RCPCH_AUDIT_TEAM_ONLY_PERMISSIONS = [
    ("paediatricdiabetesunit", "can_access_all_pdus"),
    ("paediatricdiabetesunit", "can_manage_inactive_pdus"),
    ("auditperiod", "can_view_hidden_audit_periods"),
    ("auditperiod", "can_edit_closed_audit_periods"),
    ("submission", "can_override_data_upload_rules"),
    ("npdauser", "can_manage_users_in_any_pdu"),
    ("npdauser", "can_assign_rcpch_audit_team_role"),
    ("npdauser", "can_reset_user_two_factor"),
    ("npdauser", "can_preview_features"),
    ("banner", "view_banner"),
]


def add_permissions_to_audit_team_group(apps, schema_editor):
    # Permissions are normally created after all migrations run
    # (post_migrate), so create them now to attach them.
    app_config = apps.get_app_config("npda")
    app_config.models_module = True
    create_contenttypes(app_config, verbosity=0, apps=apps)
    create_permissions(app_config, verbosity=0, apps=apps)
    app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    group = Group.objects.filter(name=ROLE_GROUPS[RCPCH_AUDIT_TEAM]).first()
    if group is None:
        # Fresh database: the seeder creates the group with these permissions.
        return

    for model, codename in RCPCH_AUDIT_TEAM_ONLY_PERMISSIONS:
        group.permissions.add(
            Permission.objects.get(
                content_type__app_label="npda",
                content_type__model=model,
                codename=codename,
            )
        )


def sync_roles_and_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    NPDAUser = apps.get_model("npda", "NPDAUser")

    groups = {group.name: group for group in Group.objects.all()}
    if not groups:
        # Fresh database: no groups or users to sync.
        return

    flagged = NPDAUser.objects.filter(is_rcpch_audit_team_member=True) | (
        NPDAUser.objects.filter(is_rcpch_staff=True)
    )
    flagged.exclude(role=RCPCH_AUDIT_TEAM).update(role=RCPCH_AUDIT_TEAM)

    NPDAUser.objects.filter(role=RCPCH_AUDIT_TEAM).update(
        is_rcpch_audit_team_member=True, is_rcpch_staff=True
    )

    for user in NPDAUser.objects.prefetch_related("groups"):
        group = groups.get(ROLE_GROUPS.get(user.role, DEFAULT_GROUP))
        if group is None:
            continue
        if {g.pk for g in user.groups.all()} != {group.pk}:
            user.groups.set([group])


class Migration(migrations.Migration):
    dependencies = [
        ("npda", "0047_rcpch_audit_team_permissions"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(
            add_permissions_to_audit_team_group, migrations.RunPython.noop
        ),
        migrations.RunPython(sync_roles_and_groups, migrations.RunPython.noop),
    ]
