# Generated by Django 5.0 on 2023-12-30 23:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("npda", "0007_alter_site_reason_leaving_service"),
    ]

    operations = [
        migrations.AlterField(
            model_name="site",
            name="date_leaving_service",
            field=models.DateField(
                blank=True, null=True, verbose_name="Date of leaving service"
            ),
        ),
    ]
