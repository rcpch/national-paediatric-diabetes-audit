import os
import tempfile

import pytest
from django.apps import apps
from django.core.management import call_command

# Factories
from project.npda.tests.factories import PaediatricsDiabetesUnitFactory

# Models
PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")
OrganisationEmployer = apps.get_model("npda", "OrganisationEmployer")
NPDAUser = apps.get_model("npda", "NPDAUser")

from project.constants import (  # noqa: E402
    AUDIT_CENTRE_COORDINATOR,
    AUDIT_CENTRE_EDITOR,
    DR,
    MS,
)


@pytest.mark.django_db
def test_import_users_command(
    seed_groups_fixture,
    seed_users_fixture,
):
    # Create sample PaediatricDiabetesUnit objects
    PaediatricsDiabetesUnitFactory(pz_code="PZ999")
    PaediatricsDiabetesUnitFactory(pz_code="PZ215")

    # Create a temporary CSV file with sample data
    csv_content = f"""first_name,surname,title,email,role,pz_code
John,Doe,Dr,john.doe@example.com,{AUDIT_CENTRE_COORDINATOR},PZ999
Jane,Smith,Ms,jane.smith@example.com,{AUDIT_CENTRE_EDITOR},PZ215
"""
    temp_dir = tempfile.mkdtemp()
    csv_file_path = os.path.join(temp_dir, "sample_users.csv")
    with open(csv_file_path, "w") as csv_file:
        csv_file.write(csv_content)

    # Run the import_users management command
    call_command("import_users", csv_file_path)

    # Check that the users were created
    user1 = NPDAUser.objects.get(email="john.doe@example.com")
    assert user1.first_name == "John"
    assert user1.surname == "Doe"
    assert user1.title == DR
    assert user1.role == AUDIT_CENTRE_COORDINATOR
    assert OrganisationEmployer.objects.filter(
        paediatric_diabetes_unit__pz_code="PZ999",
        npda_user=user1,
    ).exists()

    user2 = NPDAUser.objects.get(email="jane.smith@example.com")
    assert user2.first_name == "Jane"
    assert user2.surname == "Smith"
    assert user2.title == MS
    assert user2.role == AUDIT_CENTRE_EDITOR
    assert OrganisationEmployer.objects.filter(
        paediatric_diabetes_unit__pz_code="PZ215",
        npda_user=user2,
    ).exists()

    # Clean up the temporary directory
    os.remove(csv_file_path)
    os.rmdir(temp_dir)
