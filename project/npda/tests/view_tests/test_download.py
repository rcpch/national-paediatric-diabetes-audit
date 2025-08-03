import pytest

from django.urls import reverse

from project.npda.models import NPDAUser, Submission
from project.npda.tests.test_csv_upload import mock_remote_calls
from project.npda.tests.model_tests.test_submissions import ALDER_HEY_PZ_CODE, GOSH_PZ_CODE
from project.npda.tests.UserDataClasses import AUDIT_CENTRE_EDITOR, AUDIT_CENTRE_COORDINATOR, AUDIT_CENTRE_READER, RCPCH_AUDIT_TEAM
from project.npda.tests.utils import login_and_verify_user
from project.npda.general_functions.csv import csv_parse

@pytest.fixture
def valid_df(dummy_sheets_folder):
    file = dummy_sheets_folder / "dummy_sheet_test.csv"
    return csv_parse(file).df


@pytest.mark.parametrize(
    "role,action",
    [
        pytest.param(f"{AUDIT_CENTRE_EDITOR}", "download-report"),
        pytest.param(f"{AUDIT_CENTRE_EDITOR}", "download-data"),
        pytest.param(f"{AUDIT_CENTRE_COORDINATOR}", "download-report"),
        pytest.param(f"{AUDIT_CENTRE_COORDINATOR}", "download-data"),
    ]
)
@pytest.mark.django_db
def test_uploaders_can_download_data_for_their_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    mock_remote_calls,
    tmp_path,
    valid_df,
    role,
    action
):
    ah_coordinator_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=role,
    ).first()

    tmp_csv_path = tmp_path / "dummy_sheet_test.csv"
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
    
    match action:
        case "download-report":
            assert response["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            assert response["Content-Disposition"] == 'attachment; filename="dummy_sheet_test_data_quality_report.xlsx"'
            
        case "download-data":
            assert response["Content-Type"] == "text/csv"
            assert response["Content-Disposition"] == 'attachment; filename="dummy_sheet_test.csv"'


@pytest.mark.parametrize(
    "role,action",
    [
        pytest.param(f"{AUDIT_CENTRE_EDITOR}", "download-report"),
        pytest.param(f"{AUDIT_CENTRE_EDITOR}", "download-data"),
        pytest.param(f"{AUDIT_CENTRE_COORDINATOR}", "download-report"),
        pytest.param(f"{AUDIT_CENTRE_COORDINATOR}", "download-data"),
    ]
)
@pytest.mark.django_db
def test_uploaders_cannot_download_data_for_other_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    mock_remote_calls,
    tmp_path,
    valid_df,
    role,
    action,
):
    ah_coordinator_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=role,
    ).first()

    gosh_coordinator_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE,
        role=role,
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



@pytest.mark.parametrize(
    "action,home_pdu,requested_pdu",
    [
        pytest.param(*list([action] + params)) for params in [
            [
                ALDER_HEY_PZ_CODE,
                ALDER_HEY_PZ_CODE,
            ],
            [
                ALDER_HEY_PZ_CODE,
                GOSH_PZ_CODE
            ]
        ] for action in [
            "download-report",
            "download-data"
        ]
    ]
)
@pytest.mark.django_db
def test_readers_cannot_download_data_for_any_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    mock_remote_calls,
    tmp_path,
    valid_df,
    action,
    home_pdu,
    requested_pdu,
):
    home_pdu_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=home_pdu,
        role=AUDIT_CENTRE_READER,
    ).first()

    requested_pdu_editor = NPDAUser.objects.filter(
        organisation_employers__pz_code=requested_pdu,
        role=AUDIT_CENTRE_EDITOR,
    ).first()

    requested_pdu_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=requested_pdu,
        role=AUDIT_CENTRE_READER,
    ).first()

    tmp_csv_path = tmp_path / "dummy_sheet_test.csv"
    valid_df.to_csv(tmp_csv_path, index=False)

    client = login_and_verify_user(client, requested_pdu_editor)
    pz_code = requested_pdu_editor.organisation_employers.first().pz_code

    upload_url = reverse("pdu-upload-csv", kwargs={ "pz_code": pz_code, "audit_period": "2025-2026"})

    # Send POST request with CSV file
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

    client = login_and_verify_user(client, home_pdu_user)

    response = client.post(
        download_url,
        {
            'submit-data': action,
            'audit_id': sub_id,
        }
    )

    assert response.status_code == 403
    assert "Content-Disposition" not in response

    client = login_and_verify_user(client, requested_pdu_user)

    response = client.post(
        download_url,
        {
            'submit-data': action,
            'audit_id': sub_id,
        }
    )

    assert response.status_code == 403
    assert "Content-Disposition" not in response


@pytest.mark.parametrize(
    "action",
    [
        pytest.param("download-report"),
        pytest.param("download-data")
    ]
)
@pytest.mark.django_db
def test_rcpch_audit_team_can_download_data_for_any_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    mock_remote_calls,
    tmp_path,
    valid_df,
    action
):
    ah_coordinator_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=AUDIT_CENTRE_COORDINATOR,
    ).first()

    tmp_csv_path = tmp_path / "dummy_sheet_test.csv"
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

    gosh_coordinator_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE,
        role=AUDIT_CENTRE_COORDINATOR,
    ).first()

    tmp_csv_path = tmp_path / "dummy_sheet_test.csv"
    valid_df.to_csv(tmp_csv_path, index=False)

    client = login_and_verify_user(client, gosh_coordinator_user)

    upload_url = reverse("pdu-upload-csv", kwargs={ "pz_code": GOSH_PZ_CODE, "audit_period": "2025-2026"})

    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(
            upload_url,
            {
                'csv_upload': csv_file
            },
            format='multipart'
        )

    assert response.status_code == 302

    assert Submission.objects.count() == 2
    sub_id = Submission.objects.first().id

    gosh_coordinator_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE,
        role=AUDIT_CENTRE_COORDINATOR,
    ).first()

    download_url = reverse("submissions")

    response = client.post(
        download_url,
        {
            'submit-data': action,
            'audit_id': sub_id,
        }
    )

    assert response.status_code == 200

    match action:
        case "download-report":
            assert response["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            assert response["Content-Disposition"] == 'attachment; filename="dummy_sheet_test_data_quality_report.xlsx"'

        case "download-data":
            assert response["Content-Type"] == "text/csv"
            assert response["Content-Disposition"] == 'attachment; filename="dummy_sheet_test.csv"'