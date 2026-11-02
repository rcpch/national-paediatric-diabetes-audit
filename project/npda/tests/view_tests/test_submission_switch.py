"""Tests for the switch-to-questionnaire and switch-to-csv POST actions of
`SubmissionsListView`.

Only RCPCH audit team members and superusers may switch a submission between
questionnaire and CSV upload. These tests ensure that:

- normal (non audit team, non superuser) users are denied (403) for both switch
  actions, and the submission is left untouched
- audit team members can switch a CSV submission to a questionnaire submission
  (clearing `csv_file_name`/`csv_file`) and a questionnaire submission to a CSV
  submission (setting a dummy `csv_file_name`/`csv_file`)
- switching a submission that is already in the target state is refused with an
  error message and a redirect back to the submissions list
- audit team members can switch submissions for PDUs they are not employed at
"""

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from project.npda.models import AuditPeriod, NPDAUser, Submission
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory
from project.npda.tests.model_tests.test_submissions import GOSH_PZ_CODE
from project.npda.tests.UserDataClasses import (
    AUDIT_CENTRE_COORDINATOR,
    AUDIT_CENTRE_EDITOR,
    AUDIT_CENTRE_READER,
    RCPCH_AUDIT_TEAM,
)
from project.npda.tests.utils import create_submission, login_and_verify_user

SWITCH_TO_QUESTIONNAIRE = "switch-to-questionnaire"
SWITCH_TO_CSV = "switch-to-csv"

SWITCH_ACTIONS = [SWITCH_TO_QUESTIONNAIRE, SWITCH_TO_CSV]

CSV_FILE_NAME = "test_switch.csv"
CSV_FILE_CONTENTS = b"npda,csv,contents"

# Filename assigned by the view when switching a questionnaire submission to CSV
DUMMY_CSV_FILE_NAME = "dummy_csv_to_switch_from_questionnaire_to_csv_upload.csv"

# Roles that are not audit team members or superusers
NON_AUDIT_TEAM_ROLES = [
    AUDIT_CENTRE_EDITOR,
    AUDIT_CENTRE_COORDINATOR,
    AUDIT_CENTRE_READER,
]


def submissions_url(pz_code: str, audit_period: AuditPeriod) -> str:
    return reverse(
        "pdu-submissions",
        kwargs={"audit_period": audit_period.slug, "pz_code": pz_code},
    )


def patients_url(pz_code: str, audit_period: AuditPeriod) -> str:
    return reverse(
        "pdu-patients",
        kwargs={"audit_period": audit_period.slug, "pz_code": pz_code},
    )


def post_switch(
    client, action: str, submission: Submission, pz_code: str, audit_period
):
    return client.post(
        submissions_url(pz_code, audit_period),
        {"submit-data": action, "audit_id": submission.id},
    )


def flash_message_texts(response) -> list[str]:
    return [str(message) for message in get_messages(response.wsgi_request)]


@pytest.mark.parametrize("role", NON_AUDIT_TEAM_ROLES)
@pytest.mark.django_db
def test_normal_user_cannot_switch_csv_submission_to_questionnaire(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client, role
):
    """Normal users cannot switch a CSV submission to a questionnaire submission."""
    audit_period = AuditPeriod.objects.get_default_audit_period()
    submission = create_submission(
        audit_period,
        pz_code=ALDER_HEY_PZ_CODE,
        csv_file_name=CSV_FILE_NAME,
        csv_file=CSV_FILE_CONTENTS,
    )

    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=role,
    ).first()
    client = login_and_verify_user(client, ah_user)

    response = post_switch(
        client, SWITCH_TO_QUESTIONNAIRE, submission, ALDER_HEY_PZ_CODE, audit_period
    )

    assert response.status_code == 403

    # The submission is untouched
    submission.refresh_from_db()
    assert submission.csv_file_name == CSV_FILE_NAME
    assert bytes(submission.csv_file) == CSV_FILE_CONTENTS


@pytest.mark.parametrize("role", NON_AUDIT_TEAM_ROLES)
@pytest.mark.django_db
def test_normal_user_cannot_switch_questionnaire_submission_to_csv(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client, role
):
    """Normal users cannot switch a questionnaire submission to a CSV submission."""
    audit_period = AuditPeriod.objects.get_default_audit_period()
    submission = create_submission(audit_period, pz_code=ALDER_HEY_PZ_CODE)

    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=role,
    ).first()
    client = login_and_verify_user(client, ah_user)

    response = post_switch(
        client, SWITCH_TO_CSV, submission, ALDER_HEY_PZ_CODE, audit_period
    )

    assert response.status_code == 403

    # The submission is untouched
    submission.refresh_from_db()
    assert submission.csv_file_name is None
    assert submission.csv_file is None


@pytest.mark.parametrize("action", SWITCH_ACTIONS)
@pytest.mark.django_db
def test_normal_user_cannot_switch_submission_for_another_pdu(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client, action
):
    """Normal users cannot switch submissions belonging to a PDU they are not employed at."""
    audit_period = AuditPeriod.objects.get_default_audit_period()
    gosh_submission = create_submission(
        audit_period,
        pz_code=GOSH_PZ_CODE,
        csv_file_name=CSV_FILE_NAME,
        csv_file=CSV_FILE_CONTENTS,
    )

    ah_editor = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=AUDIT_CENTRE_EDITOR,
    ).first()
    client = login_and_verify_user(client, ah_editor)

    response = post_switch(client, action, gosh_submission, GOSH_PZ_CODE, audit_period)

    assert response.status_code == 403

    # The submission is untouched
    gosh_submission.refresh_from_db()
    assert gosh_submission.csv_file_name == CSV_FILE_NAME
    assert bytes(gosh_submission.csv_file) == CSV_FILE_CONTENTS


@pytest.mark.django_db
def test_audit_team_member_can_switch_csv_submission_to_questionnaire(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client
):
    """Audit team members can switch a CSV submission to a questionnaire submission."""
    audit_period = AuditPeriod.objects.get_default_audit_period()
    submission = create_submission(
        audit_period,
        pz_code=ALDER_HEY_PZ_CODE,
        csv_file_name=CSV_FILE_NAME,
        csv_file=CSV_FILE_CONTENTS,
    )

    audit_team_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=RCPCH_AUDIT_TEAM,
    ).first()
    client = login_and_verify_user(client, audit_team_user)

    response = post_switch(
        client, SWITCH_TO_QUESTIONNAIRE, submission, ALDER_HEY_PZ_CODE, audit_period
    )

    assert response.status_code == 302
    assert response.url == patients_url(ALDER_HEY_PZ_CODE, audit_period)

    # The CSV file has been cleared
    submission.refresh_from_db()
    assert submission.csv_file_name is None
    assert submission.csv_file is None

    assert "Submission switched to questionnaire successfully." in flash_message_texts(
        response
    )


@pytest.mark.django_db
def test_audit_team_member_cannot_switch_questionnaire_submission_to_questionnaire(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client
):
    """Switching a submission that is already a questionnaire submission is refused."""
    audit_period = AuditPeriod.objects.get_default_audit_period()
    submission = create_submission(audit_period, pz_code=ALDER_HEY_PZ_CODE)

    audit_team_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=RCPCH_AUDIT_TEAM,
    ).first()
    client = login_and_verify_user(client, audit_team_user)

    response = post_switch(
        client, SWITCH_TO_QUESTIONNAIRE, submission, ALDER_HEY_PZ_CODE, audit_period
    )

    # Refused with an error message, redirected back to the submissions list
    assert response.status_code == 302
    assert response.url == submissions_url(ALDER_HEY_PZ_CODE, audit_period)
    assert (
        "This submission is already a questionnaire submission."
        in flash_message_texts(response)
    )

    # The submission is untouched
    submission.refresh_from_db()
    assert submission.csv_file_name is None
    assert submission.csv_file is None


@pytest.mark.django_db
def test_audit_team_member_can_switch_questionnaire_submission_to_csv(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client
):
    """Audit team members can switch a questionnaire submission to a CSV submission."""
    audit_period = AuditPeriod.objects.get_default_audit_period()
    submission = create_submission(audit_period, pz_code=ALDER_HEY_PZ_CODE)

    audit_team_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=RCPCH_AUDIT_TEAM,
    ).first()
    client = login_and_verify_user(client, audit_team_user)

    response = post_switch(
        client, SWITCH_TO_CSV, submission, ALDER_HEY_PZ_CODE, audit_period
    )

    assert response.status_code == 302
    assert response.url == patients_url(ALDER_HEY_PZ_CODE, audit_period)

    # The dummy CSV file details have been set
    submission.refresh_from_db()
    assert submission.csv_file_name == DUMMY_CSV_FILE_NAME
    assert bytes(submission.csv_file) == (
        f"This is a dummy CSV file to switch {ALDER_HEY_PZ_CODE} from questionnaire to CSV upload".encode()
    )

    assert "Submission switched to CSV successfully." in flash_message_texts(response)


@pytest.mark.django_db
def test_audit_team_member_cannot_switch_csv_submission_to_csv(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client
):
    """Switching a submission that is already a CSV submission is refused."""
    audit_period = AuditPeriod.objects.get_default_audit_period()
    submission = create_submission(
        audit_period,
        pz_code=ALDER_HEY_PZ_CODE,
        csv_file_name=CSV_FILE_NAME,
        csv_file=CSV_FILE_CONTENTS,
    )

    audit_team_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=RCPCH_AUDIT_TEAM,
    ).first()
    client = login_and_verify_user(client, audit_team_user)

    response = post_switch(
        client, SWITCH_TO_CSV, submission, ALDER_HEY_PZ_CODE, audit_period
    )

    # Refused with an error message, redirected back to the submissions list
    assert response.status_code == 302
    assert response.url == submissions_url(ALDER_HEY_PZ_CODE, audit_period)
    assert "This submission is already a CSV submission." in flash_message_texts(
        response
    )

    # The submission is untouched
    submission.refresh_from_db()
    assert submission.csv_file_name == CSV_FILE_NAME
    assert bytes(submission.csv_file) == CSV_FILE_CONTENTS


@pytest.mark.parametrize("action", SWITCH_ACTIONS)
@pytest.mark.django_db
def test_audit_team_member_can_switch_submission_for_another_pdu(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client, action
):
    """Audit team members can switch submissions for PDUs they are not employed at."""
    audit_period = AuditPeriod.objects.get_default_audit_period()
    # switch-to-questionnaire starts from a CSV submission,
    # switch-to-csv starts from a questionnaire submission
    csv_file_name = CSV_FILE_NAME if action == SWITCH_TO_QUESTIONNAIRE else None
    gosh_submission = create_submission(
        audit_period,
        pz_code=GOSH_PZ_CODE,
        csv_file_name=csv_file_name,
        csv_file=CSV_FILE_CONTENTS if csv_file_name else None,
    )

    ah_audit_team_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=RCPCH_AUDIT_TEAM,
    ).first()
    client = login_and_verify_user(client, ah_audit_team_user)

    response = post_switch(client, action, gosh_submission, GOSH_PZ_CODE, audit_period)

    # Both switches succeed for a PDU the audit team member is not employed at
    assert response.status_code == 302
    assert response.url == patients_url(GOSH_PZ_CODE, audit_period)

    gosh_submission.refresh_from_db()
    match action:
        case "switch-to-questionnaire":
            assert gosh_submission.csv_file_name is None
            assert gosh_submission.csv_file is None
        case "switch-to-csv":
            assert gosh_submission.csv_file_name == DUMMY_CSV_FILE_NAME


@pytest.mark.parametrize("action", SWITCH_ACTIONS)
@pytest.mark.django_db
def test_superuser_can_switch_submission(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client, action
):
    """Superusers can switch submissions in both directions."""
    audit_period = AuditPeriod.objects.get_default_audit_period()
    # switch-to-questionnaire starts from a CSV submission,
    # switch-to-csv starts from a questionnaire submission
    csv_file_name = CSV_FILE_NAME if action == SWITCH_TO_QUESTIONNAIRE else None
    submission = create_submission(
        audit_period,
        pz_code=ALDER_HEY_PZ_CODE,
        csv_file_name=csv_file_name,
        csv_file=CSV_FILE_CONTENTS if csv_file_name else None,
    )

    superuser = NPDAUserFactory(
        first_name="switch",
        surname="superuser",
        role=RCPCH_AUDIT_TEAM,
        is_superuser=True,
        organisation_employers=[ALDER_HEY_PZ_CODE],
    )
    client = login_and_verify_user(client, superuser)

    response = post_switch(client, action, submission, ALDER_HEY_PZ_CODE, audit_period)

    assert response.status_code == 302
    assert response.url == patients_url(ALDER_HEY_PZ_CODE, audit_period)

    submission.refresh_from_db()
    match action:
        case "switch-to-questionnaire":
            assert submission.csv_file_name is None
            assert submission.csv_file is None
        case "switch-to-csv":
            assert submission.csv_file_name == DUMMY_CSV_FILE_NAME
