# Generated by Django 5.0.6 on 2024-06-09 20:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("npda", "0003_remove_auditcohort_user_confirmed_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditcohort",
            name="patient",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="npda.patient"
            ),
        ),
    ]
