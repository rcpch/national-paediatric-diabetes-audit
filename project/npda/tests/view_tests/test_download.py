import pytest

from django.urls import reverse

from project.npda.models import NPDAUser, Submission
from project.npda.tests.test_csv_upload import mock_remote_calls
from project.npda.tests.model_tests.test_submissions import ALDER_HEY_PZ_CODE, GOSH_PZ_CODE
from project.npda.tests.UserDataClasses import test_user_audit_centre_coordinator_data
from project.npda.tests.utils import login_and_verify_user
from project.npda.general_functions.csv import csv_parse

@pytest.fixture
def valid_df(dummy_sheets_folder):
    file = dummy_sheets_folder / "dummy_sheet_test.csv"
    return csv_parse(file).df


@pytest.mark.parametrize(
    "action,filename,content_disposition,content_type",
    [
        pytest.param(
            "download-report",
            "dummy_sheet_test.csv",
            'attachment; filename="dummy_sheet_test_data_quality_report.xlsx"',
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        pytest.param(
            "download-data",
            "dummy_sheet_test.csv",
            'attachment; filename="dummy_sheet_test.csv"',
            "text/csv"),
    ],
)
@pytest.mark.django_db
def test_coordinator_can_download_data_for_their_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    mock_remote_calls,
    tmp_path,
    valid_df,
    action,
    filename,
    content_disposition,
    content_type
):
    ah_coordinator_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_coordinator_data.role,
    ).first()

    tmp_csv_path = tmp_path / filename
    valid_df.to_csv(tmp_csv_path, index=False)

    client = login_and_verify_user(client, ah_coordinator_user)

    upload_url = reverse("pdu-upload-csv", kwargs={ "pz_code": ALDER_HEY_PZ_CODE, "audit_period": "2025-2026"})

    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(
            upload_url,
            {
                'csv_upload': csv_file
            },
            format='multipart'
        )

    assert response.status_code == 302

    assert Submission.objects.count() == 1

    sub_id = Submission.objects.first().id
    download_url = reverse("submissions")

    response = client.post(
        download_url,
        {
            'submit-data': action,
            'audit_id': sub_id,
        }
    )

    assert response.status_code == 200

    assert response['Content-Disposition'] == content_disposition
    assert response['Content-Type'] == content_type


@pytest.mark.parametrize(
    "action,",
    [
        pytest.param("download-report"),
        pytest.param("download-data"),
    ],
)
@pytest.mark.django_db
def test_coordinator_cannot_download_report_for_other_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    mock_remote_calls,
    tmp_path,
    valid_df,
    action,
):
    ah_coordinator_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_coordinator_data.role,
    ).first()

    gosh_coordinator_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE,
        role=test_user_audit_centre_coordinator_data.role,
    ).first()

    tmp_csv_path = tmp_path / "dummy_sheet_test.csv"
    valid_df.to_csv(tmp_csv_path, index=False)

    client = login_and_verify_user(client, ah_coordinator_user)

    ah_upload_url = reverse("pdu-upload-csv", kwargs={ "pz_code": ALDER_HEY_PZ_CODE, "audit_period": "2025-2026"})

    # Send POST request with CSV file
    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(
            ah_upload_url,
            {
                'csv_upload': csv_file
            },
            format='multipart'
        )

    assert response.status_code == 302

    assert Submission.objects.count() == 1

    sub_id = Submission.objects.first().id
    download_url = reverse("submissions")

    client = login_and_verify_user(client, gosh_coordinator_user)

    response = client.post(
        download_url,
        {
            'submit-data': action,
            'audit_id': sub_id,
        }
    )

    assert response.status_code == 403
    assert "Content-Disposition" not in response

