# Python Imports
import collections
from collections import defaultdict
from datetime import datetime
import json
import logging

# Django Imports
from django.apps import apps
from django.db import transaction

# Third party imports
from celery import shared_task
import numpy as np
import pandas as pd

# Project Imports
from .models import Visit
from .forms.patient_form import PatientForm
from .forms.visit_form import VisitForm
from .general_functions.csv.progress_recorder import ProgressTracker

# Logging setup
logger = logging.getLogger(__name__)


@shared_task
def hello():
    """
    THIS IS A SCHEDULED TASK THAT IS CALLED AT 06:00 EVERY DAY
    THE CRON DATE/FREQUENCY IS SET IN SETTING.PY
    """
    logger.debug("0600 cron check task ran successfully")


@shared_task(bind=True)
def save_patient_and_visits_to_submission(
    self, patient_row_json, patient_dict, patient_group_dict, pz_code, submission_id
):
    """
    Accepts a list of patient visits, creates a patient instance (validating using a patient form), then iterates
    through the visits, creating a form for each and gathering up the errors
    """

    """
    Helper functions
    """

    def retain_errors_and_invalid_field_data(form):
        # We want to retain fields even if they're invalid so that we can return them to the user
        # Use the field value from cleaned_data, falling back to data if it's not there
        for key, value in form.cleaned_data.items():
            setattr(form.instance, key, value)

        for key, value in form.data.items():
            if key not in form.cleaned_data:
                setattr(form.instance, key, value)

        form.instance.is_valid = form.is_valid()
        form.instance.errors = (
            None if form.is_valid() else form.errors.get_json_data(escape_html=True)
        )

    def record_errors_from_form(errors_to_return, row_index, form):
        for field, errors in form.errors.as_data().items():
            for error in errors:
                errors_to_return[row_index][field].extend(error.messages)

    def row_to_dict(row, model, csv_headings):
        ret = {}
        for entry in csv_headings:
            if "model" in entry and apps.get_model("npda", entry["model"]) == model:
                model_field_name = entry["model_field"]
                model_field_definition = model._meta.get_field(model_field_name)

                csv_value = row[entry["heading"]]
                model_field_value = csv_value_to_model_value(
                    model_field_definition, csv_value
                )

                if model_field_name in [
                    "diabetes_type",
                    "reason_leaving_service",
                    "hba1c_format",
                    "closed_loop_system",
                    "glucose_monitoring",
                    "retinal_screening_result",
                    "albuminuria_stage",
                    "thyroid_treatment_status",
                    "gluten_free_diet",
                    "psychological_additional_support_status",
                    "smoking_status",
                    "dietician_additional_appointment_offered",
                    "ketone_meter_training",
                    "hospital_admission_reason",
                    "dka_additional_therapies",
                ]:
                    if model_field_value:
                        try:
                            # this is a workaround - these fields are integer fields but the csv sometimes has them as floats
                            # this is because pandas reads the csv and converts the integers to floats
                            # so we need to convert them back to integers
                            # equally though, we need to handle the case where the csv has a blank value or a string that can't be converted to an integer
                            # and there are probably lots of edge cases that we haven't thought of so the best way to handle this is to try to convert the value to an integer
                            model_field_value = int(model_field_value)
                        except (TypeError, ValueError):
                            model_field_value = model_field_value
                            # if we can't convert it to an integer it is probably a blank value or a string that can't be converted to an integer
                            # the form will not be able to save it so we need to set it to None
                ret[model_field_name] = model_field_value

        return ret

    def get_csv_headings(pz_code):
        """
        Get the csv headings for England or Jersey
        """
        from project.constants import (
            CSV_HEADING_OBJECTS,
            UNIQUE_IDENTIFIER_ENGLAND,
            UNIQUE_IDENTIFIER_JERSEY,
        )

        if pz_code == "PZ248":
            return UNIQUE_IDENTIFIER_JERSEY + CSV_HEADING_OBJECTS
        else:
            return UNIQUE_IDENTIFIER_ENGLAND + CSV_HEADING_OBJECTS

    def csv_value_to_model_value(model_field, value):
        if pd.isnull(value) or value == pd.NaT:
            return None

        if type(value) == datetime:
            if value == datetime(1, 1, 1, 0, 0):
                return None
            return value.date()

        if isinstance(value, pd.Timestamp):
            # Convert datetime(1, 1, 1, 0, 0) to None - this is an invalid date
            # A workaround because in the process of converting the DataFrame to a dictionary
            # datefields that are empty are converted to datetime(1, 1, 1, 0, 0) which is invalid
            return value.to_pydatetime().date()

        # Pass Django forms native Python values not numpy ones
        # https://github.com/rcpch/national-paediatric-diabetes-audit/issues/425
        if isinstance(value, np.generic):
            return value.item()

        return value

    def convert_invalid_dates_to_none(data):
        """
        Recursively convert datetime(1, 1, 1, 0, 0) to None in the given data.
        """
        if isinstance(data, dict):
            return {
                key: convert_invalid_dates_to_none(value) for key, value in data.items()
            }
        elif isinstance(data, list):
            return [convert_invalid_dates_to_none(element) for element in data]
        elif isinstance(data, datetime) and data == datetime(1, 1, 1, 0, 0):
            return None
        else:
            return data

    def convert_iso_dates(obj):
        """Recursively converts ISO 8601 date strings in a JSON-like object to datetime."""
        if isinstance(obj, dict):
            return {k: convert_iso_dates(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_iso_dates(i) for i in obj]
        elif isinstance(obj, str):
            try:
                return (
                    pd.to_datetime(obj) if "T" in obj else obj
                )  # Check for ISO format
            except ValueError:
                return obj
        return obj

    def set_field_value_to_none_if_type_mismatch(form, visit_field):
        """
        Set the value of the field to None if the type is a mismatch
        """
        if form.fields[visit_field].widget.input_type == "select":
            # expecting a key value
            if field == "ethnicity":
                # expecting a string
                if type(visit_form.data[visit_field]) != str:
                    setattr(visit_form.instance, field, None)
            else:
                # expecting an integer
                if type(form.data[visit_field]) != int:
                    setattr(form.instance, field, None)
        elif form.fields[visit_field].widget.input_type == "date":
            # expecting a date
            if type(form.data[visit_field]) != datetime:
                setattr(form.instance, field, None)

    """
    Main function
    """

    # Create a progress tracker
    progress_tracker = ProgressTracker(self.request.id)
    total_visits = len(patient_group_dict)

    # import the models
    Submission = apps.get_model("npda", "Submission")
    PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")
    Transfer = apps.get_model("npda", "Transfer")

    print("running save patient in celery...")

    # Gather all error messages indexed by row number and the field that caused them (__all__ if we don't know which one)
    # dict[number, dict[str, list[str]]]
    errors_to_return = collections.defaultdict(lambda: collections.defaultdict(list))
    deserialized_patient_row = json.loads(patient_row_json)

    patient_row = pd.Series(convert_iso_dates(deserialized_patient_row))
    patient_group = pd.DataFrame(patient_group_dict)
    patient_form = PatientForm(data=patient_dict)
    pdu = PaediatricDiabetesUnit.objects.get(pz_code=pz_code)
    submission = Submission.objects.get(id=submission_id)

    # This protects the whole block of code from failing if there is an error and the database cannot be rolled back
    # This is important because we are creating multiple objects in the database
    # Hopefully it will never be needed, but it's good to have it just in case
    with transaction.atomic():
        if not patient_form.is_valid():
            retain_errors_and_invalid_field_data(patient_form)
            record_errors_from_form(
                errors_to_return, patient_row["row_index"], patient_form
            )
            # if the errors are in critical fields, we can't continue with this row
            critical_fields = [
                "nhs_number",
                "unique_reference_number",
                "date_of_birth",
                "diabetes_type",
                "diagnosis_date",
            ]
            if any(
                field in errors_to_return[patient_row["row_index"]]
                for field in critical_fields
            ):
                return errors_to_return
        try:
            patient = patient_form.save()
        except Exception as e:
            logger.error(f"Critical Error preventing creating patient: {e}")
            # If we can't create the patient, we can't create a transfer or the visits either
            # So we can't continue with this row
            # We have already gathered the errors from the patient form, so we can return them
            return errors_to_return

        transfer_fields = row_to_dict(
            patient_row, Transfer, csv_headings=get_csv_headings(pdu.pz_code)
        )

        if patient:
            # Save the patient transfer record
            Transfer.objects.create(
                **transfer_fields, patient=patient, paediatric_diabetes_unit=pdu
            )

            # Add the patient to the submission
            submission.patients.add(patient)

            # Process each visit for the patient
            for visit_index, visit_row in patient_group.iterrows():
                visit_dict = row_to_dict(
                    visit_row, Visit, csv_headings=get_csv_headings(pdu.pz_code)
                )
                # Convert invalid numpy types to None
                visit_dict = convert_invalid_dates_to_none(visit_dict)
                visit_dict["patient"] = patient

                visit_form = VisitForm(data=visit_dict, initial={"patient": patient})

                if not visit_form.is_valid():
                    retain_errors_and_invalid_field_data(visit_form)
                    record_errors_from_form(
                        errors_to_return, visit_row["row_index"], visit_form
                    )
                    # if the errors are critical (eg type mismatch) we should cast these values to None
                    # so that we can continue with the row
                    for field, errors in visit_form.errors.as_data().items():
                        for error in errors:
                            print(f"Critical Error {error.code}: {error.messages}")
                            if error.code in ["invalid", "invalid_choice"]:
                                # test if the error is a type mismatch - if so, set the value to None
                                set_field_value_to_none_if_type_mismatch(
                                    visit_form, field
                                )
                visit = visit_form.save()
                visit.is_valid = visit_form.is_valid()
                visit.save()

                # Update the progress tracker
                progress_tracker.set_progress(visit_index + 1, total_visits, patient.id)

    return errors_to_return


@shared_task
def gather_errors(results, submission_id):
    """
    Gather errors from all tasks and store them in the submission.
    Note: This function is called by a chord (a group of tasks that run in parallel) so it will only be called once all
    tasks have completed.
    We do not need access to each task object, just the results, so do not need to bind the function (bind=True).
    """
    errors_to_return = defaultdict(lambda: defaultdict(list))

    # Combine errors from all tasks
    for task_errors in results:
        for row_index, field_errors in task_errors.items():
            for field, errors in field_errors.items():
                errors_to_return[row_index][field].extend(errors)

    # Get the Submission model
    Submission = apps.get_model("npda", "Submission")

    # Get the submission instance
    try:
        submission = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        raise Exception("Submission not found or does not exist")

    # Store the errors in the submission
    if errors_to_return:
        submission.errors = json.dumps(errors_to_return)
        submission.save()

    print(f"Completing gather_errors: Errors to return: {errors_to_return}")

    return errors_to_return
