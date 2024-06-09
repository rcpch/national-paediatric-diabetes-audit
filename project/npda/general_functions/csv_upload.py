# python imports
from datetime import date
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
from .cohort_for_date import retrieve_cohort_for_date

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

    csv_file = os.path.join(
        settings.BASE_DIR, "project", "npda", "dummy_sheets", "dummy_sheet_invalid.csv"
    )

    try:
        dataframe = pd.read_csv(
            csv_file, parse_dates=ALL_DATES, dayfirst=True, date_format="%d/%m/%Y"
        )
    except ValueError as error:
        return {"status": 500, "errors": f"Invalid file: {error}"}

    def validate_row(row):
        """
        Validate each row

        Generates an array of error objects

        returns boolean (True if valid), None or array of error messages {'message': '[field name], [message]'}
        """

        """ 
        get all the data for this row
        """
        # Patient fields
        row_number = row["NHS Number"].replace(" ", "")
        date_of_birth = row["Date of Birth"]
        postcode = row["Postcode of usual address"]
        sex = row["Stated gender"]
        ethnicity = row["Ethnic Category"]
        diabetes_type = row["Diabetes Type"]
        gp_practice_ods_code = row["GP Practice Code"]
        practice_validation = gp_details_for_ods_code(ods_code=gp_practice_ods_code)
        diagnosis_date = row["Date of Diabetes Diagnosis"]
        death_date = row["Death Date"]
        # Site fields
        date_leaving_service = row["Date of leaving service"]
        reason_leaving_service = row["Reason for leaving service"]

        # Visit fields
        visit_date = row["Visit/Appointment Date"]
        height = row["Patient Height (cm)"]
        weight = row["Patient Weight (kg)"]
        height_weight_observation_date = row["Observation Date (Height and weight)"]
        hba1c = row["Hba1c Value"]
        hba1c_format = row["HbA1c result format"]
        hba1c_date = row["Observation Date: Hba1c Value"]
        treatment = row["Diabetes Treatment at time of Hba1c measurement"]
        closed_loop_system = row[
            "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?"
        ]
        glucose_monitoring = row[
            "At the time of HbA1c measurement, in addition to standard blood glucose monitoring (SBGM), was the patient using any other method of glucose monitoring?"
        ]
        systolic_blood_pressure = row["Systolic Blood Pressure"]
        diastolic_blood_pressure = row["Diastolic Blood pressure"]
        blood_pressure_observation_date = row["Observation Date (Blood Pressure)"]
        foot_examination_observation_date = row["Foot Assessment / Examination Date"]
        retinal_screening_observation_date = row["Retinal Screening date"]
        retinal_screening_result = row["Retinal Screening Result"]
        albumin_creatinine_ratio = row["Urinary Albumin Level (ACR)"]
        albumin_creatinine_ratio_date = row["Observation Date: Urinary Albumin Level"]
        albuminuria_stage = row["Albuminuria Stage"]
        total_cholesterol = row["Total Cholesterol Level (mmol/l)"]
        total_cholesterol_date = row["Observation Date: Total Cholesterol Level"]
        thyroid_function_date = row["Observation Date: Thyroid Function"]
        thyroid_treatment_status = row[
            "At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?"
        ]
        coeliac_screen_date = row["Observation Date: Coeliac Disease Screening"]
        gluten_free_diet = row["Has the patient been recommended a Gluten-free diet?"]
        psychological_screening_assessment_date = row[
            "Observation Date - Psychological Screening Assessment"
        ]
        psychological_additional_support_status = row[
            "Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?"
        ]
        smoking_status = row["Does the patient smoke?"]
        smoking_cessation_referral_date = row[
            "Date of offer of referral to smoking cessation service (if patient is a current smoker)"
        ]
        carbohydrate_counting_level_three_education_date = row[
            "Date of Level 3 carbohydrate counting education received"
        ]
        dietician_additional_appointment_offered = row[
            "Was the patient offered an additional appointment with a paediatric dietitian?"
        ]
        dietician_additional_appointment_date = row[
            "Date of additional appointment with dietitian"
        ]
        ketone_meter_training = row[
            "Was the patient using (or trained to use) blood ketone testing equipment at time of visit?"
        ]
        flu_immunisation_recommended_date = row[
            "Date that influenza immunisation was recommended"
        ]
        sick_day_rules_training_date = row[
            "Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia"
        ]
        hospital_admission_date = row["Start date (Hospital Provider Spell)"]
        hospital_discharge_date = row["Discharge date (Hospital provider spell)"]
        hospital_admission_reason = row["Reason for admission"]
        dka_additional_therapies = row[
            "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?"
        ]
        hospital_admission_other = row[
            "Only complete if OTHER selected: Reason for admission (free text)"
        ]

        mandatory_fields = [
            {
                "field": "date_of_birth",
                "name": "date of birth (YYYY-MM-DD)",
                "model": "Patient",
            },
            {
                "field": "postcode",
                "name": "Postcode of usual address",
                "model": "Patient",
            },
            {"field": "sex", "name": "Stated gender", "model": "Patient"},
            {"field": "ethnicity", "name": "Ethnic Category", "model": "Patient"},
            {"field": "diabetes_type", "name": "Diabetes Type", "model": "Patient"},
            {
                "field": "gp_practice_ods_code",
                "name": "GP Practice Code",
                "model": "Patient",
            },
            {
                "field": "diagnosis_date",
                "name": "Date of Diabetes Diagnosis",
                "model": "Patient",
            },
            {"field": "visit_date", "name": "Visit/Appointment Date", "model": "Visit"},
        ]

        """
        Private methods
        """

        def create_error(
            field_name: str,
            list_item: str,
            allowed_list: list,
            field_text: str,
            model: Literal["Patient", "Visit", "Site"],
        ):
            """
            Creates error object from item, list and string text
            """
            item_match = False
            for choice in allowed_list:
                if choice[0] == list_item:
                    item_match = True

            if item_match:
                # all items are valid, no errors
                return True, None, True, None, True, None
            else:
                error = {
                    "field": field_name,
                    "message": f"{field_text} supplied invalid. Must supply one of {allowed_list}",
                }
                if model == "Patient":
                    return False, error, True, None, True, None
                elif model == "Visit":
                    return True, None, False, error, True, None
                elif model == "Site":
                    return True, None, False, None, False, error

        def validate_date(
            date_under_examination_field_name,
            date_under_examination_name,
            date_under_examination,
            field_parent_model,
            date_of_birth,
            date_of_diagnosis,
            date_of_death=None,
        ):
            """
            Dates passed in are already validated as date objects
            This method validates the dates themselves
            It returns 4 values: 2 booleans relating to the model the validity of the field relates to, 2 lists of errors relating to each model field
            """
            patient_errors = []
            visit_errors = []
            site_errors = []

            if date_under_examination is None:
                # empty dates are not validated - if they are mandatory, they are caught further down
                return (patient_errors, visit_errors, site_errors)

            if date_under_examination < date_of_birth:
                error = {
                    "field": date_under_examination_field_name,
                    "message": f"'{date_under_examination_name}' cannot be before date of birth.",
                }
                if field_parent_model == "Patient":
                    patient_errors.append(error)
                elif field_parent_model == "Visit":
                    visit_errors.append(error)
                elif field_parent_model == "Site":
                    site_errors.append(error)

            if (
                date_under_examination < date_of_diagnosis
                and date_under_examination_field_name != "date_of_death"
            ):
                error = {
                    "field": date_under_examination_field_name,
                    "message": f"'{date_under_examination_name}' cannot be before date of diagnosis.",
                }
                if field_parent_model == "Patient":
                    patient_errors.append(error)
                elif field_parent_model == "Visit":
                    visit_errors.append(error)
                elif field_parent_model == "Site":
                    site_errors.append(error)

            if date_of_death is not None:
                if date_under_examination > date_of_death:
                    error = {
                        "field": date_under_examination_field_name,
                        "message": f"'{date_under_examination_name}' cannot be after date of death.",
                    }
                    if field_parent_model == "Patient":
                        patient_errors.append(error)
                    elif field_parent_model == "Visit":
                        visit_errors.append(error)
                    elif field_parent_model == "Site":
                        site_errors.append(error)

            return (
                patient_errors,
                visit_errors,
                site_errors,
            )

        lists_of_choices = [
            create_error(
                field_name="sex",
                list_item=sex,
                allowed_list=SEX_TYPE,
                field_text="'Stated gender'",
                model="Patient",
            ),
            create_error(
                field_name="ethnicity",
                list_item=ethnicity,
                allowed_list=ETHNICITIES,
                field_text="'Ethnic Category'",
                model="Patient",
            ),
            create_error(
                field_name="diabetes_type",
                list_item=diabetes_type,
                allowed_list=DIABETES_TYPES,
                field_text="'Diabetes Type'",
                model="Patient",
            ),
            create_error(
                field_name="reason_leaving_service",
                list_item=reason_leaving_service,
                allowed_list=LEAVE_PDU_REASONS,
                field_text="'Reason for leaving service'",
                model="Site",
            ),
            create_error(
                field_name="treatment",
                list_item=treatment,
                allowed_list=TREATMENT_TYPES,
                field_text="'Diabetes Treatment at time of Hba1c measurement'",
                model="Visit",
            ),
            create_error(
                field_name="closed_loop_system",
                list_item=closed_loop_system,
                allowed_list=CLOSED_LOOP_TYPES,
                field_text="'If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?'",
                model="Visit",
            ),
            create_error(
                field_name="glucose_monitoring",
                list_item=glucose_monitoring,
                allowed_list=GLUCOSE_MONITORING_TYPES,
                field_text="'At the time of HbA1c measurement, in addition to standard blood glucose monitoring (SBGM), was the patient using any other method of glucose monitoring?'",
                model="Visit",
            ),
            create_error(
                field_name="hba1c_format",
                list_item=hba1c_format,
                allowed_list=HBA1C_FORMATS,
                field_text="'HbA1c result format'",
                model="Visit",
            ),
            create_error(
                field_name="albuminuria_stage",
                list_item=albuminuria_stage,
                allowed_list=ALBUMINURIA_STAGES,
                field_text="'Albuminuria Stage'",
                model="Visit",
            ),
            create_error(
                field_name="retinal_screening_result",
                list_item=retinal_screening_result,
                allowed_list=RETINAL_SCREENING_RESULTS,
                field_text="'Provide a result for retinal screening only if screen performed. Abnormal is defined as any level of retinopathy in either eye.'",
                model="Visit",
            ),
            create_error(
                field_name="thyroid_treatment_status",
                list_item=thyroid_treatment_status,
                allowed_list=THYROID_TREATMENT_STATUS,
                field_text="'At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?'",
                model="Visit",
            ),
            create_error(
                field_name="gluten_free_diet",
                list_item=gluten_free_diet,
                allowed_list=YES_NO_UNKNOWN,
                field_text="'Has the patient been recommended a Gluten-free diet?'",
                model="Visit",
            ),
            create_error(
                field_name="psychological_additional_support_status",
                list_item=psychological_additional_support_status,
                allowed_list=YES_NO_UNKNOWN,
                field_text="'Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?'",
                model="Visit",
            ),
            create_error(
                field_name="smoking_status",
                list_item=smoking_status,
                allowed_list=SMOKING_STATUS,
                field_text="'Does the patient smoke?'",
                model="Visit",
            ),
            create_error(
                field_name="dietician_additional_appointment_offered",
                list_item=dietician_additional_appointment_offered,
                allowed_list=YES_NO_UNKNOWN,
                field_text="'Was the patient offered an additional appointment with a paediatric dietitian?'",
                model="Visit",
            ),
            create_error(
                field_name="ketone_meter_training",
                list_item=ketone_meter_training,
                allowed_list=YES_NO_UNKNOWN,
                field_text="'Was the patient using (or trained to use) blood ketone testing equipment at time of visit?'",
                model="Visit",
            ),
            create_error(
                field_name="hospital_admission_reason",
                list_item=hospital_admission_reason,
                allowed_list=HOSPITAL_ADMISSION_REASONS,
                field_text="'Reason for admission'",
                model="Visit",
            ),
            create_error(
                field_name="dka_additional_therapies",
                list_item=dka_additional_therapies,
                allowed_list=DKA_ADDITIONAL_THERAPIES,
                field_text="'Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?'",
                model="Visit",
            ),
        ]

        list_of_dates = [
            validate_date(
                date_under_examination_field_name="date_leaving_service",
                date_under_examination_name="Date of leaving service",
                date_under_examination=date_leaving_service,
                field_parent_model="Site",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="visit_date",
                date_under_examination_name="Visit/Appointment Date",
                date_under_examination=visit_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="height_weight_observation_date",
                date_under_examination_name="Observation Date (Height and weight)",
                date_under_examination=height_weight_observation_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="hba1c_date",
                date_under_examination_name="Observation Date: Hba1c Value",
                date_under_examination=hba1c_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="blood_pressure_observation_date",
                date_under_examination_name="Observation Date (Blood Pressure)",
                date_under_examination=blood_pressure_observation_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="foot_examination_observation_date",
                date_under_examination_name="Foot Assessment / Examination Date",
                date_under_examination=foot_examination_observation_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="retinal_screening_observation_date",
                date_under_examination_name="Retinal Screening date",
                date_under_examination=retinal_screening_observation_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="albumin_creatinine_ratio_date",
                date_under_examination_name="Observation Date: Urinary Albumin Level",
                date_under_examination=albumin_creatinine_ratio_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="total_cholesterol_date",
                date_under_examination_name="Observation Date: Total Cholesterol Level",
                date_under_examination=total_cholesterol_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="thyroid_function_date",
                date_under_examination_name="Observation Date: Thyroid Function",
                date_under_examination=thyroid_function_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="coeliac_screen_date",
                date_under_examination_name="Observation Date: Coeliac Disease Screening",
                date_under_examination=coeliac_screen_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="psychological_screening_assessment_date",
                date_under_examination_name="Observation Date - Psychological Screening Assessment",
                date_under_examination=psychological_screening_assessment_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="smoking_cessation_referral_date",
                date_under_examination_name="Date of offer of referral to smoking cessation service (if patient is a current smoker)",
                date_under_examination=smoking_cessation_referral_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="carbohydrate_counting_level_three_education_date",
                date_under_examination_name="Date of Level 3 carbohydrate counting education received",
                date_under_examination=carbohydrate_counting_level_three_education_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="dietician_additional_appointment_date",
                date_under_examination_name="Date of additional appointment with dietitian",
                date_under_examination=dietician_additional_appointment_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="flu_immunisation_recommended_date",
                date_under_examination_name="Date that influenza immunisation was recommended",
                date_under_examination=flu_immunisation_recommended_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="sick_day_rules_training_date",
                date_under_examination_name="Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia",
                date_under_examination=sick_day_rules_training_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="hospital_admission_date",
                date_under_examination_name="Start date (Hospital Provider Spell)",
                date_under_examination=hospital_admission_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_field_name="hospital_discharge_date",
                date_under_examination_name="Discharge date (Hospital provider spell)",
                date_under_examination=hospital_discharge_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
        ]

        """
        Validation starts here
        """
        # initialize
        patient_errors = []
        visit_errors = []
        site_errors = []

        # validate mandatory fields (these are only in Patient and Visit)
        for mandatory_field in mandatory_fields:
            if mandatory_field is None:
                if mandatory_field["model"] == "Patient":
                    patient_errors.append(
                        {
                            "field": mandatory_field["field"],
                            "message": f"'{mandatory_field['name']}' cannot be empty.",
                        }
                    )
                elif mandatory_field["model"] == "Visit":
                    visit_errors.append(
                        {
                            "field": mandatory_field["field"],
                            "message": f"'{mandatory_field['name']}' cannot be empty.",
                        }
                    )

        # validate list items
        for list_item in lists_of_choices:
            (
                patient_valid,
                patient_error,
                visit_valid,
                visit_error,
                site_valid,
                site_error,
            ) = list_item
            if not patient_valid:
                patient_errors.append(patient_error)
            elif not visit_valid:
                visit_errors.append(visit_error)
            elif not site_valid:
                site_errors.append(site_error)

        # validate dates
        for list_date in list_of_dates:
            (
                patient_error_list,
                visit_error_list,
                site_error_list,
            ) = list_date

            if len(patient_error_list) > 0:
                patient_errors += patient_error_list
            elif len(visit_error_list) > 0:
                visit_errors += visit_error_list
            elif len(site_error_list) > 0:
                site_errors += site_error_list

        # remaining validations
        if nhs_number.is_valid(row_number):
            pass
        else:
            error = {"field": "nhs_number", "message": "NHS Number invalid."}
            patient_errors.append(error)

        if AuditCohort.objects.filter(
            patient__nhs_number=row_number, submission_active=True
        ).exists():
            error = {"field": "nhs_number", "message": "NHS Number already exists."}
            patient_errors.append(error)

        if validate_postcode(postcode=postcode):
            pass
        else:
            error = {"field": "postcode", "message": "Postcode invalid."}
            patient_errors.append(error)

        if hasattr(practice_validation, "error"):
            error = {
                "field": "gp_practice_ods_code",
                "message": f"GP ODS Code invalid. {practice_validation['error']}",
            }
            patient_errors.append(error)

        if height is not None:
            if height < 50:
                error = {
                    "field": "height",
                    "message": f"'Patient Height (cm)' invalid. Cannot be below 50cm.",
                }
                visit_errors.append(error)
            elif height > 250:
                error = {
                    "field": "height",
                    "message": f"'Patient Height (cm)' invalid. Cannot be above 250cm.",
                }
                visit_errors.append(error)

        if weight is not None:
            if weight < 1:
                error = {
                    "field": "weight",
                    "message": f"'Patient Weight (kg)' invalid. Cannot be below 1kg.",
                }
                visit_errors.append(error)
            elif weight > 200:
                error = {
                    "field": "weight",
                    "message": f"'Patient Weight (kg)' invalid. Cannot be above 200kg.",
                }
                visit_errors.append(error)

        if hba1c is not None:
            if hba1c_format is None:
                error = {
                    "field": "hab1c_format",
                    "message": f"'Hba1c Value' invalid. Must supply HbA1c format.",
                }
                visit_errors.append(error)
            elif hba1c_format == 1:
                # mmol/mol
                if hba1c < 20 or hba1c > 195:
                    error = {
                        "field": "hba1c",
                        "message": f"'Hba1c Value' invalid. Out of range.",
                    }
                    visit_errors.append(error)
            elif hba1c_format == 2:
                # %
                if hba1c < 3 or hba1c > 20:
                    error = {
                        "field": "hba1c",
                        "message": f"'Hba1c Value' invalid. Out of range.",
                    }
                    visit_errors.append(error)

        if systolic_blood_pressure is not None:
            if systolic_blood_pressure > 240 or systolic_blood_pressure < 80:
                error = {
                    "field": "systolic_blood_pressure",
                    "message": f"'Systolic Blood Pressure' invalid. Out of range.",
                }
                visit_errors.append(error)

        if diastolic_blood_pressure is not None:
            if diastolic_blood_pressure < 20 or diastolic_blood_pressure > 120:
                error = {
                    "field": "diastolic_blood_pressure",
                    "message": f"'Diastolic Blood pressure' invalid. Out of range.",
                }
                visit_errors.append(error)

        if albumin_creatinine_ratio is not None:
            if albumin_creatinine_ratio > 50 or albumin_creatinine_ratio < 0:
                error = {
                    "field": "albumin_creatinine_ratio",
                    "message": f"'Urinary Albumin Level (ACR)' invalid. Out of range.",
                }
                visit_errors.append(error)

        if total_cholesterol is not None:
            if total_cholesterol > 12 or total_cholesterol < 2:
                error = {
                    "field": "total_cholesterol",
                    "message": f"'Total Cholesterol Level (mmol/l)' invalid. Out of range.",
                }
                visit_errors.append(error)

        # test if there were errors - return validation results with is_valid flag
        return (
            len(patient_errors) == 0,
            patient_errors,
            len(visit_errors) == 0,
            visit_errors,
            len(site_errors) == 0,
            site_errors,
        )

    # private method - saves the csv row in the model as a record
    def save_row(row, timestamp):
        """
        Save each row as a record
        First validate the values in the row, then create a Patient instance - if contains invalid items, set is_valid to False, with the error messages
        Then use the Patient instance to create a Visit instance, again testing values first and storing if is_valid and errors
        """
        (
            patient_is_valid,
            patient_errors,
            visit_is_valid,
            visit_errors,
            site_is_valid,
            site_errors,
        ) = validate_row(row)
        # save the site
        try:
            # save site
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
        except Exception as error:
            raise Exception(f"Could not save site: {error}")

        nhs_number = row["NHS Number"].replace(" ", "")

        try:
            patient, created = Patient.objects.update_or_create(
                nhs_number=nhs_number,
                defaults={
                    "site": site,
                    "date_of_birth": row["Date of Birth"],
                    "postcode": row["Postcode of usual address"],
                    "sex": row["Stated gender"],
                    "ethnicity": row["Ethnic Category"],
                    "diabetes_type": row["Diabetes Type"],
                    "diagnosis_date": row["Date of Diabetes Diagnosis"],
                    "death_date": (
                        row["Death Date"] if not pd.isnull(row["Death Date"]) else None
                    ),
                    "gp_practice_ods_code": row["GP Practice Code"],
                    "is_valid": patient_is_valid,
                    "errors": (patient_errors if patient_errors is not None else None),
                },
            )
        except Exception as error:
            raise Exception(f"Could not save patient: {error}")

        try:
            obj = {
                "patient": patient,
                "visit_date": row["Visit/Appointment Date"],
                "height": row["Patient Height (cm)"],
                "weight": row["Patient Weight (kg)"],
                "height_weight_observation_date": (
                    row["Observation Date (Height and weight)"]
                    if row["Observation Date (Height and weight)"] != " "
                    else None
                ),
                "hba1c": row["Hba1c Value"],
                "hba1c_format": row["HbA1c result format"],
                "hba1c_date": (
                    row["Observation Date: Hba1c Value"]
                    if not pd.isnull(row["Observation Date: Hba1c Value"])
                    else None
                ),
                "treatment": row["Diabetes Treatment at time of Hba1c measurement"],
                "closed_loop_system": (
                    row[
                        "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?"
                    ]
                    if not pd.isnull(
                        row[
                            "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?"
                        ]
                    )
                    else None
                ),
                "glucose_monitoring": row[
                    "At the time of HbA1c measurement, in addition to standard blood glucose monitoring (SBGM), was the patient using any other method of glucose monitoring?"
                ],
                "systolic_blood_pressure": row["Systolic Blood Pressure"],
                "diastolic_blood_pressure": row["Diastolic Blood pressure"],
                "blood_pressure_observation_date": (
                    row["Observation Date (Blood Pressure)"]
                    if not pd.isnull(row["Observation Date (Blood Pressure)"])
                    else None
                ),
                "foot_examination_observation_date": (
                    row["Foot Assessment / Examination Date"]
                    if not pd.isnull(row["Foot Assessment / Examination Date"])
                    else None
                ),
                "retinal_screening_observation_date": (
                    row["Retinal Screening date"]
                    if not pd.isnull(row["Retinal Screening date"])
                    else None
                ),
                "retinal_screening_result": row["Retinal Screening Result"],
                "albumin_creatinine_ratio": row["Urinary Albumin Level (ACR)"],
                "albumin_creatinine_ratio_date": (
                    row["Observation Date: Urinary Albumin Level"]
                    if not pd.isnull(row["Observation Date: Urinary Albumin Level"])
                    else None
                ),
                "albuminuria_stage": row["Albuminuria Stage"],
                "total_cholesterol": row["Total Cholesterol Level (mmol/l)"],
                "total_cholesterol_date": (
                    row["Observation Date: Total Cholesterol Level"]
                    if not pd.isnull(row["Observation Date: Total Cholesterol Level"])
                    else None
                ),
                "thyroid_function_date": (
                    row["Observation Date: Thyroid Function"]
                    if not pd.isnull(row["Observation Date: Thyroid Function"])
                    else None
                ),
                "thyroid_treatment_status": (
                    row[
                        "At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?"
                    ]
                    if not pd.isnull(
                        row[
                            "At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?"
                        ]
                    )
                    else None
                ),
                "coeliac_screen_date": (
                    row["Observation Date: Coeliac Disease Screening"]
                    if not pd.isnull(row["Observation Date: Coeliac Disease Screening"])
                    else None
                ),
                "gluten_free_diet": (
                    row["Has the patient been recommended a Gluten-free diet?"]
                    if not pd.isnull(
                        row["Has the patient been recommended a Gluten-free diet?"]
                    )
                    else None
                ),
                "psychological_screening_assessment_date": (
                    row["Observation Date - Psychological Screening Assessment"]
                    if not pd.isnull(
                        row["Observation Date - Psychological Screening Assessment"]
                    )
                    else None
                ),
                "psychological_additional_support_status": (
                    row[
                        "Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?"
                    ]
                    if not pd.isnull(
                        row[
                            "Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?"
                        ]
                    )
                    else None
                ),
                "smoking_status": (
                    row["Does the patient smoke?"]
                    if not pd.isnull(row["Does the patient smoke?"])
                    else None
                ),
                "smoking_cessation_referral_date": (
                    row[
                        "Date of offer of referral to smoking cessation service (if patient is a current smoker)"
                    ]
                    if not pd.isnull(
                        row[
                            "Date of offer of referral to smoking cessation service (if patient is a current smoker)"
                        ]
                    )
                    else None
                ),
                "carbohydrate_counting_level_three_education_date": (
                    row["Date of Level 3 carbohydrate counting education received"]
                    if not pd.isnull(
                        row["Date of Level 3 carbohydrate counting education received"]
                    )
                    else None
                ),
                "dietician_additional_appointment_offered": (
                    row[
                        "Was the patient offered an additional appointment with a paediatric dietitian?"
                    ]
                    if not pd.isnull(
                        row[
                            "Was the patient offered an additional appointment with a paediatric dietitian?"
                        ]
                    )
                    else None
                ),
                "dietician_additional_appointment_date": (
                    row["Date of additional appointment with dietitian"]
                    if not pd.isnull(
                        row["Date of additional appointment with dietitian"]
                    )
                    else None
                ),
                "ketone_meter_training": (
                    row[
                        "Was the patient using (or trained to use) blood ketone testing equipment at time of visit?"
                    ]
                    if not pd.isnull(
                        row[
                            "Was the patient using (or trained to use) blood ketone testing equipment at time of visit?"
                        ]
                    )
                    else None
                ),
                "flu_immunisation_recommended_date": (
                    row["Date that influenza immunisation was recommended"]
                    if not pd.isnull(
                        row["Date that influenza immunisation was recommended"]
                    )
                    else None
                ),
                "sick_day_rules_training_date": (
                    row[
                        "Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia"
                    ]
                    if not pd.isnull(
                        row[
                            "Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia"
                        ]
                    )
                    else None
                ),
                "hospital_admission_date": (
                    row["Start date (Hospital Provider Spell)"]
                    if not pd.isnull(row["Start date (Hospital Provider Spell)"])
                    else None
                ),
                "hospital_discharge_date": (
                    row["Discharge date (Hospital provider spell)"]
                    if not pd.isnull(row["Discharge date (Hospital provider spell)"])
                    else None
                ),
                "hospital_admission_reason": (
                    row["Reason for admission"]
                    if not pd.isnull(row["Reason for admission"])
                    else None
                ),
                "dka_additional_therapies": (
                    row[
                        "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?"
                    ]
                    if not pd.isnull(
                        row[
                            "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?"
                        ]
                    )
                    else None
                ),
                "hospital_admission_other": row[
                    "Only complete if OTHER selected: Reason for admission (free text)"
                ],
                "is_valid": visit_is_valid,
                "errors": (visit_errors if visit_errors is not None else None),
            }
            Visit.objects.create(**obj)
        except Exception as error:
            # called if database error or similar and database could not save instances.
            # Otherwise data, even if invalid, is saved
            return {"status": 422, "errors": f"Could not save visit {obj}: {error}"}

        AuditCohort.objects.update_or_create(
            patient=patient,
            pz_code=pdu_pz_code,
            ods_code=organisation_ods_code,
            defaults={
                "submission_active": False,
                "submission_date": timestamp,
                "submission_by": user,
            },
        )

        return {"status": 200, "errors": None}

        # save the results - validate  as you go within the save_row function

    # by passing this in we can use the same timestamp for all records
    timestamp = timezone.now()

    try:
        dataframe.apply(lambda row: save_row(row, timestamp=timestamp), axis=1)
    except Exception as error:
        # There was an error saving one or more records - this is likely not a problem with the data passed in
        return {"status": 500, "errors": error}

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
    matching_patients_in_current_cohort = Patient.objects.filter(
        nhs_number__in=list(unique_nhs_numbers_no_spaces),
        audit_cohorts__submission_active=True,
        audit_cohorts__audit_year=date.today().year,
        audit_cohorts__cohort_number=retrieve_cohort_for_date(
            date_instance=date.today()
        ),
    ).count()

    summary = {
        "total_records": total_records,
        "number_unique_nhs_numbers": number_unique_nhs_numbers,
        "count_of_records_per_nhs_number": list(
            count_of_records_per_nhs_number.items()
        ),
        "matching_patients_in_current_cohort": matching_patients_in_current_cohort,
    }

    return summary
