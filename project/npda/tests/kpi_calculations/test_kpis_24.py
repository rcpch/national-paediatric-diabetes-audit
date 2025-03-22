"""Tests for the HCL KPI."""

import pytest
from dateutil.relativedelta import relativedelta

from project.npda.kpi_class.kpis import CalculateKPIS, KPIResult
from project.npda.models import Patient
from project.npda.tests import utils
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.npda.tests.kpi_calculations.test_calculate_kpis import \
    assert_kpi_result_equal


@pytest.mark.django_db
def test_kpi_calculation_24(AUDIT_START_DATE):
    """Tests that KPI24 is calculated correctly.

    Denominator: Total number of eligible patients (measure 1)

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is either
        * 3 = insulin pump
        * or 6 = Insulin pump therapy plus other blood glucose lowering medication

        AND whose most recent entry for item 21 (based on visit date) is either
        * 2 = Closed loop system (licenced)
        * or 3 = Closed loop system (DIY, unlicenced)
        * or 4 = Closed loop system (licence status unknown)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible (KPI1)
    eligible_criteria = {
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
    }
    for treatment_val in (3, 6):

        # Now create the passing patients
        passing_closed_loop_2 = PatientFactory(
            postcode=f"passing_closed_loop_2_{treatment_val}",
            # KPI1 eligible
            **eligible_criteria,
            # KPI24 eligible
            visit__treatment=treatment_val,
            # 2 = Closed loop system (licenced)
            visit__closed_loop_system=2,
        )
        passing_closed_loop_3 = PatientFactory(
            postcode=f"passing_closed_loop_2_{treatment_val}",
            # KPI1 eligible
            **eligible_criteria,
            # KPI24 eligible
            visit__treatment=treatment_val,
            # 3 = Closed loop system (DIY, unlicenced)
            visit__closed_loop_system=3,
        )
        passing_closed_loop_4 = PatientFactory(
            postcode=f"passing_closed_loop_2_{treatment_val}",
            # KPI1 eligible
            **eligible_criteria,
            # KPI24 eligible
            visit__treatment=treatment_val,
            # 4 = Closed loop system (licence status unknown)
            visit__closed_loop_system=4,
        )

        # Failing patients
        # A 'failing' pt who has pump therapy but not closed loop system
        failing_closed_loop = PatientFactory(
            postcode=f"failing_closed_loop_{treatment_val}",
            # KPI1 eligible
            **eligible_criteria,
            # KPI24 eligible
            visit__treatment=treatment_val,
            # AND whose most recent entry for item 21 (based on visit date) is NOT
            # either [2,3,4]
            visit__closed_loop_system=1,
        )

    # Create Patients and Visits that should be ineligble
    # Visit date before audit period
    ineligible_patient_visit_date = PatientFactory(
        postcode="ineligible_patient_visit_date",
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
        visit__treatment=1,
    )
    # Above age 25 at start of audit period
    ineligible_patient_too_old = PatientFactory(
        postcode="ineligible_patient_too_old",
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
        visit__treatment=1,
    )

    # KPI24 specific
    # tx regimen not 3 or 6
    for treatment_val in (1, 2, 4, 5, 7, 8):
        ineligible_tx_regimen = PatientFactory(
            postcode=f"ineligible_tx_regimen_{treatment_val}",
            # KPI1 eligible
            **eligible_criteria,
            # ineligible tx regimen
            visit__treatment=treatment_val,
        )

    # Create a submission (BEFORE calculating KPIs)
    submission = utils.create_submission(
        AUDIT_START_DATE,
        pz_code=ineligible_patient_visit_date.paediatric_diabetes_units.first().paediatric_diabetes_unit.pz_code,
    )
    submission.patients.add(*Patient.objects.all())

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(calculation_date=AUDIT_START_DATE)
    calc_kpis.set_patients_for_calculation(
        pz_codes=[
            ineligible_patient_visit_date.paediatric_diabetes_units.first().paediatric_diabetes_unit.pz_code
        ]
    )

    EXPECTED_TOTAL_ELIGIBLE = 8
    EXPECTED_TOTAL_INELIGIBLE = 8
    EXPECTED_TOTAL_PASSED = 6
    EXPECTED_TOTAL_FAILED = 2

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_PASSED,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_FAILED,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_24_hybrid_closed_loop_system(),
    )


# Edge case found as part of https://github.com/rcpch/national-paediatric-diabetes-audit/issues/797
@pytest.mark.django_db
def test_kpi_calculation_24_for_patients_who_have_come_off_hcl(AUDIT_START_DATE):
    first_visit_date = AUDIT_START_DATE + relativedelta(days=2)

    patient = PatientFactory(
        visit__visit_date=first_visit_date,
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        visit__treatment=3,
        visit__closed_loop_system=2,
    )

    calc_kpis = CalculateKPIS(calculation_date=AUDIT_START_DATE)
    calc_kpis.set_patients_for_calculation(Patient.objects.filter(pk__in=[patient.pk]))

    first_result = calc_kpis.calculate_kpi_24_hybrid_closed_loop_system()
    assert first_result.total_passed == 1

    # Add a more recent visit where they are back on injections
    second_visit_date = first_visit_date + relativedelta(months=3)

    VisitFactory(
        patient=patient,
        visit_date=second_visit_date,
        treatment=1
    )

    second_result = calc_kpis.calculate_kpi_24_hybrid_closed_loop_system()
    assert second_result.total_passed == 0