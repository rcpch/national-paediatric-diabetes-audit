"""
Seeds 2 Patients in test db once per session. One user in GOSH. One user in different Trust (Addenbrooke's)
"""

# Standard imports
import pytest

# 3rd Party imports

# E12 Imports
from npda.models import Organisation, Patient
from .PatientFactory import PatientFactory


@pytest.mark.django_db
@pytest.fixture(scope="session")
def seed_cases_fixture(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # prevent repeat seed
        if not Patient.objects.all().exists():
            GOSH = Organisation.objects.get(
                ods_code="RP401",
                trust__ods_code="RP4",
            )

            ADDENBROOKES = Organisation.objects.get(
                ods_code="RGT01",
                trust__ods_code="RGT",
            )

            for organisation in [GOSH, ADDENBROOKES]:
                Patient(
                    first_name=f"child_{organisation.name}",
                    organisations__organisation=organisation,
                )
        else:
            print("Test cases seeded. Skipping")
