import collections
import csv
import dataclasses
import datetime
import re
import tempfile
import unicodedata
from datetime import date
from decimal import Decimal
from io import StringIO
from unittest.mock import AsyncMock, patch

import nhs_number
import numpy as np
import pandas as pd
import pytest
from asgiref.sync import async_to_sync
from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.contrib.gis.geos import Point
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.urls import reverse
from freezegun import freeze_time

from project.constants import (
    ALL_VISIT_DATES,
    DIABETES_TYPES,
    ETHNICITIES,
    LEAVE_PDU_REASONS,
    SEX_TYPE,
    csv_definition_for,
    get_all_visit_dates,
)
from project.constants.user import RCPCH_AUDIT_TEAM
from project.npda.forms.external_patient_validators import (
    PatientExternalValidationResult,
)
from project.npda.forms.external_visit_validators import (
    CentileAndSDS,
    VisitExternalValidationResult,
)
from project.npda.general_functions.csv import (
    create_csv_submission,
    csv_clean,
    csv_parse,
    csv_upload,
)
from project.npda.general_functions.headings import (
    get_field_heading,
)
from project.npda.general_functions.quarter_for_date import (
    current_audit_year_start_date,
)
from project.npda.models import (
    AuditPeriod,
    NPDAUser,
    PaediatricDiabetesUnit,
    Patient,
    Submission,
    Transfer,
    Visit,
)
from project.npda.tests.factories.patient_factory import (
    INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE,
    TODAY,
    VALID_FIELDS,
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


def _sex_heading_for_df(df):
    return _heading_for_df("sex", df)


def _sex_heading_for_csv_string(csv_str):
    return _heading_for_csv_string("sex", csv_str)


def _heading_for_df(field_name, df, years=(2026, 2021)):
    """Return the column heading for `field_name` present in the dataframe.

    Tries the provided `years` in order and falls back to the last year's heading.
    """
    for year in years:
        heading = get_field_heading(field_name, year)
        if heading in df.columns:
            return heading

    return get_field_heading(field_name, years[-1])


def _heading_for_csv_string(field_name, csv_str, years=(2026, 2021)):
    """Return the column heading for `field_name` present in a CSV string's header row."""
    import csv as _csv

    reader = _csv.reader(csv_str.splitlines())
    header = next(reader)
    for year in years:
        heading = get_field_heading(field_name, year)
        if heading in header:
            return heading

    return get_field_heading(field_name, years[-1])


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
RCPCH_PZ_CODE = "PZ999"


@pytest.fixture
def valid_df(dummy_sheets_folder):
    file = dummy_sheets_folder / "dummy_sheet_test.csv"
    return csv_parse(file).df


@pytest.fixture(params=[2021, 2026])
def dataset_year(request):
    return request.param


@pytest.fixture
def dummy_sheet_csv(dummy_sheets_folder, dataset_year):
    """Override the conftest fixture to return the correct CSV for the dataset year."""
    filename = (
        "dummy_sheet_2026_test.csv" if dataset_year == 2026 else "dummy_sheet_test.csv"
    )
    file = dummy_sheets_folder / filename
    with open(file) as f:
        return f.read()


@pytest.fixture
def single_row_valid_df(dummy_sheets_folder, dataset_year):
    filename = (
        "dummy_sheet_2026_test.csv" if dataset_year == 2026 else "dummy_sheet_test.csv"
    )
    file = dummy_sheets_folder / filename
    df = csv_parse(file, dataset_year=dataset_year).df
    csv_clean(df, dataset_year=dataset_year)
    df = df.head(1)
    return df


@pytest.fixture
def audit_period_for_dataset_year(dataset_year):
    """Create an AuditPeriod for the supplied dataset_year for tests.

    Tests that need a matching audit period for the CSV can depend on this
    fixture and pass it into `csv_upload_sync` as `_audit_period`.
    """
    slug = f"{dataset_year}-{dataset_year + 1}"
    audit_period, _created = AuditPeriod.objects.get_or_create(
        slug=slug,
        defaults={
            "is_open": True,
            "is_visible": True,
            "start_date": date(dataset_year, 4, 1),
            "end_date": date(dataset_year + 1, 3, 31),
        },
    )

    # Ensure dates/visibility are set to expected values even if the object existed
    audit_period.is_open = True
    audit_period.is_visible = True
    audit_period.start_date = date(dataset_year, 4, 1)
    audit_period.end_date = date(dataset_year + 1, 3, 31)
    audit_period.save()

    return audit_period


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
def one_patient_with_four_visits(dummy_sheets_folder):
    file = dummy_sheets_folder / "one_patient_four_visits.csv"
    df = csv_parse(file).df

    return df


@pytest.fixture
def test_user(seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture):
    return NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()


@pytest.fixture
def test_rcpch_user(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    return NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE, role=RCPCH_AUDIT_TEAM
    ).first()


@pytest.fixture
def freeze_for_audit(audit_period_for_dataset_year):
    with freeze_time(audit_period_for_dataset_year.end_date - relativedelta(days=1)):
        yield


# The database is not rolled back if we used the built in async support for pytest
# https://github.com/pytest-dev/pytest-asyncio/issues/226
def csv_upload_sync(
    user, dataframe, pdu=None, errors_to_return=None, _audit_period=None
):
    # If an explicit audit period is provided use it, otherwise try to
    # infer an appropriate AuditPeriod from the dataframe's visit date so
    # tests that supply 2026 CSVs get a matching 2026 audit period.
    if _audit_period:
        audit_period = _audit_period
    else:
        audit_period = None

        # Try to find a visit date column from the known visit date headings
        for _field, heading in ALL_VISIT_DATES:
            if heading in dataframe.columns:
                try:
                    first_visit = dataframe[heading].iloc[0]
                except Exception:
                    first_visit = None

                if first_visit is not None and not pd.isna(first_visit):
                    # Normalize to a date instance if it's a Timestamp
                    date_instance = (
                        first_visit.date()
                        if hasattr(first_visit, "date")
                        else first_visit
                    )

                    start_date = current_audit_year_start_date(
                        date_instance=date_instance
                    )

                    audit_period = AuditPeriod.objects.filter(
                        start_date=start_date
                    ).first()
                    break

        # Fallback to the first seeded audit period if we couldn't infer
        if not audit_period:
            audit_period = AuditPeriod.objects.first()

    if not pdu:
        pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)

    new_submission = create_csv_submission(
        pdu=pdu,
        audit_period=audit_period,
        csv_file_bytes=None,
        csv_file_name=None,
        submission_active=True,
        user=user,
        ip_address=None,
        new_dataframe=dataframe,
    )

    return async_to_sync(csv_upload)(
        dataframe,
        errors_to_return=(
            collections.defaultdict(lambda: collections.defaultdict(list))
            if errors_to_return is None
            else errors_to_return
        ),
        csv_file_name=None,
        submission=new_submission,
    )


def read_csv_from_str(contents, encoding="utf-8", dataset_year=None):
    with tempfile.NamedTemporaryFile() as f:
        # remove the daggers!
        contents = contents.replace("\u2020", "").replace("\u2021", "")
        f.write(contents.encode(encoding))
        f.seek(0)

        # If dataset_year is not provided, try parsing using 2026 headings first
        # (the dummy CSV fixtures are dataset-year-specific). If both parses
        # succeed, pick the one that best matches the file (fewest missing
        # columns) or that reports more parsing errors (so tests that expect
        # parse-time errors continue to work). This avoids silently accepting
        # a successful but incorrect year parse.
        if dataset_year is None:
            try:
                res_2026 = csv_parse(f, dataset_year=2026)
            except Exception:
                f.seek(0)
                return csv_parse(f)

            f.seek(0)
            try:
                res_default = csv_parse(f)
            except Exception:
                return res_2026

            # Prefer the parse that reported more parsing errors (so tests
            # expecting parse-time errors continue to work). If both report
            # the same number of errors, break ties by choosing the parse
            # with fewer missing columns.
            if len(res_default.errors_to_return) > len(res_2026.errors_to_return):
                return res_default
            if len(res_2026.errors_to_return) > len(res_default.errors_to_return):
                return res_2026

            # Tie-breaker: fewer missing columns
            if len(res_default.missing_columns) <= len(res_2026.missing_columns):
                return res_default
            return res_2026
        return csv_parse(f, dataset_year=dataset_year)


def modify_raw_csv(csv_str, start=None, end=None, replacements=None):
    # Sometimes we have to alter the CSV directly to test values
    # of the wrong type.
    if replacements is None:
        replacements = {}
    reader = csv.reader(StringIO(csv_str))
    [header, *rows] = list(reader)

    start_ix = 0 if start is None else start - 1
    end_ix = len(rows) if end is None else end - 1

    rows = rows[start_ix:end_ix]

    def _normalize_heading(s: str) -> str:
        nk = unicodedata.normalize("NFKD", s)
        nk = "".join(ch for ch in nk if not unicodedata.combining(ch))
        nk = re.sub(r"[^0-9a-zA-Z]+", " ", nk)
        nk = re.sub(r"\s+", " ", nk).strip().lower()
        return nk

    # build normalized header index for fallback matches
    normalized_index = {_normalize_heading(h): i for i, h in enumerate(header)}

    for replacement in replacements:
        row_ix = replacement["row"] - 1
        column = replacement["column"]
        value = replacement["value"]

        try:
            column_ix = header.index(column)
        except ValueError:
            # fallback to normalized matching (strip footnote marks etc.)
            norm = _normalize_heading(column)
            if norm in normalized_index:
                column_ix = normalized_index[norm]
            else:
                raise ValueError(
                    f"Column '{column}' not found in CSV headers"
                ) from None

        rows[row_ix][column_ix] = value

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(header)
    writer.writerows(rows)

    return output.getvalue()


@pytest.mark.django_db
def test_create_patient(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    csv_upload_sync(
        test_user,
        single_row_valid_df,
        _audit_period=audit_period_for_dataset_year,
    )
    patient = Patient.objects.first()

    # Resolve canonical headings for this dataset year to make the test dataset-aware
    nhs_heading = get_field_heading("nhs_number", dataset_year)
    dob_heading = get_field_heading("date_of_birth", dataset_year)
    diabetes_type_heading = get_field_heading("diabetes_type", dataset_year)
    diagnosis_date_heading = get_field_heading("diagnosis_date", dataset_year)

    assert patient.nhs_number == nhs_number.standardise_format(
        single_row_valid_df[nhs_heading][0]
    )
    assert patient.date_of_birth == single_row_valid_df[dob_heading][0].date()
    assert patient.diabetes_type == single_row_valid_df[diabetes_type_heading][0]
    assert (
        patient.diagnosis_date == single_row_valid_df[diagnosis_date_heading][0].date()
    )
    assert patient.death_date is None


@pytest.mark.django_db
def test_create_patient_with_death_date(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    # set the death date to fall within the audit period
    death_date = audit_period_for_dataset_year.start_date + relativedelta(months=6)
    single_row_valid_df.loc[0, "Death Date"] = pd.to_datetime(death_date)
    # set visit date to avoid audit period conflict
    visit_heading = get_field_heading("visit_date", dataset_year)
    single_row_valid_df.loc[0, visit_heading] = death_date - relativedelta(months=1)

    csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    patient = Patient.objects.first()

    assert patient.death_date == single_row_valid_df["Death Date"][0].date()


@pytest.mark.django_db
def test_multiple_patients(
    test_user,
    two_patients_first_with_two_visits_second_with_one,
    audit_period_for_dataset_year,
):
    df = two_patients_first_with_two_visits_second_with_one

    assert df["NHS Number"][0] == df["NHS Number"][1]
    assert df["NHS Number"][0] != df["NHS Number"][2]

    csv_upload_sync(test_user, df, _audit_period=audit_period_for_dataset_year)

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
    audit_period_for_dataset_year,
):
    # As this test needs full transaction support we can't use our session fixtures
    test_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    # Delete all patients to ensure we're starting from a clean slate
    Patient.objects.all().delete()

    single_row_valid_df.loc[0, "Date of Birth"] = None

    assert Patient.objects.count() == 0, (
        "There should be no patients in the database before the test"
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "date_of_birth" in errors[0]

    # Catastrophic - we can't save this patient at all
    assert Patient.objects.count() == 0


@pytest.mark.django_db
def test_missing_nhs_number(
    seed_groups_per_function_fixture,
    seed_users_per_function_fixture,
    seed_audit_periods_per_function_fixture,
    single_row_valid_df,
    audit_period_for_dataset_year,
):
    # As these tests need full transaction support we can't use our session fixtures
    test_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    # Delete all patients to ensure we're starting from a clean slate
    Patient.objects.all().delete()

    single_row_valid_df.loc[0, "NHS Number"] = None

    assert Patient.objects.count() == 0, (
        "There should be no patients in the database before the test"
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "nhs_number" in errors[0]

    # We shouldn't save this patient (invariant enforced in Patient.clean not in the database)
    assert Patient.objects.count() == 0


@pytest.mark.django_db
def test_missing_date_of_diagnosis(
    test_user, single_row_valid_df, audit_period_for_dataset_year
):
    single_row_valid_df.loc[0, "Date of Diabetes Diagnosis"] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "diagnosis_date" in errors[0]

    assert Patient.objects.count() == 1

    patient = Patient.objects.first()
    assert patient.diagnosis_date is None


@pytest.mark.django_db
def test_missing_diabetes_type(
    test_user, single_row_valid_df, audit_period_for_dataset_year
):
    single_row_valid_df.loc[0, "Diabetes Type"] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

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
    audit_period.start_date = current_audit_year_start_date(
        date_instance=df["Visit/Appointment Date"][1].date()
    )
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
    audit_period.start_date = current_audit_year_start_date(
        date_instance=df["Visit/Appointment Date"][1].date()
    )
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
    test_user, two_patients_with_one_visit_each, audit_period_for_dataset_year
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

    errors = csv_upload_sync(test_user, df, _audit_period=audit_period_for_dataset_year)

    assert "treatment" in errors[0]
    assert "treatment" in errors[1]

    [patient_one, patient_two] = Patient.objects.all()

    assert Visit.objects.count() == 2

    visit_for_first_patient = Visit.objects.filter(patient=patient_one).first()
    visit_for_second_patient = Visit.objects.filter(patient=patient_two).first()

    assert visit_for_first_patient.treatment is None
    assert "treatment" in visit_for_first_patient.errors

    assert visit_for_second_patient.treatment is None
    assert "treatment" in visit_for_second_patient.errors


@pytest.mark.django_db
def test_invalid_nhs_number(
    test_user, single_row_valid_df, audit_period_for_dataset_year
):
    invalid_nhs_number = "123456789"
    single_row_valid_df["NHS Number"] = invalid_nhs_number

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "nhs_number" in errors[0]

    patient = Patient.objects.first()
    assert patient.nhs_number == "123456789"


@pytest.mark.django_db
def test_future_date_of_birth(
    test_user, single_row_valid_df, audit_period_for_dataset_year
):
    date_of_birth = TODAY + relativedelta(days=1)
    single_row_valid_df["Date of Birth"] = pd.to_datetime(date_of_birth)

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "date_of_birth" in errors[0]

    patient = Patient.objects.first()

    assert patient.date_of_birth == date_of_birth
    assert "date_of_birth" in patient.errors

    error_message = patient.errors["date_of_birth"][0]["message"]
    assert error_message == "Cannot be in the future"


@pytest.mark.django_db
def test_over_25(test_user, single_row_valid_df, audit_period_for_dataset_year):
    date_of_birth = TODAY + -relativedelta(years=25, days=1)
    single_row_valid_df["Date of Birth"] = pd.to_datetime(date_of_birth)

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "date_of_birth" in errors[0]

    patient = Patient.objects.first()

    assert patient.date_of_birth == date_of_birth
    assert "date_of_birth" in patient.errors

    error_message = patient.errors["date_of_birth"][0]["message"]
    assert error_message == "NPDA patients cannot be 25+ years old. This patient is 25"


@pytest.mark.django_db
def test_future_diagnosis_date(
    test_user, single_row_valid_df, audit_period_for_dataset_year
):
    diagnosis_date = TODAY + relativedelta(days=1)
    single_row_valid_df["Date of Diabetes Diagnosis"] = pd.to_datetime(diagnosis_date)

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "diagnosis_date" in errors[0]

    patient = Patient.objects.first()

    assert patient.diagnosis_date == diagnosis_date
    assert "diagnosis_date" in patient.errors

    error_message = patient.errors["diagnosis_date"][0]["message"]
    assert error_message == "Cannot be in the future"


@pytest.mark.django_db
def test_diagnosis_date_before_date_of_birth(
    test_user, single_row_valid_df, audit_period_for_dataset_year
):
    date_of_birth = (VALID_FIELDS["date_of_birth"],)
    diagnosis_date = VALID_FIELDS["date_of_birth"] - relativedelta(years=1)

    single_row_valid_df["Date of Diabetes Diagnosis"] = pd.to_datetime(diagnosis_date)

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

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
def test_invalid_sex(test_user, single_row_valid_df, audit_period_for_dataset_year):
    single_row_valid_df[_sex_heading_for_df(single_row_valid_df)] = 45

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "sex" in errors[0]

    patient = Patient.objects.first()

    assert patient.sex is None
    assert "sex" in patient.errors


@pytest.mark.django_db
def test_not_specified_sex(
    test_user, single_row_valid_df, audit_period_for_dataset_year
):
    single_row_valid_df[_sex_heading_for_df(single_row_valid_df)] = 3

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "sex" not in errors[0]

    patient = Patient.objects.first()

    assert patient.sex == 3
    assert patient.errors is None


@pytest.mark.django_db
def test_unknown_sex(test_user, single_row_valid_df, audit_period_for_dataset_year):
    single_row_valid_df[_sex_heading_for_df(single_row_valid_df)] = 99

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "sex" not in errors[0]

    patient = Patient.objects.first()

    assert patient.sex == 99
    assert patient.errors is None


@pytest.mark.django_db
def test_missing_gp_ods_code(
    test_user, single_row_valid_df, audit_period_for_dataset_year
):
    single_row_valid_df["GP Practice Code"] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
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
def test_future_death_date(
    test_user, single_row_valid_df, audit_period_for_dataset_year
):
    death_date = TODAY + relativedelta(days=1)

    single_row_valid_df["Death Date"] = pd.to_datetime(death_date)

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "death_date" in errors[0]

    patient = Patient.objects.first()

    assert patient.death_date == death_date
    assert "death_date" in patient.errors

    error_message = patient.errors["death_date"][0]["message"]
    assert error_message == "Cannot be in the future"


@pytest.mark.django_db
def test_death_date_before_date_of_birth(
    test_user, single_row_valid_df, audit_period_for_dataset_year
):
    date_of_birth = (VALID_FIELDS["date_of_birth"],)
    death_date = VALID_FIELDS["date_of_birth"] - relativedelta(years=1)

    single_row_valid_df["Death Date"] = pd.to_datetime(death_date)

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
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
def test_invalid_postcode(
    test_user, single_row_valid_df, audit_period_for_dataset_year
):
    single_row_valid_df["Postcode of usual address"] = "not a postcode"

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "postcode" in errors[0]

    patient = Patient.objects.first()

    assert patient.postcode == "not a postcode"
    assert "postcode" in patient.errors


@pytest.mark.django_db
@patch(
    "project.npda.general_functions.csv.csv_upload.validate_patient_async",
    mock_patient_external_validation_result(postcode=None),
)
def test_error_validating_postcode(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    single_row_valid_df["Postcode of usual address"] = "WC1X 8SH"

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

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
def test_invalid_gp_ods_code(
    test_user, single_row_valid_df, audit_period_for_dataset_year
):
    single_row_valid_df["GP Practice Code"] = "not a GP code"

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
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
    audit_period.start_date = current_audit_year_start_date(
        date_instance=single_row_valid_df["Visit/Appointment Date"][0].date()
    )
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)
    assert len(errors) == 0

    patient = Patient.objects.first()
    assert patient.gp_practice_ods_code == "G85023"


@pytest.mark.django_db
def test_gp_ods_code_trailing_space(
    test_user, dummy_sheet_csv, audit_period_for_dataset_year
):
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
        csv_upload_sync(test_user, df, _audit_period=audit_period_for_dataset_year)

        assert mock_validate_patient_async.call_count == 1
        assert (
            mock_validate_patient_async.mock_calls[0].kwargs["gp_practice_ods_code"]
            == "G85023"
        )


@pytest.mark.django_db
def test_lookup_index_of_multiple_deprivation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    patient = Patient.objects.first()
    assert (
        patient.index_of_multiple_deprivation_quintile
        == INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE
    )


@patch(
    "project.npda.general_functions.csv.csv_upload.validate_patient_async",
    AsyncMock(
        return_value=dataclasses.replace(
            MOCK_PATIENT_EXTERNAL_VALIDATION_RESULT,
            index_of_multiple_deprivation_quintile=None,
        )
    ),
)
@pytest.mark.django_db
def test_error_looking_up_index_of_multiple_deprivation(
    test_user, single_row_valid_df, audit_period_for_dataset_year
):
    csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    patient = Patient.objects.first()
    assert patient.index_of_multiple_deprivation_quintile is None


@pytest.mark.django_db
def test_save_location_from_postcode(
    test_user, single_row_valid_df, audit_period_for_dataset_year
):
    csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

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
def test_missing_location_from_postcode(
    test_user, single_row_valid_df, audit_period_for_dataset_year
):
    csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

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
    single_row_valid_df,
    tmp_path,
    client,
    test_rcpch_user,
    dataset_year,
    audit_period_for_dataset_year,
):
    # Add additional columns
    single_row_valid_df["extra_one"] = "ada"
    single_row_valid_df["extra_two"] = "lovelace"

    Submission.objects.all().delete()  # Clear any previous submissions

    # write back into temp
    tmp_csv_path = tmp_path / "dummy_sheet_test.csv"
    single_row_valid_df.to_csv(tmp_csv_path, index=False)

    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)

    url = reverse(
        "pdu-upload-csv",
        kwargs={
            "pz_code": ALDER_HEY_PZ_CODE,
            "audit_period": audit_period_for_dataset_year.slug,
        },
    )

    # Feed file to view
    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(url, {"csv_upload": csv_file}, format="multipart")

    assert response.status_code == 200

    assert Submission.objects.count() == 0, (
        "No submission should be created if there are column errors"
    )


@pytest.mark.django_db
def test_duplicate_columns_causes_error(
    single_row_valid_df,
    client,
    test_rcpch_user,
    tmp_path,
    audit_period_for_dataset_year,
):
    single_row_valid_df["NHS Number_2"] = single_row_valid_df["NHS Number"]
    single_row_valid_df["NHS Number_3"] = single_row_valid_df["NHS Number"]
    single_row_valid_df["Date of Birth_2"] = single_row_valid_df["Date of Birth"]

    tmp_csv_path = tmp_path / "dummy_sheet_test.csv"
    single_row_valid_df.to_csv(tmp_csv_path, index=False)

    Submission.objects.all().delete()  # Clear any previous submissions

    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)

    # Feed file and re-duplicate columns to the CSV
    with open(tmp_csv_path) as csv_file:
        csv = csv_file.read()
        csv = csv.replace("NHS Number_2", "NHS Number")
        csv = csv.replace("NHS Number_3", "NHS Number")
        csv = csv.replace("Date of Birth_2", "Date of Birth")
        # Reset the file pointer to the beginning of the file
        csv_file.seek(0)

        url = reverse(
            "pdu-upload-csv",
            kwargs={
                "pz_code": ALDER_HEY_PZ_CODE,
                "audit_period": audit_period_for_dataset_year.slug,
            },
        )

        response = client.post(url, {"csv_upload": csv_file}, format="multipart")

    assert response.status_code == 200
    assert "Warning: Column errors detected!" in response.content.decode("utf-8")

    assert Submission.objects.count() == 0, (
        "No submission should be created if there are column errors"
    )


@pytest.mark.django_db
def test_missing_columns_causes_error(
    test_rcpch_user,
    single_row_valid_df,
    client,
    tmp_path,
    audit_period_for_dataset_year,
):
    df = single_row_valid_df.drop(
        columns=["Urinary Albumin Level (ACR)", "Total Cholesterol Level (mmol/l)"]
    )

    Submission.objects.all().delete()  # Clear any previous submissions

    tmp_csv_path = tmp_path / "dummy_sheet_test.csv"
    df.to_csv(tmp_csv_path, index=False)

    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)

    url = reverse(
        "pdu-upload-csv",
        kwargs={
            "pz_code": ALDER_HEY_PZ_CODE,
            "audit_period": audit_period_for_dataset_year.slug,
        },
    )

    # Feed file into view
    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(url, {"csv_upload": csv_file}, format="multipart")

    assert response.status_code == 200
    assert "Warning: Column errors detected!" in response.content.decode("utf-8")

    assert Submission.objects.count() == 0, (
        "No submission should be created if there are column errors"
    )


@pytest.mark.django_db
def test_case_insensitive_column_headers(
    test_user, dummy_sheet_csv, audit_period_for_dataset_year, dataset_year
):
    csv = dummy_sheet_csv

    lines = csv.split("\n")
    lines[0] = lines[0].lower()
    csv = "\n".join(lines)

    parsed_csv = read_csv_from_str(csv, dataset_year=dataset_year)
    assert len(parsed_csv.additional_columns) == 0

    errors = csv_upload_sync(
        test_user, parsed_csv.df, _audit_period=audit_period_for_dataset_year
    )
    if dataset_year >= 2026:
        assert len(errors) == 3
    else:
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
def test_invalid_nhs_number_column_name(
    single_row_valid_df, client, test_rcpch_user, tmp_path
):
    single_row_valid_df = single_row_valid_df.rename(
        columns={"NHS Number": "NHS Nunberxns"}
    )

    tmp_csv_path = tmp_path / "dummy_sheet_test.csv"
    single_row_valid_df.to_csv(tmp_csv_path, index=False)

    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)

    url = reverse(
        "pdu-upload-csv",
        kwargs={"pz_code": ALDER_HEY_PZ_CODE, "audit_period": "2025-2026"},
    )

    # Feed file into view
    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(url, {"csv_upload": csv_file}, format="multipart")

    assert response.status_code == 302
    assert response.url == url

    error_messages = list(get_messages(response.wsgi_request))

    assert len(error_messages) == 1
    assert error_messages[0].tags == "error"
    assert (
        error_messages[0].message
        == "Invalid CSV format: No unique identifier column is present. Please ensure one of Unique Reference Number or NHS Number is present in the file."
    )


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/741
@pytest.mark.django_db
def test_invalid_date_of_birth_column_name_with_mixed_case_column_headers(
    test_user, dummy_sheet_csv, dataset_year
):
    csv = dummy_sheet_csv.replace("Date of Birth", "DOB").replace(
        "HbA1c result format", "HBA1C Result Format"
    )
    results = read_csv_from_str(csv, dataset_year=dataset_year)
    print(results)
    assert results.missing_columns == []
    assert results.additional_columns == []


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/741
@pytest.mark.django_db
def test_old_template_headers(
    test_user, dummy_sheet_csv_old_headers, audit_period_for_dataset_year, dataset_year
):
    if dataset_year >= 2026:
        pytest.skip("Old headers are not supported in dataset year 2026 and beyond")
    csv = dummy_sheet_csv_old_headers
    results = read_csv_from_str(csv, dataset_year=dataset_year)

    assert results.missing_columns == []
    assert results.additional_columns == []

    csv_upload_sync(test_user, results.df, _audit_period=audit_period_for_dataset_year)

    assert Patient.objects.count() > 0
    assert Visit.objects.count() > 0


@pytest.mark.django_db
def test_csv_year_mismatch_raises_error(
    test_user, dummy_sheet_csv, audit_period_for_dataset_year, dataset_year
):
    # dummy_sheet_csv returns the CSV matching dataset_year.
    # Parsing it with the *opposite* year must raise a ValueError because
    # csv_parse detects the header/year mismatch.
    opposite_year = 2021 if dataset_year == 2026 else 2026
    with pytest.raises(ValueError, match="Please check your file and upload again"):
        read_csv_from_str(dummy_sheet_csv, dataset_year=opposite_year)


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
def test_empty_csv_raises_error(
    single_row_valid_df,
    tmp_path,
    client,
    test_rcpch_user,
    dataset_year,
    audit_period_for_dataset_year,
):
    """A CSV with headers but no data rows should return a user-facing error, not a 500."""
    headers_only = single_row_valid_df.iloc[:0].to_csv(index=False)

    Submission.objects.all().delete()

    tmp_csv_path = tmp_path / "empty_sheet.csv"
    tmp_csv_path.write_text(headers_only)

    client = login_and_verify_user(client, test_rcpch_user)

    url = reverse(
        "pdu-upload-csv",
        kwargs={
            "pz_code": ALDER_HEY_PZ_CODE,
            "audit_period": audit_period_for_dataset_year.slug,
        },
    )

    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(url, {"csv_upload": csv_file}, format="multipart")

    assert response.status_code == 302
    assert response.url == url

    error_messages = list(get_messages(response.wsgi_request))
    assert len(error_messages) == 1
    assert error_messages[0].tags == "error"
    assert "no data rows" in error_messages[0].message

    assert Submission.objects.count() == 0


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
    df = one_patient_two_visits.rename(
        columns={"NHS Number": "Unique Reference Number"}
    )
    csv = df.to_csv(index=False, date_format="%d/%m/%Y")

    parsed_csv = read_csv_from_str(csv)
    assert parsed_csv.identifier_column == "Unique Reference Number"


@pytest.mark.django_db
def test_missing_identifier_columns(
    test_rcpch_user, one_patient_two_visits, client, tmp_path
):
    df = one_patient_two_visits.drop(["NHS Number"], axis=1)

    tmp_csv_path = tmp_path / "dummy_sheet_test.csv"
    df.to_csv(tmp_csv_path, index=False)

    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)

    url = reverse(
        "pdu-upload-csv",
        kwargs={"pz_code": ALDER_HEY_PZ_CODE, "audit_period": "2025-2026"},
    )

    # Feed file into view
    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(url, {"csv_upload": csv_file}, format="multipart")

    assert response.status_code == 302
    assert response.url == url

    error_messages = list(get_messages(response.wsgi_request))
    assert len(error_messages) == 1
    assert error_messages[0].tags == "error"

    assert (
        error_messages[0].message
        == "Invalid CSV format: No unique identifier column is present. Please ensure one of Unique Reference Number or NHS Number is present in the file."
    )


@pytest.mark.django_db
def test_both_identifier_columns_causes_an_error(
    test_rcpch_user, one_patient_two_visits, client, tmp_path
):
    df = one_patient_two_visits
    df = df.assign(**{"Unique Reference Number": np.arange(df.shape[0])})

    tmp_csv_path = tmp_path / "dummy_sheet_test.csv"
    df.to_csv(tmp_csv_path, index=False)

    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)

    url = reverse(
        "pdu-upload-csv",
        kwargs={"pz_code": ALDER_HEY_PZ_CODE, "audit_period": "2025-2026"},
    )

    # Feed file into view
    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(url, {"csv_upload": csv_file}, format="multipart")

    assert response.status_code == 302
    assert response.url == url

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
def test_urine_albumin_value_is_rounded_to_one_decimal(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    acr = get_field_heading("albumin_creatinine_ratio", dataset_year=dataset_year)
    single_row_valid_df[acr] = 0.73

    csv = single_row_valid_df.to_csv(index=False, date_format="%d/%m/%Y")

    # --- Debugging: inspect raw CSV header and parsed/cleaned columns ---
    # Print raw header and codepoints to detect unexpected characters (e.g. daggers)
    header_line = csv.splitlines()[0]
    print("raw header repr:", repr(header_line))
    print("header codepoints:", [hex(ord(ch)) for ch in header_line])

    # Inspect parse results before upload
    parsed = read_csv_from_str(csv, dataset_year=dataset_year)
    print("parsed.columns:", parsed.df.columns.tolist())
    print("parsed.template_columns sample:", parsed.template_columns[:10])
    print("parsed.missing_columns:", parsed.missing_columns)
    print("parsed.additional_columns:", parsed.additional_columns)

    # Run csv_clean to normalise and parse dates, then inspect the Hba1c date column
    from project.npda.general_functions.csv.csv_clean import csv_clean

    df = parsed.df
    df = csv_clean(df, dataset_year=dataset_year)

    hba_col = get_field_heading("hba1c_date", dataset_year=dataset_year)
    if hba_col in df.columns:
        print("hba1c_date dtype:", df[hba_col].dtype)
        for i, v in enumerate(df[hba_col].tolist()[:5]):
            print(f"hba1c_date[{i}]:", repr(v), type(v))
    else:
        print(hba_col, "not found in parsed dataframe columns")

    # Proceed with the normal upload assertions
    csv_upload_sync(test_user, df, _audit_period=audit_period_for_dataset_year)

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

    assert Patient.objects.count() == 0, (
        "There should be no patients in the database before the test"
    )

    df = read_csv_from_str(csv).df
    errors = csv_upload_sync(test_user, df)

    assert len(errors) == 1

    assert Patient.objects.count() == 0, (
        "There should be no patients in the database after the test"
    )


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
def test_bad_date_format_on_optional_column(dummy_sheet_csv, dataset_year):
    # Use the year-correct CSV to avoid the 2021/2026 header mismatch check.
    # Both dummy CSVs have at least 2 rows with the same NHS number first.
    lines = dummy_sheet_csv.splitlines()
    csv_two_rows = "\n".join([lines[0]] + lines[1:3])

    column = get_field_heading(
        "carbohydrate_counting_level_three_education_date", dataset_year
    )

    df = read_csv_from_str(csv_two_rows, dataset_year=dataset_year).df
    df[column] = df[column].astype(str)
    df[column] = "beep"

    csv = df.to_csv(index=False, date_format="%d/%m/%Y")

    df = read_csv_from_str(csv, dataset_year=dataset_year).df
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
def test_hba1c_value_ifcc_less_than_20(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    if dataset_year >= 2026:
        pytest.skip("Test applies only to 2021 headings")

    hba1c_value = get_field_heading("hba1c", dataset_year)
    hba1c_date = get_field_heading("hba1c_date", dataset_year)
    visit_date = get_field_heading("visit_date", dataset_year)
    if dataset_year < 2026:
        hba1c_format = get_field_heading("hba1c_format", dataset_year)
        single_row_valid_df[hba1c_format] = 1  # IFCC (mmol/mol)
    single_row_valid_df[hba1c_value] = 18.0  # IFCC (mmol/mol)
    single_row_valid_df[hba1c_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )
    single_row_valid_df[visit_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "hba1c" in errors[0]

    visit = Visit.objects.first()

    # This would be rejected in the questionnaire but saved if it was a csv upload
    assert visit.hba1c == 18
    assert "hba1c" in visit.errors


@pytest.mark.django_db
def test_hba1c_value_ifcc_more_than_195(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    hba1c_value = get_field_heading("hba1c", dataset_year)
    hba1c_date = get_field_heading("hba1c_date", dataset_year)
    visit_date = get_field_heading("visit_date", dataset_year)
    if dataset_year < 2026:
        hba1c_format = get_field_heading("hba1c_format", dataset_year)
        single_row_valid_df[hba1c_format] = 1  # IFCC (mmol/mol)
        single_row_valid_df.loc[0, hba1c_format] = 1  # IFCC (mmol/mol)
    single_row_valid_df.loc[0, hba1c_value] = 196
    single_row_valid_df.loc[0, hba1c_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )
    single_row_valid_df.loc[0, visit_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "hba1c" in errors[0]

    visit = Visit.objects.first()

    # This would be rejected in the questionnaire but saved if it was a csv upload
    assert visit.hba1c == 196
    assert "hba1c" in visit.errors


@pytest.mark.django_db
def test_hba1c_value_dcct_more_than_20(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    if dataset_year >= 2026:
        pytest.skip("Test applies only to 2021 headings")
    hba1c_value = get_field_heading("hba1c", dataset_year)
    hba1c_date = get_field_heading("hba1c_date", dataset_year)
    visit_date = get_field_heading("visit_date", dataset_year)
    hba1c_format = get_field_heading("hba1c_format", dataset_year)
    single_row_valid_df[hba1c_format] = 2  # DCCT (%)
    single_row_valid_df.loc[0, hba1c_value] = 21
    single_row_valid_df.loc[0, hba1c_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )
    single_row_valid_df.loc[0, visit_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "hba1c" in errors[0]

    visit = Visit.objects.first()

    # This would be rejected in the questionnaire but saved if it was a csv upload
    assert visit.hba1c == 21
    assert "hba1c" in visit.errors


def test_hba1c_value_dcct_inferred_in_2026_dataset(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    if dataset_year < 2026:
        pytest.skip("Test applies only to 2026+ headings")

    hba1c_value = get_field_heading("hba1c", dataset_year)
    hba1c_date = get_field_heading("hba1c_date", dataset_year)
    visit_date = get_field_heading("visit_date", dataset_year)

    single_row_valid_df.loc[0, hba1c_value] = 6
    single_row_valid_df.loc[0, hba1c_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )
    single_row_valid_df.loc[0, visit_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "hba1c" not in errors[0]

    visit = Visit.objects.first()

    assert visit.hba1c == 6
    assert visit.hba1c_format == 2  # DCCT (%)

    assert visit.errors is None


def test_hba1c_value_ifcc_inferred_in_2026_dataset(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    if dataset_year < 2026:
        pytest.skip("Test applies only to 2026+ headings")

    hba1c_value = get_field_heading("hba1c", dataset_year)
    hba1c_date = get_field_heading("hba1c_date", dataset_year)
    visit_date = get_field_heading("visit_date", dataset_year)

    single_row_valid_df.loc[0, hba1c_value] = 64
    single_row_valid_df.loc[0, hba1c_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )
    single_row_valid_df.loc[0, visit_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "hba1c" not in errors[0]

    visit = Visit.objects.first()

    assert visit.hba1c == 64
    assert visit.hba1c_format == 1  # IFCC (mmol/mol)

    assert visit.errors is None


@pytest.mark.django_db
def test_hba1c_value_dcct_less_than_3(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    if dataset_year >= 2026:
        pytest.skip("Test applies only to 2021 headings")
    hba1c_value = get_field_heading("hba1c", dataset_year)
    hba1c_date = get_field_heading("hba1c_date", dataset_year)
    visit_date = get_field_heading("visit_date", dataset_year)
    hba1c_format = get_field_heading("hba1c_format", dataset_year)
    single_row_valid_df[hba1c_format] = 2  # DCCT (%)
    single_row_valid_df.loc[0, hba1c_value] = 2
    single_row_valid_df.loc[0, hba1c_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )
    single_row_valid_df.loc[0, visit_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )
    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "hba1c" in errors[0]

    visit = Visit.objects.first()

    # This would be rejected in the questionnaire but saved if it was a csv upload
    assert visit.hba1c == 2
    assert "hba1c" in visit.errors


@pytest.mark.django_db
def test_hba1c_missing(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    hba1c_value = get_field_heading("hba1c", dataset_year)
    hba1c_date = get_field_heading("hba1c_date", dataset_year)
    if dataset_year < 2026:
        hba1c_format = get_field_heading("hba1c_format", dataset_year)
        single_row_valid_df[hba1c_format] = 2  # DCCT (%)
    single_row_valid_df.loc[0, hba1c_value] = None
    single_row_valid_df.loc[0, hba1c_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "hba1c" in errors[0]

    visit = Visit.objects.first()

    # This would be rejected in the questionnaire but saved if it was a csv upload
    assert visit.hba1c is None
    assert "hba1c" in visit.errors


"""
Diabetes treatment tests
"""


@pytest.mark.django_db
def test_treatment_closed_loop_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that both pump and closed loop system are accepted
    """
    if dataset_year >= 2026:
        pytest.skip("Test applies only to 2021 headings")
    treatment = get_field_heading("treatment", dataset_year)
    closed_loop_system = get_field_heading("closed_loop_system", dataset_year)
    single_row_valid_df.loc[0, treatment] = 3
    single_row_valid_df.loc[
        0,
        closed_loop_system,
    ] = 1

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert len(errors) == 0

    visit = Visit.objects.first()
    assert visit.treatment == 3
    assert visit.closed_loop_system == 1


@pytest.mark.django_db
def test_treatment_missing_closed_loop_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that both closed loop system selected but treatment is None fail validation
    """
    if dataset_year >= 2026:
        pytest.skip("Test applies only to 2021 headings")
    treatment = get_field_heading("treatment", dataset_year)
    closed_loop_system = get_field_heading("closed_loop_system", dataset_year)
    single_row_valid_df.loc[0, treatment] = None
    single_row_valid_df.loc[
        0,
        closed_loop_system,
    ] = 1

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "treatment" in errors[0]

    visit = Visit.objects.first()
    assert visit.treatment is None
    assert visit.closed_loop_system == 1


@pytest.mark.django_db
def test_treatment_mdi_but_closed_loop_selected_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that MDI selected but closed loop system is also selected
    """
    if dataset_year >= 2026:
        pytest.skip("Test applies only to 2021 headings")
    treatment = get_field_heading("treatment", dataset_year)
    closed_loop_system = get_field_heading("closed_loop_system", dataset_year)
    single_row_valid_df.loc[0, treatment] = 2  # MDI
    single_row_valid_df.loc[
        0,
        closed_loop_system,
    ] = 2  # Closed loop system (licensed)

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "closed_loop_system" in errors[0]

    visit = Visit.objects.first()
    assert visit.treatment == 2
    assert visit.closed_loop_system == 2
    assert "closed_loop_system" in visit.errors


"""
Blood pressure tests
"""


@pytest.mark.django_db
def test_blood_pressure_values_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that both systolic and diastolic blood pressure values are accepted
    """
    systolic_blood_pressure = get_field_heading("systolic_blood_pressure", dataset_year)
    diastolic_blood_pressure = get_field_heading(
        "diastolic_blood_pressure", dataset_year
    )
    blood_pressure_observation_date = get_field_heading(
        "blood_pressure_observation_date", dataset_year
    )
    single_row_valid_df.loc[0, systolic_blood_pressure] = 120
    single_row_valid_df.loc[0, diastolic_blood_pressure] = 80
    single_row_valid_df.loc[0, blood_pressure_observation_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert len(errors) == 0

    visit = Visit.objects.first()
    assert visit.systolic_blood_pressure == 120
    assert visit.diastolic_blood_pressure == 80


@pytest.mark.django_db
def test_blood_pressure_missing_values_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that one missing systolic blood pressure value fails validation
    """
    systolic_blood_pressure = get_field_heading("systolic_blood_pressure", dataset_year)
    diastolic_blood_pressure = get_field_heading(
        "diastolic_blood_pressure", dataset_year
    )
    blood_pressure_observation_date = get_field_heading(
        "blood_pressure_observation_date", dataset_year
    )
    single_row_valid_df.loc[0, systolic_blood_pressure] = None
    single_row_valid_df.loc[0, diastolic_blood_pressure] = 80
    single_row_valid_df.loc[0, blood_pressure_observation_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "systolic_blood_pressure" in errors[0], (
        "Systolic Blood Pressure is None but passes validation."
    )

    visit = Visit.objects.first()
    assert visit.systolic_blood_pressure is None
    assert visit.diastolic_blood_pressure == 80


@pytest.mark.django_db
def test_blood_pressure_missing_date_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that one missing blood pressure observation date fails validation
    """
    systolic_blood_pressure = get_field_heading("systolic_blood_pressure", dataset_year)
    diastolic_blood_pressure = get_field_heading(
        "diastolic_blood_pressure", dataset_year
    )
    blood_pressure_observation_date = get_field_heading(
        "blood_pressure_observation_date", dataset_year
    )
    single_row_valid_df.loc[0, systolic_blood_pressure] = 120
    single_row_valid_df.loc[0, diastolic_blood_pressure] = 80
    single_row_valid_df.loc[0, blood_pressure_observation_date] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "blood_pressure_observation_date" in errors[0], (
        "Blood Pressure observation date is None but passes validation."
    )

    visit = Visit.objects.first()
    assert visit.systolic_blood_pressure == 120, (
        f"Systolic blood pressure should be 120 but was {visit.systolic_blood_pressure}"
    )
    assert visit.diastolic_blood_pressure == 80, (
        f"Diastolic blood pressure should be 80 but was {visit.diastolic_blood_pressure}"
    )
    assert visit.blood_pressure_observation_date is None, (
        f"Blood pressure observation date should be empty but is {visit.blood_pressure_observation_date}"
    )


@pytest.mark.django_db
def test_systolic_blood_pressure_over_240_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that systolic blood pressure value > 240 fails validation
    """
    systolic_blood_pressure = get_field_heading("systolic_blood_pressure", dataset_year)
    diastolic_blood_pressure = get_field_heading(
        "diastolic_blood_pressure", dataset_year
    )
    blood_pressure_observation_date = get_field_heading(
        "blood_pressure_observation_date", dataset_year
    )
    single_row_valid_df.loc[0, systolic_blood_pressure] = 250
    single_row_valid_df.loc[0, diastolic_blood_pressure] = 80
    single_row_valid_df.loc[0, blood_pressure_observation_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "systolic_blood_pressure" in errors[0], (
        "Systolic Blood Pressure is >240 (so really dangerously high!) but passes validation."
    )

    visit = Visit.objects.first()
    assert visit.systolic_blood_pressure == 250, (
        f"Systolic blood pressure should be 250 (and really the child should be in hospital) but was {visit.systolic_blood_pressure}"
    )
    assert visit.diastolic_blood_pressure == 80, (
        f"Diastolic blood pressure should be 80 but was {visit.diastolic_blood_pressure}"
    )
    assert (
        visit.blood_pressure_observation_date
        == audit_period_for_dataset_year.start_date + relativedelta(months=1)
    ), (
        f"Blood pressure observation date should be {audit_period_for_dataset_year.start_date + relativedelta(months=1)} but is {visit.blood_pressure_observation_date}"
    )


@pytest.mark.django_db
def test_systolic_blood_pressure_below_50_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that systolic blood pressure value < 80 fails validation
    """
    systolic_blood_pressure = get_field_heading("systolic_blood_pressure", dataset_year)
    diastolic_blood_pressure = get_field_heading(
        "diastolic_blood_pressure", dataset_year
    )
    blood_pressure_observation_date = get_field_heading(
        "blood_pressure_observation_date", dataset_year
    )
    single_row_valid_df.loc[0, systolic_blood_pressure] = 49
    single_row_valid_df.loc[0, diastolic_blood_pressure] = 40
    single_row_valid_df.loc[0, blood_pressure_observation_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "systolic_blood_pressure" in errors[0], (
        "Systolic Blood Pressure is < 50 (so really dangerously low!) but passes validation."
    )

    visit = Visit.objects.first()
    assert visit.systolic_blood_pressure == 49, (
        f"Systolic blood pressure should be 49 (and really the child should be in hospital) but was {visit.systolic_blood_pressure}"
    )
    assert visit.diastolic_blood_pressure == 40, (
        f"Diastolic blood pressure should be 40 but was {visit.diastolic_blood_pressure}"
    )
    assert (
        visit.blood_pressure_observation_date
        == audit_period_for_dataset_year.start_date + relativedelta(months=1)
    ), (
        f"Blood pressure observation date should be {audit_period_for_dataset_year.start_date + relativedelta(months=1)} but is {visit.blood_pressure_observation_date}"
    )


@pytest.mark.django_db
def test_diastolic_blood_pressure_over_120_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that diastolic blood pressure value > 120 fails validation
    """
    diastolic_blood_pressure = get_field_heading(
        "diastolic_blood_pressure", dataset_year
    )
    systolic_blood_pressure = get_field_heading("systolic_blood_pressure", dataset_year)
    blood_pressure_observation_date = get_field_heading(
        "blood_pressure_observation_date", dataset_year
    )
    single_row_valid_df.loc[0, systolic_blood_pressure] = 120
    single_row_valid_df.loc[0, diastolic_blood_pressure] = (
        125  # Note that pressure has a lower case 'p'
    )
    single_row_valid_df.loc[0, blood_pressure_observation_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "diastolic_blood_pressure" in errors[0], (
        "Diastolic Blood Pressure is >120 (so really dangerously high!) but passes validation."
    )

    visit = Visit.objects.first()
    assert visit.systolic_blood_pressure == 120, (
        f"Systolic blood pressure should be 120 but was {visit.systolic_blood_pressure}"
    )
    assert visit.diastolic_blood_pressure == 125, (
        f"Diastolic blood pressure should be 125 (and really the child should be in hospital) but was {visit.diastolic_blood_pressure}"
    )
    assert (
        visit.blood_pressure_observation_date
        == audit_period_for_dataset_year.start_date + relativedelta(months=1)
    ), (
        f"Blood pressure observation date should be {audit_period_for_dataset_year.start_date + relativedelta(months=1)} but is {visit.blood_pressure_observation_date}"
    )


@pytest.mark.django_db
def test_diastolic_blood_pressure_below_20_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that diastolic blood pressure value < 20 fails validation
    """
    diastolic_blood_pressure = get_field_heading(
        "diastolic_blood_pressure", dataset_year
    )
    systolic_blood_pressure = get_field_heading("systolic_blood_pressure", dataset_year)
    blood_pressure_observation_date = get_field_heading(
        "blood_pressure_observation_date", dataset_year
    )
    single_row_valid_df.loc[0, systolic_blood_pressure] = 120
    single_row_valid_df.loc[0, diastolic_blood_pressure] = (
        15  # Note that pressure has a lower case 'p'
    )
    single_row_valid_df.loc[0, blood_pressure_observation_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )
    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "diastolic_blood_pressure" in errors[0], (
        "Diastolic Blood Pressure is < 20 (so really dangerously low!) but passes validation."
    )

    visit = Visit.objects.first()
    assert visit.systolic_blood_pressure == 120, (
        f"Systolic blood pressure should be 120 but was {visit.systolic_blood_pressure}"
    )
    assert visit.diastolic_blood_pressure == 15, (
        f"Diastolic blood pressure should be 15 (and really the child should be in hospital) but was {visit.diastolic_blood_pressure}"
    )
    assert (
        visit.blood_pressure_observation_date
        == audit_period_for_dataset_year.start_date + relativedelta(months=1)
    ), (
        f"Blood pressure observation date should be {audit_period_for_dataset_year.start_date + relativedelta(months=1)} but is {visit.blood_pressure_observation_date}"
    )


"""
Retinal screening tests
"""


@pytest.mark.django_db
def test_decs_value_form_passes_validation(
    test_user, single_row_valid_df, dataset_year, audit_period_for_dataset_year
):
    """
    Test that DECS value is accepted
    """
    retinal_screening_date = get_field_heading(
        "retinal_screening_observation_date", dataset_year
    )
    retinal_screening_result = get_field_heading(
        "retinal_screening_result", dataset_year
    )
    single_row_valid_df.loc[0, retinal_screening_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )
    single_row_valid_df.loc[0, retinal_screening_result] = 1  # Normal

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert len(errors) == 0, (
        f"Retinal screening date and result should pass validation, but failed with errors: {errors}"
    )

    visit = Visit.objects.first()
    assert (
        visit.retinal_screening_observation_date
        == audit_period_for_dataset_year.start_date + relativedelta(months=1)
    ), (
        f"Saved Retinal screening date should be {audit_period_for_dataset_year.start_date + relativedelta(months=1)}   , but was {visit.retinal_screening_observation_date}"
    )
    assert visit.retinal_screening_result == 1, (
        f"Saved Retinal screening result should be 1 (Normal), but was {visit.retinal_screening_result}"
    )


@pytest.mark.django_db
def test_decs_value_none_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that a missing DECS value is invalid
    """
    retinal_screening_date = get_field_heading(
        "retinal_screening_observation_date", dataset_year
    )
    retinal_screening_result = get_field_heading(
        "retinal_screening_result", dataset_year
    )
    single_row_valid_df.loc[0, retinal_screening_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )
    single_row_valid_df.loc[0, retinal_screening_result] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "retinal_screening_result" in errors[0], (
        "Retinal screening result should fail validation due to missing result, but passed."
    )

    visit = Visit.objects.first()
    assert (
        visit.retinal_screening_observation_date
        == audit_period_for_dataset_year.start_date + relativedelta(months=1)
    ), (
        f"Saved Retinal screening date should be {audit_period_for_dataset_year.start_date + relativedelta(months=1)}, but was {visit.retinal_screening_observation_date}"
    )
    assert visit.retinal_screening_result is None, (
        f"Saved Retinal screening result should be None, but was {visit.retinal_screening_result}"
    )


@pytest.mark.django_db
def test_decs_date_none_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that a missing DECS date is invalid
    """
    retinal_screening_date = get_field_heading(
        "retinal_screening_observation_date", dataset_year
    )
    retinal_screening_result = get_field_heading(
        "retinal_screening_result", dataset_year
    )
    single_row_valid_df.loc[0, retinal_screening_date] = None
    single_row_valid_df.loc[0, retinal_screening_result] = 1  # Normal

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "retinal_screening_observation_date" in errors[0], (
        "Retinal screening date should fail validation due to missing date, but passed."
    )

    visit = Visit.objects.first()
    assert visit.retinal_screening_observation_date is None, (
        f"Saved Retinal screening date should be None, but was {visit.retinal_screening_observation_date}"
    )
    assert visit.retinal_screening_result == 1, (
        f"Saved Retinal screening result should be 1 (Normal), but was {visit.retinal_screening_result}"
    )


"""
Urine albumin tests
"""


@pytest.mark.django_db
def test_urine_albumin_value_form_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that urine albumin value is accepted
    """
    acr = get_field_heading("albumin_creatinine_ratio", dataset_year)
    albuminuria_stage = get_field_heading("albuminuria_stage", dataset_year)
    acr_date = get_field_heading("albumin_creatinine_ratio_date", dataset_year)
    single_row_valid_df.loc[0, acr] = 30
    single_row_valid_df.loc[0, albuminuria_stage] = 1  # Normal
    single_row_valid_df.loc[0, acr_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert visit.albumin_creatinine_ratio == 30, (
        f"Saved urine albumin should be 30, but was {visit.albumin_creatinine_ratio}"
    )
    assert visit.albuminuria_stage == 1, (
        f"Saved urine albumin stage should be 1 (Normal), but was {visit.albuminuria_stage}"
    )
    assert (
        visit.albumin_creatinine_ratio_date
        == audit_period_for_dataset_year.start_date + relativedelta(months=1)
    ), (
        f"Saved urine albumin observation date should be {audit_period_for_dataset_year.start_date + relativedelta(months=1)}, but was {visit.albumin_creatinine_ratio_date}"
    )


@pytest.mark.django_db
def test_urine_albumin_value_below_range_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that urine albumin value is rejected if below range
    """
    acr = get_field_heading("albumin_creatinine_ratio", dataset_year)
    albuminuria_stage = get_field_heading("albuminuria_stage", dataset_year)
    acr_date = get_field_heading("albumin_creatinine_ratio_date", dataset_year)
    single_row_valid_df.loc[0, acr] = -10
    single_row_valid_df.loc[0, albuminuria_stage] = 1  # Normal
    single_row_valid_df.loc[0, acr_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "albumin_creatinine_ratio" in errors[0], (
        "Urine albumin creatinine ratio should fail validation as < 3, but passed."
    )

    visit = Visit.objects.first()

    assert visit.albumin_creatinine_ratio == Decimal("-10"), (
        f"Saved urine albumin should be -10, but was {visit.albumin_creatinine_ratio}"
    )
    assert visit.albuminuria_stage == 1, (
        f"Saved urine albumin stage should be 1 (Normal), but was {visit.albuminuria_stage}"
    )
    assert (
        visit.albumin_creatinine_ratio_date
        == audit_period_for_dataset_year.start_date + relativedelta(months=1)
    ), (
        f"Saved urine albumin observation date should be {audit_period_for_dataset_year.start_date + relativedelta(months=1)}, but was {visit.albumin_creatinine_ratio_date}"
    )


@pytest.mark.django_db
def test_urine_albumin_value_above_range_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that urine albumin value is rejected if above range
    """
    acr = get_field_heading("albumin_creatinine_ratio", dataset_year)
    albuminuria_stage = get_field_heading("albuminuria_stage", dataset_year)
    acr_date = get_field_heading("albumin_creatinine_ratio_date", dataset_year)
    single_row_valid_df.loc[0, acr] = 1000
    single_row_valid_df.loc[0, albuminuria_stage] = 1  # Normal
    single_row_valid_df.loc[0, acr_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "albumin_creatinine_ratio" in errors[0], (
        "Urine albumin creatinine ratio should fail validation as > 50, but passed."
    )

    visit = Visit.objects.first()

    assert visit.albumin_creatinine_ratio == 1000, (
        f"Saved urine albumin should be 1000, but was {visit.albumin_creatinine_ratio}"
    )
    assert visit.albuminuria_stage == 1, (
        f"Saved urine albumin stage should be 1 (Normal), but was {visit.albuminuria_stage}"
    )
    assert (
        visit.albumin_creatinine_ratio_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=1)
    ), (
        f"Saved urine albumin observation date should be {audit_period_for_dataset_year.start_date + relativedelta(days=1)}, but was {visit.albumin_creatinine_ratio_date}"
    )


@pytest.mark.django_db
def test_urine_albumin_value_missing_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that urine albumin value missing  is rejected
    """
    acr = get_field_heading("albumin_creatinine_ratio", dataset_year)
    albuminuria_stage = get_field_heading("albuminuria_stage", dataset_year)
    acr_date = get_field_heading("albumin_creatinine_ratio_date", dataset_year)
    single_row_valid_df.loc[0, acr] = None
    single_row_valid_df.loc[0, albuminuria_stage] = 1  # Normal
    single_row_valid_df.loc[0, acr_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "albumin_creatinine_ratio" in errors[0], (
        "Urine albumin creatinine level should fail validation as None, but passed."
    )

    visit = Visit.objects.first()

    assert visit.albumin_creatinine_ratio is None, (
        f"Saved urine albumin should be None, but was {visit.albumin_creatinine_ratio}"
    )
    assert visit.albuminuria_stage == 1, (
        f"Saved urine albumin stage should be 1 (Normal), but was {visit.albuminuria_stage}"
    )
    assert (
        visit.albumin_creatinine_ratio_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=1)
    ), (
        f"Saved urine albumin observation date should be {audit_period_for_dataset_year.start_date + relativedelta(days=1)}, but was {visit.albumin_creatinine_ratio_date}"
    )


@pytest.mark.django_db
def test_urine_albumin_stage_missing_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that urine albumin value missing  is rejected
    """
    acr = get_field_heading("albumin_creatinine_ratio", dataset_year)
    albuminuria_stage = get_field_heading("albuminuria_stage", dataset_year)
    acr_date = get_field_heading("albumin_creatinine_ratio_date", dataset_year)
    single_row_valid_df.loc[0, acr] = 10
    single_row_valid_df.loc[0, albuminuria_stage] = None
    single_row_valid_df.loc[0, acr_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "albuminuria_stage" in errors[0], (
        "Urine albumin creatinine stage should fail validation as None, but passed."
    )

    visit = Visit.objects.first()

    assert visit.albumin_creatinine_ratio == 10, (
        f"Saved urine albumin should be 10, but was {visit.albumin_creatinine_ratio}"
    )
    assert visit.albuminuria_stage is None, (
        f"Saved urine albumin stage should be None, but was {visit.albuminuria_stage}"
    )
    assert (
        visit.albumin_creatinine_ratio_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=1)
    ), (
        f"Saved urine albumin observation date should be {audit_period_for_dataset_year.start_date + relativedelta(days=1)}, but was {visit.albumin_creatinine_ratio_date}"
    )


@pytest.mark.django_db
def test_urine_albumin_date_missing_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that urine albumin date missing is rejected
    """
    acr = get_field_heading("albumin_creatinine_ratio", dataset_year)
    albuminuria_stage = get_field_heading("albuminuria_stage", dataset_year)
    acr_date = get_field_heading("albumin_creatinine_ratio_date", dataset_year)
    single_row_valid_df.loc[0, acr] = 10
    single_row_valid_df.loc[0, albuminuria_stage] = 1  # Normal
    single_row_valid_df.loc[0, acr_date] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "albumin_creatinine_ratio_date" in errors[0], (
        "Urine albumin creatinine date should fail validation as None, but passed."
    )

    visit = Visit.objects.first()

    assert visit.albumin_creatinine_ratio == 10, (
        f"Saved urine albumin should be 10, but was {visit.albumin_creatinine_ratio}"
    )
    assert visit.albuminuria_stage == 1, (
        f"Saved urine albumin stage should be 1 (Normal), but was {visit.albuminuria_stage}"
    )
    assert visit.albumin_creatinine_ratio_date is None, (
        f"Saved urine albumin observation date should be None, but was {visit.albumin_creatinine_ratio_date}"
    )


"""
Total cholesterol tests
"""


@pytest.mark.django_db
def test_total_cholesterol_value_form_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that total cholesterol value is accepted
    """
    tcol = get_field_heading("total_cholesterol", dataset_year)
    tcol_date = get_field_heading("total_cholesterol_date", dataset_year)
    single_row_valid_df.loc[0, tcol] = 5
    single_row_valid_df.loc[0, tcol_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert visit.total_cholesterol == 5, (
        f"Saved total cholesterol should be 5, but was {visit.total_cholesterol}"
    )
    assert (
        visit.total_cholesterol_date
        == audit_period_for_dataset_year.start_date + relativedelta(months=1)
    ), (
        f"Saved total cholesterol observation date should be {audit_period_for_dataset_year.start_date + relativedelta(months=1)}, but was {visit.total_cholesterol_date}"
    )


@pytest.mark.django_db
def test_total_cholesterol_value_above_reference_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that total cholesterol value is rejected if impossible
    """
    tcol = get_field_heading("total_cholesterol", dataset_year)
    tcol_date = get_field_heading("total_cholesterol_date", dataset_year)
    single_row_valid_df.loc[0, tcol] = 20
    single_row_valid_df.loc[0, tcol_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "total_cholesterol" in errors[0], (
        "Total cholesterol should fail validation as above reference range, but passed."
    )

    visit = Visit.objects.first()

    assert visit.total_cholesterol == 20, (
        f"Saved total cholesterol should be 1000, but was {visit.total_cholesterol}"
    )
    assert (
        visit.total_cholesterol_date
        == audit_period_for_dataset_year.start_date + relativedelta(months=1)
    ), (
        f"Saved total cholesterol observation date should be {audit_period_for_dataset_year.start_date + relativedelta(months=1)}   , but was {visit.total_cholesterol_date}"
    )


@pytest.mark.django_db
def test_total_cholesterol_value_below_reference_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that total cholesterol value is rejected if impossible
    """
    tcol = get_field_heading("total_cholesterol", dataset_year)
    tcol_date = get_field_heading("total_cholesterol_date", dataset_year)
    single_row_valid_df.loc[0, tcol] = 0.1
    single_row_valid_df.loc[0, tcol_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "total_cholesterol" in errors[0], (
        "Total cholesterol should fail validation as impossible, but passed."
    )

    visit = Visit.objects.first()

    assert visit.total_cholesterol == Decimal("0.1"), (
        f"Saved total cholesterol should be 0, but was {visit.total_cholesterol}"
    )
    assert (
        visit.total_cholesterol_date
        == audit_period_for_dataset_year.start_date + relativedelta(months=1)
    ), (
        f"Saved total cholesterol observation date should be {audit_period_for_dataset_year.start_date + relativedelta(months=1)}, but was {visit.total_cholesterol_date}"
    )


@pytest.mark.django_db
def test_total_cholesterol_value_missing_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that total cholesterol value missing  is rejected
    """
    tcol = get_field_heading("total_cholesterol", dataset_year)
    tcol_date = get_field_heading("total_cholesterol_date", dataset_year)
    single_row_valid_df.loc[0, tcol] = None
    single_row_valid_df.loc[0, tcol_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "total_cholesterol" in errors[0], (
        "Total cholesterol should fail validation as None, but passed."
    )

    visit = Visit.objects.first()

    assert visit.total_cholesterol is None, (
        f"Saved total cholesterol should be None, but was {visit.total_cholesterol}"
    )
    assert (
        visit.total_cholesterol_date
        == audit_period_for_dataset_year.start_date + relativedelta(months=1)
    ), (
        f"Saved total cholesterol observation date should be {audit_period_for_dataset_year.start_date + relativedelta(months=1)}, but was {visit.total_cholesterol_date}"
    )


@pytest.mark.django_db
def test_total_cholesterol_date_missing_form_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that total cholesterol date missing is rejected
    """
    tcol = get_field_heading("total_cholesterol", dataset_year)
    tcol_date = get_field_heading("total_cholesterol_date", dataset_year)
    single_row_valid_df.loc[0, tcol] = 5
    single_row_valid_df.loc[0, tcol_date] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "total_cholesterol_date" in errors[0], (
        "Total cholesterol date should fail validation as None, but passed."
    )

    visit = Visit.objects.first()

    assert visit.total_cholesterol == 5, (
        f"Saved total cholesterol should be 5, but was {visit.total_cholesterol}"
    )
    assert visit.total_cholesterol_date is None, (
        f"Saved total cholesterol observation date should be None, but was {visit.total_cholesterol_date}"
    )


"""
Thyroid treatment tests
"""


@pytest.mark.django_db
def test_thyroid_treatment_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that thyroid treatment is accepted
    """
    thyroid_treatment_status = get_field_heading(
        "thyroid_treatment_status", dataset_year
    )
    thyroid_function_date = get_field_heading("thyroid_function_date", dataset_year)
    single_row_valid_df.loc[
        0,
        thyroid_treatment_status,
    ] = 1  # Normal
    single_row_valid_df.loc[0, thyroid_function_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert visit.thyroid_treatment_status == 1
    assert (
        visit.thyroid_function_date
        == audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )


@pytest.mark.django_db
def test_thyroid_treatment_missing_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that a missing thyroid treatment value is rejected
    """
    thyroid_treatment_status = get_field_heading(
        "thyroid_treatment_status", dataset_year
    )
    thyroid_function_date = get_field_heading("thyroid_function_date", dataset_year)
    single_row_valid_df.loc[
        0,
        thyroid_treatment_status,
    ] = None
    single_row_valid_df.loc[0, thyroid_function_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "thyroid_treatment_status" in errors[0]

    visit = Visit.objects.first()

    assert visit.thyroid_treatment_status is None
    assert (
        visit.thyroid_function_date
        == audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )


@pytest.mark.django_db
def test_thyroid_treatment_date_missing_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that a missing thyroid treatment date is rejected
    """
    thyroid_treatment_status = get_field_heading(
        "thyroid_treatment_status", dataset_year
    )
    thyroid_function_date = get_field_heading("thyroid_function_date", dataset_year)
    single_row_valid_df.loc[
        0,
        thyroid_treatment_status,
    ] = 2
    single_row_valid_df.loc[0, thyroid_function_date] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )
    assert "thyroid_function_date" not in errors[0]

    visit = Visit.objects.first()

    assert visit.thyroid_treatment_status == 2
    assert visit.thyroid_function_date is None


"""
Coeliac screening tests
"""


@pytest.mark.django_db
def test_coeliac_screening_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that coeliac screening is accepted
    """
    coeliac_screen = get_field_heading("coeliac_screen_date", dataset_year)
    gluten_free_diet = get_field_heading("gluten_free_diet", dataset_year)
    single_row_valid_df.loc[0, coeliac_screen] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )
    single_row_valid_df.loc[0, gluten_free_diet] = 1

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert (
        visit.coeliac_screen_date
        == audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )
    assert visit.gluten_free_diet == 1


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/628
@pytest.mark.django_db
def test_coeliac_screening_missing_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    coeliac_screen_date = get_field_heading("coeliac_screen_date", dataset_year)
    gluten_free_diet = get_field_heading("gluten_free_diet", dataset_year)
    single_row_valid_df.loc[0, coeliac_screen_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )
    single_row_valid_df.loc[0, gluten_free_diet] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "gluten_free_diet" not in errors[0]

    visit = Visit.objects.first()

    assert (
        visit.coeliac_screen_date
        == audit_period_for_dataset_year.start_date + relativedelta(months=1)
    )
    assert visit.gluten_free_diet is None


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/628
@pytest.mark.django_db
def test_coeliac_screening_date_missing_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    coeliac_screen_date = get_field_heading("coeliac_screen_date", dataset_year)
    gluten_free_diet = get_field_heading("gluten_free_diet", dataset_year)
    single_row_valid_df.loc[0, coeliac_screen_date] = None
    single_row_valid_df.loc[0, gluten_free_diet] = 1

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "coeliac_screen_date" not in errors[0]

    visit = Visit.objects.first()

    assert visit.coeliac_screen_date is None
    assert visit.gluten_free_diet == 1


"""
Psychological support tests
"""


@pytest.mark.django_db
def test_psychological_support_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that psychological support is accepted
    """
    psychological_screening_assessment_date = get_field_heading(
        "psychological_screening_assessment_date", dataset_year
    )
    psychological_additional_support_status = get_field_heading(
        "psychological_additional_support_status", dataset_year
    )
    single_row_valid_df.loc[0, psychological_screening_assessment_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )
    single_row_valid_df.loc[0, psychological_additional_support_status] = 1

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert (
        visit.psychological_screening_assessment_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )
    assert visit.psychological_additional_support_status == 1


@pytest.mark.django_db
def test_psychological_support_missing_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that a missing psychological support value is rejected
    """
    psychological_screening_assessment_date = get_field_heading(
        "psychological_screening_assessment_date", dataset_year
    )
    psychological_additional_support_status = get_field_heading(
        "psychological_additional_support_status", dataset_year
    )
    single_row_valid_df.loc[0, psychological_screening_assessment_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )
    single_row_valid_df.loc[
        0,
        psychological_additional_support_status,
    ] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "psychological_additional_support_status" in errors[0]

    visit = Visit.objects.first()

    assert (
        visit.psychological_screening_assessment_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )
    assert visit.psychological_additional_support_status is None


@pytest.mark.django_db
def test_psychological_support_date_missing_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that a missing psychological support date is rejected
    """
    psychological_screening_assessment_date = get_field_heading(
        "psychological_screening_assessment_date", dataset_year
    )
    psychological_additional_support_status = get_field_heading(
        "psychological_additional_support_status", dataset_year
    )
    single_row_valid_df.loc[0, psychological_screening_assessment_date] = None
    single_row_valid_df.loc[
        0,
        psychological_additional_support_status,
    ] = 1

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "psychological_screening_assessment_date" in errors[0]

    visit = Visit.objects.first()

    assert visit.psychological_screening_assessment_date is None
    assert visit.psychological_additional_support_status == 1


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/628
@pytest.mark.django_db
def test_psychological_support_date_missing_with_unknown_status_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    psychological_screening_assessment_date = get_field_heading(
        "psychological_screening_assessment_date", dataset_year
    )
    psychological_additional_support_status = get_field_heading(
        "psychological_additional_support_status", dataset_year
    )
    single_row_valid_df.loc[0, psychological_screening_assessment_date] = None
    single_row_valid_df.loc[
        0,
        psychological_additional_support_status,
    ] = 99  # Unknown

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "psychological_screening_assessment_date" not in errors[0]

    visit = Visit.objects.first()

    assert visit.psychological_screening_assessment_date is None
    assert visit.psychological_additional_support_status == 99


"""
Smoking status tests
"""


@pytest.mark.django_db
def test_smoking_status_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that smoking status is accepted
    """
    smoking_cessation_referral_date = get_field_heading(
        "smoking_cessation_referral_date", dataset_year
    )
    single_row_valid_df.loc[
        0,
        smoking_cessation_referral_date,
    ] = audit_period_for_dataset_year.start_date + relativedelta(days=1)
    if dataset_year >= 2026:
        smoking_status = get_field_heading("smoking_vaping_status", dataset_year)
    else:
        smoking_status = get_field_heading("smoking_status", dataset_year)
    single_row_valid_df.loc[0, smoking_status] = 2  # Current smoker

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert (
        visit.smoking_cessation_referral_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )
    if dataset_year and dataset_year >= 2026:
        assert visit.smoking_vaping_status == 2
    else:
        assert visit.smoking_status == 2


@pytest.mark.django_db
def test_smoking_status_non_smoker_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that smoking status is accepted
    """
    if dataset_year >= 2026:
        smoking_status = get_field_heading("smoking_vaping_status", dataset_year)
    else:
        smoking_status = get_field_heading("smoking_status", dataset_year)
    smoking_cessation_referral_date = get_field_heading(
        "smoking_cessation_referral_date", dataset_year
    )
    single_row_valid_df.loc[
        0,
        smoking_cessation_referral_date,
    ] = None
    single_row_valid_df.loc[0, smoking_status] = 1  # Non-smoker

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert visit.smoking_cessation_referral_date is None
    if dataset_year >= 2026:
        assert visit.smoking_vaping_status == 1
    else:
        assert visit.smoking_status == 1


@pytest.mark.django_db
def test_smoking_status_non_smoker_referral_date_provided_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that a non-smoker with a referral date is rejected
    """
    if dataset_year >= 2026:
        smoking_status = get_field_heading("smoking_vaping_status", dataset_year)
    else:
        smoking_status = get_field_heading("smoking_status", dataset_year)
    smoking_cessation_referral_date = get_field_heading(
        "smoking_cessation_referral_date", dataset_year
    )
    single_row_valid_df.loc[
        0,
        smoking_cessation_referral_date,
    ] = audit_period_for_dataset_year.start_date + relativedelta(days=1)
    single_row_valid_df.loc[0, smoking_status] = 1  # Non-smoker

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "smoking_cessation_referral_date" in errors[0]

    visit = Visit.objects.first()

    assert (
        visit.smoking_cessation_referral_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )
    if dataset_year >= 2026:
        assert visit.smoking_vaping_status == 1
    else:
        assert visit.smoking_status == 1


@pytest.mark.django_db
def test_smoking_status_missing_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that a missing smoking status value is rejected
    """
    if dataset_year >= 2026:
        smoking_status = get_field_heading("smoking_vaping_status", dataset_year)
    else:
        smoking_status = get_field_heading("smoking_status", dataset_year)
    smoking_cessation_referral_date = get_field_heading(
        "smoking_cessation_referral_date", dataset_year
    )
    single_row_valid_df.loc[
        0,
        smoking_cessation_referral_date,
    ] = audit_period_for_dataset_year.start_date + relativedelta(days=1)
    single_row_valid_df.loc[0, smoking_status] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "smoking_cessation_referral_date" in errors[0]

    visit = Visit.objects.first()

    assert (
        visit.smoking_cessation_referral_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )
    assert visit.smoking_status is None


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/791
@pytest.mark.django_db
def test_smoking_status_smoker_does_not_require_cessation_referral_date(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that smoking status is accepted
    """
    if dataset_year >= 2026:
        smoking_status = get_field_heading("smoking_vaping_status", dataset_year)
    else:
        smoking_status = get_field_heading("smoking_status", dataset_year)
    smoking_cessation_referral_date = get_field_heading(
        "smoking_cessation_referral_date", dataset_year
    )
    single_row_valid_df.loc[
        0,
        smoking_cessation_referral_date,
    ] = None
    single_row_valid_df.loc[0, smoking_status] = 2  # Current smoker not vaper

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert visit.smoking_cessation_referral_date is None
    if dataset_year >= 2026:
        assert visit.smoking_vaping_status == 2
    else:
        assert visit.smoking_status == 2


"""
Dietitian referral tests
"""


@pytest.mark.django_db
def test_dietician_referral_status_additional_offered_form_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that dietician referral status and date are accepted
    """
    dietician_additional_appointment_offered = get_field_heading(
        "dietician_additional_appointment_offered", dataset_year
    )
    dietician_additional_appointment_date = get_field_heading(
        "dietician_additional_appointment_date", dataset_year
    )
    single_row_valid_df.loc[
        0,
        dietician_additional_appointment_offered,
    ] = 1
    single_row_valid_df.loc[0, dietician_additional_appointment_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert visit.dietician_additional_appointment_offered == 1
    assert (
        visit.dietician_additional_appointment_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )


@pytest.mark.django_db
def test_dietician_no_additional_offered_form_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that dietician referral status and date are accepted
    """

    dietician_additional_appointment_offered = get_field_heading(
        "dietician_additional_appointment_offered", dataset_year
    )
    dietician_additional_appointment_date = get_field_heading(
        "dietician_additional_appointment_date", dataset_year
    )
    single_row_valid_df.loc[
        0,
        dietician_additional_appointment_offered,
    ] = 2
    single_row_valid_df.loc[0, dietician_additional_appointment_date] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert visit.dietician_additional_appointment_offered == 2
    assert visit.dietician_additional_appointment_date is None


@pytest.mark.django_db
def test_dietician_no_additional_offered_date_provided_fail_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that dietician extra appointment not offered but date provided should fail
    """

    dietician_additional_appointment_offered = get_field_heading(
        "dietician_additional_appointment_offered", dataset_year
    )
    dietician_additional_appointment_date = get_field_heading(
        "dietician_additional_appointment_date", dataset_year
    )
    single_row_valid_df.loc[
        0,
        dietician_additional_appointment_offered,
    ] = 2
    single_row_valid_df.loc[0, dietician_additional_appointment_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "dietician_additional_appointment_date" in errors[0]

    visit = Visit.objects.first()

    assert visit.dietician_additional_appointment_offered == 2
    assert (
        visit.dietician_additional_appointment_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )


@pytest.mark.django_db
def test_dietician_additional_offered_date_missing_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that dietician extra appointment offered but date missing should pass
    https://github.com/rcpch/national-paediatric-diabetes-audit/issues/668
    """
    dietician_additional_appointment_offered = get_field_heading(
        "dietician_additional_appointment_offered", dataset_year
    )
    dietician_additional_appointment_date = get_field_heading(
        "dietician_additional_appointment_date", dataset_year
    )
    single_row_valid_df.loc[
        0,
        dietician_additional_appointment_offered,
    ] = 1
    single_row_valid_df.loc[0, dietician_additional_appointment_date] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "dietician_additional_appointment_date" not in errors[0]

    visit = Visit.objects.first()

    assert visit.dietician_additional_appointment_offered == 1
    assert visit.dietician_additional_appointment_date is None


@pytest.mark.django_db
def test_dietician_additional_offered_no_but_date_offered_fail_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that dietician additional appointment answered No but date offered should fail
    """
    dietician_additional_appointment_offered = get_field_heading(
        "dietician_additional_appointment_offered", dataset_year
    )
    dietician_additional_appointment_date = get_field_heading(
        "dietician_additional_appointment_date", dataset_year
    )
    single_row_valid_df.loc[
        0,
        dietician_additional_appointment_offered,
    ] = 2
    single_row_valid_df.loc[0, dietician_additional_appointment_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "dietician_additional_appointment_date" in errors[0]

    visit = Visit.objects.first()

    assert visit.dietician_additional_appointment_offered == 2
    assert (
        visit.dietician_additional_appointment_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )


"""
Inpatient admission tests
"""


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that inpatient admission for stabilisation is accepted
    """
    hospital_admission_date = get_field_heading("hospital_admission_date", dataset_year)
    hospital_discharge_date = get_field_heading("hospital_discharge_date", dataset_year)
    admission_reason_field = (
        "hospital_admission_reason_2026"
        if dataset_year >= 2026
        else "hospital_admission_reason"
    )
    hospital_admission_reason = get_field_heading(admission_reason_field, dataset_year)
    dka_additional_therapies = get_field_heading(
        "dka_additional_therapies", dataset_year
    )
    hospital_admission_other = get_field_heading(
        "hospital_admission_other", dataset_year
    )
    single_row_valid_df.loc[0, hospital_admission_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=8)
    )
    single_row_valid_df.loc[0, hospital_discharge_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=10)
    )

    single_row_valid_df.loc[0, hospital_admission_reason] = (
        1 if dataset_year < 2026 else 5
    )  # Stabilisation for pre-2026 dataset, DKA for 2026 dataset
    single_row_valid_df.loc[
        0,
        dka_additional_therapies,
    ] = None
    single_row_valid_df.loc[0, hospital_admission_other] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(
        date_instance=single_row_valid_df["Visit/Appointment Date"][0].date()
    )
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert (
        visit.hospital_admission_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=8)
    ), f"Admission date should be 1/1/2023, but was {visit.hospital_admission_date}"
    assert (
        visit.hospital_discharge_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=10)
    ), f"Discharge date should be 2/1/2023, but was {visit.hospital_discharge_date}"
    if dataset_year < 2026:
        assert visit.hospital_admission_reason == 1, (
            f"Admission reason should be 1 (stabilisation), but was {visit.hospital_admission_reason}"
        )
    else:
        assert visit.hospital_admission_reason_2026 == 5, (
            f"Admission reason should be 5 (Stabilisation), but was {visit.hospital_admission_reason_2026}"
        )
    assert visit.dka_additional_therapies is None, (
        f"DKA additional therapies should be None, but was {visit.dka_additional_therapies}"
    )
    assert visit.hospital_admission_other is None, (
        f"Admission other should be None, but was {visit.hospital_admission_other}"
    )


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_missing_date_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that inpatient admission for stabilisation is rejected if date missing
    """
    hospital_admission_date = get_field_heading("hospital_admission_date", dataset_year)
    hospital_discharge_date = get_field_heading("hospital_discharge_date", dataset_year)
    admission_reason_field = (
        "hospital_admission_reason_2026"
        if dataset_year >= 2026
        else "hospital_admission_reason"
    )
    hospital_admission_reason = get_field_heading(admission_reason_field, dataset_year)
    dka_additional_therapies = get_field_heading(
        "dka_additional_therapies", dataset_year
    )
    hospital_admission_other = get_field_heading(
        "hospital_admission_other", dataset_year
    )
    single_row_valid_df.loc[0, hospital_admission_date] = None
    single_row_valid_df.loc[0, hospital_discharge_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=10)
    )
    single_row_valid_df.loc[0, hospital_admission_reason] = (
        1 if dataset_year < 2026 else 5
    )  # Stabilisation for 2023-2025, DKA for 2026 onwards
    single_row_valid_df.loc[
        0,
        dka_additional_therapies,
    ] = None
    single_row_valid_df.loc[0, hospital_admission_other] = None

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(
        date_instance=single_row_valid_df["Visit/Appointment Date"][0].date()
    )
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert "hospital_admission_date" in errors[0]

    visit = Visit.objects.first()

    assert visit.hospital_admission_date is None
    assert (
        visit.hospital_discharge_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=10)
    )
    if dataset_year < 2026:
        assert visit.hospital_admission_reason == 1, (
            f"Admission reason should be 1 (stabilisation), but was {visit.hospital_admission_reason}"
        )
    else:
        assert visit.hospital_admission_reason_2026 == 5, (
            f"Admission reason should be 5 (Stabilisation), but was {visit.hospital_admission_reason_2026}"
        )
    assert visit.dka_additional_therapies is None, (
        f"DKA additional therapies should be None, but was {visit.dka_additional_therapies}"
    )
    assert visit.hospital_admission_other is None


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_discharge_date_before_admission_date_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that inpatient admission for stabilisation is rejected if discharge date before admission date
    """
    hospital_admission_date = get_field_heading("hospital_admission_date", dataset_year)
    hospital_discharge_date = get_field_heading("hospital_discharge_date", dataset_year)
    admission_reason_field = (
        "hospital_admission_reason_2026"
        if dataset_year >= 2026
        else "hospital_admission_reason"
    )
    hospital_admission_reason = get_field_heading(admission_reason_field, dataset_year)
    dka_additional_therapies = get_field_heading(
        "dka_additional_therapies", dataset_year
    )
    hospital_admission_other = get_field_heading(
        "hospital_admission_other", dataset_year
    )
    single_row_valid_df.loc[0, hospital_admission_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=8)
    )
    single_row_valid_df.loc[0, hospital_discharge_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )
    single_row_valid_df.loc[0, hospital_admission_reason] = (
        1 if dataset_year < 2026 else 5
    )  # Stabilisation for 2023-2025, DKA for 2026 onwards
    single_row_valid_df.loc[
        0,
        dka_additional_therapies,
    ] = None
    single_row_valid_df.loc[0, hospital_admission_other] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "hospital_admission_date" in errors[0]

    visit = Visit.objects.first()

    assert (
        visit.hospital_admission_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=8)
    )
    assert (
        visit.hospital_discharge_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )
    if dataset_year < 2026:
        assert visit.hospital_admission_reason == 1, (
            f"Admission reason should be 1 (stabilisation), but was {visit.hospital_admission_reason}"
        )
    else:
        assert visit.hospital_admission_reason_2026 == 5, (
            f"Admission reason should be 5 (Stabilisation), but was {visit.hospital_admission_reason_2026}"
        )
    assert visit.dka_additional_therapies is None, (
        f"DKA additional therapies should be None, but was {visit.dka_additional_therapies}"
    )
    assert visit.hospital_admission_other is None, (
        f"Hospital admission other should be None, but was {visit.hospital_admission_other}"
    )


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_discharge_date_before_diagnosis_date_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that inpatient admission for stabilisation is rejected if discharge date before admission date
    """
    diagnosis_date = get_field_heading("diagnosis_date", dataset_year)
    hospital_admission_date = get_field_heading("hospital_admission_date", dataset_year)
    hospital_discharge_date = get_field_heading("hospital_discharge_date", dataset_year)
    admission_reason_field = (
        "hospital_admission_reason_2026"
        if dataset_year >= 2026
        else "hospital_admission_reason"
    )
    hospital_admission_reason = get_field_heading(admission_reason_field, dataset_year)
    dka_additional_therapies = get_field_heading(
        "dka_additional_therapies", dataset_year
    )
    hospital_admission_other = get_field_heading(
        "hospital_admission_other", dataset_year
    )
    single_row_valid_df.loc[0, diagnosis_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=10)
    )
    single_row_valid_df.loc[0, hospital_admission_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=12)
    )
    single_row_valid_df.loc[0, hospital_discharge_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=11)
    )
    single_row_valid_df.loc[0, hospital_admission_reason] = (
        1 if dataset_year < 2026 else 5
    )  # Stabilisation
    single_row_valid_df.loc[
        0,
        dka_additional_therapies,
    ] = None
    single_row_valid_df.loc[0, hospital_admission_other] = None

    if dataset_year >= 2026:
        with freeze_time(
            audit_period_for_dataset_year.end_date + relativedelta(days=1)
        ):
            errors = csv_upload_sync(
                test_user,
                single_row_valid_df,
                _audit_period=audit_period_for_dataset_year,
            )
    else:
        errors = csv_upload_sync(
            test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
        )

    assert "hospital_admission_date" in errors[0]

    visit = Visit.objects.first()

    assert (
        visit.patient.diagnosis_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=10)
    ), (
        f"Diagnosis date should be {audit_period_for_dataset_year.start_date + relativedelta(days=10)}, but was {visit.patient.diagnosis_date}"
    )
    assert (
        visit.hospital_admission_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=12)
    ), (
        f"Admission date should be {audit_period_for_dataset_year.start_date + relativedelta(days=8)}, but was {visit.hospital_admission_date}"
    )
    assert (
        visit.hospital_discharge_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=11)
    ), (
        f"Discharge date should be {audit_period_for_dataset_year.start_date + relativedelta(days=1)}, but was {visit.hospital_discharge_date}"
    )
    if dataset_year < 2026:
        assert visit.hospital_admission_reason == 1, (
            f"Admission reason should be 1 (stabilisation), but was {visit.hospital_admission_reason}"
        )
    else:
        assert visit.hospital_admission_reason_2026 == 5, (
            f"Admission reason should be 5 (stabilisation in 2026), but was {visit.hospital_admission_reason_2026}"
        )
    assert visit.dka_additional_therapies is None, (
        f"DKA additional therapies should be None, but was {visit.dka_additional_therapies}"
    )
    assert visit.hospital_admission_other is None, (
        f"Admission other should be None, but was {visit.hospital_admission_other}"
    )


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_discharge_date_after_date_of_death_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that inpatient admission for stabilisation is rejected if discharge date before admission date
    """
    death_date = get_field_heading("death_date", dataset_year)
    hospital_admission_date = get_field_heading("hospital_admission_date", dataset_year)
    hospital_discharge_date = get_field_heading("hospital_discharge_date", dataset_year)
    admission_reason_field = (
        "hospital_admission_reason_2026"
        if dataset_year >= 2026
        else "hospital_admission_reason"
    )
    hospital_admission_reason = get_field_heading(admission_reason_field, dataset_year)
    dka_additional_therapies = get_field_heading(
        "dka_additional_therapies", dataset_year
    )
    hospital_admission_other = get_field_heading(
        "hospital_admission_other", dataset_year
    )
    hba1c_date = get_field_heading("hba1c_date", dataset_year)
    single_row_valid_df.loc[0, hba1c_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )
    single_row_valid_df.loc[0, death_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=0)
    )
    single_row_valid_df.loc[0, hospital_admission_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )
    single_row_valid_df.loc[0, hospital_discharge_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=8)
    )
    single_row_valid_df.loc[0, hospital_admission_reason] = (
        1 if dataset_year < 2026 else 5
    )  # Stabilisation for pre-2026 dataset, DKA for 2026 dataset
    single_row_valid_df.loc[
        0,
        dka_additional_therapies,
    ] = None
    single_row_valid_df.loc[0, hospital_admission_other] = None

    with freeze_time(audit_period_for_dataset_year.end_date - relativedelta(days=1)):
        errors = csv_upload_sync(
            test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
        )

    assert "hospital_discharge_date" in errors[0]

    visit = Visit.objects.first()

    assert (
        visit.patient.death_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=0)
    ), (
        f"Date of death should be {audit_period_for_dataset_year.start_date + relativedelta(days=0)}, but was {visit.patient.date_of_death}"
    )
    assert (
        visit.hospital_admission_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=1)
    ), (
        f"Admission date should be {audit_period_for_dataset_year.start_date + relativedelta(days=1)}, but was {visit.hospital_admission_date}"
    )
    assert (
        visit.hospital_discharge_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=8)
    ), (
        f"Discharge date should be {audit_period_for_dataset_year.start_date + relativedelta(days=8)}, but was {visit.hospital_discharge_date}"
    )
    if dataset_year < 2026:
        assert visit.hospital_admission_reason == 1, (
            f"Admission reason should be 1 (stabilisation), but was {visit.hospital_admission_reason}"
        )
    else:
        assert visit.hospital_admission_reason_2026 == 5, (
            f"Admission reason should be 5 (stabilisation in 2026), but was {visit.hospital_admission_reason_2026}"
        )
    assert visit.dka_additional_therapies is None, (
        f"DKA additional therapies should be None, but was {visit.dka_additional_therapies}"
    )
    assert visit.hospital_admission_other is None, (
        f"Admission other should be None, but was {visit.hospital_admission_other}"
    )


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_dka_additional_therapies_provided_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that inpatient admission for stabilisation is rejected if DKA additional therapies provided
    """
    hospital_admission_date = get_field_heading("hospital_admission_date", dataset_year)
    hospital_discharge_date = get_field_heading("hospital_discharge_date", dataset_year)
    admission_reason_field = (
        "hospital_admission_reason_2026"
        if dataset_year >= 2026
        else "hospital_admission_reason"
    )
    hospital_admission_reason = get_field_heading(admission_reason_field, dataset_year)
    dka_additional_therapies = get_field_heading(
        "dka_additional_therapies", dataset_year
    )
    hospital_admission_other = get_field_heading(
        "hospital_admission_other", dataset_year
    )
    single_row_valid_df.loc[0, hospital_admission_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=0)
    )
    single_row_valid_df.loc[0, hospital_discharge_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=7)
    )
    single_row_valid_df.loc[0, hospital_admission_reason] = (
        1 if dataset_year < 2026 else 5
    )  # Stabilisation for pre-2026 dataset, DKA for 2026 dataset
    single_row_valid_df.loc[0, dka_additional_therapies] = 1  # Hypertonic saline
    single_row_valid_df.loc[0, hospital_admission_other] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "dka_additional_therapies" in errors[0]

    visit = Visit.objects.first()

    assert (
        visit.hospital_admission_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=0)
    ), (
        f"Admission date should be {audit_period_for_dataset_year.start_date + relativedelta(days=0)}, but was {visit.hospital_admission_date}"
    )
    assert (
        visit.hospital_discharge_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=7)
    ), (
        f"Discharge date should be {audit_period_for_dataset_year.start_date + relativedelta(days=7)}, but was {visit.hospital_discharge_date}"
    )
    if dataset_year < 2026:
        assert visit.hospital_admission_reason == 1, (
            f"Admission reason should be 1 (stabilisation), but was {visit.hospital_admission_reason}"
        )
    else:
        assert visit.hospital_admission_reason_2026 == 5, (
            f"Admission reason should be 5 (stabilisation in 2026), but was {visit.hospital_admission_reason_2026}"
        )
    assert visit.dka_additional_therapies == 1, (
        f"DKA additional therapies should be 1 (hypertonic saline), but was {visit.dka_additional_therapies}"
    )
    assert visit.hospital_admission_other is None, (
        f"Admission other should be None, but was {visit.hospital_admission_other}"
    )


@pytest.mark.django_db
def test_inpatient_admission_stabilisation_hospital_admission_other_provided_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that inpatient admission for stabilisation is rejected if DKA additional therapies provided
    """
    hospital_admission_date = get_field_heading("hospital_admission_date", dataset_year)
    hospital_discharge_date = get_field_heading("hospital_discharge_date", dataset_year)
    admission_reason_field = (
        "hospital_admission_reason_2026"
        if dataset_year >= 2026
        else "hospital_admission_reason"
    )
    hospital_admission_reason = get_field_heading(admission_reason_field, dataset_year)
    dka_additional_therapies = get_field_heading(
        "dka_additional_therapies", dataset_year
    )
    hospital_admission_other = get_field_heading(
        "hospital_admission_other", dataset_year
    )
    single_row_valid_df.loc[0, hospital_admission_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=0)
    )
    single_row_valid_df.loc[0, hospital_discharge_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=7)
    )
    single_row_valid_df.loc[0, hospital_admission_reason] = (
        1 if dataset_year < 2026 else 5
    )  # Stabilisation for pre-2026 dataset, DKA for 2026 dataset
    single_row_valid_df.loc[
        0,
        dka_additional_therapies,
    ] = 1  # Hypertonic saline
    single_row_valid_df.loc[0, hospital_admission_other] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "dka_additional_therapies" in errors[0]

    visit = Visit.objects.first()

    assert (
        visit.hospital_admission_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=0)
    ), (
        f"Admission date should be {audit_period_for_dataset_year.start_date + relativedelta(days=0)}, but was {visit.hospital_admission_date}"
    )
    assert (
        visit.hospital_discharge_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=7)
    ), (
        f"Discharge date should be {audit_period_for_dataset_year.start_date + relativedelta(days=7)}, but was {visit.hospital_discharge_date}"
    )
    if dataset_year < 2026:
        assert visit.hospital_admission_reason == 1, (
            f"Admission reason should be 1 (stabilisation), but was {visit.hospital_admission_reason}"
        )
    else:
        assert visit.hospital_admission_reason_2026 == 5, (
            f"Admission reason should be 5 (stabilisation in 2026), but was {visit.hospital_admission_reason_2026}"
        )
    assert visit.dka_additional_therapies == 1, (
        f"DKA additional therapies should be 1 (hypertonic saline), but was {visit.dka_additional_therapies}"
    )
    assert visit.hospital_admission_other is None, (
        f"Admission other should be None, but was {visit.hospital_admission_other}"
    )


@pytest.mark.django_db
def test_inpatient_admission_dka_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that inpatient admission for DKA with additional therapies is accepted
    """
    hospital_admission_date = get_field_heading("hospital_admission_date", dataset_year)
    hospital_discharge_date = get_field_heading("hospital_discharge_date", dataset_year)
    admission_reason_field = (
        "hospital_admission_reason_2026"
        if dataset_year >= 2026
        else "hospital_admission_reason"
    )
    hospital_admission_reason = get_field_heading(admission_reason_field, dataset_year)
    dka_additional_therapies = get_field_heading(
        "dka_additional_therapies", dataset_year
    )
    hospital_admission_other = get_field_heading(
        "hospital_admission_other", dataset_year
    )
    if dataset_year >= 2026:
        blood_gas_ph = get_field_heading("blood_gas_ph", dataset_year)
        blood_gas_bicarbonate = get_field_heading("blood_gas_bicarbonate", dataset_year)
    single_row_valid_df.loc[0, hospital_admission_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=0)
    )
    single_row_valid_df.loc[0, hospital_discharge_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=7)
    )
    single_row_valid_df.loc[0, hospital_admission_reason] = (
        2 if dataset_year < 2026 else 1
    )  # DKA
    single_row_valid_df.loc[
        0,
        dka_additional_therapies,
    ] = 1  # Hypertonic saline
    single_row_valid_df.loc[0, hospital_admission_other] = None
    if dataset_year >= 2026:
        single_row_valid_df.loc[0, blood_gas_ph] = 7.1
        single_row_valid_df.loc[0, blood_gas_bicarbonate] = 20

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert len(errors) == 0

    visit = Visit.objects.first()

    assert (
        visit.hospital_admission_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=0)
    ), (
        f"Admission date should be {audit_period_for_dataset_year.start_date + relativedelta(days=0)}, but was {visit.hospital_admission_date}"
    )
    assert (
        visit.hospital_discharge_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=7)
    ), (
        f"Discharge date should be {audit_period_for_dataset_year.start_date + relativedelta(days=7)}, but was {visit.hospital_discharge_date}"
    )
    if dataset_year < 2026:
        assert visit.hospital_admission_reason == 2, (
            f"Admission reason should be 2 (DKA), but was {visit.hospital_admission_reason}"
        )
    else:
        assert visit.hospital_admission_reason_2026 == 1, (
            f"Admission reason should be 1 (DKA in 2026), but was {visit.hospital_admission_reason_2026}"
        )
    assert visit.dka_additional_therapies == 1, (
        f"DKA additional therapies should be 1 (hypertonic saline), but was {visit.dka_additional_therapies}"
    )
    assert visit.hospital_admission_other is None, (
        f"Admission other should be None, but was {visit.hospital_admission_other}"
    )


@pytest.mark.django_db
def test_inpatient_admission_dka_additional_therapies_missing_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that inpatient admission for DKA without additional therapies is rejected
    """
    hospital_admission_date = get_field_heading("hospital_admission_date", dataset_year)
    hospital_discharge_date = get_field_heading("hospital_discharge_date", dataset_year)
    admission_reason_field = (
        "hospital_admission_reason_2026"
        if dataset_year >= 2026
        else "hospital_admission_reason"
    )
    hospital_admission_reason = get_field_heading(admission_reason_field, dataset_year)
    dka_additional_therapies = get_field_heading(
        "dka_additional_therapies", dataset_year
    )
    hospital_admission_other = get_field_heading(
        "hospital_admission_other", dataset_year
    )
    single_row_valid_df.loc[0, hospital_admission_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=0)
    )
    single_row_valid_df.loc[0, hospital_discharge_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=7)
    )
    single_row_valid_df.loc[0, hospital_admission_reason] = (
        2 if dataset_year < 2026 else 1
    )  # DKA
    single_row_valid_df.loc[
        0,
        dka_additional_therapies,
    ] = None
    single_row_valid_df.loc[0, hospital_admission_other] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "dka_additional_therapies" in errors[0]

    visit = Visit.objects.first()

    assert (
        visit.hospital_admission_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=0)
    ), (
        f"Admission date should be {audit_period_for_dataset_year.start_date + relativedelta(days=0)}, but was {visit.hospital_admission_date}"
    )
    assert (
        visit.hospital_discharge_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=7)
    ), (
        f"Discharge date should be {audit_period_for_dataset_year.start_date + relativedelta(days=7)}, but was {visit.hospital_discharge_date}"
    )
    if dataset_year < 2026:
        assert visit.hospital_admission_reason == 2, (
            f"Admission reason should be 2 (DKA), but was {visit.hospital_admission_reason}"
        )
    else:
        assert visit.hospital_admission_reason_2026 == 1, (
            f"Admission reason should be 1 (DKA in 2026), but was {visit.hospital_admission_reason_2026}"
        )
    assert visit.dka_additional_therapies is None, (
        f"DKA additional therapies should be None, but was {visit.dka_additional_therapies}"
    )
    assert visit.hospital_admission_other is None, (
        f"Admission other should be None, but was {visit.hospital_admission_other}"
    )


@pytest.mark.django_db
def test_inpatient_admission_dka_additional_therapies_hospital_admission_also_provided_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Tests that a hospital admission for DKA with additional therapies is rejected if hospital admission other is provided
    """
    hospital_admission_date = get_field_heading("hospital_admission_date", dataset_year)
    hospital_discharge_date = get_field_heading("hospital_discharge_date", dataset_year)
    admission_reason_field = (
        "hospital_admission_reason_2026"
        if dataset_year >= 2026
        else "hospital_admission_reason"
    )
    hospital_admission_reason = get_field_heading(admission_reason_field, dataset_year)
    dka_additional_therapies = get_field_heading(
        "dka_additional_therapies", dataset_year
    )
    hospital_admission_other = get_field_heading(
        "hospital_admission_other", dataset_year
    )
    single_row_valid_df.loc[0, hospital_admission_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=0)
    )
    single_row_valid_df.loc[0, hospital_discharge_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=7)
    )
    single_row_valid_df.loc[0, hospital_admission_reason] = (
        2 if dataset_year < 2026 else 1
    )  # DKA
    single_row_valid_df.loc[
        0,
        dka_additional_therapies,
    ] = 1  # Hypertonic saline
    single_row_valid_df.loc[0, hospital_admission_other] = "Other reason"
    if dataset_year >= 2026:
        blood_gas_ph = get_field_heading("blood_gas_ph", dataset_year)
        blood_gas_bicarbonate = get_field_heading("blood_gas_bicarbonate", dataset_year)
        single_row_valid_df.loc[0, blood_gas_ph] = 7.1
        single_row_valid_df.loc[0, blood_gas_bicarbonate] = 20

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    expected_reason_key = (
        "hospital_admission_reason_2026"
        if dataset_year >= 2026
        else "hospital_admission_reason"
    )
    assert expected_reason_key in errors[0]

    visit = Visit.objects.first()

    assert (
        visit.hospital_admission_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=0)
    ), (
        f"Admission date should be {audit_period_for_dataset_year.start_date + relativedelta(days=0)}, but was {visit.hospital_admission_date}"
    )
    assert (
        visit.hospital_discharge_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=7)
    ), (
        f"Discharge date should be {audit_period_for_dataset_year.start_date + relativedelta(days=7)}, but was {visit.hospital_discharge_date}"
    )
    if dataset_year < 2026:
        assert visit.hospital_admission_reason == 2, (
            f"Admission reason should be 2 (DKA), but was {visit.hospital_admission_reason}"
        )
    else:
        assert visit.hospital_admission_reason_2026 == 1, (
            f"Admission reason should be 1 (DKA in 2026), but was {visit.hospital_admission_reason_2026}"
        )
    assert visit.dka_additional_therapies == 1, (
        f"DKA additional therapies should be 1 (hypertonic saline), but was {visit.dka_additional_therapies}"
    )
    assert visit.hospital_admission_other == "Other reason", (
        f"Admission other should be 'Other reason', but was {visit.hospital_admission_other}"
    )


@pytest.mark.django_db
def test_inpatient_admission_other_passes_validation(
    freeze_for_audit,
    test_user,
    single_row_valid_df,
    audit_period_for_dataset_year,
    dataset_year,
):
    """
    Test that inpatient admission for other reason is accepted
    """
    hospital_admission_date = get_field_heading("hospital_admission_date", dataset_year)
    hospital_discharge_date = get_field_heading("hospital_discharge_date", dataset_year)
    admission_reason_field = (
        "hospital_admission_reason_2026"
        if dataset_year >= 2026
        else "hospital_admission_reason"
    )
    hospital_admission_reason = get_field_heading(admission_reason_field, dataset_year)
    dka_additional_therapies = get_field_heading(
        "dka_additional_therapies", dataset_year
    )
    hospital_admission_other = get_field_heading(
        "hospital_admission_other", dataset_year
    )
    single_row_valid_df.loc[0, hospital_admission_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=0)
    )
    single_row_valid_df.loc[0, hospital_discharge_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=7)
    )
    single_row_valid_df.loc[0, hospital_admission_reason] = 6  # Other
    single_row_valid_df.loc[
        0,
        dka_additional_therapies,
    ] = None
    single_row_valid_df.loc[0, hospital_admission_other] = "Other reason"

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert len(errors) == 0, "Should not have any errors but got: " + str(errors)

    visit = Visit.objects.first()

    assert (
        visit.hospital_admission_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=0)
    ), (
        f"Admission date should be {audit_period_for_dataset_year.start_date + relativedelta(days=0)}, but was {visit.hospital_admission_date}"
    )
    assert (
        visit.hospital_discharge_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=7)
    ), (
        f"Discharge date should be {audit_period_for_dataset_year.start_date + relativedelta(days=7)}   , but was {visit.hospital_discharge_date}"
    )
    if dataset_year < 2026:
        assert visit.hospital_admission_reason == 6, (
            f"Admission reason should be 6 (other), but was {visit.hospital_admission_reason}"
        )
    else:
        assert visit.hospital_admission_reason_2026 == 6, (
            f"Admission reason should be 6 (other), but was {visit.hospital_admission_reason}"
        )
    assert visit.dka_additional_therapies is None, (
        f"DKA additional therapies should be None, but was {visit.dka_additional_therapies}"
    )
    assert visit.hospital_admission_other == "Other reason", (
        f"Admission other should be 'Other reason', but was {visit.hospital_admission_other}"
    )


@pytest.mark.django_db
def test_inpatient_admission_other_missing_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that inpatient admission for other reason is rejected if reason missing
    """
    hospital_admission_date = get_field_heading("hospital_admission_date", dataset_year)
    hospital_discharge_date = get_field_heading("hospital_discharge_date", dataset_year)
    admission_reason_field = (
        "hospital_admission_reason_2026"
        if dataset_year >= 2026
        else "hospital_admission_reason"
    )
    hospital_admission_reason = get_field_heading(admission_reason_field, dataset_year)
    dka_additional_therapies = get_field_heading(
        "dka_additional_therapies", dataset_year
    )
    hospital_admission_other = get_field_heading(
        "hospital_admission_other", dataset_year
    )
    single_row_valid_df.loc[0, hospital_admission_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=0)
    )
    single_row_valid_df.loc[0, hospital_discharge_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=7)
    )
    single_row_valid_df.loc[0, hospital_admission_reason] = (
        6  # Other (same code in 2021 and 2026)
    )
    single_row_valid_df.loc[0, hospital_admission_other] = "Other reason"
    single_row_valid_df.loc[
        0,
        dka_additional_therapies,
    ] = None
    single_row_valid_df.loc[0, hospital_admission_other] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "hospital_admission_other" in errors[0]

    visit = Visit.objects.first()

    assert (
        visit.hospital_admission_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=0)
    ), (
        f"Admission date should be {audit_period_for_dataset_year.start_date + relativedelta(days=0)}, but was {visit.hospital_admission_date}"
    )
    assert (
        visit.hospital_discharge_date
        == audit_period_for_dataset_year.start_date + relativedelta(days=7)
    ), (
        f"Discharge date should be {audit_period_for_dataset_year.start_date + relativedelta(days=7)}, but was {visit.hospital_discharge_date}"
    )
    if dataset_year < 2026:
        assert visit.hospital_admission_reason == 6, (
            f"Admission reason should be 6 (other), but was {visit.hospital_admission_reason}"
        )
    else:
        assert visit.hospital_admission_reason_2026 == 6, (
            f"Admission reason should be 6 (other), but was {visit.hospital_admission_reason_2026}"
        )
    assert visit.dka_additional_therapies is None, (
        f"DKA additional therapies should be None, but was {visit.dka_additional_therapies}"
    )
    assert visit.hospital_admission_other is None, (
        f"Admission other should be None, but was {visit.hospital_admission_other}"
    )


"""
Visit date tests
"""


@pytest.mark.django_db
def test_visit_date_provided_passes_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that a visit date is accepted
    """
    visit_date = get_field_heading("visit_date", dataset_year)
    single_row_valid_df.loc[0, visit_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(days=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert len(errors) == 0, "Should not have any errors but got: " + str(errors)

    visit = Visit.objects.first()

    assert visit.visit_date == audit_period_for_dataset_year.start_date + relativedelta(
        days=1
    ), (
        f"Visit/Appointment Date should be {audit_period_for_dataset_year.start_date + relativedelta(days=1)}, but was {visit.visit_date}"
    )


@pytest.mark.django_db
def test_visit_date_missing_fails_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that a missing Visit/Appointment Date is rejected
    """
    visit_date = get_field_heading("visit_date", dataset_year)
    single_row_valid_df.loc[0, visit_date] = None

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "visit_date" in errors[0], "Expected error in visit_date, but got None"

    visit = Visit.objects.first()

    assert visit.visit_date is None, (
        f"Visit/Appointment Date should be None, but was {visit.visit_date}"
    )


@pytest.mark.django_db
def test_visit_date_not_before_date_of_birth(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that a Visit/Appointment Date before the date of birth is rejected
    """
    date_of_birth = get_field_heading("date_of_birth", dataset_year)
    visit_date = get_field_heading("visit_date", dataset_year)
    single_row_valid_df.loc[0, date_of_birth] = (
        audit_period_for_dataset_year.start_date + relativedelta(months=6)
    )
    single_row_valid_df.loc[0, visit_date] = audit_period_for_dataset_year.start_date
    # For dataset years >= 2026, freeze "today" to the day before
    # the audit period ends so validations that compare to today behave
    # consistently in CI/local runs.
    if dataset_year >= 2026:
        freeze_dt = audit_period_for_dataset_year.end_date - datetime.timedelta(days=1)
        with freeze_time(freeze_dt.isoformat()):
            errors = csv_upload_sync(
                test_user,
                single_row_valid_df,
                _audit_period=audit_period_for_dataset_year,
            )
            assert "visit_date" in errors[0]
            visit = Visit.objects.first()
            assert visit.visit_date == audit_period_for_dataset_year.start_date, (
                f"Visit date should be {audit_period_for_dataset_year.start_date}, but was {visit.visit_date}"
            )
            assert (
                visit.patient.date_of_birth
                == audit_period_for_dataset_year.start_date + relativedelta(months=6)
            ), (
                f"Date of birth should be {audit_period_for_dataset_year.start_date + relativedelta(months=6)}, but was {visit.patient.date_of_birth}"
            )
    else:
        errors = csv_upload_sync(
            test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
        )
        assert "visit_date" in errors[0]
        visit = Visit.objects.first()
        assert visit.visit_date == audit_period_for_dataset_year.start_date, (
            f"Visit date should be {audit_period_for_dataset_year.start_date}, but was {visit.visit_date}"
        )
        assert (
            visit.patient.date_of_birth
            == audit_period_for_dataset_year.start_date + relativedelta(months=6)
        ), (
            f"Date of birth should be {audit_period_for_dataset_year.start_date + relativedelta(years=1)}, but was {visit.patient.date_of_birth}"
        )


@pytest.mark.django_db
def test_visit_date_not_after_date_of_death(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Test that a Visit/Appointment Date after the date of death is rejected
    """
    death_date = get_field_heading("death_date", dataset_year)
    visit_date = get_field_heading("visit_date", dataset_year)
    single_row_valid_df.loc[0, death_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(years=0)
    )
    single_row_valid_df.loc[0, visit_date] = (
        audit_period_for_dataset_year.start_date + relativedelta(years=1)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "visit_date" in errors[0]

    visit = Visit.objects.first()

    assert visit.visit_date == audit_period_for_dataset_year.start_date + relativedelta(
        years=1
    ), (
        f"Visit date should be {audit_period_for_dataset_year.start_date + relativedelta(years=1)}, but was {visit.visit_date}"
    )
    assert (
        visit.patient.death_date
        == audit_period_for_dataset_year.start_date + relativedelta(years=0)
    ), (
        f"Death date should be {audit_period_for_dataset_year.start_date + relativedelta(years=0)}, but was {visit.patient.death_date}"
    )


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
def test_alternative_formats_for_sex(
    test_user,
    dummy_sheet_csv,
    alternative,
    expected,
    audit_period_for_dataset_year,
    dataset_year,
):
    if dataset_year >= 2026:
        sex_col = get_field_heading("sex", dataset_year)
    else:
        sex_col = _sex_heading_for_csv_string(dummy_sheet_csv)
    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[{"row": 1, "column": sex_col, "value": alternative}],
    )

    df = read_csv_from_str(one_row_csv).df

    errors = csv_upload_sync(test_user, df, _audit_period=audit_period_for_dataset_year)
    assert len(errors) == 0

    patient = Patient.objects.first()
    assert patient.sex == expected


@pytest.mark.django_db
def test_mix_of_standard_and_alternative_formats_for_sex(
    test_user, dummy_sheet_csv, dataset_year
):
    two_rows_csv = modify_raw_csv(
        dummy_sheet_csv,
        start=2,  # inclusive
        end=4,  # exclusive
        replacements=[
            {
                "row": 2,
                "column": _sex_heading_for_csv_string(dummy_sheet_csv)
                if dataset_year < 2026
                else get_field_heading("sex", dataset_year),
                "value": "M",
            }
        ],
    )

    df = read_csv_from_str(two_rows_csv).df

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(
        date_instance=df["Visit/Appointment Date"][0].date()
    )
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

    assert patient.ethnicity is None
    assert "ethnicity" in patient.errors


@pytest.mark.django_db
def test_case_insensitive_ethnic_category(test_user, dummy_sheet_csv):
    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[{"row": 1, "column": "Ethnic Category", "value": "a"}],
    )

    df = read_csv_from_str(one_row_csv).df

    errors = csv_upload_sync(test_user, df)
    assert "ethnicity" not in errors[0]

    patient = Patient.objects.first()

    assert patient.ethnicity == "A"
    assert patient.errors is None


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
        pytest.param("hospital_admission_reason_2026"),
        pytest.param("dka_additional_therapies"),
    ],
)
@pytest.mark.django_db
def test_bad_data_for_positive_small_integer_fields(
    test_user, dummy_sheet_csv, model_field, dataset_year, audit_period_for_dataset_year
):
    if (
        model_field
        in [
            "smoking_status",
            "hba1c_format",
            "treatment",
            "closed_loop_system",
            "glucose_monitoring",
            "hospital_admission_reason",
        ]
        and dataset_year >= 2026
    ):
        match model_field:
            case "smoking_status":
                model_field = "smoking_vaping_status"
            case "hba1c_format":
                pytest.skip("hba1c_format not in use for dataset year 2026 and beyond")
            case "treatment":
                pytest.skip("treatment not in use for dataset year 2026 and beyond")
            case "closed_loop_system":
                pytest.skip(
                    "closed_loop_system not in use for dataset year 2026 and beyond"
                )
            case "glucose_monitoring":
                pytest.skip(
                    "glucose_monitoring not in use for dataset year 2026 and beyond"
                )
            case "hospital_admission_reason":
                model_field = "hospital_admission_reason_2026"

    if model_field == "hospital_admission_reason_2026" and dataset_year < 2026:
        pytest.skip(
            "hospital_admission_reason_2026 only in use for dataset year 2026 and beyond"
        )

    headings = csv_definition_for(model_field, dataset_year)
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

        # need to add the date to transfer in 2026 for it to pass
        replacements = [{"row": 1, "column": column, "value": value}]
        if model_field == "reason_leaving_service":
            date_column = csv_definition_for("date_leaving_service", dataset_year)[
                "heading"
            ]
            date_value = (
                audit_period_for_dataset_year.end_date - relativedelta(days=1)
            ).strftime("%d/%m/%Y")
            replacements.append({"row": 1, "column": date_column, "value": date_value})

        one_row_csv = modify_raw_csv(
            dummy_sheet_csv,
            end=2,  # exclusive
            replacements=replacements,
        )

        df = read_csv_from_str(one_row_csv).df

        with freeze_time(
            audit_period_for_dataset_year.end_date - relativedelta(days=1)
        ):
            errors = csv_upload_sync(
                test_user, df, pdu=pdu, _audit_period=audit_period_for_dataset_year
            )

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
    audit_period.start_date = current_audit_year_start_date(
        date_instance=df["Visit/Appointment Date"][0].date()
    )
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, df, _audit_period=audit_period)

    assert len(errors) > 0
    assert model.objects.count() == 1

    instance = model.objects.first()

    assert getattr(instance, model_field) is None
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
def test_bad_data_for_date_fields(
    freeze_for_audit,
    test_user,
    dummy_sheet_csv,
    model_field,
    audit_period_for_dataset_year,
    dataset_year,
):
    headings = csv_definition_for(model_field, dataset_year=dataset_year)

    column = headings["heading"]
    model = apps.get_model("npda", headings["model"])

    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[{"row": 1, "column": column, "value": "NOT A DATE"}],
    )

    results = read_csv_from_str(one_row_csv, dataset_year=dataset_year)
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
    assert getattr(instance, model_field) is None


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
    audit_period.start_date = current_audit_year_start_date(
        date_instance=df["Visit/Appointment Date"][0].date()
    )
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, df, _audit_period=audit_period)

    assert len(errors) > 0
    assert model.objects.count() == 1

    instance = model.objects.first()

    assert getattr(instance, model_field) is None
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
    audit_period.start_date = current_audit_year_start_date(
        date_instance=df["Visit/Appointment Date"][0].date()
    )
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, df, _audit_period=audit_period)

    assert len(errors) == 0


@pytest.mark.django_db
def test_remove_empty_spaces_from_empty_fields(
    test_user, dummy_sheet_csv, dataset_year, audit_period_for_dataset_year
):
    """
    Test that empty spaces in empty fields are removed
    """
    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[
            {
                "row": 1,
                "column": "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
                "value": "   ",
            }
        ],
    )

    df = read_csv_from_str(one_row_csv, dataset_year=dataset_year).df

    errors = csv_upload_sync(test_user, df, _audit_period=audit_period_for_dataset_year)

    assert len(errors) == 0

    patient = Patient.objects.first()
    assert (
        Visit.objects.filter(patient=patient).first().dka_additional_therapies is None
    ), (
        f"Expected empty string for DKA additional therapies, but got {Visit.objects.filter(patient=patient).first().dka_additional_therapies}"
    )


@pytest.mark.django_db
def test_remove_empty_spaces_in_empty_date_fields(test_user, dummy_sheet_csv):
    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[{"row": 1, "column": "Death Date", "value": "   "}],
    )

    parsed_csv = read_csv_from_str(one_row_csv)
    assert len(parsed_csv.errors_to_return) == 0, (
        f"Expected no errors when parsing CSV, got {parsed_csv.errors_to_return}"
    )

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(
        date_instance=parsed_csv.df["Visit/Appointment Date"][0].date()
    )
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(
        test_user,
        parsed_csv.df,
        _audit_period=audit_period,
        errors_to_return=parsed_csv.errors_to_return,
    )

    assert len(errors) == 0, f"Expected no errors when uploading CSV, got {errors}"


@pytest.mark.django_db
def test_csv_height_weight_fields_with_units_have_units_removed(
    test_user, dummy_sheet_csv
):
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
    audit_period.start_date = current_audit_year_start_date(
        date_instance=df["Visit/Appointment Date"][0].date()
    )
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(test_user, df, _audit_period=audit_period)

    assert len(errors) == 0

    patient = Patient.objects.first()
    visit = Visit.objects.filter(patient=patient).first()

    assert visit.height == Decimal("150.0"), (
        f"Expected height to be 150.0, but got {visit.height}"
    )
    assert visit.weight == Decimal("50.0"), (
        f"Expected weight to be 50.0, but got {visit.weight}"
    )


@pytest.mark.django_db
def test_submission_has_audit_period_attached(test_user, single_row_valid_df):
    audit_period = AuditPeriod.objects.first()

    Submission.objects.all().delete()  # Clear any previous submissions

    csv_upload_sync(test_user, single_row_valid_df, _audit_period=audit_period)

    assert Submission.objects.count() == 1, "Expected one submission to be created"
    submission = Submission.objects.first()

    assert submission.audit_period == audit_period, (
        f"Expected submission to have audit period {audit_period}, but got {submission.audit_period}"
    )


@pytest.mark.django_db
def test_visit_with_too_big_decimal_number_still_saves(test_user, dummy_sheet_csv):
    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[{"row": 1, "column": "Patient Weight (kg)", "value": "3405.5"}],
    )

    parsed_csv = read_csv_from_str(one_row_csv)
    assert len(parsed_csv.errors_to_return) == 0, (
        f"Expected no errors when parsing CSV, got {parsed_csv.errors_to_return}"
    )

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(
        date_instance=parsed_csv.df["Visit/Appointment Date"][0].date()
    )
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(
        test_user,
        parsed_csv.df,
        _audit_period=audit_period,
        errors_to_return=parsed_csv.errors_to_return,
    )

    assert "weight" in errors[0], f"Expected weight to be in errors, but got {errors}"

    assert Visit.objects.count() == 1, "Expected one visit to be created"
    visit = Visit.objects.first()

    assert visit.weight == Decimal(0)
    assert "weight" in visit.errors, (
        f"Expected weight to have an error, but got {visit.errors}"
    )


@pytest.mark.django_db
def test_visit_with_too_precise_decimal_number_is_rounded(test_user, dummy_sheet_csv):
    one_row_csv = modify_raw_csv(
        dummy_sheet_csv,
        end=2,  # exclusive
        replacements=[
            {"row": 1, "column": "Patient Weight (kg)", "value": "34.12345612"}
        ],
    )

    parsed_csv = read_csv_from_str(one_row_csv)
    assert len(parsed_csv.errors_to_return) == 0, (
        f"Expected no errors when parsing CSV, got {parsed_csv.errors_to_return}"
    )

    # Set the audit period to be valid for the visit date at the outset
    audit_period = AuditPeriod.objects.first()
    audit_period.start_date = current_audit_year_start_date(
        date_instance=parsed_csv.df["Visit/Appointment Date"][0].date()
    )
    audit_period.end_date = audit_period.start_date + relativedelta(years=1)

    errors = csv_upload_sync(
        test_user,
        parsed_csv.df,
        errors_to_return=parsed_csv.errors_to_return,
        _audit_period=audit_period,
    )
    assert len(errors) == 0, f"Expected no errors when uploading CSV, got {errors}"

    assert Visit.objects.count() == 1, "Expected one visit to be created"
    visit = Visit.objects.first()

    assert visit.weight == Decimal("34.1")


# testing dates outside of the range of the audit period
@pytest.mark.django_db
def test_visit_form_dates_outside_of_audit_period(
    freeze_for_audit,
    test_user,
    single_row_valid_df,
    seed_audit_periods_fixture,
    audit_period_for_dataset_year,
    dataset_year,
):
    """
    Test that all dates outside in a visit of the audit period are allowed (https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1379)
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
        hospital_discharge_date
    """
    birth_date = get_field_heading("date_of_birth", dataset_year)
    diagnosis_date = get_field_heading("diagnosis_date", dataset_year)
    if dataset_year >= 2026:
        smoking_status = get_field_heading("smoking_vaping_status", dataset_year)
        hba1c_date = get_field_heading("hba1c_date", dataset_year)
        carbohydrate_counting_level_three_education_date = get_field_heading(
            "carbohydrate_counting_level_three_education_date", dataset_year
        )
    else:
        carbohydrate_counting_level_three_education_date = get_field_heading(
            "carbohydrate_counting_level_three_education_date", dataset_year
        )
        smoking_status = get_field_heading("smoking_status", dataset_year)
    reason_for_admission = get_field_heading("hospital_admission_reason", dataset_year)
    # set date of birth to 01/01/2015 as this cannot be after the other mocked dates
    single_row_valid_df.loc[0, birth_date] = (
        audit_period_for_dataset_year.start_date - relativedelta(years=5)
    )
    # set date of diabetes diagnosis to 01/01/2018 as this cannot be after the other mocked dates
    single_row_valid_df.loc[0, diagnosis_date] = (
        audit_period_for_dataset_year.start_date - relativedelta(years=2)
    )
    # set a smoking cessation outcome
    single_row_valid_df.loc[0, smoking_status] = 2  # Current smoker
    # set reason for admission to 1 (stabilisation) as this is required for the hospital admission dates
    single_row_valid_df.loc[0, reason_for_admission] = 1  # Stabilisation

    # set all the dates associated with the visit to 01/01/2020
    for date_field in get_all_visit_dates(dataset_year):
        # date_field is a (field_name, heading) tuple — use the heading to index the DataFrame
        single_row_valid_df.loc[0, date_field[1]] = (
            audit_period_for_dataset_year.start_date + relativedelta(years=1)
        )

    all_visits = get_all_visit_dates(dataset_year)

    assert Visit.objects.count() == 0, (
        "Expected no visits to be created before the test"
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "visit_date" in errors[0], (
        f"Expected visit_date to be in errors, but got {errors}"
    )

    for date_field in all_visits:
        if date_field[0] != "visit_date":
            assert date_field[0] not in errors[0], (
                f"Expected {date_field} not to be in errors, but got {errors}"
            )
    assert Visit.objects.count() == 1, (
        "Expected the visit still to be created even though visit date outside of audit period"
    )


@pytest.mark.django_db
def test_thyroid_and_coeliac_dates_within_90_days_before_diagnosis_pass_validation(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    # Set the audit period to be valid for the visit date at the outset

    diagnosis_date = get_field_heading("diagnosis_date", dataset_year)
    single_row_valid_df.loc[0, diagnosis_date] = (
        audit_period_for_dataset_year.start_date + datetime.timedelta(days=100)
    )

    coeliac_screening_date = get_field_heading("coeliac_screen_date", dataset_year)
    single_row_valid_df.loc[0, coeliac_screening_date] = (
        audit_period_for_dataset_year.start_date + datetime.timedelta(days=56)
    )
    thyroid_function_date = get_field_heading("thyroid_function_date", dataset_year)
    single_row_valid_df.loc[0, thyroid_function_date] = (
        audit_period_for_dataset_year.start_date + datetime.timedelta(days=89)
    )

    errors = csv_upload_sync(
        test_user, single_row_valid_df, _audit_period=audit_period_for_dataset_year
    )

    assert "coeliac_screen_date" not in errors[0]
    assert "thyroid_function_date" not in errors[0]


@pytest.mark.django_db
def test_uploading_csv_against_incorrect_pdu(
    freeze_for_audit,
    single_row_valid_df,
    tmp_path,
    client,
    test_rcpch_user,
    dataset_year,
    audit_period_for_dataset_year,
):
    single_row_valid_df["PDU Number"] = RCPCH_PZ_CODE

    # write back into temp
    tmp_csv_path = (
        tmp_path
        / "dummy_sheet_test_csv_upload_test_uploading_csv_against_incorrect_pdu.csv"
    )
    single_row_valid_df.to_csv(tmp_csv_path, index=False)

    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)

    url = reverse(
        "pdu-upload-csv",
        kwargs={
            "pz_code": ALDER_HEY_PZ_CODE,
            "audit_period": audit_period_for_dataset_year.slug,
        },
    )

    # Feed file to view
    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(url, {"csv_upload": csv_file}, format="multipart")

    assert response.status_code == 302

    error_messages = list(get_messages(response.wsgi_request))
    assert error_messages[0].level_tag == "error"

    assert Submission.objects.count() == 0, (
        "No submission should be created for incorrect PDU"
    )


@pytest.mark.django_db
def test_uploading_csv_with_conflicting_pdu_numbers(
    two_patients_with_one_visit_each, tmp_path, client, test_rcpch_user
):
    two_patients_with_one_visit_each.at[0, "PDU Number"] = RCPCH_PZ_CODE

    # write back into temp
    tmp_csv_path = (
        tmp_path
        / "dummy_sheet_test_csv_upload_test_uploading_csv_with_conflicting_pdu_numbers.csv"
    )
    two_patients_with_one_visit_each.to_csv(tmp_csv_path, index=False)

    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)

    url = reverse(
        "pdu-upload-csv",
        kwargs={"pz_code": ALDER_HEY_PZ_CODE, "audit_period": "2025-2026"},
    )

    # Feed file to view
    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(url, {"csv_upload": csv_file}, format="multipart")

    assert response.status_code == 302

    error_messages = list(get_messages(response.wsgi_request))
    assert error_messages[0].level_tag == "error"

    assert Submission.objects.count() == 0, (
        "No submission should be created for incorrect PDU"
    )


@pytest.mark.django_db
def test_uploading_csv_with_pdu_number_missing_leading_pz(
    two_patients_with_one_visit_each, tmp_path, client, test_rcpch_user
):
    two_patients_with_one_visit_each = two_patients_with_one_visit_each.assign(
        **{"PDU Number": "004"}
    )

    # write back into temp
    tmp_csv_path = (
        tmp_path
        / "dummy_sheet_test_csv_upload_test_uploading_csv_with_pdu_number_missing_leading_pz.csv"
    )
    two_patients_with_one_visit_each.to_csv(tmp_csv_path, index=False)

    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)

    url = reverse(
        "pdu-upload-csv", kwargs={"pz_code": "PZ004", "audit_period": "2025-2026"}
    )

    # Feed file to view
    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(url, {"csv_upload": csv_file}, format="multipart")

    assert response.status_code == 302

    redirect_url = reverse(
        "pdu-upload-csv-in-progress",
        kwargs={"pz_code": "PZ004", "audit_period": "2025-2026"},
    )
    assert response.url == redirect_url

    assert Submission.objects.count() == 1, (
        "Submission should be created for PDU with missing leading PZ"
    )
    assert Submission.objects.first().paediatric_diabetes_unit.pz_code == "PZ004"


@pytest.mark.django_db
def test_uploading_csv_with_pdu_number_missing_leading_zeros(
    two_patients_with_one_visit_each, tmp_path, client, test_rcpch_user
):
    two_patients_with_one_visit_each = two_patients_with_one_visit_each.assign(
        **{"PDU Number": "4"}
    )

    # write back into temp
    tmp_csv_path = (
        tmp_path
        / "dummy_sheet_test_csv_upload_ttest_uploading_csv_with_pdu_number_missing_leading_zeros.csv"
    )
    two_patients_with_one_visit_each.to_csv(tmp_csv_path, index=False)

    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)

    url = reverse(
        "pdu-upload-csv", kwargs={"pz_code": "PZ004", "audit_period": "2025-2026"}
    )

    # Feed file to view
    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(url, {"csv_upload": csv_file}, format="multipart")

    assert response.status_code == 302

    redirect_url = reverse(
        "pdu-upload-csv-in-progress",
        kwargs={"pz_code": "PZ004", "audit_period": "2025-2026"},
    )
    assert response.url == redirect_url

    assert Submission.objects.count() == 1, (
        "Submission should be created for PDU with missing leading zeroes"
    )
    assert Submission.objects.first().paediatric_diabetes_unit.pz_code == "PZ004"


@pytest.mark.django_db
def test_conflicting_stated_gender(test_user, one_patient_with_four_visits):
    df = one_patient_with_four_visits

    sex_col = _sex_heading_for_df(df)
    df.loc[0, sex_col] = SEX_TYPE[0][0]
    df.loc[1, sex_col] = SEX_TYPE[0][0]
    df.loc[2, sex_col] = SEX_TYPE[1][0]
    df.loc[3, sex_col] = SEX_TYPE[1][0]

    errors = csv_upload_sync(test_user, df)
    assert "sex" in errors[0]

    assert Patient.objects.count() == 1
    # Most recent (by visit date) modal value
    assert Patient.objects.first().sex == SEX_TYPE[1][0]


@pytest.mark.django_db
def test_conflicting_ethnicity(test_user, one_patient_with_four_visits):
    df = one_patient_with_four_visits

    df.loc[0, "Ethnic Category"] = ETHNICITIES[0][0]
    df.loc[1, "Ethnic Category"] = ETHNICITIES[0][0]
    df.loc[2, "Ethnic Category"] = ETHNICITIES[1][0]
    df.loc[3, "Ethnic Category"] = ETHNICITIES[1][0]

    errors = csv_upload_sync(test_user, df)
    assert "ethnicity" in errors[0]

    assert Patient.objects.count() == 1
    # Most recent (by visit date) modal value
    assert Patient.objects.first().ethnicity == ETHNICITIES[1][0]


@pytest.mark.django_db
def test_conflicting_ethnicity_where_null_is_the_most_common_value(
    test_user, one_patient_with_four_visits
):
    df = one_patient_with_four_visits

    df.loc[0, "Ethnic Category"] = ETHNICITIES[0][0]
    df.loc[1, "Ethnic Category"] = None
    df.loc[2, "Ethnic Category"] = None
    df.loc[3, "Ethnic Category"] = ETHNICITIES[1][0]

    errors = csv_upload_sync(test_user, df)
    assert "ethnicity" in errors[0]

    assert Patient.objects.count() == 1
    # Most recent (by visit date) modal value
    assert Patient.objects.first().ethnicity == ETHNICITIES[1][0]


@pytest.mark.django_db
def test_conflicting_date_of_birth(test_user, one_patient_with_four_visits):
    df = one_patient_with_four_visits

    df.loc[0, "Date of Birth"] = "01/01/2010"
    df.loc[1, "Date of Birth"] = "01/01/2010"
    df.loc[2, "Date of Birth"] = "01/01/2012"
    df.loc[3, "Date of Birth"] = "01/01/2012"

    errors = csv_upload_sync(test_user, df)
    assert "date_of_birth" in errors[0]

    assert Patient.objects.count() == 1
    # Most recent (by visit date) modal value
    assert Patient.objects.first().date_of_birth == datetime.date(2012, 1, 1)


@pytest.mark.django_db(transaction=True)
def test_conflicting_date_of_birth_where_null_is_the_only_value(
    seed_groups_per_function_fixture,
    seed_users_per_function_fixture,
    seed_audit_periods_per_function_fixture,
    one_patient_with_four_visits,
):
    # As this test needs full transaction support we can't use our session fixtures
    test_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    # Delete all patients to ensure we're starting from a clean slate
    Patient.objects.all().delete()

    df = one_patient_with_four_visits

    df.loc[0, "Date of Birth"] = None
    df.loc[1, "Date of Birth"] = None
    df.loc[2, "Date of Birth"] = None
    df.loc[3, "Date of Birth"] = None

    errors = csv_upload_sync(test_user, df)
    assert "date_of_birth" in errors[0]

    assert Patient.objects.count() == 0


@pytest.mark.django_db
def test_conflicting_leaving_reason(test_user, one_patient_with_four_visits):
    df = one_patient_with_four_visits

    df.loc[0, "Reason for leaving service"] = LEAVE_PDU_REASONS[0][0]
    df.loc[0, "Date of leaving service"] = "01/01/2020"
    df.loc[1, "Reason for leaving service"] = LEAVE_PDU_REASONS[0][0]
    df.loc[1, "Date of leaving service"] = "01/01/2020"
    df.loc[2, "Reason for leaving service"] = LEAVE_PDU_REASONS[1][0]
    df.loc[2, "Date of leaving service"] = "01/01/2020"
    df.loc[3, "Reason for leaving service"] = LEAVE_PDU_REASONS[1][0]
    df.loc[3, "Date of leaving service"] = "01/01/2020"

    errors = csv_upload_sync(test_user, df)
    assert "reason_leaving_service" in errors[0]

    assert Patient.objects.count() == 1
    assert Transfer.objects.count() == 1
    # 1 > 2 > 3
    assert Transfer.objects.first().reason_leaving_service == LEAVE_PDU_REASONS[0][0]


@pytest.mark.django_db
def test_conflict_resolved_leaving_reason_must_have_date_attached(
    test_user, one_patient_with_four_visits
):
    df = one_patient_with_four_visits

    df.loc[0, "Reason for leaving service"] = LEAVE_PDU_REASONS[0][0]
    df.loc[1, "Reason for leaving service"] = LEAVE_PDU_REASONS[0][0]

    df.loc[2, "Reason for leaving service"] = LEAVE_PDU_REASONS[1][0]
    df.loc[2, "Date of leaving service"] = "01/01/2020"
    df.loc[3, "Reason for leaving service"] = LEAVE_PDU_REASONS[1][0]
    df.loc[3, "Date of leaving service"] = "01/01/2020"

    errors = csv_upload_sync(test_user, df)
    assert "reason_leaving_service" in errors[0]

    assert Patient.objects.count() == 1
    assert Transfer.objects.count() == 1
    # 1 > 2 > 3
    assert Transfer.objects.first().reason_leaving_service == LEAVE_PDU_REASONS[1][0]


@pytest.mark.django_db
def test_conflicting_diagnosis_date(test_user, one_patient_with_four_visits):
    df = one_patient_with_four_visits

    df.loc[0, "Date of Diabetes Diagnosis"] = "01/01/2019"
    df.loc[1, "Date of Diabetes Diagnosis"] = "01/01/2019"
    df.loc[2, "Date of Diabetes Diagnosis"] = "01/01/2018"
    df.loc[3, "Date of Diabetes Diagnosis"] = "01/01/2018"

    errors = csv_upload_sync(test_user, df)
    assert "diagnosis_date" in errors[0]

    assert Patient.objects.count() == 1
    # Earliest
    assert Patient.objects.first().diagnosis_date == datetime.date(2018, 1, 1)


@pytest.mark.django_db
def test_conflicting_diabetes_type_where_last_row_is_null(
    test_user, one_patient_with_four_visits
):
    df = one_patient_with_four_visits

    df.loc[0, "Diabetes Type"] = DIABETES_TYPES[0][0]
    df.loc[1, "Diabetes Type"] = DIABETES_TYPES[0][0]
    df.loc[2, "Diabetes Type"] = DIABETES_TYPES[1][0]
    df.loc[3, "Diabetes Type"] = None

    errors = csv_upload_sync(test_user, df)

    assert Patient.objects.count() == 1
    # Most recent by visit date
    assert Patient.objects.first().diabetes_type == DIABETES_TYPES[1][0]


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1344
@pytest.mark.django_db
def test_uploading_csv_with_multiple_pdu_numbers_including_one_missing(
    two_patients_first_with_two_visits_second_with_one,
    tmp_path,
    client,
    test_rcpch_user,
):
    two_patients_first_with_two_visits_second_with_one.at[0, "PDU Number"] = None
    two_patients_first_with_two_visits_second_with_one.at[1, "PDU Number"] = (
        RCPCH_PZ_CODE
    )
    two_patients_first_with_two_visits_second_with_one.at[2, "PDU Number"] = (
        ALDER_HEY_PZ_CODE
    )

    # write back into temp
    tmp_csv_path = (
        tmp_path
        / "dummy_sheet_test_csv_upload_test_uploading_csv_with_multiple_pdu_numbers_including_one_missing.csv"
    )
    two_patients_first_with_two_visits_second_with_one.to_csv(tmp_csv_path, index=False)

    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)

    url = reverse(
        "pdu-upload-csv",
        kwargs={"pz_code": ALDER_HEY_PZ_CODE, "audit_period": "2025-2026"},
    )

    # Feed file to view
    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(url, {"csv_upload": csv_file}, format="multipart")

    assert response.status_code == 302

    error_messages = list(get_messages(response.wsgi_request))
    assert error_messages[0].level_tag == "error"

    assert Submission.objects.count() == 0, (
        "No submission should be created for incorrect PDU"
    )


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1344
# Found as part of debugging the above issue so including for maximum regression proofing hopefully
@pytest.mark.django_db
def test_uploading_csv_with_first_row_missing_pdu_number(
    two_patients_with_one_visit_each, tmp_path, client, test_rcpch_user
):
    two_patients_with_one_visit_each = two_patients_with_one_visit_each.assign(
        **{"PDU Number": "PZ004"}
    )
    two_patients_with_one_visit_each.at[0, "PDU Number"] = None

    # write back into temp
    tmp_csv_path = (
        tmp_path
        / "dummy_sheet_test_csv_upload_test_uploading_csv_with_first_row_missing_pdu_number.csv"
    )
    two_patients_with_one_visit_each.to_csv(tmp_csv_path, index=False)

    # Log in user
    client = login_and_verify_user(client, test_rcpch_user)

    url = reverse(
        "pdu-upload-csv", kwargs={"pz_code": "PZ004", "audit_period": "2025-2026"}
    )

    # Feed file to view
    with open(tmp_csv_path, "rb") as csv_file:
        response = client.post(url, {"csv_upload": csv_file}, format="multipart")

    assert response.status_code == 302

    redirect_url = reverse(
        "pdu-upload-csv-in-progress",
        kwargs={"pz_code": "PZ004", "audit_period": "2025-2026"},
    )
    assert response.url == redirect_url

    assert Submission.objects.count() == 1, (
        "Submission should be created for upload where first row is missing PDU number but subsequent rows have correct PDU number"
    )
    assert Submission.objects.first().paediatric_diabetes_unit.pz_code == "PZ004"


@pytest.mark.django_db
def test_transfer_date_and_reason_leaving_service_are_saved(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    Regression: both date_leaving_service and reason_leaving_service must be
    persisted to the Transfer instance when both are present in the CSV.

    This test sets pd.Timestamp directly — it verifies that csv_upload's
    row_to_dict / PatientForm / get_valid_transfer_fields pipeline works
    correctly given already-parsed dates.  For the full end-to-end path
    (including the csv_parse string→Timestamp conversion) see
    test_transfer_date_and_reason_leaving_service_saved_via_full_parse.
    """
    leave_date = date(2022, 6, 1)
    leave_reason = LEAVE_PDU_REASONS[0][0]  # 1 = Transitioned to adult diabetes service

    single_row_valid_df.loc[0, "Date of leaving service"] = pd.Timestamp(leave_date)
    single_row_valid_df.loc[0, "Reason for leaving service"] = leave_reason

    errors = csv_upload_sync(
        test_user,
        single_row_valid_df,
        _audit_period=audit_period_for_dataset_year,
    )

    assert Transfer.objects.count() == 1
    transfer = Transfer.objects.first()

    assert transfer.date_leaving_service == leave_date, (
        f"Expected date_leaving_service={leave_date}, got {transfer.date_leaving_service}"
    )
    assert transfer.reason_leaving_service == leave_reason, (
        f"Expected reason_leaving_service={leave_reason}, got {transfer.reason_leaving_service}"
    )


@pytest.mark.django_db
def test_transfer_date_leaving_service_resolved_from_later_row(
    test_user, one_patient_with_four_visits
):
    """
    Regression for PZ016: when a patient has multiple rows and only a later
    row carries date_leaving_service + reason_leaving_service, both must still
    be saved to the Transfer instance.

    Previously merge_rows_for_patient had no case for date_leaving_service in
    its match statement.  It correctly resolved reason_leaving_service (via
    smallest_code_with_attached_date) and wrote the resolved value onto all
    rows, but left date_leaving_service unmodified — so rows.iloc[0] still had
    NaT.  PatientForm.clean() then saw reason supplied but no date, added an
    "invalid"-code error, and get_valid_transfer_fields nulled the date out.
    """
    df = one_patient_with_four_visits

    leave_date = date(2022, 6, 1)
    leave_reason = LEAVE_PDU_REASONS[0][0]  # 1 = Transitioned to adult diabetes service

    # Only the last row carries the transfer date and reason — earlier rows are empty
    df.loc[0, "Date of leaving service"] = None
    df.loc[0, "Reason for leaving service"] = None
    df.loc[1, "Date of leaving service"] = None
    df.loc[1, "Reason for leaving service"] = None
    df.loc[2, "Date of leaving service"] = None
    df.loc[2, "Reason for leaving service"] = None
    df.loc[3, "Date of leaving service"] = pd.Timestamp(leave_date)
    df.loc[3, "Reason for leaving service"] = leave_reason

    errors = csv_upload_sync(test_user, df)

    assert Transfer.objects.count() == 1
    transfer = Transfer.objects.first()

    assert transfer.date_leaving_service == leave_date, (
        f"date_leaving_service was not resolved from the later row. "
        f"Expected {leave_date}, got {transfer.date_leaving_service}. "
        f"Upload errors: {dict(errors)}"
    )
    assert transfer.reason_leaving_service == leave_reason, (
        f"Expected reason_leaving_service={leave_reason}, got {transfer.reason_leaving_service}"
    )


@pytest.mark.django_db
def test_transfer_date_and_reason_leaving_service_saved_via_full_parse(
    test_user, dummy_sheet_csv, audit_period_for_dataset_year, dataset_year
):
    """
    Production-faithful regression test: both date_leaving_service and
    reason_leaving_service must survive the full pipeline:
      raw CSV string → csv_parse (string→pd.Timestamp) → csv_upload.

    The previous test sets a pd.Timestamp directly, bypassing csv_parse.
    This one uses modify_raw_csv + read_csv_from_str so the date string
    "01/06/2022" must be parsed by csv_parse exactly as it would be in
    production.  If csv_parse silently coerces date_leaving_service to NaT
    (e.g. wrong format), PatientForm's cross-field validation adds an
    "invalid" error → get_valid_transfer_fields nulls the field → Transfer
    has date_leaving_service=None even though reason_leaving_service saved.
    """
    leave_date = date(2022, 6, 1)
    leave_date_str = "01/06/2022"  # DD/MM/YYYY — the format the NPDA template uses
    leave_reason = LEAVE_PDU_REASONS[0][0]  # 1 = Transitioned to adult diabetes service

    modified_csv = modify_raw_csv(
        dummy_sheet_csv,
        replacements=[
            {
                "row": 1,
                "column": "Date of leaving service",
                "value": leave_date_str,
            },
            {
                "row": 1,
                "column": "Reason for leaving service",
                "value": str(leave_reason),
            },
        ],
    )

    parsed = read_csv_from_str(modified_csv, dataset_year=dataset_year)
    df = parsed.df.head(1)

    errors = csv_upload_sync(
        test_user,
        df,
        _audit_period=audit_period_for_dataset_year,
    )

    assert Transfer.objects.count() == 1, (
        f"Expected 1 Transfer, got {Transfer.objects.count()}. Upload errors: {dict(errors)}"
    )
    transfer = Transfer.objects.first()

    assert transfer.date_leaving_service == leave_date, (
        f"date_leaving_service was dropped during csv_parse or csv_upload. "
        f"Expected {leave_date}, got {transfer.date_leaving_service}. "
        f"Upload errors: {dict(errors)}"
    )
    assert transfer.reason_leaving_service == leave_reason, (
        f"Expected reason_leaving_service={leave_reason}, got {transfer.reason_leaving_service}"
    )


@pytest.mark.django_db
def test_reason_leaving_service_without_date_is_silently_dropped(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    A reason_leaving_service with no attached date_leaving_service is silently
    discarded by the merge step.

    merge_rows_for_patient processes reason_leaving_service via
    smallest_code_with_attached_date, which does dropna(subset=["Date of
    leaving service"]).  When no row has a date, it returns None — so the
    reason is nulled before PatientForm ever sees it.  Both fields arrive at
    PatientForm as None, so no cross-field validation error is raised and the
    Transfer is created with both fields null.

    This is the intended gate-keeping behaviour: a reason without a date
    carries no clinical meaning and is discarded rather than stored
    inconsistently.
    """
    leave_reason = LEAVE_PDU_REASONS[0][0]

    single_row_valid_df.loc[0, "Reason for leaving service"] = leave_reason
    single_row_valid_df.loc[0, "Date of leaving service"] = None

    errors = csv_upload_sync(
        test_user,
        single_row_valid_df,
        _audit_period=audit_period_for_dataset_year,
    )

    # No cross-field error — the merge step already discarded the orphaned reason
    assert "date_leaving_service" not in errors[0]
    assert "reason_leaving_service" not in errors[0]

    assert Transfer.objects.count() == 1
    transfer = Transfer.objects.first()
    assert transfer.date_leaving_service is None
    assert transfer.reason_leaving_service is None


@pytest.mark.django_db
def test_date_leaving_service_without_reason_raises_error(
    test_user, single_row_valid_df, audit_period_for_dataset_year, dataset_year
):
    """
    A date_leaving_service supplied without a reason_leaving_service must raise a
    validation error on reason_leaving_service.  PatientForm.clean() enforces this
    cross-field rule and the error code is "invalid", so get_valid_transfer_fields
    nulls reason_leaving_service in the Transfer (it was already None), but date
    survives because there is no error on that field.
    """
    leave_date = date(2022, 6, 1)

    single_row_valid_df.loc[0, "Date of leaving service"] = pd.Timestamp(leave_date)
    single_row_valid_df.loc[0, "Reason for leaving service"] = None

    errors = csv_upload_sync(
        test_user,
        single_row_valid_df,
        _audit_period=audit_period_for_dataset_year,
    )

    assert "reason_leaving_service" in errors[0], (
        "Expected a validation error on reason_leaving_service when date is set without a reason"
    )

    assert Transfer.objects.count() == 1
    assert Transfer.objects.first().reason_leaving_service is None
