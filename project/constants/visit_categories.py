VISIT_CATEGORIES_BY_TAB = {
    "Routine Measurements": {
        "Measurements": {
            "colour": "rcpch_yellow",
            "fields": [
                {"field": "height", "dataset_years": [2021, 2026]},
                {"field": "weight", "dataset_years": [2021, 2026]},
                {
                    "field": "height_weight_observation_date",
                    "dataset_years": [2021, 2026],
                },
            ],
        },
        "HBA1c": {
            "colour": "rcpch_dark_grey",
            "fields": [
                {"field": "hba1c", "dataset_years": [2021, 2026]},
                {"field": "hba1c_format", "dataset_years": [2021]},
                {"field": "hba1c_date", "dataset_years": [2021, 2026]},
            ],
        },
        "Treatment": {
            "colour": "rcpch_strong_green_light_tint1",
            "fields": [
                {"field": "treatment", "dataset_years": [2021]},
                {"field": "closed_loop_system", "dataset_years": [2021, 2026]},
                {"field": "insulin_regimen", "dataset_years": [2026]},
                {"field": "non_insulin_medication", "dataset_years": [2026]},
                {"field": "dietary_lifestyle_modification", "dataset_years": [2026]},
            ],
        },
        "CGM": {
            "colour": "rcpch_aqua_green_light_tint1",
            "fields": [
                {"field": "glucose_monitoring", "dataset_years": [2021]},
                {"field": "cgm_use", "dataset_years": [2026]},
            ],
        },
        "BP": {
            "colour": "rcpch_orange_light_tint1",
            "fields": [
                {"field": "systolic_blood_pressure", "dataset_years": [2021, 2026]},
                {"field": "diastolic_blood_pressure", "dataset_years": [2021, 2026]},
                {
                    "field": "blood_pressure_observation_date",
                    "dataset_years": [2021, 2026],
                },
            ],
        },
    },
    "Annual Review": {
        "Foot Care": {
            "colour": "rcpch_gold",
            "fields": [
                {
                    "field": "foot_examination_observation_date",
                    "dataset_years": [2021, 2026],
                },
            ],
        },
        "DECS": {
            "colour": "rcpch_vivid_green",
            "fields": [
                {
                    "field": "retinal_screening_observation_date",
                    "dataset_years": [2021, 2026],
                },
                {"field": "retinal_screening_result", "dataset_years": [2021, 2026]},
            ],
        },
        "ACR": {
            "colour": "rcpch_red_light_tint2",
            "fields": [
                {"field": "albumin_creatinine_ratio", "dataset_years": [2021, 2026]},
                {
                    "field": "albumin_creatinine_ratio_date",
                    "dataset_years": [2021, 2026],
                },
                {"field": "albuminuria_stage", "dataset_years": [2021, 2026]},
            ],
        },
        "Cholesterol": {
            "colour": "rcpch_orange_dark_tint",
            "fields": [
                {"field": "total_cholesterol", "dataset_years": [2021, 2026]},
                {"field": "total_cholesterol_date", "dataset_years": [2021, 2026]},
            ],
        },
        "Thyroid": {
            "colour": "rcpch_red_dark_tint",
            "fields": [
                {"field": "thyroid_function_date", "dataset_years": [2021, 2026]},
                {"field": "thyroid_treatment_status", "dataset_years": [2021, 2026]},
            ],
        },
        "Coeliac": {
            "colour": "rcpch_purple_light_tint2",
            "fields": [
                {"field": "coeliac_screen_date", "dataset_years": [2021, 2026]},
                {"field": "gluten_free_diet", "dataset_years": [2021, 2026]},
            ],
        },
        "Psychology": {
            "colour": "rcpch_yellow_dark_tint",
            "fields": [
                {
                    "field": "psychological_screening_assessment_date",
                    "dataset_years": [2021, 2026],
                },
                {
                    "field": "psychological_additional_support_status",
                    "dataset_years": [2021, 2026],
                },
                {"field": "psychological_support_outcome", "dataset_years": [2026]},
            ],
        },
        "Smoking": {
            "colour": "rcpch_strong_green_dark_tint",
            "fields": [
                {"field": "smoking_status", "dataset_years": [2021]},
                {"field": "smoking_vaping_status", "dataset_years": [2026]},
                {
                    "field": "smoking_cessation_referral_date",
                    "dataset_years": [2021, 2026],
                },
            ],
        },
        "Dietician": {
            "colour": "rcpch_aqua_green_dark_tint",
            "fields": [
                {
                    "field": "carbohydrate_counting_level_three_education_date",
                    "dataset_years": [2021, 2026],
                },
                {
                    "field": "dietician_additional_appointment_offered",
                    "dataset_years": [2021, 2026],
                },
                {
                    "field": "dietician_additional_appointment_date",
                    "dataset_years": [2021, 2026],
                },
            ],
        },
        "Sick Day Rules": {
            "colour": "rcpch_pink_light_tint2",
            "fields": [
                {"field": "ketone_meter_training", "dataset_years": [2021, 2026]},
                {
                    "field": "sick_day_rules_training_date",
                    "dataset_years": [2021, 2026],
                },
            ],
        },
        "Immunisation (flu)": {
            "colour": "rcpch_orange",
            "fields": [
                {
                    "field": "flu_immunisation_recommended_date",
                    "dataset_years": [2021, 2026],
                },
            ],
        },
    },
    "Inpatient Entry": {
        "Hospital Admission": {
            "colour": "rcpch_strong_green_dark_tint",
            "fields": [
                {"field": "hospital_admission_date", "dataset_years": [2021, 2026]},
                {"field": "hospital_discharge_date", "dataset_years": [2021, 2026]},
                {"field": "hospital_admission_reason", "dataset_years": [2021]},
                {"field": "hospital_admission_reason_2026", "dataset_years": [2026]},
                {"field": "dka_additional_therapies", "dataset_years": [2021, 2026]},
                {"field": "hospital_admission_other", "dataset_years": [2021, 2026]},
                {"field": "blood_gas_ph", "dataset_years": [2026]},
                {"field": "blood_gas_bicarbonate", "dataset_years": [2026]},
            ],
        }
    },
}
