# Python Imports
import collections
from collections import defaultdict
from datetime import datetime
import json
import logging

# Django Imports
from django.apps import apps
from django.conf import settings
import django
import os

# Third party imports
from celery import shared_task
import numpy as np
import pandas as pd

# Project Imports
from .models import Patient, Transfer, Visit, NPDAUser
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
                    # this is a workaround - these fields are integer fields but the csv sometimes has them as floats
                    model_field_value = (
                        int(model_field_value) if model_field_value else None
                    )
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

    print(
        f"{PaediatricDiabetesUnit.objects.all().count()} paediatric diabetes units exist"
    )
    print(
        f"PDU PZ Code: {pz_code}, Paediatric Diabetes Unit exists: {PaediatricDiabetesUnit.objects.filter(pz_code=pz_code).exists()}"
    )
    print(f"{NPDAUser.objects.all().count()} users exist")
    print(f"{Patient.objects.all().count()} patients exist")
    print(f"{Submission.objects.all().count()} submissions exist")
    if Submission.objects.all().count() > 0:
        print(
            f"Submission: {Submission.objects.all().first().id}, PDU: {Submission.objects.all().first().paediatric_diabetes_unit} is active: {Submission.objects.all().first().submission_active}"
        )

    # Gather all error messages indexed by row number and the field that caused them (__all__ if we don't know which one)
    # dict[number, dict[str, list[str]]]
    errors_to_return = collections.defaultdict(lambda: collections.defaultdict(list))
    deserialized_patient_row = json.loads(patient_row_json)

    patient_row = pd.Series(convert_iso_dates(deserialized_patient_row))
    patient_group = pd.DataFrame(patient_group_dict)
    patient_form = PatientForm(data=patient_dict)
    pdu = PaediatricDiabetesUnit.objects.get(pz_code=pz_code)
    submission = Submission.objects.get(id=submission_id)

    if not patient_form.is_valid():
        retain_errors_and_invalid_field_data(patient_form)
        record_errors_from_form(
            errors_to_return, patient_row["row_index"], patient_form
        )

    patient = patient_form.save()

    transfer_fields = row_to_dict(
        patient_row, Transfer, csv_headings=get_csv_headings(pdu.pz_code)
    )

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
