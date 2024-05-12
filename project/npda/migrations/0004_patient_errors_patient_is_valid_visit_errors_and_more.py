# Generated by Django 5.0.4 on 2024-05-10 21:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("npda", "0003_alter_npdauser_options_alter_patient_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="patient",
            name="errors",
            field=models.CharField(
                blank=True, null=True, verbose_name="Validation errors"
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="is_valid",
            field=models.BooleanField(
                blank=True, null=True, verbose_name="Record is valid"
            ),
        ),
        migrations.AddField(
            model_name="visit",
            name="errors",
            field=models.CharField(
                blank=True, null=True, verbose_name="Validation errors"
            ),
        ),
        migrations.AddField(
            model_name="visit",
            name="is_valid",
            field=models.BooleanField(
                blank=True, null=True, verbose_name="Record is valid"
            ),
        ),
    ]