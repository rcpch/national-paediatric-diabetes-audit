from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("npda", "0042_remove_npdauser_view_preference"),
    ]

    operations = [
        migrations.AddField(
            model_name="npdauser",
            name="feature_flags",
            field=models.JSONField(default=list, blank=True),
        ),
    ]
