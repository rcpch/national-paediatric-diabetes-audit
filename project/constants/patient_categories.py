PATIENT_CATEGORIES_BY_TAB = {
    "Identifiers and Patient Details": {
        "Identifiers": {
            "colour": "rcpch_yellow",
            "fields": ["nhs_number", "unique_reference_number", "date_of_birth"],
        },
        "Demographics": {
            "colour": "rcpch_dark_grey",
            "fields": [
                "sex",
                "postcode",
                "location_wgs",
                "location_bng",
                "location_wgs84",
                "ethnicity",
                "index_of_multiple_deprivation_quintile",
                "death_date",
            ],
        },
    },
    "Diabetes Details": {
        "Diagnosis": {
            "colour": "rcpch_strong_green_light_tint1",
            "fields": [
                "diabetes_type",
                "diagnosis_date",
                "immunotherapy_received",
                "immunotherapy_date",
            ],
        },
    },
    "GP Details": {
        "GP Information": {
            "colour": "rcpch_aqua_green_light_tint1",
            "fields": ["gp_practice_ods_code", "gp_practice_postcode"],
        }
    },
    "Neurodevelopmental Conditions": {
        "Conditions": {
            "colour": "rcpch_orange_light_tint1",
            "fields": ["adhd_asd_status", "learning_disability_status"],
        }
    },
}
