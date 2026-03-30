"""Tests for the CalculateKPIS class.

Also contains utils / helper functions for testing the CalculateKPIS class.
"""

import logging
from datetime import date, timedelta

import pytest
from django.db.models import QuerySet

from project.npda.kpi_class.kpis import CalculateKPIS, KPIResult, kpi_registry
from project.npda.models.patient import Patient
from project.npda.models.submission import Submission
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory
from project.npda.tests.factories.paediatrics_diabetes_unit_factory import (
    PaediatricsDiabetesUnitFactory,
)
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.UserDataClasses import test_user_audit_centre_reader_data

# Logging
logger = logging.getLogger(__name__)


# HELPERS
def assert_kpi_result_equal(
    expected: KPIResult,
    actual: KPIResult,
) -> None:
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

    # Queryset checks
    if expected.patient_querysets is not None:
        # If actual.patient_querysets is None, we can't compare the querysets
        if actual.patient_querysets is None:
            mismatches.append(
                f"patient_querysets: expected {expected.patient_querysets}, got None"
            )
        else:
            # For each pt queryset in expected, check if the actual queryset is
            # the same
            for key, expected_queryset in expected.patient_querysets.items():
                actual_queryset = actual.patient_querysets.get(key)

                # Convert to list and order by id to compare
                expected_queryset = list(expected_queryset.order_by("id"))
                actual_queryset = list(actual_queryset.order_by("id"))

                if expected_queryset != actual_queryset:
                    mismatches.append(
                        f"patient_querysets[{key}]:"
                        f"\nexpected_queryset\n\t{expected_queryset}"
                        f"\nactual_queryset\n\t{actual_queryset}\n"
                    )

    if mismatches:
        mismatch_details = "\n".join(mismatches)
        raise AssertionError(f"KPIResult mismatch:\n{mismatch_details}")


@pytest.mark.django_db
def test_ensure_mocked_audit_date_range_is_correct(AUDIT_START_DATE):
    """Ensure that the mocked audit date range is correct."""
    calc_kpis = CalculateKPIS(calculation_date=AUDIT_START_DATE)

    assert calc_kpis.audit_start_date == date(2024, 4, 1), (
        "Mocked audit start date incorrect!"
    )
    assert calc_kpis.audit_end_date == date(2025, 3, 31), (
        "Mocked audit end date incorrect!"
    )


@pytest.mark.parametrize(
    "calculation_method, calculation_args",
    [
        ("calculate_kpis_for_patients", {"patients": Patient.objects.all()}),
        ("calculate_kpis_for_pdus", {"pz_codes": ["mocked_pz_code"]}),
    ],
)
@pytest.mark.django_db
def test_kpi_calculations_dont_break_when_no_patients(
    calculation_method,
    calculation_args,
    AUDIT_START_DATE,
):
    """Tests none of the KPIs break when no patients are present.

    Just runs all KPI calculations with no patients present.
    """

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    kpi_calculator = CalculateKPIS(calculation_date=AUDIT_START_DATE)

    # Run each calculation method
    kpi_calculation_method = getattr(kpi_calculator, calculation_method)
    kpi_calculations_object = kpi_calculation_method(**calculation_args)

    for kpi, results in kpi_calculations_object["calculated_kpi_values"].items():
        # remove the kpi_label key from the results
        results.pop("kpi_label", None)
        # also remove the patient_querysets key from the results
        results.pop("patient_querysets", None)

        values = list(results.values())

        # if this is one of measures 1-12, the pass and failed keys will contain None - remove them
        assert all(
            isinstance(value, int) or isinstance(value, float)
            for value in values
            if value is not None
        ), f"KPI {kpi} has non-integer values: {results}"


@pytest.mark.django_db
def test_calculate_kpis_return_obj_has_correct_kpi_labels(AUDIT_START_DATE):
    """Tests that the CalculateKPIS object has the correct KPI label for each
    KPI.

    Do this by taking the kpi_registry and comparing it to the result object.

    The CalculateKPIS is a pretty thin wrapper around the kpi_registry anyway but this is to ensure
    that the KPI labels are correctly set.
    """
    kpi_calculator = CalculateKPIS(calculation_date=AUDIT_START_DATE)

    kpi_calc_obj = kpi_calculator.calculate_kpis_for_patients(Patient.objects.all())

    kpi_results_obj = kpi_calc_obj["calculated_kpi_values"]

    for actual_kpi_attribute_name, result_obj in kpi_results_obj.items():
        actual_kpi_label = result_obj["kpi_label"]

        # Get the expected KPI label from the registry
        kpi_names_split = actual_kpi_attribute_name.split("_")

        kpi_number = int(kpi_names_split[1])
        if kpi_number == 32:
            kpi_number = 320 + int(kpi_names_split[2])  # offset for subkpis

        EXPECTED_KPI_NAMES = kpi_registry.get_kpi(kpi_number)

        assert actual_kpi_attribute_name == EXPECTED_KPI_NAMES.attribute_name, (
            f"KPI {actual_kpi_attribute_name} has incorrect attribute name: "
        )
        "{actual_kpi_attribute_name}"

        assert actual_kpi_label == EXPECTED_KPI_NAMES.rendered_label, (
            f"KPI {actual_kpi_attribute_name} has incorrect label: {actual_kpi_label}"
        )


@pytest.mark.django_db
def test_calculate_kpis_only_includes_patients_with_an_active_submission(
    AUDIT_START_DATE: date,
    seed_groups_fixture,
    seed_users_fixture,
):
    """Tests that only patients with an active submission are included in the KPI calculations."""
    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    submission_pdu = PaediatricsDiabetesUnitFactory()

    # User in this pdu
    user_data = test_user_audit_centre_reader_data
    submission_user = NPDAUserFactory(
        organisation_employers=[submission_pdu.pz_code],
        groups=[user_data.group_name],
        role=user_data.role,
    )

    # Create an inactive submission
    # using postcode for debugging purposes
    inactive_submission_pt = PatientFactory(
        postcode="inactive_submission_pt",
        diabetes_type=1,
        visit__visit_date=AUDIT_START_DATE
        + timedelta(days=1),  # visit date must be within audit period and not None
    )
    inactive_submission = Submission.objects.create(
        audit_year=AUDIT_START_DATE.year,
        paediatric_diabetes_unit=submission_pdu,
        submission_date=AUDIT_START_DATE + timedelta(days=1),
        submission_active=False,
        submission_by=submission_user,
    )
    inactive_submission.patients.add(inactive_submission_pt)

    # Now create an active submission
    # using postcode for debugging purposes
    active_submission_pt = PatientFactory(
        postcode="active_submission_pt",
        diabetes_type=1,
        visit__visit_date=AUDIT_START_DATE
        + timedelta(days=1),  # visit date must be within audit period and not None
    )
    # create active submission
    active_submission = Submission.objects.create(
        audit_year=AUDIT_START_DATE.year,
        paediatric_diabetes_unit=submission_pdu,
        submission_date=AUDIT_START_DATE + timedelta(days=1),
        submission_active=True,
        submission_by=submission_user,
    )
    active_submission.patients.add(active_submission_pt)

    # Perform calculations
    kpi_calculator = CalculateKPIS(
        calculation_date=AUDIT_START_DATE,
        return_pt_querysets=True,
    )

    kpi_calculator.set_patients_for_calculation(pz_codes=[submission_pdu.pz_code])

    kpi_1_patients: QuerySet[Patient] = kpi_calculator._calculate_kpis()[
        "calculated_kpi_values"
    ][kpi_calculator.kpi_name_registry.get_attribute_name(1)]["patient_querysets"]

    # Ensure correct pts
    assert (
        inactive_submission_pt not in kpi_1_patients["eligible"]
    )  # inactive submission patients should have been filtered out
    assert (
        inactive_submission_pt not in kpi_1_patients["ineligible"]
    )  # inactive submission patients should have been filtered out
    assert active_submission_pt in kpi_1_patients["eligible"]
    assert active_submission_pt not in kpi_1_patients["ineligible"]


# NOTE: Leaving commented (on 15 Mar 2025) in case we come back to this, see PR #781 for details
# @pytest.mark.django_db
# def test_calculate_kpis_excludes_patients_in_an_active_submission_with_no_visit_dates_within_audit_period(
#     AUDIT_START_DATE: date,
#     seed_groups_fixture,
#     seed_users_fixture,
# ):
#     """
#     Tests that patients in an active submission with no visit dates within the audit period are excluded from the KPI calculations.
#     This is because users will upload a csv file which may include visit dates outside the audit period as well as in.
#     """

#     # Ensure starting with clean pts in test db
#     Patient.objects.all().delete()

#     submission_pdu = PaediatricsDiabetesUnitFactory()

#     # User in this pdu
#     user_data = test_user_audit_centre_reader_data
#     submission_user = NPDAUserFactory(
#         organisation_employers=[submission_pdu.pz_code],
#         groups=[user_data.group_name],
#         role=user_data.role,
#     )

#     # Create an active submission
#     # using postcode for debugging purposes
#     active_submission_pt = PatientFactory(
#         postcode="active_submission_pt",
#         diabetes_type=1,
#         visit__visit_date=AUDIT_START_DATE
#         - timedelta(days=2),  # visit date must be outside audit period and not None
#     )
#     # add a second visit outside the audit period
#     Visit.objects.create(
#         patient=active_submission_pt,
#         visit_date=AUDIT_START_DATE - timedelta(days=1),
#     )

#     # create active submission
#     active_submission = Submission.objects.create(
#         audit_year=AUDIT_START_DATE.year,
#         paediatric_diabetes_unit=submission_pdu,
#         submission_date=AUDIT_START_DATE + timedelta(days=1),
#         submission_active=True,
#         submission_by=submission_user,
#     )
#     active_submission.patients.add(active_submission_pt)

#     # Perform calculations
#     kpi_calculator = CalculateKPIS(
#         calculation_date=AUDIT_START_DATE,
#         return_pt_querysets=True,
#     )

#     kpi_calculator.set_patients_for_calculation(pz_codes=[submission_pdu.pz_code])

#     kpi_1_patients: QuerySet[Patient] = kpi_calculator._calculate_kpis()[
#         "calculated_kpi_values"
#     ][kpi_calculator.kpi_name_registry.get_attribute_name(1)]["patient_querysets"]

#     assert (
#         active_submission_pt not in kpi_1_patients["eligible"]
#     )  # active submission patients with one or more visit dates within audit period should be included
#     assert active_submission_pt not in kpi_1_patients["ineligible"]
#     # count the number of visits in the patient_querysets
