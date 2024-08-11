# Standard imports
from datetime import date, timedelta
import pytest
import logging

# 3rd Party imports
from django.core.exceptions import ValidationError

# NPDA Imports
from project.npda.tests.factories import PatientFactory
from project.constants import (
    ETHNICITIES,
    DIABETES_TYPES,
    SEX_TYPE,
)

# Logging
logger = logging.getLogger(__name__)


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


@pytest.mark.skip(
    reason="Need to discuss model-level validation for future dates of birth"
)
@pytest.mark.django_db
def test_patient_creation_with_future_date_of_birth_raises_error():
    """Test creating a Patient with a future date of birth raises ValidationError."""
    future_date = date.today() + timedelta(days=1)
    with pytest.raises(ValidationError):
        PatientFactory(date_of_birth=future_date)


@pytest.mark.skip(reason="Need to discuss model-level validation for age constraints")
@pytest.mark.django_db
def test_patient_creation_with_over_19_years_old_date_of_birth_raises_error():
    """Test creating a Patient with a date of birth over or equal to 19 years old raises ValidationError."""
    over_19_years_date = date.today() - timedelta(days=365 * 19)
    with pytest.raises(ValidationError):
        PatientFactory(date_of_birth=over_19_years_date)


@pytest.mark.django_db
def test_patient_creation_without_diabetes_type_raises_error():
    """Test creating a Patient without a diabetes type raises ValidationError."""
    with pytest.raises(ValidationError):
        PatientFactory(diabetes_type=None)


@pytest.mark.skip(reason="Need to discuss model-level validation for diabetes type")
@pytest.mark.django_db
def test_patient_creation_with_invalid_diabetes_type_raises_error():
    """Test creating a Patient with an invalid diabetes type raises ValidationError."""
    with pytest.raises(ValidationError):
        PatientFactory(diabetes_type=DIABETES_TYPE_INVALID)


@pytest.mark.django_db
def test_patient_creation_without_date_of_diagnosis_raises_error():
    """Test creating a Patient without a date of diagnosis raises ValidationError."""
    with pytest.raises(ValidationError):
        PatientFactory(diagnosis_date=None)


@pytest.mark.skip(
    reason="Need to discuss model-level validation for future diagnosis dates"
)
@pytest.mark.django_db
def test_patient_creation_with_future_date_of_diagnosis_raises_error():
    """Test creating a Patient with a future date of diagnosis raises ValidationError."""
    future_date = date.today() + timedelta(days=1)
    with pytest.raises(ValidationError):
        PatientFactory(diagnosis_date=future_date)


@pytest.mark.skip(
    reason="Need to discuss model-level validation for diagnosis date vs birth date"
)
@pytest.mark.django_db
def test_patient_creation_with_date_of_diagnosis_before_date_of_birth_raises_error():
    """Test creating a Patient with a date of diagnosis before the date of birth raises ValidationError."""
    birth_date = date(2005, 1, 1)
    diagnosis_date = date(2004, 12, 31)
    with pytest.raises(ValidationError):
        PatientFactory(date_of_birth=birth_date, diagnosis_date=diagnosis_date)


@pytest.mark.skip(reason="Need to discuss model-level validation for postcode format")
@pytest.mark.django_db
def test_patient_creation_with_invalid_postcode_raises_error():
    """Test creating a Patient with an invalid postcode raises ValidationError."""
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
    """Test creating a Patient with an invalid sex raises ValidationError."""
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
    """Test creating a Patient with an invalid ethnicity raises ValidationError."""
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
    """Test creating a Patient with an invalid death date raises ValidationError."""
    future_date = date.today() + timedelta(days=1)
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
    """Test creating a Patient with an invalid GP practice ODS code raises ValidationError."""
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
    """Test creating a Patient without a Paediatric Diabetes Unit instance raises ValidationError."""
    with pytest.raises(ValidationError):
        PatientFactory(transfer=None)
