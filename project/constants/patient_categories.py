PATIENT_CATEGORIES_2021 = [
    {
        "priority": 1,
        "name": "Patient Identifiers",
        "colour": "rcpch_yellow",
        "fields": ["nhs_number", "unique_reference_number", "date_of_birth"],
    },
    {
        "priority": 2,
        "name": "Demographics",
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
    {
        "priority": 4,
        "name": "Diagnosis",
        "colour": "rcpch_orange_light_tint1",
        "fields": [
            "diabetes_type",
            "diagnosis_date",
        ],
    },
    {
        "priority": 3,
        "name": "GP Information",
        "colour": "rcpch_aqua_green_light_tint1",
        "fields": ["gp_practice_ods_code", "gp_practice_postcode"],
    },
]

PATIENT_CATEGORIES_2026 = [
    {
        "priority": 1,
        "name": "Patient Identifiers",
        "colour": "rcpch_yellow",
        "fields": ["nhs_number", "unique_reference_number", "date_of_birth"],
    },
    {
        "priority": 2,
        "name": "Demographics",
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
    {
        "priority": 4,
        "name": "Diagnosis",
        "colour": "rcpch_orange_light_tint1",
        "fields": [
            "diabetes_type",
            "diagnosis_date",
            "immunotherapy_received",
            "immunotherapy_date",
        ],
    },
    {
        "priority": 3,
        "name": "GP Information",
        "colour": "rcpch_aqua_green_light_tint1",
        "fields": ["gp_practice_ods_code", "gp_practice_postcode"],
    },
    {
        "priority": 5,
        "name": "Neurodevelopmental Conditions",
        "colour": "rcpch_red_light_tint1",
        "fields": ["adhd_asd_status", "learning_disability_status"],
    },
]
