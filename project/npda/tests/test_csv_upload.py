import pytest
import pandas as pd
import nhs_number

from functools import partial
from dateutil.relativedelta import relativedelta
from unittest.mock import Mock
from requests import RequestException

from django.apps import apps
from django.core.exceptions import ValidationError

from project.npda.models import NPDAUser, Patient
from project.npda.general_functions.csv_upload import read_csv, csv_upload
from project.npda.tests.mocks.mock_patient import (
    TODAY,
    VALID_FIELDS,
    INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE,
    patient_form_with_mock_remote_calls
)

ALDER_HEY_PZ_CODE = "PZ074"


@pytest.fixture
def dummy_sheets_folder(request):
    return request.config.rootdir / 'project' / 'npda' / 'dummy_sheets'

@pytest.fixture
def valid_df(dummy_sheets_folder):
    return read_csv(dummy_sheets_folder / 'dummy_sheet.csv')

@pytest.fixture
def single_row_valid_df(dummy_sheets_folder):
    return read_csv(dummy_sheets_folder / 'dummy_sheet.csv').head(1)

@pytest.fixture
def test_user(seed_groups_fixture, seed_users_fixture):
    return NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

# TODO MRB: test transfer
# TODO MRB: test Visit creation and validation

@pytest.mark.django_db
def test_create_patient(test_user, single_row_valid_df):
    csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)
    patient = Patient.objects.first()

    assert(patient.nhs_number == nhs_number.normalise_number(single_row_valid_df["NHS Number"][0]))
    assert(patient.date_of_birth == single_row_valid_df["Date of Birth"][0].date())
    assert(patient.diabetes_type == single_row_valid_df["Diabetes Type"][0])
    assert(patient.diagnosis_date == single_row_valid_df["Date of Diabetes Diagnosis"][0].date())
    assert(patient.death_date is None)


@pytest.mark.django_db
def test_create_patient_with_death_date(test_user, single_row_valid_df):
    death_date = VALID_FIELDS["diagnosis_date"] + relativedelta(years=1)
    single_row_valid_df["Death Date"] = pd.to_datetime(death_date)

    csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)
    patient = Patient.objects.first()

    assert(patient.death_date == single_row_valid_df["Death Date"][0].date())


@pytest.mark.django_db
def test_multiple_rows(test_user, valid_df):
    df = valid_df.head(3)

    assert(df["NHS Number"][0] == df["NHS Number"][1])
    assert(df["NHS Number"][0] != df["NHS Number"][2])

    csv_upload(test_user, df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)

    assert(Patient.objects.count() == 2)

    first_patient = Patient.objects.all()[0]
    second_patient = Patient.objects.all()[1]

    assert(first_patient.nhs_number == nhs_number.normalise_number(df["NHS Number"][0]))
    assert(first_patient.date_of_birth == df["Date of Birth"][0].date())
    assert(first_patient.diabetes_type == df["Diabetes Type"][0])
    assert(first_patient.diagnosis_date == df["Date of Diabetes Diagnosis"][0].date())

    assert(second_patient.nhs_number == nhs_number.normalise_number(df["NHS Number"][2]))
    assert(second_patient.date_of_birth == df["Date of Birth"][2].date())
    assert(second_patient.diabetes_type == df["Diabetes Type"][2])
    assert(second_patient.diagnosis_date == df["Date of Diabetes Diagnosis"][2].date())


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
def test_one_row_fails_one_row_passes(test_user, valid_df):
    # TODO MRB: a descriptive fixture for this
    df = valid_df.drop(1).reset_index(drop=True).head(2)
    print(f"!! {df}")
    assert(df["NHS Number"][0] != df["NHS Number"][1])

    # Force a failure to save
    df["NHS Number"][0] = None

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)
    
    # TODO: assert row number in exception

    assert(Patient.objects.count() == 1)

    patient = Patient.objects.first()
    assert(patient.nhs_number == df["NHS Number"][1])


@pytest.mark.django_db
def test_invalid_nhs_number(test_user, single_row_valid_df):
    invalid_nhs_number = "123456789"
    single_row_valid_df["NHS Number"] = invalid_nhs_number 

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
    single_row_valid_df["Date of Birth"] = pd.to_datetime(date_of_birth)

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
    single_row_valid_df["Date of Birth"] = pd.to_datetime(date_of_birth)

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)

    patient = Patient.objects.first()

    assert(patient.date_of_birth == date_of_birth)
    assert("date_of_birth" in patient.errors)

    error_message = patient.errors["date_of_birth"][0]['message']
    assert(error_message == "NPDA patients cannot be 25+ years old. This patient is 25")


@pytest.mark.django_db
def test_invalid_diabetes_type(test_user, single_row_valid_df):
    single_row_valid_df["Diabetes Type"] = 45 

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)

    patient = Patient.objects.first()

    assert(patient.diabetes_type == 45)
    assert("diabetes_type" in patient.errors)


@pytest.mark.django_db
def test_future_diagnosis_date(test_user, single_row_valid_df):
    diagnosis_date = TODAY + relativedelta(days=1)
    single_row_valid_df["Date of Diabetes Diagnosis"] = pd.to_datetime(diagnosis_date)

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)

    patient = Patient.objects.first()

    assert(patient.diagnosis_date == diagnosis_date)
    assert("diagnosis_date" in patient.errors)

    error_message = patient.errors["diagnosis_date"][0]['message']
    # TODO MRB: why does this have entity encoding issues?
    assert(error_message == "&#x27;Diagnosis Date&#x27; cannot be in the future")


@pytest.mark.django_db
def test_diagnosis_date_before_date_of_birth(test_user, single_row_valid_df):
    date_of_birth = VALID_FIELDS["date_of_birth"],
    diagnosis_date = VALID_FIELDS["date_of_birth"] - relativedelta(years=1)

    single_row_valid_df["Date of Diabetes Diagnosis"] = pd.to_datetime(diagnosis_date)

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)

    patient = Patient.objects.first()

    assert(patient.diagnosis_date == diagnosis_date)
    assert("diagnosis_date" in patient.errors)

    error_message = patient.errors["diagnosis_date"][0]['message']
    # TODO MRB: why does this have entity encoding issues?
    assert(error_message == "&#x27;Date of Diabetes Diagnosis&#x27; cannot be before &#x27;Date of Birth&#x27;")


@pytest.mark.django_db
def test_invalid_sex(test_user, single_row_valid_df):
    single_row_valid_df["Stated gender"] = 45 

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)

    patient = Patient.objects.first()

    assert(patient.sex == 45)
    assert("sex" in patient.errors)


@pytest.mark.django_db
def test_invalid_ethnicity(test_user, single_row_valid_df):
    single_row_valid_df["Ethnic Category"] = "45" 

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)

    patient = Patient.objects.first()

    assert(patient.ethnicity == "45")
    assert("ethnicity" in patient.errors)


@pytest.mark.django_db
def test_missing_gp_ods_code(test_user, single_row_valid_df):
    single_row_valid_df["GP Practice Code"] = None 

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)

    patient = Patient.objects.first()

    assert("gp_practice_ods_code" in patient.errors)


@pytest.mark.django_db
def test_future_death_date(test_user, single_row_valid_df):
    death_date = TODAY + relativedelta(days = 1)

    single_row_valid_df["Death Date"] = pd.to_datetime(death_date)

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)

    patient = Patient.objects.first()

    assert(patient.death_date == death_date)
    assert("death_date" in patient.errors)

    error_message = patient.errors["death_date"][0]['message']
    # TODO MRB: why does this have entity encoding issues?
    assert(error_message == "&#x27;Death Date&#x27; cannot be in the future")


@pytest.mark.django_db
def test_death_date_before_date_of_birth(test_user, single_row_valid_df):
    date_of_birth = VALID_FIELDS["date_of_birth"],
    death_date = VALID_FIELDS["date_of_birth"] - relativedelta(years=1)

    single_row_valid_df["Death Date"] = pd.to_datetime(death_date)

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)

    patient = Patient.objects.first()

    assert(patient.death_date == death_date)
    assert("death_date" in patient.errors)

    error_message = patient.errors["death_date"][0]['message']
    # TODO MRB: why does this have entity encoding issues?
    assert(error_message == "&#x27;Death Date&#x27; cannot be before &#x27;Date of Birth&#x27;")


@pytest.mark.django_db
def test_spaces_removed_from_postcode(test_user, single_row_valid_df):
    single_row_valid_df["Postcode of usual address"] = "WC1X 8SH"

    csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)
    patient = Patient.objects.first()

    assert(patient.postcode == "WC1X8SH")


@pytest.mark.django_db
def test_dashes_removed_from_postcode(test_user, single_row_valid_df):
    single_row_valid_df["Postcode of usual address"] = "WC1X-8SH"

    csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form_with_mock_remote_calls)
    patient = Patient.objects.first()

    assert(patient.postcode == "WC1X8SH")


@pytest.mark.django_db
def test_invalid_postcode(test_user, single_row_valid_df):
    single_row_valid_df["Postcode of usual address"] = "not a postcode"

    patient_form = partial(patient_form_with_mock_remote_calls,
        validate_postcode=Mock(return_value=False))

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form)
    
    patient = Patient.objects.first()

    assert(patient.postcode == "not a postcode")
    assert("postcode" in patient.errors)


@pytest.mark.django_db
def test_error_validating_postcode(test_user, single_row_valid_df):
    single_row_valid_df["Postcode of usual address"] = "WC1X 8SH"

    patient_form = partial(patient_form_with_mock_remote_calls,
        validate_postcode=Mock(side_effect=RequestException("Oopsie!")))

    csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form)
    
    patient = Patient.objects.first()
    assert(patient.postcode == "WC1X8SH")


@pytest.mark.django_db
def test_invalid_gp_ods_code(test_user, single_row_valid_df):
    single_row_valid_df["GP Practice Code"] = "not a GP code"

    patient_form = partial(patient_form_with_mock_remote_calls,
        gp_details_for_ods_code=Mock(return_value=None))

    with pytest.raises(ValidationError) as e_info:
        csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form)
    
    patient = Patient.objects.first()

    assert(patient.gp_practice_ods_code == "not a GP code")
    assert("gp_practice_ods_code" in patient.errors)


@pytest.mark.django_db
def test_error_validating_gp_ods_code(test_user, single_row_valid_df):
    single_row_valid_df["GP Practice Code"] = "G85023"

    patient_form = partial(patient_form_with_mock_remote_calls,
        validate_postcode=Mock(side_effect=RequestException("Oopsie!")))

    csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form)
    
    patient = Patient.objects.first()
    assert(patient.gp_practice_ods_code == "G85023")


# TODO MRB: this fails because we do the lookup in PatientForm.save
# This isn't called from csv_upload because we create instances manually to preserve data on error
@pytest.mark.django_db
@pytest.mark.skip(reason="IMD lookup for CSV upload needs implementing")
def test_lookup_index_of_multiple_deprivation(test_user, single_row_valid_df):
    patient_form = partial(patient_form_with_mock_remote_calls,
        imd_for_postcode=Mock(return_value=INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE))

    csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form)
    
    patient = Patient.objects.first()
    assert(patient.index_of_multiple_deprivation_quintile == INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE)


@pytest.mark.django_db
def test_error_looking_up_index_of_multiple_deprivation(test_user, single_row_valid_df):
    patient_form = partial(patient_form_with_mock_remote_calls,
        imd_for_postcode=Mock(side_effect=RequestException("oopsie!")))

    csv_upload(test_user, single_row_valid_df, ALDER_HEY_PZ_CODE, None, patient_form)
    
    patient = Patient.objects.first()
    assert(patient.index_of_multiple_deprivation_quintile is None)



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
