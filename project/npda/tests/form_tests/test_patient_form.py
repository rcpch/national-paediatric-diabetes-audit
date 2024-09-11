# Standard imports
from datetime import date, timedelta
from enum import Enum
import pytest
import logging
from unittest.mock import patch, Mock

# 3rd Party imports
from django.core.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from requests import RequestException

# NPDA Imports
from project.npda.tests.factories import PatientFactory
from project.constants import (
    ETHNICITIES,
    DIABETES_TYPES,
    SEX_TYPE,
)
from project.npda.models.patient import Patient
from project.npda.forms.patient_form import PatientForm, PatientFormWithSynchronousValidators
from project.npda import general_functions

# Logging
logger = logging.getLogger(__name__)

TODAY = date.today()
DATE_OF_BIRTH = TODAY - relativedelta(years=10)

VALID_FIELDS = {
    "nhs_number": "6239431915",
    "sex": SEX_TYPE[0][0],
    "date_of_birth": TODAY - relativedelta(years=10),
    "postcode": "NW1 2DB",
    "ethnicity":  ETHNICITIES[0][0],
    "diabetes_type":  DIABETES_TYPES[0][0],
    "diagnosis_date": DATE_OF_BIRTH + relativedelta(years=8),
    "gp_practice_ods_code": "G85023"
}

VALID_FIELDS_WITH_GP_POSTCODE = VALID_FIELDS | {
    "gp_practice_ods_code": None,
    "gp_practice_postcode": "SE13 5PJ"
}


# We don't want to call remote services unexpectedly during unit tests
@pytest.fixture(autouse=True)
def patch_validate_postcode():
    with patch('project.npda.forms.patient_form.validate_postcode', Mock(side_effect=Exception("Unexpected call to validate_postcode"))) as _mock:
        yield _mock

@pytest.fixture(autouse=True)
def patch_gp_ods_code_for_postcode():
    with patch('project.npda.forms.patient_form.gp_ods_code_for_postcode', Mock(side_effect=Exception("Unexpected call to gp_ods_code_for_postcode"))) as _mock:
        yield _mock

@pytest.fixture(autouse=True)
def patch_gp_details_for_ods_code():
    with patch('project.npda.forms.patient_form.gp_details_for_ods_code', Mock(side_effect=Exception("Unexpected call to gp_details_for_ods_code"))) as _mock:
        yield _mock

@pytest.fixture(autouse=True)
def patch_imd_for_postcode():
    with patch('project.npda.forms.patient_form.imd_for_postcode', Mock(side_effect=Exception("Unexpected call to imd_for_postcode"))) as _mock:
        yield _mock


@pytest.mark.django_db
def test_create_patient():
    form = PatientForm(VALID_FIELDS)
    assert(len(form.errors.as_data()) == 0)


@pytest.mark.django_db
def test_create_patient_with_death_date():
    form = PatientForm(VALID_FIELDS | {
        "death_date": VALID_FIELDS["diagnosis_date"] + relativedelta(years=1)
    })

    assert(len(form.errors.as_data()) == 0)


def test_missing_nhs_number():
    form = PatientForm({})
    assert("nhs_number" in form.errors.as_data())


def test_invalid_nhs_number():
    form = PatientForm({
        "nhs_number": "123456789"
    })

    assert("nhs_number" in form.errors.as_data())


def test_date_of_birth_missing():
    form = PatientForm({})
    assert("date_of_birth" in form.errors.as_data())


def test_future_date_of_birth():
    form = PatientForm({
        "date_of_birth": TODAY + timedelta(days=1)
    })

    errors = form.errors.as_data()
    assert("date_of_birth" in errors)

    error_message = errors["date_of_birth"][0].messages[0]
    assert(error_message == "'Date of Birth' cannot be in the future")


def test_over_25():
    form = PatientForm({
        "date_of_birth": TODAY - relativedelta(years=25, days=1)
    })

    errors = form.errors.as_data()
    assert("date_of_birth" in errors)

    error_message = errors["date_of_birth"][0].messages[0]
    assert(error_message == "NPDA patients cannot be 25+ years old. This patient is 25")


def test_missing_diabetes_type():
    form = PatientForm({})
    assert("diabetes_type" in form.errors.as_data())


def test_invalid_diabetes_type():
    form = PatientForm({
        "diabetes_type": 45
    })

    assert("diabetes_type" in form.errors.as_data())


def test_missing_diagnosis_date():
    form = PatientForm({})
    assert("diagnosis_date" in form.errors.as_data())


def test_future_diagnosis_date():
    form = PatientForm({
        "diagnosis_date": TODAY + timedelta(days=1)
    })

    errors = form.errors.as_data()
    assert("diagnosis_date" in errors)

    error_message = errors["diagnosis_date"][0].messages[0]
    assert(error_message == "'Diagnosis Date' cannot be in the future")


def test_diagnosis_date_before_date_of_birth():
    form = PatientForm({
        "date_of_birth": VALID_FIELDS["date_of_birth"],
        "diagnosis_date": VALID_FIELDS["date_of_birth"] - relativedelta(years=1)
    })

    errors = form.errors.as_data()
    assert("diagnosis_date" in errors)

    error_message = errors["diagnosis_date"][0].messages[0]
    assert(error_message == "'Date of Diabetes Diagnosis' cannot be before 'Date of Birth'")


def test_invalid_sex():
    form = PatientForm({
        "sex": 45
    })

    assert("sex" in form.errors.as_data())


def test_invalid_ethnicity():
    form = PatientForm({
        "ethnicity": 45
    })

    assert("ethnicity" in form.errors.as_data())


def test_missing_gp_details():
    form = PatientForm({})
    
    errors = form.errors.as_data()
    assert("gp_practice_ods_code" in errors)

    error_message = errors["gp_practice_ods_code"][0].messages[0]
    assert(error_message == "'GP Practice ODS code' and 'GP Practice postcode' cannot both be empty")


def test_patient_creation_with_future_death_date():
    form = PatientForm({
        "death_date": TODAY + relativedelta(years=1)
    })

    errors = form.errors.as_data()
    assert("death_date" in errors)

    error_message = errors["death_date"][0].messages[0]
    assert(error_message == "'Death Date' cannot be in the future")


def test_patient_creation_with_death_date_before_date_of_birth():
    form = PatientForm({
        "date_of_birth": VALID_FIELDS["date_of_birth"],
        "death_date": VALID_FIELDS["date_of_birth"] - relativedelta(years=1)
    })

    errors = form.errors.as_data()
    assert("death_date" in errors)

    error_message = errors["death_date"][0].messages[0]
    assert(error_message == "'Death Date' cannot be before 'Date of Birth'")


@pytest.mark.django_db
def test_spaces_removed_from_postcode():
    form = PatientForm(VALID_FIELDS | {
        "postcode": "WC1X 8SH",
    })

    form.is_valid()
    assert(form.cleaned_data["postcode"] == "WC1X8SH")


@pytest.mark.django_db
def test_dashes_removed_from_postcode():
    form = PatientForm(VALID_FIELDS | {
        "postcode": "WC1X-8SH",
    })

    form.is_valid()
    assert(form.cleaned_data["postcode"] == "WC1X8SH")


@pytest.mark.django_db
@patch('project.npda.forms.patient_form.validate_postcode', Mock(return_value=True))
@patch('project.npda.forms.patient_form.gp_details_for_ods_code', Mock(return_value=True))
def test_valid_postcode():
    form = PatientFormWithSynchronousValidators(VALID_FIELDS)

    form.is_valid()
    assert(len(form.errors.as_data()) == 0)


@pytest.mark.django_db
@patch('project.npda.forms.patient_form.validate_postcode', Mock(return_value=False))
@patch('project.npda.forms.patient_form.gp_details_for_ods_code', Mock(return_value=True))
def test_invalid_postcode():
    form = PatientFormWithSynchronousValidators(VALID_FIELDS)

    form.is_valid()
    assert("postcode" in form.errors.as_data())


@pytest.mark.django_db
@patch('project.npda.forms.patient_form.validate_postcode', Mock(side_effect=RequestException("oopsie!")))
@patch('project.npda.forms.patient_form.gp_details_for_ods_code', Mock(return_value=True))
def test_error_validating_postcode():
    # TODO MRB: report this back somehow rather than just eat it in the log?
    form = PatientFormWithSynchronousValidators(VALID_FIELDS)

    form.is_valid()
    assert(len(form.errors.as_data()) == 0)


@pytest.mark.django_db
@patch('project.npda.forms.patient_form.validate_postcode', Mock(return_value=True))
@patch('project.npda.forms.patient_form.gp_ods_code_for_postcode', Mock(return_value=VALID_FIELDS["gp_practice_ods_code"]))
def test_valid_gp_postcode():
    form = PatientFormWithSynchronousValidators(VALID_FIELDS_WITH_GP_POSTCODE)

    form.is_valid()
    assert(len(form.errors.as_data()) == 0)


@pytest.mark.django_db
@patch('project.npda.forms.patient_form.validate_postcode', Mock(return_value=True))
@patch('project.npda.forms.patient_form.gp_ods_code_for_postcode', Mock(return_value=None))
def test_invalid_gp_postcode():
    form = PatientFormWithSynchronousValidators(VALID_FIELDS_WITH_GP_POSTCODE)

    form.is_valid()
    assert("gp_practice_postcode" in form.errors.as_data())


@pytest.mark.django_db
@patch('project.npda.forms.patient_form.validate_postcode', Mock(return_value=True))
@patch('project.npda.forms.patient_form.gp_ods_code_for_postcode', Mock(side_effect=RequestException("oopsie!")))
def test_error_validating_gp_postcode():
    # TODO MRB: report this back somehow rather than just eat it in the log?
    form = PatientFormWithSynchronousValidators(VALID_FIELDS_WITH_GP_POSTCODE)

    form.is_valid()
    assert(len(form.errors.as_data()) == 0)


@pytest.mark.django_db
@patch('project.npda.forms.patient_form.validate_postcode', Mock(return_value=True))
@patch('project.npda.forms.patient_form.gp_details_for_ods_code', Mock(return_value=True))
def test_valid_gp_ods_code():
    form = PatientFormWithSynchronousValidators(VALID_FIELDS)

    form.is_valid()
    assert(len(form.errors.as_data()) == 0)


@pytest.mark.django_db
@patch('project.npda.forms.patient_form.validate_postcode', Mock(return_value=True))
@patch('project.npda.forms.patient_form.gp_details_for_ods_code', Mock(return_value=None))
def test_invalid_gp_ods_code():
    form = PatientFormWithSynchronousValidators(VALID_FIELDS)

    form.is_valid()
    assert("gp_practice_ods_code" in form.errors.as_data())


@pytest.mark.django_db
@patch('project.npda.forms.patient_form.validate_postcode', Mock(return_value=True))
@patch('project.npda.forms.patient_form.gp_details_for_ods_code', Mock(side_effect=RequestException("oopsie!")))
def test_error_validating_gp_ods_code():
    # TODO MRB: report this back somehow rather than just eat it in the log?
    form = PatientFormWithSynchronousValidators(VALID_FIELDS)

    form.is_valid()
    assert(len(form.errors.as_data()) == 0)


@pytest.mark.django_db
@patch('project.npda.forms.patient_form.validate_postcode', Mock(return_value=True))
@patch('project.npda.forms.patient_form.gp_details_for_ods_code', Mock(return_value=True))
@patch('project.npda.forms.patient_form.imd_for_postcode', Mock(return_value=4))
def test_lookup_index_of_multiple_deprivation():
    form = PatientFormWithSynchronousValidators(VALID_FIELDS)

    form.is_valid()
    assert(len(form.errors.as_data()) == 0)

    patient = form.save()
    assert(patient.index_of_multiple_deprivation_quintile == 4)


@pytest.mark.django_db
@patch('project.npda.forms.patient_form.validate_postcode', Mock(return_value=True))
@patch('project.npda.forms.patient_form.gp_details_for_ods_code', Mock(return_value=True))
@patch('project.npda.forms.patient_form.imd_for_postcode', Mock(side_effect=RequestException("oopsie!")))
def test_error_looking_up_index_of_multiple_deprivation():
    # TODO MRB: report this back somehow rather than just eat it in the log?
    form = PatientFormWithSynchronousValidators(VALID_FIELDS)

    patient = form.save()
    patient.index_of_multiple_deprivation_quintile = None