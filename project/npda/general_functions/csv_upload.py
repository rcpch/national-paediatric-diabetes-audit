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
from django.core.exceptions import ValidationError

# third part imports
import pandas as pd
import numpy as np

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

    dataframe = pd.read_csv(
        csv_file, parse_dates=ALL_DATES, dayfirst=True, date_format="%d/%m/%Y"
    )

    # Set previous quarter to inactive
    AuditCohort.objects.filter(
        pz_code=pdu_pz_code,
        ods_code=organisation_ods_code,
        audit_year=date.today().year,
        quarter=retrieve_quarter_for_date(date_instance=date.today()),
    ).update(submission_active=False)

    # Create new quarter
    new_cohort = AuditCohort.objects.create(
        pz_code=pdu_pz_code,
        ods_code=organisation_ods_code,
        audit_year=date.today().year,
        quarter=retrieve_quarter_for_date(date_instance=date.today()),
        submission_date=timezone.now(),
        submission_by=user
    )

    def csv_value_to_model_value(model_field, value):
        if pd.isnull(value):
            return None
        
        # Pandas will convert an integer column to float if it contains missing values
        # http://pandas.pydata.org/pandas-docs/stable/user_guide/gotchas.html#missing-value-representation-for-numpy-types
        if pd.api.types.is_float(value) and model_field.choices:
            return int(value)

        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime().date()
        
        return value

    def row_to_dict(row, model, mapping):
        return {
            model_field: csv_value_to_model_value(
                model._meta.get_field(model_field), row[csv_field]
            )
                for model_field, csv_field in mapping.items()
        }
  
    def validate_site(row):
        # TODO MRB: do something with site_errors
        return row_to_dict(row, Site, {
            "date_leaving_service": "Date of leaving service",
            "reason_leaving_service": "Reason for leaving service"
        }) | {
            "paediatric_diabetes_unit_pz_code": pdu_pz_code,
            "organisation_ods_code": organisation_ods_code
        }

    def validate_patient_using_form(row):
        fields = row_to_dict(row, Patient, {
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

        # TODO MRB: check we Validate gp practice ods code
        form = PatientForm(fields)

        assign_original_row_indices_to_errors(form, row)

        return form

    def validate_visit_using_form(patient, row):
        fields = row_to_dict(row, Visit, {
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

        form = VisitForm(fields, initial = {
            "patient": patient
        })

        assign_original_row_indices_to_errors(form, row)

        return form

    def assign_original_row_indices_to_errors(form, row):
        for _, errors in form.errors.as_data().items():
            for error in errors:
                error.original_row_index = row["row_index"]

    def validate_rows(rows):
        first_row = rows.iloc[0]

        site_fields = validate_site(first_row)
        patient_form = validate_patient_using_form(first_row)

        visits = rows.apply(lambda row: validate_visit_using_form(patient_form.instance, row), axis = 1)

        return (patient_form, site_fields, visits)

    def gather_errors(form):
        ret = {}

        for field, errors in form.errors.as_data().items():
            for error in errors:
                errors_for_field = []

                if field in ret:
                    errors_for_field = ret[field]

                errors_for_field.append(error)

                ret[field] = errors_for_field
        
        return ret
    
    def has_error_that_would_fail_save(errors):
        for _, errors in errors.items():
            for error in errors:
                if error.code == 'required':
                    return True

    def create_instance(model, form):
        # We want to retain fields even if they're invalid so that we can edit them in the UI
        # Use the field value from cleaned_data, falling back to data if it's not there
        data = form.data | form.cleaned_data
        instance = model(**data)
        
        instance.is_valid = form.is_valid()
        instance.errors = None if form.is_valid() else form.errors.get_json_data(escape_html = True)

        return instance

    # We only one to create one patient per NHS number
    # Remember the original row number to help users find where the problem was in the CSV
    dataframe["row_index"] = np.arange(dataframe.shape[0])

    visits_by_patient = dataframe.groupby("NHS Number", sort = False, dropna = False)

    errors_to_return = {}

    for _, rows in visits_by_patient:
        (patient_form, site_fields, visits) = validate_rows(rows)

        errors_to_return = errors_to_return | gather_errors(patient_form)
        
        for visit_form in visits:
            errors_to_return = errors_to_return | gather_errors(visit_form)
        
        if not has_error_that_would_fail_save(errors_to_return):
            site = Site.objects.create(**site_fields)
            
            patient = create_instance(Patient, patient_form)

            patient.site = site
            patient.save()

            new_cohort.patients.add(patient)

            for visit_form in visits:
                visit = create_instance(Visit, visit_form)
                visit.patient = patient
                visit.save()
    
    new_cohort.save()

    if errors_to_return:
        raise ValidationError(errors_to_return)


def csv_summarise(csv_file):
    """
    This function takes a csv file and processes the file to create a summary of the data
    It returns a dictionary with the status of the operation and the summary data
    """
    Patient = apps.get_model("npda", "Patient")
    
    dataframe = pd.read_csv(
        csv_file, parse_dates=ALL_DATES, dayfirst=True, date_format="%d/%m/%Y"
    )

    total_records = len(dataframe)
    number_unique_nhs_numbers = dataframe["NHS Number"].nunique()
    unique_nhs_numbers_no_spaces = (
        dataframe["NHS Number"].fillna('').apply(lambda x: x.replace(" ", "")).unique()
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
