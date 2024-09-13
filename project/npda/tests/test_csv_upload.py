import pytest
import pandas as pd

from dateutil.relativedelta import relativedelta

from django.apps import apps
from django.core.exceptions import ValidationError

from project.npda.models import NPDAUser, Patient
from project.npda.general_functions.csv_upload import read_csv, csv_upload
from project.npda.tests.mocks.mock_patient import (
    TODAY,
    patient_form_with_mock_remote_calls
)

ALDER_HEY_PZ_CODE = "PZ074"


@pytest.fixture
def dummy_sheets_folder(request):
    return request.config.rootdir / 'project' / 'npda' / 'dummy_sheets'

@pytest.fixture
def single_row_valid_df(dummy_sheets_folder):
    return read_csv(dummy_sheets_folder / 'dummy_sheet.csv').head(1)

@pytest.fixture
def test_user(seed_users_fixture):
    return NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()


@pytest.mark.parametrize("column", [
    pytest.param("NHS Number"),
    pytest.param("Date of Birth"),
    pytest.param("Diabetes Type"),
    pytest.param("Date of Diabetes Diagnosis")
])
@pytest.mark.django_db
def test_missing_mandatory_field(test_user, single_row_valid_df, column):
    single_row_valid_df[column] = None

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)

    # TODO MRB: report back the original column names rather than the form/model field names
    # assert(column in e_info.value.message_dict)

    # Catastrophic - we can't save this patient at all
    assert(Patient.objects.count() == 0)


@pytest.mark.django_db
def test_invalid_nhs_number(test_user, single_row_valid_df):
    invalid_nhs_number = "123456789"
    single_row_valid_df.at[0, "NHS Number"] = invalid_nhs_number 

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)

    # Not catastrophic - error saved in model and raised back to caller
    patient = Patient.objects.first()

    assert(patient.nhs_number == invalid_nhs_number)

    # TODO MRB: create a ValidationError model field
    assert("nhs_number" in patient.errors)


@pytest.mark.django_db
def test_future_date_of_birth(test_user, single_row_valid_df):
    date_of_birth = TODAY + relativedelta(days=1)
    single_row_valid_df.at[0, "Date of Birth"] = pd.to_datetime(date_of_birth)

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)

    patient = Patient.objects.first()

    assert(patient.date_of_birth == date_of_birth)
    assert("date_of_birth" in patient.errors)

    error_message = patient.errors["date_of_birth"][0]['message']
    # TODO MRB: why does this have entity encoding issues?
    assert(error_message == "&#x27;Date of Birth&#x27; cannot be in the future")


@pytest.mark.django_db
def test_over_25(test_user, single_row_valid_df):
    date_of_birth = TODAY + - relativedelta(years=25, days=1)
    single_row_valid_df.at[0, "Date of Birth"] = pd.to_datetime(date_of_birth)

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)

    patient = Patient.objects.first()

    assert(patient.date_of_birth == date_of_birth)
    assert("date_of_birth" in patient.errors)

    error_message = patient.errors["date_of_birth"][0]['message']
    assert(error_message == "NPDA patients cannot be 25+ years old. This patient is 25")


@pytest.mark.django_db
def test_invalid_diabetes_type(test_user, single_row_valid_df):
    single_row_valid_df.at[0, "Diabetes Type"] = 45 

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)

    # Not catastrophic - error saved in model and raised back to caller
    patient = Patient.objects.first()

    assert(patient.diabetes_type == 45)
    assert("diabetes_type" in patient.errors)


@pytest.mark.django_db
def test_future_diagnosis_date(test_user, single_row_valid_df):
    diagnosis_date = TODAY + relativedelta(days=1)
    single_row_valid_df.at[0, "Date of Diabetes Diagnosi"] = pd.to_datetime(diagnosis_date)

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)

    patient = Patient.objects.first()

    assert(patient.diagnosis_date == diagnosis_date)
    assert("diagnosis_date" in patient.errors)

    error_message = patient.errors["diagnosis_date"][0]['message']
    # TODO MRB: why does this have entity encoding issues?
    assert(error_message == "&#x27;Diagnosis Date&#x27; cannot be in the future")

# # TODO MRB: should probably expand this out to each possible error just for completeness
# def test_synchronous_validation_errors_saved():
#     raise Error("not implemented")

# def test_postcode_validation_error_saved():
#     raise Error("not implemented")

# def test_index_of_multiple_deprivation_saved():
#     raise Error("not implemented")

# def test_error_calculating_index_of_multiple_deprivation():
#     raise Error("not implemented")

# def test_gp_ods_code_validation_error_saved():
#     raise Error("not implemented")

# def test_error_validating_gp_ods_code():
#     raise Error("not implemented")

# def test_postcode_validation_error_saved():
#     raise Error("not implemented")

# def test_error_validating_postcode():
#     raise Error("not implemented")

# def test_multiple_rows():
#     raise Error("not implemented")
