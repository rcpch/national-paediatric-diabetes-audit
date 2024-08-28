# Generated by Django 5.0.7 on 2024-07-25 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("npda", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="patient",
            name="nhs_number",
            field=models.CharField(verbose_name="NHS Number"),
        ),
        migrations.AlterField(
            model_name="patient",
            name="postcode",
            field=models.CharField(
                blank=True, null=True, verbose_name="Postcode of usual address"
            ),
        ),
    ]