# Standard imports
from datetime import date, timedelta
from enum import Enum
import pytest
import logging
from unittest.mock import patch

# 3rd Party imports
from django.core.exceptions import ValidationError

# NPDA Imports
from project.npda.tests.factories import PatientFactory
from project.constants import (
    ETHNICITIES,
    DIABETES_TYPES,
    SEX_TYPE,
)
from project.npda.models.patient import Patient, PatientError

# Logging
logger = logging.getLogger(__name__)

# Constants
DATE_OF_BIRTH = date(2024, 1, 1)
TODAY = date.today()

# Helper functions
def check_error_field_has_errors(model_instance, field_name:str, error_enums:list[str]):
    """
    Check that the specified error enum is in the errors field for the specified field.

    Args:
        model_instance: The model instance to check.
        field_name: The name of the field to check.
        error_enum: The error enum to check for.
    """
    
    # Firstly, if model.errors is None, that means no errors have been added
    # so we can return False
    if model_instance.errors is None:
        return False
    
    # Check if the field_name is in the errors field
    assert field_name in model_instance.errors
    
    # Using set as order of errors does not matter
    return set(error_enums) == set(model_instance.errors[field_name])


@pytest.mark.django_db
@patch.object(
    Patient, "get_todays_date", return_value=DATE_OF_BIRTH - timedelta(days=10)
)
def test_age_days_before_birth(mock_get_todays_date):
    """Test .age_days() method when the current date is before the date of birth."""
    # Create a patient instance with a specific date of birth
    patient = Patient(date_of_birth=DATE_OF_BIRTH)

    # Call the method and assert the expected result
    expected_days = (mock_get_todays_date.return_value - patient.date_of_birth).days
    assert patient.age_days() == expected_days


@pytest.mark.django_db
@patch.object(Patient, "get_todays_date", return_value=DATE_OF_BIRTH)
def test_age_days_on_birth_date(mock_get_todays_date):
    """Test .age_days() method when the current date is the date of birth."""
    # Create a patient instance with a specific date of birth
    patient = Patient(date_of_birth=DATE_OF_BIRTH)

    # Call the method and assert the expected result
    expected_days = 0
    assert patient.age_days() == expected_days


@pytest.mark.django_db
@patch.object(
    Patient, "get_todays_date", return_value=DATE_OF_BIRTH + timedelta(days=365)
)
def test_age_days_after_birth(mock_get_todays_date):
    """Test .age_days() method when the current date is after the date of birth."""
    # Create a patient instance with a specific date of birth
    patient = Patient(date_of_birth=DATE_OF_BIRTH)

    # Call the method and assert the expected result
    expected_days = 365
    assert patient.age_days() == expected_days


@pytest.mark.django_db
@patch.object(Patient, "get_todays_date", return_value=date(2021, 2, 28))
def test_age_days_on_leap_year(mock_get_todays_date):
    """Test .age_days() method for a leap year scenario."""
    # Create a patient instance with a specific date of birth
    leap_birth_date = date(2020, 2, 29)
    patient = Patient(date_of_birth=leap_birth_date)

    # Call the method and assert the expected result
    expected_days = (mock_get_todays_date.return_value - patient.date_of_birth).days
    assert patient.age_days() == expected_days


@pytest.mark.django_db
@patch.object(Patient, "get_todays_date", return_value=date(2024, 2, 29))
def test_age_days_on_next_leap_year(mock_get_todays_date):
    """Test .age_days() method for a leap year scenario, crossing into a new leap year."""
    # Create a patient instance with a specific date of birth
    leap_birth_date = date(2020, 2, 29)
    patient = Patient(date_of_birth=leap_birth_date)

    # Call the method and assert the expected result
    expected_days = (mock_get_todays_date.return_value - patient.date_of_birth).days
    assert patient.age_days() == expected_days


# NHS NUMBER TESTS
@pytest.fixture
def valid_nhs_number():
    """Provide a valid NHS number using the factory."""
    return PatientFactory().nhs_number


@pytest.fixture
def invalid_nhs_number():
    """Provide an invalid NHS number for testing."""
    return "123456789"


@pytest.mark.django_db
def test_patient_creation_without_nhs_number_raises_error():
    """Test creating a Patient without an NHS number raises ValidationError."""
    with pytest.raises(ValidationError):
        PatientFactory(nhs_number=None)


@pytest.mark.django_db
def test_patient_creation_with_invalid_nhs_number_raises_error(invalid_nhs_number):
    """Test creating a Patient with an invalid NHS number raises ValidationError."""
    with pytest.raises(ValidationError):
        PatientFactory(nhs_number=invalid_nhs_number)


@pytest.mark.django_db
def test_patient_creation_with_duplicate_nhs_number_raises_error():
    """Test creating a Patient with a duplicate NHS number raises ValidationError."""
    duplicate_nhs_number = PatientFactory().nhs_number
    with pytest.raises(ValidationError):
        PatientFactory(nhs_number=duplicate_nhs_number)


# Constants for below tests
SEX_TYPE_VALID = SEX_TYPE[0][0]
ETHNICITY_VALID = ETHNICITIES[0][0]
DIABETES_TYPE_VALID = DIABETES_TYPES[0][0]
VALID_POSTCODE = "NW1 2DB"
SEX_TYPE_INVALID = 45
ETHNICITY_INVALID = "45"
DIABETES_TYPE_INVALID = 45
INVALID_POSTCODE = "!!@@##"
UNKNOWN_POSTCODE = "ZZ99 45"


@pytest.mark.django_db
def test_patient_creation_without_date_of_birth_raises_error():
    """Test creating a Patient without a date of birth raises ValidationError."""
    with pytest.raises(ValidationError):
        PatientFactory(date_of_birth=None)


@pytest.mark.django_db
def test_patient_creation_with_future_date_of_birth_raises_error():
    """Test creating a Patient with a future date of birth creates an error item."""
    future_date = TODAY + timedelta(days=1)
    new_patient = PatientFactory(date_of_birth=future_date)
    
    assert check_error_field_has_errors(new_patient, 'date_of_birth', [PatientError.DOB_IN_FUTURE.name]), "Error not raised for future date of birth"


@pytest.mark.django_db
def test_patient_creation_with_over_19_years_old_date_of_birth_raises_error():
    """Test creating a Patient with a date of birth over or equal to 19 years old creates an error item."""
    # 1 day over 19
    over_19_years_date = TODAY - timedelta(days=(1 + (365 * 19)))
    new_patient = PatientFactory(date_of_birth=over_19_years_date)
    
    age_in_days = new_patient.age_days()
    
    assert check_error_field_has_errors(new_patient, 'date_of_birth', [PatientError.PT_OLDER_THAN_19yo.name]), f"Error not raised for patient over 19 years old ({age_in_days / 19=})"


@pytest.mark.django_db
def test_patient_creation_without_diabetes_type_raises_error():
    """Test creating a Patient without a diabetes type creates an error item."""
    with pytest.raises(ValidationError):
        PatientFactory(diabetes_type=None)

@pytest.mark.django_db
def test_patient_creation_with_invalid_diabetes_type_raises_error():
    """Test creating a Patient with an invalid diabetes type creates an error item."""
    
    new_patient = PatientFactory(diabetes_type=DIABETES_TYPE_INVALID)
    
    assert check_error_field_has_errors(new_patient, 'diabetes_type', [PatientError.INVALID_DIABETES_TYPE.name]), "Error not raised for invalid diabetes type"


@pytest.mark.django_db
def test_patient_creation_without_date_of_diagnosis_raises_error():
    """Test creating a Patient without a date of diagnosis creates an error item."""
    with pytest.raises(ValidationError):
        PatientFactory(diagnosis_date=None)


@pytest.mark.skip(
    reason="Need to discuss model-level validation for future diagnosis dates"
)
@pytest.mark.django_db
def test_patient_creation_with_future_date_of_diagnosis_raises_error():
    """Test creating a Patient with a future date of diagnosis creates an error item."""
    future_date = TODAY + timedelta(days=1)
    with pytest.raises(ValidationError):
        PatientFactory(diagnosis_date=future_date)


@pytest.mark.skip(
    reason="Need to discuss model-level validation for diagnosis date vs birth date"
)
@pytest.mark.django_db
def test_patient_creation_with_date_of_diagnosis_before_date_of_birth_raises_error():
    """Test creating a Patient with a date of diagnosis before the date of birth creates an error item."""
    birth_date = date(2005, 1, 1)
    diagnosis_date = date(2004, 12, 31)
    with pytest.raises(ValidationError):
        PatientFactory(date_of_birth=birth_date, diagnosis_date=diagnosis_date)


@pytest.mark.skip(reason="Need to discuss model-level validation for postcode format")
@pytest.mark.django_db
def test_patient_creation_with_invalid_postcode_raises_error():
    """Test creating a Patient with an invalid postcode creates an error item."""
    with pytest.raises(ValidationError):
        PatientFactory(postcode=INVALID_POSTCODE)


@pytest.mark.django_db
def test_patient_creation_with_valid_index_of_multiple_deprivation():
    """Test creating a Patient with valid details including a valid index of multiple deprivation."""
    patient = PatientFactory()
    assert patient.index_of_multiple_deprivation_quintile is not None


@pytest.mark.django_db
def test_patient_creation_with_unknown_postcode_sets_index_of_multiple_deprivation_to_none():
    """Test that if an index of multiple deprivation quintile cannot be calculated, it is set to None."""
    patient = PatientFactory(postcode=UNKNOWN_POSTCODE)
    assert patient.index_of_multiple_deprivation_quintile is None


@pytest.mark.django_db
def test_patient_creation_with_valid_sex():
    """Test creating a Patient with a valid sex does not raise an error."""
    try:
        PatientFactory(sex=SEX_TYPE_VALID)
    except ValidationError:
        pytest.fail("ValidationError raised for a valid sex")


@pytest.mark.skip(reason="Need to discuss model-level validation for sex type")
@pytest.mark.django_db
def test_patient_creation_with_invalid_sex_raises_error():
    """Test creating a Patient with an invalid sex creates an error item."""
    with pytest.raises(ValidationError):
        PatientFactory(sex=SEX_TYPE_INVALID)


@pytest.mark.django_db
def test_patient_creation_with_valid_ethnicity():
    """Test creating a Patient with a valid ethnicity does not raise an error."""
    try:
        PatientFactory(ethnicity=ETHNICITY_VALID)
    except ValidationError:
        pytest.fail("ValidationError raised for a valid ethnicity")


@pytest.mark.skip(reason="Need to discuss model-level validation for ethnicity")
@pytest.mark.django_db
def test_patient_creation_with_invalid_ethnicity_raises_error():
    """Test creating a Patient with an invalid ethnicity creates an error item."""
    with pytest.raises(ValidationError):
        PatientFactory(ethnicity=ETHNICITY_INVALID)


@pytest.mark.django_db
def test_patient_creation_with_valid_death_date():
    """Test creating a Patient with a valid death date does not raise an error."""
    try:
        PatientFactory(
            death_date=date(2024, 1, 1)
        )  # Ensure this is valid for your context
    except ValidationError:
        pytest.fail("ValidationError raised for a valid death date")


@pytest.mark.skip(
    reason="Need to discuss model-level validation for future death dates"
)
@pytest.mark.django_db
def test_patient_creation_with_invalid_death_date_raises_error():
    """Test creating a Patient with an invalid death date creates an error item."""
    future_date = TODAY + timedelta(days=1)
    with pytest.raises(ValidationError):
        PatientFactory(death_date=future_date)


@pytest.mark.django_db
def test_patient_creation_with_valid_gp_practice_ods_code():
    """Test creating a Patient with a valid GP practice ODS code does not raise an error."""
    try:
        PatientFactory(gp_practice_ods_code="RP401")  # Assuming 'RP401' is valid
    except ValidationError:
        pytest.fail("ValidationError raised for a valid GP practice ODS code")


@pytest.mark.skip(reason="Need to discuss model-level validation for ODS code")
@pytest.mark.django_db
def test_patient_creation_with_invalid_gp_practice_ods_code_raises_error():
    """Test creating a Patient with an invalid GP practice ODS code creates an error item."""
    with pytest.raises(ValidationError):
        PatientFactory(gp_practice_ods_code="@@@@@@")


@pytest.mark.django_db
def test_patient_creation_with_pdu_instance():
    """Test creating a Patient with a Paediatric Diabetes Unit instance associated does not raise an error."""
    try:
        PatientFactory(
            transfer__paediatric_diabetes_unit__pz_code="VALID_PZ"
        )  # Ensure 'VALID_PZ' is valid
    except ValidationError:
        pytest.fail("ValidationError raised for a valid PDU association")


@pytest.mark.skip(reason="Need to discuss model-level validation for PDU association")
@pytest.mark.django_db
def test_patient_creation_without_pdu_instance_raises_error():
    """Test creating a Patient without a Paediatric Diabetes Unit instance creates an error item."""
    with pytest.raises(ValidationError):
        PatientFactory(transfer=None)
