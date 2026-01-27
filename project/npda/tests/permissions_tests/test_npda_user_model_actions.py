"""
Tests for NPDAUser model actions.

- NPDAUser can be created if a valid email, role and PDU are provided.
- NPDAUser cannot be created if an invalid email is provided.
- NPDAUser cannot be created if an invalid role is provided (incorrect key).
- NPDAUser cannot be created if an invalid PDU is provided.
- NPDAUser can be updated if a valid email, role and PDU are provided.
- NPDAUser cannot be updated if an invalid email is provided.
- NPDAUser cannot be updated if an invalid role is provided (incorrect key).
- NPDAUser cannot be updated if an invalid PDU is provided.
- NPDAUser cannot be deleted.
- NPDAUser can be deactivated.
- NPDAUser can be reactivated.
"""

from datetime import date
import logging
from http import HTTPStatus

# Python imports
import pytest

# 3rd party imports
from django.apps import apps
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from project.npda.models.audit_period import AuditPeriod

from project.constants.user import (
    AUDIT_CENTRE_COORDINATOR,
    RCPCH_AUDIT_TEAM,
    TRUST_AUDIT_TEAM_COORDINATOR_ACCESS,
    AUDIT_CENTRE_READER,
)

# E12 imports
from project.npda.general_functions.audit_period import get_audit_period_for_date
from project.npda.general_functions.csv import csv_parse
from project.npda.models import NPDAUser, Submission
from project.npda.models.organisation_employer import OrganisationEmployer
from project.npda.models.paediatric_diabetes_unit import PaediatricDiabetesUnit
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory
from project.npda.tests.UserDataClasses import (
    test_user_audit_centre_coordinator_data,
    test_user_audit_centre_editor_data,
    test_user_audit_centre_reader_data,
    test_user_rcpch_audit_team_data,
)
from project.npda.tests.utils import login_and_verify_user

logger = logging.getLogger(__name__)

ALDER_HEY_PZ_CODE = "PZ074"

GOSH_PZ_CODE = "PZ196"


@pytest.fixture
def valid_df(dummy_sheets_folder):
    file = dummy_sheets_folder / "dummy_sheet_test.csv"
    return csv_parse(file).df


@pytest.fixture(params=[2021, 2026])
def dataset_year(request):
    return request.param


@pytest.fixture
def audit_period_for_dataset_year(dataset_year):
    """Create an AuditPeriod for the supplied dataset_year for tests.

    Tests that need a matching audit period for the CSV can depend on this
    fixture and pass it into `csv_upload_sync` as `_audit_period`.
    """
    slug = f"{dataset_year}-{dataset_year + 1}"
    audit_period, _created = AuditPeriod.objects.get_or_create(
        slug=slug,
        defaults={
            "is_open": True,
            "is_visible": True,
            "start_date": date(dataset_year, 4, 1),
            "end_date": date(dataset_year + 1, 3, 31),
        },
    )

    # Ensure dates/visibility are set to expected values even if the object existed
    audit_period.is_open = True
    audit_period.is_visible = True
    audit_period.start_date = date(dataset_year, 4, 1)
    audit_period.end_date = date(dataset_year + 1, 3, 31)
    audit_period.save()

    return audit_period


def check_all_users_in_pdu(user, users, pz_code):
    for user in users:
        pz_codes = [org["pz_code"] for org in user.organisation_employers.values()]

        if not pz_code in pz_codes:
            pytest.fail(
                f"{user} in {pz_code} should not be able to see {user} in {pz_codes}"
            )


@pytest.mark.django_db
def test_npda_user_list_view_users_can_only_see_users_from_their_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """Except for RCPCH_AUDIT_TEAM, users should only see users from their own PDU."""

    ah_users = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    )
    # Check there are users from outside Alder Hey so this test doesn't pass by accident
    non_ah_users = NPDAUser.objects.exclude(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    )
    assert non_ah_users.count() > 0

    ah_user = ah_users.first()

    client = login_and_verify_user(client, ah_user)

    url = reverse("npda_users")
    response = client.get(url)

    assert response.status_code == HTTPStatus.OK

    users = response.context_data["object_list"]
    check_all_users_in_pdu(ah_user, users, ALDER_HEY_PZ_CODE)


@pytest.mark.django_db
def test_npda_user_list_view_rcpch_audit_team_can_view_all_users(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """RCPCH_AUDIT_TEAM users can view all users."""

    ah_users = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    )
    # Check there are users from outside Alder Hey so this test doesn't pass by accident
    non_ah_users = NPDAUser.objects.exclude(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    )
    assert non_ah_users.count() > 0

    ah_audit_team_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=RCPCH_AUDIT_TEAM,
    ).first()

    client = login_and_verify_user(client, ah_audit_team_user)

    response = client.get(reverse("npda_users"))
    assert response.status_code == HTTPStatus.OK

    users = response.context_data["object_list"]
    assert users.count() > ah_users.count()


@pytest.mark.django_db
def test_editor_can_upload_csv(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    dummy_sheets_folder,
):
    # create a test user with the editor role
    editor_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()
    client = login_and_verify_user(client, editor_user)
    # create a test CSV file

    file = dummy_sheets_folder / "dummy_sheet_test.csv"

    # upload the CSV file by posting to  'home' view
    url = reverse("home")
    with open(file, "rb") as f:
        response = client.post(
            url,
            {"csv_file": f},
            content_type="multipart/form-data",
        )
    # check the response status code
    assert response.status_code != HTTPStatus.FORBIDDEN
    # tricky test as it is hard to check the response as it is a redirect from an async call
    # this tests is really to check that the upload is not forbidden


@pytest.mark.django_db
def test_reader_cannot_upload_csv(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    dummy_sheets_folder,
):
    # create a test user with the editor role
    reader_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_reader_data.role,
    ).first()
    client = login_and_verify_user(client, reader_user)
    # create a test CSV file

    file = dummy_sheets_folder / "dummy_sheet_test.csv"

    # upload the CSV file by posting to  'home' view
    url = url = reverse(
        "pdu-upload-csv",
        kwargs={"pz_code": ALDER_HEY_PZ_CODE, "audit_period": "2025-2026"},
    )
    with open(file, "rb") as f:
        response = client.post(
            url,
            {"csv_file": f},
            content_type="multipart/form-data",
        )
    # check the response status code
    assert response.status_code == HTTPStatus.FORBIDDEN


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/906
@pytest.mark.django_db
def test_coordinators_cannot_change_their_role(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    user = NPDAUser.objects.filter(role=AUDIT_CENTRE_COORDINATOR).first()
    client = login_and_verify_user(client, user)

    url = reverse("npdauser-update", kwargs={"pk": user.pk})

    response = client.post(
        url,
        {
            "email": user.email,
            "first_name": user.first_name,
            "surname": user.surname,
            "role": RCPCH_AUDIT_TEAM,
        },
    )

    user.refresh_from_db()
    assert user.role == AUDIT_CENTRE_COORDINATOR

    assert user.groups.count() == 1
    assert user.groups.first().name == TRUST_AUDIT_TEAM_COORDINATOR_ACCESS


@pytest.mark.django_db
def test_coordinators_cannot_change_their_employer_htmx(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE, role=AUDIT_CENTRE_COORDINATOR
    ).first()

    client = login_and_verify_user(client, user)

    url = reverse("npdauser-update", kwargs={"pk": user.pk})

    response = client.post(
        url,
        data={
            "email": user.email,
            "first_name": user.first_name,
            "surname": user.surname,
            "add_employer": GOSH_PZ_CODE,
        },
        **{
            # Gated on request.htmx
            "HTTP_HX-Request": "true",
        },
    )

    user.refresh_from_db()
    employers = {e.pz_code for e in user.organisation_employers.all()}

    assert employers == {ALDER_HEY_PZ_CODE}


# Not actually used in the UI but possible to construct manually
@pytest.mark.django_db
def test_coordinators_cannot_change_their_employer_post(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE, role=AUDIT_CENTRE_COORDINATOR
    ).first()

    client = login_and_verify_user(client, user)

    url = reverse("npdauser-update", kwargs={"pk": user.pk})

    response = client.post(url, data={"add_employer": GOSH_PZ_CODE})

    user.refresh_from_db()
    employers = {e.pz_code for e in user.organisation_employers.all()}

    assert employers == {ALDER_HEY_PZ_CODE}


@pytest.mark.django_db
def test_coordinators_cannot_create_users_outside_of_their_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    user_count_before = NPDAUser.objects.count()

    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE, role=AUDIT_CENTRE_COORDINATOR
    ).first()

    client = login_and_verify_user(client, ah_user)

    url = reverse("npdauser-create")

    response = client.post(
        url,
        {
            "first_name": "Bob",
            "surname": "Bobertson",
            "email": "bob@bobertson.com",
            "role": AUDIT_CENTRE_COORDINATOR,
            "add_employer": GOSH_PZ_CODE,
        },
    )

    user_count_after = NPDAUser.objects.count()
    assert user_count_after == user_count_before


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/911
@pytest.mark.django_db
def test_audit_team_can_create_users_outside_of_their_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    user_count_before = NPDAUser.objects.count()

    audit_team_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE, role=RCPCH_AUDIT_TEAM
    ).first()

    client = login_and_verify_user(client, audit_team_user)

    url = reverse("npdauser-create")

    response = client.post(
        url,
        {
            "first_name": "Bob",
            "surname": "Bobertson",
            "email": "bob@bobertson.com",
            "role": AUDIT_CENTRE_COORDINATOR,
            "add_employer": GOSH_PZ_CODE,
        },
    )

    user_count_after = NPDAUser.objects.count()
    assert user_count_after == (user_count_before + 1)

    new_user = NPDAUser.objects.filter(email="bob@bobertson.com").first()

    assert new_user.organisation_employers.count() == 1
    assert new_user.organisation_employers.first().pz_code == GOSH_PZ_CODE


@pytest.mark.django_db
def test_coordinators_cannot_create_audit_team_members(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    user_count_before = NPDAUser.objects.count()

    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE, role=AUDIT_CENTRE_COORDINATOR
    ).first()

    client = login_and_verify_user(client, ah_user)

    url = reverse("npdauser-create")

    response = client.post(
        url,
        {
            "first_name": "Bob",
            "surname": "Bobertson",
            "email": "bob@bobertson.com",
            "role": RCPCH_AUDIT_TEAM,
        },
    )

    user_count_after = NPDAUser.objects.count()
    assert user_count_after == user_count_before


# These tests pass already before fixing https://github.com/rcpch/national-paediatric-diabetes-audit/issues/906
# as handled by the mixins but leaving them in for completeness sake.
@pytest.mark.django_db
@pytest.mark.parametrize("action", ["deactivate", "activate"])
def test_coordinators_cannot_activate_or_inactivate_users_outside_of_their_pdu(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client, action
):
    ah_coordinator = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE, role=AUDIT_CENTRE_COORDINATOR
    ).first()

    gosh_coordinator = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE, role=AUDIT_CENTRE_COORDINATOR
    ).first()

    # Set initial state based on action being tested
    if action == "deactivate":
        gosh_coordinator.is_active = True
    else:  # activate
        gosh_coordinator.is_active = False
    gosh_coordinator.save()

    initial_status = gosh_coordinator.is_active

    client = login_and_verify_user(client, ah_coordinator)

    url = reverse("npdauser-update", kwargs={"pk": gosh_coordinator.pk})

    response = client.post(url, data={action: "true"})

    assert response.status_code == HTTPStatus.FORBIDDEN
    gosh_coordinator.refresh_from_db()

    assert gosh_coordinator.is_active == initial_status


@pytest.mark.django_db
def test_coordinators_cannot_add_employers_outside_of_their_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    ah_coordinator = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE, role=AUDIT_CENTRE_COORDINATOR
    ).first()

    gosh_coordinator = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE, role=AUDIT_CENTRE_COORDINATOR
    ).first()

    client = login_and_verify_user(client, ah_coordinator)

    url = reverse("npdauser-update", kwargs={"pk": gosh_coordinator.pk})

    response = client.post(
        url,
        data={"add_employer": ALDER_HEY_PZ_CODE},
        **{
            # Gated on request.htmx
            "HTTP_HX-Request": "true",
        },
    )

    gosh_coordinator.refresh_from_db()
    employers = {e.pz_code for e in gosh_coordinator.organisation_employers.all()}

    assert employers == {GOSH_PZ_CODE}


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/911
@pytest.mark.django_db
def test_audit_team_can_add_employers_outside_of_their_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    audit_team_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE, role=RCPCH_AUDIT_TEAM
    ).first()

    ah_coordinator = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE, role=AUDIT_CENTRE_COORDINATOR
    ).first()

    client = login_and_verify_user(client, audit_team_user)

    url = reverse("npdauser-pdu-update", kwargs={"pk": ah_coordinator.pk})

    response = client.post(
        url,
        data={"add_employer": GOSH_PZ_CODE},
        **{
            # Gated on request.htmx
            "HTTP_HX-Request": "true",
        },
    )

    ah_coordinator.refresh_from_db()
    employers = {e.pz_code for e in ah_coordinator.organisation_employers.all()}

    assert employers == {ALDER_HEY_PZ_CODE, GOSH_PZ_CODE}

    VisitActivity = apps.get_model("npda", "VisitActivity")
    assert VisitActivity.objects.filter(
        npdauser=ah_coordinator,
        activity=15,  # Assigned to a new PDU
        npdauser_admin=audit_team_user,  # The user who made the change
    ).exists(), (
        "Expected a VisitActivity to be created when a coordinator tries to change their PDU."
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_flag",
    ["is_superuser", "is_staff", "is_rcpch_audit_team_member", "is_rcpch_staff"],
)
def test_coordinators_cannot_set_user_flags(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    user_flag,
):
    coordinator = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE, role=AUDIT_CENTRE_COORDINATOR
    ).first()

    assert getattr(coordinator, user_flag) is False

    client = login_and_verify_user(client, coordinator)

    url = reverse("npdauser-update", kwargs={"pk": coordinator.pk})

    data = {
        "add_employer": ALDER_HEY_PZ_CODE,
        "first_name": coordinator.first_name,
        "surname": coordinator.surname,
        "email": coordinator.email,
        "role": coordinator.role,
    }

    data[user_flag] = "on"

    client.post(url, data)

    coordinator.refresh_from_db()
    assert getattr(coordinator, user_flag) is False


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_flag",
    ["is_rcpch_audit_team_member", "is_rcpch_staff"],
)
def test_coordinators_cannot_create_users_with_superuser_flags(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    user_flag,
):
    user_count_before = NPDAUser.objects.count()

    coordinator = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE, role=AUDIT_CENTRE_COORDINATOR
    ).first()

    client = login_and_verify_user(client, coordinator)

    url = reverse("npdauser-create")

    data = {
        "first_name": "Bob",
        "surname": "Bobertson",
        "email": "bob@bobertson.com",
        "add_employer": ALDER_HEY_PZ_CODE,
        "role": AUDIT_CENTRE_COORDINATOR,
    }

    data[user_flag] = "on"

    client.post(url, data)

    user_count_after = NPDAUser.objects.count()
    assert user_count_after == user_count_before


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_flag",
    ["is_superuser", "is_staff"],
)
def test_coordinators_cannot_create_users_with_django_admin_flags(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    user_flag,
):
    coordinator = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE, role=AUDIT_CENTRE_COORDINATOR
    ).first()

    client = login_and_verify_user(client, coordinator)

    url = reverse("npdauser-create")

    data = {
        "first_name": "Bob",
        "surname": "Bobertson",
        "email": "bob@bobertson.com",
        "add_employer": ALDER_HEY_PZ_CODE,
        "role": AUDIT_CENTRE_COORDINATOR,
    }

    data[user_flag] = "on"

    client.post(url, data)

    user = NPDAUser.objects.get(email="bob@bobertson.com")
    assert getattr(user, user_flag) is False


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_data",
    [
        test_user_audit_centre_editor_data,
        test_user_audit_centre_coordinator_data,
        test_user_rcpch_audit_team_data,
    ],
)
def test_users_can_download_csv(
    client,
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    user_data,
):
    """Test that editor, coordinator, and RCPCH audit team users can download CSV files."""

    # Create a test user and log in
    test_user = NPDAUser.objects.filter(
        role=user_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    client = login_and_verify_user(client, test_user)

    (audit_start_date, _) = get_audit_period_for_date(timezone.now())

    # Create a test submission
    submission = Submission.objects.create(
        audit_year=audit_start_date.year,
        submission_date=timezone.now(),
        submission_active=True,
        submission_by=test_user,
        paediatric_diabetes_unit=test_user.organisation_employers.first(),
        csv_file=b"test_csv_data",
        csv_file_name="test_csv_file.csv",
        errors={},
    )

    Transfer = apps.get_model("npda.Transfer")
    patient = PatientFactory()
    # Update the transfer to match the user's PDU
    Transfer.objects.filter(patient=patient).update(
        paediatric_diabetes_unit=test_user.organisation_employers.first(),
    )
    submission.patients.add(patient)
    # Create a test visit for the patient
    VisitFactory(patient=patient)

    # Make a POST request to download the CSV file (HTMX)
    url = reverse(
        "pdu-submissions",
        kwargs={
            "pz_code": test_user.organisation_employers.first().pz_code,
            "audit_period": f"{audit_start_date.year}-{audit_start_date.year + 1}",
        },
    )

    response = client.post(
        url,
        {"submit-data": "download-data", "audit_id": submission.pk},
    )

    # Check that the response is successful and has the correct content type for a file download
    assert response.status_code == HTTPStatus.OK
    assert response.has_header("Content-Disposition")
    assert "attachment" in response["Content-Disposition"]
    assert "filename" in response["Content-Disposition"]
    assert response["Content-Type"] == "text/csv"


@pytest.mark.django_db
def test_reader_cannot_download_csv(
    client,
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
):
    """Test that the reader cannot download CSV files."""

    # Create a test user and log in
    editor_user = NPDAUser.objects.filter(
        role=test_user_audit_centre_reader_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    client = login_and_verify_user(client, editor_user)

    (audit_start_date, _) = get_audit_period_for_date(timezone.now())

    # Create a test submission
    submission = Submission.objects.create(
        audit_year=audit_start_date.year,
        submission_date=timezone.now(),
        submission_active=True,
        submission_by=editor_user,
        paediatric_diabetes_unit=editor_user.organisation_employers.first(),
        csv_file=b"test_csv_data",
        csv_file_name="test_csv_file.csv",
        errors={},
    )

    Transfer = apps.get_model("npda.Transfer")
    patient = PatientFactory()
    # Update the transfer to match the user's PDU
    Transfer.objects.filter(patient=patient).update(
        paediatric_diabetes_unit=editor_user.organisation_employers.first(),
    )
    submission.patients.add(patient)
    # Create a test visit for the patient
    VisitFactory(patient=patient)

    # Make a POST request to download the CSV file (HTMX)
    url = reverse(
        "pdu-submissions",
        kwargs={
            "pz_code": editor_user.organisation_employers.first().pz_code,
            "audit_period": f"{audit_start_date.year}-{audit_start_date.year + 1}",
        },
    )

    response = client.post(
        url,
        {"submit-data": "download-data", "audit_id": submission.pk},
    )

    # Check that the response is successful and has the correct content type for a file download
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_data",
    [
        test_user_audit_centre_editor_data,
        test_user_audit_centre_coordinator_data,
        test_user_rcpch_audit_team_data,
    ],
)
def test_users_can_download_report(
    client,
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    user_data,
    valid_df,
    dummy_sheet_csv,
    dataset_year,
):
    """Test that editor, coordinator, and RCPCH audit team users can download the validation report."""

    # Create a test user and log in
    test_user = NPDAUser.objects.filter(
        role=user_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    client = login_and_verify_user(client, test_user)

    (audit_start_date, _) = get_audit_period_for_date(timezone.now())

    # Create a test submission
    submission = Submission.objects.create(
        audit_year=audit_start_date.year,
        submission_date=timezone.now(),
        submission_active=True,
        submission_by=test_user,
        paediatric_diabetes_unit=test_user.organisation_employers.first(),
        csv_file=valid_df.to_csv(index=False).encode("utf-8"),
        csv_file_name="test_csv_file.csv",
        errors={},
    )

    Transfer = apps.get_model("npda.Transfer")
    patient = PatientFactory()
    # Update the transfer to match the user's PDU
    Transfer.objects.filter(patient=patient).update(
        paediatric_diabetes_unit=test_user.organisation_employers.first(),
    )
    submission.patients.add(patient)
    # Create a test visit for the patient
    VisitFactory(patient=patient)

    # Make a POST request to download the report (HTMX)
    url = reverse(
        "pdu-submissions",
        kwargs={
            "pz_code": test_user.organisation_employers.first().pz_code,
            "audit_period": f"{audit_start_date.year}-{audit_start_date.year + 1}",
        },
    )

    response = client.post(
        url,
        {"submit-data": "download-report", "audit_id": submission.pk},
    )

    # Check that the response is successful and has the correct content type for a file download (likely xlsx)
    assert response.status_code == HTTPStatus.OK
    assert response.has_header("Content-Disposition")
    assert "attachment" in response["Content-Disposition"]
    assert "filename" in response["Content-Disposition"]
    assert (
        response["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@pytest.mark.django_db
def test_rcpch_audit_team_can_delete_submission(
    client,
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    valid_df,
):
    """Test that RCPCH audit team members can delete submissions."""

    # Create a test RCPCH audit team user and log in
    audit_team_user = NPDAUser.objects.filter(
        role=test_user_rcpch_audit_team_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    client = login_and_verify_user(client, audit_team_user)

    (audit_start_date, _) = get_audit_period_for_date(timezone.now())

    # Create a test submission
    submission = Submission.objects.create(
        audit_year=audit_start_date.year,
        submission_date=timezone.now(),
        submission_active=False,  # cannot delete active submissions without first creating a new one
        submission_by=audit_team_user,
        paediatric_diabetes_unit=audit_team_user.organisation_employers.first(),
        csv_file=valid_df.to_csv(index=False).encode("utf-8"),
        csv_file_name="test_csv_file.csv",
        errors={},
    )

    Transfer = apps.get_model("npda.Transfer")
    patient = PatientFactory()
    # Update the transfer to match the user's PDU
    Transfer.objects.filter(patient=patient).update(
        paediatric_diabetes_unit=audit_team_user.organisation_employers.first(),
    )
    submission.patients.add(patient)
    # Create a test visit for the patient
    VisitFactory(patient=patient)

    # Make a POST request to delete the data (HTMX)
    url = reverse(
        "pdu-submissions",
        kwargs={
            "pz_code": audit_team_user.organisation_employers.first().pz_code,
            "audit_period": f"{audit_start_date.year}-{audit_start_date.year + 1}",
        },
    )

    response = client.post(
        url, {"submit-data": "delete-data", "audit_id": submission.pk}, follow=True
    )
    # Check that the deletion was successful (we expect a success message in the response)
    assert response.status_code == HTTPStatus.OK
    assert Submission.objects.filter(pk=submission.pk).count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_data",
    [
        test_user_audit_centre_editor_data,
        test_user_audit_centre_coordinator_data,
    ],
)
def test_non_rcpch_audit_team_cannot_delete_submission(
    client,
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    user_data,
    valid_df,
):
    """Test that editors and coordinators cannot delete submissions."""

    # Create a test user (editor or coordinator) and log in
    non_deleting_user = NPDAUser.objects.filter(
        role=user_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    client = login_and_verify_user(client, non_deleting_user)

    (audit_start_date, _) = get_audit_period_for_date(timezone.now())

    # Create a test submission
    submission = Submission.objects.create(
        audit_year=audit_start_date.year,
        submission_date=timezone.now(),
        submission_active=True,
        submission_by=non_deleting_user,
        paediatric_diabetes_unit=non_deleting_user.organisation_employers.first(),
        csv_file=valid_df.to_csv(index=False).encode("utf-8"),
        csv_file_name="test_csv_file.csv",
        errors={},
    )

    Transfer = apps.get_model("npda.Transfer")
    patient = PatientFactory()
    # Update the transfer to match the user's PDU
    Transfer.objects.filter(patient=patient).update(
        paediatric_diabetes_unit=non_deleting_user.organisation_employers.first(),
    )
    submission.patients.add(patient)
    # Create a test visit for the patient
    VisitFactory(patient=patient)

    # Make a POST request to delete the data (HTMX)
    url = reverse(
        "pdu-submissions",
        kwargs={
            "pz_code": non_deleting_user.organisation_employers.first().pz_code,
            "audit_period": f"{audit_start_date.year}-{audit_start_date.year + 1}",
        },
    )

    response = client.post(
        url,
        {"submit-data": "delete-data", "audit_id": submission.pk},
    )

    # Check that the deletion was NOT successful
    assert (
        response.status_code == HTTPStatus.FORBIDDEN
    )  # The view might re-render with an error
    assert Submission.objects.filter(pk=submission.pk).exists()


@pytest.mark.django_db
def test_users_cant_see_user_logs_for_different_pdus_users(
    client: Client,
    seed_groups_fixture,
    seed_users_fixture,
):
    """Test that users cannot see user logs for different PDU users."""

    # Create a test user
    test_user = NPDAUser.objects.filter(
        role=test_user_audit_centre_editor_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    # Create a test user for a different PDU
    different_pdu_user = NPDAUser.objects.filter(
        role=test_user_audit_centre_editor_data.role,
        organisation_employers__pz_code=GOSH_PZ_CODE,
    ).first()

    # Login user
    client = login_and_verify_user(client, test_user)

    # Make a GET request to the user logs page
    url = reverse("npdauser-logs", kwargs={"npdauser_id": different_pdu_user.pk})
    response = client.get(url)

    # Check that the response is forbidden
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_editors_and_readers_can_only_view_their_own_logs(
    client: Client,
    seed_groups_fixture,
    seed_users_fixture,
):
    """Test that editors and readers can only view their own logs."""

    # Create another user in same PDU
    another_user_same_pdu = NPDAUser.objects.filter(
        role=test_user_rcpch_audit_team_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()
    # Get another user in different PDU
    another_user_different_pdu = NPDAUser.objects.filter(
        role=test_user_audit_centre_reader_data.role,
        organisation_employers__pz_code=GOSH_PZ_CODE,
    ).first()

    # Get test users
    editor_user = NPDAUser.objects.filter(
        role=test_user_audit_centre_editor_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()
    reader_user = NPDAUser.objects.filter(
        role=test_user_audit_centre_reader_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()
    coordinator_user = NPDAUser.objects.filter(
        role=test_user_audit_centre_coordinator_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    for user in [editor_user, reader_user, coordinator_user]:
        # Login user
        client = login_and_verify_user(client, user)

        # Check they can see their own logs
        url = reverse("npdauser-logs", kwargs={"npdauser_id": user.pk})
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK, (
            f"User {user.first_name} ({user.organisation_employers.first().pz_code}) should be able to see their own logs"
        )

        # Make a GET request to the other user's logs
        # NOTE: though the test_users_cant_see_user_logs_for_different_pdus_users already checks that
        # the user cannot see logs for users in different PDUs, no harm in checking again
        for other_user in [another_user_same_pdu, another_user_different_pdu]:
            url = reverse("npdauser-logs", kwargs={"npdauser_id": other_user.pk})
            response = client.get(url)

            # Check that the response is forbidden
            # Coordinators CAN see other users' logs in their PDU
            if user.role == test_user_audit_centre_coordinator_data.role:
                if (
                    other_user.organisation_employers.first().pz_code
                    == user.organisation_employers.first().pz_code
                ):
                    assert response.status_code == HTTPStatus.OK, (
                        f"User {user.first_name} ({user.organisation_employers.first().pz_code}) should be able to see logs for user {other_user.first_name} ({other_user.organisation_employers.first().pz_code})"
                    )
                else:
                    assert response.status_code == HTTPStatus.FORBIDDEN, (
                        f"User {user.first_name} ({user.organisation_employers.first().pz_code}) should not be able to see logs for user {other_user.first_name} ({other_user.organisation_employers.first().pz_code})"
                    )
            else:
                # Readers and editors CANNOT see any other logs
                assert response.status_code == HTTPStatus.FORBIDDEN, (
                    f"User {user.first_name} ({user.organisation_employers.first().pz_code}) should not be able to see logs for user {other_user.first_name} ({other_user.organisation_employers.first().pz_code})"
                )

    # Also check the other users can see all logs
    rcpch_audit_team_user = NPDAUser.objects.filter(
        role=test_user_rcpch_audit_team_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    for user_should_see_all_logs in [
        rcpch_audit_team_user,
    ]:
        client = login_and_verify_user(client, user_should_see_all_logs)

        # Self
        url = reverse(
            "npdauser-logs", kwargs={"npdauser_id": user_should_see_all_logs.pk}
        )
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK, (
            f"User {user_should_see_all_logs.first_name} ({user_should_see_all_logs.organisation_employers.first().pz_code}) should be able to see their own logs"
        )

        # Other users in same PDU
        for other_user in [another_user_same_pdu, another_user_different_pdu]:
            url = reverse("npdauser-logs", kwargs={"npdauser_id": other_user.pk})
            response = client.get(url)
            assert response.status_code == HTTPStatus.OK, (
                f"User {user_should_see_all_logs.first_name} ({user_should_see_all_logs.organisation_employers.first().pz_code}) should be able to see logs for user {other_user.first_name} ({other_user.organisation_employers.first().pz_code})"
            )

        # Other users in different PDU
        for other_user in [another_user_different_pdu]:
            url = reverse("npdauser-logs", kwargs={"npdauser_id": other_user.pk})
            response = client.get(url)
            assert response.status_code == HTTPStatus.OK, (
                f"User {user_should_see_all_logs.first_name} ({user_should_see_all_logs.organisation_employers.first().pz_code}) should be able to see logs for user {other_user.first_name} ({other_user.organisation_employers.first().pz_code})"
            )


@pytest.mark.django_db
def test_coordinators_can_see_users_with_multiple_employers_if_in_same_pdu(
    client: Client,
    seed_groups_fixture,
    seed_users_fixture,
):
    """Test that coordinators can see users with multiple employers if they are in the same PDU."""

    # Create a test user
    test_coordinator = NPDAUser.objects.filter(
        role=test_user_audit_centre_coordinator_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    # Create a test user with multiple employers in the same PDU
    test_user_multiple_employers = NPDAUser.objects.filter(
        role=test_user_audit_centre_editor_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    GOSH = PaediatricDiabetesUnit.objects.get(pz_code=GOSH_PZ_CODE)
    # Add multiple employers to the test user
    OrganisationEmployer.objects.create(
        npda_user=test_user_multiple_employers,
        paediatric_diabetes_unit=GOSH,
        is_primary_employer=False,
    )

    # Login user
    client = login_and_verify_user(client, test_coordinator)

    # Make a GET request to the user logs page
    url = reverse(
        "npdauser-logs", kwargs={"npdauser_id": test_user_multiple_employers.pk}
    )
    response = client.get(url)

    # Check that the response is successful
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_coordinators_can_edit_users_with_multiple_employers_even_if_in_same_pdu(
    client: Client,
    seed_groups_fixture,
    seed_users_fixture,
):
    """Test that coordinators can see users with multiple employers if they are in the same PDU."""

    # Create a test user
    test_coordinator = NPDAUser.objects.filter(
        role=test_user_audit_centre_coordinator_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    # Create a test user with multiple employers in the same PDU
    test_user_multiple_employers = NPDAUser.objects.filter(
        role=test_user_audit_centre_editor_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    GOSH = PaediatricDiabetesUnit.objects.get(pz_code=GOSH_PZ_CODE)
    # Add multiple employers to the test user
    OrganisationEmployer.objects.create(
        npda_user=test_user_multiple_employers,
        paediatric_diabetes_unit=GOSH,
        is_primary_employer=False,
    )

    # Login user
    client = login_and_verify_user(client, test_coordinator)

    # Make a GET request to the user logs page
    url = reverse("npdauser-update", kwargs={"pk": test_user_multiple_employers.pk})
    response = client.get(url)

    # Check that the response is successful
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize("action", ["deactivate", "activate"])
def test_coordinators_cannot_activate_or_deactivate_users_with_multiple_employers_even_if_in_same_pdu(
    client: Client, seed_groups_fixture, seed_users_fixture, action
):
    """Test that coordinators cannot activate or deactivate users with multiple employers even if they are in the same PDU."""

    # Create a test user
    test_coordinator = NPDAUser.objects.filter(
        role=test_user_audit_centre_coordinator_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    # Create a test user with multiple employers in the same PDU
    test_user_multiple_employers = NPDAUser.objects.filter(
        role=test_user_audit_centre_editor_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    GOSH = PaediatricDiabetesUnit.objects.get(pz_code=GOSH_PZ_CODE)
    # Add multiple employers to the test user
    OrganisationEmployer.objects.create(
        npda_user=test_user_multiple_employers,
        paediatric_diabetes_unit=GOSH,
        is_primary_employer=False,
    )

    if action == "deactivate":
        test_user_multiple_employers.is_active = True
    else:  # activate
        test_user_multiple_employers.is_active = False
    test_user_multiple_employers.save()

    initial_status = test_user_multiple_employers.is_active

    assert test_user_multiple_employers.has_perm("npda.delete_npdauser") is False, (
        f"User {test_user_multiple_employers.first_name} ({test_user_multiple_employers.pz_code}) should not be able to change the active status of user {test_user_multiple_employers.first_name} ({test_user_multiple_employers.organisation_employers.first().pz_code})"
    )
    assert test_user_multiple_employers.organisation_employers.count() > 1, (
        f"User {test_user_multiple_employers.first_name} ({test_user_multiple_employers.pz_code}) should have multiple employers"
    )

    # Login user
    client = login_and_verify_user(client, test_coordinator)

    # Make a POST request to the user update url
    url = reverse("npdauser-update", kwargs={"pk": test_user_multiple_employers.pk})
    response = client.post(url, data={action: "true"})

    # Check that the response is successful
    assert response.status_code == HTTPStatus.FORBIDDEN

    test_user_multiple_employers.refresh_from_db()
    assert test_user_multiple_employers.is_active == initial_status, (
        f"User {test_user_multiple_employers.first_name} ({test_user_multiple_employers.pz_code}) should not be able to change the active status of user {test_user_multiple_employers.first_name} ({test_user_multiple_employers.organisation_employers.first().pz_code})"
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "initial_active, expected_active, action_label",
    [
        (True, False, "deactivate"),
        (False, True, "activate"),
    ],
)
def test_rcpch_audit_team_and_superusers_can_toggle_is_active_for_users_with_multiple_employers(
    client,
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    initial_active,
    expected_active,
    action_label,
):
    """
    RCPCH audit team and superusers should be able to activate or deactivate users with multiple employers.
    This test checks both activating and deactivating scenarios.
    """

    # Get an audit team member
    audit_team_member = NPDAUser.objects.filter(
        role=test_user_rcpch_audit_team_data.role,
    ).first()
    assert audit_team_member.organisation_employers.count() > 0

    # Get a user with multiple employers
    user = NPDAUser.objects.filter(
        role=test_user_audit_centre_editor_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()
    assert user.organisation_employers.count() > 0

    # Add a second employer
    gosh_pdu = PaediatricDiabetesUnit.objects.get(pz_code=GOSH_PZ_CODE)
    OrganisationEmployer.objects.create(
        npda_user=user,
        paediatric_diabetes_unit=gosh_pdu,
        is_primary_employer=False,
    )
    assert user.organisation_employers.count() > 1

    # Set initial is_active state
    user.is_active = initial_active
    user.save()

    # Login as audit team member
    client = login_and_verify_user(client, audit_team_member)

    # POST to update user
    url = reverse("npdauser-update", kwargs={"pk": user.pk})

    data = {
        "deactivate": "true",
        "first_name": user.first_name,
        "surname": user.surname,
        "email": user.email,
        "role": user.role,
    }

    data[action_label] = "true"

    response = client.post(url, data)

    # Should not be forbidden
    assert response.status_code != HTTPStatus.FORBIDDEN, (
        f"Audit team member should be able to {action_label} user {user.first_name}."
    )

    # Refresh and check outcome
    user.refresh_from_db()
    assert user.is_active == expected_active, (
        f"After {action_label}, user.is_active should be {expected_active} but got {user.is_active}."
    )


@pytest.mark.django_db
@pytest.mark.parametrize("action", ["deactivate", "activate"])
def test_coordinators_cannot_activate_or_deactivate_themselves(
    client: Client,
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    action,
):
    """Test that coordinators cannot activate or deactivate themselves."""

    test_coordinator = NPDAUser.objects.filter(
        role=test_user_audit_centre_coordinator_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    # ✅ Keep user active for login, regardless of test scenario
    test_coordinator.is_active = True
    test_coordinator.save()

    # Login while user is active
    client = login_and_verify_user(client, test_coordinator)
    url = reverse("npdauser-update", kwargs={"pk": test_coordinator.pk})
    response = client.post(url, data={action: "true"})
    assert response.status_code == HTTPStatus.FORBIDDEN
    test_coordinator.refresh_from_db()
    assert test_coordinator.is_active == True  # Should remain active


@pytest.mark.django_db
def test_coordinators_can_view_user_logs_with_multiple_employers_if_in_the_same_pdu(
    client: Client,
    seed_groups_fixture,
    seed_users_fixture,
):
    """Test that coordinators can see user logs with multiple employers if they are in the same PDU."""

    # Create a test user
    test_coordinator = NPDAUser.objects.filter(
        role=test_user_audit_centre_coordinator_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    # Create a test user with multiple employers in the same PDU
    test_user_multiple_employers = NPDAUser.objects.filter(
        role=test_user_audit_centre_editor_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    GOSH = PaediatricDiabetesUnit.objects.get(pz_code=GOSH_PZ_CODE)

    # Add multiple employers to the test user
    OrganisationEmployer.objects.create(
        npda_user=test_user_multiple_employers,
        paediatric_diabetes_unit=GOSH,
        is_primary_employer=False,
    )

    # Login user
    client = login_and_verify_user(client, test_coordinator)

    # Make a GET request to the user logs page
    url = reverse(
        "npdauser-logs", kwargs={"npdauser_id": test_user_multiple_employers.pk}
    )
    response = client.get(url)

    # Check that the response is successful
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_coordinators_with_multiple_employers_can_view_user_logs_with_multiple_employers_if_in_the_same_pdu(
    client: Client,
    seed_groups_fixture,
    seed_users_fixture,
):
    """Test that coordinators with multiple employers can see user logs with multiple employers if they are in the same PDU."""

    # Create a test user
    test_coordinator = NPDAUser.objects.filter(
        role=test_user_audit_centre_coordinator_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    # Create a test user with multiple employers in the same PDU
    test_user_multiple_employers = NPDAUser.objects.filter(
        role=test_user_audit_centre_editor_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    GOSH = PaediatricDiabetesUnit.objects.get(pz_code=GOSH_PZ_CODE)
    # Add multiple employers to the test user
    OrganisationEmployer.objects.create(
        npda_user=test_user_multiple_employers,
        paediatric_diabetes_unit=GOSH,
        is_primary_employer=False,
    )

    OrganisationEmployer.objects.create(
        npda_user=test_coordinator,
        paediatric_diabetes_unit=GOSH,
        is_primary_employer=False,
    )

    # Login user
    client = login_and_verify_user(client, test_coordinator)

    # Make a GET request to the user logs page
    url = reverse(
        "npdauser-logs", kwargs={"npdauser_id": test_user_multiple_employers.pk}
    )
    response = client.get(url)

    # Check that the response is successful
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_coordinators_with_multiple_employers_cannot_view_user_logs_with_multiple_employers_if_no_common_pdu(
    client: Client,
    seed_groups_fixture,
    seed_users_fixture,
):
    """Test that coordinators with multiple employers cannot see user logs with multiple employers if they are in different PDUs."""

    KINGS_COLLEGE = "PZ215"
    BCH_PZ_CODE = "PZ108"

    # Create a test coordinator with multiple employers in different PDUs from the user
    test_coordinator = NPDAUserFactory(
        role=test_user_audit_centre_coordinator_data.role,
        organisation_employers=[KINGS_COLLEGE, BCH_PZ_CODE],
    )
    OrganisationEmployer.objects.filter(
        npda_user=test_coordinator,
        paediatric_diabetes_unit__pz_code=KINGS_COLLEGE,
    ).update(is_primary_employer=False)  # can't have 2 primary employers

    # Create a test user with multiple employers
    test_user_multiple_employers = NPDAUser.objects.filter(
        role=test_user_audit_centre_editor_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    GOSH = PaediatricDiabetesUnit.objects.get(pz_code=GOSH_PZ_CODE)
    # Add multiple employers to the test user
    OrganisationEmployer.objects.create(
        npda_user=test_user_multiple_employers,
        paediatric_diabetes_unit=GOSH,
        is_primary_employer=False,
    )

    # Login user
    client = login_and_verify_user(client, test_coordinator)

    # Make a GET request to the user logs page
    url = reverse(
        "npdauser-logs", kwargs={"npdauser_id": test_user_multiple_employers.pk}
    )
    response = client.get(url)

    # Check that the response is successful
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_user_creation_has_a_timestamp_and_user(
    client: Client,
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
):
    """
    Test that user creation has a timestamp and user.
    Also checks that the VisitActivity is created for user creation.
    """

    # Create a test user
    test_user = NPDAUser.objects.filter(
        role=AUDIT_CENTRE_COORDINATOR,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    # Login user
    client = login_and_verify_user(client, test_user)

    # Create a new user
    url = reverse("npdauser-create")
    response = client.post(
        url,
        {
            "first_name": "Alice",
            "surname": "Smith",
            "email": "alice.smith@nhs.net",
            "role": AUDIT_CENTRE_COORDINATOR,
            "add_employer": ALDER_HEY_PZ_CODE,
        },
    )

    new_user = NPDAUser.objects.get(email="alice.smith@nhs.net")
    assert new_user.created_by == test_user
    assert new_user.created_at is not None
    assert (
        new_user.created_at <= timezone.now()
    )  # Ensure the timestamp is not in the future

    VisitActivity = apps.get_model("npda.VisitActivity")
    assert VisitActivity.objects.filter(
        npdauser=new_user,
        activity=10,  # User creation
    ).exists(), "VisitActivity should have been created for user creation"


@pytest.mark.django_db
def test_user_update_has_a_timestamp_and_user(
    client: Client,
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
):
    """Test that user creation has a timestamp and user."""

    # Create a test user
    test_user = NPDAUser.objects.filter(
        role=AUDIT_CENTRE_COORDINATOR,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    user_with_role = NPDAUser.objects.filter(
        role=AUDIT_CENTRE_READER,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    # Login user
    client = login_and_verify_user(client, test_user)

    # Create a new user
    url = reverse("npdauser-update", kwargs={"pk": user_with_role.pk})
    response = client.post(
        url,
        {
            "role": AUDIT_CENTRE_COORDINATOR,
            "surname": user_with_role.surname,  # Required fields
            "first_name": user_with_role.first_name,  # Required fields
            "email": user_with_role.email,  # Required fields
            "add_employer": ALDER_HEY_PZ_CODE,  # Required fields
        },
    )

    new_user = NPDAUser.objects.get(email=user_with_role.email)
    assert new_user.email == user_with_role.email
    assert new_user.role != AUDIT_CENTRE_READER  # Ensure the role has been updated
    assert new_user.updated_at is not None
    assert (
        new_user.updated_at <= timezone.now()
    )  # Ensure the timestamp is not in the future
    assert new_user.role == AUDIT_CENTRE_COORDINATOR

    VisitActivity = apps.get_model("npda.VisitActivity")
    assert VisitActivity.objects.filter(
        npdauser=new_user,
        activity=12,  # User role change
        npdauser_admin=test_user,  # The user who made the change
    ).exists(), "VisitActivity should have been created with new user role change"


@pytest.mark.django_db
def test_coordinator_cannot_change_email_for_user_with_multiple_pdus(
    client: Client,
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
):
    # Create a test coordinator in PZ999
    malicious_coordinator = NPDAUserFactory(
        first_name="Malicious",
        surname="Coordinator",
        role=AUDIT_CENTRE_COORDINATOR,
        is_active=True,
        is_staff=False,
        is_rcpch_audit_team_member=False,
        is_rcpch_staff=False,
        groups=[test_user_audit_centre_coordinator_data.group_name],
        organisation_employers=["PZ999"],
    )

    # Create a test reader in PZ999
    victim_reader = NPDAUserFactory(
        first_name="Victim",
        surname="Reader",
        role=AUDIT_CENTRE_READER,
        is_active=True,
        is_staff=False,
        is_rcpch_audit_team_member=False,
        is_rcpch_staff=False,
        groups=[test_user_audit_centre_reader_data.group_name],
        organisation_employers=["PZ999", "PZ001"],
    )

    # Login coordinator
    client = login_and_verify_user(client, malicious_coordinator)

    email_before = victim_reader.email

    url = reverse("npdauser-update", kwargs={"pk": victim_reader.pk})
    client.post(
        url,
        {
            "email": "malicious@actor.com",
            # Other required fields
            "role": victim_reader.role,
            "surname": victim_reader.surname,
            "first_name": victim_reader.first_name,
        },
    )

    victim_reader.refresh_from_db()

    assert victim_reader.email == email_before, (
        f"Malicious coordinator should not be able to change email of user in multiple PDUs."
    )


@pytest.mark.django_db
def test_coordinator_cannot_change_role_for_user_with_multiple_pdus(
    client: Client,
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
):
    # Create a test coordinator in PZ999
    malicious_coordinator = NPDAUserFactory(
        first_name="Malicious Coordinator",
        role=AUDIT_CENTRE_COORDINATOR,
        is_active=True,
        is_staff=False,
        is_rcpch_audit_team_member=False,
        is_rcpch_staff=False,
        groups=[test_user_audit_centre_coordinator_data.group_name],
        organisation_employers=["PZ999"],
    )

    # Create a test reader in PZ999
    victim_reader = NPDAUserFactory(
        first_name="Victim Reader",
        role=AUDIT_CENTRE_READER,
        is_active=True,
        is_staff=False,
        is_rcpch_audit_team_member=False,
        is_rcpch_staff=False,
        groups=[test_user_audit_centre_reader_data.group_name],
        organisation_employers=["PZ999", "PZ001"],
    )

    # Login coordinator
    client = login_and_verify_user(client, malicious_coordinator)

    email_before = victim_reader.email

    url = reverse("npdauser-update", kwargs={"pk": victim_reader.pk})
    client.post(
        url,
        {
            "role": AUDIT_CENTRE_COORDINATOR,
            # Other required fields
            "email": victim_reader.email,
            "surname": victim_reader.surname,
            "first_name": victim_reader.first_name,
        },
    )

    victim_reader.refresh_from_db()

    assert victim_reader.role == AUDIT_CENTRE_READER, (
        f"Malicious coordinator should not be able to change role of user in multiple PDUs."
    )
