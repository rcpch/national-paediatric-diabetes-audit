# Generated by Django 5.0 on 2023-12-30 23:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("npda", "0006_patient_gp_practice_postcode_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="site",
            name="reason_leaving_service",
            field=models.PositiveSmallIntegerField(
                blank=True,
                choices=[
                    (1, "Transitioned to adult diabetes service"),
                    (2, "Moved out of area"),
                    (3, "Other"),
                ],
                null=True,
                verbose_name="Reason for leaving service",
            ),
        ),
    ]
