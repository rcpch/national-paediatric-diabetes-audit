import dataclasses
import datetime
from decimal import Decimal
import pytest
from unittest.mock import Mock, patch

from django.core.exceptions import ValidationError

from project.constants import ALL_VISIT_DATES
from project.npda.forms.visit_form import VisitForm
from project.npda.forms.external_visit_validators import (
    VisitExternalValidationResult,
    CentileAndSDS,
)
from project.npda.models import Visit, AuditPeriod
from project.npda.tests.factories.patient_factory import PatientFactory


MOCK_EXTERNAL_VALIDATION_RESULT = VisitExternalValidationResult(None, None, None, None)


def mock_external_validation_result(**kwargs):
    return Mock(
        return_value=dataclasses.replace(MOCK_EXTERNAL_VALIDATION_RESULT, **kwargs)
    )


# We don't want to call remote services in unit tests
@pytest.fixture(autouse=True)
def mock_remote_calls():
    with patch(
        "project.npda.forms.visit_form.validate_visit_sync",
        Mock(return_value=MOCK_EXTERNAL_VALIDATION_RESULT),
    ):
        yield None


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/359
@pytest.mark.django_db
def test_height_and_weight_set_correctly():
    patient = PatientFactory()

    form = VisitForm(
        data={
            "height": "60",
            "weight": "50",
            "height_weight_observation_date": "2026-01-01",
        },
        initial={"patient": patient},
    )

    # Not passing all the data so it will have errors, just trigger the cleaners
    form.is_valid()

    assert form.cleaned_data["height"] == 60
    assert form.cleaned_data["weight"] == 50


@pytest.mark.django_db
def test_height_and_weight_missing_values():
    patient = PatientFactory()

    form = VisitForm(
        data={
            "height": None,
            "weight": None,
            "height_weight_observation_date": "2026-01-01",
        },
        initial={"patient": patient},
    )

    # Not passing all the data so it will have errors, just trigger the cleaners
    assert form.is_valid() == False, f"Height/Weight not supplied but date supplied"


@pytest.mark.django_db
def test_height_and_weight_missing_date():
    patient = PatientFactory()

    form = VisitForm(
        data={
            "height": "60",
            "weight": None,
            "height_weight_observation_date": None,
        },
        initial={"patient": patient},
    )

    # Not passing all the data so it will have errors, just trigger the cleaners
    assert form.is_valid() == False, (
        f"Height/Weight observation date not supplied but height/weight supplied"
    )


@pytest.mark.django_db
@patch(
    "project.npda.forms.visit_form.validate_visit_sync",
    mock_external_validation_result(
        height_result=CentileAndSDS(centile=Decimal("0.1"), sds=Decimal("0.2")),
        weight_result=CentileAndSDS(centile=Decimal("0.3"), sds=Decimal("0.4")),
        bmi=Decimal("0.5"),
        bmi_result=CentileAndSDS(centile=Decimal("0.6"), sds=Decimal("0.7")),
    ),
)
def test_dgc_results_saved():
    patient = PatientFactory()

    form = VisitForm(
        data={
            "height": "60",
            "weight": "50",
            "height_weight_observation_date": "2026-01-01",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    form.is_valid()

    # TODO MRB: why do I have to do this in test but it happens automatically normally?
    form.instance.patient_id = patient.id
    visit = form.save()

    assert visit.height_centile == Decimal("0.1")
    assert visit.height_sds == Decimal("0.2")
    assert visit.weight_centile == Decimal("0.3")
    assert visit.weight_sds == Decimal("0.4")
    assert visit.bmi == Decimal("0.5")
    assert visit.bmi_centile == Decimal("0.6")
    assert visit.bmi_sds == Decimal("0.7")


@pytest.mark.django_db
@patch(
    "project.npda.forms.visit_form.validate_visit_sync",
    mock_external_validation_result(
        height_result=CentileAndSDS(centile=Decimal("0.1"), sds=Decimal("0.2")),
    ),
)
def test_partial_dgc_results_saved():
    patient = PatientFactory()

    form = VisitForm(
        data={
            "height": "60",
            "weight": "50",
            "height_weight_observation_date": "2026-01-01",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    form.is_valid()

    # TODO MRB: why do I have to do this in test but it happens automatically normally?
    form.instance.patient_id = patient.id
    visit = form.save()

    assert visit.height_centile == Decimal("0.1")
    assert visit.height_sds == Decimal("0.2")
    assert visit.weight_centile is None
    assert visit.weight_sds is None
    assert visit.bmi is None
    assert visit.bmi_centile is None
    assert visit.bmi_sds is None


@pytest.mark.django_db
@patch(
    "project.npda.forms.visit_form.validate_visit_sync",
    mock_external_validation_result(height_result=ValidationError("oh noes!")),
)
def test_dgc_height_validation_error():
    patient = PatientFactory()

    form = VisitForm(
        data={
            "height": "60",
            "weight": "50",
            "height_weight_observation_date": "2026-01-01",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    form.is_valid()

    assert form.errors["height"] == ["oh noes!"]


@pytest.mark.django_db
@patch(
    "project.npda.forms.visit_form.validate_visit_sync",
    mock_external_validation_result(weight_result=ValidationError("oh noes!")),
)
def test_dgc_weight_validation_error():
    patient = PatientFactory()

    form = VisitForm(
        data={
            "height": "60",
            "weight": "50",
            "height_weight_observation_date": "2026-01-01",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    form.is_valid()

    assert form.errors["weight"] == ["oh noes!"]


@pytest.mark.django_db
@patch(
    "project.npda.forms.visit_form.validate_visit_sync",
    mock_external_validation_result(bmi_result=ValidationError("oh noes!")),
)
def test_dgc_bmi_validation_error():
    patient = PatientFactory()

    form = VisitForm(
        data={
            "height": "60",
            "weight": "50",
            "height_weight_observation_date": "2026-01-01",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    form.is_valid()

    assert form.errors["height"] == ["oh noes!"]
    assert form.errors["weight"] == ["oh noes!"]


"""
HbA1c tests
"""


@pytest.mark.django_db
def test_hba1c_value_ifcc_less_than_20_form_fail_validation():
    """
    Test that HbA1c value (IFCC mmol/mol) less than 20 % fails validation
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "hba1c": "2",
            "hba1c_format": "2",  # IFCC (mmol/mol)
            "hba1c_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    form.is_valid()

    assert "hba1c" in form.errors


@pytest.mark.django_db
def test_hba1c_value_dcct_less_than_20_form_pass_validation():
    """
    Test that HbA1c value (DCCT %) less than 20 % is accepted
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "hba1c": "5",
            "hba1c_format": "2",  # DCCT (%)
            "hba1c_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"


@pytest.mark.django_db
def test_hba1c_value_ifcc_more_than_195_form_validation():
    """
    Test that HbA1c value (IFCC mmol/mo) > 195 mmol/mol fails validation
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "hba1c": "200",
            "hba1c_format": "1",  # IFCC (mmol/mol)
            "hba1c_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should not be valid when hba1c > 195 mmol/mol"
    )
    assert "hba1c" in form.errors


@pytest.mark.django_db
def test_hba1c_value_dcct_more_than_20_form_fails_validation():
    """
    Test that HbA1c value (DCCT %) more than 20 fails validation
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "hba1c": "25",
            "hba1c_format": "2",  # DCCT (%)
            "hba1c_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, f"Form should be not valid when hba1c > 20%"
    assert "hba1c" in form.errors


@pytest.mark.django_db
def test_hba1c_value_dcct_less_than_3_form_fails_validation():
    """
    Test that HbA1c value (DCCT %) < 3% fails validation
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "hba1c": "2",
            "hba1c_format": "2",  # DCCT (%)
            "hba1c_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, f"Form should not be valid when hba1c < 3%"
    assert "hba1c" in form.errors


@pytest.mark.django_db
def test_hba1c_missing_form_fails_validation():
    """
    Test that HbA1c value (DCCT %) < 3% fails validation
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "hba1c": None,
            "hba1c_format": "2",  # DCCT (%)
            "hba1c_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, f"Form should not be valid when HbA1c is missing"
    assert "hba1c" in form.errors


@pytest.mark.django_db
def test_hba1c_date_missing_form_fails_validation():
    """
    Test that HbA1c value (DCCT %) missing fails validation
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "hba1c": 5,
            "hba1c_format": "2",  # DCCT (%)
            "hba1c_date": None,
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should not be valid when HbA1c date is missing"
    )
    assert "hba1c_date" in form.errors


@pytest.mark.django_db
def test_hba1c_date_and_hba1c_format_missing_form_fails_validation():
    """
    Test that HbA1c format and date missing fails validation
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "hba1c": 5,
            "hba1c_format": None,  # DCCT (%)
            "hba1c_date": None,
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should not be valid when HbA1c date and format are missing"
    )
    assert "hba1c_date" in form.errors
    assert "hba1c_format" in form.errors


@pytest.mark.django_db
def test_hba1c_date_and_hba1c_format_hba1c_all_missing_form_passes_validation():
    """
    Test that HbA1c format and date missing fails validation
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "hba1c": None,
            "hba1c_format": None,  # DCCT (%)
            "hba1c_date": None,
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == True, (
        f"Form should  be valid when HbA1c, HbA1c date and format are missing, but got {form.errors}"
    )
    assert "hba1c_date" not in form.errors
    assert "hba1c_format" not in form.errors
    assert "hba1c" not in form.errors


"""
Diabetes treatment tests
"""


@pytest.mark.django_db
def test_treatment_closed_loop_form_passes_validation():
    """
    Test that both pump and closed loop system are accepted
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "treatment": "3",  # Insulin pump
            "closed_loop_system": "1",  # Closed loop system (licenced)
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"


@pytest.mark.django_db
def test_treatment_missing_closed_loop_form_fails_validation():
    """
    Test that both closed loop system selected but treatment is None fail validation
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "treatment": None,
            "closed_loop_system": "1",  # Closed loop system (licenced)
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as closed loop system selected but treatment not selected as 1 or 3 (pump or pump + meds)"
    )


@pytest.mark.django_db
def test_treatment_mdi_but_closed_loop_selected_form_fails_validation():
    """
    Test that MDI selected but closed loop system is also selected
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "treatment": 2,  # MDI
            "closed_loop_system": "1",  # Closed loop system (licenced)
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as closed loop system selected but treatment not selected as 1 or 3 (pump or pump + meds)"
    )


"""
Blood pressure tests
"""


@pytest.mark.django_db
def test_blood_pressure_values_form_passes_validation():
    """
    Test that both systolic and diastolic blood pressure values are accepted
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "systolic_blood_pressure": "120",
            "diastolic_blood_pressure": "80",
            "blood_pressure_observation_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"


@pytest.mark.django_db
def test_blood_pressure_missing_values_form_fails_validation():
    """
    Test that one missing systolic blood pressure value fails validation
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "systolic_blood_pressure": None,
            "diastolic_blood_pressure": "80",
            "blood_pressure_observation_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as missing systolic blood pressure but passed measure."
    )


@pytest.mark.django_db
def test_blood_pressure_missing_date_form_fails_validation():
    """
    Test that missing blood pressure observation date fails validation
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "systolic_blood_pressure": "120",
            "diastolic_blood_pressure": "80",
            "blood_pressure_observation_date": None,
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as missing blood pressure date but passed measure."
    )


@pytest.mark.django_db
def test_systolic_blood_pressure_over_240_form_fails_validation():
    """
    Test that systolic blood pressure value > 240 fails validation
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "systolic_blood_pressure": "250",
            "diastolic_blood_pressure": "80",
            "blood_pressure_observation_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as systolic blood pressure > 240 and is a medical emergency, but passed measure."
    )


@pytest.mark.django_db
def test_systolic_blood_pressure_below_80_form_fails_validation():
    """
    Test that systolic blood pressure value < 80 fails validation
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "systolic_blood_pressure": "60",
            "diastolic_blood_pressure": "80",
            "blood_pressure_observation_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as systolic blood pressure < 80 and tbh not really compatible with life, but passed measure."
    )


@pytest.mark.django_db
def test_diastolic_blood_pressure_over_120_form_fails_validation():
    """
    Test that diastolic blood pressure value > 120 fails validation
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "systolic_blood_pressure": "120",
            "diastolic_blood_pressure": "125",
            "blood_pressure_observation_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as diastolic blood pressure > 120 and is a medical emergency, but passed measure."
    )


@pytest.mark.django_db
def test_diastolic_blood_pressure_below_20_form_fails_validation():
    """
    Test that diastolic blood pressure value < 20 fails validation
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "systolic_blood_pressure": "120",
            "diastolic_blood_pressure": "15",
            "blood_pressure_observation_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as diastolic blood pressure < 20, but passed measure."
    )


"""
DECS tests
"""


@pytest.mark.django_db
def test_decs_value_form_passes_validation():
    """
    Test that DECS value is accepted
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "retinal_screening_result": 1,  # Normal
            "retinal_screening_observation_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"


@pytest.mark.django_db
def test_decs_value_unrecognized_form_fails_validation():
    """
    Test that an impossible DECS value is invalid
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "retinal_screening_result": 94,  # invalid
            "retinal_screening_observation_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Invalid retinal screening result offered but test passed"
    )


@pytest.mark.django_db
def test_decs_value_none_form_fails_validation():
    """
    Test that a missing DECS value is invalid
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "retinal_screening_result": None,  # invalid
            "retinal_screening_observation_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"No retinal screening result offered but test passed"
    )


@pytest.mark.django_db
def test_decs_normal_result_without_date_passes_validation():
    """
    Test that Normal retinal screening result without a date is valid (new KPI logic)
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "retinal_screening_result": 1,  # Normal
            "retinal_screening_observation_date": None,
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid(), (
        f"Form should be valid for Normal result without date but got {form.errors}"
    )


@pytest.mark.django_db
def test_decs_abnormal_result_without_date_fails_validation():
    """
    Test that Abnormal retinal screening result without a date is invalid
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "retinal_screening_result": 2,  # Abnormal
            "retinal_screening_observation_date": None,
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Abnormal retinal screening result without date should fail validation"
    )


"""
Urine albumin tests
"""


@pytest.mark.django_db
def test_urine_albumin_value_form_passes_validation():
    """
    Test that urine albumin value is accepted
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "albumin_creatinine_ratio": 10,
            "albumin_creatinine_ratio_date": "2026-01-01",
            "albuminuria_stage": 1,  # Normal
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"


@pytest.mark.django_db
def test_urine_albumin_impossible_value_form_fails_validation():
    """
    Test that urine albumin staget is rejected if impossible
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "albumin_creatinine_ratio": 10,
            "albumin_creatinine_ratio_date": "2026-01-01",
            "albuminuria_stage": 8,  # Impossible
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as albuminuria stage impossible, but got {form.errors}"
    )


@pytest.mark.django_db
def test_urine_albumin_value_below_range_form_fails_validation():
    """
    Test that urine albumin value is rejected if below range
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "albumin_creatinine_ratio": -5,
            "albumin_creatinine_ratio_date": "2026-01-01",
            "albuminuria_stage": 2,  # microalbuminuria
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as albuminuria < 0, passed"
    )


@pytest.mark.django_db
def test_urine_albumin_value_above_range_form_fails_validation():
    """
    Test that urine albumin value is rejected if above range
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "albumin_creatinine_ratio": 1000,
            "albumin_creatinine_ratio_date": "2026-01-01",
            "albuminuria_stage": 3,  # macroalbuminuria
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as albuminuria < 3, passed"
    )


@pytest.mark.django_db
def test_urine_albumin_value_missing_form_fails_validation():
    """
    Test that urine albumin value missing  is rejected
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "albumin_creatinine_ratio": None,
            "albumin_creatinine_ratio_date": "2026-01-01",
            "albuminuria_stage": 2,  # micrralbuminuria
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as albuminuria None, passed"
    )


@pytest.mark.django_db
def test_urine_albumin_stage_missing_form_fails_validation():
    """
    Test that urine albumin value missing  is rejected
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "albumin_creatinine_ratio": 10,
            "albumin_creatinine_ratio_date": "2026-01-01",
            "albuminuria_stage": None,  # microalbuminuria
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as albuminuria None, passed"
    )


@pytest.mark.django_db
def test_urine_albumin_date_missing_form_fails_validation():
    """
    Test that urine albumin date missing is rejected
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "albumin_creatinine_ratio": 10,
            "albumin_creatinine_ratio_date": None,
            "albuminuria_stage": 1,  # Normal
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as albuminuria date is None, passed"
    )


"""
Cholesterol tests
"""


@pytest.mark.django_db
def test_total_cholesterol_value_form_passes_validation():
    """
    Test that total cholesterol value is accepted
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "total_cholesterol": 4,
            "total_cholesterol_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"
    assert "total_cholesterol" not in form.errors


@pytest.mark.django_db
def test_total_cholesterol_value_below_range_form_fails_validation():
    """
    Test that total cholesterol value is rejected if below range
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "total_cholesterol": 1,
            "total_cholesterol_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as total cholesterol < 2, passed"
    )


@pytest.mark.django_db
def test_total_cholesterol_value_above_range_form_fails_validation():
    """
    Test that total cholesterol value is rejected if above range
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "total_cholesterol": 20,
            "total_cholesterol_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as total cholesterol > 12 mmol/L, passed"
    )


@pytest.mark.django_db
def test_total_cholesterol_value_missing_form_fails_validation():
    """
    Test that total cholesterol value missing  is rejected
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "total_cholesterol": None,
            "total_cholesterol_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as total cholesterol None, passed"
    )


@pytest.mark.django_db
def test_total_cholesterol_date_missing_form_fails_validation():
    """
    Test that total cholesterol date missing is rejected
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "total_cholesterol": 4,
            "total_cholesterol_date": None,
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Form should be invalid as total cholesterol date is None, passed"
    )


"""
thyroid tests
"""


@pytest.mark.django_db
def test_thyroid_treatment_status_form_passes_validation():
    """
    Test that thyroid function status and date are accepted
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "thyroid_treatment_status": 2,  # Thyroxine for hypothyroidism
            "thyroid_function_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"
    assert "thyroid_treatment_status" not in form.errors
    assert "thyroid_function_date" not in form.errors


@pytest.mark.django_db
def test_thyroid_treatment_status_unrecognized_form_fails_validation():
    """
    Test that an impossible thyroid function status is invalid
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "thyroid_treatment_status": 94,  # invalid
            "thyroid_function_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Invalid thyroid treatment status offered but test passed"
    )
    assert "thyroid_treatment_status" in form.errors


@pytest.mark.django_db
def test_thyroid_treatment_status_none_form_fails_validation():
    """
    Test that missing thyroid function status is invalid
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "thyroid_treatment_status": None,  # invalid
            "thyroid_function_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"No thyroid treatment status offered but test passed"
    )
    assert "thyroid_treatment_status" in form.errors


@pytest.mark.django_db
def test_thyroid_function_date_none_form_passes_validation():
    """
    Test that missing thyroid function date is valid
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "thyroid_treatment_status": 2,
            "thyroid_function_date": None,
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == True, (
        f"No thyroid function date offered with treatment should pass"
    )
    assert "thyroid_function_date" not in form.errors


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/625
@pytest.mark.django_db
def test_thyroid_function_date_none_form_passes_validation_if_treatment_not_prescribed():
    """
    Test that missing thyroid function date is invalid
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "thyroid_treatment_status": 1,
            "thyroid_function_date": None,
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"
    assert "thyroid_treatment_status" not in form.errors
    assert "thyroid_function_date" not in form.errors


"""
Coeliac tests
"""


@pytest.mark.django_db
def test_coeliac_treatment_status_form_passes_validation():
    """
    Test that coeliac function status and date are accepted
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "gluten_free_diet": 1,  # Normal
            "coeliac_screen_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"
    assert "gluten_free_diet" not in form.errors
    assert "coeliac_screen_date" not in form.errors


@pytest.mark.django_db
def test_coeliac_treatment_status_unrecognized_form_fails_validation():
    """
    Test that an impossible coeliac function status is invalid
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "gluten_free_diet": 94,  # invalid
            "coeliac_screen_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Invalid coeliac function status offered but test passed"
    )


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/628
@pytest.mark.django_db
def test_coeliac_treatment_status_none_form_passes_validation():
    patient = PatientFactory()

    form = VisitForm(
        data={
            "gluten_free_diet": None,  # invalid
            "coeliac_screen_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert "gluten_free_diet" not in form.errors


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/628
@pytest.mark.django_db
def test_coeliac_screen_date_none_form_fails_validation():
    patient = PatientFactory()

    form = VisitForm(
        data={
            "gluten_free_diet": 1,  # Normal
            "coeliac_screen_date": None,
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert "gluten_free_diet" not in form.errors


"""
Psychological tests
"""


@pytest.mark.django_db
def test_psychological_status_form_passes_validation():
    """
    Test that psychological status and date are accepted
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "psychological_additional_support_status": 1,  # Normal
            "psychological_screening_assessment_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"
    assert "psychological_additional_support_status" not in form.errors
    assert "psychological_screening_assessment_date" not in form.errors


@pytest.mark.django_db
def test_psychological_status_unrecognized_form_fails_validation():
    """
    Test that an impossible psychological status is invalid
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "psychological_additional_support_status": 94,  # invalid
            "psychological_screening_assessment_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Invalid psychological status offered but test passed"
    )


@pytest.mark.django_db
def test_psychological_status_none_form_fails_validation():
    """
    Test that missing psychological status is invalid
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "psychological_additional_support_status": None,  # invalid
            "psychological_screening_assessment_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, f"No psychological status offered but test passed"


@pytest.mark.django_db
def test_psychological_screen_date_none_form_fails_validation():
    """
    Test that missing psychological date is invalid
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "psychological_additional_support_status": 1,  # Normal
            "psychological_screening_assessment_date": None,
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid() == False, f"No psychological date offered but test passed"


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/628
@pytest.mark.django_db
def test_psychological_screen_date_none_with_status_unknown_passes_validation():
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "psychological_additional_support_status": 99,  # Unknown
            "psychological_screening_assessment_date": None,
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert "psychological_screening_assessment_date" not in form.errors
    assert form.is_valid()


"""
Smoking tests
"""


@pytest.mark.django_db
def test_smoking_status_smoker_form_passes_validation():
    """
    Test that smoking status and date are accepted
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "smoking_status": 2,  # current smoker
            "smoking_cessation_referral_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"
    assert "smoking_status" not in form.errors
    assert "smoking_cessation_referral_date" not in form.errors


@pytest.mark.django_db
def test_smoking_status_non_smoker_form_passes_validation():
    """
    Test that smoking status and date are accepted
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "smoking_status": 1,  # non smoker
            "smoking_cessation_referral_date": None,
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"
    assert "smoking_status" not in form.errors
    assert "smoking_cessation_referral_date" not in form.errors


@pytest.mark.django_db
def test_smoking_status_unrecognized_form_fails_validation():
    """
    Test that an impossible smoking status is invalid
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "smoking_status": 94,  # invalid
            "smoking_cessation_referral_date": "2026-01-01",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, f"Invalid smoking status offered but test passed"
    assert "smoking_status" in form.errors, (
        "Invalid smoking status offered but test passed"
    )
    assert "smoking_cessation_referral_date" in form.errors, (
        "Smoking cessation referral date in context of invalid smoking status offered but test passed"
    )


@pytest.mark.django_db
def test_smoking_status_date_when_non_smoker_form_fails_validation():
    """
    Test that smoking cessation referral date exist if the patient is a non-smoker should fail
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "smoking_status": 1,  # Non-smoker
            "smoking_cessation_referral_date": "2026-01-01",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Smoking cessation referral date offered but test passed"
    )
    assert "smoking_status" not in form.errors
    assert "smoking_cessation_referral_date" in form.errors


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/791
@pytest.mark.django_db
def test_smoking_status_smoker_does_not_require_cessation_referral_date():
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "smoking_status": 2,  # current smoker
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"
    assert "smoking_status" not in form.errors
    assert "smoking_cessation_referral_date" not in form.errors


"""
Dietician tests
"""


@pytest.mark.django_db
def test_dietician_referral_status_additional_offered_form_passes_validation():
    """
    Test that dietician referral status and date are accepted
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "dietician_additional_appointment_offered": 1,  # Yes
            "dietician_additional_appointment_date": "2026-01-01",
            "carbohydrate_counting_level_three_education_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"
    assert "dietician_referral_status" not in form.errors
    assert "dietician_referral_date" not in form.errors


@pytest.mark.django_db
def test_dietician_no_additional_offered_form_passes_validation():
    """
    Test that dietician referral status and date are accepted
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "dietician_additional_appointment_offered": 2,  # No
            "dietician_additional_appointment_date": None,
            "carbohydrate_counting_level_three_education_date": "2026-01-01",
        },
        initial={"patient": patient},
    )
    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"
    assert "dietician_referral_status" not in form.errors
    assert "dietician_referral_date" not in form.errors


@pytest.mark.django_db
def test_dietician_no_additional_offered_date_provided_fail_validation():
    """
    Test that dietician extra appointment not offered but date provided should fail
    """

    patient = PatientFactory()

    form = VisitForm(
        data={
            "dietician_additional_appointment_offered": 2,  # No
            "dietician_additional_appointment_date": "2026-01-01",
            "carbohydrate_counting_level_three_education_date": "2026-01-01",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Dietician extra appointment not offered but date provided should fail"
    )
    assert "dietician_additional_appointment_date" in form.errors


@pytest.mark.django_db
def test_dietician_additional_offered_date_missing_passes_validation():
    """
    Test that dietician extra appointment offered but date missing should pass
    https://github.com/rcpch/national-paediatric-diabetes-audit/issues/668
    """

    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "dietician_additional_appointment_offered": 1,  # Yes
            "dietician_additional_appointment_date": None,
            "carbohydrate_counting_level_three_education_date": "2026-01-01",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid(), (
        f"Dietician extra appointment offered but date missing should pass"
    )
    assert "dietician_additional_appointment_date" not in form.errors


@pytest.mark.django_db
def test_dietician_additional_offered_no_but_date_offered_fail_validation():
    """
    Test that dietician additional appointment No but date offered should fail
    """

    patient = PatientFactory()

    form = VisitForm(
        data={
            "dietician_additional_appointment_offered": 2,  # No
            "dietician_additional_appointment_date": "2026-01-01",
            "carbohydrate_counting_level_three_education_date": "2026-01-01",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Dietician additional appointment No but date offered should fail"
    )
    assert "dietician_additional_appointment_date" in form.errors


"""
inpatient tests
"""


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_passes_validation():
    """
    Test that inpatient admission for stabilisation is accepted
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "hospital_admission_date": "2026-01-01",
            "hospital_discharge_date": "2026-01-08",
            "hospital_admission_reason": 1,  # patient stabilisation
            # dka_additional_therapies
            # hospital_admission_other
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"
    assert "hospital_admission_date" not in form.errors
    assert "hospital_discharge_date" not in form.errors
    assert "hospital_admission_reason" not in form.errors


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_missing_date_fails_validation():
    """
    Test that inpatient admission for stabilisation is rejected if date missing
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "hospital_admission_date": None,
            "hospital_discharge_date": "2026-01-08",
            "hospital_admission_reason": 1,  # patient stabilisation
            # dka_additional_therapies
            # hospital_admission_other
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Inpatient admission for stabilisation missing date should fail"
    )
    assert "hospital_admission_date" in form.errors


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_discharge_date_before_admission_date_fails_validation():
    """
    Test that inpatient admission for stabilisation is rejected if discharge date before admission date
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "hospital_admission_date": "2026-01-10",
            "hospital_discharge_date": "2026-01-08",
            "hospital_admission_reason": 1,  # patient stabilisation
            # dka_additional_therapies
            # hospital_admission_other
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Inpatient admission for stabilisation admission date before discharge date should fail"
    )
    assert "hospital_admission_date" in form.errors


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_discharge_date_before_diagnosis_date_fails_validation():
    """
    Test that inpatient admission for stabilisation is rejected if discharge date before admission date
    """
    patient = PatientFactory()
    patient.diagnosis_date = datetime.date(2026, 1, 10)

    form = VisitForm(
        data={
            "hospital_admission_date": "2026-01-01",
            "hospital_discharge_date": "2026-01-08",
            "hospital_admission_reason": 1,  # patient stabilisation
            # dka_additional_therapies
            # hospital_admission_other
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Inpatient admission for stabilisation admission date before discharge date should fail"
    )
    assert "hospital_discharge_date" in form.errors


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_admission_date_more_than_eleven_days_before_diagnosis_date_fails_validation():
    """
    Test that inpatient admission for stabilisation is rejected if diagnosis date is more than 11 days before admission date
    """
    patient = PatientFactory()
    patient.diagnosis_date = datetime.date(2026, 1, 15)

    form = VisitForm(
        data={
            "hospital_admission_date": "2026-01-01",
            "hospital_discharge_date": "2026-01-016",
            "hospital_admission_reason": 1,  # patient stabilisation
            # dka_additional_therapies
            # hospital_admission_other
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Inpatient admission for stabilisation admission date more than 11 days before diagnosis date should fail"
    )
    assert "hospital_admission_date" in form.errors


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_admission_date_less_than_eleven_days_before_diagnosis_date_passes_validation():
    """
    Test that inpatient admission for stabilisation passes if admission date is within 11 days of diagnosis date
    """
    patient = PatientFactory()
    patient.diagnosis_date = datetime.date(2026, 1, 15)

    form = VisitForm(
        data={
            "visit_date": "2026-02-01",  # Required for validation
            "hospital_admission_date": "2026-01-10",
            "hospital_discharge_date": "2026-01-16",
            "hospital_admission_reason": 1,  # patient stabilisation
            # dka_additional_therapies
            # hospital_admission_other
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid()


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_when_diagnosis_date_missing():
    """
    Test that inpatient admission for stabilisation passes if admission date is within 11 days of diagnosis date
    """
    patient = PatientFactory()
    patient.diagnosis_date = None

    form = VisitForm(
        data={
            "visit_date": "2026-02-01",  # Required for validation
            "hospital_admission_date": "2026-01-01",
            "hospital_discharge_date": "2026-01-08",
            "hospital_admission_reason": 1,  # patient stabilisation
            # dka_additional_therapies
            # hospital_admission_other
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid()


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_discharge_date_after_date_of_death_fails_validation():
    """
    Test that inpatient admission for stabilisation is rejected if discharge date before admission date
    """
    patient = PatientFactory()
    patient.death_date = datetime.date(2026, 1, 1)

    form = VisitForm(
        data={
            "hospital_admission_date": "2026-01-01",
            "hospital_discharge_date": "2026-01-08",
            "hospital_admission_reason": 1,  # patient stabilisation
            # dka_additional_therapies
            # hospital_admission_other
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Inpatient admission for stabilisation admission date before discharge date should fail"
    )
    assert "hospital_discharge_date" in form.errors


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_dka_additional_therapies_provided_fails_validation():
    """
    Test that inpatient admission for stabilisation is rejected if DKA additional therapies provided
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "hospital_admission_date": "2026-01-01",
            "hospital_discharge_date": "2026-01-08",
            "hospital_admission_reason": 1,  # patient stabilisation
            "dka_additional_therapies": 1,  # hypertonic saline
            # hospital_admission_other
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Inpatient admission for stabilisation with DKA additional therapies should fail"
    )
    assert "dka_additional_therapies" in form.errors, (
        "DKA additional therapies should be in errors as hospital admission for stabilisation"
    )


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_hospital_admission_other_provided_fails_validation():
    """
    Test that inpatient admission for stabilisation is rejected if DKA additional therapies provided
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "hospital_admission_date": "2026-01-01",
            "hospital_discharge_date": "2026-01-08",
            "hospital_admission_reason": 1,  # patient stabilisation
            "hospital_admission_other": "Other reason",
            "dka_additional_therapies": None,
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Inpatient admission for stabilisation with hospital admission other should fail"
    )
    assert "hospital_admission_reason" in form.errors, (
        "Hospital admission other should be in errors as hospital admission for stabilisation"
    )


@pytest.mark.django_db
def test_inpatient_admission_dka_passes_validation():
    """
    Test that inpatient admission for DKA with additional therapies is accepted
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "hospital_admission_date": "2026-01-01",
            "hospital_discharge_date": "2026-01-08",
            "hospital_admission_reason": 2,  # DKA
            "dka_additional_therapies": 1,  # hypertonic saline
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"
    assert "hospital_admission_date" not in form.errors
    assert "hospital_discharge_date" not in form.errors
    assert "hospital_admission_reason" not in form.errors
    assert "dka_additional_therapies" not in form.errors


@pytest.mark.django_db
def test_inpatient_admission_dka_additional_therapies_missing_fails_validation():
    """
    Test that inpatient admission for DKA without additional therapies is rejected
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "hospital_admission_date": "2026-01-01",
            "hospital_discharge_date": "2026-01-08",
            "hospital_admission_reason": 2,  # DKA
            "dka_additional_therapies": None,
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Inpatient admission for DKA without additional therapies should fail"
    )
    assert "dka_additional_therapies" in form.errors, (
        "DKA additional therapies should be in errors as hospital admission for DKA"
    )


@pytest.mark.django_db
def test_inpatient_admission_dka_additional_therapies_hospital_admission_also_provided_fails_validation():
    """
    Tests that a hospital admission for DKA with additional therapies is rejected if hospital admission other is provided
    """

    patient = PatientFactory()

    form = VisitForm(
        data={
            "hospital_admission_date": "2026-01-01",
            "hospital_discharge_date": "2026-01-08",
            "hospital_admission_reason": 2,  # DKA
            "dka_additional_therapies": 1,  # hypertonic saline
            "hospital_admission_other": "Other reason",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Inpatient admission for DKA with additional therapies and hospital_admission_other should fail"
    )
    assert "hospital_admission_reason" in form.errors, (
        "hospital_admission_other should be in errors as hospital admission for DKA"
    )


@pytest.mark.django_db
def test_inpatient_admission_other_passes_validation():
    """
    Test that inpatient admission for other reason is accepted
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "hospital_admission_date": "2026-01-01",
            "hospital_discharge_date": "2026-01-08",
            "hospital_admission_reason": 6,  # Other
            "hospital_admission_other": "Other reason",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"
    assert "hospital_admission_date" not in form.errors
    assert "hospital_discharge_date" not in form.errors
    assert "hospital_admission_reason" not in form.errors
    assert "hospital_admission_other" not in form.errors


@pytest.mark.django_db
def test_inpatient_admission_other_missing_fails_validation():
    """
    Test that inpatient admission for other reason is rejected if reason missing
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "hospital_admission_date": "2026-01-01",
            "hospital_discharge_date": "2026-01-08",
            "hospital_admission_reason": 6,  # Other
            "hospital_admission_other": None,
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, (
        f"Inpatient admission for other reason without reason should fail"
    )
    assert "hospital_admission_other" in form.errors, (
        "hospital_admission_other should be in errors as hospital admission for other reason"
    )


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/991
@pytest.mark.django_db
def test_inpatient_admission_without_discharge_date():
    """
    Questionnaire users may prefer to enter the admission as they go to avoid having to remember to do it on discharge
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",  # Required for validation
            "hospital_admission_date": "2026-01-01",
            "hospital_discharge_date": None,
            "hospital_admission_reason": 1,  # patient stabilisation
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert len(form.errors) == 0, f"Form should be valid but got {form.errors}"
    assert form.is_valid()


"""
Visit date tests
"""


@pytest.mark.django_db
def test_visit_date_provided_passes_validation():
    """
    Test that visit date is accepted
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid(), f"Form should be valid but got {form.errors}"
    assert "visit_date" not in form.errors


@pytest.mark.django_db
def test_visit_date_missing_fails_validation():
    """
    Test that visit date is rejected if missing
    """
    patient = PatientFactory()

    form = VisitForm(
        data={
            "visit_date": None,
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, f"Visit date missing should fail"
    assert "visit_date" in form.errors


@pytest.mark.django_db
def test_visit_date_after_diagnosis_date_passes_validation():
    """
    Test that visit date after diagnosis date is accepted
    """
    patient = PatientFactory()
    patient.diagnosis_date = datetime.date(2026, 1, 1)

    form = VisitForm(
        data={
            "visit_date": "2026-01-10",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid(), (
        f"Visit date after diagnosis date should pass but got {form.errors}"
    )
    assert "visit_date" not in form.errors


@pytest.mark.django_db
def test_visit_date_before_diagnosis_date_fails_validation():
    """
    Test that visit date before diagnosis date is rejected
    """
    patient = PatientFactory()
    patient.diagnosis_date = datetime.date(2026, 1, 10)

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, f"Visit date before diagnosis date should fail"
    assert "visit_date" in form.errors


@pytest.mark.django_db
def test_visit_date_after_death_date_fails_validation():
    """
    Test that visit date after death date is rejected
    """
    patient = PatientFactory()
    patient.death_date = datetime.date(2026, 1, 1)

    form = VisitForm(
        data={
            "visit_date": "2026-01-10",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, f"Visit date after death date should fail"
    assert "visit_date" in form.errors


@pytest.mark.django_db
def test_visit_date_before_death_date_passes_validation():
    """
    Test that visit date before death date is accepted
    """
    patient = PatientFactory()
    patient.death_date = datetime.date(2026, 1, 10)

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid(), (
        f"Visit date before death date should pass but got {form.errors}"
    )
    assert "visit_date" not in form.errors


@pytest.mark.django_db
def test_visit_date_before_birth_date_fails_validation():
    """
    Test that visit date before birth date is rejected
    """
    patient = PatientFactory()
    patient.date_of_birth = datetime.date(2026, 1, 10)

    form = VisitForm(
        data={
            "visit_date": "2026-01-01",
        },
        initial={"patient": patient},
    )

    # Trigger the cleaners
    assert form.is_valid() == False, f"Visit date before birth date should fail"
    assert "visit_date" in form.errors


@pytest.mark.parametrize(
    "test_case_index,test_data",
    enumerate(
        [
            {
                "visit_date": "2020-01-01",
                "height_weight_observation_date": "2020-01-01",
                "height": 150,
                "weight": 50,
            },
            {
                "visit_date": "2020-01-01",
                "hba1c_date": "2020-01-01",
                "hba1c": 58,
                "hba1c_format": 1,  # mmol/mol
            },
            {
                "visit_date": "2020-01-01",
                "blood_pressure_observation_date": "2020-01-01",
                "systolic_blood_pressure": 120,
                "diastolic_blood_pressure": 80,
            },
            {
                "visit_date": "2020-01-01",
                "foot_examination_observation_date": "2020-01-01",
                "foot_examination_status": 1,  # Normal
            },
            {
                "visit_date": "2020-01-01",
                "retinal_screening_observation_date": "2020-01-01",
                "retinal_screening_result": 1,  # Normal
            },
            {
                "visit_date": "2020-01-01",
                "albumin_creatinine_ratio_date": "2020-01-01",
                "albumin_creatinine_ratio": 30,
                "albuminuria_stage": 1,  # Normal
            },
            {
                "visit_date": "2020-01-01",
                "total_cholesterol_date": "2020-01-01",
                "total_cholesterol": 4.5,
            },
            {
                "visit_date": "2020-01-01",
                "thyroid_function_date": "2020-01-01",
                "thyroid_treatment_status": 1,  # Normal
            },
            {
                "visit_date": "2020-01-01",
                "coeliac_screen_date": "2020-01-01",
                "gluten_free_diet": 1,  # Normal
            },
            {
                "visit_date": "2020-01-01",
                "psychological_screening_assessment_date": "2020-01-01",
                "psychological_additional_support_status": 1,  # Normal
            },
            {
                "visit_date": "2020-01-01",
                "smoking_cessation_referral_date": "2020-01-01",
                "smoking_status": 2,  # Current smoker
            },
            {
                "visit_date": "2020-01-01",
                "carbohydrate_counting_level_three_education_date": "2020-01-01",
            },
            {
                "visit_date": "2020-01-01",
                "dietician_additional_appointment_offered": 1,  # Yes
                "dietician_additional_appointment_date": "2020-02-02",  # Date after visit date
            },
            {
                "visit_date": "2020-02-02",
                "flu_immunisation_recommended_date": "2020-01-01",
            },
            {
                "visit_date": "2020-01-01",
                "sick_day_rules_training_date": "2020-01-01",
            },
            {
                "visit_date": "2020-01-01",
                "hospital_admission_date": "2020-01-01",
                "hospital_discharge_date": "2020-01-08",
                "hospital_admission_reason": 1,  # patient stabilisation
            },
        ]
    ),
)
@pytest.mark.django_db
def test_visit_form_dates_outside_of_audit_period(test_case_index, test_data):
    """
    Test that all dates outside of the audit period are flagged as errors
    2024 / 2025 audit period is seeded in the fixture
    All the dates tested include:
        visit_date, height_weight_observation_date, hba1c_date,
        blood_pressure_observation_date, foot_examination_observation_date,
        retinal_screening_observation_date, albumin_creatinine_ratio_date,
        total_cholesterol_date, thyroid_function_date, coeliac_screen_date,
        psychological_screening_assessment_date, smoking_cessation_referral_date,
        carbohydrate_counting_level_three_education_date,
        dietician_additional_appointment_date, flu_immunisation_recommended_date,
        sick_day_rules_training_date, hospital_admission_date
        **hospital_discharge_date EXCLUDED as it is possible to have an admission
        without a discharge date in the audit period**
    """
    # Test data with dates outside audit period

    # Create patient once
    audit_period = AuditPeriod.objects.create(
        start_date=datetime.date(2024, 4, 1),
        end_date=datetime.date(2025, 3, 31),
        is_open=True,
        is_visible=True,
    )  # this will be 2024 / 2025

    patient = PatientFactory()
    # Set date of birth to 01/01/2015 as this cannot be after the other mocked dates
    patient.date_of_birth = datetime.date(2015, 1, 10)
    patient.diagnosis_date = datetime.date(
        2018, 1, 1
    )  # set diagnosis date to 01/01/2018
    patient.smoking_status = 2  # Current smoker
    patient.save()

    # Test each data scenario
    form = VisitForm(
        data=test_data,
        initial={
            "patient": patient,
        },
        audit_period=audit_period,
    )

    # Trigger the cleaners
    is_valid = form.is_valid()

    # Extract the date field being tested from the data
    date_fields = [key for key in test_data.keys() if "date" in key]
    tested_field = (
        date_fields[0]
        if date_fields[0] != "hospital_discharge_date" and date_fields
        else "unknown"
    )

    assert not is_valid, (
        f"Test case {test_case_index + 1} ({tested_field}): Form should be invalid due to dates outside audit period {audit_period}, but got valid form. Errors: {form.errors}"
    )

    # Verify that visit_date is always in errors (since all test cases have dates outside audit period)
    assert "visit_date" in form.errors, (
        f"Test case {i + 1} ({tested_field}): visit_date should be in form errors"
    )
    assert tested_field in form.errors, (
        f"Test case {i + 1} ({tested_field}): {tested_field} should be in form errors"
    )


@pytest.mark.django_db
def test_carb_counting_date_outside_of_audit_year_passes_validation_if_patient_diagnosed_before_audit_year():
    audit_period = AuditPeriod.objects.create(
        start_date=datetime.date(2024, 4, 1),
        end_date=datetime.date(2025, 3, 31),
        is_open=True,
        is_visible=True,
    )

    patient = PatientFactory()
    patient.diagnosis_date = datetime.date(2023, 1, 1)
    patient.save()

    form = VisitForm(
        data={
            "visit_date": "2025-01-01",  # Required for validation
            "carbohydrate_counting_level_three_education_date": "2024-01-01",
        },
        initial={"patient": patient},
        audit_period=audit_period,
    )

    assert form.is_valid()


@pytest.mark.django_db
def test_thyroid_and_coeliac_dates_within_90_days_before_diagnosis_pass_validation():
    patient = PatientFactory()
    patient.diagnosis_date = datetime.date(2026, 1, 10)
    patient.save()

    form = VisitForm(
        data={
            "visit_date": "2026-02-01",  # Required for validation
            "thyroid_treatment_status": 1,  # Required if thyroid function date provided
            "thyroid_function_date": "2025-12-7",  # 56 days before diagnosis
            "coeliac_screen_date": "2025-12-12",  # 51 days before diagnosis
        },
        initial={"patient": patient},
    )

    assert form.is_valid(), f"Expected form to be valid but got errors: {form.errors}"
    assert "thyroid_function_date" not in form.errors
    assert "coeliac_screen_date" not in form.errors


@pytest.mark.django_db
def test_thyroid_and_coeliac_dates_earlier_Than_90_days_before_diagnosis_fail_validation():
    patient = PatientFactory()
    patient.diagnosis_date = datetime.date(2026, 1, 10)
    patient.save()

    form = VisitForm(
        data={
            "visit_date": "2026-02-01",  # Required for validation
            "thyroid_treatment_status": 1,  # Required if thyroid function date provided
            "thyroid_function_date": "2025-10-04",  # 120 days before diagnosis
            "coeliac_screen_date": "2025-09-20",  # 134 days before diagnosis
        },
        initial={"patient": patient},
    )

    assert not form.is_valid()
    assert "thyroid_function_date" in form.errors
    assert "coeliac_screen_date" in form.errors
