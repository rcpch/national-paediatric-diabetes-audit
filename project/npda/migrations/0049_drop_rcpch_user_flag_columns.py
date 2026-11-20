"""
Drop the is_rcpch_audit_team_member / is_rcpch_staff columns (the "contract"
half of an expand/contract change).

0048 removed both fields from Django's model state, gave the columns a
database default and recorded who held the flags in VisitActivity. It has been
deployed, so no running revision reads or writes the columns any more. This
migration only changes the database: the model state is already correct.

Reversing re-adds both columns, defaulting to False. The values they held are
not restored; the record of them is the "RCPCH flags at removal" VisitActivity
entries written by 0048.
"""

from django.db import migrations

TABLE = "npda_npdauser"
FLAG_COLUMNS = ("is_rcpch_audit_team_member", "is_rcpch_staff")


class Migration(migrations.Migration):
    dependencies = [
        ("npda", "0048_remove_rcpch_user_flags_from_models"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                f'ALTER TABLE "{TABLE}" DROP COLUMN IF EXISTS "{column}";'
                for column in FLAG_COLUMNS
            ],
            reverse_sql=[
                f'ALTER TABLE "{TABLE}" ADD COLUMN IF NOT EXISTS "{column}" '
                "boolean NOT NULL DEFAULT false;"
                for column in FLAG_COLUMNS
            ],
        ),
    ]
