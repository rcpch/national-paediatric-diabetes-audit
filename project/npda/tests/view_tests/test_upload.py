import os

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.urls import reverse

from project.npda.models.audit_period import AuditPeriod
from project.npda.models.npda_user import NPDAUser
from project.npda.tests.model_tests.test_submissions import ALDER_HEY_PZ_CODE
from project.npda.tests.UserDataClasses import \
    test_user_audit_centre_coordinator_data
from project.npda.tests.utils import login_and_verify_user
from project.npda.tests.test_csv_upload import mock_remote_calls

@pytest.mark.django_db
def test_generate_csv_upload_to_view(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    mock_remote_calls,
    tmpdir,
):
    """Integration test for CSV generation and upload to home view.

    Use the generate csv manage.py cmd to create a CSV file and upload it to
    the home view.

    Mocks remote calls.
    """

    # Get a user
    ah_coordinator_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_coordinator_data.role,
    ).first()
    client = login_and_verify_user(client, ah_coordinator_user)

    # Directory to store generated CSV files
    tmpdir_path = str(tmpdir)

    # Simulate `create_csv` commands
    call_command(
        "create_csv",
        pts=5,
        visits="CDCD DHPC ACDC CDCD",
        hb_target="T",
        age_range="11_15",
        build=True,
        output_path=tmpdir_path,
    )
    call_command(
        "create_csv",
        pts=5,
        visits="CDCCD DDCC CACC",
        hb_target="A",
        age_range="16_19",
        build=True,
        output_path=tmpdir_path,
    )
    call_command(
        "create_csv",
        pts=5,
        visits="CDC ACDC CDCD",
        hb_target="T",
        age_range="0_4",
        build=True,
        output_path=tmpdir_path,
    )
    call_command(
        "create_csv",
        coalesce=True,
        output_path=tmpdir_path,
    )

    # Read the generated coalesced CSV for upload
    tmp_dir_filenames = os.listdir(tmpdir_path)
    coalesced_csv_name = next(
        (file for file in tmp_dir_filenames if file.startswith("coalesced_")),
        None,
    )
    coalesced_csv_path = os.path.join(tmpdir_path, coalesced_csv_name)
    assert os.path.exists(coalesced_csv_path), "CSV file not generated"

    with open(coalesced_csv_path, "rb") as f:
        csv_file = SimpleUploadedFile(
            f.name, f.read(), content_type="text/csv"
        )

    # Send POST request with CSV file
    url = reverse("upload_csv")
    response = client.post(url, {"csv_upload": csv_file})

    # Assert the response to ensure no error
    assert response.status_code == 302


@pytest.mark.django_db
def test_coordinator_cannot_upload_csv_to_closed_audit_year(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    mock_remote_calls,
    dummy_sheet_csv
):
    ah_coordinator_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_coordinator_data.role,
    ).first()
    client = login_and_verify_user(client, ah_coordinator_user)

    audit_period = AuditPeriod.objects.get_default_audit_period()
    audit_period.is_open = False
    audit_period.save()

    csv_file = SimpleUploadedFile(
        "test_coordinator_cannot_upload_csv_to_closed_audit_year.csv",
        dummy_sheet_csv.encode(),
        content_type="text/csv"
    )

    # Send POST request with CSV file
    url = reverse("upload_csv")
    response = client.post(url, {"csv_upload": csv_file})

    # Assert the response to ensure no error
    assert response.status_code == 403