# Generated by Django 5.0.6 on 2024-06-09 21:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("npda", "0004_alter_auditcohort_patient"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditcohort",
            name="submission_approved",
            field=models.BooleanField(
                default=False,
                help_text="Submission has been approved for inclusion in the audit",
                verbose_name="Submission approved",
            ),
        ),
        migrations.AlterField(
            model_name="auditcohort",
            name="patient",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="audit_cohorts",
                to="npda.patient",
            ),
        ),
    ]
