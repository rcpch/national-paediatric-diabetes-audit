import logging
import timeit

# django imports
from django.apps import apps
from django.utils import timezone
from django.core.exceptions import ValidationError

# third part imports
from celery import chord, group
from celery.result import GroupResult
import pandas as pd
import numpy as np

# RCPCH imports
from project.constants import (
    CSV_HEADING_OBJECTS,
    UNIQUE_IDENTIFIER_ENGLAND,
    UNIQUE_IDENTIFIER_JERSEY,
)
from project.npda.tasks import save_patient_and_visits_to_submission, gather_errors

# Logging setup
logger = logging.getLogger(__name__)


def csv_upload(user, dataframe, csv_file_name, csv_file_bytes, pz_code, audit_year):
    """
    Function to upload a CSV file to the database
    """
    # Get the models
    Patient = apps.get_model("npda", "Patient")
    Transfer = apps.get_model("npda", "Transfer")
    Visit = apps.get_model("npda", "Visit")
    Submission = apps.get_model("npda", "Submission")
    PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")

    start = timeit.default_timer()

    # Helper functions
    def csv_value_to_model_value(model_field, value):
        if pd.isnull(value) or value == pd.NaT:
            return None

        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime().date()

        # Pass Django forms native Python values not numpy ones
        # https://github.com/rcpch/national-paediatric-diabetes-audit/issues/425
        return value.item() if isinstance(value, np.generic) else value

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

    if pz_code == "PZ248":
        CSV_HEADINGS = UNIQUE_IDENTIFIER_JERSEY + CSV_HEADING_OBJECTS
    else:
        CSV_HEADINGS = UNIQUE_IDENTIFIER_ENGLAND + CSV_HEADING_OBJECTS

    """
    Work starts here - create a new submission and delete the previous one
    """

    # get the PDU object
    # TODO #249 MRB: handle case where PDU does not exist
    pdu = PaediatricDiabetesUnit.objects.get(pz_code=pz_code)

    # Set previous submission to inactive
    if Submission.objects.filter(
        paediatric_diabetes_unit__pz_code=pdu.pz_code,
        audit_year=audit_year,
        submission_active=True,
    ).exists():
        original_submission = Submission.objects.filter(
            submission_active=True,
            paediatric_diabetes_unit__pz_code=pdu.pz_code,
            audit_year=audit_year,
        ).get()  # there can be only one of these - store it in a variable in case we need to revert
    else:
        original_submission = None

    # Create new submission for the audit year
    # It is not possble to create submissions in years other than the current year
    try:
        new_submission = Submission.objects.create(
            paediatric_diabetes_unit=pdu,
            audit_year=audit_year,
            submission_date=timezone.now(),
            submission_by=user,  # user is the user who is logged in. Passed in as a parameter
            submission_active=True,
            csv_file=csv_file_bytes,
            csv_file_name=csv_file_name,
        )

        new_submission.save()

    except Exception as e:
        logger.error(f"Error creating new submission: {e}")
        # the new submission was not created  - no action required as the previous submission is still active
        raise ValidationError(
            {
                "csv_upload": "Error creating new submission. The old submission has been restored."
            }
        )

    # now can delete all patients and visits from the previous active submission
    if original_submission:
        try:
            original_submission_patient_count = Patient.objects.filter(
                submissions=original_submission
            ).count()
            logger.debug(
                f"Deleting patients from previous submission: {original_submission_patient_count}"
            )
            Patient.objects.filter(submissions=original_submission).delete()
        except Exception as e:
            raise ValidationError(
                {"csv_upload": "Error deleting patients from previous submission"}
            )

    # now can delete the any previous active submission's csv file (if it exists)
    # and remove the path from the field by setting it to None
    # the rest of the submission will be retained
    if original_submission:
        original_submission.submission_active = False
        try:
            original_submission.save()  # this action will delete the csv file also as per the save method in the model
        except Exception as e:
            raise ValidationError(
                {"csv_upload": "Error deactivating previous submission"}
            )

    """
    Process the csv file and validate and save the data in the tables, parsing any errors
    """

    # Remember the original row number to help users find where the problem was in the CSV
    dataframe = dataframe.assign(row_index=np.arange(dataframe.shape[0]))

    # We only one to create one patient per NHS number (or URN if in Jersey) and we can't create their visits if we fail to save the patient model
    if new_submission.paediatric_diabetes_unit.pz_code == "PZ248":
        visits_by_patient = dataframe.groupby(
            "Unique Reference Number", sort=False, dropna=False
        )
    else:
        visits_by_patient = dataframe.groupby("NHS Number", sort=False, dropna=False)

    # Process each patient and their visits
    tasks = []
    for patient_index, patient_group in visits_by_patient:
        patient_row = patient_group.iloc[0]
        patient_dict = row_to_dict(patient_row, Patient, csv_headings=CSV_HEADINGS)

        patients_submission_task = save_patient_and_visits_to_submission.s(
            patient_row_json=patient_row.to_json(date_format="iso"),
            patient_dict=patient_dict,
            patient_group_dict=patient_group.to_dict(orient="records"),
            pdu_id=pdu.id,
            submission_id=new_submission.id,
        )
        tasks.append(patients_submission_task)

    chords = chord(tasks)(
        gather_errors.s(new_submission.id)
    )  # gather_errors is a task that will be run after all the tasks in the chord have completed

    # Additionally, we can store all the tasks in a group to get the status of the group if we access it in the view
    # We will not apply the gather_errors task to this group as it will be applied to the chord
    group_id = chords.parent.id
    group_result = GroupResult(id=group_id, results=chords.parent.results)
    group_result.save()

    end = timeit.default_timer()

    logger.debug(f"Time taken to process the CSV file: {end - start} seconds")

    return str(group_id)
