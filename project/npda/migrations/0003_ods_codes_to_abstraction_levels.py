from datetime import date
from django.db import migrations
from ...constants import (
    INTEGRATED_CARE_BOARDS,
    NHS_ENGLAND_REGIONS,
    LOCAL_HEALTH_BOARDS,
)


def ods_codes_to_abstraction_levels(apps, schema_editor):
    """
    Updates all the abstraction level models with ODS codes
    """
    IntegratedCareBoard = apps.get_model("npda", "IntegratedCareBoard")
    NHSEnglandRegion = apps.get_model("npda", "NHSEnglandRegion")
    LocalHealthBoard = apps.get_model("npda", "LocalHealthBoard")

    print(
        "\033[38;2;17;167;142m",
        "Updating Integrated Care Boards with ODS codes",
        "\033[38;2;17;167;142m",
    )

    for icb in INTEGRATED_CARE_BOARDS:
        # iterates through all 42 ICBs and updates model with ODS code
        if IntegratedCareBoard.objects.filter(
            boundary_identifier=icb["gss_code"]
        ).exists():
            # should already exist in the database
            IntegratedCareBoard.objects.filter(
                boundary_identifier=icb["gss_code"]
            ).update(ods_code=icb["ods_code"], publication_date=date(2023, 3, 15))
            print(f"Updated {icb['name']} to include ODS code")
        else:
            raise Exception(
                f"Seeding error. {icb['gss_code']}/{icb['name']} not found in the database to seed."
            )

    print(
        "\033[38;2;17;167;142m",
        "Updating NHS England Regions with NHS England region codes",
        "\033[38;2;17;167;142m",
    )

    for nhs_england_region in NHS_ENGLAND_REGIONS:
        # iterates through all 42 ICBs and updates model with ODS code
        if NHSEnglandRegion.objects.filter(
            boundary_identifier=nhs_england_region["NHS_ENGLAND_REGION_ONS_CODE"]
        ).exists():
            # should already exist in the database
            nhs_england_region_object = NHSEnglandRegion.objects.filter(
                boundary_identifier=nhs_england_region["NHS_ENGLAND_REGION_ONS_CODE"]
            ).get()
            nhs_england_region_object.region_code = nhs_england_region[
                "NHS_ENGLAND_REGION_CODE"
            ]
            nhs_england_region_object.publication_date = date(2022, 7, 30)
            nhs_england_region_object.save()
            print(
                f"Updated {nhs_england_region['NHS_ENGLAND_REGION_NAME']} to include ODS code"
            )
        else:
            raise Exception("Seeding error. No NHS England region entity to seed.")

    print(
        "\033[38;2;17;167;142m",
        "Updating Local Health Boards with ODS codes.",
        "\033[38;2;17;167;142m",
    )

    for local_health_board in LOCAL_HEALTH_BOARDS:
        # iterates through all 42 ICBs and updates model with ODS code
        if LocalHealthBoard.objects.filter(
            boundary_identifier=local_health_board["gss_code"]
        ).exists():
            # should already exist in the database
            LocalHealthBoard.objects.filter(
                boundary_identifier=local_health_board["gss_code"]
            ).update(
                ods_code=local_health_board["ods_code"],
                publication_date=date(2022, 4, 14),
            )
            print(f"Updated {local_health_board['health_board']} to include ODS code")
        else:
            raise Exception("Seeding error. No Local Health Board entity to seed.")


class Migration(migrations.Migration):
    dependencies = [
        ("npda", "0002_seed_abstraction_levels"),
    ]

    operations = [
        migrations.RunPython(ods_codes_to_abstraction_levels),
    ]
