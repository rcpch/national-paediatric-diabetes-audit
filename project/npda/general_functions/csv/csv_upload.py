# python imports
import asyncio
import collections
import json
import logging

import httpx
import numpy as np

# third part imports
import pandas as pd
from asgiref.sync import sync_to_async

# django imports
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db import models as django_models
from django.utils import timezone

# RCPCH imports
from project.constants import (
    CSV_HEADING_OBJECTS,
    CSV_HEADING_OBJECTS_2026,
    UNIQUE_IDENTIFIER_ENGLAND,
    UNIQUE_IDENTIFIER_JERSEY,
)
from project.npda.general_functions.csv import gather_unique_patient_and_visit_counts

# Logging setup
logger = logging.getLogger(__name__)

from project.npda.forms.external_patient_validators import (  # noqa: E402
    validate_patient_async,
)
from project.npda.forms.external_visit_validators import (  # noqa: E402
    validate_visit_async,
)
from project.npda.forms.patient_form import PatientForm  # noqa: E402
from project.npda.forms.visit_form import VisitForm  # noqa: E402
from project.npda.general_functions.csv.csv_clean import csv_clean  # noqa: E402
from project.npda.general_functions.csv.csv_merge import (  # noqa: E402
    merge_rows_for_patient,
)
from project.npda.models import (  # noqa: E402
    Patient,
    Submission,
    Transfer,
    Visit,
    VisitActivity,
)


def create_csv_submission(
    pdu,
    audit_period,
    csv_file_bytes,
    csv_file_name,
    submission_active,
    user=None,
    ip_address=None,
    new_dataframe=None,
):
    old_submission = Submission.objects.filter(
        paediatric_diabetes_unit=pdu,
        audit_period=audit_period,
        submission_active=True,
    ).first()

    if old_submission:
        old_submission.submission_active = False
        old_submission.save()

    # Gather unique patient and visit counts and update the submission
    patient_count, visit_per_patient_count, total_rows = (
        gather_unique_patient_and_visit_counts(
            dataframe=new_dataframe, is_jersey=pdu.pz_code == "PZ248"
        )
    )

    submission = Submission.objects.create(
        submission_date=timezone.now(),
        submission_by=user,
        paediatric_diabetes_unit=pdu,
        audit_year=audit_period.audit_year(),  # compatibility
        audit_period=audit_period,
        csv_file=csv_file_bytes,
        csv_file_name=csv_file_name,
        submission_active=submission_active,
        total_unique_patients=patient_count,
        total_unique_visits=total_rows,
        visit_counts_per_patient=json.dumps(visit_per_patient_count),
    )

    if user:
        VisitActivity.objects.create(
            activity=8,
            ip_address=ip_address,
            npdauser=user,
        )  # uploaded csv - activity 8

    return submission


def tidy_up_old_submissions(pdu, new_submission):
    all_submissions = Submission.objects.filter(
        paediatric_diabetes_unit=pdu,
        audit_year=new_submission.audit_year,  # compatibility
        audit_period=new_submission.audit_period,
    )

    for submission in all_submissions:
        if submission.id != new_submission.id:
            Patient.objects.filter(submissions=submission).delete()

            submission.submission_active = False
            submission.save()


async def csv_upload(
    dataframe,
    errors_to_return,
    csv_file_name,
    submission,
    allow_empty_visits=False,
    save_errors_on_submission=True,
):
    """
    Processes standardised NPDA csv file and persists results in NPDA tables
    Returns the empty dict if successful, otherwise ValidationErrors indexed by the row they occurred at
    """
    pdu = submission.paediatric_diabetes_unit

    # Infer dataset_year from submission.audit_period
    try:
        dataset_year = submission.audit_period.get_dataset_year()
    except Exception:
        dataset_year = 2021

    # But the dataframe itself may contain 2026 headings; prefer detecting from the dataframe
    # if present so tests that pass a dataframe directly don't rely on seeded AuditPeriod years.
    from project.npda.general_functions.headings import get_field_heading

    try:
        # Check for clear 2026-only headings
        if (
            get_field_heading("sex", 2026) in dataframe.columns
            or get_field_heading("blood_gas_ph", 2026) in dataframe.columns
        ):
            dataset_year = 2026
        # Otherwise if the dataframe explicitly has 2021 sex heading, prefer 2021
        elif get_field_heading("sex", 2021) in dataframe.columns:
            dataset_year = 2021
    except Exception:
        logger.debug(
            "Could not determine dataset year from headings, falling back to submission-derived year"
        )

    if pdu.pz_code == "PZ248":
        if dataset_year == 2026:
            CSV_HEADINGS = UNIQUE_IDENTIFIER_JERSEY + CSV_HEADING_OBJECTS_2026
        else:
            CSV_HEADINGS = UNIQUE_IDENTIFIER_JERSEY + CSV_HEADING_OBJECTS
        identifier_heading = UNIQUE_IDENTIFIER_JERSEY[0]["heading"]
    else:
        if dataset_year == 2026:
            CSV_HEADINGS = UNIQUE_IDENTIFIER_ENGLAND + CSV_HEADING_OBJECTS_2026
        else:
            CSV_HEADINGS = UNIQUE_IDENTIFIER_ENGLAND + CSV_HEADING_OBJECTS
        identifier_heading = UNIQUE_IDENTIFIER_ENGLAND[0]["heading"]

    # Helper functions
    def csv_value_to_model_value(model_field, value):
        if pd.isnull(value):
            return None

        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime().date()

        # Pass Django forms native Python values not numpy ones
        # https://github.com/rcpch/national-paediatric-diabetes-audit/issues/425
        python_value = value.item() if isinstance(value, np.generic) else value

        # pandas 2.x iterrows() converts Int64 (nullable int) columns to float64
        # when constructing the per-row Series, so 1 becomes np.float64(1.0).
        # .item() then gives Python float 1.0. Django's TypedChoiceField
        # stringifies that as "1.0" which doesn't match choice "1", causing
        # "Select a valid choice. 1.0 is not one of the available choices."
        # Cast integer-valued floats back to int for integer model fields.
        if (
            isinstance(python_value, float)
            and python_value.is_integer()
            and isinstance(model_field, django_models.IntegerField)
        ):
            return int(python_value)

        return python_value

    def row_to_dict(row, model):
        # Use the resolved CSV_HEADINGS (depends on dataset_year and PDU)
        ret = {}

        for entry in CSV_HEADINGS:
            if "model" in entry and apps.get_model("npda", entry["model"]) == model:
                model_field_name = entry["model_field"]
                model_field_definition = model._meta.get_field(model_field_name)

                csv_value = row[entry["heading"]]
                model_field_value = csv_value_to_model_value(
                    model_field_definition, csv_value
                )

                ret[model_field_name] = model_field_value

        return ret

    async def validate_patient_using_form(row, async_client):
        # Date and reason leaving service are validated by the patient form but saved in Transfer
        fields = row_to_dict(row, Patient) | row_to_dict(row, Transfer)

        form = PatientForm(
            fields, paediatric_diabetes_unit=pdu, audit_period=submission.audit_period
        )
        form.async_validation_results = await validate_patient_async(
            postcode=fields["postcode"],
            gp_practice_ods_code=fields["gp_practice_ods_code"],
            gp_practice_postcode=None,
            async_client=async_client,
        )

        return form

    async def validate_visit_using_form(patient_form, row, async_client):
        fields = row_to_dict(
            row,
            Visit,
        )

        form = VisitForm(
            data=fields,
            initial={"patient": patient_form.instance},
            audit_period=submission.audit_period,
        )
        form.async_validation_results = await validate_visit_async(
            birth_date=patient_form.cleaned_data.get("date_of_birth"),
            observation_date=fields["height_weight_observation_date"],
            height=fields["height"],
            weight=fields["weight"],
            sex=patient_form.cleaned_data.get("sex"),
            async_client=async_client,
        )

        return form

    def can_save_field(form, target_field_name):
        for field_name, errors in form.errors.as_data().items():
            if field_name == target_field_name:
                for error in errors:
                    if error.code in ["invalid", "invalid_choice"]:
                        return False

        return True

    # Numbers larger than (max_digits - decimal_places) will fail to save at the database level
    # https://github.com/rcpch/national-paediatric-diabetes-audit/issues/993
    def is_too_big_number(model, field_name, value):
        try:
            model_definition = model._meta.get_field(field_name)

            max_digits = getattr(model_definition, "max_digits", None)
            decimal_places = getattr(model_definition, "decimal_places", None)

            if max_digits and decimal_places:
                max_value = 10 ** (max_digits - decimal_places) - 1

                try:
                    return value >= max_value
                # Missing values or strings
                except TypeError:
                    return False

            return False
        except FieldDoesNotExist:
            # Handle fields like date_leaving_service that are on the PatientForm but not on the Patient model
            return False

    def save_errors_and_retain_valid_fields(row_index, form):
        # We want to retain fields so that we can show them in the user interface
        # Use the field value from cleaned_data, falling back to data if it's not there
        # We can't retain invalid fields however as they might fail database validation
        for key, value in form.cleaned_data.items():
            setattr(form.instance, key, value)

        for key, value in form.data.items():
            if is_too_big_number(form._meta.model, key, value):
                setattr(form.instance, key, 0)
            elif key not in form.cleaned_data and can_save_field(form, key):
                setattr(form.instance, key, value)
            elif not hasattr(form.instance, key):
                setattr(form.instance, key, None)

        form.instance.is_valid = form.is_valid()

        model_errors = collections.defaultdict(list)

        # From csv_parse. Strings rather than ValidationErrors.
        if row_index in errors_to_return:
            for field, errors in errors_to_return[row_index].items():
                for error in errors:
                    model_errors[field].append({"code": "", "message": error})

        # From forms. ValidationErrors.
        for field, errors in form.errors.get_json_data().items():
            model_errors[field] += errors

            # Confusingly the JSON in each instance retains the ValidationError code
            # but we just store the messages for the error json on Submission
            # TODO MRB: Rationalise in https://github.com/rcpch/national-paediatric-diabetes-audit/issues/332
            for error in errors:
                errors_to_return[row_index][field].append(error["message"])

        if model_errors:
            form.instance.errors = model_errors
        else:
            form.instance.errors = None

    def get_valid_transfer_fields(row, patient_form):
        transfer_fields = row_to_dict(row, Transfer) | {"paediatric_diabetes_unit": pdu}

        for field in transfer_fields:
            if not can_save_field(patient_form, field):
                transfer_fields[field] = None

        return transfer_fields

    """
    Process the csv file and validate and save the data in the tables, parsing any errors
    """
    dataframe = csv_clean(dataframe, dataset_year=dataset_year)

    # Remember the original row number to help users find where the problem was in the CSV
    # It may already be set if doing a bulk upload across multiple PDUs using the upload_csv command
    if "row_index" not in dataframe.columns:
        dataframe = dataframe.assign(row_index=np.arange(dataframe.shape[0]))

    # We only one to create one patient per NHS number (or URN if in Jersey) and we can't create their visits if we fail to save the patient model
    visits_by_patient = dataframe.groupby(identifier_heading, sort=False, dropna=False)

    async def save_patient_and_transfer(
        patient_form, transfer_fields, patient_row_index
    ):
        try:
            save_errors_and_retain_valid_fields(patient_row_index, patient_form)

            patient = await sync_to_async(lambda: patient_form.save(commit=False))()

            # Throw database level issues not covered by the form (eg missing both nhs_number and urn)
            patient.clean()
            await patient.asave()

            if patient:
                # add the patient to a new Transfer instance
                transfer_fields["paediatric_diabetes_unit"] = pdu
                transfer_fields["patient"] = patient
                await Transfer.objects.acreate(**transfer_fields)

                await submission.patients.aadd(patient)

            return patient
        except Exception as error:
            logger.exception(
                f"Error saving patient for {pdu.pz_code} from {csv_file_name}[{patient_row_index}]: {error}"
            )

            # We don't know what field caused the error so add to __all__
            errors_to_return[patient_row_index]["__all__"].append(str(error))

    async def save_visits(patient, visit_forms):
        for visit_form, visit_row_index in visit_forms:
            try:
                save_errors_and_retain_valid_fields(visit_row_index, visit_form)
                visit_form.instance.patient = patient

                await sync_to_async(lambda vf=visit_form: vf.save())()
            except Exception as error:
                logger.exception(
                    f"Error saving visit for {pdu.pz_code} from {csv_file_name}[{visit_row_index}]: {error}"
                )
                errors_to_return[visit_row_index]["__all__"].append(str(error))

    async def process_rows_for_patient(rows, async_client):
        patient = None
        first_patient_row_index = int(rows.iloc[0]["row_index"])

        merge_rows_for_patient(
            identifier_heading,
            rows,
            first_patient_row_index,
            errors_to_return,
            dataset_year,
        )
        patient_row = rows.iloc[0]

        try:
            patient_form = await validate_patient_using_form(patient_row, async_client)

            # Pull through cleaned_data so we can use it in the async visit validators
            await sync_to_async(patient_form.is_valid)()

            visit_forms = []
            for _, row in rows.iterrows():
                if allow_empty_visits and pd.isnull(row["Visit/Appointment Date"]):
                    logger.info(
                        f"Missing visit date for {pdu.pz_code} from {csv_file_name}[{row['row_index']}]. Skipping creating visit."
                    )
                    continue

                visit_form = await validate_visit_using_form(
                    patient_form, row, async_client
                )

                # Pull through cleaned_data
                visit_form.is_valid()

                visit_forms.append((visit_form, int(row["row_index"])))

            transfer_fields = get_valid_transfer_fields(patient_row, patient_form)

            patient = await save_patient_and_transfer(
                patient_form, transfer_fields, first_patient_row_index
            )

            if patient:
                await save_visits(patient, visit_forms)
        except Exception as e:
            # Unexpected!
            logging.exception(
                f"Unhandled exception processing {csv_file_name}[{first_patient_row_index}]"
            )  # triggers an admin email
            errors_to_return[first_patient_row_index]["__all__"].append(
                str(e)
            )  # record the row as failed

    async with httpx.AsyncClient() as async_client:
        async with asyncio.TaskGroup() as tg:
            # The maximum number of patients we will process in parallel
            # NB: each patient has a variable number of visits
            #
            # I tried 20, 10, 5 and 3 with 200 patients (16 visits each)
            # 20: 59s.
            # 10: 44s.
            # 5: 42s
            # 3: 45s
            #
            # I also tried no task group at all, just doing each patient in sequence
            # That took 1m 1s.
            #
            # So I went with 5. Seems a reasonable balance between an actual speed up and not hammering third party APIs.
            throttle_semaphore = asyncio.Semaphore(5)

            for _, rows in visits_by_patient:

                async def task(rows):
                    async with throttle_semaphore:
                        await process_rows_for_patient(rows, async_client)

                tg.create_task(task(rows))

    # Store the errors to report back to the user in the Data Quality Report
    if errors_to_return and save_errors_on_submission:
        submission.errors = json.dumps(errors_to_return)
        await submission.asave()

    return errors_to_return
