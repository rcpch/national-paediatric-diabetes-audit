# Generated by Django 5.1 on 2024-08-28 14:05

import citext.fields
from django.db import migrations
from django.contrib.postgres.operations import CITextExtension


class Migration(migrations.Migration):

    dependencies = [
        ("npda", "0007_alter_patient_nhs_number_and_more"),
    ]

    operations = [
        CITextExtension(),
        migrations.AlterField(
            model_name="npdauser",
            name="email",
            field=citext.fields.CIEmailField(
                error_messages={"unique": "This email address is already in use."},
                help_text="Enter your email address.",
                max_length=254,
                unique=True,
                verbose_name="Email address",
            ),
        ),
    ]