# Standard imports
from datetime import date, timedelta
from enum import Enum
import pytest
import logging
from unittest.mock import patch, Mock

# 3rd Party imports
from django.core.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

# NPDA Imports
from project.npda.tests.factories import PatientFactory
from project.constants import (
    ETHNICITIES,
    DIABETES_TYPES,
    SEX_TYPE,
)
from project.npda.models.patient import Patient
from project.npda.forms.patient_form import PatientForm
from project.npda import general_functions

# Logging
logger = logging.getLogger(__name__)

# Constants
TODAY = date.today()
NHS_NUMBER_VALID = "6239431915"
NHS_NUMBER_INVALID = "123456789"
SEX_TYPE_VALID = SEX_TYPE[0][0]
ETHNICITY_VALID = ETHNICITIES[0][0]
DIABETES_TYPE_VALID = DIABETES_TYPES[0][0]
VALID_POSTCODE = "NW1 2DB"
SEX_TYPE_INVALID = 45
ETHNICITY_INVALID = "45"
DIABETES_TYPE_INVALID = 45
INVALID_POSTCODE = "!!@@##"
UNKNOWN_POSTCODE = "ZZ99 45"
INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE = 1
GP_PRACTICE_ODS_CODE_VALID = 'G85023'
GP_PRACTICE_POSTCODE_VALID = 'SE13 5PJ'
GP_PRACTICE_ODS_CODE_INVALID = '@@@@@@'


# TODO: valid create
# TODO: keep tests in patient for catasrophic failures to save
# TODO: remove validators from patient model
# TODO: move network calls (IMD, postcode, GP details) to separate function


def test_missing_nhs_number():
    form = PatientForm({})
    assert("nhs_number" in form.errors.as_data())


def test_invalid_nhs_number():
    form = PatientForm({
        "nhs_number": NHS_NUMBER_INVALID
    })

    assert("nhs_number" in form.errors.as_data())


def test_date_of_birth_missing():
    form = PatientForm({})
    assert("date_of_birth" in form.errors.as_data())


def test_future_date_of_birth():
    form = PatientForm({
        "date_of_birth": TODAY + timedelta(days=1)
    })

    assert("date_of_birth" in form.errors.as_data())


def test_over_19():
    form = PatientForm({
        "date_of_birth": TODAY - relativedelta(years=19, days=1)
    })

    errors = form.errors.as_data()
    assert("date_of_birth" in errors)

    error_message = errors["date_of_birth"][0].messages[0]
    assert(error_message == "NPDA patients cannot be 19+ years old. This patient is 19")


def test_missing_diabetes_type():
    form = PatientForm({})
    assert("diabetes_type" in form.errors.as_data())


def test_invalid_diabetes_type():
    form = PatientForm({
        "diabetes_type": DIABETES_TYPE_INVALID
    })

    assert("diabetes_type" in form.errors.as_data())


def test_missing_diagnosis_date():
    form = PatientForm({})
    assert("diagnosis_date" in form.errors.as_data())


def test_future_diagnosis_date():
    form = PatientForm({
        "diagnosis_date": TODAY + timedelta(days=1)
    })

    assert("diagnosis_date" in form.errors.as_data())


def test_diagnosis_date_before_date_of_birth():
    date_of_birth = TODAY - relativedelta(years = 12)
    diagnosis_date = date_of_birth - relativedelta(years=1)

    form = PatientForm({
        "date_of_birth": date_of_birth,
        "diagnosis_date": diagnosis_date
    })

    errors = form.errors.as_data()
    assert("diagnosis_date" in errors)

    error_message = errors["diagnosis_date"][0].messages[0]
    assert(error_message == "'Date of Diabetes Diagnosis' cannot be before 'Date of Birth'")


def test_invalid_sex():
    form = PatientForm({
        "sex": SEX_TYPE_INVALID
    })

    assert("sex" in form.errors.as_data())


def test_invalid_ethnicity():
    form = PatientForm({
        "ethnicity": ETHNICITY_INVALID
    })

    assert("ethnicity" in form.errors.as_data())


# @pytest.mark.django_db
# def test_patient_creation_with_valid_death_date():
#     death_date = PatientFactory().date_of_birth + relativedelta(years=1)

#     patient = PatientFactory(death_date=death_date)
#     assert(patient.death_date == death_date)


# @pytest.mark.django_db
# def test_patient_creation_with_future_death_date_raises_error():
#     death_date = TODAY + relativedelta(years=1)

#     with pytest.raises(ValidationError):
#         PatientFactory(death_date=death_date)


# @pytest.mark.django_db
# def test_patient_creation_with_death_date_before_date_of_birth_raises_error():
#     death_date = PatientFactory().date_of_birth - relativedelta(years=1)

#     with pytest.raises(ValidationError):
#         PatientFactory(death_date=death_date)


# @pytest.mark.django_db
# def test_patient_creation_with_valid_gp_practice_ods_code():
#     patient = PatientFactory(gp_practice_ods_code=GP_PRACTICE_ODS_CODE_VALID)
    
#     assert(patient.gp_practice_ods_code == GP_PRACTICE_ODS_CODE_VALID)


# @pytest.mark.django_db
# @patch('project.npda.models.patient.gp_details_for_ods_code', Mock(return_value=None))
# def test_patient_creation_with_invalid_gp_practice_ods_code_raises_error():
#     with pytest.raises(ValidationError):
#         PatientFactory(gp_practice_ods_code="@@@@@@")


# @pytest.mark.django_db
# @patch('project.npda.models.patient.gp_ods_code_for_postcode', Mock(side_effect=Exception('oopsie')))
# def test_patient_creation_gp_practice_ods_code_lookup_failure():
#     patient = PatientFactory(gp_practice_ods_code=GP_PRACTICE_ODS_CODE_VALID)
    
#     assert(patient.gp_practice_ods_code is GP_PRACTICE_ODS_CODE_VALID)


# @pytest.mark.django_db
# def test_patient_creation_with_valid_gp_practice_postcode():
#     patient = PatientFactory(
#         gp_practice_ods_code=None,
#         gp_practice_postcode=GP_PRACTICE_POSTCODE_VALID
#     )
    
#     assert(patient.gp_practice_ods_code == GP_PRACTICE_ODS_CODE_VALID)
#     assert(patient.gp_practice_postcode == GP_PRACTICE_POSTCODE_VALID)


# @pytest.mark.django_db
# @patch('project.npda.models.patient.gp_ods_code_for_postcode', Mock(side_effect=Exception('oopsie')))
# def test_patient_creation_with_gp_practice_postcode_lookup_failure():
#     patient = PatientFactory(
#         gp_practice_ods_code=None,
#         gp_practice_postcode=GP_PRACTICE_POSTCODE_VALID
#     )
    
#     assert(patient.gp_practice_ods_code == None)
#     assert(patient.gp_practice_postcode == GP_PRACTICE_POSTCODE_VALID)


# @pytest.mark.django_db
# @patch('project.npda.models.patient.gp_details_for_ods_code', Mock(return_value=[]))
# def test_patient_creation_with_gp_practice_postcode_that_isnt_a_gp_raises_error():
#     with pytest.raises(ValidationError):
#         PatientFactory(gp_practice_postcode="WC1X 8SH")

