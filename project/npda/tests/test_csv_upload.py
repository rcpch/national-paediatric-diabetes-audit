import pytest
import pandas as pd

from django.apps import apps

from project.npda.models import NPDAUser
from project.npda.general_functions.csv_upload import read_csv, csv_upload

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
def test_missing_nhs_number(test_user, single_row_valid_df):
    csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None)
    raise Exception("not implemented")

# @pytest.mark.django_db
# def test_missing_date_of_birth(test_user, test_pdu, single_row_valid_df):
#     csv_upload(None, single_row_valid_df, test_pdu.pz_code)
#     raise Exception("not implemented")

# def test_missing_diabetes_type():
#     raise Error("not implemented")

# def test_missing_diagnosis_date():
#     raise Error("not implemented")

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
