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

import logging
from http import HTTPStatus

# Python imports
import pytest

# 3rd party imports
from django.apps import apps
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from project.constants.user import (
    AUDIT_CENTRE_COORDINATOR,
    RCPCH_AUDIT_TEAM,
    TRUST_AUDIT_TEAM_COORDINATOR_ACCESS,
)

# E12 imports
from project.npda.general_functions.audit_period import get_current_audit_year
from project.npda.general_functions.csv import csv_parse
from project.npda.models import NPDAUser, Submission, OrganisationEmployer, VisitActivity
from project.constants.user import (
    RCPCH_AUDIT_TEAM,
    AUDIT_CENTRE_COORDINATOR,
    TRUST_AUDIT_TEAM_COORDINATOR_ACCESS,
    AUDIT_CENTRE_READER
)
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory
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
    file = dummy_sheets_folder / "dummy_sheet.csv"
    return csv_parse(file).df


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

    # The user still defaults to seeing users from just their PDU
    # This is the request made when you click the "All" button on the switcher in the UI
    set_view_preference_response = client.post(
        reverse("view_preference"),
        {"view_preference": 2},
        headers={"HX-Request": "true"},
    )

    assert set_view_preference_response.status_code == HTTPStatus.NO_CONTENT

    response = client.get(reverse("npda_users"))
    assert response.status_code == HTTPStatus.OK

    users = response.context_data["object_list"]
    assert users.count() > ah_users.count()


@pytest.mark.django_db
def test_npda_user_list_view_users_cannot_switch_outside_their_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    client,
):
    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()
    client = login_and_verify_user(client, ah_user)

    set_view_preference_response = client.post(
        reverse("view_preference"),
        {"pz_code_select_name": GOSH_PZ_CODE},
        headers={"HX-Request": "true"},
    )

    assert set_view_preference_response.status_code == HTTPStatus.FORBIDDEN

    # Check the session isn't modified anyway
    response = client.get(reverse("npda_users"))
    assert response.status_code == HTTPStatus.OK

    users = response.context_data["object_list"]
    check_all_users_in_pdu(ah_user, users, ALDER_HEY_PZ_CODE)


@pytest.mark.django_db  # https://github.com/rcpch/national-paediatric-diabetes-audit/issues/189
def test_npda_user_list_view_normal_users_cannot_set_their_view_preference_to_national(
    seed_groups_fixture,
    seed_users_fixture,
    client,
):
    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()
    client = login_and_verify_user(client, ah_user)

    set_view_preference_response = client.post(
        reverse("view_preference"),
        {"view_preference": 2},
        headers={"HX-Request": "true"},
    )

    assert set_view_preference_response.status_code == HTTPStatus.FORBIDDEN

    # Check the session isn't modified anyway
    response = client.get(reverse("npda_users"))
    assert response.status_code == HTTPStatus.OK

    users = response.context_data["object_list"]
    check_all_users_in_pdu(ah_user, users, ALDER_HEY_PZ_CODE)


@pytest.mark.django_db
def test_npda_user_list_view_users_cannot_set_their_view_preference_to_organisation(
    seed_groups_fixture,
    seed_users_fixture,
    client,
):
    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    client = login_and_verify_user(client, ah_user)

    set_view_preference_response = client.post(
        reverse("view_preference"),
        {"view_preference": 0},
        headers={"HX-Request": "true"},
    )

    assert set_view_preference_response.status_code == HTTPStatus.BAD_REQUEST

    ah_user.refresh_from_db()
    assert ah_user.view_preference == 1

    # Check the session isn't modified anyway
    response = client.get(reverse("npda_users"))
    assert response.status_code == HTTPStatus.OK

    users = response.context_data["object_list"]
    check_all_users_in_pdu(ah_user, users, ALDER_HEY_PZ_CODE)


@pytest.mark.django_db
def test_editor_can_upload_csv(
    seed_groups_fixture, seed_users_fixture, client, dummy_sheets_folder
):
    # create a test user with the editor role
    editor_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()
    client = login_and_verify_user(client, editor_user)
    # create a test CSV file

    file = dummy_sheets_folder / "dummy_sheet.csv"

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
    seed_groups_fixture, seed_users_fixture, client, dummy_sheets_folder
):
    # create a test user with the editor role
    reader_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_reader_data.role,
    ).first()
    client = login_and_verify_user(client, reader_user)
    # create a test CSV file

    file = dummy_sheets_folder / "dummy_sheet.csv"

    # upload the CSV file by posting to  'home' view
    url = reverse("home")
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
# as handled by CheckPDUInstanceMixin but leaving them in for completeness sake.
@pytest.mark.django_db
def test_coordinators_cannot_delete_users_outside_of_their_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    client,
):
    user_count_before = NPDAUser.objects.count()

    ah_coordinator = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE, role=AUDIT_CENTRE_COORDINATOR
    ).first()

    gosh_coordinator = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE, role=AUDIT_CENTRE_COORDINATOR
    ).first()

    client = login_and_verify_user(client, ah_coordinator)

    url = reverse("npdauser-delete", kwargs={"pk": gosh_coordinator.pk})

    client.post(url)

    user_count_after = NPDAUser.objects.count()
    assert user_count_after == user_count_before


@pytest.mark.django_db
def test_coordinators_cannot_add_employers_outside_of_their_pdu(
    seed_groups_fixture,
    seed_users_fixture,
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
    client,
):
    audit_team_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE, role=RCPCH_AUDIT_TEAM
    ).first()

    ah_coordinator = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE, role=AUDIT_CENTRE_COORDINATOR
    ).first()

    client = login_and_verify_user(client, audit_team_user)

    url = reverse("npdauser-update", kwargs={"pk": ah_coordinator.pk})

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


    assert employers == { ALDER_HEY_PZ_CODE, GOSH_PZ_CODE }

# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/846
@pytest.mark.django_db
def test_coordinators_with_multiple_employers_can_update_users_in_all_of_them(
    seed_groups_fixture,
    seed_users_fixture,
    client,
):
    gosh_reader = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE,
        role=AUDIT_CENTRE_READER
    ).first()

    ah_coordinator = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=AUDIT_CENTRE_COORDINATOR
    ).first()

    ah_reader = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=AUDIT_CENTRE_READER
    ).first()

    # Add ah_coordinator to GOSH
    OrganisationEmployer.objects.create(
        npda_user=ah_coordinator,
        paediatric_diabetes_unit=gosh_reader.organisation_employers.first(),
        is_primary_employer=False
    )

    client = login_and_verify_user(client, ah_coordinator)

    url = reverse("npdauser-update", kwargs={ "pk": gosh_reader.pk })

    # Change name just to test permissions are ok
    response = client.post(url, data={
        "first_name": "Bob",
        "surname": "Bobertson",
        "email": gosh_reader.email,
        "role": AUDIT_CENTRE_READER,
    })

    gosh_reader.refresh_from_db()
    assert gosh_reader.first_name == "Bob"
    assert gosh_reader.surname == "Bobertson"

    url = reverse("npdauser-update", kwargs={ "pk": ah_reader.pk })

    # Change name just to test permissions are ok
    response = client.post(url, data={
        "first_name": "Bob",
        "surname": "Bobertson",
        "email": ah_reader.email,
        "role": AUDIT_CENTRE_READER,
    })

    ah_reader.refresh_from_db()
    assert ah_reader.first_name == "Bob"
    assert ah_reader.surname == "Bobertson"



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
    user_data,
):
    """Test that editor, coordinator, and RCPCH audit team users can download CSV files."""

    # Create a test user and log in
    test_user = NPDAUser.objects.filter(
        role=user_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    client = login_and_verify_user(client, test_user)

    # Create a test submission
    submission = Submission.objects.create(
        audit_year=get_current_audit_year(),
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
    url = reverse("submissions")
    response = client.post(
        url,
        {"submit-data": "download-data", "audit_id": submission.pk},
        headers={"HX-Request": "true"},  # Simulate HTMX request
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
):
    """Test that the reader cannot download CSV files."""

    # Create a test user and log in
    editor_user = NPDAUser.objects.filter(
        role=test_user_audit_centre_reader_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    client = login_and_verify_user(client, editor_user)

    # Create a test submission
    submission = Submission.objects.create(
        audit_year=get_current_audit_year(),
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
    url = reverse("submissions")
    response = client.post(
        url,
        {"submit-data": "download-data", "audit_id": submission.pk},
        headers={"HX-Request": "true"},  # Simulate HTMX request
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
    user_data,
    valid_df,
    dummy_sheet_csv,
):
    """Test that editor, coordinator, and RCPCH audit team users can download the validation report."""

    # Create a test user and log in
    test_user = NPDAUser.objects.filter(
        role=user_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    client = login_and_verify_user(client, test_user)

    # Create a test submission
    submission = Submission.objects.create(
        audit_year=get_current_audit_year(),
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
    url = reverse("submissions")
    response = client.post(
        url,
        {"submit-data": "download-report", "audit_id": submission.pk},
        headers={"HX-Request": "true"},  # Simulate HTMX request
    )

    # Check that the response is successful and has the correct content type for a file download (likely xlsx)
    assert response.status_code == HTTPStatus.OK
    assert response.has_header("Content-Disposition")
    assert "attachment" in response["Content-Disposition"]
    assert "filename" in response["Content-Disposition"]
    assert response["Content-Type"] == "text/csv"


@pytest.mark.django_db
def test_rcpch_audit_team_can_delete_submission(
    client,
    seed_groups_fixture,
    seed_users_fixture,
    valid_df,
):
    """Test that RCPCH audit team members can delete submissions."""

    # Create a test RCPCH audit team user and log in
    audit_team_user = NPDAUser.objects.filter(
        role=test_user_rcpch_audit_team_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    client = login_and_verify_user(client, audit_team_user)

    # Create a test submission
    submission = Submission.objects.create(
        audit_year=get_current_audit_year(),
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
    url = reverse("submissions")
    response = client.post(
        url,
        {"submit-data": "delete-data", "audit_id": submission.pk},
        headers={"HX-Request": "true"},  # Simulate HTMX request
        follow=True,
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

    # Create a test submission
    submission = Submission.objects.create(
        audit_year=get_current_audit_year(),
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
    url = reverse("submissions")
    response = client.post(
        url,
        {"submit-data": "delete-data", "audit_id": submission.pk},
        headers={"HX-Request": "true"},  # Simulate HTMX request
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
