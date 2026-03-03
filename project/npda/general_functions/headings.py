"""
Field headings configuration for NPDA dataset across different years.
Maps model field names to their display headings from the official dataset documents.
"""

PATIENT_FIELD_HEADINGS_2021 = {
    # Patient Details / Information
    "nhs_number": "NHS Number",
    "date_of_birth": "Date of Birth",
    "postcode": "Postcode of usual address",
    "sex": "Stated gender",
    "ethnicity": "Ethnic Category",
    "diabetes_type": "Diabetes Type",
    "diagnosis_date": "Date of Diabetes Diagnosis",
    # "date_leaving_service": "Date of leaving service", # this is in the Transfer model
    # "reason_leaving_service": "Reason for leaving service", # this is in the Transfer model
    "death_date": "Death Date",
    "gp_practice_ods_code": "GP Practice Code",
    "gp_practice_postcode": "GP Practice Postcode",
    "pdu": "PDU Number",
}

# Field headings for 2021-2025 dataset (from 2021 guidance document)
VISIT_FIELD_HEADINGS_2021 = {
    "visit_date": "Visit/Appointment Date",
    # Routine Measurements
    "height": "Patient Height (cm)",
    "weight": "Patient Weight (kg)",
    "height_weight_observation_date": "Observation Date (Height and weight)",
    "hba1c": "Hba1c Value",
    "hba1c_format": "HbA1c result format",
    "hba1c_date": "Observation Date: Hba1c Value",
    "treatment": "Diabetes Treatment at time of Hba1c measurement",
    "closed_loop_system": "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?",
    "glucose_monitoring": "At the time of HbA1c measurement, in addition to standard blood glucose monitoring (SBGM), was the patient using any other method of glucose monitoring?",
    # Annual Review / Diagnosis
    "systolic_blood_pressure": "Systolic Blood Pressure",
    "diastolic_blood_pressure": "Diastolic Blood pressure",
    "blood_pressure_observation_date": "Observation Date (Blood Pressure)",
    "foot_examination_observation_date": "Foot Assessment/Examination Date",
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
    # Psychology
    "psychological_screening_assessment_date": "Observation Date - Psychological Screening Assessment",
    "psychological_additional_support_status": "Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?",
    # Lifestyle / Education
    "smoking_status": "Does the patient smoke?",
    "smoking_cessation_referral_date": "Date of offer of referral to smoking cessation service (if patient is a current smoker)",
    "carbohydrate_counting_level_three_education_date": "Date of Level 3 carbohydrate counting education received",
    "dietician_additional_appointment_offered": "Was the patient offered an additional appointment with a paediatric dietitian?",
    "dietician_additional_appointment_date": "Date of additional appointment with dietitian",
    "ketone_meter_training": "Was the patient using (or trained to use) blood ketone testing equipment at time of visit?",
    "flu_immunisation_recommended_date": "Date that Influenza immunisation was recommended",
    "sick_day_rules_training_date": "Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia",
    # In-patient Entry
    "hospital_admission_date": "Start date (Hospital Provider Spell)",
    "hospital_discharge_date": "Discharge date (Hospital provider spell)",
    "hospital_admission_reason": "Reason for admission",
    "dka_additional_therapies": "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
    "hospital_admission_other": "Only complete if OTHER selected: Reason for admission (free text)",
}

FIELD_HEADINGS_2021 = {**PATIENT_FIELD_HEADINGS_2021, **VISIT_FIELD_HEADINGS_2021}

# Field headings for 2026+ dataset (from 2026 guidance document)

PATIENT_FIELD_HEADINGS_2026 = {
    # Patient Details / Information
    "nhs_number": "NHS Number",
    "date_of_birth": "Date of Birth",
    "postcode": "Postcode of usual address",
    "sex": "Sex assigned at birth",
    "ethnicity": "Ethnic Category",
    "diabetes_type": "Diabetes Type",
    "diagnosis_date": "Date of Diabetes Diagnosis",
    # "date_leaving_service": "Date of leaving service", # this is in the Transfer model
    # "reason_leaving_service": "Reason for leaving service", # this is in the Transfer model
    "death_date": "Death Date",
    "gp_practice_ods_code": "GP Practice Code",
    "pdu": "PDU Number",
    "adhd_asd_status": "Has the patient had a diagnosis of Attention Deficit Hyperactivity Disorder (ADHD) or Autism Spectrum Disorder (ASD)?",
    "learning_disability_status": "Does the patient have a diagnosis of a learning disability?",
    "immunotherapy_received": "Did the patient receive immunotherapy prior to or after the diagnosis of stage 3 Type 1 diabetes?",
    "immunotherapy_date": "Date immunotherapy started",
}

VISIT_FIELD_HEADINGS_2026 = {
    "visit_date": "Visit/Appointment Date",
    # Routine Measurements
    "height": "Patient Height (cm)",
    "weight": "Patient Weight (kg)",
    "height_weight_observation_date": "Observation Date (Height and weight)",
    "hba1c": "Hba1c Value",
    "hba1c_date": "Observation Date: HbA1c Value",
    # Treatment/Monitoring
    "insulin_regimen": "Insulin regime at time of visit",
    "non_insulin_medication": "Other (non-insulin) blood glucose lowering medication at time of visit",
    "dietary_lifestyle_modification": "Has lifestyle and dietary modification been recommended to reduce blood glucose levels?",
    "cgm_use": "Was the patient using a continuous glucose monitor (CGM) at time of visit?",
    "ketone_meter_training": "Was the patient using (or trained to use) blood ketone testing equipment at time of visit?",
    # Annual Review - Health Checks
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
    # Annual Review - Psychology
    "psychological_screening_assessment_date": "Date of Annual Psychological Screening Assessment",
    "psychological_additional_support_status": "Following annual psychological screening, was the patient assessed as requiring additional psychological support outside of routine care?",
    "psychological_support_outcome": "Was the patient offered an additional appointment with a mental health professional as part of the diabetes MDT?",
    # Lifestyle / Education
    "smoking_vaping_status": "Does the patient smoke and/or vape",
    "smoking_cessation_referral_date": "Date of offer of smoking cessation advice (if patient is a current smoker)",
    "flu_immunisation_recommended_date": "Date that influenza immunisation was recommended",
    "sick_day_rules_training_date": "Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia",
    # Annual Review - Dietetics
    "carbohydrate_counting_level_three_education_date": "Date of Level 3 carbohydrate counting education received",
    "dietician_additional_appointment_offered": "Was the patient offered an additional appointment with a paediatric dietitian during the audit year?",
    "dietician_additional_appointment_date": "Date of additional appointment with dietitian",
    # Admissions/Inpatient Entry
    "hospital_admission_date": "Start date (Hospital Provider Spell)",
    "hospital_discharge_date": "Discharge date (Hospital provider spell)",
    "hospital_admission_reason": "Reason for admission",
    "hospital_admission_other": "Only complete if OTHER selected: Reason for admission (free text)",
    "dka_additional_therapies": "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
    "blood_gas_ph": "Initial pH at admission",
    "blood_gas_bicarbonate": "Initial Standard bicarbonate at admission (mmol/l)",
}

FIELD_HEADINGS_2026 = {**PATIENT_FIELD_HEADINGS_2026, **VISIT_FIELD_HEADINGS_2026}


def get_field_heading(field_name, dataset_year):
    """
    Returns the official heading for a field based on dataset year.
    Works for both Patient and Visit models.

    Args:
        field_name: Name of the field to get heading for
        dataset_year: The dataset year (e.g., 2021, 2026)

    Returns:
        str: The official heading for the field, or the field_name if not found

    Example:
        >>> get_field_heading('sex', 2021)
        'Stated gender'
        >>> get_field_heading('sex_assigned_at_birth', 2026)
        'Sex assigned at birth'
    """
    if dataset_year and dataset_year >= 2026:
        return FIELD_HEADINGS_2026.get(field_name, field_name)
    else:
        return FIELD_HEADINGS_2021.get(field_name, field_name)
