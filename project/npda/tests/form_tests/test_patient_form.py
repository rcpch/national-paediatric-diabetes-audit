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
SEX_TYPE_INVALID = 45
ETHNICITY_INVALID = "45"
DIABETES_TYPE_INVALID = 45
VALID_POSTCODE = "NW1 2DB"
GP_PRACTICE_ODS_CODE_VALID = 'G85023'


# TODO: keep tests in patient for catasrophic failures to save
# TODO: remove validators from patient model
# TODO: move network calls (IMD, postcode, GP details) to separate function


@pytest.mark.django_db
def test_create_patient():
    date_of_birth = TODAY - relativedelta(years=10)
    diagnosis_date = date_of_birth + relativedelta(years=8)

    form = PatientForm({
        "nhs_number": NHS_NUMBER_VALID,
        "sex": SEX_TYPE_VALID,
        "date_of_birth": date_of_birth,
        "postcode": VALID_POSTCODE,
        "ethnicity": ETHNICITY_VALID,
        "diabetes_type": DIABETES_TYPE_VALID,
        "diagnosis_date": diagnosis_date,
        "gp_practice_ods_code": GP_PRACTICE_ODS_CODE_VALID
    })

    assert(len(form.errors.as_data()) == 0)


@pytest.mark.django_db
def test_create_patient_with_death_date():
    date_of_birth = TODAY - relativedelta(years=10)
    diagnosis_date = date_of_birth + relativedelta(years=8)
    death_date = diagnosis_date + relativedelta(years=1)

    form = PatientForm({
        "nhs_number": NHS_NUMBER_VALID,
        "sex": SEX_TYPE_VALID,
        "date_of_birth": date_of_birth,
        "postcode": VALID_POSTCODE,
        "ethnicity": ETHNICITY_VALID,
        "diabetes_type": DIABETES_TYPE_VALID,
        "diagnosis_date": diagnosis_date,
        "death_date": death_date,
        "gp_practice_ods_code": GP_PRACTICE_ODS_CODE_VALID
    })

    assert(len(form.errors.as_data()) == 0)


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


def test_missing_gp_details():
    form = PatientForm({})
    
    errors = form.errors.as_data()
    assert("gp_practice_ods_code" in errors)

    error_message = errors["gp_practice_ods_code"][0].messages[0]
    assert(error_message == "'GP Practice ODS code' and 'GP Practice postcode' cannot both be empty")


def test_patient_creation_with_future_death_date_raises_error():
    form = PatientForm({
        "death_date": TODAY + relativedelta(years=1)
    })

    assert("death_date" in form.errors.as_data())


def test_patient_creation_with_death_date_before_date_of_birth_raises_error():
    date_of_birth = TODAY - relativedelta(years=1)

    form = PatientForm({
        "date_of_birth": date_of_birth,
        "death_date": date_of_birth - relativedelta(years=1)
    })

    errors = form.errors.as_data()
    assert("death_date" in errors)

    error_message = errors["death_date"][0].messages[0]
    assert(error_message == "'Death Date' cannot be before 'Date of Birth'")

