"""Tests for the CalculateKPIS class."""

from datetime import date
from dateutil.relativedelta import relativedelta
from dataclasses import fields
import logging
from typing import List
import pytest

from project.constants.diabetes_types import DIABETES_TYPES
from project.npda.general_functions.kpis import CalculateKPIS, KPIResult
from project.npda.general_functions.model_utils import print_instance_field_attrs
from project.npda.models import Patient, Visit
from project.npda.tests.factories.patient_factory import PatientFactory

# Logging
logger = logging.getLogger(__name__)


# HELPERS
def assert_kpi_result_equal(expected: KPIResult, actual: KPIResult) -> None:
    """
    Asserts that two KPIResult objects are equal by comparing their fields and provides
    a detailed error message if they are not.

    :param expected: The expected KPIResult object.
    :param actual: The actual KPIResult object.
    :raises AssertionError: If the fields in the KPIResult objects differ.
    """
    if isinstance(expected, KPIResult) is False:
        raise TypeError(
            f"expected must be of type KPIResult (current: {type(expected)}"
        )
    if isinstance(actual, KPIResult) is False:
        raise TypeError(f"actual must be of type KPIResult (current: {type(actual)}")

    mismatches = []

    if expected.total_eligible != actual.total_eligible:
        mismatches.append(
            f"total_eligible: expected {expected.total_eligible}, got {actual.total_eligible}"
        )

    if expected.total_passed != actual.total_passed:
        mismatches.append(
            f"total_passed: expected {expected.total_passed}, got {actual.total_passed}"
        )

    if expected.total_ineligible != actual.total_ineligible:
        mismatches.append(
            f"total_ineligible: expected {expected.total_ineligible}, got {actual.total_ineligible}"
        )

    if expected.total_failed != actual.total_failed:
        mismatches.append(
            f"total_failed: expected {expected.total_failed}, got {actual.total_failed}"
        )

    if mismatches:
        mismatch_details = "\n".join(mismatches)
        raise AssertionError(f"KPIResult mismatch:\n{mismatch_details}")


@pytest.fixture
def AUDIT_START_DATE():
    """AUDIT_START_DATE is Day 2 of the first audit period"""
    return date(year=2024, month=4, day=1)


@pytest.mark.django_db
def test_ensure_mocked_audit_date_range_is_correct(AUDIT_START_DATE):
    """Ensure that the mocked audit date range is correct."""
    calc_kpis = CalculateKPIS(
        pz_code="mocked_pz_code", calculation_date=AUDIT_START_DATE
    )

    assert calc_kpis.audit_start_date == date(
        2024, 4, 1
    ), f"Mocked audit start date incorrect!"
    assert calc_kpis.audit_end_date == date(
        2025, 3, 31
    ), f"Mocked audit end date incorrect!"


@pytest.mark.django_db
def test_kpi_calculation_1(AUDIT_START_DATE):
    """Tests that KPI1 is calculated correctly."""

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    N_PATIENTS_ELIGIBLE = N_PATIENTS_PASS = 3
    N_PATIENTS_INELIGIBLE = N_PATIENTS_FAIL = 4

    # Create  Patients and Visits that should PASS KPI1
    eligible_patients: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_ELIGIBLE,
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=1),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
    )

    # Create Patients and Visits that should FAIL KPI1
    # Visit date before audit period
    ineligible_patients_visit_date: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patients_too_old: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(pz_code="PZ130", calculation_date=AUDIT_START_DATE)

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=N_PATIENTS_ELIGIBLE,
        total_passed=N_PATIENTS_PASS,
        # We have 2 sets of ineligible patients
        total_ineligible=N_PATIENTS_INELIGIBLE * 2,
        total_failed=N_PATIENTS_FAIL * 2,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT, actual=calc_kpis.calculate_kpi_1_total_eligible()
    )


@pytest.mark.django_db
def test_kpi_calculation_2(AUDIT_START_DATE):
    """Tests that KPI2 is calculated correctly.

    Essentialy KPI1 but also check date of diagnosis within audit period
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    N_PATIENTS_ELIGIBLE = N_PATIENTS_PASS = 3
    N_PATIENTS_INELIGIBLE = N_PATIENTS_FAIL = 4

    # Create  Patients and Visits that should PASS KPI2
    eligible_patients: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_ELIGIBLE,
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        diagnosis_date=AUDIT_START_DATE + relativedelta(days=10),
    )

    # Create Patients and Visits that should FAIL KPI2
    # Visit date before audit period
    ineligible_patients_visit_date: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Diagnosis date before audit period
    ineligible_patients_diagnosis_date: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        diagnosis_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patients_too_old: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(pz_code="PZ130", calculation_date=AUDIT_START_DATE)

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=N_PATIENTS_ELIGIBLE,
        total_passed=N_PATIENTS_PASS,
        # We have 3 sets of ineligible patients
        total_ineligible=N_PATIENTS_INELIGIBLE * 3,
        total_failed=N_PATIENTS_FAIL * 3,
    )

    # First set kpi1 result of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_2_total_new_diagnoses(),
    )


@pytest.mark.django_db
def test_kpi_calculation_3(AUDIT_START_DATE):
    """Tests that KPI3 is calculated correctly.

    Essentialy KPI1 but also check Diagnosis of Type 1 diabetes
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    N_PATIENTS_ELIGIBLE = N_PATIENTS_PASS = 3
    N_PATIENTS_INELIGIBLE = N_PATIENTS_FAIL = 4

    # Create  Patients and Visits that should PASS KPI3
    eligible_patients: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_ELIGIBLE,
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # T1DM
        diabetes_type=DIABETES_TYPES[0][0],
    )

    # Create Patients and Visits that should FAIL KPI3
    # Visit date before audit period
    ineligible_patients_visit_date: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patients_too_old: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )
    # Diab type is not T1DM before audit period
    ineligible_patients_diab_type: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE, diabetes_type=DIABETES_TYPES[-1][0]
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(pz_code="PZ130", calculation_date=AUDIT_START_DATE)

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=N_PATIENTS_ELIGIBLE,
        total_passed=N_PATIENTS_PASS,
        # We have 3 sets of ineligible patients
        total_ineligible=N_PATIENTS_INELIGIBLE * 3,
        total_failed=N_PATIENTS_FAIL * 3,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_3_total_t1dm(),
    )


@pytest.mark.django_db
def test_kpi_calculation_4(AUDIT_START_DATE):
    """Tests that KPI4 is calculated correctly.

    Essentialy KPI1 but also check
        Age 12 and above years at the start of the audit period
        & Diagnosis of Type 1 diabetes
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    N_PATIENTS_ELIGIBLE = N_PATIENTS_PASS = 3
    N_PATIENTS_INELIGIBLE = N_PATIENTS_FAIL = 4

    # Create  Patients and Visits that should PASS KPI4
    eligible_patients: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_ELIGIBLE,
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        # T1DM
        diabetes_type=DIABETES_TYPES[0][0],
        # 12 years old exactly at start of audit period
        date_of_birth=AUDIT_START_DATE - relativedelta(years=12),
    )

    # Create Patients and Visits that should FAIL KPI4
    # Visit date before audit period
    ineligible_patients_visit_date: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patients_too_old: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        date_of_birth=AUDIT_START_DATE - relativedelta(years=26),
    )
    # Diab type is not T1DM before audit period
    ineligible_patients_diab_type: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE, diabetes_type=DIABETES_TYPES[-1][0]
    )
    # age 1day less than 12yo at start of audit period
    ineligible_patients_lt_12yo: List[Patient] = PatientFactory.create_batch(
        size=N_PATIENTS_INELIGIBLE,
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 11),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(pz_code="PZ130", calculation_date=AUDIT_START_DATE)

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=N_PATIENTS_ELIGIBLE,
        total_passed=N_PATIENTS_PASS,
        # We have 4 sets of ineligible patients
        total_ineligible=N_PATIENTS_INELIGIBLE * 4,
        total_failed=N_PATIENTS_FAIL * 4,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_4_total_t1dm_gte_12yo(),
    )


@pytest.mark.django_db
def test_kpi_calculation_5(AUDIT_START_DATE):
    """Tests that KPI5 is calculated correctly.

    Essentialy KPI1 but also check

        Excluding
        * Date of diagnosis within the audit period
        * Date of leaving service within the audit period
        * Date of death within the audit period"
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be included
    eligible_patient_diag_NOT_within_audit_period = PatientFactory(
        postcode="eligible_patient_diag_NOT_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of diagnosis within the audit period
        diagnosis_date=AUDIT_START_DATE - relativedelta(days=2),
    )

    eligible_patient_date_leaving_NOT_within_audit_period = PatientFactory(
        postcode="eligible_patient_date_leaving_NOT_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of leaving service within the audit period
        # transfer date only not None if they have left
        transfer__date_leaving_service=None,
    )

    eligible_patient_death_NOT_within_audit_period = PatientFactory(
        postcode="eligible_patient_death_NOT_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=None,
    )

    # Create Patients and Visits that should FAIL KPI3
    # Visit date before audit period
    ineligible_patient_visit_date: List[Patient] = PatientFactory(
        postcode="ineligible_patient_visit_date",
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patient_too_old: List[Patient] = PatientFactory(
        postcode="ineligible_patient_too_old",
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )

    # KPI5 specific
    ineligible_patient_diag_within_audit_period = PatientFactory(
        postcode="ineligible_patient_diag_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of diagnosis within the audit period
        diagnosis_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_date_leaving_within_audit_period = PatientFactory(
        postcode="ineligible_patient_date_leaving_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of leaving service within the audit period
        transfer__date_leaving_service=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_death_within_audit_period = PatientFactory(
        postcode="ineligible_patient_death_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(pz_code="PZ130", calculation_date=AUDIT_START_DATE)

    EXPECTED_TOTAL_ELIGIBLE = 3
    EXPECTED_TOTAL_INELIGIBLE = 5

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_ELIGIBLE,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_INELIGIBLE,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_5_total_t1dm_complete_year(),
    )


@pytest.mark.django_db
def test_kpi_calculation_6(AUDIT_START_DATE):
    """Tests that KPI6 is calculated correctly.

    Inclusions:
        * Age 12 and above at the start of the audit period
        * Diagnosis of Type 1 diabetes
        * an observation within the audit period

    Essentialy KPI5 exclusions:
        Excluding
        * Date of diagnosis within the audit period
        * Date of leaving service within the audit period
        * Date of death within the audit period"
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should PASS KPI3
    observation_field_names = [
        "height_weight_observation_date",
        "hba1c_date",
        "blood_pressure_observation_date",
        "albumin_creatinine_ratio_date",
        "total_cholesterol_date",
        "thyroid_function_date",
        "coeliac_screen_date",
        "psychological_screening_assessment_date",
    ]
    # Loop through each observation field name and create a patient with an
    # observation date within the audit period for that field
    for field_name in observation_field_names:
        eligible_patient_pt_obs = PatientFactory(
            # string field without validation, just using for debugging
            # postcode=f"eligible_patient_{field_name}",
            # KPI1 eligible
            # Age 12 and above at the start of the audit period
            date_of_birth=AUDIT_START_DATE - relativedelta(years=12),
            # Diagnosis of Type 1 diabetes
            diabetes_type=DIABETES_TYPES[0][0],
            # an observation within the audit period
            **{f"visit__{field_name}": AUDIT_START_DATE + relativedelta(days=2)},
        )

    # Create Patients and Visits that should FAIL KPI3
    ineligible_patient_diag_within_audit_period = PatientFactory(
        postcode="ineligible_patient_diag_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of diagnosis within the audit period
        diagnosis_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_date_leaving_within_audit_period = PatientFactory(
        postcode="ineligible_patient_date_leaving_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of leaving service within the audit period
        transfer__date_leaving_service=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_death_within_audit_period = PatientFactory(
        postcode="ineligible_patient_death_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death within the audit period"
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(pz_code="PZ130", calculation_date=AUDIT_START_DATE)

    EXPECTED_TOTAL_ELIGIBLE = len(observation_field_names)
    EXPECTED_TOTAL_INELIGIBLE = 3

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_ELIGIBLE,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_INELIGIBLE,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_6_total_t1dm_complete_year_gte_12yo(),
    )


@pytest.mark.django_db
def test_kpi_calculation_7(AUDIT_START_DATE):
    """Tests that KPI7 is calculated correctly.

    Total number of patients with:
        * a valid NHS number
        * an observation within the audit period
        * Age 0-24 years at the start of the audit period
        * Diagnosis of Type 1 diabetes
        * Date of diagnosis within the audit period
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    observation_field_names = [
        "height_weight_observation_date",
        "hba1c_date",
        "blood_pressure_observation_date",
        "albumin_creatinine_ratio_date",
        "total_cholesterol_date",
        "thyroid_function_date",
        "coeliac_screen_date",
        "psychological_screening_assessment_date",
    ]
    # Loop through each observation field name and create a patient with an
    # observation date within the audit period for that field
    for field_name in observation_field_names:
        eligible_patient_pt_obs = PatientFactory(
            # string field without validation, just using for debugging
            postcode=f"eligible_patient_{field_name}",
            # KPI1 eligible
            # Age 12 and above at the start of the audit period
            date_of_birth=AUDIT_START_DATE - relativedelta(years=12),
            # Diagnosis of Type 1 diabetes
            diabetes_type=DIABETES_TYPES[0][0],
            # Diagnosis date within audit date range
            diagnosis_date=AUDIT_START_DATE + relativedelta(days=2),
            # an observation within the audit period
            **{f"visit__{field_name}": AUDIT_START_DATE + relativedelta(days=2)},
        )

    # Create Patients and Visits that should BE EXCLUDED
    ineligible_patient_not_t1dm = PatientFactory(
        postcode="ineligible_patient_not_t1dm",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # T1DM
        diabetes_type=DIABETES_TYPES[1][0],
        # Date of diagnosis inside the audit period
        diagnosis_date=AUDIT_START_DATE + relativedelta(days=2),
    )
    ineligible_patient_diag_outside_audit_period = PatientFactory(
        postcode="ineligible_patient_diag_outside_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # T1DM
        diabetes_type=DIABETES_TYPES[0][0],
        # Date of diagnosis outside the audit period
        diagnosis_date=AUDIT_START_DATE - relativedelta(days=2),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(pz_code="PZ130", calculation_date=AUDIT_START_DATE)
    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    EXPECTED_TOTAL_ELIGIBLE = len(observation_field_names)
    EXPECTED_TOTAL_INELIGIBLE = 2

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_ELIGIBLE,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_INELIGIBLE,
    )

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_7_total_new_diagnoses_t1dm(),
    )


@pytest.mark.django_db
def test_kpi_calculation_8(AUDIT_START_DATE):
    """Tests that KPI8 is calculated correctly.

    Essentialy KPI1 but also check
        * Date of death within the audit period"
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be included
    eligible_patient_death_within_audit_period = PatientFactory(
        postcode="eligible_patient_diag_NOT_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # death_date within the audit period
        death_date=AUDIT_START_DATE + relativedelta(days=2),
    )

    # Create Patients and Visits that should be excluded
    # Visit date before audit period
    ineligible_patient_visit_date: List[Patient] = PatientFactory(
        postcode="ineligible_patient_visit_date",
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patient_too_old: List[Patient] = PatientFactory(
        postcode="ineligible_patient_too_old",
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )

    # KPI8 specific
    ineligible_patient_death_outside_audit_period = PatientFactory(
        postcode="ineligible_patient_death_outside_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of death outside the audit period"
        death_date=AUDIT_START_DATE - relativedelta(days=2),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(pz_code="PZ130", calculation_date=AUDIT_START_DATE)

    EXPECTED_TOTAL_ELIGIBLE = 1
    EXPECTED_TOTAL_INELIGIBLE = 3

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_ELIGIBLE,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_INELIGIBLE,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_8_total_deaths(),
    )


@pytest.mark.django_db
def test_kpi_calculation_9(AUDIT_START_DATE):
    """Tests that KPI9 is calculated correctly.

    Essentialy KPI1 but also check
        * Date of death within the audit period"
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be included
    eligible_patient_leaving_date_within_audit_period = PatientFactory(
        postcode="eligible_patient_diag_NOT_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # leaving_date within the audit period
        transfer__date_leaving_service=AUDIT_START_DATE + relativedelta(days=2),
    )

    # Create Patients and Visits that should be excluded
    # Visit date before audit period
    ineligible_patient_visit_date: List[Patient] = PatientFactory(
        postcode="ineligible_patient_visit_date",
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patient_too_old: List[Patient] = PatientFactory(
        postcode="ineligible_patient_too_old",
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )

    # KPI9 specific
    ineligible_patient_no_leaving_date = PatientFactory(
        postcode="ineligible_patient_no_leaving_date",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # has not left
        transfer__date_leaving_service=None,
    )
    ineligible_patient_leaving_date_outside_audit_period = PatientFactory(
        postcode="ineligible_patient_leaving_date_outside_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # Date of leaving_date outside the audit period"
        transfer__date_leaving_service=AUDIT_START_DATE - relativedelta(days=2),
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(pz_code="PZ130", calculation_date=AUDIT_START_DATE)

    EXPECTED_TOTAL_ELIGIBLE = 1
    EXPECTED_TOTAL_INELIGIBLE = 4

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_ELIGIBLE,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_INELIGIBLE,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_9_total_service_transitions(),
    )


@pytest.mark.django_db
def test_kpi_calculation_10(AUDIT_START_DATE):
    """Tests that KPI10 is calculated correctly.

    Essentialy KPI1 but also check
        * most recent observation for item 37 (based on visit date) is 1 = Yes
        // NOTE: item37 is _Has the patient been recommended a Gluten-free diet?_
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be included
    eligible_patient_most_recent_gluten_free_diet_is_1 = PatientFactory(
        postcode="eligible_patient_diag_NOT_within_audit_period",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # most recent observation for item 37 (based on visit date) is 1 = Yes
        visit__gluten_free_diet=1,
    )

    # Create Patients and Visits that should be excluded
    # Visit date before audit period
    ineligible_patient_visit_date: List[Patient] = PatientFactory(
        postcode="ineligible_patient_visit_date",
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patient_too_old: List[Patient] = PatientFactory(
        postcode="ineligible_patient_too_old",
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )

    # KPI10 specific
    ineligible_patient_most_recent_additional_dietitian_appt_offerred_is_not_1 = PatientFactory(
        postcode="ineligible_patient_most_recent_additional_dietitian_appt_offerred_is_not_1",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # most recent observation for item 37 (based on visit date) is not 1
        visit__gluten_free_diet=2,
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(pz_code="PZ130", calculation_date=AUDIT_START_DATE)

    EXPECTED_TOTAL_ELIGIBLE = 1
    EXPECTED_TOTAL_INELIGIBLE = 3

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_ELIGIBLE,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_INELIGIBLE,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_10_total_coeliacs(),
    )


@pytest.mark.django_db
def test_kpi_calculation_11(AUDIT_START_DATE):
    """Tests that KPI11 is calculated correctly.

    KPI1 PLUS
    who:
        * most recent observation for item 35 (based on visit date) is either 2 = Thyroxine for hypothyroidism or 3 = Antithyroid medication for hyperthyroidism
        // NOTE: item35 is _At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?_
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be included
    eligible_patient_most_recent_thyroid_treatment_status_is_2 = PatientFactory(
        postcode="eligible_patient_most_recent_thyroid_treatment_status_is_2",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # most recent observation for item 35 (based on visit date) is 2
        visit__thyroid_treatment_status=2,
    )
    eligible_patient_most_recent_thyroid_treatment_status_is_3 = PatientFactory(
        postcode="eligible_patient_most_recent_thyroid_treatment_status_is_3",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # most recent observation for item 35 (based on visit date) is 2
        visit__thyroid_treatment_status=3,
    )

    # Create Patients and Visits that should be excluded
    # Visit date before audit period
    ineligible_patient_visit_date: List[Patient] = PatientFactory(
        postcode="ineligible_patient_visit_date",
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patient_too_old: List[Patient] = PatientFactory(
        postcode="ineligible_patient_too_old",
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )

    # KPI11 specific
    ineligible_patient_most_recent_thyroid_treatment_status_is_not_in_range_2_to_3 = PatientFactory(
        postcode="ineligible_patient_most_recent_thyroid_treatment_status_is_not_in_range_2_to_3",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # most recent observation for item 37 (based on visit date) is not 1
        visit__thyroid_treatment_status=1,
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(pz_code="PZ130", calculation_date=AUDIT_START_DATE)

    EXPECTED_TOTAL_ELIGIBLE = 2
    EXPECTED_TOTAL_INELIGIBLE = 3

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_ELIGIBLE,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_INELIGIBLE,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_11_total_thyroids(),
    )


@pytest.mark.django_db
def test_kpi_calculation_12(AUDIT_START_DATE):
    """Tests that KPI12 is calculated correctly.

    KPI1 PLUS
        * most recent observation for item 45 (based on visit date) is 1 = Yes
            // NOTE: item45 is _Was the patient using (or trained to use) blood ketone testing equipment at time of visit? _
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should be included
    eligible_patient_most_recent_ketone_meter_training_is_1 = PatientFactory(
        postcode="eligible_patient_most_recent_ketone_meter_training_is_1",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # most recent observation for item 45 (based on visit date) is 1 = Yes
        visit__ketone_meter_training=1,
    )

    # Create Patients and Visits that should be excluded
    # Visit date before audit period
    ineligible_patient_visit_date: List[Patient] = PatientFactory(
        postcode="ineligible_patient_visit_date",
        visit__visit_date=AUDIT_START_DATE - relativedelta(days=10),
    )
    # Above age 25 at start of audit period
    ineligible_patient_too_old: List[Patient] = PatientFactory(
        postcode="ineligible_patient_too_old",
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 26),
    )

    # KPI11 specific
    ineligible_patient_most_recent_ketone_meter_training_is_not_1 = PatientFactory(
        postcode="ineligible_patient_most_recent_ketone_meter_training_is_not_1",
        # KPI1 eligible
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=2),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        # most recent observation for item 37 (based on visit date) is not 1
        visit__ketone_meter_training=2,
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(pz_code="PZ130", calculation_date=AUDIT_START_DATE)

    EXPECTED_TOTAL_ELIGIBLE = 1
    EXPECTED_TOTAL_INELIGIBLE = 3

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_ELIGIBLE,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_INELIGIBLE,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_12_total_ketone_test_equipment(),
    )


@pytest.mark.django_db
def test_kpi_calculation_13(AUDIT_START_DATE):
    """Tests that KPI13 is calculated correctly.

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is 1 = One-three injections/day

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
        # most recent observation for item 20 (based on visit date) is 1 = One-three injections/day
        visit__treatment=1,
    )
    failling = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # most recent observation for item 20 (based on visit date) is not 1 = One-three injections/day
        visit__treatment=2,
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
    calc_kpis = CalculateKPIS(pz_code="PZ130", calculation_date=AUDIT_START_DATE)

    EXPECTED_TOTAL_ELIGIBLE = 2
    EXPECTED_TOTAL_INELIGIBLE = 2
    EXPECTED_TOTAL_PASSED = 1
    EXPECTED_TOTAL_FAILED = 1

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_PASSED,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_FAILED,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_13_one_to_three_injections_per_day(),
    )


@pytest.mark.django_db
def test_kpi_calculation_14(AUDIT_START_DATE):
    """Tests that KPI14 is calculated correctly.

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is 2 = Four or more injections/day

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
        # most recent observation for item 20 (based on visit date) is 1 = One-three injections/day
        visit__treatment=2,
    )
    failling = PatientFactory(
        # KPI1 eligible
        **eligible_criteria,
        # most recent observation for item 20 (based on visit date) is not 1 = One-three injections/day
        visit__treatment=1,
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
    calc_kpis = CalculateKPIS(pz_code="PZ130", calculation_date=AUDIT_START_DATE)

    EXPECTED_TOTAL_ELIGIBLE = 2
    EXPECTED_TOTAL_INELIGIBLE = 2
    EXPECTED_TOTAL_PASSED = 1
    EXPECTED_TOTAL_FAILED = 1

    EXPECTED_KPIRESULT = KPIResult(
        total_eligible=EXPECTED_TOTAL_ELIGIBLE,
        total_passed=EXPECTED_TOTAL_PASSED,
        total_ineligible=EXPECTED_TOTAL_INELIGIBLE,
        total_failed=EXPECTED_TOTAL_FAILED,
    )

    # First set self.total_kpi_1_eligible_pts_base_query_set result
    # of total eligible
    calc_kpis.calculate_kpi_1_total_eligible()

    assert_kpi_result_equal(
        expected=EXPECTED_KPIRESULT,
        actual=calc_kpis.calculate_kpi_14_four_or_more_injections_per_day(),
    )
