"""Tests for the patient report view"""

from decimal import Decimal
from http import HTTPStatus

# Python imports
from django.test import override_settings
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
from project.npda.views.patient_report.patient_report import TableCategories
from dateutil.relativedelta import relativedelta


@pytest.mark.django_db
@override_settings(SECURE_SSL_REDIRECT=False)
def test_measurements_for_patients_turning_12_in_audit_year(
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

    response = client.get(reverse("pdu-patient-measurements", kwargs={
        "audit_period": audit_period.slug,
        "pz_code": ALDER_HEY_PZ_CODE
    }))
    assert response.status_code == HTTPStatus.OK

    assert response.context["total_eligible_blood_pressure"] == 0
    assert response.context["total_eligible_urinary_albumin"] == 0
    assert response.context["total_eligible_foot_exam"] == 0
