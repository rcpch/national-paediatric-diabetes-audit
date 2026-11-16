import json
from http import HTTPStatus

import pytest
from dateutil.relativedelta import relativedelta
from django.urls import reverse

from project.npda.models.audit_period import AuditPeriod
from project.npda.models.npda_user import NPDAUser
from project.npda.models.transfer import Transfer
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.utils import create_submission, login_and_verify_user

GOSH_PZ_CODE = "PZ196"


@pytest.mark.django_db
def test_patients_in_transfer_are_marked_as_incomplete_year_of_care_in_patient_list(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    user = NPDAUser.objects.filter(organisation_employers__pz_code=GOSH_PZ_CODE).first()

    audit_period = AuditPeriod.objects.get_default_audit_period()
    sub = create_submission(audit_period, GOSH_PZ_CODE)

    diagnosed_outside_audit_year = PatientFactory(
        diagnosis_date=audit_period.start_date - relativedelta(days=2),
        is_valid=True,
    )
    sub.patients.add(diagnosed_outside_audit_year)

    diagnosed_in_audit_year = PatientFactory(
        diagnosis_date=audit_period.start_date + relativedelta(days=2),
        is_valid=True,
    )
    sub.patients.add(diagnosed_in_audit_year)

    transferred_in_audit_year = PatientFactory(
        is_valid=True,
    )
    sub.patients.add(transferred_in_audit_year)

    transfer = Transfer.objects.get(patient=transferred_in_audit_year)
    transfer.date_leaving_service = audit_period.start_date + relativedelta(days=2)
    transfer.reason_leaving_service = 1
    transfer.save()

    client = login_and_verify_user(client, user)

    response = client.get(
        reverse(
            "pdu-patients",
            kwargs={"audit_period": audit_period.slug, "pz_code": GOSH_PZ_CODE},
        )
    )
    assert response.status_code == HTTPStatus.OK

    patient_list = list(response.context["page_obj"])

    assert patient_list[0].is_first_valid
    assert patient_list[1].is_first_valid_incomplete_full_year

    expected_incomplete_patient_ids = {
        diagnosed_in_audit_year.id,
        transferred_in_audit_year.id,
    }
    actual_incomplete_patient_ids = {patient_list[1].id, patient_list[2].id}

    assert expected_incomplete_patient_ids == actual_incomplete_patient_ids


@pytest.mark.django_db
def test_fatal_csv_rows_flagged_in_patient_list_context(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """Rows with __fatal__ errors are converted to CSV row numbers and passed to the template."""
    user = NPDAUser.objects.filter(organisation_employers__pz_code=GOSH_PZ_CODE).first()

    audit_period = AuditPeriod.objects.get_default_audit_period()
    sub = create_submission(audit_period, GOSH_PZ_CODE)
    sub.errors = json.dumps(
        {
            "0": {"__fatal__": ["Error saving patient"]},
            "1": {"nhs_number": ["NHS number is invalid"]},
            "4": {"__fatal__": ["Error saving visit"]},
        }
    )
    sub.save()

    client = login_and_verify_user(client, user)

    response = client.get(
        reverse(
            "pdu-patients",
            kwargs={"audit_period": audit_period.slug, "pz_code": GOSH_PZ_CODE},
        )
    )
    assert response.status_code == HTTPStatus.OK

    # Only __fatal__ rows are included, converted to the 1-based CSV row
    # numbers used in the data quality report (0-based index + 2)
    assert response.context["fatal_error_csv_rows"] == [2, 6]

    # The alert copy is pluralised when multiple rows failed to save
    assert "check rows 2, 6" in response.content.decode()


@pytest.mark.django_db
def test_single_fatal_csv_row_alert_uses_singular_row(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """The alert reads "row" rather than "rows" when a single row failed to save."""
    user = NPDAUser.objects.filter(organisation_employers__pz_code=GOSH_PZ_CODE).first()

    audit_period = AuditPeriod.objects.get_default_audit_period()
    sub = create_submission(audit_period, GOSH_PZ_CODE)
    sub.errors = json.dumps({"3": {"__fatal__": ["Error saving patient"]}})
    sub.save()

    client = login_and_verify_user(client, user)

    response = client.get(
        reverse(
            "pdu-patients",
            kwargs={"audit_period": audit_period.slug, "pz_code": GOSH_PZ_CODE},
        )
    )
    assert response.status_code == HTTPStatus.OK

    assert response.context["fatal_error_csv_rows"] == [5]

    content = response.content.decode()
    assert "check row 5" in content
    assert "rows 5" not in content
