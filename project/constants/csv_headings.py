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
        "data_type": "string",
        "dataset_years": [2021, 2026],
    },
)

UNIQUE_IDENTIFIER_JERSEY = (
    {
        "heading": "Unique Reference Number",
        "model_field": "unique_reference_number",
        "model": "Patient",
        "data_type": "string",
        "dataset_years": [2021, 2026],
    },
)

"""
Combined CSV data types for 2021 and 2026 datasets, with unique identifier fields included
"""

ALL_HEADINGS = [
    {
        "heading": "Date of Birth",
        "model_field": "date_of_birth",
        "model": "Patient",
        "alternative_headings": ["DOB"],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Postcode of usual address",
        "model_field": "postcode",
        "model": "Patient",
        "alternative_headings": [],
        "data_type": "string",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Sex assigned at birth",
        "model_field": "sex",
        "model": "Patient",
        "alternative_headings": ["Sex assigned at birth†††"],
        "data_type": "int64",
        "dataset_years": [2026],
    },
    {
        "heading": "Stated gender",
        "model_field": "sex",
        "model": "Patient",
        "data_type": "int64",
        "dataset_years": [2021],
    },
    {
        "heading": "Ethnic Category",
        "model_field": "ethnicity",
        "model": "Patient",
        # Deliberate typo to accomodate automatically generated Wythenshawe CSVs
        "alternative_headings": ["Ethnic cateogry"],
        "data_type": "string",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Diabetes Type",
        "model_field": "diabetes_type",
        "model": "Patient",
        "alternative_headings": [],
        "data_type": "int64",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Date of Diabetes Diagnosis",
        "model_field": "diagnosis_date",
        "model": "Patient",
        "alternative_headings": ["Date of Diagnosis"],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Did the patient receive immunotherapy prior to or after the diagnosis of stage 3 Type 1 diabetes?",
        "model_field": "immunotherapy_received",
        "model": "Patient",
        "alternative_headings": [
            "Did the patient receive immunotherapy prior to or after the diagnosis of stage 3 Type 1 diabetes?†"
        ],
        "data_type": "int64",
        "dataset_years": [2026],
    },
    {
        "heading": "Date immunotherapy started",
        "model_field": "immunotherapy_date",
        "model": "Patient",
        "alternative_headings": ["Date immunotherapy started†"],
        "data_type": "date",
        "dataset_years": [2026],
    },
    {
        "heading": "Date of leaving service",
        "model_field": "date_leaving_service",
        "model": "Transfer",
        "alternative_headings": [],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Reason for leaving service",
        "model_field": "reason_leaving_service",
        "model": "Transfer",
        "alternative_headings": [],
        "data_type": "int64",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Death Date",
        "model_field": "death_date",
        "model": "Patient",
        # "Effective Death Date" was the heading used in an early NPDA CSV template
        "alternative_headings": ["Effective Death Date"],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "GP Practice Code",
        "model_field": "gp_practice_ods_code",
        "model": "Patient",
        "alternative_headings": [],
        "data_type": "string",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Has the patient had a diagnosis of Attention Deficit Hyperactivity Disorder (ADHD) or Autism Spectrum Disorder (ASD)?",
        "model_field": "adhd_asd_status",
        "model": "Patient",
        "alternative_headings": [],
        "data_type": "int64",
        "dataset_years": [2026],
    },
    {
        "heading": "Does the patient have a diagnosis of a learning disability?",
        "model_field": "learning_disability_status",
        "model": "Patient",
        "alternative_headings": [
            "Does the patient have a diagnosis of a learning disability?†"
        ],
        "data_type": "int64",
        "dataset_years": [2026],
    },
    {
        "heading": "PDU Number",
        "model_field": "pdu",
        #    Reference attached to Transfer in csv_upload
        "data_type": "string",
        "dataset_years": [2021, 2026],
    },
    # Visit date field
    {
        "heading": "Visit/Appointment Date",
        "model_field": "visit_date",
        "model": "Visit",
        "alternative_headings": ["Visit Date"],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    # Physical measurement fields
    {
        "heading": "Patient Height (cm)",
        "model_field": "height",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "float64",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Patient Weight (kg)",
        "model_field": "weight",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "float64",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Observation Date (Height and weight)",
        "model_field": "height_weight_observation_date",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    # Hba1c fields
    {
        "heading": "Hba1c Value",
        "model_field": "hba1c",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "float64",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Observation Date: HbA1c Value",
        "model_field": "hba1c_date",
        "model": "Visit",
        "alternative_headings": [
            "Observation Date: HbA1c Value†",
            "Observation Date: Hba1c Value",
        ],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "HbA1c result format",
        "model_field": "hba1c_format",
        "model": "Visit",
        # Deliberate typo to accomodate the old NPDA CSV template
        "alternative_headings": ["HB1AC Result Format"],
        "data_type": "int64",
        "dataset_years": [2021],
    },
    # Treatment and monitoring fields
    {
        "heading": "Insulin regime at time of visit",
        "model_field": "insulin_regimen",
        "model": "Visit",
        "alternative_headings": ["Insulin regime at time of visit†"],
        "data_type": "int64",
        "dataset_years": [2026],
    },
    {
        "heading": "Other (non-insulin) blood glucose lowering medication at time of visit",
        "model_field": "non_insulin_medication",
        "model": "Visit",
        "alternative_headings": [
            "Other (non-insulin) blood glucose lowering medication at time of visit†"
        ],
        "data_type": "int64",
        "dataset_years": [2026],
    },
    {
        "heading": "Has lifestyle and dietary modification been recommended to reduce blood glucose levels?",
        "model_field": "dietary_lifestyle_modification",
        "model": "Visit",
        "alternative_headings": [
            "Has lifestyle and dietary modification been recommended to reduce blood glucose levels?†"
        ],
        "data_type": "int64",
        "dataset_years": [2026],
    },
    {
        "heading": "Diabetes Treatment at time of Hba1c measurement",
        "model_field": "treatment",
        "model": "Visit",
        "alternative_headings": ["Diabetes Treatment at the time of HbA1c measurement"],
        "data_type": "int64",
        "dataset_years": [2021],
    },
    {
        "heading": "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this part of a closed loop system?",
        "model_field": "closed_loop_system",
        "model": "Visit",
        "alternative_headings": [
            # Trailing bracket to accomodate automatically generated Wythenshawe CSVs
            "If treatment included insulin pump therapy (i.e. option 3 or 6 selected), was this as part of a closed loop system?)"
        ],
        "data_type": "int64",
        "dataset_years": [2021],
    },
    {
        "heading": "At the time of HbA1c measurement, in addition to standard blood glucose monitoring (SBGM), was the patient using any other method of glucose monitoring?",
        "model_field": "glucose_monitoring",
        "model": "Visit",
        "alternative_headings": [
            "At the time of HbA1c measurement, was the patient using any other method of glucose monitoring?"
        ],
        "data_type": "int64",
        "dataset_years": [2021],
    },
    {
        "heading": "Was the patient using a continuous glucose monitor (CGM) at time of visit?",
        "model_field": "cgm_use",
        "model": "Visit",
        "alternative_headings": [
            "Was the patient using a continuous glucose monitor (CGM) at time of visit?†"
        ],
        "data_type": "int64",
        "dataset_years": [2026],
    },
    # Blood pressure fields
    {
        "heading": "Systolic Blood Pressure",
        "model_field": "systolic_blood_pressure",
        "model": "Visit",
        "data_type": "int64",
        "alternative_headings": ["Systolic Blood Pressure††"],
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Diastolic Blood pressure",
        "model_field": "diastolic_blood_pressure",
        "model": "Visit",
        "data_type": "int64",
        "alternative_headings": ["Diastolic Blood pressure†"],
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Observation Date (Blood Pressure)",
        "model_field": "blood_pressure_observation_date",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    # Foot examination fields
    {
        "heading": "Foot Assessment / Examination Date",
        "model_field": "foot_examination_observation_date",
        "model": "Visit",
        "alternative_headings": ["Foot Assessment/Examination Date"],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    # Retinal screening fields
    {
        "heading": "Retinal Screening date",
        "model_field": "retinal_screening_observation_date",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Retinal Screening Result",
        "model_field": "retinal_screening_result",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "int64",
        "dataset_years": [2021, 2026],
    },
    # Albuminuria fields
    {
        "heading": "Urinary Albumin Level (ACR)",
        "model_field": "albumin_creatinine_ratio",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "float64",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Observation Date: Urinary Albumin Level",
        "model_field": "albumin_creatinine_ratio_date",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Albuminuria Stage",
        "model_field": "albuminuria_stage",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "int64",
        "dataset_years": [2021, 2026],
    },
    # Cholesterol fields
    {
        "heading": "Total Cholesterol Level (mmol/l)",
        "model_field": "total_cholesterol",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "float64",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Observation Date: Total Cholesterol Level",
        "model_field": "total_cholesterol_date",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    # Thyroid function fields
    {
        "heading": "Observation Date: Thyroid Function",
        "model_field": "thyroid_function_date",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?",
        "model_field": "thyroid_treatment_status",
        "model": "Visit",
        "alternative_headings": [
            "At the time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?"
        ],
        "data_type": "int64",
        "dataset_years": [2021, 2026],
    },
    # Coeliac screening fields
    {
        "heading": "Observation Date: Coeliac Disease Screening",
        "model_field": "coeliac_screen_date",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Has the patient been recommended a Gluten-free diet?",
        "model_field": "gluten_free_diet",
        "model": "Visit",
        # sic from the old NPDA template (eugh non breaking spaces)
        "alternative_headings": [
            "Has the patient been\xa0recommended a Gluten-free\xa0diet?"
        ],
        "data_type": "int64",
        "dataset_years": [2021, 2026],
    },
    # Psychological screening fields
    # The official heading diverges between 2021 and 2026. Two separate entries (the same
    # pattern used for 'sex') ensure csv_parse normalises uploaded CSVs to the year-correct
    # canonical heading, and get_csv_heading_objects(year) returns the right one per year.
    {
        "heading": "Observation Date - Psychological Screening Assessment",
        "model_field": "psychological_screening_assessment_date",
        "model": "Visit",
        # sic from the old NPDA template
        "alternative_headings": [
            "Observation Date -Psychological Assessment Screening",
        ],
        "data_type": "date",
        "dataset_years": [2021],
    },
    {
        # Duplicate model_field — intentional: 2026 heading diverges from 2021.
        # get_csv_heading_objects deduplicates by model_field, so each year gets its own canonical.
        "heading": "Date of Annual Psychological Screening Assessment",
        "model_field": "psychological_screening_assessment_date",
        "model": "Visit",
        "alternative_headings": [
            "Date of Annual Psychological Screening Assessment††",  # dagger variant in 2026 template
        ],
        "data_type": "date",
        "dataset_years": [2026],
    },
    # The official heading diverges between 2021 and 2026. Two separate entries ensure
    # get_csv_heading_objects returns the year-correct canonical heading. See psychological_screening_assessment_date above.
    {
        "heading": "Was the patient assessed as requiring additional psychological/CAMHS support outside of MDT clinics?",
        "model_field": "psychological_additional_support_status",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "int64",
        "dataset_years": [2021],
    },
    {
        # Duplicate model_field — intentional: 2026 heading diverges from 2021.
        # get_csv_heading_objects deduplicates by model_field, so each year gets its own canonical.
        "heading": "Following annual psychological screening, was the patient assessed as requiring additional psychological support outside of routine care?",
        "model_field": "psychological_additional_support_status",
        "model": "Visit",
        "alternative_headings": [
            "Following annual psychological screening, was the patient assessed as requiring additional psychological support outside of routine care?†",  # dagger variant in 2026 template
        ],
        "data_type": "int64",
        "dataset_years": [2026],
    },
    {
        "heading": "Was the patient offered an additional appointment with a mental health professional as part of the diabetes MDT?",
        "model_field": "psychological_support_outcome",
        "model": "Visit",
        "alternative_headings": [
            "Was the patient offered an additional appointment with a mental health professional as part of the diabetes MDT?†"
        ],
        "data_type": "int64",
        "dataset_years": [2026],
    },
    # Smoking cessation fields
    {
        "heading": "Does the patient smoke?",
        "model_field": "smoking_status",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "int64",
        "dataset_years": [2021],
    },
    {
        "heading": "Does the patient smoke and/or vape",
        "model_field": "smoking_vaping_status",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "int64",
        "dataset_years": [2026],
    },
    # The official heading diverges between 2021 and 2026. Two separate entries ensure
    # csv_parse normalises to the year-correct canonical heading. See psychological_screening_assessment_date above.
    {
        "heading": "Date of offer of referral to smoking cessation service (if patient is a current smoker)",
        "model_field": "smoking_cessation_referral_date",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "date",
        "dataset_years": [2021],
    },
    {
        # Duplicate model_field — intentional: 2026 heading diverges from 2021.
        # get_csv_heading_objects deduplicates by model_field, so each year gets its own canonical.
        "heading": "Date of offer of smoking cessation advice (if patient is a current smoker)",
        "model_field": "smoking_cessation_referral_date",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "date",
        "dataset_years": [2026],
    },
    # Level 3 carbohydrate counting education fields
    {
        "heading": "Date of Level 3 carbohydrate counting education received",
        "model_field": "carbohydrate_counting_level_three_education_date",
        "model": "Visit",
        "alternative_headings": [
            "Date Level 3 carbohydrate counting education received",
            "Date of Level 3 carbohydrate counting education received",
        ],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    # The official heading diverges between 2021 and 2026. Two separate entries ensure
    # get_csv_heading_objects returns the year-correct canonical heading. See psychological_screening_assessment_date above.
    {
        "heading": "Was the patient offered an additional appointment with a paediatric dietitian?",
        "model_field": "dietician_additional_appointment_offered",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "int64",
        "dataset_years": [2021],
    },
    {
        # Duplicate model_field — intentional: 2026 heading diverges from 2021.
        # get_csv_heading_objects deduplicates by model_field, so each year gets its own canonical.
        "heading": "Was the patient offered an additional appointment with a paediatric dietitian during the audit year?",
        "model_field": "dietician_additional_appointment_offered",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "int64",
        "dataset_years": [2026],
    },
    {
        "heading": "Date of additional appointment with dietitian",
        "model_field": "dietician_additional_appointment_date",
        "model": "Visit",
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    # Ketone meter training field
    {
        "heading": "Was the patient using (or trained to use) blood ketone testing equipment at time of visit?",
        "model_field": "ketone_meter_training",
        "model": "Visit",
        "alternative_headings": [
            "Was the patient using (or trained to use) blood ketone testing equipment at time of visit?††",
            "Was the patient using (or trained to use) blood ketone testing equipment at time of visit?��",
        ],
        "data_type": "int64",
        "dataset_years": [2021, 2026],
    },
    # Influenza immunisation recommendation field
    {
        "heading": "Date that influenza immunisation was recommended",
        "model_field": "flu_immunisation_recommended_date",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    # Sick-day rules training field
    {
        "heading": "Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia",
        "model_field": "sick_day_rules_training_date",
        "model": "Visit",
        "alternative_headings": [
            # Missing spacing before brackets to accomodate automatically generated Wythenshawe CSVs
            "Date of provision of advice('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia",
            "Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia††",
        ],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    # Hospital admission fields
    {
        "heading": "Start date (Hospital Provider Spell)",
        "model_field": "hospital_admission_date",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Discharge date (Hospital provider spell)",
        "model_field": "hospital_discharge_date",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "date",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Reason for admission",
        "model_field": "hospital_admission_reason",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "int64",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Only complete if OTHER selected: Reason for admission (free text)",
        "model_field": "hospital_admission_other",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "string",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Only complete if DKA selected in previous question: During this DKA admission did the patient receive any of the following therapies?",
        "model_field": "dka_additional_therapies",
        "model": "Visit",
        "alternative_headings": [
            "During this DKA admission did the patient receive any of the following therapies?"
        ],
        "data_type": "int64",
        "dataset_years": [2021, 2026],
    },
    {
        "heading": "Initial pH at admission",
        "model_field": "blood_gas_ph",
        "model": "Visit",
        "alternative_headings": ["Initial pH at admission†"],
        "data_type": "float64",
        "dataset_years": [2026],
    },
    {
        "heading": "Initial Standard bicarbonate at admission (mmol/l)",
        "model_field": "blood_gas_bicarbonate",
        "model": "Visit",
        "alternative_headings": [],
        "data_type": "float64",
        "dataset_years": [2026],
    },
]


def get_csv_heading_objects(dataset_year=2021):
    """
    Returns the appropriate CSV heading objects for the given dataset year.

    Args:
        dataset_year: The dataset year (e.g., 2021, 2026). If None, returns 2021 format.

    Returns:
        tuple: CSV heading objects appropriate for the dataset year
    """
    headings_dict = {}
    for item in ALL_HEADINGS:
        if dataset_year in item["dataset_years"]:
            headings_dict[item["model_field"]] = item
    return tuple(headings_dict.values())


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
            if dataset_year is not None:
                csv_objects = get_csv_heading_objects_for_year_and_unique_identifier(
                    dataset_year, unique_identifier="england"
                )
            else:
                csv_objects = ALL_HEADINGS
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
    "Date immunotherapy started",
    "Visit/Appointment Date",
    "Observation Date (Height and weight)",
    "Observation Date: HbA1c Value",
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
# These static lists are retained for backward compatibility (e.g. visit_filters.py).
# For new code prefer get_all_visit_dates(dataset_year), which derives from ALL_HEADINGS.
ALL_VISIT_DATES_2021 = [
    ("visit_date", "Visit/Appointment Date"),
    ("height_weight_observation_date", "Observation Date (Height and weight)"),
    ("hba1c_date", "Observation Date: HbA1c Value"),  # canonical capitalisation
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
    ("hospital_admission_date", "Start date (Hospital Provider Spell)"),
    ("hospital_discharge_date", "Discharge date (Hospital provider spell)"),
]

ALL_VISIT_DATES_2026 = [
    ("visit_date", "Visit/Appointment Date"),
    ("height_weight_observation_date", "Observation Date (Height and weight)"),
    ("hba1c_date", "Observation Date: HbA1c Value"),
    ("blood_pressure_observation_date", "Observation Date (Blood Pressure)"),
    ("foot_examination_observation_date", "Foot Assessment / Examination Date"),
    ("retinal_screening_observation_date", "Retinal Screening date"),
    ("albumin_creatinine_ratio_date", "Observation Date: Urinary Albumin Level"),
    ("total_cholesterol_date", "Observation Date: Total Cholesterol Level"),
    ("thyroid_function_date", "Observation Date: Thyroid Function"),
    ("coeliac_screen_date", "Observation Date: Coeliac Disease Screening"),
    (
        "psychological_screening_assessment_date",
        "Date of Annual Psychological Screening Assessment",
    ),
    (
        "smoking_cessation_referral_date",
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
    ("hospital_admission_date", "Start date (Hospital Provider Spell)"),
    ("hospital_discharge_date", "Discharge date (Hospital provider spell)"),
]

# For backward compatibility
ALL_VISIT_DATES = ALL_VISIT_DATES_2021


def get_all_visit_dates(dataset_year=None):
    """
    Returns all visit date field mappings for the given dataset year as (model_field, heading) tuples.
    Derived from ALL_HEADINGS — single source of truth. Defaults to 2021 if dataset_year is not supplied.
    """
    year = dataset_year if dataset_year is not None else 2021
    return [
        (obj["model_field"], obj["heading"])
        for obj in get_csv_heading_objects(year)
        if obj.get("data_type") == "date" and obj.get("model") == "Visit"
    ]


# CSV data types
JERSEY_CSV_DATA_TYPES = {"Unique Reference Number": "string"}

ENGLAND_CSV_DATA_TYPES = {
    "NHS Number": "string",
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
        unique_identifier: "england", "jersey", or "all" to specify which unique identifier to include.

    Returns:
        tuple: CSV heading objects appropriate for the dataset year and unique identifier
    """
    csv_heading_objects = get_csv_heading_objects(dataset_year)

    if unique_identifier == "england":
        return UNIQUE_IDENTIFIER_ENGLAND + csv_heading_objects
    elif unique_identifier == "jersey":
        return UNIQUE_IDENTIFIER_JERSEY + csv_heading_objects
    elif unique_identifier == "all":
        return (
            UNIQUE_IDENTIFIER_ENGLAND + UNIQUE_IDENTIFIER_JERSEY + csv_heading_objects
        )
    else:
        raise ValueError(
            "unique_identifier must be either 'england', 'jersey', or 'all'"
        )
