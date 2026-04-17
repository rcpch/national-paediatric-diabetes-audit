import pathlib

import pytest
from django.urls import reverse

from project.npda.models import AuditPeriod, NPDAUser
from project.npda.tests.model_tests.test_submissions import (
    ALDER_HEY_PZ_CODE,
    GOSH_PZ_CODE,
)
from project.npda.tests.UserDataClasses import (
    AUDIT_CENTRE_COORDINATOR,
    AUDIT_CENTRE_EDITOR,
    AUDIT_CENTRE_READER,
    RCPCH_AUDIT_TEAM,
)
from project.npda.tests.utils import create_submission, login_and_verify_user

_SHEETS_DIR = pathlib.Path(__file__).resolve().parents[2] / "dummy_sheets"
_CSV_2021 = (_SHEETS_DIR / "dummy_sheet_test.csv").read_bytes()
_CSV_2026 = (_SHEETS_DIR / "dummy_sheet_2026_test.csv").read_bytes()


@pytest.mark.parametrize(
    "role,action",
    [
        pytest.param(f"{AUDIT_CENTRE_EDITOR}", "download-report"),
        pytest.param(f"{AUDIT_CENTRE_EDITOR}", "download-data"),
        pytest.param(f"{AUDIT_CENTRE_COORDINATOR}", "download-report"),
        pytest.param(f"{AUDIT_CENTRE_COORDINATOR}", "download-data"),
    ],
)
@pytest.mark.django_db
def test_uploaders_can_download_data_for_their_pdu(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client, role, action
):
    audit_period = AuditPeriod.objects.get(slug="2025-2026")
    sub = create_submission(
        audit_period,
        pz_code=ALDER_HEY_PZ_CODE,
        csv_file_name="test_download.csv",
        csv_file=_CSV_2021,
    )

    coordinator_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=role,
    ).first()

    client = login_and_verify_user(client, coordinator_user)

    download_url = reverse(
        "pdu-submissions",
        kwargs={
            "pz_code": ALDER_HEY_PZ_CODE,
            "audit_period": sub.audit_period.slug,
        },
    )

    response = client.post(
        download_url,
        {
            "submit-data": action,
            "audit_id": sub.id,
        },
    )

    assert response.status_code == 200

    match action:
        case "download-report":
            assert (
                response["Content-Type"]
                == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            assert (
                response["Content-Disposition"]
                == 'attachment; filename="test_download_data_quality_report.xlsx"'
            )

        case "download-data":
            assert response["Content-Type"] == "text/csv"
            assert (
                response["Content-Disposition"]
                == 'attachment; filename="test_download.csv"'
            )


@pytest.mark.parametrize(
    "role,action",
    [
        pytest.param(f"{AUDIT_CENTRE_EDITOR}", "download-report"),
        pytest.param(f"{AUDIT_CENTRE_EDITOR}", "download-data"),
        pytest.param(f"{AUDIT_CENTRE_COORDINATOR}", "download-report"),
        pytest.param(f"{AUDIT_CENTRE_COORDINATOR}", "download-data"),
    ],
)
@pytest.mark.django_db
def test_uploaders_cannot_download_data_for_other_pdu(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client, role, action
):
    audit_period = AuditPeriod.objects.get(slug="2025-2026")
    sub = create_submission(
        audit_period,
        pz_code=ALDER_HEY_PZ_CODE,
        csv_file_name="test_download.csv",
        csv_file=_CSV_2021,
    )

    gosh_coordinator_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE,
        role=role,
    ).first()

    download_url = reverse(
        "pdu-submissions",
        kwargs={
            "pz_code": ALDER_HEY_PZ_CODE,
            "audit_period": sub.audit_period.slug,
        },
    )

    client = login_and_verify_user(client, gosh_coordinator_user)

    response = client.post(
        download_url,
        {
            "submit-data": action,
            "audit_id": sub.id,
        },
    )

    assert response.status_code == 403
    assert "Content-Disposition" not in response


@pytest.mark.parametrize(
    "action,home_pdu,requested_pdu",
    [
        pytest.param(*list([action] + params))
        for params in [
            [
                ALDER_HEY_PZ_CODE,
                ALDER_HEY_PZ_CODE,
            ],
            [ALDER_HEY_PZ_CODE, GOSH_PZ_CODE],
        ]
        for action in ["download-report", "download-data"]
    ],
)
@pytest.mark.django_db
def test_readers_cannot_download_data_for_any_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    action,
    home_pdu,
    requested_pdu,
):
    audit_period = AuditPeriod.objects.get(slug="2025-2026")
    sub = create_submission(
        audit_period,
        pz_code=requested_pdu,
        csv_file_name="test_download.csv",
        csv_file=_CSV_2021,
    )

    home_pdu_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=home_pdu,
        role=AUDIT_CENTRE_READER,
    ).first()

    requested_pdu_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=requested_pdu,
        role=AUDIT_CENTRE_READER,
    ).first()

    download_url = reverse(
        "pdu-submissions",
        kwargs={
            "pz_code": requested_pdu,
            "audit_period": sub.audit_period.slug,
        },
    )

    client = login_and_verify_user(client, home_pdu_user)

    response = client.post(
        download_url,
        {
            "submit-data": action,
            "audit_id": sub.id,
        },
    )

    assert response.status_code == 403
    assert "Content-Disposition" not in response

    client = login_and_verify_user(client, requested_pdu_user)

    response = client.post(
        download_url,
        {
            "submit-data": action,
            "audit_id": sub.id,
        },
    )

    assert response.status_code == 403
    assert "Content-Disposition" not in response


@pytest.mark.parametrize(
    "action,pz_code",
    [
        pytest.param("download-report", ALDER_HEY_PZ_CODE),
        pytest.param("download-data", ALDER_HEY_PZ_CODE),
        pytest.param("download-report", GOSH_PZ_CODE),
        pytest.param("download-data", GOSH_PZ_CODE),
    ],
)
@pytest.mark.django_db
def test_rcpch_audit_team_can_download_data_for_any_pdu(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client, action, pz_code
):
    audit_period = AuditPeriod.objects.get(slug="2025-2026")
    sub = create_submission(
        audit_period,
        pz_code=pz_code,
        csv_file_name="test_download.csv",
        csv_file=_CSV_2021,
    )

    rcpch_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=pz_code,
        role=RCPCH_AUDIT_TEAM,
    ).first()

    client = login_and_verify_user(client, rcpch_user)

    download_url = reverse(
        "pdu-submissions",
        kwargs={
            "pz_code": pz_code,
            "audit_period": sub.audit_period.slug,
        },
    )

    response = client.post(
        download_url,
        {
            "submit-data": action,
            "audit_id": sub.id,
        },
    )

    assert response.status_code == 200

    match action:
        case "download-report":
            assert (
                response["Content-Type"]
                == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            assert (
                response["Content-Disposition"]
                == 'attachment; filename="test_download_data_quality_report.xlsx"'
            )

        case "download-data":
            assert response["Content-Type"] == "text/csv"
            assert (
                response["Content-Disposition"]
                == 'attachment; filename="test_download.csv"'
            )


@pytest.mark.django_db
def test_can_download_report_for_2026_audit_period(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client
):
    audit_period = AuditPeriod.objects.get(slug="2026-2027")
    sub = create_submission(
        audit_period,
        pz_code=ALDER_HEY_PZ_CODE,
        csv_file_name="test_download_2026.csv",
        csv_file=_CSV_2026,
    )

    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=AUDIT_CENTRE_EDITOR,
    ).first()

    client = login_and_verify_user(client, user)

    download_url = reverse(
        "pdu-submissions",
        kwargs={
            "pz_code": ALDER_HEY_PZ_CODE,
            "audit_period": sub.audit_period.slug,
        },
    )

    response = client.post(
        download_url,
        {
            "submit-data": "download-report",
            "audit_id": sub.id,
        },
    )

    assert response.status_code == 200
    assert (
        response["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert (
        response["Content-Disposition"]
        == 'attachment; filename="test_download_2026_data_quality_report.xlsx"'
    )
