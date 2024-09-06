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
from project.npda import general_functions

# Logging
logger = logging.getLogger(__name__)

# Constants
TODAY = date.today()
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

@pytest.fixture
def valid_nhs_number():
    """Provide a valid NHS number using the factory."""
    return PatientFactory().nhs_number


@pytest.fixture
def invalid_nhs_number():
    """Provide an invalid NHS number for testing."""
    return "123456789"

# We don't want to call remote services during unit tests
@pytest.fixture(autouse=True)
def patch_validate_postcode():
    with patch('project.npda.models.patient._validate_postcode') as _mock:
        yield _mock

@pytest.fixture(autouse=True)
def patch_imd_for_postcode():
    with patch('project.npda.models.patient.imd_for_postcode', return_value=INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE) as _mock:
        yield _mock

@pytest.fixture(autouse=True)
def patch_gp_ods_code_for_postcode():
    with patch('project.npda.models.patient.gp_ods_code_for_postcode', return_value=GP_PRACTICE_ODS_CODE_VALID) as _mock:
        yield _mock

@pytest.fixture(autouse=True)
def patch_gp_details_for_ods_code():
    with patch('project.npda.models.patient.gp_details_for_ods_code', return_value={"placeholder": 1234}) as _mock:
        yield _mock


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


@pytest.mark.django_db
def test_patient_creation_without_date_of_birth_raises_error():
    with pytest.raises(ValidationError):
        PatientFactory(date_of_birth=None)


@pytest.mark.django_db
def test_patient_creation_with_future_date_of_birth_raises_error():
    with pytest.raises(ValidationError) as exc_info:
        PatientFactory(date_of_birth=TODAY + timedelta(days=1))

    assert('date_of_birth' in exc_info.value.error_dict)


@pytest.mark.django_db
def test_patient_creation_with_over_19_years_old_date_of_birth_raises_error():
    # 1 day over 19
    over_19_years_date = TODAY - relativedelta(years=19, days=1)

    with pytest.raises(ValidationError) as exc_info:
        PatientFactory(date_of_birth=over_19_years_date)

    assert('date_of_birth' in exc_info.value.error_dict)

    error_message = exc_info.value.error_dict['date_of_birth'][0].messages[0]
    assert(error_message == "NPDA patients cannot be 19+ years old. This patient is 19")


@pytest.mark.django_db
def test_patient_creation_without_diabetes_type_raises_error():
    with pytest.raises(ValidationError) as exc_info:
        PatientFactory(diabetes_type=None)

    assert('diabetes_type' in exc_info.value.error_dict)


@pytest.mark.django_db
def test_patient_creation_with_invalid_diabetes_type_raises_error():
    with pytest.raises(ValidationError) as exc_info:
        PatientFactory(diabetes_type=DIABETES_TYPE_INVALID)

    assert('diabetes_type' in exc_info.value.error_dict)


@pytest.mark.django_db
def test_patient_creation_without_date_of_diagnosis_raises_error():
    with pytest.raises(ValidationError) as exc_info:
        PatientFactory(diagnosis_date=None)
    
    assert('diagnosis_date' in exc_info.value.error_dict)


@pytest.mark.django_db
def test_patient_creation_with_future_date_of_diagnosis_raises_error():
    with pytest.raises(ValidationError) as exc_info:
        PatientFactory(diagnosis_date=TODAY + timedelta(days=1))

    assert('diagnosis_date' in exc_info.value.error_dict)


@pytest.mark.django_db
def test_patient_creation_with_date_of_diagnosis_before_date_of_birth_raises_error():
    date_of_birth = PatientFactory().date_of_birth
    diagnosis_date = date_of_birth - relativedelta(years=1)

    with pytest.raises(ValidationError):
        PatientFactory(
            date_of_birth=date_of_birth,
            diagnosis_date=diagnosis_date
        )

@pytest.mark.django_db
@patch('project.npda.models.patient._validate_postcode', Mock(side_effect=ValidationError("Postcode invalid")))
def test_patient_creation_with_invalid_postcode_raises_error():
    with pytest.raises(ValidationError) as exc_info:
        PatientFactory(postcode=INVALID_POSTCODE)
    
    assert('postcode' in exc_info.value.error_dict)


@pytest.mark.django_db
def test_patient_creation_with_valid_index_of_multiple_deprivation():
    patient = PatientFactory()
    assert(patient.index_of_multiple_deprivation_quintile == INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE)


@pytest.mark.django_db
@patch('project.npda.models.patient.imd_for_postcode', Mock(side_effect=Exception('oopsie')))
def test_patient_creation_with_index_of_multiple_deprivation_lookup_failure():
    patient = PatientFactory()
    assert patient.index_of_multiple_deprivation_quintile is None


@pytest.mark.django_db
def test_patient_creation_with_valid_sex():
    patient = PatientFactory(sex=SEX_TYPE_VALID)
    assert(patient.sex == SEX_TYPE_VALID)


@pytest.mark.django_db
def test_patient_creation_with_invalid_sex_raises_error():
    with pytest.raises(ValidationError):
        PatientFactory(sex=SEX_TYPE_INVALID)


@pytest.mark.django_db
def test_patient_creation_with_valid_ethnicity():
    patient = PatientFactory(ethnicity=ETHNICITY_VALID)
    assert(patient.ethnicity == ETHNICITY_VALID)


@pytest.mark.django_db
def test_patient_creation_with_invalid_ethnicity_raises_error():
    """Test creating a Patient with an invalid ethnicity creates an error item."""
    with pytest.raises(ValidationError):
        PatientFactory(ethnicity=ETHNICITY_INVALID)


@pytest.mark.django_db
def test_patient_creation_with_valid_death_date():
    death_date = PatientFactory().date_of_birth + relativedelta(years=1)

    patient = PatientFactory(death_date=death_date)
    assert(patient.death_date == death_date)


@pytest.mark.django_db
def test_patient_creation_with_future_death_date_raises_error():
    death_date = TODAY + relativedelta(years=1)

    with pytest.raises(ValidationError):
        PatientFactory(death_date=death_date)


@pytest.mark.django_db
def test_patient_creation_with_death_date_before_date_of_birth_raises_error():
    death_date = PatientFactory().date_of_birth - relativedelta(years=1)

    with pytest.raises(ValidationError):
        PatientFactory(death_date=death_date)


@pytest.mark.django_db
def test_patient_creation_with_valid_gp_practice_ods_code():
    patient = PatientFactory(gp_practice_ods_code=GP_PRACTICE_ODS_CODE_VALID)
    
    assert(patient.gp_practice_ods_code == GP_PRACTICE_ODS_CODE_VALID)


@pytest.mark.django_db
@patch('project.npda.models.patient.gp_details_for_ods_code', Mock(return_value=None))
def test_patient_creation_with_invalid_gp_practice_ods_code_raises_error():
    with pytest.raises(ValidationError):
        PatientFactory(gp_practice_ods_code="@@@@@@")


@pytest.mark.django_db
@patch('project.npda.models.patient.gp_ods_code_for_postcode', Mock(side_effect=Exception('oopsie')))
def test_patient_creation_gp_practice_ods_code_lookup_failure():
    patient = PatientFactory(gp_practice_ods_code=GP_PRACTICE_ODS_CODE_VALID)
    
    assert(patient.gp_practice_ods_code is GP_PRACTICE_ODS_CODE_VALID)


@pytest.mark.django_db
def test_patient_creation_with_valid_gp_practice_postcode():
    patient = PatientFactory(
        gp_practice_ods_code=None,
        gp_practice_postcode=GP_PRACTICE_POSTCODE_VALID
    )
    
    assert(patient.gp_practice_ods_code == GP_PRACTICE_ODS_CODE_VALID)
    assert(patient.gp_practice_postcode == GP_PRACTICE_POSTCODE_VALID)


@pytest.mark.django_db
@patch('project.npda.models.patient.gp_ods_code_for_postcode', Mock(side_effect=Exception('oopsie')))
def test_patient_creation_with_gp_practice_postcode_lookup_failure():
    patient = PatientFactory(
        gp_practice_ods_code=None,
        gp_practice_postcode=GP_PRACTICE_POSTCODE_VALID
    )
    
    assert(patient.gp_practice_ods_code == None)
    assert(patient.gp_practice_postcode == GP_PRACTICE_POSTCODE_VALID)


@pytest.mark.django_db
@patch('project.npda.models.patient.gp_details_for_ods_code', Mock(return_value=[]))
def test_patient_creation_with_gp_practice_postcode_that_isnt_a_gp_raises_error():
    with pytest.raises(ValidationError):
        PatientFactory(gp_practice_postcode="WC1X 8SH")

