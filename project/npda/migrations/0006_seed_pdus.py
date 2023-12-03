# standard library imports
from datetime import datetime

# Django imports
from django.contrib.gis.geos import Point
from django.db import migrations
from django.utils import timezone
from django.contrib.gis.db.models import Q

from ...constants import PZ_CODES


def seed_pdus(apps, schema_editor):
    """
    Seed function which populates the PaediatricDiabetesUnit model from JSON.
    """

    # Get models
    Organisation = apps.get_model("npda", "Organisation")
    PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")

    if PaediatricDiabetesUnit.objects.all().count() >= 173:
        print(
            "\033[31m",
            "173 Paediatric Diabetes Units already seeded. Skipping...",
            "\033[31m",
        )
    else:
        print("\033[31m", "Adding new Paediatric Diabetes Units...", "\033[31m")

        for added, pdu in enumerate(PZ_CODES):
            if "ods_code" in pdu:
                if Organisation.objects.filter(ods_code=pdu["ods_code"]).exists():
                    try:
                        o = Organisation.objects.filter(ods_code=pdu["ods_code"]).get()
                        pdu = PaediatricDiabetesUnit.objects.create(
                            pz_code=pdu["pz_code"], organisation=o
                        )
                        pdu.save()
                    except Exception as error:
                        print(f"Unable to save {o} - {pdu['pz_code']}: {error}")
            else:
                print(f"{pdu['paediatric_unit']} not added")

        print(f"{added+1} PDUs added.")


class Migration(migrations.Migration):
    dependencies = [
        ("npda", "0005_seed_organisations"),
    ]

    operations = [migrations.RunPython(seed_pdus)]
