# python imports
from datetime import date
import time
import logging
import os
from typing import Literal

# django imports
from django.apps import apps
from django.conf import settings
from django.utils import timezone

# third part imports
import pandas as pd
import nhs_number

# RCPCH imports
from ...constants import (
    CSV_HEADINGS,
    ALL_DATES,
    SEX_TYPE,
    ETHNICITIES,
    DIABETES_TYPES,
    LEAVE_PDU_REASONS,
    HOSPITAL_ADMISSION_REASONS,
    TREATMENT_TYPES,
    CLOSED_LOOP_TYPES,
    GLUCOSE_MONITORING_TYPES,
    HBA1C_FORMATS,
    ALBUMINURIA_STAGES,
    RETINAL_SCREENING_RESULTS,
    THYROID_TREATMENT_STATUS,
    SMOKING_STATUS,
    YES_NO_UNKNOWN,
    DKA_ADDITIONAL_THERAPIES,
)

from .validate_postcode import validate_postcode
from .nhs_ods_requests import gp_details_for_ods_code
from .quarter_for_date import retrieve_quarter_for_date

from ..forms.patient_form import PatientForm
from ..forms.visit_form import VisitForm

# Logging setup
logger = logging.getLogger(__name__)


def csv_upload(user, csv_file=None, organisation_ods_code=None, pdu_pz_code=None):
    """
    Processes standardised NPDA csv file and persists results in NPDA tables

    accepts CSV file with standardised column names

    return True if successful, False with error message if not
    """
    Patient = apps.get_model("npda", "Patient")
    Site = apps.get_model("npda", "Site")
    Visit = apps.get_model("npda", "Visit")
    AuditCohort = apps.get_model("npda", "AuditCohort")

    # set previous quarter to inactive
    AuditCohort.objects.filter(
        pz_code=pdu_pz_code,
        ods_code=organisation_ods_code,
        audit_year=date.today().year,
        quarter=retrieve_quarter_for_date(date_instance=date.today()),
    ).update(submission_active=False)

    # create new quarter
    new_cohort = AuditCohort.objects.create(
        pz_code=pdu_pz_code,
        ods_code=organisation_ods_code,
        audit_year=date.today().year,
        quarter=retrieve_quarter_for_date(date_instance=date.today()),
        submission_date=timezone.now(),
        submission_by=user,
    )

    try:
        dataframe = pd.read_csv(
            csv_file, parse_dates=ALL_DATES, dayfirst=True, date_format="%d/%m/%Y"
        )
    except ValueError as error:
        return {"status": 500, "errors": f"Invalid file: {error}"}

    def csv_value_to_model_value(value):
        if pd.isnull(value):
            return None
        elif hasattr(value, 'to_pydatetime'):
            return value.to_pydatetime().date()
        
        return value

    def row_to_dict(row, mapping):
        return {
            model_field: csv_value_to_model_value(row[csv_field])
                for model_field, csv_field in mapping.items()
        }

    # private method - saves the csv rows for a given patient
    def save_rows(rows, timestamp, new_cohort):
        first_row = rows.iloc[0]

        patient_fields = row_to_dict(first_row, {
            "nhs_number": "NHS Number",
            "date_of_birth": "Date of Birth",
            "postcode": "Postcode of usual address",
            "sex": "Stated gender",
            "ethnicity": "Ethnic Category",
            "diabetes_type": "Diabetes Type",
            "gp_practice_ods_code": "GP Practice Code",
            "diagnosis_date": "Date of Diabetes Diagnosis",
            "death_date": "Death Date"
        })

        patient_fields["nhs_number"] = patient_fields["nhs_number"].replace(" ", "")

        patient_form = PatientForm(patient_fields)

        # TODO MRB: validate postcode
        # TODO MRB: Validate gp practice ods code
        patient_fields["is_valid"] = patient_form.is_valid()
        patient_fields["errors"] = patient_form.errors.as_json(escape_html = True)

        # TODO MRB: site errors
        patient_fields["site"] = save_site(first_row)

        site = save_site(first_row)
        patient = Patient.objects.create(**patient_fields)
        
        new_cohort.timestamp = timestamp
        new_cohort.patients.add(patient)
        new_cohort.save()

        rows.apply(lambda row: save_visit(patient, row), axis = 1)
        
    def save_site(row):
         # TODO MRB: do something with site_errors
        site, created = Site.objects.update_or_create(
            date_leaving_service=(
                row["Date of leaving service"]
                if not pd.isnull(row["Date of leaving service"])
                else None
            ),
            reason_leaving_service=(
                row["Reason for leaving service"]
                if not pd.isnull(row["Reason for leaving service"])
                else None
            ),
            paediatric_diabetes_unit_pz_code=pdu_pz_code,
            organisation_ods_code=organisation_ods_code,
        )

        return site

    def save_patient(site, row):
        fields = row_to_dict(row, {
            "nhs_number": "NHS Number",
            "date_of_birth": "Date of Birth",
            "postcode": "Postcode of usual address",
            "sex": "Stated gender",
            "ethnicity": "Ethnic Category",
            "diabetes_type": "Diabetes Type",
            "gp_practice_ods_code": "GP Practice Code",
            "diagnosis_date": "Date of Diabetes Diagnosis",
            "death_date": "Death Date"
        })

        fields["nhs_number"] = fields["nhs_number"].replace(" ", "")

        form = PatientForm(fields)

        # TODO MRB: validate postcode
        # TODO MRB: Validate gp practice ods code
        fields["is_valid"] = form.is_valid()
        fields["errors"] = form.errors.as_json(escape_html = True)

        fields["site"] = site

        patient = Patient.objects.create(**patient_fields)

    def save_visit(patient, row):
        fields = row_to_dict(row, {
            "visit_date": "Visit/Appointment Date",
            "height": "Patient Height (cm)",
            "weight": "Patient Weight (kg)",
            "height_weight_observation_date": "Observation Date (Height and weight)",
            "hba1c_format": "HbA1c result format",
            "hba1c_date": "Observation Date: Hba1c Value",
            "treatment": "Diabetes Treatment at time of Hba1c measurement",
            "closed_loop_system": "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?",
            "glucose_monitoring": "At the time of HbA1c measurement, in addition to standard blood glucose monitoring (SBGM), was the patient using any other method of glucose monitoring?",
            "systolic_blood_pressure": "Systolic Blood Pressure",
            "diastolic_blood_pressure": "Diastolic Blood pressure",
            "blood_pressure_observation_date": "Observation Date (Blood Pressure)",
            "foot_examination_observation_date": "Foot Assessment / Examination Date",
            "retinal_screening_observation_date": "Retinal Screening date",
            "retinal_screening_result": "Retinal Screening Result",
            "albumin_creatinine_ratio": "Urinary Albumin Level (ACR)",
            "albumin_creatinine_ratio_date": "Observation Date: Urinary Albumin Level",
            "albuminuria_stage": "Albuminuria Stage",
            "total_cholesterol": "Total Cholesterol Level (mmol/l)",
            "total_cholesterol_date": "Observation Date: Total Cholesterol Level",
            "thyroid_function_date": "Observation Date: Thyroid Function",
            "thyroid_treatment_status": "At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?",
            "coeliac_screen_date": "Observation Date: Coeliac Disease Screening",
            "gluten_free_diet": "Has the patient been recommended a Gluten-free diet?",
            "psychological_screening_assessment_date": "Observation Date - Psychological Screening Assessment",
            "psychological_additional_support_status": "Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?",
            "smoking_status": "Does the patient smoke?",
            "smoking_cessation_referral_date": "Date of offer of referral to smoking cessation service (if patient is a current smoker)",
            "carbohydrate_counting_level_three_education_date": "Date of Level 3 carbohydrate counting education received",
            "dietician_additional_appointment_offered": "Was the patient offered an additional appointment with a paediatric dietitian?",
            "dietician_additional_appointment_date": "Date of additional appointment with dietitian",
            "ketone_meter_training": "Was the patient using (or trained to use) blood ketone testing equipment at time of visit?",
            "flu_immunisation_recommended_date": "Date that influenza immunisation was recommended",
            "sick_day_rules_training_date": "Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia",
            "hospital_admission_date": "Start date (Hospital Provider Spell)",
            "hospital_discharge_date": "Discharge date (Hospital provider spell)",
            "hospital_admission_reason": "Reason for admission",
            "dka_additional_therapies": "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
            "hospital_admission_other": "Only complete if OTHER selected: Reason for admission (free text)"
        })

        fields["patient"] = patient

        form = VisitForm(fields, initial = {
            "patient": patient
        })

        fields["is_valid"] = form.is_valid()
        fields["errors"] = form.errors.as_json(escape_html = True)

        Visit.objects.create(**fields)

    # by passing this in we can use the same timestamp for all records
    timestamp = timezone.now()

    # sort = False preserves the original order of rows
    for (_, rows) in dataframe.groupby("NHS Number", sort = False):
        save_rows(rows, timestamp, new_cohort)

    return {"status": 200, "errors": None}


def csv_summarise(csv_file):
    """
    This function takes a csv file and processes the file to create a summary of the data
    It returns a dictionary with the status of the operation and the summary data
    """
    Patient = apps.get_model("npda", "Patient")
    # read the csv file
    try:
        dataframe = pd.read_csv(
            csv_file, parse_dates=ALL_DATES, dayfirst=True, date_format="%d/%m/%Y"
        )
    except Exception as error:
        return {
            "status": 422,
            "errors": f"Could not read csv file: {error}",
            "summary": None,
        }

    total_records = len(dataframe)
    number_unique_nhs_numbers = dataframe["NHS Number"].nunique()
    unique_nhs_numbers_no_spaces = (
        dataframe["NHS Number"].apply(lambda x: x.replace(" ", "")).unique()
    )
    count_of_records_per_nhs_number = dataframe["NHS Number"].value_counts()
    matching_patients_in_current_quarter = Patient.objects.filter(
        nhs_number__in=list(unique_nhs_numbers_no_spaces),
        audit_cohorts__submission_active=True,
        audit_cohorts__audit_year=date.today().year,
        audit_cohorts__quarter=retrieve_quarter_for_date(date_instance=date.today()),
    ).count()

    summary = {
        "total_records": total_records,
        "number_unique_nhs_numbers": number_unique_nhs_numbers,
        "count_of_records_per_nhs_number": list(
            count_of_records_per_nhs_number.items()
        ),
        "matching_patients_in_current_quarter": matching_patients_in_current_quarter,
    }

    return summary
