"""
Stop using the retired is_rcpch_audit_team_member / is_rcpch_staff fields
without dropping their database columns (the "expand" half of an
expand/contract change).

Deploys start the new revision, and run migrate, while the previous revision
is still serving. The previous revision's model still has both fields, so the
columns must stay until it is gone. This migration:

0. writes a VisitActivity entry recording the flags of every user who has
   either set, as an audit record of who held them at removal (users created
   with a flag set have no earlier record of it, and changes were only logged
   from July 2025);
1. gives both columns a database default of False, so inserts from code that
   no longer knows about the fields (this release onwards) still succeed;
2. removes the fields from Django's model state only. The columns stay, and the
   previous revision can keep reading and writing them while it drains.

A later migration drops the columns, once no running revision uses them.
"""

from django.db import migrations, models
from django.db.models import Q

FLAG_FIELDS = ("is_rcpch_audit_team_member", "is_rcpch_staff")

# VisitActivity.CHANGED_ADMIN_FLAG ("Superuser or admin status changed"), the
# activity the user change log already uses for flag changes
CHANGED_ADMIN_FLAG = 13


def record_flags_at_removal(apps, schema_editor):
    """
    One VisitActivity per user with either flag set, recording both flags,
    e.g. "RCPCH flags at removal: is_rcpch_audit_team_member=True,
    is_rcpch_staff=False".
    """
    NPDAUser = apps.get_model("npda", "NPDAUser")
    VisitActivity = apps.get_model("npda", "VisitActivity")

    flagged_users = NPDAUser.objects.filter(
        Q(is_rcpch_audit_team_member=True) | Q(is_rcpch_staff=True)
    ).values_list("pk", *FLAG_FIELDS)

    VisitActivity.objects.bulk_create(
        [
            VisitActivity(
                activity=CHANGED_ADMIN_FLAG,
                npdauser_id=pk,
                details=(
                    "RCPCH flags at removal: "
                    f"is_rcpch_audit_team_member={is_rcpch_audit_team_member}, "
                    f"is_rcpch_staff={is_rcpch_staff}"
                ),
            )
            for pk, is_rcpch_audit_team_member, is_rcpch_staff in flagged_users
        ]
    )


class Migration(migrations.Migration):
    dependencies = [
        ("npda", "0047_rcpch_audit_team_permissions"),
    ]

    operations = [
        # 0. Audit record of who held the flags. Reversing leaves the entries
        # in place: they're an audit log.
        migrations.RunPython(record_flags_at_removal, migrations.RunPython.noop),
        # 1. Database default, so inserts that omit the columns still work
        *[
            migrations.AlterField(
                model_name="npdauser",
                name=field_name,
                field=models.BooleanField(default=False, db_default=False),
            )
            for field_name in FLAG_FIELDS
        ],
        # 2. Remove from the model only; the columns stay in the database
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(model_name="npdauser", name=field_name)
                for field_name in FLAG_FIELDS
            ],
            database_operations=[],
        ),
    ]
