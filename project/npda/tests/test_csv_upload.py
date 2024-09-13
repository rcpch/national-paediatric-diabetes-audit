import pytest
import pandas as pd

from django.apps import apps
from django.core.exceptions import ValidationError

from project.npda.models import NPDAUser, Patient
from project.npda.general_functions.csv_upload import read_csv, csv_upload
from project.npda.tests.mocks.mock_patient import patient_form_with_mock_remote_calls

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


@pytest.mark.django_db
@pytest.mark.parametrize("column", [
    pytest.param("NHS Number"),
    pytest.param("Date of Birth"),
    pytest.param("Diabetes Type"),
    pytest.param("Date of Diabetes Diagnosis")
])
def test_missing_mandatory_field(test_user, single_row_valid_df, column):
    single_row_valid_df[column] = None

    # Catastrophic - we can't save this patient at all
    with pytest.raises(ValidationError) as e_info:    
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)

    assert(column in e_info.value.message_dict)
    assert(Patient.objects.count() == 0)


@pytest.mark.django_db
def test_invalid_nhs_number(test_user, single_row_valid_df):
    single_row_valid_df.at[0, "NHS Number"] = "123456789"

    # Not catastrophic - error saved in model
    csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)


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
