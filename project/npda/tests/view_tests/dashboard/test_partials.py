"""Tests for the unit report view"""

from decimal import Decimal
from http import HTTPStatus

# Python imports
import pytest

# 3rd party imports
from django.urls import reverse

# E12 imports
from project.npda.models import NPDAUser
from project.npda.models.audit_period import AuditPeriod
from project.npda.models.patient import Patient
from project.npda.models.submission import Submission
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.factories import (
    test_user_audit_centre_editor_data
)
from project.npda.tests.utils import login_and_verify_user
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.constants.diabetes_types import DIABETES_TYPES
from project.constants.hba1c_format import HBA1C_FORMATS
from project.constants.leave_pdu_reasons import LEAVE_PDU_REASONS
from dateutil.relativedelta import relativedelta


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1156
@pytest.mark.django_db
def test_count_of_patients_transitioning_to_adult_care_does_not_include_other_transfers(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get_default_audit_period()
    audit_period.is_open = True
    audit_period.save()

    date_of_birth = audit_period.start_date - relativedelta(years=11, days=2)

    patient = PatientFactory(
        nhs_number="4444444444",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date - relativedelta(days=2), # complete year of care
        transfer__date_leaving_service=audit_period.start_date + relativedelta(days=2),
        transfer__reason_leaving_service=LEAVE_PDU_REASONS[1][0] # Moved out of area
    )

    # Need a visit in the audit period to be eligible
    VisitFactory(
        patient=patient,
        visit_date=audit_period.start_date + relativedelta(days=10),
        hba1c=60,  # 60 mmol/mol
        hba1c_format=HBA1C_FORMATS[0][0],  # mmol/mol format
        hba1c_date=audit_period.start_date + relativedelta(days=10),
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    response = client.get(reverse("get_transitioned_to_adult_service_partial"))
    assert response.status_code == HTTPStatus.OK

    assert response.context["number"] == 0
