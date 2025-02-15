# Python Imports
import collections
from collections import defaultdict
import json
import logging

# Django Imports
from django.apps import apps
from django.conf import settings

# Third party imports
from celery import shared_task
import numpy as np
import pandas as pd

# Project Imports
from .models import Patient, Transfer, Visit
from .forms.patient_form import PatientForm
from .forms.visit_form import VisitForm

# Logging setup
logger = logging.getLogger(__name__)


@shared_task
def hello():
    """
    THIS IS A SCHEDULED TASK THAT IS CALLED AT 06:00 EVERY DAY
    THE CRON DATE/FREQUENCY IS SET IN SETTING.PY
    """
    logger.debug("0600 cron check task ran successfully")


@shared_task
def save_patient_and_visits_to_submission(
    patient_row_dict, patient_dict, patient_group_dict, pdu_id, submission_id
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

    def convert_numpy_types(data):
        """
        Recursively convert numpy types to native Python types.
        """
        if isinstance(data, dict):
            return {
                convert_numpy_types(key): convert_numpy_types(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [convert_numpy_types(element) for element in data]
        elif isinstance(data, np.generic):
            return data.item()
        elif isinstance(data, np.ndarray):
            return data.tolist()
        else:
            return data

    def merge_errors(existing_errors, new_errors):
        """
        Merge new errors into existing errors.
        """
        for key, value in new_errors.items():
            if key in existing_errors:
                if isinstance(value, dict):
                    merge_errors(existing_errors[key], value)
                else:
                    existing_errors[key].extend(value)
            else:
                existing_errors[key] = value
        return existing_errors

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
        if pd.isnull(value):
            return None

        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime().date()

        # Pass Django forms native Python values not numpy ones
        # https://github.com/rcpch/national-paediatric-diabetes-audit/issues/425
        return value.item() if isinstance(value, np.generic) else value

    """
    Main function
    """
    Submission = apps.get_model("npda", "Submission")
    PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")

    print("running save patient in celery...")

    # Gather all error messages indexed by row number and the field that caused them (__all__ if we don't know which one)
    # dict[number, dict[str, list[str]]]
    errors_to_return = collections.defaultdict(lambda: collections.defaultdict(list))
    patient_row = pd.Series(patient_row_dict)
    patient_group = pd.DataFrame(patient_group_dict)
    patient_form = PatientForm(data=patient_dict)
    pdu = PaediatricDiabetesUnit.objects.get(pk=pdu_id)
    submission = Submission.objects.get(pk=submission_id)

    if not patient_form.is_valid():
        retain_errors_and_invalid_field_data(patient_form)
        record_errors_from_form(
            errors_to_return, patient_row["row_index"], patient_form
        )

    patient = patient_form.save()

    transfer_fields = row_to_dict(
        patient_row, Transfer, csv_headings=get_csv_headings(pdu.pz_code)
    )

    # Save or update the patient transfer record
    Transfer.objects.update_or_create(
        patient=patient, paediatric_diabetes_unit=pdu, defaults=transfer_fields
    )

    # Add the patient to the submission
    submission.patients.add(patient)

    # Process each visit for the patient
    for visit_index, visit_row in patient_group.iterrows():
        visit_dict = row_to_dict(
            visit_row, Visit, csv_headings=get_csv_headings(pdu.pz_code)
        )
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

    return errors_to_return


@shared_task
def gather_errors(results, submission_id):
    """
    Gather errors from all tasks and store them in the submission.
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
    submission = Submission.objects.get(id=submission_id)

    # Store the errors in the submission
    if errors_to_return:
        submission.errors = json.dumps(errors_to_return)
        submission.save()

    return errors_to_return
