# Generated by Django 5.0.6 on 2024-05-11 15:14

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("npda", "0004_patient_errors_patient_is_valid_visit_errors_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="patient",
            name="errors",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    blank=True,
                    default=None,
                    null=True,
                    verbose_name="Validation errors",
                ),
                null=True,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="patient",
            name="is_valid",
            field=models.BooleanField(
                blank=True, default=False, null=True, verbose_name="Record is valid"
            ),
        ),
        migrations.AlterField(
            model_name="visit",
            name="errors",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    blank=True,
                    default=None,
                    null=True,
                    verbose_name="Validation errors",
                ),
                null=True,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="visit",
            name="is_valid",
            field=models.BooleanField(
                blank=True, default=False, null=True, verbose_name="Record is valid"
            ),
        ),
    ]
