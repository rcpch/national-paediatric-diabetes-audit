import os
from django.apps import apps
from django.conf import settings
import pandas as pd
import nhs_number
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


def csv_upload(csv_file=None):
    """
    Processes standardised NPDA csv file and persists results in NPDA tables

    accepts CSV file with standardised column names

    return True if successful, False with error message if not
    """
    Patient = apps.get_model("npda", "Patient")
    Site = apps.get_model("npda", "Site")
    Visit = apps.get_model("npda", "Visit")
    PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")

    csv_file = os.path.join(
        settings.BASE_DIR, "project", "npda", "dummy_sheets", "dummy_sheet.csv"
    )

    try:
        dataframe = pd.read_csv(
            csv_file, parse_dates=ALL_DATES, dayfirst=True, date_format="%d/%m/%Y"
        )
    except ValueError as error:
        return {"result": False, "error": f"Invalid file: {error}"}

    def validate_row(row):
        """
        Validate each row

        Generates an array of error objects

        returns boolean (True if valid), None or array of error messages {'message': '[field name], [message]'}
        """
        # initialize errors array
        errors = []

        # get all the data for this row
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
        # Site validations
        date_leaving_service = row["Date of leaving service"]
        reason_leaving_service = row["Reason for leaving service"]
        # Visit validations
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
            {"field": date_of_birth, "name": "date of birth (YYYY-MM-DD)"},
            {"field": postcode, "name": "Postcode of usual address"},
            {"field": sex, "name": "Stated gender"},
            {"field": ethnicity, "name": "Ethnic Category"},
            {"field": diabetes_type, "name": "Diabetes Type"},
            {"field": gp_practice_ods_code, "name": "GP Practice Code"},
            {"field": diagnosis_date, "name": "Date of Diabetes Diagnosis"},
            {
                "field": visit_date,
                "name": "Visit/Appointment Date",
            },
        ]

        """
        Private methods
        """

        def create_error(list_item: str, allowed_list: list, field_text: str):
            """
            Creates error object from item, list and string text
            """
            if list_item in allowed_list:
                return False, None
            else:
                error = {
                    "message": f"{field_text} supplied invalid. Must supply one of {LEAVE_PDU_REASONS}"
                }
                return True, error

        def validate_date(
            date_under_examination_name,
            date_under_examination,
            date_of_birth,
            date_of_diagnosis,
            date_of_death=None,
        ):
            """
            Dates passed in are already validated as date objects
            This method validates the dates themselves
            """
            errors = []
            valid = True

            if date_under_examination is None:
                return valid, None

            if date_under_examination < date_of_birth:
                error = {
                    "message": f"'{date_under_examination_name}' cannot be before date of birth."
                }
                errors.append(error)
                valid = False

            if date_under_examination < date_of_diagnosis:
                error = {
                    "message": f"'{date_under_examination_name}' cannot be before date of diagnosis."
                }
                errors.append(error)
                valid = False

            if date_of_death is not None:
                if date_under_examination > date_of_death:
                    error = {
                        "message": f"'{date_under_examination_name}' cannot be after date of death."
                    }
                    errors.append(error)
                    valid = False

            return valid, errors

        lists_of_choices = [
            create_error(
                list_item=sex, allowed_list=SEX_TYPE, field_text="'Stated gender'"
            ),
            create_error(
                list_item=ethnicity,
                allowed_list=ETHNICITIES,
                field_text="'Ethnic Category'",
            ),
            create_error(
                list_item=diabetes_type,
                allowed_list=DIABETES_TYPES,
                field_text="'Diabetes Type'",
            ),
            create_error(
                list_item=reason_leaving_service,
                allowed_list=LEAVE_PDU_REASONS,
                field_text="'Reason for leaving service'",
            ),
            create_error(
                list_item=treatment,
                allowed_list=TREATMENT_TYPES,
                field_text="'Diabetes Treatment at time of Hba1c measurement'",
            ),
            create_error(
                list_item=closed_loop_system,
                allowed_list=CLOSED_LOOP_TYPES,
                field_text="'If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?'",
            ),
            create_error(
                list_item=glucose_monitoring,
                allowed_list=GLUCOSE_MONITORING_TYPES,
                field_text="'At the time of HbA1c measurement, in addition to standard blood glucose monitoring (SBGM), was the patient using any other method of glucose monitoring?'",
            ),
            create_error(
                list_item=hba1c_format,
                allowed_list=HBA1C_FORMATS,
                field_text="'HbA1c result format'",
            ),
            create_error(
                list_item=albuminuria_stage,
                allowed_list=ALBUMINURIA_STAGES,
                field_text="'Albuminuria Stage'",
            ),
            create_error(
                list_item=retinal_screening_result,
                allowed_list=RETINAL_SCREENING_RESULTS,
                field_text="'Provide a result for retinal screening only if screen performed. Abnormal is defined as any level of retinopathy in either eye.'",
            ),
            create_error(
                list_item=thyroid_treatment_status,
                allowed_list=THYROID_TREATMENT_STATUS,
                field_text="'At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?'",
            ),
            create_error(
                list_item=gluten_free_diet,
                allowed_list=YES_NO_UNKNOWN,
                field_text="'Has the patient been recommended a Gluten-free diet?'",
            ),
            create_error(
                list_item=psychological_additional_support_status,
                allowed_list=YES_NO_UNKNOWN,
                field_text="'Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?'",
            ),
            create_error(
                list_item=smoking_status,
                allowed_list=SMOKING_STATUS,
                field_text="'Does the patient smoke?'",
            ),
            create_error(
                list_item=dietician_additional_appointment_offered,
                allowed_list=YES_NO_UNKNOWN,
                field_text="'Was the patient offered an additional appointment with a paediatric dietitian?'",
            ),
            create_error(
                list_item=ketone_meter_training,
                allowed_list=YES_NO_UNKNOWN,
                field_text="'Was the patient using (or trained to use) blood ketone testing equipment at time of visit?'",
            ),
            create_error(
                list_item=hospital_admission_reason,
                allowed_list=HOSPITAL_ADMISSION_REASONS,
                field_text="'Reason for admission'",
            ),
            create_error(
                list_item=dka_additional_therapies,
                allowed_list=DKA_ADDITIONAL_THERAPIES,
                field_text="'Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?'",
            ),
        ]

        list_of_dates = [
            validate_date(
                date_under_examination_name="Date of leaving service",
                date_under_examination=date_leaving_service,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Visit/Appointment Date",
                date_under_examination=visit_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Observation Date (Height and weight)",
                date_under_examination=height_weight_observation_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Observation Date: Hba1c Value",
                date_under_examination=hba1c_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Observation Date (Blood Pressure)",
                date_under_examination=blood_pressure_observation_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Foot Assessment / Examination Date",
                date_under_examination=foot_examination_observation_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Retinal Screening date",
                date_under_examination=retinal_screening_observation_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Observation Date: Urinary Albumin Level",
                date_under_examination=albumin_creatinine_ratio_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Observation Date: Total Cholesterol Level",
                date_under_examination=total_cholesterol_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Observation Date: Thyroid Function",
                date_under_examination=thyroid_function_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Observation Date: Coeliac Disease Screening",
                date_under_examination=coeliac_screen_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Observation Date - Psychological Screening Assessment",
                date_under_examination=psychological_screening_assessment_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Date of offer of referral to smoking cessation service (if patient is a current smoker)",
                date_under_examination=smoking_cessation_referral_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Date of Level 3 carbohydrate counting education received",
                date_under_examination=carbohydrate_counting_level_three_education_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Date of additional appointment with dietitian",
                date_under_examination=dietician_additional_appointment_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Date that influenza immunisation was recommended",
                date_under_examination=flu_immunisation_recommended_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia",
                date_under_examination=sick_day_rules_training_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Start date (Hospital Provider Spell)",
                date_under_examination=hospital_admission_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
            validate_date(
                date_under_examination_name="Discharge date (Hospital provider spell)",
                date_under_examination=hospital_discharge_date,
                date_of_birth=date_of_birth,
                date_of_diagnosis=diagnosis_date,
                date_of_death=death_date,
            ),
        ]

        """
        Validation starts here
        """

        # validate mandatory fields
        for mandatory_field in mandatory_fields:
            if mandatory_field is None:
                errors.append(
                    {"message": f"'{mandatory_field['name']}' cannot be empty."}
                )

        # validate list items
        for list_item in lists_of_choices:
            valid, error = list_item
            if valid:
                pass
            else:
                errors.append(error)

        # validate dates
        for list_date in list_of_dates:
            valid, error_list = list_date
            if not valid:
                errors += error_list

        # remaining validations
        if nhs_number.is_valid(row_number):
            pass
        else:
            error = {"message": "NHS Number invalid."}
            errors.append(error)

        if validate_postcode(postcode=postcode):
            pass
        else:
            error = {"message": "Postcode invalid."}
            errors.append(error)

        if hasattr(practice_validation, "error"):
            error = {"message": f"GP ODS Code invalid. {practice_validation['error']}"}
            errors.append(error)

        if height is not None:
            if height < 50:
                error = {
                    "message": f"'Patient Height (cm)' invalid. Cannot be below 50cm."
                }
                errors.append(error)
            elif height > 250:
                error = {
                    "message": f"'Patient Height (cm)' invalid. Cannot be above 250cm."
                }
                errors.append(error)

        if weight is not None:
            if weight < 1:
                error = {
                    "message": f"'Patient Weight (kg)' invalid. Cannot be below 1kg."
                }
                errors.append(error)
            elif weight > 200:
                error = {
                    "message": f"'Patient Weight (kg)' invalid. Cannot be above 200kg."
                }
                errors.append(error)

        if hba1c is not None:
            if hba1c_format is None:
                error = {"message": f"'Hba1c Value' invalid. Must supply HbA1c format."}
                errors.append(error)
            elif hba1c_format == 1:
                # mmol/mol
                if hba1c < 20 or hba1c > 195:
                    error = {"message": f"'Hba1c Value' invalid. Out of range."}
                    errors.append(error)
            elif hba1c_format == 2:
                # %
                if hba1c < 3 or hba1c > 20:
                    error = {"message": f"'Hba1c Value' invalid. Out of range."}
                    errors.append(error)

        if systolic_blood_pressure is not None:
            if systolic_blood_pressure > 240 or systolic_blood_pressure < 80:
                error = {"message": f"'Systolic Blood Pressure' invalid. Out of range."}
                errors.append(error)

        if diastolic_blood_pressure is not None:
            if diastolic_blood_pressure < 20 or diastolic_blood_pressure > 120:
                error = {
                    "message": f"'Diastolic Blood pressure' invalid. Out of range."
                }
                errors.append(error)

        if albumin_creatinine_ratio is not None:
            if albumin_creatinine_ratio > 50 or albumin_creatinine_ratio < 0:
                error = {
                    "message": f"'Urinary Albumin Level (ACR)' invalid. Out of range."
                }
                errors.append(error)

        if total_cholesterol is not None:
            if total_cholesterol > 12 or total_cholesterol < 2:
                error = {
                    "message": f"'Total Cholesterol Level (mmol/l)' invalid. Out of range."
                }
                errors.append(error)

        if len(errors) > 0:
            return False, errors
        else:
            return True, None

    def save_row(row):
        """
        Save each row as a record
        """
        nhs_number = row["NHS Number"].replace(" ", "")
        try:
            patient, created = Patient.objects.get_or_create(
                nhs_number=nhs_number,
                date_of_birth=row["Date of Birth"],
                postcode=row["Postcode of usual address"],
                sex=row["Stated gender"],
                ethnicity=row["Ethnic Category"],
                diabetes_type=row["Diabetes Type"],
                diagnosis_date=row["Date of Diabetes Diagnosis"],
                death_date=(
                    row["Death Date"] if not pd.isnull(row["Death Date"]) else None
                ),
                gp_practice_ods_code=row["GP Practice Code"],
            )
        except Exception as error:
            raise Exception(f"Could not save patient: {error}")

        try:
            pdu = PaediatricDiabetesUnit.objects.get(pz_code=row["PDU Number"])
        except Exception as error:
            raise Exception(f"Could not find PDU: {error}")

        try:
            site, created = Site.objects.get_or_create(
                date_leaving_service=row["Date of leaving service"]
                if not pd.isnull(row["Date of leaving service"])
                else None,
                reason_leaving_service=row["Reason for leaving service"]
                if not pd.isnull(row["Reason for leaving service"])
                else None,
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
                "height_weight_observation_date": row[
                    "Observation Date (Height and weight)"
                ]
                if row["Observation Date (Height and weight)"] != " "
                else None,
                "hba1c": row["Hba1c Value"],
                "hba1c_format": row["HbA1c result format"],
                "hba1c_date": row["Observation Date: Hba1c Value"]
                if not pd.isnull(row["Observation Date: Hba1c Value"])
                else None,
                "treatment": row["Diabetes Treatment at time of Hba1c measurement"],
                "closed_loop_system": row[
                    "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?"
                ]
                if not pd.isnull(
                    row[
                        "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?"
                    ]
                )
                else None,
                "glucose_monitoring": row[
                    "At the time of HbA1c measurement, in addition to standard blood glucose monitoring (SBGM), was the patient using any other method of glucose monitoring?"
                ],
                "systolic_blood_pressure": row["Systolic Blood Pressure"],
                "diastolic_blood_pressure": row["Diastolic Blood pressure"],
                "blood_pressure_observation_date": row[
                    "Observation Date (Blood Pressure)"
                ]
                if not pd.isnull(row["Observation Date (Blood Pressure)"])
                else None,
                "foot_examination_observation_date": row[
                    "Foot Assessment / Examination Date"
                ]
                if not pd.isnull(row["Foot Assessment / Examination Date"])
                else None,
                "retinal_screening_observation_date": row["Retinal Screening date"]
                if not pd.isnull(row["Retinal Screening date"])
                else None,
                "retinal_screening_result": row["Retinal Screening Result"],
                "albumin_creatinine_ratio": row["Urinary Albumin Level (ACR)"],
                "albumin_creatinine_ratio_date": row[
                    "Observation Date: Urinary Albumin Level"
                ]
                if not pd.isnull(row["Observation Date: Urinary Albumin Level"])
                else None,
                "albuminuria_stage": row["Albuminuria Stage"],
                "total_cholesterol": row["Total Cholesterol Level (mmol/l)"],
                "total_cholesterol_date": row[
                    "Observation Date: Total Cholesterol Level"
                ]
                if not pd.isnull(row["Observation Date: Total Cholesterol Level"])
                else None,
                "thyroid_function_date": row["Observation Date: Thyroid Function"]
                if not pd.isnull(row["Observation Date: Thyroid Function"])
                else None,
                "thyroid_treatment_status": row[
                    "At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?"
                ]
                if not pd.isnull(
                    row[
                        "At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?"
                    ]
                )
                else None,
                "coeliac_screen_date": row[
                    "Observation Date: Coeliac Disease Screening"
                ]
                if not pd.isnull(row["Observation Date: Coeliac Disease Screening"])
                else None,
                "gluten_free_diet": row[
                    "Has the patient been recommended a Gluten-free diet?"
                ]
                if not pd.isnull(
                    row["Has the patient been recommended a Gluten-free diet?"]
                )
                else None,
                "psychological_screening_assessment_date": row[
                    "Observation Date - Psychological Screening Assessment"
                ]
                if not pd.isnull(
                    row["Observation Date - Psychological Screening Assessment"]
                )
                else None,
                "psychological_additional_support_status": row[
                    "Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?"
                ]
                if not pd.isnull(
                    row[
                        "Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?"
                    ]
                )
                else None,
                "smoking_status": row["Does the patient smoke?"]
                if not pd.isnull(row["Does the patient smoke?"])
                else None,
                "smoking_cessation_referral_date": row[
                    "Date of offer of referral to smoking cessation service (if patient is a current smoker)"
                ]
                if not pd.isnull(
                    row[
                        "Date of offer of referral to smoking cessation service (if patient is a current smoker)"
                    ]
                )
                else None,
                "carbohydrate_counting_level_three_education_date": row[
                    "Date of Level 3 carbohydrate counting education received"
                ]
                if not pd.isnull(
                    row["Date of Level 3 carbohydrate counting education received"]
                )
                else None,
                "dietician_additional_appointment_offered": row[
                    "Was the patient offered an additional appointment with a paediatric dietitian?"
                ]
                if not pd.isnull(
                    row[
                        "Was the patient offered an additional appointment with a paediatric dietitian?"
                    ]
                )
                else None,
                "dietician_additional_appointment_date": row[
                    "Date of additional appointment with dietitian"
                ]
                if not pd.isnull(row["Date of additional appointment with dietitian"])
                else None,
                "ketone_meter_training": row[
                    "Was the patient using (or trained to use) blood ketone testing equipment at time of visit?"
                ]
                if not pd.isnull(
                    row[
                        "Was the patient using (or trained to use) blood ketone testing equipment at time of visit?"
                    ]
                )
                else None,
                "flu_immunisation_recommended_date": row[
                    "Date that influenza immunisation was recommended"
                ]
                if not pd.isnull(
                    row["Date that influenza immunisation was recommended"]
                )
                else None,
                "sick_day_rules_training_date": row[
                    "Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia"
                ]
                if not pd.isnull(
                    row[
                        "Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia"
                    ]
                )
                else None,
                "hospital_admission_date": row["Start date (Hospital Provider Spell)"]
                if not pd.isnull(row["Start date (Hospital Provider Spell)"])
                else None,
                "hospital_discharge_date": row[
                    "Discharge date (Hospital provider spell)"
                ]
                if not pd.isnull(row["Discharge date (Hospital provider spell)"])
                else None,
                "hospital_admission_reason": row["Reason for admission"]
                if not pd.isnull(row["Reason for admission"])
                else None,
                "dka_additional_therapies": row[
                    "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?"
                ]
                if not pd.isnull(
                    row[
                        "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?"
                    ]
                )
                else None,
                "hospital_admission_other": row[
                    "Only complete if OTHER selected: Reason for admission (free text)"
                ],
            }
            visit = Visit.objects.get_or_create(**obj)
        except Exception as error:
            return {"status": 422, "errors": f"Could not save visit {obj}: {error}"}

        return {"status": 200, "errors": None}

    # validate the data
    errors = []
    for index, row in dataframe.iterrows():
        is_valid, error = validate_row(row)
        if not is_valid:
            errors += errors

    if len(errors) > 0:
        # There are errors in the user data - return a list of errors to the user and do not save any records
        return {"status": 422, "errors": errors}
    else:
        # no errors - save the results
        try:
            dataframe.apply(save_row, axis=1)
        except Exception as error:
            # There was an error saving one or more records - this is likely not a problem with the data passed in
            return {"status": 500, "errors": error}

        return {"status": 200, "errors": None}
