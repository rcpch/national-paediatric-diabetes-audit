# python imports
import os
import logging
from typing import Literal

# django imports
from django.apps import apps
from django.conf import settings

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

# Logging setup
logger = logging.getLogger(__name__)


def csv_upload(csv_file=None):
    """
    Processes standardised NPDA csv file and persists results in NPDA tables

    accepts CSV file with standardised column names

    return True if successful, False with error message if not
    """
    Patient = apps.get_model("npda", "Patient")
    Site = apps.get_model("npda", "Site")
    Visit = apps.get_model("npda", "Visit")
    # PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")

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
                "field": date_of_birth,
                "name": "date of birth (YYYY-MM-DD)",
                "model": "Patient",
            },
            {
                "field": postcode,
                "name": "Postcode of usual address",
                "model": "Patient",
            },
            {"field": sex, "name": "Stated gender", "model": "Patient"},
            {"field": ethnicity, "name": "Ethnic Category", "model": "Patient"},
            {"field": diabetes_type, "name": "Diabetes Type", "model": "Patient"},
            {
                "field": gp_practice_ods_code,
                "name": "GP Practice Code",
                "model": "Patient",
            },
            {
                "field": diagnosis_date,
                "name": "Date of Diabetes Diagnosis",
                "model": "Patient",
            },
            {"field": visit_date, "name": "Visit/Appointment Date", "model": "Visit"},
        ]

        """
        Private methods
        """

        def create_error(
            list_item: str,
            allowed_list: list,
            field_text: str,
            model: Literal["Patient", "Visit", "Site"],
        ):
            """
            Creates error object from item, list and string text
            """

            if list_item in allowed_list:
                # all items are valid, no errors
                return True, None, True, None
            else:
                error = {
                    "message": f"{field_text} supplied invalid. Must supply one of {allowed_list}"
                }
                if model == "Patient":
                    return False, error, True, None, True, None
                elif model == "Visit":
                    return True, None, False, error, True, None
                elif model == "Site":
                    return True, None, False, None, False, error

        def validate_date(
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
            patient_valid = True
            visit_errors = []
            visit_valid = True
            site_valid = True
            site_errors = []

            if date_under_examination is None:
                # empty dates are not validated - if they are mandatory, they are caught further down
                return (
                    patient_valid,
                    patient_errors,
                    visit_valid,
                    visit_errors,
                    site_valid,
                    site_errors,
                )

            if date_under_examination < date_of_birth:
                error = {
                    "message": f"'{date_under_examination_name}' cannot be before date of birth."
                }
                if field_parent_model == "Patient":
                    patient_errors.append(error)
                    patient_valid = False
                elif field_parent_model == "Visit":
                    visit_valid = False
                    visit_errors.append(error)
                elif field_parent_model == "Site":
                    site_valid = False
                    site_errors.append(error)

            if date_under_examination < date_of_diagnosis:
                error = {
                    "message": f"'{date_under_examination_name}' cannot be before date of diagnosis."
                }
                if field_parent_model == "Patient":
                    patient_errors.append(error)
                    patient_valid = False
                elif field_parent_model == "Visit":
                    visit_valid = False
                    visit_errors.append(error)
                elif field_parent_model == "Site":
                    site_valid = False
                    site_errors.append(error)

            if date_of_death is not None:
                if date_under_examination > date_of_death:
                    error = {
                        "message": f"'{date_under_examination_name}' cannot be after date of death."
                    }
                    # this is a patient field
                    patient_errors.append(error)
                    patient_valid = False

            return (
                patient_valid,
                patient_errors,
                visit_valid,
                visit_errors,
                site_valid,
                site_errors,
            )

        lists_of_choices = [
            create_error(
                list_item=sex,
                allowed_list=SEX_TYPE,
                field_text="'Stated gender'",
                model="Patient",
            ),
            create_error(
                list_item=ethnicity,
                allowed_list=ETHNICITIES,
                field_text="'Ethnic Category'",
                model="Patient",
            ),
            create_error(
                list_item=diabetes_type,
                allowed_list=DIABETES_TYPES,
                field_text="'Diabetes Type'",
                model="Patient",
            ),
            create_error(
                list_item=reason_leaving_service,
                allowed_list=LEAVE_PDU_REASONS,
                field_text="'Reason for leaving service'",
                model="Site",
            ),
            create_error(
                list_item=treatment,
                allowed_list=TREATMENT_TYPES,
                field_text="'Diabetes Treatment at time of Hba1c measurement'",
                model="Visit",
            ),
            create_error(
                list_item=closed_loop_system,
                allowed_list=CLOSED_LOOP_TYPES,
                field_text="'If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?'",
                model="Visit",
            ),
            create_error(
                list_item=glucose_monitoring,
                allowed_list=GLUCOSE_MONITORING_TYPES,
                field_text="'At the time of HbA1c measurement, in addition to standard blood glucose monitoring (SBGM), was the patient using any other method of glucose monitoring?'",
                model="Visit",
            ),
            create_error(
                list_item=hba1c_format,
                allowed_list=HBA1C_FORMATS,
                field_text="'HbA1c result format'",
                model="Visit",
            ),
            create_error(
                list_item=albuminuria_stage,
                allowed_list=ALBUMINURIA_STAGES,
                field_text="'Albuminuria Stage'",
                model="Visit",
            ),
            create_error(
                list_item=retinal_screening_result,
                allowed_list=RETINAL_SCREENING_RESULTS,
                field_text="'Provide a result for retinal screening only if screen performed. Abnormal is defined as any level of retinopathy in either eye.'",
                model="Visit",
            ),
            create_error(
                list_item=thyroid_treatment_status,
                allowed_list=THYROID_TREATMENT_STATUS,
                field_text="'At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?'",
                model="Visit",
            ),
            create_error(
                list_item=gluten_free_diet,
                allowed_list=YES_NO_UNKNOWN,
                field_text="'Has the patient been recommended a Gluten-free diet?'",
                model="Visit",
            ),
            create_error(
                list_item=psychological_additional_support_status,
                allowed_list=YES_NO_UNKNOWN,
                field_text="'Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?'",
                model="Visit",
            ),
            create_error(
                list_item=smoking_status,
                allowed_list=SMOKING_STATUS,
                field_text="'Does the patient smoke?'",
                model="Visit",
            ),
            create_error(
                list_item=dietician_additional_appointment_offered,
                allowed_list=YES_NO_UNKNOWN,
                field_text="'Was the patient offered an additional appointment with a paediatric dietitian?'",
                model="Visit",
            ),
            create_error(
                list_item=ketone_meter_training,
                allowed_list=YES_NO_UNKNOWN,
                field_text="'Was the patient using (or trained to use) blood ketone testing equipment at time of visit?'",
                model="Visit",
            ),
            create_error(
                list_item=hospital_admission_reason,
                allowed_list=HOSPITAL_ADMISSION_REASONS,
                field_text="'Reason for admission'",
                model="Visit",
            ),
            create_error(
                list_item=dka_additional_therapies,
                allowed_list=DKA_ADDITIONAL_THERAPIES,
                field_text="'Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?'",
                model="Visit",
            ),
        ]

        list_of_dates = [
            validate_date(
                date_under_examination_name="Date of leaving service",
                date_under_examination=date_leaving_service,
                field_parent_model="Site",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Visit/Appointment Date",
                date_under_examination=visit_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Observation Date (Height and weight)",
                date_under_examination=height_weight_observation_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Observation Date: Hba1c Value",
                date_under_examination=hba1c_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Observation Date (Blood Pressure)",
                date_under_examination=blood_pressure_observation_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Foot Assessment / Examination Date",
                date_under_examination=foot_examination_observation_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Retinal Screening date",
                date_under_examination=retinal_screening_observation_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Observation Date: Urinary Albumin Level",
                date_under_examination=albumin_creatinine_ratio_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Observation Date: Total Cholesterol Level",
                date_under_examination=total_cholesterol_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Observation Date: Thyroid Function",
                date_under_examination=thyroid_function_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Observation Date: Coeliac Disease Screening",
                date_under_examination=coeliac_screen_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Observation Date - Psychological Screening Assessment",
                date_under_examination=psychological_screening_assessment_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Date of offer of referral to smoking cessation service (if patient is a current smoker)",
                date_under_examination=smoking_cessation_referral_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Date of Level 3 carbohydrate counting education received",
                date_under_examination=carbohydrate_counting_level_three_education_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Date of additional appointment with dietitian",
                date_under_examination=dietician_additional_appointment_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Date that influenza immunisation was recommended",
                date_under_examination=flu_immunisation_recommended_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia",
                date_under_examination=sick_day_rules_training_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Start date (Hospital Provider Spell)",
                date_under_examination=hospital_admission_date,
                field_parent_model="Visit",
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
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
                        {"message": f"'{mandatory_field['name']}' cannot be empty."}
                    )
                elif mandatory_field["model"] == "Visit":
                    visit_errors.append(
                        {"message": f"'{mandatory_field['name']}' cannot be empty."}
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
                patient_valid,
                patient_error_list,
                visit_valid,
                visit_error_list,
                site_valid,
                site_error_list,
            ) = list_date

            if not patient_valid:
                patient_errors += patient_error_list
            elif not visit_valid:
                visit_errors += visit_error_list
            elif not site_valid:
                site_errors += site_error_list

        # remaining validations
        if nhs_number.is_valid(row_number):
            pass
        else:
            error = {"message": "NHS Number invalid."}
            patient_errors.append(error)

        if validate_postcode(postcode=postcode):
            pass
        else:
            error = {"message": "Postcode invalid."}
            patient_errors.append(error)

        if hasattr(practice_validation, "error"):
            error = {"message": f"GP ODS Code invalid. {practice_validation['error']}"}
            patient_errors.append(error)

        if height is not None:
            if height < 50:
                error = {
                    "message": f"'Patient Height (cm)' invalid. Cannot be below 50cm."
                }
                visit_errors.append(error)
            elif height > 250:
                error = {
                    "message": f"'Patient Height (cm)' invalid. Cannot be above 250cm."
                }
                visit_errors.append(error)

        if weight is not None:
            if weight < 1:
                error = {
                    "message": f"'Patient Weight (kg)' invalid. Cannot be below 1kg."
                }
                visit_errors.append(error)
            elif weight > 200:
                error = {
                    "message": f"'Patient Weight (kg)' invalid. Cannot be above 200kg."
                }
                visit_errors.append(error)

        if hba1c is not None:
            if hba1c_format is None:
                error = {"message": f"'Hba1c Value' invalid. Must supply HbA1c format."}
                visit_errors.append(error)
            elif hba1c_format == 1:
                # mmol/mol
                if hba1c < 20 or hba1c > 195:
                    error = {"message": f"'Hba1c Value' invalid. Out of range."}
                    visit_errors.append(error)
            elif hba1c_format == 2:
                # %
                if hba1c < 3 or hba1c > 20:
                    error = {"message": f"'Hba1c Value' invalid. Out of range."}
                    visit_errors.append(error)

        if systolic_blood_pressure is not None:
            if systolic_blood_pressure > 240 or systolic_blood_pressure < 80:
                error = {"message": f"'Systolic Blood Pressure' invalid. Out of range."}
                visit_errors.append(error)

        if diastolic_blood_pressure is not None:
            if diastolic_blood_pressure < 20 or diastolic_blood_pressure > 120:
                error = {
                    "message": f"'Diastolic Blood pressure' invalid. Out of range."
                }
                visit_errors.append(error)

        if albumin_creatinine_ratio is not None:
            if albumin_creatinine_ratio > 50 or albumin_creatinine_ratio < 0:
                error = {
                    "message": f"'Urinary Albumin Level (ACR)' invalid. Out of range."
                }
                visit_errors.append(error)

        if total_cholesterol is not None:
            if total_cholesterol > 12 or total_cholesterol < 2:
                error = {
                    "message": f"'Total Cholesterol Level (mmol/l)' invalid. Out of range."
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
    def save_row(row):
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

        nhs_number = row["NHS Number"].replace(" ", "")
        try:
            patient, created = Patient.objects.update_or_create(
                nhs_number=nhs_number,
                defaults={
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
                    "errors": patient_errors,
                },
            )
        except Exception as error:
            raise Exception(f"Could not save patient: {error}")

        # This is a temporizing step while we have no Organisations models available
        """
        try:
            pdu = PaediatricDiabetesUnit.objects.get(pz_code=row["PDU Number"])
        except Exception as error:
            raise Exception(f"Could not find PDU: {error}")
        """
        pdu = None

        try:
            site, created = Site.objects.get_or_create(
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
                pdu=pdu,
                patient=patient,
            )
        except Exception as error:
            raise Exception(f"Could not save site: {error}")

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
                "errors": visit_errors,
            }
            Visit.objects.update_or_create(**obj)
        except Exception as error:
            # called if database error or similar and database could not save instances.
            # Otherwise data, even if invalid, is saved
            return {"status": 422, "errors": f"Could not save visit {obj}: {error}"}

        return {"status": 200, "errors": None}

    # save the results - validate  as you go within the save_row function
    try:
        dataframe.apply(save_row, axis=1)
    except Exception as error:
        # There was an error saving one or more records - this is likely not a problem with the data passed in
        return {"status": 500, "errors": error}

    return {"status": 200, "errors": None}
