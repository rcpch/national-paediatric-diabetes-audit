"""
CSV Heading Objects for NPDA dataset - supports both 2021 and 2026 datasets.
Maps CSV column headings to model fields with year-appropriate headings.
"""

UNIQUE_IDENTIFIER_ENGLAND = (
    {
        "heading": "NHS Number",
        "model_field": "nhs_number",
        "model": "Patient",
        "alternative_headings": ["NHSNumber"],
    },
)

UNIQUE_IDENTIFIER_JERSEY = (
    {
        "heading": "Unique Reference Number",
        "model_field": "unique_reference_number",
        "model": "Patient",
    },
)

CSV_HEADING_OBJECTS = (
    # patient
    {
        "heading": "Date of Birth",
        "model_field": "date_of_birth",
        "model": "Patient",
        "alternative_headings": ["DOB"],
    },
    {
        "heading": "Postcode of usual address",
        "model_field": "postcode",
        "model": "Patient",
    },
    {
        "heading": "Stated gender",
        "model_field": "sex",
        "model": "Patient",
    },
    {
        "heading": "Ethnic Category",
        "model_field": "ethnicity",
        "model": "Patient",
        # Deliberate typo to accomodate automatically generated Wythenshawe CSVs
        "alternative_headings": ["Ethnic cateogry"],
    },
    {
        "heading": "Diabetes Type",
        "model_field": "diabetes_type",
        "model": "Patient",
    },
    {
        "heading": "Date of Diabetes Diagnosis",
        "model_field": "diagnosis_date",
        "model": "Patient",
        "alternative_headings": ["Date of Diagnosis"],
    },
    {
        "heading": "Date of leaving service",
        "model_field": "date_leaving_service",
        "model": "Transfer",
    },
    {
        "heading": "Reason for leaving service",
        "model_field": "reason_leaving_service",
        "model": "Transfer",
    },
    {
        "heading": "Death Date",
        "model_field": "death_date",
        "model": "Patient",
        "alternative_headings": ["Effective Death Date"],
    },
    {
        "heading": "GP Practice Code",
        "model_field": "gp_practice_ods_code",
        "model": "Patient",
    },
    {
        "heading": "PDU Number",
        "model_field": "pdu",
        # Reference attached to Transfer in csv_upload
        # Transfer
    },
    # Visit
    {
        "heading": "Visit/Appointment Date",
        "model_field": "visit_date",
        "model": "Visit",
        "alternative_headings": ["Visit Date"],
    },
    {
        "heading": "Patient Height (cm)",
        "model_field": "height",
        "model": "Visit",
    },
    {
        "heading": "Patient Weight (kg)",
        "model_field": "weight",
        "model": "Visit",
    },
    {
        "heading": "Observation Date (Height and weight)",
        "model_field": "height_weight_observation_date",
        "model": "Visit",
    },
    {"heading": "Hba1c Value", "model_field": "hba1c", "model": "Visit"},
    {
        "heading": "HbA1c result format",
        "model_field": "hba1c_format",
        "model": "Visit",
        # Deliberate typo to accomodate the old NPDA CSV template
        "alternative_headings": ["HB1AC Result Format"],
    },
    {
        "heading": "Observation Date: Hba1c Value",
        "model_field": "hba1c_date",
        "model": "Visit",
    },
    {
        "heading": "Diabetes Treatment at time of Hba1c measurement",
        "model_field": "treatment",
        "model": "Visit",
        "alternative_headings": ["Diabetes Treatment at the time of HbA1c measurement"],
    },
    {
        "heading": "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?",
        "model_field": "closed_loop_system",
        "model": "Visit",
        "alternative_headings": [
            # Trailing bracket to accomodate automatically generated Wythenshawe CSVs
            "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this as part of a closed loop system?)"
        ],
    },
    {
        "heading": "At the time of HbA1c measurement, in addition to standard blood glucose monitoring (SBGM), was the patient using any other method of glucose monitoring?",
        "model_field": "glucose_monitoring",
        "model": "Visit",
        "alternative_headings": [
            "At the time of HbA1c measurement, was the patient using any other method of glucose monitoring?"
        ],
    },
    {
        "heading": "Systolic Blood Pressure",
        "model_field": "systolic_blood_pressure",
        "model": "Visit",
    },
    {
        "heading": "Diastolic Blood pressure",
        "model_field": "diastolic_blood_pressure",
        "model": "Visit",
    },
    {
        "heading": "Observation Date (Blood Pressure)",
        "model_field": "blood_pressure_observation_date",
        "model": "Visit",
    },
    {
        "heading": "Foot Assessment / Examination Date",
        "model_field": "foot_examination_observation_date",
        "model": "Visit",
        "alternative_headings": ["Foot Assessment/Examination Date"],
    },
    {
        "heading": "Retinal Screening date",
        "model_field": "retinal_screening_observation_date",
        "model": "Visit",
    },
    {
        "heading": "Retinal Screening Result",
        "model_field": "retinal_screening_result",
        "model": "Visit",
    },
    {
        "heading": "Urinary Albumin Level (ACR)",
        "model_field": "albumin_creatinine_ratio",
        "model": "Visit",
    },
    {
        "heading": "Observation Date: Urinary Albumin Level",
        "model_field": "albumin_creatinine_ratio_date",
        "model": "Visit",
    },
    {
        "heading": "Albuminuria Stage",
        "model_field": "albuminuria_stage",
        "model": "Visit",
    },
    {
        "heading": "Total Cholesterol Level (mmol/l)",
        "model_field": "total_cholesterol",
        "model": "Visit",
    },
    {
        "heading": "Observation Date: Total Cholesterol Level",
        "model_field": "total_cholesterol_date",
        "model": "Visit",
    },
    {
        "heading": "Observation Date: Thyroid Function",
        "model_field": "thyroid_function_date",
        "model": "Visit",
    },
    {
        "heading": "At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?",
        "model_field": "thyroid_treatment_status",
        "model": "Visit",
        "alternative_headings": [
            "At the time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?"
        ],
    },
    {
        "heading": "Observation Date: Coeliac Disease Screening",
        "model_field": "coeliac_screen_date",
        "model": "Visit",
    },
    {
        "heading": "Has the patient been recommended a Gluten-free diet?",
        "model_field": "gluten_free_diet",
        "model": "Visit",
        # sic from the old NPDA template (eugh non breaking spaces)
        "alternative_headings": [
            "Has the patient been\xa0recommended a Gluten-free\xa0diet?"
        ],
    },
    {
        "heading": "Observation Date - Psychological Screening Assessment",
        "model_field": "psychological_screening_assessment_date",
        "model": "Visit",
        # sic from the old NPDA template
        "alternative_headings": [
            "Observation Date -Psychological Assessment Screening"
        ],
    },
    {
        "heading": "Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?",
        "model_field": "psychological_additional_support_status",
        "model": "Visit",
    },
    {
        "heading": "Does the patient smoke?",
        "model_field": "smoking_status",
        "model": "Visit",
    },
    {
        "heading": "Date of offer of referral to smoking cessation service (if patient is a current smoker)",
        "model_field": "smoking_cessation_referral_date",
        "model": "Visit",
    },
    {
        "heading": "Date of Level 3 carbohydrate counting education received",
        "model_field": "carbohydrate_counting_level_three_education_date",
        "model": "Visit",
        "alternative_headings": [
            "Date Level 3 carbohydrate counting education received"
        ],
    },
    {
        "heading": "Was the patient offered an additional appointment with a paediatric dietitian?",
        "model_field": "dietician_additional_appointment_offered",
        "model": "Visit",
    },
    {
        "heading": "Date of additional appointment with dietitian",
        "model_field": "dietician_additional_appointment_date",
        "model": "Visit",
    },
    {
        "heading": "Was the patient using (or trained to use) blood ketone testing equipment at time of visit?",
        "model_field": "ketone_meter_training",
        "model": "Visit",
    },
    {
        "heading": "Date that influenza immunisation was recommended",
        "model_field": "flu_immunisation_recommended_date",
        "model": "Visit",
    },
    {
        "heading": "Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia",
        "model_field": "sick_day_rules_training_date",
        "model": "Visit",
        "alternative_headings": [
            # Missing spacing before brackets to accomodate automatically generated Wythenshawe CSVs
            "Date of provision of advice('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia"
        ],
    },
    {
        "heading": "Start date (Hospital Provider Spell)",
        "model_field": "hospital_admission_date",
        "model": "Visit",
    },
    {
        "heading": "Discharge date (Hospital provider spell)",
        "model_field": "hospital_discharge_date",
        "model": "Visit",
    },
    {
        "heading": "Reason for admission",
        "model_field": "hospital_admission_reason",
        "model": "Visit",
    },
    {
        "heading": "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
        "model_field": "dka_additional_therapies",
        "model": "Visit",
        "alternative_headings": [
            "During this DKA admission did the patient receive any of the following therapies?"
        ],
    },
    {
        "heading": "Only complete if OTHER selected: Reason for admission (free text)",
        "model_field": "hospital_admission_other",
        "model": "Visit",
    },
)

# Combined CSV heading objects (use for backward compatibility)
CSV_HEADING_OBJECTS_2021 = CSV_HEADING_OBJECTS

# Additional/changed headings for 2026+ dataset
CSV_HEADING_OBJECTS_2026_ADDITIONS = (
    # Changed headings (2026 versions)
    {
        "heading": "Sex assigned at birth",
        "model_field": "sex",
        "model": "Patient",
        "alternative_headings": ["Stated gender"],  # Accept old format too
    },
    # New fields for 2026
    {
        "heading": "Has the patient had a diagnosis of Attention Deficit Hyperactivity Disorder (ADHD) or Autism Spectrum Disorder (ASD)?",
        "model_field": "adhd_asd_diagnosis",
        "model": "Patient",
    },
    {
        "heading": "Does the patient have a diagnosis of a learning disability?",
        "model_field": "learning_disability",
        "model": "Patient",
    },
    {
        "heading": "Insulin regime at time of visit",
        "model_field": "insulin_regime",
        "model": "Visit",
    },
    {
        "heading": "Other (non-insulin) blood glucose lowering medication at time of visit",
        "model_field": "non_insulin_medication",
        "model": "Visit",
    },
    {
        "heading": "Has lifestyle and dietary modification been recommended to reduce blood glucose levels?",
        "model_field": "lifestyle_dietary_modification",
        "model": "Visit",
    },
    {
        "heading": "Was the patient using a continuous glucose monitor (CGM) at time of visit?",
        "model_field": "cgm_use",
        "model": "Visit",
    },
    {
        "heading": "Did the patient receive immunotherapy prior to or after the diagnosis of stage 3 Type 1 diabetes?",
        "model_field": "immunotherapy_received",
        "model": "Visit",
    },
    {
        "heading": "Date immunotherapy started",
        "model_field": "immunotherapy_date",
        "model": "Visit",
    },
    {
        "heading": "Does the patient smoke and/or vape",
        "model_field": "smoking_vaping_status",
        "model": "Visit",
        "alternative_headings": ["Does the patient smoke?"],  # Accept old format too
    },
    {
        "heading": "Date of offer of smoking cessation advice (if patient is a current smoker)",
        "model_field": "smoking_cessation_advice_date",
        "model": "Visit",
        "alternative_headings": [
            "Date of offer of referral to smoking cessation service (if patient is a current smoker)"
        ],
    },
    {
        "heading": "Date of Annual Psychological Screening Assessment",
        "model_field": "annual_psychological_assessment_date",
        "model": "Visit",
        "alternative_headings": [
            "Observation Date - Psychological Screening Assessment"
        ],
    },
    {
        "heading": "Following annual psychological screening, was the patient assessed as requiring additional psychological support outside of routine care?",
        "model_field": "psychological_additional_support_status",
        "model": "Visit",
        "alternative_headings": [
            "Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?"
        ],
    },
    {
        "heading": "Was the patient offered an additional appointment with a mental health professional as part of the diabetes MDT?",
        "model_field": "mental_health_appointment_offered",
        "model": "Visit",
    },
    {
        "heading": "Date of Level 3 carbohydrate counting education received",
        "model_field": "carbohydrate_counting_level_three_education_date",
        "model": "Visit",
        "alternative_headings": [
            "Date Level 3 carbohydrate counting education received"
        ],
    },
    {
        "heading": "Was the patient offered an additional appointment with a paediatric dietitian during the audit year?",
        "model_field": "dietician_additional_appointment_offered",
        "model": "Visit",
        "alternative_headings": [
            "Was the patient offered an additional appointment with a paediatric dietitian?"
        ],
    },
    {
        "heading": "Initial pH at admission",
        "model_field": "initial_ph_admission",
        "model": "Visit",
    },
    {
        "heading": "Initial Standard bicarbonate at admission (mmol/l)",
        "model_field": "initial_bicarbonate_admission",
        "model": "Visit",
    },
)

CSV_HEADING_OBJECTS_2026 = (
    # patient
    {
        "heading": "Date of Birth",
        "model_field": "date_of_birth",
        "model": "Patient",
        "alternative_headings": [],
    },
    {
        "heading": "Postcode of usual address",
        "model_field": "postcode",
        "model": "Patient",
        "alternative_headings": [],
    },
    {
        "heading": "Sex assigned at birth",
        "model_field": "sex",
        "model": "Patient",
        "alternative_headings": ["Sex assigned at birth†††"],
    },
    {
        "heading": "Ethnic Category",
        "model_field": "ethnicity",
        "model": "Patient",
        "alternative_headings": [],
    },
    {
        "heading": "Has the patient had a diagnosis of Attention Deficit Hyperactivity Disorder (ADHD) or Autism Spectrum Disorder (ASD)?",
        "model_field": "adhd_asd_diagnosis",
        "model": "Patient",
        "alternative_headings": [],
    },
    {
        "heading": "Does the patient have a diagnosis of a learning disability?",
        "model_field": "learning_disability",
        "model": "Patient",
        "alternative_headings": [
            "Does the patient have a diagnosis of a learning disability?†"
        ],
    },
    {
        "heading": "Diabetes Type",
        "model_field": "diabetes_type",
        "model": "Patient",
        "alternative_headings": [],
    },
    {
        "heading": "Date of Diabetes Diagnosis",
        "model_field": "diagnosis_date",
        "model": "Patient",
        "alternative_headings": [],
    },
    {
        "heading": "Date of leaving service",
        "model_field": "date_leaving_service",
        "model": "Transfer",
        "alternative_headings": [],
    },
    {
        "heading": "Reason for leaving service",
        "model_field": "reason_leaving_service",
        "model": "Transfer",
        "alternative_headings": [],
    },
    {
        "heading": "Death Date",
        "model_field": "death_date",
        "model": "Patient",
        "alternative_headings": [],
    },
    {
        "heading": "GP Practice Code",
        "model_field": "gp_practice_ods_code",
        "model": "Patient",
        "alternative_headings": [],
    },
    {
        "heading": "PDU Number",
        "model_field": "pdu",
        #    Reference attached to Transfer in csv_upload
    },
    # Visit
    {
        "heading": "Visit/Appointment Date",
        "model_field": "visit_date",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Patient Height (cm)",
        "model_field": "height",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Patient Weight (kg)",
        "model_field": "weight",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Observation Date (Height and weight)",
        "model_field": "height_weight_observation_date",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Hba1c Value",
        "model_field": "hba1c",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Observation Date: HbA1c Value",
        "model_field": "hba1c_date",
        "model": "Visit",
        "alternative_headings": ["Observation Date: HbA1c Value†"],
    },
    {
        "heading": "Insulin regime at time of visit",
        "model_field": "insulin_regimen",
        "model": "Visit",
        "alternative_headings": ["Insulin regime at time of visit†"],
    },
    {
        "heading": "Other (non-insulin) blood glucose lowering medication at time of visit",
        "model_field": "non_insulin_medication",
        "model": "Visit",
        "alternative_headings": [
            "Other (non-insulin) blood glucose lowering medication at time of visit†"
        ],
    },
    {
        "heading": "Has lifestyle and dietary modification been recommended to reduce blood glucose levels?",
        "model_field": "dietary_lifestyle_modification",
        "model": "Visit",
        "alternative_headings": [
            "Has lifestyle and dietary modification been recommended to reduce blood glucose levels?†"
        ],
    },
    {
        "heading": "Was the patient using a continuous glucose monitor (CGM) at time of visit?",
        "model_field": "cgm_use",
        "model": "Visit",
        "alternative_headings": [
            "Was the patient using a continuous glucose monitor (CGM) at time of visit?†"
        ],
    },
    {
        "heading": "Was the patient using (or trained to use) blood ketone testing equipment at time of visit?",
        "model_field": "ketone_meter_training",
        "model": "Visit",
        "alternative_headings": [
            "Was the patient using (or trained to use) blood ketone testing equipment at time of visit?††"
        ],
    },
    {
        "heading": "Did the patient receive immunotherapy prior to or after the diagnosis of stage 3 Type 1 diabetes?",
        "model_field": "immunotherapy_received",
        "model": "Visit",
        "alternative_headings": [
            "Did the patient receive immunotherapy prior to or after the diagnosis of stage 3 Type 1 diabetes?†"
        ],
    },
    {
        "heading": "Date immunotherapy started",
        "model_field": "immunotherapy_date",
        "model": "Visit",
        "alternative_headings": ["Date immunotherapy started†"],
    },
    {
        "heading": "Systolic Blood Pressure",
        "model_field": "systolic_blood_pressure",
        "model": "Visit",
        "alternative_headings": ["Systolic Blood Pressure††"],
    },
    {
        "heading": "Diastolic Blood pressure",
        "model_field": "diastolic_blood_pressure",
        "model": "Visit",
        "alternative_headings": ["Diastolic Blood pressure†"],
    },
    {
        "heading": "Observation Date (Blood Pressure)",
        "model_field": "blood_pressure_observation_date",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Foot Assessment / Examination Date",
        "model_field": "foot_examination_observation_date",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Retinal Screening date",
        "model_field": "retinal_screening_observation_date",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Retinal Screening Result",
        "model_field": "retinal_screening_result",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Urinary Albumin Level (ACR)",
        "model_field": "albumin_creatinine_ratio",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Observation Date: Urinary Albumin Level",
        "model_field": "albumin_creatinine_ratio_date",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Albuminuria Stage",
        "model_field": "albuminuria_stage",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Total Cholesterol Level (mmol/l)",
        "model_field": "total_cholesterol",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Observation Date: Total Cholesterol Level",
        "model_field": "total_cholesterol_date",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Observation Date: Thyroid Function",
        "model_field": "thyroid_function_date",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?",
        "model_field": "thyroid_treatment_status",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Observation Date: Coeliac Disease Screening",
        "model_field": "coeliac_screen_date",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Has the patient been recommended a Gluten-free diet?",
        "model_field": "gluten_free_diet",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Does the patient smoke and/or vape",
        "model_field": "smoking_vaping_status",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Date of offer of smoking cessation advice (if patient is a current smoker)",
        "model_field": "smoking_cessation_referral_date",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Date that influenza immunisation was recommended",
        "model_field": "flu_immunisation_recommended_date",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia",
        "model_field": "sick_day_rules_training_date",
        "model": "Visit",
        "alternative_headings": [
            "Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia††"
        ],
    },
    {
        "heading": "Date of Annual Psychological Screening Assessment",
        "model_field": "psychological_screening_assessment_date",
        "model": "Visit",
        "alternative_headings": ["Date of Annual Psychological Screening Assessment††"],
    },
    {
        "heading": "Following annual psychological screening, was the patient assessed as requiring additional psychological support outside of routine care?",
        "model_field": "psychological_additional_support_status",
        "model": "Visit",
        "alternative_headings": [
            "Following annual psychological screening, was the patient assessed as requiring additional psychological support outside of routine care?†"
        ],
    },
    {
        "heading": "Was the patient offered an additional appointment with a mental health professional as part of the diabetes MDT?",
        "model_field": "psychological_support_outcome",
        "model": "Visit",
        "alternative_headings": [
            "Was the patient offered an additional appointment with a mental health professional as part of the diabetes MDT?†"
        ],
    },
    {
        "heading": "Date of Level 3 carbohydrate counting education received",
        "model_field": "carbohydrate_counting_level_three_education_date",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Was the patient offered an additional appointment with a paediatric dietitian during the audit year?",
        "model_field": "dietician_additional_appointment_offered",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Date of additional appointment with dietitian",
        "model_field": "dietician_additional_appointment_date",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Start date (Hospital Provider Spell)",
        "model_field": "hospital_admission_date",
        "model": "",
        "alternative_headings": [],
    },
    {
        "heading": "Discharge date (Hospital provider spell)",
        "model_field": "hospital_discharge_date",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Reason for admission",
        "model_field": "hospital_admission_reason",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Only complete if OTHER selected: Reason for admission (free text)",
        "model_field": "hospital_admission_other",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
        "model_field": "dka_additional_therapies",
        "model": "Visit",
        "alternative_headings": [],
    },
    {
        "heading": "Initial pH at admission",
        "model_field": "blood_gas_ph",
        "model": "Visit",
        "alternative_headings": ["Initial pH at admission†"],
    },
    {
        "heading": "Initial Standard bicarbonate at admission (mmol/l)",
        "model_field": "blood_gas_bicarbonate",
        "model": "Visit",
        "alternative_headings": [],
    },
)


def get_csv_heading_objects(dataset_year=None):
    """
    Returns the appropriate CSV heading objects for the given dataset year.

    Args:
        dataset_year: The dataset year (e.g., 2021, 2026). If None, returns 2021 format.

    Returns:
        tuple: CSV heading objects appropriate for the dataset year
    """
    if dataset_year and dataset_year >= 2026:
        # Merge 2021 base with 2026 additions/changes
        # Create a dict to handle overrides
        headings_dict = {}

        # Add all 2021 headings
        for item in CSV_HEADING_OBJECTS_2021:
            headings_dict[item["model_field"]] = item

        # Override/add with 2026 versions
        for item in CSV_HEADING_OBJECTS_2026:
            headings_dict[item["model_field"]] = item

        return tuple(headings_dict.values())
    else:
        return CSV_HEADING_OBJECTS_2021


def csv_definition_for(model_field_or_column: str, dataset_year=None):
    """
    Returns the CSV definition for a given model field or column heading.

    Args:
        model_field_or_column: Model field name or CSV column heading
        dataset_year: The dataset year (e.g., 2021, 2026)

    Returns:
        dict: CSV heading definition object, or None if not found
    """
    match model_field_or_column:
        case "nhs_number" | "NHS Number":
            return UNIQUE_IDENTIFIER_ENGLAND[0]
        case "unique_reference_number" | "Unique Reference Number":
            return UNIQUE_IDENTIFIER_JERSEY[0]
        case _:
            csv_objects = get_csv_heading_objects_for_year_and_unique_identifier(
                dataset_year, unique_identifier="england"
            )
            for item in csv_objects:
                if item["model_field"] == model_field_or_column:
                    return item
                if item["heading"] == model_field_or_column:
                    return item
                # Check alternative headings
                if "alternative_headings" in item:
                    if model_field_or_column in item["alternative_headings"]:
                        return item
    return None


# Date field lists
ALL_DATES_2021 = [
    "Date of Birth",
    "Date of Diabetes Diagnosis",
    "Date of leaving service",
    "Death Date",
    "Visit/Appointment Date",
    "Observation Date (Height and weight)",
    "Observation Date: Hba1c Value",
    "Observation Date (Blood Pressure)",
    "Foot Assessment / Examination Date",
    "Retinal Screening date",
    "Observation Date: Urinary Albumin Level",
    "Observation Date: Total Cholesterol Level",
    "Observation Date: Thyroid Function",
    "Observation Date: Coeliac Disease Screening",
    "Observation Date - Psychological Screening Assessment",
    "Date of offer of referral to smoking cessation service (if patient is a current smoker)",
    "Date of Level 3 carbohydrate counting education received",
    "Date of additional appointment with dietitian",
    "Date that influenza immunisation was recommended",
    "Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia",
    "Start date (Hospital Provider Spell)",
    "Discharge date (Hospital provider spell)",
]

ALL_DATES_2026 = [
    "Date of Birth",
    "Date of Diabetes Diagnosis",
    "Date of leaving service",
    "Death Date",
    "Visit/Appointment Date",
    "Observation Date (Height and weight)",
    "Observation Date: Hba1c Value",
    "Observation Date (Blood Pressure)",
    "Foot Assessment / Examination Date",
    "Retinal Screening date",
    "Observation Date: Urinary Albumin Level",
    "Observation Date: Total Cholesterol Level",
    "Observation Date: Thyroid Function",
    "Observation Date: Coeliac Disease Screening",
    "Date of Annual Psychological Screening Assessment",
    "Date of offer of smoking cessation advice (if patient is a current smoker)",
    "Date of Level 3 carbohydrate counting education received",
    "Date of additional appointment with dietitian",
    "Date that influenza immunisation was recommended",
    "Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia",
    "Date immunotherapy started",
    "Start date (Hospital Provider Spell)",
    "Discharge date (Hospital provider spell)",
]

# For backward compatibility
ALL_DATES = ALL_DATES_2021


def get_all_dates(dataset_year=None):
    """Returns all date field headings for the given dataset year."""
    if dataset_year and dataset_year >= 2026:
        return ALL_DATES_2026
    return ALL_DATES_2021


# Visit date field mappings
ALL_VISIT_DATES_2021 = [
    ("visit_date", "Visit/Appointment Date"),
    ("height_weight_observation_date", "Observation Date (Height and weight)"),
    ("hba1c_date", "Observation Date: Hba1c Value"),
    ("blood_pressure_observation_date", "Observation Date (Blood Pressure)"),
    ("foot_examination_observation_date", "Foot Assessment / Examination Date"),
    ("retinal_screening_observation_date", "Retinal Screening date"),
    ("albumin_creatinine_ratio_date", "Observation Date: Urinary Albumin Level"),
    ("total_cholesterol_date", "Observation Date: Total Cholesterol Level"),
    ("thyroid_function_date", "Observation Date: Thyroid Function"),
    ("coeliac_screen_date", "Observation Date: Coeliac Disease Screening"),
    (
        "psychological_screening_assessment_date",
        "Observation Date - Psychological Screening Assessment",
    ),
    (
        "smoking_cessation_referral_date",
        "Date of offer of referral to smoking cessation service (if patient is a current smoker)",
    ),
    (
        "carbohydrate_counting_level_three_education_date",
        "Date Level 3 carbohydrate counting education received",
    ),
    (
        "dietician_additional_appointment_date",
        "Date of additional appointment with dietitian",
    ),
    (
        "flu_immunisation_recommended_date",
        "Date that influenza immunisation was recommended",
    ),
    (
        "sick_day_rules_training_date",
        "Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia",
    ),
    ("hospital_admission_date", "Start date (Hospital Provider Spell)"),
    ("hospital_discharge_date", "Discharge date (Hospital provider spell)"),
]

ALL_VISIT_DATES_2026 = [
    ("visit_date", "Visit/Appointment Date"),
    ("height_weight_observation_date", "Observation Date (Height and weight)"),
    ("hba1c_date", "Observation Date: Hba1c Value"),
    ("blood_pressure_observation_date", "Observation Date (Blood Pressure)"),
    ("foot_examination_observation_date", "Foot Assessment / Examination Date"),
    ("retinal_screening_observation_date", "Retinal Screening date"),
    ("albumin_creatinine_ratio_date", "Observation Date: Urinary Albumin Level"),
    ("total_cholesterol_date", "Observation Date: Total Cholesterol Level"),
    ("thyroid_function_date", "Observation Date: Thyroid Function"),
    ("coeliac_screen_date", "Observation Date: Coeliac Disease Screening"),
    (
        "annual_psychological_assessment_date",
        "Date of Annual Psychological Screening Assessment",
    ),
    (
        "smoking_cessation_advice_date",
        "Date of offer of smoking cessation advice (if patient is a current smoker)",
    ),
    (
        "carbohydrate_counting_level_three_education_date",
        "Date of Level 3 carbohydrate counting education received",
    ),
    (
        "dietician_additional_appointment_date",
        "Date of additional appointment with dietitian",
    ),
    (
        "flu_immunisation_recommended_date",
        "Date that influenza immunisation was recommended",
    ),
    (
        "sick_day_rules_training_date",
        "Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia",
    ),
    ("immunotherapy_date", "Date immunotherapy started"),
    ("hospital_admission_date", "Start date (Hospital Provider Spell)"),
    ("hospital_discharge_date", "Discharge date (Hospital provider spell)"),
]

# For backward compatibility
ALL_VISIT_DATES = ALL_VISIT_DATES_2021


def get_all_visit_dates(dataset_year=None):
    """Returns all visit date field mappings for the given dataset year."""
    if dataset_year and dataset_year >= 2026:
        return ALL_VISIT_DATES_2026
    return ALL_VISIT_DATES_2021


# CSV data types
JERSEY_CSV_DATA_TYPES = {"Unique Reference Number": "string"}

ENGLAND_CSV_DATA_TYPES = {
    "NHS Number": "string",
}

CSV_DATA_TYPES_MINUS_DATES = {
    "Postcode of usual address": "string",
    "Stated gender": "Int64",
    "Ethnic Category": "string",  # choices are all capital letters
    "Diabetes Type": "Int64",
    "Reason for leaving service": "Int64",
    "GP Practice Code": "string",
    "PDU Number": "string",
    "Patient Height (cm)": "float64",
    "Patient Weight (kg)": "float64",
    "Hba1c Value": "float64",
    "HbA1c result format": "Int64",
    "Diabetes Treatment at time of Hba1c measurement": "Int64",
    "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?": "Int64",
    "At the time of HbA1c measurement, in addition to standard blood glucose monitoring (SBGM), was the patient using any other method of glucose monitoring?": "Int64",
    "Systolic Blood Pressure": "Int64",
    "Diastolic Blood pressure": "Int64",
    "Retinal Screening Result": "Int64",
    "Urinary Albumin Level (ACR)": "float64",
    "Albuminuria Stage": "Int64",
    "Total Cholesterol Level (mmol/l)": "float64",
    "At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?": "Int64",
    "Has the patient been recommended a Gluten-free diet?": "Int64",
    "Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?": "Int64",
    "Does the patient smoke?": "Int64",
    "Was the patient offered an additional appointment with a paediatric dietitian?": "Int64",
    "Was the patient using (or trained to use) blood ketone testing equipment at time of visit?": "Int64",
    "Reason for admission": "Int64",
    "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?": "Int64",
    "Only complete if OTHER selected: Reason for admission (free text)": "string",
}

NONNULL_FIELDS = [
    "Date of Birth",
    "Diabetes Type",
    "PDU Number",
    "Visit/Appointment Date",
]


def get_csv_heading_objects_for_year_and_unique_identifier(
    dataset_year=2021, unique_identifier="england"
):
    """
    Returns the appropriate CSV heading objects for the given dataset year and unique identifier.

    Args:
        dataset_year: The dataset year (e.g., 2021, 2026). If None, returns 2021 format.
        unique_identifier: "england" or "jersey" to specify which unique identifier to include.

    Returns:
        tuple: CSV heading objects appropriate for the dataset year and unique identifier
    """
    csv_heading_objects = get_csv_heading_objects(dataset_year)

    if unique_identifier == "england":
        return UNIQUE_IDENTIFIER_ENGLAND + csv_heading_objects
    elif unique_identifier == "jersey":
        return UNIQUE_IDENTIFIER_JERSEY + csv_heading_objects
    else:
        raise ValueError("unique_identifier must be either 'england' or 'jersey'")
