"""The Dashboard uses various methods that calculate metrics loosely based on KPIs.

These test those other methods."""

import logging
from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta
import pytest
from freezegun import freeze_time

from project.constants.albuminuria_stage import ALBUMINURIA_STAGES
from project.constants.hospital_admission_reasons import HOSPITAL_ADMISSION_REASONS
from project.constants.yes_no_unknown import YES_NO_UNKNOWN
from project.npda.kpi_class.kpis import CalculateKPIS, KPIResult
from project.npda.models import Patient
from project.npda.tests import utils
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.npda.tests.kpi_calculations.test_calculate_kpis import assert_kpi_result_equal

# Logging
logger = logging.getLogger(__name__)


@pytest.mark.django_db
def test_get_new_diagnoses_this_month(
    AUDIT_START_DATE,
    seed_groups_fixture,
    seed_users_fixture,
):
    """Tests that get_new_diagnoses_this_month returns correct count.

    Should only count patients diagnosed in the current month."""

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Freeze time to a specific date
    frozen_date = AUDIT_START_DATE + relativedelta(days=1) 
    current_month_start = date(frozen_date.year, frozen_date.month, 1)

    # Create 3 patients diagnosed within this month
    current_month_patients = PatientFactory.create_batch(
        size=3,
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        diagnosis_date=current_month_start + relativedelta(days=5),  # February 6, 2024
    )

    # Create 2 patients diagnosed last month
    last_month_patients = PatientFactory.create_batch(
        size=2,
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        diagnosis_date=current_month_start - relativedelta(days=5),  # January 27, 2024
    )

    # Create a submission (BEFORE calculating KPIs)
    submission = utils.create_submission(
        AUDIT_START_DATE,
        pz_code=current_month_patients[0]
        .paediatric_diabetes_units.first()
        .paediatric_diabetes_unit.pz_code,
    )
    submission.patients.add(*Patient.objects.all())

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    with freeze_time(frozen_date):
        calc_kpis = CalculateKPIS(calculation_date=AUDIT_START_DATE)
        calc_kpis.set_patients_for_calculation(pz_codes=["PZ130"])

        # Should only return count of patients diagnosed this month (February)
        assert calc_kpis.get_new_diagnoses_this_month() == 3


@pytest.mark.django_db
def test_get_new_admissions_this_month(
    AUDIT_START_DATE,
    seed_groups_fixture,
    seed_users_fixture,
):
    """Tests that get_new_admissions_this_month returns correct count.

    Should only count patients admitted to hospital in the current month."""

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Freeze time to a specific date
    frozen_date = AUDIT_START_DATE + relativedelta(days=1)
    current_month_start = date(frozen_date.year, frozen_date.month, 1)

    # Base criteria for eligible patients
    eligible_criteria = {
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
    }

    # Create passing patients with hospital admissions this month
    passing_valid_admission_reason_and_admission_within_audit_range = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # valid admission reason
        visit__hospital_admission_reason=HOSPITAL_ADMISSION_REASONS[0][0],
        # admission date within audit range
        visit__hospital_admission_date=current_month_start + relativedelta(days=2),
    )
    passing_valid_admission_reason_and_discharge_within_audit_range = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # valid admission reason
        visit__hospital_admission_reason=HOSPITAL_ADMISSION_REASONS[-1][0],
        # discharge date within audit range
        visit__hospital_discharge_date=current_month_start + relativedelta(days=2),
    )

    # Create failing pts
    failing_invalid_admission_reason = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # invalid admission reason
        visit__hospital_admission_reason="42",
        # admission date within audit range
        visit__hospital_admission_date=current_month_start + relativedelta(days=2),
    )
    failing_both_admission_outside_audit_date = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # valid admission reason
        visit__hospital_admission_reason=HOSPITAL_ADMISSION_REASONS[-1][0],
        # admission date outside audit range
        visit__hospital_admission_date=current_month_start - relativedelta(days=2),
    )

    # Create a submission (BEFORE calculating KPIs)
    submission = utils.create_submission(
        AUDIT_START_DATE,
        pz_code=passing_valid_admission_reason_and_admission_within_audit_range
        .paediatric_diabetes_units.first()
        .paediatric_diabetes_unit.pz_code,
    )
    submission.patients.add(*Patient.objects.all())

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    with freeze_time(frozen_date):
        calc_kpis = CalculateKPIS(calculation_date=AUDIT_START_DATE)
        calc_kpis.set_patients_for_calculation(pz_codes=["PZ130"])

        # should only return count of patients admitted this month
        assert calc_kpis.get_number_of_admissions_this_month() == 2
