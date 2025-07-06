import dataclasses
import datetime
import tempfile
import csv
import collections
from io import StringIO
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from asgiref.sync import async_to_sync

import nhs_number
import pandas as pd
import numpy as np
import pytest
from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.core.exceptions import ValidationError
from django.contrib.gis.geos import Point
from django.contrib.messages import get_messages
from django.urls import reverse

from project.constants.user import RCPCH_AUDIT_TEAM
from project.npda.general_functions.csv import (
    csv_upload,
    csv_parse,
    create_csv_submission,
)
from project.npda.general_functions.quarter_for_date import (
    current_audit_year_start_date,
)
from project.constants import csv_definition_for, ALL_VISIT_DATES
from project.npda.models import (
    NPDAUser,
    Patient,
    Visit,
    PaediatricDiabetesUnit,
    AuditPeriod,
    Submission
)
from project.npda.tests.factories.patient_factory import (
    INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE,
    TODAY,
    VALID_FIELDS,
)
from project.npda.forms.external_patient_validators import (
    PatientExternalValidationResult,
)
from project.npda.forms.external_visit_validators import (
    VisitExternalValidationResult,
    CentileAndSDS,
)
from project.npda.tests.utils import login_and_verify_user


MOCK_PATIENT_EXTERNAL_VALIDATION_RESULT = PatientExternalValidationResult(
    postcode=VALID_FIELDS["postcode"],
    gp_practice_ods_code=VALID_FIELDS["gp_practice_ods_code"],
    gp_practice_postcode=None,
    index_of_multiple_deprivation_quintile=INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE,
    location_bng=Point(100, -100),
    location_wgs84=Point(200, -200),
)

MOCK_VISIT_EXTERNAL_VALIDATION_RESULT = VisitExternalValidationResult(
    height_result=CentileAndSDS(centile=Decimal(0.5), sds=Decimal(0.5)),
    weight_result=CentileAndSDS(centile=Decimal(0.5), sds=Decimal(0.5)),
    bmi=Decimal(0.5),
    bmi_result=CentileAndSDS(centile=Decimal(0.5), sds=Decimal(0.5)),
)


def mock_patient_external_validation_result(**kwargs):
    return AsyncMock(
        return_value=dataclasses.replace(
            MOCK_PATIENT_EXTERNAL_VALIDATION_RESULT, **kwargs
        )
    )


# We don't want to call remote services in unit tests
@pytest.fixture(autouse=True)
def mock_remote_calls():
    with patch(
        "project.npda.general_functions.csv.csv_upload.validate_patient_async",
        AsyncMock(return_value=MOCK_PATIENT_EXTERNAL_VALIDATION_RESULT),
    ):
        with patch(
            "project.npda.general_functions.csv.csv_upload.validate_visit_async",
            AsyncMock(return_value=MOCK_VISIT_EXTERNAL_VALIDATION_RESULT),
        ):
            yield None


ALDER_HEY_PZ_CODE = "PZ074"


@pytest.fixture
def valid_df(dummy_sheets_folder):
    file = dummy_sheets_folder / "dummy_sheet_test.csv"
    return csv_parse(file).df


@pytest.fixture
def single_row_valid_df(dummy_sheets_folder):
    file = dummy_sheets_folder / "dummy_sheet_test.csv"
    df = csv_parse(file).df
    df = df.head(1)

    return df


@pytest.fixture
def one_patient_two_visits(dummy_sheets_folder):
    file = dummy_sheets_folder / "dummy_sheet_test.csv"
    df = csv_parse(file).df

    df = df.head(2)
    assert df["NHS Number"][0] == df["NHS Number"][1]

    return df


@pytest.fixture
def two_patients_first_with_two_visits_second_with_one(dummy_sheets_folder):
    file = dummy_sheets_folder / "dummy_sheet_test.csv"
    df = csv_parse(file).df

    df = df.head(3)

    assert df["NHS Number"][0] == df["NHS Number"][1]
    assert df["NHS Number"][2] != df["NHS Number"][0]

    return df


@pytest.fixture
def two_patients_with_one_visit_each(dummy_sheets_folder):
    file = dummy_sheets_folder / "dummy_sheet_test.csv"
    df = csv_parse(file).df

    df = df.drop([0]).head(2).reset_index(drop=True)

    assert len(df) == 2
    assert df["NHS Number"][1] != df["NHS Number"][0]

    return df


@pytest.fixture
def test_user(seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture):
    return NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

@pytest.fixture
def test_rcpch_user(seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture):
    return NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=RCPCH_AUDIT_TEAM
    ).first()

# The database is not rolled back if we used the built in async support for pytest
# https://github.com/pytest-dev/pytest-asyncio/issues/226
@async_to_sync
async def csv_upload_sync(
    user, dataframe, pdu=None, errors_to_return=None, _audit_period=None
):
    audit_period = _audit_period if _audit_period else await AuditPeriod.objects.afirst()

    if not pdu:
        pdu = await PaediatricDiabetesUnit.objects.aget(pz_code=ALDER_HEY_PZ_CODE)

    new_submission = await create_csv_submission(
        pdu=pdu,
        audit_period=audit_period,
        csv_file_bytes=None,
        csv_file_name=None,
        submission_active=True,
        user=user,
        ip_address=None
    )

    return await csv_upload(
        dataframe,
        errors_to_return=(
            collections.defaultdict(lambda: collections.defaultdict(list))
            if errors_to_return is None
            else errors_to_return
        ),
        csv_file_name=None,
        submission=new_submission
    )


def read_csv_from_str(contents, encoding="utf-8"):
    with tempfile.NamedTemporaryFile() as f:
        f.write(contents.encode(encoding))
        f.seek(0)

        return csv_parse(f)


def modify_raw_csv(csv_str, start=None, end=None, replacements={}):
    # Sometimes we have to alter the CSV directly to test values
    # of the wrong type.
    reader = csv.reader(StringIO(csv_str))
    [header, *rows] = [row for row in reader]

    start_ix = 0 if start is None else start - 1
    end_ix = len(rows) if end is None else end - 1

    rows = rows[start_ix:end_ix]

    for replacement in replacements:
        row_ix = replacement["row"] - 1
        column_ix = header.index(replacement["column"])
        value = replacement["value"]

        rows[row_ix][column_ix] = value

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(header)
    writer.writerows(rows)

    return output.getvalue()

@pytest.mark.django_db
def test_create_patient(test_user, single_row_valid_df):

    csv_upload_sync(test_user, single_row_valid_df)
    patient = Patient.objects.first()

    assert patient.nhs_number == nhs_number.standardise_format(
        single_row_valid_df["NHS Number"][0]
    )
    assert patient.date_of_birth == single_row_valid_df["Date of Birth"][0].date()
    assert patient.diabetes_type == single_row_valid_df["Diabetes Type"][0]
    assert (
        patient.diagnosis_date
        == single_row_valid_df["Date of Diabetes Diagnosis"][0].date()
    )
    assert patient.death_date is None


@pytest.mark.django_db
def test_create_patient_with_death_date(test_user, single_row_valid_df):
    death_date = VALID_FIELDS["diagnosis_date"] + relativedelta(years=1)
    single_row_valid_df.loc[0, "Death Date"] = pd.to_datetime(death_date)

    csv_upload_sync(test_user, single_row_valid_df)
    patient = Patient.objects.first()

    assert patient.death_date == single_row_valid_df["Death Date"][0].date()


@pytest.mark.django_db
def test_multiple_patients(
    test_user, two_patients_first_with_two_visits_second_with_one
):
    df = two_patients_first_with_two_visits_second_with_one

    assert df["NHS Number"][0] == df["NHS Number"][1]
    assert df["NHS Number"][0] != df["NHS Number"][2]

    csv_upload_sync(test_user, df)

    assert Patient.objects.count() == 2
    [first_patient, second_patient] = Patient.objects.all()

    assert Visit.objects.filter(patient=first_patient).count() == 2
    assert Visit.objects.filter(patient=second_patient).count() == 1

    assert first_patient.nhs_number == nhs_number.standardise_format(
        df["NHS Number"][0]
    )
    assert first_patient.date_of_birth == df["Date of Birth"][0].date()
    assert first_patient.diabetes_type == df["Diabetes Type"][0]
    assert first_patient.diagnosis_date == df["Date of Diabetes Diagnosis"][0].date()

    assert second_patient.nhs_number == nhs_number.standardise_format(
        df["NHS Number"][2]
    )
    assert second_patient.date_of_birth == df["Date of Birth"][2].date()
    assert second_patient.diabetes_type == df["Diabetes Type"][2]
    assert second_patient.diagnosis_date == df["Date of Diabetes Diagnosis"][2].date()


@pytest.mark.django_db(transaction=True)
def test_missing_date_of_birth(
    seed_groups_per_function_fixture,
    seed_users_per_function_fixture,
    seed_audit_periods_per_function_fixture,
    single_row_valid_df,
):
    # As this test needs full transaction support we can't use our session fixtures
    test_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    # Delete all patients to ensure we're starting from a clean slate
    Patient.objects.all().delete()

    single_row_valid_df.loc[0, "Date of Birth"] = None

    assert (
        Patient.objects.count() == 0
    ), "There should be no patients in the database before the test"

    errors = csv_upload_sync(test_user, single_row_valid_df)

    assert "date_of_birth" in errors[0]

    # Catastrophic - we can't save this patient at all
    assert Patient.objects.count() == 0


@pytest.mark.django_db
def test_missing_nhs_number(
    seed_groups_per_function_fixture,
    seed_users_per_function_fixture,
    seed_audit_periods_per_function_fixture,
    single_row_valid_df,
):
    # As these tests need full transaction support we can't use our session fixtures
    test_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    # Delete all patients to ensure we're starting from a clean slate
    Patient.objects.all().delete()

    single_row_valid_df.loc[0, "NHS Number"] = None

    assert (
        Patient.objects.count() == 0
    ), "There should be no patients in the database before the test"

    errors = csv_upload_sync(test_user, single_row_valid_df)

    assert "nhs_number" in errors[0]

    # We shouldn't save this patient (invariant enforced in Patient.clean not in the database)
    assert Patient.objects.count() == 0


@pytest.mark.django_db
def test_missing_date_of_diagnosis(test_user, single_row_valid_df):
    single_row_valid_df.loc[0, "Date of Diabetes Diagnosis"] = None

    errors = csv_upload_sync(test_user, single_row_valid_df)

    assert "diagnosis_date" in errors[0]

    assert Patient.objects.count() == 1

    patient = Patient.objects.first()
    assert patient.diagnosis_date is None


@pytest.mark.django_db
def test_missing_diabetes_type(test_user, single_row_valid_df):
    single_row_valid_df.loc[0, "Diabetes Type"] = None

    errors = csv_upload_sync(test_user, single_row_valid_df)

    assert "diabetes_type" in errors[0]

    assert Patient.objects.count() == 1

    patient = Patient.objects.first()
    assert patient.diabetes_type is None


@pytest.mark.django_db
def test_error_in_multiple_visits(test_user, one_patient_two_visits):
    df = one_patient_two_visits
    df.loc[0, "Diabetes Treatment at time of Hba1c measurement"] = 45
    df.loc[
        0,
        "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?",
    ] = 3
    df.loc[1, "Diabetes Treatment at time of Hba1c measurement"] = 3
    df.loc[
        1,
        "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?",
    ] = 3

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=df["Visit/Appointment Date"][1].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, df, _audit_period=audit_period)
    assert "treatment" in errors[0]

    assert Visit.objects.count() == 2

    [first_visit, second_visit] = Visit.objects.all().order_by("visit_date")

    assert first_visit.treatment is None
    assert "treatment" in first_visit.errors

    assert (
        second_visit.treatment
        == df["Diabetes Treatment at time of Hba1c measurement"][1]
    )

    assert second_visit.errors is None


@pytest.mark.django_db
def test_multiple_patients_where_one_has_visit_errors_and_the_other_does_not(
    test_user, two_patients_first_with_two_visits_second_with_one
):
    df = two_patients_first_with_two_visits_second_with_one

    assert df["NHS Number"][0] == df["NHS Number"][1]
    assert df["NHS Number"][0] != df["NHS Number"][2]

    df.loc[0, "Diabetes Treatment at time of Hba1c measurement"] = 45
    df.loc[
        0,
        "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?",
    ] = 3

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=df["Visit/Appointment Date"][1].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    # # set all the visit dates to be the same so we can test the treatment error
    # for item_date in ALL_VISIT_DATES:
    #     df[item_date[1]] = df["Visit/Appointment Date"][1]

    errors = csv_upload_sync(test_user, df, _audit_period=audit_period)
    assert "treatment" in errors[0]

    [patient_one, patient_two] = Patient.objects.all()

    assert Visit.objects.count() == 3

    [first_visit_for_first_patient, second_visit_for_first_patient] = (
        Visit.objects.filter(patient=patient_one).order_by("visit_date")
    )

    [visit_for_second_patient] = Visit.objects.filter(patient=patient_two)

    assert first_visit_for_first_patient.treatment is None
    assert "treatment" in first_visit_for_first_patient.errors

    assert (
        second_visit_for_first_patient.treatment
        == df["Diabetes Treatment at time of Hba1c measurement"][1]
    )
    assert second_visit_for_first_patient.errors is None

    assert (
        visit_for_second_patient.treatment
        == df["Diabetes Treatment at time of Hba1c measurement"][2]
    )
    assert visit_for_second_patient.errors is None


@pytest.mark.django_db
def test_multiple_patients_with_visit_errors(
    test_user, two_patients_with_one_visit_each
):
    df = two_patients_with_one_visit_each

    df.loc[0, "Diabetes Treatment at time of Hba1c measurement"] = 45
    df.loc[
        0,
        "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?",
    ] = 3
    df.loc[1, "Diabetes Treatment at time of Hba1c measurement"] = 45
    df.loc[
        1,
        "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?",
    ] = 3

    errors = csv_upload_sync(test_user, df)

    assert "treatment" in errors[0]
    assert "treatment" in errors[1]

    [patient_one, patient_two] = Patient.objects.all()

    assert Visit.objects.count() == 2

    visit_for_first_patient = Visit.objects.filter(patient=patient_one).first()
    visit_for_second_patient = Visit.objects.filter(patient=patient_two).first()

    assert visit_for_first_patient.treatment == None
    assert "treatment" in visit_for_first_patient.errors

    assert visit_for_second_patient.treatment == None
    assert "treatment" in visit_for_second_patient.errors


@pytest.mark.django_db
def test_invalid_nhs_number(test_user, single_row_valid_df):
    invalid_nhs_number = "123456789"
    single_row_valid_df["NHS Number"] = invalid_nhs_number

    errors = csv_upload_sync(test_user, single_row_valid_df)
    assert "nhs_number" in errors[0]

    patient = Patient.objects.first()
    assert patient.nhs_number == "123456789"


@pytest.mark.django_db
def test_future_date_of_birth(test_user, single_row_valid_df):
    date_of_birth = TODAY + relativedelta(days=1)
    single_row_valid_df["Date of Birth"] = pd.to_datetime(date_of_birth)

    errors = csv_upload_sync(test_user, single_row_valid_df)
    assert "date_of_birth" in errors[0]

    patient = Patient.objects.first()

    assert patient.date_of_birth == date_of_birth
    assert "date_of_birth" in patient.errors

    error_message = patient.errors["date_of_birth"][0]["message"]
    assert error_message == "Cannot be in the future"


@pytest.mark.django_db
def test_over_25(test_user, single_row_valid_df):
    date_of_birth = TODAY + -relativedelta(years=25, days=1)
    single_row_valid_df["Date of Birth"] = pd.to_datetime(date_of_birth)

    errors = csv_upload_sync(test_user, single_row_valid_df)
    assert "date_of_birth" in errors[0]

    patient = Patient.objects.first()

    assert patient.date_of_birth == date_of_birth
    assert "date_of_birth" in patient.errors

    error_message = patient.errors["date_of_birth"][0]["message"]
    assert error_message == "NPDA patients cannot be 25+ years old. This patient is 25"


@pytest.mark.django_db
def test_future_diagnosis_date(test_user, single_row_valid_df):
    diagnosis_date = TODAY + relativedelta(days=1)
    single_row_valid_df["Date of Diabetes Diagnosis"] = pd.to_datetime(diagnosis_date)

    errors = csv_upload_sync(test_user, single_row_valid_df)
    assert "diagnosis_date" in errors[0]

    patient = Patient.objects.first()

    assert patient.diagnosis_date == diagnosis_date
    assert "diagnosis_date" in patient.errors

    error_message = patient.errors["diagnosis_date"][0]["message"]
    assert error_message == "Cannot be in the future"


@pytest.mark.django_db
def test_diagnosis_date_before_date_of_birth(test_user, single_row_valid_df):
    date_of_birth = (VALID_FIELDS["date_of_birth"],)
    diagnosis_date = VALID_FIELDS["date_of_birth"] - relativedelta(years=1)

    single_row_valid_df["Date of Diabetes Diagnosis"] = pd.to_datetime(diagnosis_date)

    errors = csv_upload_sync(test_user, single_row_valid_df)

    assert "diagnosis_date" in errors[0]
    error_message = errors[0]["diagnosis_date"][0]

    assert (
        error_message == "'Date of Diabetes Diagnosis' cannot be before 'Date of Birth'"
    )

    patient = Patient.objects.first()

    assert patient.diagnosis_date == diagnosis_date
    assert "diagnosis_date" in patient.errors

    error_message = patient.errors["diagnosis_date"][0]["message"]
    assert (
        error_message == "'Date of Diabetes Diagnosis' cannot be before 'Date of Birth'"
    )


@pytest.mark.django_db
def test_invalid_sex(test_user, single_row_valid_df):
    single_row_valid_df["Stated gender"] = 45

    errors = csv_upload_sync(test_user, single_row_valid_df)
    assert "sex" in errors[0]

    patient = Patient.objects.first()

    assert patient.sex == None
    assert "sex" in patient.errors


@pytest.mark.django_db
def test_not_specified_sex(test_user, single_row_valid_df):
    single_row_valid_df["Stated gender"] = 3

    errors = csv_upload_sync(test_user, single_row_valid_df)
    assert "sex" not in errors[0]

    patient = Patient.objects.first()

    assert patient.sex == 3
    assert patient.errors is None


@pytest.mark.django_db
def test_unknown_sex(test_user, single_row_valid_df):
    single_row_valid_df["Stated gender"] = 99

    errors = csv_upload_sync(test_user, single_row_valid_df)
    assert "sex" not in errors[0]

    patient = Patient.objects.first()

    assert patient.sex == 99
    assert patient.errors is None


@pytest.mark.django_db
def test_missing_gp_ods_code(test_user, single_row_valid_df):
    single_row_valid_df["GP Practice Code"] = None

    errors = csv_upload_sync(test_user, single_row_valid_df)
    assert "gp_practice_ods_code" in errors[0]

    error_message = errors[0]["gp_practice_ods_code"][0]
    assert (
        error_message
        == "'GP Practice ODS code' and 'GP Practice postcode' cannot both be empty"
    )

    patient = Patient.objects.first()

    assert "gp_practice_ods_code" in patient.errors

    error_message = patient.errors["gp_practice_ods_code"][0]["message"]
    assert (
        error_message
        == "'GP Practice ODS code' and 'GP Practice postcode' cannot both be empty"
    )


@pytest.mark.django_db
def test_future_death_date(test_user, single_row_valid_df):
    death_date = TODAY + relativedelta(days=1)

    single_row_valid_df["Death Date"] = pd.to_datetime(death_date)

    errors = csv_upload_sync(test_user, single_row_valid_df)
    assert "death_date" in errors[0]

    patient = Patient.objects.first()

    assert patient.death_date == death_date
    assert "death_date" in patient.errors

    error_message = patient.errors["death_date"][0]["message"]
    assert error_message == "Cannot be in the future"


@pytest.mark.django_db
def test_death_date_before_date_of_birth(test_user, single_row_valid_df):
    date_of_birth = (VALID_FIELDS["date_of_birth"],)
    death_date = VALID_FIELDS["date_of_birth"] - relativedelta(years=1)

    single_row_valid_df["Death Date"] = pd.to_datetime(death_date)

    errors = csv_upload_sync(test_user, single_row_valid_df)
    assert "death_date" in errors[0]

    error_message = errors[0]["death_date"][0]
    assert error_message == "'Death Date' cannot be before 'Date of Birth'"

    patient = Patient.objects.first()

    assert patient.death_date == death_date
    assert "death_date" in patient.errors

    error_message = patient.errors["death_date"][0]["message"]
    assert error_message == "'Death Date' cannot be before 'Date of Birth'"


@pytest.mark.django_db
@patch(
    "project.npda.general_functions.csv.csv_upload.validate_patient_async",
    mock_patient_external_validation_result(
        postcode=ValidationError("Invalid postcode")
    ),
)
def test_invalid_postcode(test_user, single_row_valid_df):
    single_row_valid_df["Postcode of usual address"] = "not a postcode"

    errors = csv_upload_sync(test_user, single_row_valid_df)
    assert "postcode" in errors[0]

    patient = Patient.objects.first()

    assert patient.postcode == "not a postcode"
    assert "postcode" in patient.errors


@pytest.mark.django_db
@patch(
    "project.npda.general_functions.csv.csv_upload.validate_patient_async",
    mock_patient_external_validation_result(postcode=None),
)
def test_error_validating_postcode(test_user, single_row_valid_df):
    single_row_valid_df["Postcode of usual address"] = "WC1X 8SH"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert len(errors) == 0

    patient = Patient.objects.first()
    assert patient.postcode == "WC1X8SH"


@pytest.mark.django_db
@patch(
    "project.npda.general_functions.csv.csv_upload.validate_patient_async",
    mock_patient_external_validation_result(
        gp_practice_ods_code=ValidationError("Invalid ODS code")
    ),
)
def test_invalid_gp_ods_code(test_user, single_row_valid_df):
    single_row_valid_df["GP Practice Code"] = "not a GP code"

    errors = csv_upload_sync(test_user, single_row_valid_df)
    assert "gp_practice_ods_code" in errors[0]

    patient = Patient.objects.first()

    assert patient.gp_practice_ods_code == "not a GP code"
    assert "gp_practice_ods_code" in patient.errors


@pytest.mark.django_db
@patch(
    "project.npda.general_functions.csv.csv_upload.validate_patient_async",
    mock_patient_external_validation_result(postcode=None),
)
def test_error_validating_gp_ods_code(test_user, single_row_valid_df):
    single_row_valid_df["GP Practice Code"] = "G85023"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)
    assert len(errors) == 0

    patient = Patient.objects.first()
    assert patient.gp_practice_ods_code == "G85023"


@pytest.mark.django_db
def test_gp_ods_code_trailing_space(test_user, dummy_sheet_csv):
    with patch(
        "project.npda.general_functions.csv.csv_upload.validate_patient_async",
        AsyncMock(return_value=MOCK_PATIENT_EXTERNAL_VALIDATION_RESULT),
    ) as mock_validate_patient_async:
        one_row_csv = modify_raw_csv(
            dummy_sheet_csv,
            end=2,  # exclusive
            replacements=[{"row": 1, "column": "GP Practice Code", "value": "G85023 "}],
        )

        df = read_csv_from_str(one_row_csv).df
        csv_upload_sync(test_user, df)

        assert mock_validate_patient_async.call_count == 1
        assert mock_validate_patient_async.mock_calls[0].kwargs['gp_practice_ods_code'] == "G85023"


@pytest.mark.django_db
def test_lookup_index_of_multiple_deprivation(test_user, single_row_valid_df):
    csv_upload_sync(test_user, single_row_valid_df)

    patient = Patient.objects.first()
    assert (
        patient.index_of_multiple_deprivation_quintile
        == INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE
    )


@pytest.mark.django_db
@patch(
    "project.npda.general_functions.csv.csv_upload.validate_patient_async",
    mock_patient_external_validation_result(
        index_of_multiple_deprivation_quintile=None
    ),
)
def test_error_looking_up_index_of_multiple_deprivation(test_user, single_row_valid_df):
    csv_upload_sync(test_user, single_row_valid_df)

    patient = Patient.objects.first()
    assert patient.index_of_multiple_deprivation_quintile is None


@pytest.mark.django_db
def test_save_location_from_postcode(test_user, single_row_valid_df):
    csv_upload_sync(test_user, single_row_valid_df)

    patient = Patient.objects.first()
    assert patient.location_bng == MOCK_PATIENT_EXTERNAL_VALIDATION_RESULT.location_bng
    assert (
        patient.location_wgs84 == MOCK_PATIENT_EXTERNAL_VALIDATION_RESULT.location_wgs84
    )


@pytest.mark.django_db
@patch(
    "project.npda.general_functions.csv.csv_upload.validate_patient_async",
    mock_patient_external_validation_result(
        location_bng=None,
        location_wgs84=None,
    ),
)
def test_missing_location_from_postcode(test_user, single_row_valid_df):
    csv_upload_sync(test_user, single_row_valid_df)

    patient = Patient.objects.first()
    assert patient.location_bng is None
    assert patient.location_wgs84 is None


@pytest.mark.django_db
def test_strip_first_spaces_in_column_name(test_user, dummy_sheet_csv):
    csv = dummy_sheet_csv.replace("NHS Number", "  NHS Number")
    df = read_csv_from_str(csv).df

    assert df.columns[0] == "NHS Number"

    csv_upload_sync(test_user, df)
    patient = Patient.objects.first()

    assert patient.nhs_number == nhs_number.standardise_format(df["NHS Number"][0])


@pytest.mark.django_db
def test_strip_last_spaces_in_column_name(test_user, dummy_sheet_csv):
    csv = dummy_sheet_csv.replace("NHS Number", "NHS Number  ")
    df = read_csv_from_str(csv).df

    assert df.columns[0] == "NHS Number"

    csv_upload_sync(test_user, df)
    patient = Patient.objects.first()

    assert patient.nhs_number == nhs_number.standardise_format(df["NHS Number"][0])


# Originally found in https://github.com/rcpch/national-paediatric-diabetes-audit/actions/runs/11627684066/job/32381466250
# so we have a separate unit test for it
@pytest.mark.django_db
def test_spaces_in_date_column_name(test_user, dummy_sheet_csv):
    csv = dummy_sheet_csv.replace("Date of Birth", "  Date of Birth")
    df = read_csv_from_str(csv).df

    csv_upload_sync(test_user, df)
    patient = Patient.objects.first()

    assert patient.date_of_birth == df["Date of Birth"][0].date()


@pytest.mark.django_db
def test_different_column_order(test_user, single_row_valid_df):
    columns = single_row_valid_df.columns.to_list()

    # Move the first column to the end
    columns = columns[1:] + columns[:1]
    df = single_row_valid_df[columns]

    csv_upload_sync(test_user, df)
    assert Patient.objects.count() == 1


@pytest.mark.django_db
def test_additional_columns_causes_error(
    single_row_valid_df, tmp_path, client, test_rcpch_user
):
    # Add additional columns
    single_row_valid_df["extra_one"] = "ada"
    single_row_valid_df["extra_two"] = "lovelace"

    Submission.objects.all().delete() # Clear any previous submissions

    # write back into temp
    tmp_csv_path = tmp_path / "dummy_sheet_test.csv"
    single_row_valid_df.to_csv(tmp_csv_path, index=False)

    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)
    session = client.session
    session['can_upload_csv'] = True
    session.save()

    # Feed file to view
    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(
            reverse('upload_csv'),
            {
                'csv_upload': csv_file
            },
            format='multipart'
        )

    assert response.status_code == 200
    assert "Warning: Column errors detected!" in response.content.decode("utf-8")

    assert Submission.objects.count() == 0, "No submission should be created if there are column errors"


@pytest.mark.django_db
def test_duplicate_columns_causes_error(single_row_valid_df, client, test_rcpch_user, tmp_path):
    single_row_valid_df["NHS Number_2"] = single_row_valid_df["NHS Number"]
    single_row_valid_df["NHS Number_3"] = single_row_valid_df["NHS Number"]
    single_row_valid_df["Date of Birth_2"] = single_row_valid_df["Date of Birth"]

    tmp_csv_path = tmp_path / "dummy_sheet_test.csv"
    single_row_valid_df.to_csv(tmp_csv_path, index=False)

    Submission.objects.all().delete()  # Clear any previous submissions

    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)
    session = client.session
    session['can_upload_csv'] = True
    session.save()

    # Feed file and re-duplicate columns to the CSV
    with open(tmp_csv_path, "r") as csv_file:
        csv = csv_file.read()
        csv = csv.replace("NHS Number_2", "NHS Number")
        csv = csv.replace("NHS Number_3", "NHS Number")
        csv = csv.replace("Date of Birth_2", "Date of Birth")
        # Reset the file pointer to the beginning of the file
        csv_file.seek(0)

        response = client.post(
            reverse('upload_csv'),
            {
                'csv_upload': csv_file
            },
            format='multipart'
        )

    assert response.status_code == 200
    assert "Warning: Column errors detected!" in response.content.decode("utf-8")

    assert Submission.objects.count() == 0, "No submission should be created if there are column errors"
    
    


@pytest.mark.django_db
def test_missing_columns_causes_error(test_rcpch_user, single_row_valid_df, client, tmp_path):
    df = single_row_valid_df.drop(
        columns=["Urinary Albumin Level (ACR)", "Total Cholesterol Level (mmol/l)"]
    )

    Submission.objects.all().delete()  # Clear any previous submissions

    tmp_csv_path = tmp_path / "dummy_sheet_test.csv"
    df.to_csv(tmp_csv_path, index=False)

    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)
    session = client.session
    session['can_upload_csv'] = True
    session.save()

    # Feed file into view
    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(
            reverse('upload_csv'),
            {
                'csv_upload': csv_file
            },
            format='multipart'
        )

    assert response.status_code == 200
    assert "Warning: Column errors detected!" in response.content.decode("utf-8")

    assert Submission.objects.count() == 0, "No submission should be created if there are column errors"


@pytest.mark.django_db
def test_case_insensitive_column_headers(test_user, dummy_sheet_csv):
    csv = dummy_sheet_csv

    lines = csv.split("\n")
    lines[0] = lines[0].lower()
    csv = "\n".join(lines)

    parsed_csv = read_csv_from_str(csv)
    assert len(parsed_csv.additional_columns) == 0

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=parsed_csv.df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, parsed_csv.df, _audit_period=audit_period)

    assert len(errors) == 0


@pytest.mark.django_db
def test_mixed_case_column_headers(test_user, dummy_sheet_csv):
    csv = dummy_sheet_csv.replace("NHS Number", "NHS number")
    df = read_csv_from_str(csv).df

    assert df.columns[0] == "NHS Number"

@pytest.mark.django_db
def test_column_headers_with_quotes(test_user, dummy_sheet_csv):
    csv = dummy_sheet_csv.replace("NHS Number", '"NHS Number"')
    assert '"NHS Number"' in csv
    df = read_csv_from_str(csv).df

    assert df.columns[0] == "NHS Number"


@pytest.mark.django_db
def test_invalid_nhs_number_column_name(single_row_valid_df, client, test_rcpch_user, tmp_path):
    single_row_valid_df = single_row_valid_df.rename(columns={"NHS Number": "NHS Nunberxns"})
    
    tmp_csv_path = tmp_path / "dummy_sheet_test.csv"
    single_row_valid_df.to_csv(tmp_csv_path, index=False)
    
    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)
    session = client.session
    session['can_upload_csv'] = True
    session.save()

    # Feed file into view
    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(
            reverse('upload_csv'),
            {
                'csv_upload': csv_file
            },
            format='multipart'
        )

    assert response.status_code == 302
    assert response.url == reverse("upload_csv")
    
    error_messages = list(get_messages(response.wsgi_request))

    assert len(error_messages) == 1
    assert error_messages[0].tags == "error"
    assert error_messages[0].message == "Invalid CSV format: No unique identifier column is present. Please ensure one of Unique Reference Number or NHS Number is present in the file."


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/741
@pytest.mark.django_db
def test_invalid_date_of_birth_column_name_with_mixed_case_column_headers(
    test_user, dummy_sheet_csv
):
    csv = dummy_sheet_csv.replace("Date of Birth", "DOB").replace(
        "HbA1c result format", "HBA1C Result Format"
    )
    results = read_csv_from_str(csv)

    assert results.missing_columns == []
    assert results.additional_columns == []


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/741
@pytest.mark.django_db
def test_old_template_headers(test_user, dummy_sheet_csv_old_headers):
    csv = dummy_sheet_csv_old_headers
    results = read_csv_from_str(csv)

    assert results.missing_columns == []
    assert results.additional_columns == []

    csv_upload_sync(test_user, results.df)

    assert(Patient.objects.count() > 0)
    assert(Visit.objects.count() > 0)


@pytest.mark.django_db
def test_first_row_with_extra_cell_at_the_start(test_user, single_row_valid_df):
    csv = single_row_valid_df.to_csv(index=False, date_format="%d/%m/%Y")

    lines = csv.split("\n")
    lines[1] = "extra_value," + lines[1]

    csv = "\n".join(lines)

    with pytest.raises(ValueError):
        read_csv_from_str(csv)


@pytest.mark.django_db
def test_first_row_with_extra_cell_on_the_end(test_user, single_row_valid_df):
    csv = single_row_valid_df.to_csv(index=False, date_format="%d/%m/%Y")

    lines = csv.split("\n")
    lines[1] += ",extra_value"

    csv = "\n".join(lines)

    with pytest.raises(ValueError):
        read_csv_from_str(csv)


@pytest.mark.django_db
def test_second_row_with_extra_cell_at_the_start(test_user, one_patient_two_visits):
    csv = one_patient_two_visits.to_csv(index=False, date_format="%d/%m/%Y")

    lines = csv.split("\n")
    lines[2] = "extra_value," + lines[1]

    csv = "\n".join(lines)

    with pytest.raises(pd.errors.ParserError):
        read_csv_from_str(csv)


@pytest.mark.django_db
def test_second_row_with_extra_cell_on_the_end(test_user, one_patient_two_visits):
    csv = one_patient_two_visits.to_csv(index=False, date_format="%d/%m/%Y")

    lines = csv.split("\n")
    lines[2] += ",extra_value"

    csv = "\n".join(lines)

    with pytest.raises(pd.errors.ParserError):
        read_csv_from_str(csv)


@pytest.mark.django_db
def test_upload_without_headers(test_user, one_patient_two_visits):
    csv = one_patient_two_visits.to_csv(index=False, date_format="%d/%m/%Y")

    lines = csv.split("\n")
    lines = lines[1:]

    csv = "\n".join(lines)

    # The first row of the csv file does not match any of the predefined column names - this is a fatal error and the csv should be rejected and the user notified
    with pytest.raises(
        ValueError,
        match="The first row of the csv file does not match any of the predefined column names. Please include these and upload the file again.",
    ):
        df = read_csv_from_str(csv).df
        csv_upload_sync(test_user, df)

    # No patients or associated visits should be saved
    assert Patient.objects.count() == 0
    assert Visit.objects.count() == 0


@pytest.mark.django_db
def test_jersey_csv(test_user, one_patient_two_visits):
    df = one_patient_two_visits.rename(columns={"NHS Number": "Unique Reference Number"})
    csv = df.to_csv(index=False, date_format="%d/%m/%Y")

    parsed_csv = read_csv_from_str(csv)
    assert parsed_csv.identifier_column == "Unique Reference Number"


@pytest.mark.django_db
def test_missing_identifier_columns(test_rcpch_user, one_patient_two_visits, client, tmp_path):
    df = one_patient_two_visits.drop(["NHS Number"], axis=1)

    tmp_csv_path = tmp_path / "dummy_sheet_test.csv"
    df.to_csv(tmp_csv_path, index=False)

    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)
    session = client.session
    session['can_upload_csv'] = True
    session.save()

    # Feed file into view
    with open(tmp_csv_path, "rb") as csv_file:

        response = client.post(
            reverse('upload_csv'),
            {
                'csv_upload': csv_file
            },
            format='multipart'
        )

    assert response.status_code == 302
    assert response.url == reverse("upload_csv")
    
    error_messages = list(get_messages(response.wsgi_request))
    assert len(error_messages) == 1
    assert error_messages[0].tags == "error"

    assert (
        error_messages[0].message
        == "Invalid CSV format: No unique identifier column is present. Please ensure one of Unique Reference Number or NHS Number is present in the file."
    )


@pytest.mark.django_db
def test_both_identifier_columns_causes_an_error(test_rcpch_user, one_patient_two_visits, client, tmp_path):
    df = one_patient_two_visits
    df = df.assign(**{"Unique Reference Number": np.arange(df.shape[0])})
    
    tmp_csv_path = tmp_path / "dummy_sheet_test.csv"
    df.to_csv(tmp_csv_path, index=False)

    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)
    session = client.session
    session['can_upload_csv'] = True
    session.save()

    # Feed file into view
    with open(tmp_csv_path, "rb") as csv_file:

        response = client.post(
            reverse('upload_csv'),
            {
                'csv_upload': csv_file
            },
            format='multipart'
        )

    assert response.status_code == 302
    assert response.url == reverse("upload_csv")
    
    error_messages = list(get_messages(response.wsgi_request))
    assert len(error_messages) == 1
    assert error_messages[0].tags == "error"

    assert (
        error_messages[0].message
        == "Invalid CSV format: Both Unique Reference Number and NHS Number columns are present. Please ensure only one of these is present in the file."
    )


@pytest.mark.django_db
def test_dates_with_short_year(one_patient_two_visits):
    csv = one_patient_two_visits.to_csv(index=False, date_format="%d/%m/%y")
    df = read_csv_from_str(csv).df

    assert df.equals(one_patient_two_visits)


@pytest.mark.django_db
def test_urine_albumin_value_is_rounded_to_one_decimal(test_user, single_row_valid_df):
    single_row_valid_df["Urinary Albumin Level (ACR)"] = 0.73
    csv = single_row_valid_df.to_csv(index=False, date_format="%d/%m/%Y")

    df = read_csv_from_str(csv).df
    csv_upload_sync(test_user, df)

    visit = Visit.objects.first()

    assert visit.albumin_creatinine_ratio == round(Decimal("0.73"), 1)
    assert "albumin_creatinine_ratio" not in (visit.errors or {})


@pytest.mark.django_db(transaction=True)
def test_bad_date_format_on_date_of_birth(
    seed_groups_per_function_fixture,
    seed_users_per_function_fixture,
    seed_audit_periods_per_function_fixture,
    one_patient_two_visits,
):
    # As these tests need full transaction support we can't use our session fixtures
    test_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    # Delete all patients to ensure we're starting from a clean slate
    Patient.objects.all().delete()

    df = one_patient_two_visits
    column = "Date of Birth"

    df[column] = df[column].astype(str)
    df[column] = "beep"

    csv = df.to_csv(index=False, date_format="%d/%m/%Y")

    assert (
        Patient.objects.count() == 0
    ), "There should be no patients in the database before the test"

    df = read_csv_from_str(csv).df
    errors = csv_upload_sync(test_user, df)

    assert len(errors) == 1

    assert (
        Patient.objects.count() == 0
    ), "There should be no patients in the database after the test"


@pytest.mark.django_db
def test_bad_date_format_on_date_of_diagnosis(test_user, single_row_valid_df):
    df = single_row_valid_df

    column = "Date of Diabetes Diagnosis"

    df[column] = df[column].astype(str)
    df[column] = "beep"

    csv = df.to_csv(index=False, date_format="%d/%m/%Y")

    # Slightly janky - date format errors are returned separately from parse_csv
    # as they are swallowed up into NaT and we cannot later distinguish between
    # that an the cell being empty in the CSV upload. To avoid rewriting all the usage
    # of csv_upload_sync across all tests we assert in two stages here
    errors = read_csv_from_str(csv).errors_to_return

    assert len(errors) == 1
    assert "diagnosis_date" in errors[0]
    assert (
        errors[0]["diagnosis_date"][0]
        == "Date format is incorrect (expected DD/MM/YYYY)"
    )

    errors = csv_upload_sync(test_user, df, errors_to_return=errors)
    assert "diagnosis_date" in errors[0]
    assert (
        errors[0]["diagnosis_date"][0]
        == "Date format is incorrect (expected DD/MM/YYYY)"
    )

    assert Patient.objects.count() == 1
    patient = Patient.objects.first()

    assert patient.diagnosis_date is None

    assert "diagnosis_date" in patient.errors
    assert (
        patient.errors["diagnosis_date"][0]["message"]
        == "Date format is incorrect (expected DD/MM/YYYY)"
    )


@pytest.mark.django_db
def test_bad_date_format_on_optional_column(one_patient_two_visits):
    df = one_patient_two_visits

    column = "Date of Level 3 carbohydrate counting education received"

    df[column] = df[column].astype(str)
    df[column] = "beep"

    csv = df.to_csv(index=False, date_format="%d/%m/%Y")

    df = read_csv_from_str(csv).df
    assert len(df) == 2


@pytest.mark.django_db
def test_height_is_rounded_to_one_decimal(test_user, single_row_valid_df):
    single_row_valid_df["Patient Height (cm)"] = 123.456
    single_row_valid_df["Patient Weight (kg)"] = 7.89

    csv_upload_sync(test_user, single_row_valid_df)

    visit = Visit.objects.first()

    assert visit.height == round(
        Decimal("123.456"), 1
    )  # Values are stored as Decimals (4 digits with 1 decimal place)
    assert visit.weight == round(
        Decimal("7.89"), 1
    )  # Values are stored as Decimals (4 digits with 1 decimal place)


@pytest.mark.django_db
@patch(
    "project.npda.general_functions.csv.csv_upload.validate_patient_async",
    mock_patient_external_validation_result(
        postcode=ValidationError("Invalid postcode")
    ),
)
def test_cleaned_fields_are_stored_when_other_fields_are_invalid(
    test_user, single_row_valid_df
):
    # PATIENT
    # - Valid, cleaning should remove the spaces
    single_row_valid_df["NHS Number"] = "719 573 0220"

    # Postcode marked as invalid by the mock patched above
    single_row_valid_df["Postcode of usual address"] = "not a real postcode"

    # VISIT
    # - Valid, cleaning should retain only one decimal place
    single_row_valid_df["Patient Weight (kg)"] = 7.89

    # - Invalid - cannot be less than 40
    single_row_valid_df["Patient Height (cm)"] = 38

    csv_upload_sync(test_user, single_row_valid_df)

    patient = Patient.objects.first()
    visit = Visit.objects.first()

    assert patient.nhs_number == "7195730220"  # cleaned version saved
    assert patient.postcode == "not a real postcode"  # saved but invalid

    assert visit.weight == round(Decimal("7.89"), 1)  # cleaned version saved
    assert visit.height == 38  # saved but invalid


@pytest.mark.django_db
def test_async_visit_fields_are_saved(test_user, single_row_valid_df):
    csv_upload_sync(test_user, single_row_valid_df)
    visit = Visit.objects.first()

    assert (
        visit.height_centile
        == MOCK_VISIT_EXTERNAL_VALIDATION_RESULT.height_result.centile
    )
    assert visit.height_sds == MOCK_VISIT_EXTERNAL_VALIDATION_RESULT.height_result.sds

    assert (
        visit.weight_centile
        == MOCK_VISIT_EXTERNAL_VALIDATION_RESULT.weight_result.centile
    )
    assert visit.weight_sds == MOCK_VISIT_EXTERNAL_VALIDATION_RESULT.weight_result.sds

    assert visit.bmi == MOCK_VISIT_EXTERNAL_VALIDATION_RESULT.bmi

    assert visit.bmi_centile == MOCK_VISIT_EXTERNAL_VALIDATION_RESULT.bmi_result.centile
    assert visit.bmi_sds == MOCK_VISIT_EXTERNAL_VALIDATION_RESULT.bmi_result.sds


"""
HbA1c tests
"""


@pytest.mark.django_db
def test_hba1c_value_ifcc_less_than_20(test_user, single_row_valid_df):
    single_row_valid_df.loc[0, "Hba1c Value"] = 18
    single_row_valid_df.loc[0, "HbA1c result format"] = 1  # IFCC (mmol/mol)
    single_row_valid_df.loc[0, "Observation Date: Hba1c Value"] = "01/01/2022"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "hba1c" in errors[0]

    visit = Visit.objects.first()

    # This would be rejected in the questionnaire but saved if it was a csv upload
    assert visit.hba1c == 18
    assert "hba1c" in visit.errors


@pytest.mark.django_db
def test_hba1c_value_ifcc_more_than_195(test_user, single_row_valid_df):
    single_row_valid_df.loc[0, "Hba1c Value"] = 196
    single_row_valid_df.loc[0, "HbA1c result format"] = 1  # IFCC (mmol/mol)
    single_row_valid_df.loc[0, "Observation Date: Hba1c Value"] = "01/01/2022"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)
    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "hba1c" in errors[0]

    visit = Visit.objects.first()

    # This would be rejected in the questionnaire but saved if it was a csv upload
    assert visit.hba1c == 196
    assert "hba1c" in visit.errors


@pytest.mark.django_db
def test_hba1c_value_dcct_more_than_20(test_user, single_row_valid_df):
    single_row_valid_df.loc[0, "Hba1c Value"] = 21
    single_row_valid_df.loc[0, "HbA1c result format"] = 2  # DCCT (%)
    single_row_valid_df.loc[0, "Observation Date: Hba1c Value"] = "01/01/2022"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "hba1c" in errors[0]

    visit = Visit.objects.first()

    # This would be rejected in the questionnaire but saved if it was a csv upload
    assert visit.hba1c == 21
    assert "hba1c" in visit.errors


@pytest.mark.django_db
def test_hba1c_value_dcct_less_than_3(test_user, single_row_valid_df):
    single_row_valid_df.loc[0, "Hba1c Value"] = 2
    single_row_valid_df.loc[0, "HbA1c result format"] = 2  # DCCT (%)
    single_row_valid_df.loc[0, "Observation Date: Hba1c Value"] = "01/01/2022"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)
    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "hba1c" in errors[0]

    visit = Visit.objects.first()

    # This would be rejected in the questionnaire but saved if it was a csv upload
    assert visit.hba1c == 2
    assert "hba1c" in visit.errors


@pytest.mark.django_db
def test_hba1c_missing(test_user, single_row_valid_df):
    single_row_valid_df.loc[0, "Hba1c Value"] = None
    single_row_valid_df.loc[0, "HbA1c result format"] = 2  # DCCT (%)
    single_row_valid_df.loc[0, "Observation Date: Hba1c Value"] = "01/01/2022"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)
    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "hba1c" in errors[0]

    visit = Visit.objects.first()

    # This would be rejected in the questionnaire but saved if it was a csv upload
    assert visit.hba1c == None
    assert "hba1c" in visit.errors


"""
Diabetes treatment tests
"""


@pytest.mark.django_db
def test_treatment_closed_loop_passes_validation(test_user, single_row_valid_df):
    """
    Test that both pump and closed loop system are accepted
    """
    single_row_valid_df.loc[0, "Diabetes Treatment at time of Hba1c measurement"] = 3
    single_row_valid_df.loc[
        0,
        "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?",
    ] = 1

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)
    assert len(errors) == 0

    visit = Visit.objects.first()
    assert visit.treatment == 3
    assert visit.closed_loop_system == 1


@pytest.mark.django_db
def test_treatment_missing_closed_loop_form_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that both closed loop system selected but treatment is None fail validation
    """
    single_row_valid_df.loc[0, "Diabetes Treatment at time of Hba1c measurement"] = None
    single_row_valid_df.loc[
        0,
        "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?",
    ] = 1

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)
    assert "treatment" in errors[0]

    visit = Visit.objects.first()
    assert visit.treatment is None
    assert visit.closed_loop_system == 1


@pytest.mark.django_db
def test_treatment_mdi_but_closed_loop_selected_form_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that MDI selected but closed loop system is also selected
    """
    single_row_valid_df.loc[0, "Diabetes Treatment at time of Hba1c measurement"] = (
        2  # MDI
    )
    single_row_valid_df.loc[
        0,
        "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?",
    ] = 2  # Closed loop system (licensed)

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)
    assert "closed_loop_system" in errors[0]

    visit = Visit.objects.first()
    assert visit.treatment == 2
    assert visit.closed_loop_system == 2
    assert "closed_loop_system" in visit.errors


"""
Blood pressure tests
"""


@pytest.mark.django_db
def test_blood_pressure_values_passes_validation(test_user, single_row_valid_df):
    """
    Test that both systolic and diastolic blood pressure values are accepted
    """
    single_row_valid_df.loc[0, "Systolic Blood Pressure"] = 120
    single_row_valid_df.loc[0, "Diastolic Blood pressure"] = (
        80  # Note that pressure has a lower case 'p'
    )
    single_row_valid_df.loc[0, "Observation Date (Blood Pressure)"] = "01/01/2023"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)
    assert len(errors) == 0

    visit = Visit.objects.first()
    assert visit.systolic_blood_pressure == 120
    assert visit.diastolic_blood_pressure == 80


@pytest.mark.django_db
def test_blood_pressure_missing_values_fails_validation(test_user, single_row_valid_df):
    """
    Test that one missing systolic blood pressure value fails validation
    """
    single_row_valid_df.loc[0, "Systolic Blood Pressure"] = None
    single_row_valid_df.loc[0, "Diastolic Blood pressure"] = (
        80  # Note that pressure has a lower case 'p'
    )
    single_row_valid_df.loc[0, "Observation Date (Blood Pressure)"] = "01/01/2023"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)
    assert (
        "systolic_blood_pressure" in errors[0]
    ), "Systolic Blood Pressure is None but passes validation."

    visit = Visit.objects.first()
    assert visit.systolic_blood_pressure == None
    assert visit.diastolic_blood_pressure == 80


@pytest.mark.django_db
def test_blood_pressure_missing_date_form_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that one missing blood pressure observation date fails validation
    """

    single_row_valid_df.loc[0, "Systolic Blood Pressure"] = 120
    single_row_valid_df.loc[0, "Diastolic Blood pressure"] = (
        80  # Note that pressure has a lower case 'p'
    )
    single_row_valid_df.loc[0, "Observation Date (Blood Pressure)"] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)
    assert (
        "blood_pressure_observation_date" in errors[0]
    ), "Blood Pressure observation date is None but passes validation."

    visit = Visit.objects.first()
    assert (
        visit.systolic_blood_pressure == 120
    ), f"Systolic blood pressure should be 120 but was {visit.systolic_blood_pressure}"
    assert (
        visit.diastolic_blood_pressure == 80
    ), f"Diastolic blood pressure should be 80 but was {visit.diastolic_blood_pressure}"
    assert (
        visit.blood_pressure_observation_date is None
    ), f"Blood pressure observation date should be empty but is {visit.blood_pressure_observation_date}"


@pytest.mark.django_db
def test_systolic_blood_pressure_over_240_form_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that systolic blood pressure value > 240 fails validation
    """

    single_row_valid_df.loc[0, "Systolic Blood Pressure"] = 250
    single_row_valid_df.loc[0, "Diastolic Blood pressure"] = (
        80  # Note that pressure has a lower case 'p'
    )
    single_row_valid_df.loc[0, "Observation Date (Blood Pressure)"] = "01/01/2023"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)
    assert (
        "systolic_blood_pressure" in errors[0]
    ), "Systolic Blood Pressure is >240 (so really dangerously high!) but passes validation."

    visit = Visit.objects.first()
    assert (
        visit.systolic_blood_pressure == 250
    ), f"Systolic blood pressure should be 250 (and really the child should be in hospital) but was {visit.systolic_blood_pressure}"
    assert (
        visit.diastolic_blood_pressure == 80
    ), f"Diastolic blood pressure should be 80 but was {visit.diastolic_blood_pressure}"
    assert visit.blood_pressure_observation_date == datetime.date(
        2023, 1, 1
    ), f"Blood pressure observation date should be 1/1/2023 but is {visit.blood_pressure_observation_date}"


@pytest.mark.django_db
def test_systolic_blood_pressure_below_50_form_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that systolic blood pressure value < 80 fails validation
    """

    single_row_valid_df.loc[0, "Systolic Blood Pressure"] = 49
    single_row_valid_df.loc[0, "Diastolic Blood pressure"] = (
        40  # Note that pressure has a lower case 'p'
    )
    single_row_valid_df.loc[0, "Observation Date (Blood Pressure)"] = "01/01/2023"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)
    assert (
        "systolic_blood_pressure" in errors[0]
    ), "Systolic Blood Pressure is < 50 (so really dangerously low!) but passes validation."

    visit = Visit.objects.first()
    assert (
        visit.systolic_blood_pressure == 49
    ), f"Systolic blood pressure should be 49 (and really the child should be in hospital) but was {visit.systolic_blood_pressure}"
    assert (
        visit.diastolic_blood_pressure == 40
    ), f"Diastolic blood pressure should be 40 but was {visit.diastolic_blood_pressure}"
    assert visit.blood_pressure_observation_date == datetime.date(
        2023, 1, 1
    ), f"Blood pressure observation date should be 1/1/203 but is {visit.blood_pressure_observation_date}"


@pytest.mark.django_db
def test_diastolic_blood_pressure_over_120_form_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that diastolic blood pressure value > 120 fails validation
    """

    single_row_valid_df.loc[0, "Systolic Blood Pressure"] = 120
    single_row_valid_df.loc[0, "Diastolic Blood pressure"] = (
        125  # Note that pressure has a lower case 'p'
    )
    single_row_valid_df.loc[0, "Observation Date (Blood Pressure)"] = "01/01/2023"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)
    assert (
        "diastolic_blood_pressure" in errors[0]
    ), "Diastolic Blood Pressure is >120 (so really dangerously high!) but passes validation."

    visit = Visit.objects.first()
    assert (
        visit.systolic_blood_pressure == 120
    ), f"Systolic blood pressure should be 120 but was {visit.systolic_blood_pressure}"
    assert (
        visit.diastolic_blood_pressure == 125
    ), f"Diastolic blood pressure should be 125 (and really the child should be in hospital) but was {visit.diastolic_blood_pressure}"
    assert visit.blood_pressure_observation_date == datetime.date(
        2023, 1, 1
    ), f"Blood pressure observation date should be 1/1/2023 but is {visit.blood_pressure_observation_date}"


@pytest.mark.django_db
def test_diastolic_blood_pressure_below_20_form_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that diastolic blood pressure value < 20 fails validation
    """

    single_row_valid_df.loc[0, "Systolic Blood Pressure"] = 120
    single_row_valid_df.loc[0, "Diastolic Blood pressure"] = (
        15  # Note that pressure has a lower case 'p'
    )
    single_row_valid_df.loc[0, "Observation Date (Blood Pressure)"] = "01/01/2023"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)
    assert (
        "diastolic_blood_pressure" in errors[0]
    ), "Diastolic Blood Pressure is < 20 (so really dangerously low!) but passes validation."

    visit = Visit.objects.first()
    assert (
        visit.systolic_blood_pressure == 120
    ), f"Systolic blood pressure should be 120 but was {visit.systolic_blood_pressure}"
    assert (
        visit.diastolic_blood_pressure == 15
    ), f"Diastolic blood pressure should be 15 (and really the child should be in hospital) but was {visit.diastolic_blood_pressure}"
    assert visit.blood_pressure_observation_date == datetime.date(
        2023, 1, 1
    ), f"Blood pressure observation date should be 1/1/2023 but is {visit.blood_pressure_observation_date}"


"""
Retinal screening tests
"""


@pytest.mark.django_db
def test_decs_value_form_passes_validation(test_user, single_row_valid_df):
    """
    Test that DECS value is accepted
    """
    single_row_valid_df.loc[0, "Retinal Screening date"] = "01/01/2023"
    single_row_valid_df.loc[0, "Retinal Screening Result"] = 1  # Normal

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert (
        len(errors) == 0
    ), f"Retinal screening date and result should pass validation, but failed with errors: {errors}"

    visit = Visit.objects.first()
    assert visit.retinal_screening_observation_date == datetime.date(
        2023, 1, 1
    ), f"Saved Retinal screening date should be 1/1/2023, but was {visit.retinal_screening_observation_date}"
    assert (
        visit.retinal_screening_result == 1
    ), f"Saved Retinal screening result should be 1 (Normal), but was {visit.retinal_screening_result}"


@pytest.mark.django_db
def test_decs_value_none_form_fails_validation(test_user, single_row_valid_df):
    """
    Test that a missing DECS value is invalid
    """
    single_row_valid_df.loc[0, "Retinal Screening date"] = "01/01/2023"
    single_row_valid_df.loc[0, "Retinal Screening Result"] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert (
        "retinal_screening_result" in errors[0]
    ), f"Retinal screening result should fail validation due to missing result, but passed."

    visit = Visit.objects.first()
    assert visit.retinal_screening_observation_date == datetime.date(
        2023, 1, 1
    ), f"Saved Retinal screening date should be 1/1/2023, but was {visit.retinal_screening_observation_date}"
    assert (
        visit.retinal_screening_result == None
    ), f"Saved Retinal screening result should be None, but was {visit.retinal_screening_result}"


@pytest.mark.django_db
def test_decs_date_none_form_fails_validation(test_user, single_row_valid_df):
    """
    Test that a missing DECS date is invalid
    """
    single_row_valid_df.loc[0, "Retinal Screening date"] = None
    single_row_valid_df.loc[0, "Retinal Screening Result"] = 1  # Normal

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert (
        "retinal_screening_observation_date" in errors[0]
    ), f"Retinal screening date should fail validation due to missing date, but passed."

    visit = Visit.objects.first()
    assert (
        visit.retinal_screening_observation_date == None
    ), f"Saved Retinal screening date should be None, but was {visit.retinal_screening_observation_date}"
    assert (
        visit.retinal_screening_result == 1
    ), f"Saved Retinal screening result should be 1 (Normal), but was {visit.retinal_screening_result}"


"""
Urine albumin tests
"""


@pytest.mark.django_db
def test_urine_albumin_value_form_passes_validation(test_user, single_row_valid_df):
    """
    Test that urine albumin value is accepted
    """
    single_row_valid_df.loc[0, "Urinary Albumin Level (ACR)"] = 30
    single_row_valid_df.loc[0, "Albuminuria Stage"] = 1  # Normal
    single_row_valid_df.loc[0, "Observation Date: Urinary Albumin Level"] = "01/01/2023"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert (
        visit.albumin_creatinine_ratio == 30
    ), f"Saved urine albumin should be 30, but was {visit.albumin_creatinine_ratio}"
    assert (
        visit.albuminuria_stage == 1
    ), f"Saved urine albumin stage should be 1 (Normal), but was {visit.albuminuria_stage}"
    assert visit.albumin_creatinine_ratio_date == datetime.date(
        2023, 1, 1
    ), f"Saved urine albumin observation date should be 1/1/2023, but was {visit.albumin_creatinine_ratio_date}"


@pytest.mark.django_db
def test_urine_albumin_value_below_range_form_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that urine albumin value is rejected if below range
    """
    single_row_valid_df.loc[0, "Urinary Albumin Level (ACR)"] = -10
    single_row_valid_df.loc[0, "Albuminuria Stage"] = 1  # Normal
    single_row_valid_df.loc[0, "Observation Date: Urinary Albumin Level"] = "01/01/2023"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert (
        "albumin_creatinine_ratio" in errors[0]
    ), f"Urine albumin creatinine ratio should fail validation as < 3, but passed."

    visit = Visit.objects.first()

    assert visit.albumin_creatinine_ratio == Decimal(
        "-10"
    ), f"Saved urine albumin should be -10, but was {visit.albumin_creatinine_ratio}"
    assert (
        visit.albuminuria_stage == 1
    ), f"Saved urine albumin stage should be 1 (Normal), but was {visit.albuminuria_stage}"
    assert visit.albumin_creatinine_ratio_date == datetime.date(
        2023, 1, 1
    ), f"Saved urine albumin observation date should be 1/1/2023, but was {visit.albumin_creatinine_ratio_date}"


@pytest.mark.django_db
def test_urine_albumin_value_above_range_form_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that urine albumin value is rejected if above range
    """
    single_row_valid_df.loc[0, "Urinary Albumin Level (ACR)"] = 1000
    single_row_valid_df.loc[0, "Albuminuria Stage"] = 1  # Normal
    single_row_valid_df.loc[0, "Observation Date: Urinary Albumin Level"] = "01/01/2023"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert (
        "albumin_creatinine_ratio" in errors[0]
    ), f"Urine albumin creatinine ratio should fail validation as > 50, but passed."

    visit = Visit.objects.first()

    assert (
        visit.albumin_creatinine_ratio == 1000
    ), f"Saved urine albumin should be 1000, but was {visit.albumin_creatinine_ratio}"
    assert (
        visit.albuminuria_stage == 1
    ), f"Saved urine albumin stage should be 1 (Normal), but was {visit.albuminuria_stage}"
    assert visit.albumin_creatinine_ratio_date == datetime.date(
        2023, 1, 1
    ), f"Saved urine albumin observation date should be 1/1/2023, but was {visit.albumin_creatinine_ratio_date}"


@pytest.mark.django_db
def test_urine_albumin_value_missing_form_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that urine albumin value missing  is rejected
    """
    single_row_valid_df.loc[0, "Urinary Albumin Level (ACR)"] = None
    single_row_valid_df.loc[0, "Albuminuria Stage"] = 1  # Normal
    single_row_valid_df.loc[0, "Observation Date: Urinary Albumin Level"] = "01/01/2023"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert (
        "albumin_creatinine_ratio" in errors[0]
    ), f"Urine albumin creatinine level should fail validation as None, but passed."

    visit = Visit.objects.first()

    assert (
        visit.albumin_creatinine_ratio is None
    ), f"Saved urine albumin should be None, but was {visit.albumin_creatinine_ratio}"
    assert (
        visit.albuminuria_stage == 1
    ), f"Saved urine albumin stage should be 1 (Normal), but was {visit.albuminuria_stage}"
    assert visit.albumin_creatinine_ratio_date == datetime.date(
        2023, 1, 1
    ), f"Saved urine albumin observation date should be 1/1/2023, but was {visit.albumin_creatinine_ratio_date}"


@pytest.mark.django_db
def test_urine_albumin_stage_missing_form_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that urine albumin value missing  is rejected
    """
    single_row_valid_df.loc[0, "Urinary Albumin Level (ACR)"] = 10
    single_row_valid_df.loc[0, "Albuminuria Stage"] = None
    single_row_valid_df.loc[0, "Observation Date: Urinary Albumin Level"] = "01/01/2023"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert (
        "albuminuria_stage" in errors[0]
    ), f"Urine albumin creatinine stage should fail validation as None, but passed."

    visit = Visit.objects.first()

    assert (
        visit.albumin_creatinine_ratio == 10
    ), f"Saved urine albumin should be 10, but was {visit.albumin_creatinine_ratio}"
    assert (
        visit.albuminuria_stage == None
    ), f"Saved urine albumin stage should be None, but was {visit.albuminuria_stage}"
    assert visit.albumin_creatinine_ratio_date == datetime.date(
        2023, 1, 1
    ), f"Saved urine albumin observation date should be 1/1/2023, but was {visit.albumin_creatinine_ratio_date}"


@pytest.mark.django_db
def test_urine_albumin_date_missing_form_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that urine albumin date missing is rejected
    """
    single_row_valid_df.loc[0, "Urinary Albumin Level (ACR)"] = 10
    single_row_valid_df.loc[0, "Albuminuria Stage"] = 1  # Normal
    single_row_valid_df.loc[0, "Observation Date: Urinary Albumin Level"] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert (
        "albumin_creatinine_ratio_date" in errors[0]
    ), f"Urine albumin creatinine date should fail validation as None, but passed."

    visit = Visit.objects.first()

    assert (
        visit.albumin_creatinine_ratio == 10
    ), f"Saved urine albumin should be 10, but was {visit.albumin_creatinine_ratio}"
    assert (
        visit.albuminuria_stage == 1
    ), f"Saved urine albumin stage should be 1 (Normal), but was {visit.albuminuria_stage}"
    assert (
        visit.albumin_creatinine_ratio_date == None
    ), f"Saved urine albumin observation date should be None, but was {visit.albumin_creatinine_ratio_date}"


"""
Total cholesterol tests
"""


@pytest.mark.django_db
def test_total_cholesterol_value_form_passes_validation(test_user, single_row_valid_df):
    """
    Test that total cholesterol value is accepted
    """
    single_row_valid_df.loc[0, "Total Cholesterol Level (mmol/l)"] = 5
    single_row_valid_df.loc[0, "Observation Date: Total Cholesterol Level"] = (
        "01/01/2023"
    )

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert (
        visit.total_cholesterol == 5
    ), f"Saved total cholesterol should be 5, but was {visit.total_cholesterol}"
    assert visit.total_cholesterol_date == datetime.date(
        2023, 1, 1
    ), f"Saved total cholesterol observation date should be 1/1/2023, but was {visit.total_cholesterol_date}"


@pytest.mark.django_db
def test_total_cholesterol_value_above_reference_form_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that total cholesterol value is rejected if impossible
    """
    single_row_valid_df.loc[0, "Total Cholesterol Level (mmol/l)"] = 20
    single_row_valid_df.loc[0, "Observation Date: Total Cholesterol Level"] = (
        "01/01/2023"
    )

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert (
        "total_cholesterol" in errors[0]
    ), f"Total cholesterol should fail validation as above reference range, but passed."

    visit = Visit.objects.first()

    assert (
        visit.total_cholesterol == 20
    ), f"Saved total cholesterol should be 1000, but was {visit.total_cholesterol}"
    assert visit.total_cholesterol_date == datetime.date(
        2023, 1, 1
    ), f"Saved total cholesterol observation date should be 1/1/2023, but was {visit.total_cholesterol_date}"


@pytest.mark.django_db
def test_total_cholesterol_value_below_reference_form_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that total cholesterol value is rejected if impossible
    """
    single_row_valid_df.loc[0, "Total Cholesterol Level (mmol/l)"] = 0.1
    single_row_valid_df.loc[0, "Observation Date: Total Cholesterol Level"] = (
        "01/01/2023"
    )

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert (
        "total_cholesterol" in errors[0]
    ), f"Total cholesterol should fail validation as impossible, but passed."

    visit = Visit.objects.first()

    assert visit.total_cholesterol == Decimal(
        "0.1"
    ), f"Saved total cholesterol should be 0, but was {visit.total_cholesterol}"
    assert visit.total_cholesterol_date == datetime.date(
        2023, 1, 1
    ), f"Saved total cholesterol observation date should be 1/1/2023, but was {visit.total_cholesterol_date}"


@pytest.mark.django_db
def test_total_cholesterol_value_missing_form_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that total cholesterol value missing  is rejected
    """
    single_row_valid_df.loc[0, "Total Cholesterol Level (mmol/l)"] = None
    single_row_valid_df.loc[0, "Observation Date: Total Cholesterol Level"] = (
        "01/01/2023"
    )

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert (
        "total_cholesterol" in errors[0]
    ), f"Total cholesterol should fail validation as None, but passed."

    visit = Visit.objects.first()

    assert (
        visit.total_cholesterol is None
    ), f"Saved total cholesterol should be None, but was {visit.total_cholesterol}"
    assert visit.total_cholesterol_date == datetime.date(
        2023, 1, 1
    ), f"Saved total cholesterol observation date should be 1/1/2023, but was {visit.total_cholesterol_date}"


@pytest.mark.django_db
def test_total_cholesterol_date_missing_form_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that total cholesterol date missing is rejected
    """
    single_row_valid_df.loc[0, "Total Cholesterol Level (mmol/l)"] = 5
    single_row_valid_df.loc[0, "Observation Date: Total Cholesterol Level"] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert (
        "total_cholesterol_date" in errors[0]
    ), f"Total cholesterol date should fail validation as None, but passed."

    visit = Visit.objects.first()

    assert (
        visit.total_cholesterol == 5
    ), f"Saved total cholesterol should be 5, but was {visit.total_cholesterol}"
    assert (
        visit.total_cholesterol_date == None
    ), f"Saved total cholesterol observation date should be None, but was {visit.total_cholesterol_date}"


"""
Thyroid treatment tests
"""


@pytest.mark.django_db
def test_thyroid_treatment_passes_validation(test_user, single_row_valid_df):
    """
    Test that thyroid treatment is accepted
    """
    single_row_valid_df.loc[
        0,
        "At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?",
    ] = 1  # Normal
    single_row_valid_df.loc[0, "Observation Date: Thyroid Function"] = "01/01/2023"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert visit.thyroid_treatment_status == 1
    assert visit.thyroid_function_date == datetime.date(2023, 1, 1)


@pytest.mark.django_db
def test_thyroid_treatment_missing_fails_validation(test_user, single_row_valid_df):
    """
    Test that a missing thyroid treatment value is rejected
    """
    single_row_valid_df.loc[
        0,
        "At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?",
    ] = None
    single_row_valid_df.loc[0, "Observation Date: Thyroid Function"] = "01/01/2023"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "thyroid_treatment_status" in errors[0]

    visit = Visit.objects.first()

    assert visit.thyroid_treatment_status is None
    assert visit.thyroid_function_date == datetime.date(2023, 1, 1)


@pytest.mark.django_db
def test_thyroid_treatment_date_missing_passes_validation(
    test_user, single_row_valid_df
):
    """
    Test that a missing thyroid treatment date is rejected
    """
    single_row_valid_df.loc[
        0,
        "At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?",
    ] = 2
    single_row_valid_df.loc[0, "Observation Date: Thyroid Function"] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "thyroid_function_date" not in errors[0]

    visit = Visit.objects.first()

    assert visit.thyroid_treatment_status == 2
    assert visit.thyroid_function_date is None


"""
Coeliac screening tests
"""


@pytest.mark.django_db
def test_coeliac_screening_passes_validation(test_user, single_row_valid_df):
    """
    Test that coeliac screening is accepted
    """
    single_row_valid_df.loc[0, "Observation Date: Coeliac Disease Screening"] = (
        "01/01/2023"
    )
    single_row_valid_df.loc[
        0, "Has the patient been recommended a Gluten-free diet?"
    ] = 1  # Yes

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert visit.coeliac_screen_date == datetime.date(2023, 1, 1)
    assert visit.gluten_free_diet == 1


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/628
@pytest.mark.django_db
def test_coeliac_screening_missing_fails_validation(test_user, single_row_valid_df):
    single_row_valid_df.loc[0, "Observation Date: Coeliac Disease Screening"] = (
        "01/01/2023"
    )
    single_row_valid_df.loc[
        0, "Has the patient been recommended a Gluten-free diet?"
    ] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "gluten_free_diet" not in errors[0]

    visit = Visit.objects.first()

    assert visit.coeliac_screen_date == datetime.date(2023, 1, 1)
    assert visit.gluten_free_diet is None


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/628
@pytest.mark.django_db
def test_coeliac_screening_date_missing_passes_validation(
    test_user, single_row_valid_df
):
    single_row_valid_df.loc[0, "Observation Date: Coeliac Disease Screening"] = None
    single_row_valid_df.loc[
        0, "Has the patient been recommended a Gluten-free diet?"
    ] = 1

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "coeliac_screen_date" not in errors[0]

    visit = Visit.objects.first()

    assert visit.coeliac_screen_date is None
    assert visit.gluten_free_diet == 1


"""
Psychological support tests
"""


@pytest.mark.django_db
def test_psychological_support_passes_validation(test_user, single_row_valid_df):
    """
    Test that psychological support is accepted
    """
    single_row_valid_df.loc[
        0, "Observation Date - Psychological Screening Assessment"
    ] = "01/01/2023"
    single_row_valid_df.loc[
        0,
        "Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?",
    ] = 1

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert visit.psychological_screening_assessment_date == datetime.date(2023, 1, 1)
    assert visit.psychological_additional_support_status == 1


@pytest.mark.django_db
def test_psychological_support_missing_fails_validation(test_user, single_row_valid_df):
    """
    Test that a missing psychological support value is rejected
    """
    single_row_valid_df.loc[
        0, "Observation Date - Psychological Screening Assessment"
    ] = "01/01/2023"
    single_row_valid_df.loc[
        0,
        "Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?",
    ] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "psychological_additional_support_status" in errors[0]

    visit = Visit.objects.first()

    assert visit.psychological_screening_assessment_date == datetime.date(2023, 1, 1)
    assert visit.psychological_additional_support_status is None


@pytest.mark.django_db
def test_psychological_support_date_missing_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that a missing psychological support date is rejected
    """
    single_row_valid_df.loc[
        0, "Observation Date - Psychological Screening Assessment"
    ] = None
    single_row_valid_df.loc[
        0,
        "Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?",
    ] = 1

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "psychological_screening_assessment_date" in errors[0]

    visit = Visit.objects.first()

    assert visit.psychological_screening_assessment_date is None
    assert visit.psychological_additional_support_status == 1


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/628
@pytest.mark.django_db
def test_psychological_support_date_missing_fails_validation(
    test_user, single_row_valid_df
):
    single_row_valid_df.loc[
        0, "Observation Date - Psychological Screening Assessment"
    ] = None
    single_row_valid_df.loc[
        0,
        "Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?",
    ] = 99  # Unknown

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "psychological_screening_assessment_date" not in errors[0]

    visit = Visit.objects.first()

    assert visit.psychological_screening_assessment_date is None
    assert visit.psychological_additional_support_status == 99


"""
Smoking status tests
"""


@pytest.mark.django_db
def test_smoking_status_passes_validation(test_user, single_row_valid_df):
    """
    Test that smoking status is accepted
    """
    single_row_valid_df.loc[
        0,
        "Date of offer of referral to smoking cessation service (if patient is a current smoker)",
    ] = "01/01/2023"
    single_row_valid_df.loc[0, "Does the patient smoke?"] = 2  # Current smoker

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert visit.smoking_cessation_referral_date == datetime.date(2023, 1, 1)
    assert visit.smoking_status == 2


@pytest.mark.django_db
def test_smoking_status_non_smoker_passes_validation(test_user, single_row_valid_df):
    """
    Test that smoking status is accepted
    """
    single_row_valid_df.loc[
        0,
        "Date of offer of referral to smoking cessation service (if patient is a current smoker)",
    ] = None
    single_row_valid_df.loc[0, "Does the patient smoke?"] = 1  # Non-smoker

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert visit.smoking_cessation_referral_date is None
    assert visit.smoking_status == 1


@pytest.mark.django_db
def test_smoking_status_non_smoker_referral_date_provided_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that a non-smoker with a referral date is rejected
    """
    single_row_valid_df.loc[
        0,
        "Date of offer of referral to smoking cessation service (if patient is a current smoker)",
    ] = "01/01/2023"
    single_row_valid_df.loc[0, "Does the patient smoke?"] = 1  # Non-smoker

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "smoking_cessation_referral_date" in errors[0]

    visit = Visit.objects.first()

    assert visit.smoking_cessation_referral_date == datetime.date(2023, 1, 1)
    assert visit.smoking_status == 1


@pytest.mark.django_db
def test_smoking_status_missing_fails_validation(test_user, single_row_valid_df):
    """
    Test that a missing smoking status value is rejected
    """
    single_row_valid_df.loc[
        0,
        "Date of offer of referral to smoking cessation service (if patient is a current smoker)",
    ] = "01/01/2023"
    single_row_valid_df.loc[0, "Does the patient smoke?"] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "smoking_cessation_referral_date" in errors[0]

    visit = Visit.objects.first()

    assert visit.smoking_cessation_referral_date == datetime.date(2023, 1, 1)
    assert visit.smoking_status is None


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/791
@pytest.mark.django_db
def test_smoking_status_smoker_does_not_require_cessation_referral_date(
    test_user, single_row_valid_df
):
    """
    Test that smoking status is accepted
    """
    single_row_valid_df.loc[
        0,
        "Date of offer of referral to smoking cessation service (if patient is a current smoker)",
    ] = None
    single_row_valid_df.loc[0, "Does the patient smoke?"] = 2  # Current smoker

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert visit.smoking_cessation_referral_date is None
    assert visit.smoking_status == 2


"""
Dietitian referral tests
"""


@pytest.mark.django_db
def test_dietician_referral_status_additional_offered_form_passes_validation(
    test_user, single_row_valid_df
):
    """
    Test that dietician referral status and date are accepted
    """
    single_row_valid_df.loc[
        0,
        "Was the patient offered an additional appointment with a paediatric dietitian?",
    ] = 1
    single_row_valid_df.loc[0, "Date of additional appointment with dietitian"] = (
        "01/01/2023"
    )

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert visit.dietician_additional_appointment_offered == 1
    assert visit.dietician_additional_appointment_date == datetime.date(2023, 1, 1)


@pytest.mark.django_db
def test_dietician_no_additional_offered_form_passes_validation(
    test_user, single_row_valid_df
):
    """
    Test that dietician referral status and date are accepted
    """
    single_row_valid_df.loc[
        0,
        "Was the patient offered an additional appointment with a paediatric dietitian?",
    ] = 2
    single_row_valid_df.loc[0, "Date of additional appointment with dietitian"] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert visit.dietician_additional_appointment_offered == 2
    assert visit.dietician_additional_appointment_date is None


@pytest.mark.django_db
def test_dietician_no_additional_offered_date_provided_fail_validation(
    test_user, single_row_valid_df
):
    """
    Test that dietician extra appointment not offered but date provided should fail
    """
    single_row_valid_df.loc[
        0,
        "Was the patient offered an additional appointment with a paediatric dietitian?",
    ] = 2
    single_row_valid_df.loc[0, "Date of additional appointment with dietitian"] = (
        "01/01/2023"
    )

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "dietician_additional_appointment_date" in errors[0]

    visit = Visit.objects.first()

    assert visit.dietician_additional_appointment_offered == 2
    assert visit.dietician_additional_appointment_date == datetime.date(2023, 1, 1)


@pytest.mark.django_db
def test_dietician_additional_offered_date_missing_passes_validation(
    test_user, single_row_valid_df
):
    """
    Test that dietician extra appointment offered but date missing should pass
    https://github.com/rcpch/national-paediatric-diabetes-audit/issues/668
    """
    single_row_valid_df.loc[
        0,
        "Was the patient offered an additional appointment with a paediatric dietitian?",
    ] = 1
    single_row_valid_df.loc[0, "Date of additional appointment with dietitian"] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "dietician_additional_appointment_date" not in errors[0]

    visit = Visit.objects.first()

    assert visit.dietician_additional_appointment_offered == 1
    assert visit.dietician_additional_appointment_date is None


@pytest.mark.django_db
def test_dietician_additional_offered_no_but_date_offered_fail_validation(
    test_user, single_row_valid_df
):
    """
    Test that dietician additional appointment answered No but date offered should fail
    """
    single_row_valid_df.loc[
        0,
        "Was the patient offered an additional appointment with a paediatric dietitian?",
    ] = 2
    single_row_valid_df.loc[0, "Date of additional appointment with dietitian"] = (
        "01/01/2023"
    )

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "dietician_additional_appointment_date" in errors[0]

    visit = Visit.objects.first()

    assert visit.dietician_additional_appointment_offered == 2
    assert visit.dietician_additional_appointment_date == datetime.date(2023, 1, 1)


"""
Inpatient admission tests
"""


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_passes_validation(
    test_user, single_row_valid_df
):
    """
    Test that inpatient admission for stabilisation is accepted
    """
    single_row_valid_df.loc[0, "Start date (Hospital Provider Spell)"] = (
        "01/01/2023"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Discharge date (Hospital provider spell)"] = (
        "01/02/2023"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Reason for admission"] = 1  # Stabilisation
    single_row_valid_df.loc[
        0,
        "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
    ] = None
    single_row_valid_df.loc[
        0, "Only complete if OTHER selected: Reason for admission (free text)"
    ] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert visit.hospital_admission_date == datetime.date(
        2023, 1, 1
    ), f"Admission date should be 1/1/2023, but was {visit.hospital_admission_date}"
    assert visit.hospital_discharge_date == datetime.date(
        2023, 1, 2
    ), f"Discharge date should be 2/1/2023, but was {visit.hospital_discharge_date}"
    assert (
        visit.hospital_admission_reason == 1
    ), f"Admission reason should be 1 (stabilisation), but was {visit.hospital_admission_reason}"
    assert (
        visit.dka_additional_therapies == None
    ), f"DKA additional therapies should be None, but was {visit.dka_additional_therapies}"
    assert (
        visit.hospital_admission_other == None
    ), f"Admission other should be None, but was {visit.hospital_admission_other}"


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_missing_date_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that inpatient admission for stabilisation is rejected if date missing
    """
    single_row_valid_df.loc[0, "Start date (Hospital Provider Spell)"] = None
    single_row_valid_df.loc[0, "Discharge date (Hospital provider spell)"] = (
        "01/02/2024"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Reason for admission"] = 1
    single_row_valid_df.loc[
        0,
        "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
    ] = None
    single_row_valid_df.loc[
        0, "Only complete if OTHER selected: Reason for admission (free text)"
    ] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "hospital_admission_date" in errors[0]

    visit = Visit.objects.first()

    assert visit.hospital_admission_date == None
    assert visit.hospital_discharge_date == datetime.date(year=2024, month=1, day=2)
    assert visit.hospital_admission_reason == 1
    assert visit.dka_additional_therapies == None
    assert visit.hospital_admission_other == None


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_discharge_date_before_admission_date_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that inpatient admission for stabilisation is rejected if discharge date before admission date
    """
    single_row_valid_df.loc[0, "Start date (Hospital Provider Spell)"] = (
        "01/08/2022"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Discharge date (Hospital provider spell)"] = (
        "01/01/2023"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Reason for admission"] = 1
    single_row_valid_df.loc[
        0,
        "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
    ] = None
    single_row_valid_df.loc[
        0, "Only complete if OTHER selected: Reason for admission (free text)"
    ] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "hospital_admission_date" in errors[0]

    visit = Visit.objects.first()

    assert visit.hospital_admission_date == datetime.date(year=2022, month=1, day=8)
    assert visit.hospital_discharge_date == datetime.date(year=2023, month=1, day=1)
    assert visit.hospital_admission_reason == 1
    assert visit.dka_additional_therapies == None
    assert visit.hospital_admission_other == None


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_discharge_date_before_diagnosis_date_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that inpatient admission for stabilisation is rejected if discharge date before admission date
    """
    single_row_valid_df.loc[0, "Date of Diabetes Diagnosis"] = "1/10/2021"  # mm/dd/yyyy
    single_row_valid_df.loc[0, "Start date (Hospital Provider Spell)"] = (
        "01/08/2023"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Discharge date (Hospital provider spell)"] = (
        "01/01/2023"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Reason for admission"] = 1
    single_row_valid_df.loc[
        0,
        "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
    ] = None
    single_row_valid_df.loc[
        0, "Only complete if OTHER selected: Reason for admission (free text)"
    ] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "hospital_admission_date" in errors[0]

    visit = Visit.objects.first()

    assert visit.patient.diagnosis_date == datetime.date(
        2021, 1, 10
    ), f"Diagnosis date should be 1/1/2021, but was {visit.patient.diagnosis_date}"
    assert visit.hospital_admission_date == datetime.date(
        2023, 1, 8
    ), f"Admission date should be 8/1/2023, but was {visit.hospital_admission_date}"
    assert visit.hospital_discharge_date == datetime.date(
        2023, 1, 1
    ), f"Discharge date should be 1/1/2023, but was {visit.hospital_discharge_date}"
    assert (
        visit.hospital_admission_reason == 1
    ), f"Admission reason should be 1 (stabilisation), but was {visit.hospital_admission_reason}"
    assert (
        visit.dka_additional_therapies == None
    ), f"DKA additional therapies should be None, but was {visit.dka_additional_therapies}"
    assert (
        visit.hospital_admission_other == None
    ), f"Admission other should be None, but was {visit.hospital_admission_other}"


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_discharge_date_after_date_of_death_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that inpatient admission for stabilisation is rejected if discharge date before admission date
    """
    single_row_valid_df.loc[0, "Death Date"] = "01/01/2022"
    single_row_valid_df.loc[0, "Start date (Hospital Provider Spell)"] = "01/01/2022"
    single_row_valid_df.loc[0, "Discharge date (Hospital provider spell)"] = (
        "01/08/2022"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Reason for admission"] = 1
    single_row_valid_df.loc[
        0,
        "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
    ] = None
    single_row_valid_df.loc[
        0, "Only complete if OTHER selected: Reason for admission (free text)"
    ] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "hospital_discharge_date" in errors[0]

    visit = Visit.objects.first()

    assert visit.patient.death_date == datetime.date(
        2022, 1, 1
    ), f"Date of death should be 1/1/2022, but was {visit.patient.date_of_death}"
    assert visit.hospital_admission_date == datetime.date(
        2022, 1, 1
    ), f"Admission date should be 1/1/2022, but was {visit.hospital_admission_date}"
    assert visit.hospital_discharge_date == datetime.date(
        2022, 1, 8
    ), f"Discharge date should be 8/1/2022, but was {visit.hospital_discharge_date}"
    assert (
        visit.hospital_admission_reason == 1
    ), f"Admission reason should be 1 (stabilisation), but was {visit.hospital_admission_reason}"
    assert (
        visit.dka_additional_therapies == None
    ), f"DKA additional therapies should be None, but was {visit.dka_additional_therapies}"
    assert (
        visit.hospital_admission_other == None
    ), f"Admission other should be None, but was {visit.hospital_admission_other}"


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_dka_additional_therapies_provided_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that inpatient admission for stabilisation is rejected if DKA additional therapies provided
    """
    single_row_valid_df.loc[0, "Start date (Hospital Provider Spell)"] = (
        "01/01/2023"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Discharge date (Hospital provider spell)"] = (
        "01/08/2023"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Reason for admission"] = 1  # Stabilisation
    single_row_valid_df.loc[
        0,
        "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
    ] = 1  # Hypertonic saline
    single_row_valid_df.loc[
        0, "Only complete if OTHER selected: Reason for admission (free text)"
    ] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "dka_additional_therapies" in errors[0]

    visit = Visit.objects.first()

    assert visit.hospital_admission_date == datetime.date(
        2023, 1, 1
    ), f"Admission date should be 1/1/2023, but was {visit.hospital_admission_date}"
    assert visit.hospital_discharge_date == datetime.date(
        2023, 1, 8
    ), f"Discharge date should be 8/1/2023, but was {visit.hospital_discharge_date}"
    assert (
        visit.hospital_admission_reason == 1
    ), f"Admission reason should be 1 (stabilisation), but was {visit.hospital_admission_reason}"
    assert (
        visit.dka_additional_therapies == 1
    ), f"DKA additional therapies should be 1 (hypertonic saline), but was {visit.dka_additional_therapies}"
    assert (
        visit.hospital_admission_other == None
    ), f"Admission other should be None, but was {visit.hospital_admission_other}"


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_hospital_admission_other_provided_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that inpatient admission for stabilisation is rejected if DKA additional therapies provided
    """
    single_row_valid_df.loc[0, "Start date (Hospital Provider Spell)"] = (
        "01/01/2023"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Discharge date (Hospital provider spell)"] = (
        "01/08/2023"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Reason for admission"] = 1  # Stabilisation
    single_row_valid_df.loc[
        0,
        "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
    ] = 1  # Hypertonic saline
    single_row_valid_df.loc[
        0, "Only complete if OTHER selected: Reason for admission (free text)"
    ] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "dka_additional_therapies" in errors[0]

    visit = Visit.objects.first()

    assert visit.hospital_admission_date == datetime.date(
        2023, 1, 1
    ), f"Admission date should be 1/1/2023, but was {visit.hospital_admission_date}"
    assert visit.hospital_discharge_date == datetime.date(
        2023, 1, 8
    ), f"Discharge date should be 8/1/2023, but was {visit.hospital_discharge_date}"
    assert (
        visit.hospital_admission_reason == 1
    ), f"Admission reason should be 1 (stabilisation), but was {visit.hospital_admission_reason}"
    assert (
        visit.dka_additional_therapies == 1
    ), f"DKA additional therapies should be 1 (hypertonic saline), but was {visit.dka_additional_therapies}"
    assert (
        visit.hospital_admission_other == None
    ), f"Admission other should be None, but was {visit.hospital_admission_other}"


@pytest.mark.django_db
def test_inpatient_admission_dka_passes_validation(test_user, single_row_valid_df):
    """
    Test that inpatient admission for DKA with additional therapies is accepted
    """
    single_row_valid_df.loc[0, "Start date (Hospital Provider Spell)"] = (
        "01/01/2023"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Discharge date (Hospital provider spell)"] = (
        "01/08/2023"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Reason for admission"] = 2  # DKA
    single_row_valid_df.loc[
        0,
        "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
    ] = 1  # Hypertonic saline
    single_row_valid_df.loc[
        0, "Only complete if OTHER selected: Reason for admission (free text)"
    ] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert visit.hospital_admission_date == datetime.date(
        2023, 1, 1
    ), f"Admission date should be 1/1/2022, but was {visit.hospital_admission_date}"
    assert visit.hospital_discharge_date == datetime.date(
        2023, 1, 8
    ), f"Discharge date should be 8/1/2022, but was {visit.hospital_discharge_date}"
    assert (
        visit.hospital_admission_reason == 2
    ), f"Admission reason should be 2 (DKA), but was {visit.hospital_admission_reason}"
    assert (
        visit.dka_additional_therapies == 1
    ), f"DKA additional therapies should be 1 (hypertonic saline), but was {visit.dka_additional_therapies}"
    assert (
        visit.hospital_admission_other == None
    ), f"Admission other should be None, but was {visit.hospital_admission_other}"


@pytest.mark.django_db
def test_inpatient_admission_dka_additional_therapies_missing_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that inpatient admission for DKA without additional therapies is rejected
    """
    single_row_valid_df.loc[0, "Start date (Hospital Provider Spell)"] = (
        "01/01/2022"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Discharge date (Hospital provider spell)"] = (
        "01/08/2022"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Reason for admission"] = 2  # DKA
    single_row_valid_df.loc[
        0,
        "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
    ] = None
    single_row_valid_df.loc[
        0, "Only complete if OTHER selected: Reason for admission (free text)"
    ] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "dka_additional_therapies" in errors[0]

    visit = Visit.objects.first()

    assert visit.hospital_admission_date == datetime.date(
        2022, 1, 1
    ), f"Admission date should be 1/1/2022, but was {visit.hospital_admission_date}"
    assert visit.hospital_discharge_date == datetime.date(
        2022, 1, 8
    ), f"Discharge date should be 8/1/2022, but was {visit.hospital_discharge_date}"
    assert (
        visit.hospital_admission_reason == 2
    ), f"Admission reason should be 2 (DKA), but was {visit.hospital_admission_reason}"
    assert (
        visit.dka_additional_therapies == None
    ), f"DKA additional therapies should be None, but was {visit.dka_additional_therapies}"
    assert (
        visit.hospital_admission_other == None
    ), f"Admission other should be None, but was {visit.hospital_admission_other}"


@pytest.mark.django_db
def test_inpatient_admission_dka_additional_therapies_hospital_admission_also_provided_fails_validation(
    test_user, single_row_valid_df
):
    """
    Tests that a hospital admission for DKA with additional therapies is rejected if hospital admission other is provided
    """
    single_row_valid_df.loc[0, "Start date (Hospital Provider Spell)"] = (
        "01/01/2023"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Discharge date (Hospital provider spell)"] = (
        "01/08/2023"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Reason for admission"] = 2  # DKA
    single_row_valid_df.loc[
        0,
        "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
    ] = 1  # Hypertonic saline
    single_row_valid_df.loc[
        0, "Only complete if OTHER selected: Reason for admission (free text)"
    ] = "Other reason"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "hospital_admission_reason" in errors[0]

    visit = Visit.objects.first()

    assert visit.hospital_admission_date == datetime.date(
        2023, 1, 1
    ), f"Admission date should be 1/1/2023, but was {visit.hospital_admission_date}"
    assert visit.hospital_discharge_date == datetime.date(
        2023, 1, 8
    ), f"Discharge date should be 8/1/2023, but was {visit.hospital_discharge_date}"
    assert (
        visit.hospital_admission_reason == 2
    ), f"Admission reason should be 2 (DKA), but was {visit.hospital_admission_reason}"
    assert (
        visit.dka_additional_therapies == 1
    ), f"DKA additional therapies should be 1 (hypertonic saline), but was {visit.dka_additional_therapies}"
    assert (
        visit.hospital_admission_other == "Other reason"
    ), f"Admission other should be 'Other reason', but was {visit.hospital_admission_other}"


@pytest.mark.django_db
def test_inpatient_admission_other_passes_validation(test_user, single_row_valid_df):
    """
    Test that inpatient admission for other reason is accepted
    """
    single_row_valid_df.loc[0, "Start date (Hospital Provider Spell)"] = (
        "01/01/2023"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Discharge date (Hospital provider spell)"] = (
        "01/08/2023"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Reason for admission"] = 6  # Other
    single_row_valid_df.loc[
        0,
        "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
    ] = None
    single_row_valid_df.loc[
        0, "Only complete if OTHER selected: Reason for admission (free text)"
    ] = "Other reason"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert len(errors) == 0, "Should not have any errors but got: " + str(errors)

    visit = Visit.objects.first()

    assert visit.hospital_admission_date == datetime.date(
        2023, 1, 1
    ), f"Admission date should be 1/1/2023, but was {visit.hospital_admission_date}"
    assert visit.hospital_discharge_date == datetime.date(
        2023, 1, 8
    ), f"Discharge date should be 8/1/2023, but was {visit.hospital_discharge_date}"
    assert (
        visit.hospital_admission_reason == 6
    ), f"Admission reason should be 6 (other), but was {visit.hospital_admission_reason}"
    assert (
        visit.dka_additional_therapies == None
    ), f"DKA additional therapies should be None, but was {visit.dka_additional_therapies}"
    assert (
        visit.hospital_admission_other == "Other reason"
    ), f"Admission other should be 'Other reason', but was {visit.hospital_admission_other}"


@pytest.mark.django_db
def test_inpatient_admission_other_missing_fails_validation(
    test_user, single_row_valid_df
):
    """
    Test that inpatient admission for other reason is rejected if reason missing
    """

    single_row_valid_df.loc[0, "Start date (Hospital Provider Spell)"] = (
        "01/01/2023"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Discharge date (Hospital provider spell)"] = (
        "01/08/2023"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Reason for admission"] = 6  # Other
    single_row_valid_df.loc[
        0,
        "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
    ] = None
    single_row_valid_df.loc[
        0, "Only complete if OTHER selected: Reason for admission (free text)"
    ] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "hospital_admission_other" in errors[0]

    visit = Visit.objects.first()

    assert visit.hospital_admission_date == datetime.date(
        2023, 1, 1
    ), f"Admission date should be 1/1/2023, but was {visit.hospital_admission_date}"
    assert visit.hospital_discharge_date == datetime.date(
        2023, 1, 8
    ), f"Discharge date should be 8/1/2023, but was {visit.hospital_discharge_date}"
    assert (
        visit.hospital_admission_reason == 6
    ), f"Admission reason should be 6 (other), but was {visit.hospital_admission_reason}"
    assert (
        visit.dka_additional_therapies == None
    ), f"DKA additional therapies should be None, but was {visit.dka_additional_therapies}"
    assert (
        visit.hospital_admission_other == None
    ), f"Admission other should be None, but was {visit.hospital_admission_other}"


"""
Visit date tests
"""


@pytest.mark.django_db
def test_visit_date_provided_passes_validation(test_user, single_row_valid_df):
    """
    Test that a visit date is accepted
    """
    single_row_valid_df.loc[0, "Visit/Appointment Date"] = "01/01/2023"  # mm/dd/yyyy

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert len(errors) == 0, "Should not have any errors but got: " + str(errors)

    visit = Visit.objects.first()

    assert visit.visit_date == datetime.date(
        2023, 1, 1
    ), f"Visit/Appointment Date should be 1/1/2023, but was {visit.visit_date}"


@pytest.mark.django_db
def test_visit_date_missing_fails_validation(test_user, single_row_valid_df):
    """
    Test that a missing Visit/Appointment Date is rejected
    """
    single_row_valid_df.loc[0, "Visit/Appointment Date"] = None

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=None)

    assert "visit_date" in errors[0], f"Expected error in visit_date, but got None"

    visit = Visit.objects.first()

    assert (
        visit.visit_date == None
    ), f"Visit/Appointment Date should be None, but was {visit.visit_date}"


@pytest.mark.django_db
def test_visit_date_not_before_date_of_birth(test_user, single_row_valid_df):
    """
    Test that a Visit/Appointment Date before the date of birth is rejected
    """
    single_row_valid_df.loc[0, "Date of Birth"] = "01/01/2022"
    single_row_valid_df.loc[0, "Visit/Appointment Date"] = "01/01/2021"  # mm/dd/yyyy

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "visit_date" in errors[0]

    visit = Visit.objects.first()

    assert visit.visit_date == datetime.date(
        2021, 1, 1
    ), f"Visit date should be 1/1/2021, but was {visit.visit_date}"
    assert visit.patient.date_of_birth == datetime.date(
        2022, 1, 1
    ), f"Date of birth should be 1/1/2022, but was {visit.patient.date_of_birth}"


@pytest.mark.django_db
def test_visit_date_not_after_date_of_death(test_user, single_row_valid_df):
    """
    Test that a Visit/Appointment Date after the date of death is rejected
    """
    single_row_valid_df.loc[0, "Death Date"] = "01/01/2022"  # mm/dd/yyyy
    single_row_valid_df.loc[0, "Visit/Appointment Date"] = "01/01/2023"  # mm/dd/yyyy

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "visit_date" in errors[0]

    visit = Visit.objects.first()

    assert visit.visit_date == datetime.date(
        2023, 1, 1
    ), f"Visit date should be 1/1/2023, but was {visit.visit_date}"
    assert visit.patient.death_date == datetime.date(
        2022, 1, 1
    ), f"Death date should be 1/1/2022, but was {visit.patient.death_date}"


@pytest.mark.django_db
def test_visit_date_not_before_diagnosis_date(test_user, single_row_valid_df):
    """
    Test that a Visit/Appointment Date before the date of diagnosis is rejected
    """
    single_row_valid_df.loc[0, "Date of Diabetes Diagnosis"] = (
        "01/01/2022"  # mm/dd/yyyy
    )
    single_row_valid_df.loc[0, "Visit/Appointment Date"] = "01/01/2021"  # mm/dd/yyyy

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=single_row_valid_df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "visit_date" in errors[0]

    visit = Visit.objects.first()

    assert visit.visit_date == datetime.date(
        year=2021, month=1, day=1
    ), f"Visit date should be 1/1/2021, but was {visit.visit_date}"
    assert visit.patient.diagnosis_date == datetime.date(
        year=2022, month=1, day=1
    ), f"Diagnosis date should be 1/1/2022, but was {visit.patient.diagnosis_date}"


@pytest.mark.parametrize(
    "alternative,expected",
    [
        pytest.param("Unknown", 99),
        pytest.param("unknown", 99),
        pytest.param("M", 1),
        pytest.param("m", 1),
        pytest.param("F", 2),
        pytest.param("f", 2),
    ],
)
@pytest.mark.django_db
def test_alternative_formats_for_sex(test_user, dummy_sheet_csv, alternative, expected):
    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[{"row": 1, "column": "Stated gender", "value": alternative}],
    )

    df = read_csv_from_str(one_row_csv).df

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, df, _audit_period=audit_period)
    assert len(errors) == 0

    patient = Patient.objects.first()
    assert patient.sex == expected


@pytest.mark.django_db
def test_mix_of_standard_and_alternative_formats_for_sex(test_user, dummy_sheet_csv):
    two_rows_csv = modify_raw_csv(
        dummy_sheet_csv,
        start=2,  # inclusive
        end=4,  # exclusive
        replacements=[{"row": 2, "column": "Stated gender", "value": "M"}],
    )

    df = read_csv_from_str(two_rows_csv).df

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    # Double check we do have different patients
    assert df["NHS Number"].nunique() == 2

    errors = csv_upload_sync(test_user, df, _audit_period=audit_period)
    assert len(errors) == 0

    [patient1, patient2] = Patient.objects.all()

    assert patient1.sex == 1
    assert patient2.sex == 1


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("7"),
        pytest.param("TOO_LONG"),
    ],
)
@pytest.mark.django_db
def test_bad_data_for_ethnic_category(test_user, dummy_sheet_csv, value):
    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[{"row": 1, "column": "Ethnic Category", "value": value}],
    )

    df = read_csv_from_str(one_row_csv).df

    errors = csv_upload_sync(test_user, df)
    assert len(errors) > 0

    patient = Patient.objects.first()

    assert patient.ethnicity == None
    assert "ethnicity" in patient.errors


@pytest.mark.parametrize(
    "model_field",
    [
        pytest.param("reason_leaving_service"),
        pytest.param("hba1c_format"),
        pytest.param("treatment"),
        pytest.param("closed_loop_system"),
        pytest.param("glucose_monitoring"),
        pytest.param("retinal_screening_result"),
        pytest.param("albuminuria_stage"),
        pytest.param("thyroid_treatment_status"),
        pytest.param("gluten_free_diet"),
        pytest.param("psychological_additional_support_status"),
        pytest.param("smoking_status"),
        pytest.param("dietician_additional_appointment_offered"),
        pytest.param("ketone_meter_training"),
        pytest.param("hospital_admission_reason"),
        pytest.param("dka_additional_therapies"),
    ],
)
@pytest.mark.django_db
def test_bad_data_for_positive_small_integer_fields(
    test_user, dummy_sheet_csv, model_field
):
    headings = csv_definition_for(model_field)

    column = headings["heading"]
    model = apps.get_model("npda", headings["model"])

    pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)

    for [value, expected, assertion_message] in [
        [94, None, f"Failed to handle {model_field} with incorrect choice (94)"],
        [-1, None, f"Failed to handle {model_field} with -1 (negative number)"],
        [99.5, None, f"Failed to handle {model_field} with 99.5 (float)"],
        [
            9999,
            None,
            f"Failed to handle {model_field} with 9999 (value bigger than int8)",
        ],
        [
            32768,
            None,
            f"Failed to handle {model_field} 32768 (value bigger than Django small integer field)",
        ],
        ["STRING", None, f"Failed to handle unexpected string for {model_field}"],
    ]:
        # Clear out patients created by previous iterations of the loop
        Patient.objects.all().delete()

        one_row_csv = modify_raw_csv(
            dummy_sheet_csv,
            end=2,  # exclusive
            replacements=[{"row": 1, "column": column, "value": value}],
        )

        df = read_csv_from_str(one_row_csv).df

        errors = csv_upload_sync(test_user, df, pdu=pdu)

        assert len(errors) > 0, assertion_message
        assert model.objects.count() == 1, assertion_message

        instance = model.objects.first()

        assert getattr(instance, model_field) == expected, assertion_message

        # No errors field in Transfer
        if hasattr(instance, "errors"):
            assert model_field in instance.errors



@pytest.mark.parametrize(
    "model_field",
    [
        pytest.param("systolic_blood_pressure"),
        pytest.param("diastolic_blood_pressure"),
    ],
)
@pytest.mark.django_db
def test_bad_data_for_integer_fields(test_user, dummy_sheet_csv, model_field):
    headings = csv_definition_for(model_field)

    column = headings["heading"]
    model = apps.get_model("npda", headings["model"])

    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[{"row": 1, "column": column, "value": "STRING"}],
    )

    df = read_csv_from_str(one_row_csv).df

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, df, _audit_period=audit_period)

    assert len(errors) > 0
    assert model.objects.count() == 1

    instance = model.objects.first()

    assert getattr(instance, model_field) == None
    assert model_field in instance.errors


@pytest.mark.parametrize(
    "model_field",
    [
        pytest.param("date_leaving_service"),
        pytest.param("death_date"),
        pytest.param("visit_date"),
        pytest.param("height_weight_observation_date"),
        pytest.param("hba1c_date"),
        pytest.param("blood_pressure_observation_date"),
        pytest.param("foot_examination_observation_date"),
        pytest.param("retinal_screening_observation_date"),
        pytest.param("albumin_creatinine_ratio_date"),
        pytest.param("total_cholesterol_date"),
        pytest.param("thyroid_function_date"),
        pytest.param("coeliac_screen_date"),
        pytest.param("psychological_screening_assessment_date"),
        pytest.param("smoking_cessation_referral_date"),
        pytest.param("carbohydrate_counting_level_three_education_date"),
        pytest.param("dietician_additional_appointment_date"),
        pytest.param("flu_immunisation_recommended_date"),
        pytest.param("sick_day_rules_training_date"),
        pytest.param("hospital_admission_date"),
        pytest.param("hospital_discharge_date"),
    ],
)
@pytest.mark.django_db
def test_bad_data_for_date_fields(test_user, dummy_sheet_csv, model_field):
    headings = csv_definition_for(model_field)

    column = headings["heading"]
    model = apps.get_model("npda", headings["model"])

    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[{"row": 1, "column": column, "value": "NOT A DATE"}],
    )

    results = read_csv_from_str(one_row_csv)

    # Slightly janky - date format errors are returned separately from parse_csv
    # as they are swallowed up into NaT and we cannot later distinguish between
    # that an the cell being empty in the CSV upload. To avoid rewriting all the usage
    # of csv_upload_sync across all tests we assert in two stages here
    errors = results.errors_to_return

    assert len(errors) > 0
    assert model_field in errors[0]

    csv_upload_sync(test_user, results.df, errors_to_return=errors)

    assert model.objects.count() == 1

    instance = model.objects.first()
    assert getattr(instance, model_field) == None


@pytest.mark.parametrize(
    "model_field",
    [
        pytest.param("height"),
        pytest.param("weight"),
        pytest.param("hba1c"),
        pytest.param("albumin_creatinine_ratio"),
        pytest.param("total_cholesterol"),
    ],
)
@pytest.mark.django_db
def test_bad_data_for_decimal_fields(test_user, dummy_sheet_csv, model_field):
    headings = csv_definition_for(model_field)

    column = headings["heading"]
    model = apps.get_model("npda", headings["model"])

    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[{"row": 1, "column": column, "value": "STRING"}],
    )

    df = read_csv_from_str(one_row_csv).df

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, df, _audit_period=audit_period)

    assert len(errors) > 0
    assert model.objects.count() == 1

    instance = model.objects.first()

    assert getattr(instance, model_field) == None
    assert model_field in instance.errors

# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/999
@pytest.mark.django_db
def test_non_breaking_space_in_iso_8859_1_csv(test_user, dummy_sheet_csv):
    """
    Test that a non-breaking space in an ISO-8859-1 CSV is handled correctly
    """
    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[{"row": 1, "column": "NHS Number", "value": "4773730404\xa0"}],
    )

    df = read_csv_from_str(one_row_csv, encoding="iso-8859-1").df

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, df, _audit_period=audit_period)

    assert len(errors) == 0

@pytest.mark.django_db
def test_remove_empty_spaces_from_empty_fields(test_user, dummy_sheet_csv):
    """
    Test that empty spaces in empty fields are removed
    """
    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[{"row": 1, "column": "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?", "value": "   "}],
    )

    df = read_csv_from_str(one_row_csv).df

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, df, _audit_period=audit_period)

    assert len(errors) == 0

    patient = Patient.objects.first()
    assert Visit.objects.filter(patient=patient).first().dka_additional_therapies == None, f"Expected empty string for DKA additional therapies, but got {Visit.objects.filter(patient=patient).first().dka_additional_therapies}"

@pytest.mark.django_db
def test_remove_empty_spaces_in_empty_date_fields(test_user, dummy_sheet_csv):
    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[{"row": 1, "column": "Death Date", "value": "   "}],
    )

    parsed_csv = read_csv_from_str(one_row_csv)
    assert len(parsed_csv.errors_to_return) == 0, f"Expected no errors when parsing CSV, got {parsed_csv.errors_to_return}"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=parsed_csv.df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, parsed_csv.df, _audit_period=audit_period, errors_to_return=parsed_csv.errors_to_return)

    assert len(errors) == 0, f"Expected no errors when uploading CSV, got {errors}"

@pytest.mark.django_db
def test_csv_height_weight_fields_with_units_have_units_removed(test_user, dummy_sheet_csv):
    """
    Test that height and weight fields with units have the units removed
    """
    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[
            {"row": 1, "column": "Patient Height (cm)", "value": "150 cm"},
            {"row": 1, "column": "Patient Weight (kg)", "value": "50 kg"},
        ],
    )

    df = read_csv_from_str(one_row_csv).df

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, df, _audit_period=audit_period)

    assert len(errors) == 0

    patient = Patient.objects.first()
    visit = Visit.objects.filter(patient=patient).first()

    assert visit.height == Decimal("150.0"), f"Expected height to be 150.0, but got {visit.height}"
    assert visit.weight == Decimal("50.0"), f"Expected weight to be 50.0, but got {visit.weight}"

@pytest.mark.django_db
def test_submission_has_audit_period_attached(test_user, single_row_valid_df):
    audit_period = AuditPeriod.objects.first()

    Submission.objects.all().delete()  # Clear any previous submissions

    csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert Submission.objects.count() == 1, "Expected one submission to be created"
    submission = Submission.objects.first()

    assert submission.audit_period == audit_period, f"Expected submission to have audit period {audit_period}, but got {submission.audit_period}"

@pytest.mark.django_db
def test_visit_with_too_big_decimal_number_still_saves(test_user, dummy_sheet_csv):
    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[{"row": 1, "column": "Patient Weight (kg)", "value": "3405.5"}],
    )

    parsed_csv = read_csv_from_str(one_row_csv)
    assert len(parsed_csv.errors_to_return) == 0, f"Expected no errors when parsing CSV, got {parsed_csv.errors_to_return}"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=parsed_csv.df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, parsed_csv.df, _audit_period=audit_period, errors_to_return=parsed_csv.errors_to_return)
    
    assert "weight" in errors[0], f"Expected weight to be in errors, but got {errors}"

    assert Visit.objects.count() == 1, "Expected one visit to be created"
    visit = Visit.objects.first()

    assert visit.weight == Decimal(0)
    assert "weight" in visit.errors, f"Expected weight to have an error, but got {visit.errors}"

@pytest.mark.django_db
def test_visit_with_too_precise_decimal_number_is_rounded(test_user, dummy_sheet_csv):
    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[{"row": 1, "column": "Patient Weight (kg)", "value": "34.12345612"}],
    )

    parsed_csv = read_csv_from_str(one_row_csv)
    assert len(parsed_csv.errors_to_return) == 0, f"Expected no errors when parsing CSV, got {parsed_csv.errors_to_return}"

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(date_instance=parsed_csv.df["Visit/Appointment Date"][0].date())
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, parsed_csv.df, errors_to_return=parsed_csv.errors_to_return, _audit_period=audit_period)
    assert len(errors) == 0, f"Expected no errors when uploading CSV, got {errors}"

    assert Visit.objects.count() == 1, "Expected one visit to be created"
    visit = Visit.objects.first()

    assert visit.weight == Decimal('34.1')

# testing dates outside of the range of the audit period
@pytest.mark.django_db
def test_visit_form_dates_outside_of_audit_period(test_user, single_row_valid_df, seed_audit_periods_fixture):
    """
    Test that all dates outside in a visit of the audit period are flagged as errors, but the visit is still created
    2024 / 2025 audit period is seeded in the fixture
    All the dates tested include:
        visit_date
        height_weight_observation_date
        hba1c_date
        blood_pressure_observation_date
        foot_examination_observation_date
        retinal_screening_observation_date
        albumin_creatinine_ratio_date
        total_cholesterol_date
        thyroid_function_date
        coeliac_screen_date
        psychological_screening_assessment_date
        smoking_cessation_referral_date
        carbohydrate_counting_level_three_education_date
        dietician_additional_appointment_date
        flu_immunisation_recommended_date
        sick_day_rules_training_date
        hospital_admission_date
        **hospital_discharge_date NOT INCLUDED AS IT IS POSSIBLE TO BE DISCHARGED AFTER THE AUDIT ENDS**
    """
    audit_period = AuditPeriod.objects.first() # this will be 2024 / 2025
    # set date of birth to 01/01/2015 as this cannot be after the other mocked dates
    single_row_valid_df.loc[0, "Date of Birth"] = "01/01/2015"
    # set date of diabetes diagnosis to 01/01/2018 as this cannot be after the other mocked dates
    single_row_valid_df.loc[0, "Date of Diabetes Diagnosis"] = "01/01/2018"
    # set a smoking cessation outcome
    single_row_valid_df.loc[0, "Does the patient smoke?"] = 2 # Current smoker
    # set reason for admission to 1 (stabilisation) as this is required for the hospital admission dates
    single_row_valid_df.loc[0, "Reason for admission"] = 1 # Stabilisation

    # set all the dates associated with the visit to 01/01/2020
    for date_field in ALL_VISIT_DATES:
        single_row_valid_df.loc[0, date_field] = "01/01/2020"
    
    # REMOVE the hospital discharge date as this is not included in the test
    ALL_VISIT_DATES.remove(("hospital_discharge_date", "Discharge date (Hospital provider spell)"))

    assert Visit.objects.count() == 0, "Expected no visits to be created before the test"
    
    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)
    for date_field in ALL_VISIT_DATES:
        assert date_field[0] in errors[0], f"Expected {date_field} to be in errors, but got {errors}"
    assert Visit.objects.count() == 1, "Expected the visit still to be created even though visit date outside of audit period"
