"""Tests for the Treatment Regimen KPIS."""

import pytest
from dateutil.relativedelta import relativedelta

from project.constants.diabetes_treatment import TREATMENT_TYPES
from project.npda.kpi_class.kpis import CalculateKPIS, KPIResult
from project.npda.models import Patient
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.kpi_calculations.test_calculate_kpis import (
    assert_kpi_result_equal,
)

# Set up test params for kpis 13-20, as they all have the same denominator
# and the only thing being changed is value for visit__treatment
# the final option (9 - unknown) is not a KPI calculation so excluded
TX_TYPE_PARAMS = []
for treatment_type in TREATMENT_TYPES[:-1]:
    expected_result = KPIResult(
        total_eligible=8,
        total_passed=1,
        total_ineligible=2,
        total_failed=7,
    )
    TX_TYPE_PARAMS.append((treatment_type[0], expected_result))


@pytest.mark.parametrize(("treatment", "expected_result"), TX_TYPE_PARAMS)
@pytest.mark.django_db
def test_kpi_calculations_13_to_20(
    AUDIT_START_DATE, treatment: int, expected_result: KPIResult
):
    """Tests that KPIS13-20 are calculated correctly.

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is `treatment` (int 1-9)

    Denominator: Total number of eligible patients (measure 1)
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be eligible
    eligible_criteria = {
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
    }
    passing = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # most recent observation for treatment regimen (item 20) is `treatment`
        visit__treatment=treatment,
    )

    # TODO: query are these 'failing' or just 'not passing'?
    # Create failing patients (remember exclude final option 9 - unknown)
    for val, _ in TREATMENT_TYPES[:-1]:
        if val != treatment:

            failing = PatientFactory(
                # KPI1 eligible
                **eligible_criteria,
                # most recent observation for treatment regimen (item 20) is NOT `treatment`
                visit__treatment=val,
            )

    # Create Patients and Visits that should be excluded
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

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(calculation_date=AUDIT_START_DATE)
    # Need to be mocked as not using public `calculate_kpis_for_*` methods
    calc_kpis.patients = Patient.objects.all()
    calc_kpis.total_patients_count = Patient.objects.count()

    # Dynamically get the kpi calc method based on treatment type
    #   `treatment` is an int between 1-8
    #   these kpi calulations start at 13
    #   so just offset by 12 to get kpi number
    kpi_number = treatment + 12
    kpi_method_name = calc_kpis.kpi_name_registry.get_attribute_name(kpi_number)
    kpi_calc_method = getattr(calc_kpis, f"calculate_{kpi_method_name}")
    assert_kpi_result_equal(
        expected=expected_result,
        actual=kpi_calc_method(),
    )
