---
title: API Endpoints
author: Dr Simon Chapman
---

This is not a replacement for the OpenAPI spec. 

| HTTP Method	| URL | Pattern	Action | Description |
| -- | -- | -- | -- |
| GET |	/patients/ | list | Get all patients |
| POST | /patients/	| create | Create new patient |
| GET |	/patients/{id}/	| retrieve | Get specific patient |
| PUT |	/patients/{id}/	| update | Full update of patient |
| PATCH |	/patients/{id}/ |	partial_update | Partial update of patient |
| GET |	/patients/{id}/visit | list | Get all visits for a given patient |
| POST |	/patients/{id}/visit | create | Create a visit for a given patient |
| GET |	/patients/{id}/visit/{id} | retrieve | Retrieve a visit for a given patient |
| PUT |	/patients/{id}/visit | update | Update a visit for a given patient |
| PATCH |	/patients/{id}/visit | partial update | Partial update of a visit for a given patient |

The patient id accepted is the NHS number of the patient (or the Unique Reference Number if from Jersey). The visit id is the individual visit id and would need to be persisted by the user for later use.

For example:

```console
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "visit_date": "2024-12-11",
    "height": "115.0",
    "weight": "34",
    "bmi": null,
    "height_weight_observation_date": "2024-12-11",
    "hba1c": null,
    "hba1c_format": null,
    "hba1c_date": null,
    "treatment": null,
    "closed_loop_system": null,
    "glucose_monitoring": null,
    "systolic_blood_pressure": null,
    "diastolic_blood_pressure": null,
    "blood_pressure_observation_date": null,
    "foot_examination_observation_date": null,
    "retinal_screening_observation_date": null,
    "retinal_screening_result": null,
    "albumin_creatinine_ratio": null,
    "albumin_creatinine_ratio_date": null,
    "albuminuria_stage": null,
    "total_cholesterol": null,
    "total_cholesterol_date": null,
    "thyroid_function_date": null,
    "thyroid_treatment_status": null,
    "coeliac_screen_date": null,
    "gluten_free_diet": null,
    "psychological_screening_assessment_date": null,
    "psychological_additional_support_status": null,
    "smoking_status": null,
    "smoking_cessation_referral_date": null,
    "carbohydrate_counting_level_three_education_date": null,
    "dietician_additional_appointment_offered": null,
    "dietician_additional_appointment_date": null,
    "flu_immunisation_recommended_date": null,
    "ketone_meter_training": null,
    "sick_day_rules_training_date": null,
    "hospital_admission_date": null,
    "hospital_discharge_date": null,
    "hospital_admission_reason": null,
    "dka_additional_therapies": null,
    "hospital_admission_other": null,
    "height_centile": "0.00",
    "weight_centile": null,
    "bmi_centile": null
  }' \
  http://npda.localhost/api/v1/patients/0339520329/visits/
  ```

  Would yield:

```json
[
    {
        "id": 801,
        "visit_date": "2024-11-11",
        "height": "115.0",
        "weight": null,
        "bmi": null,
        "height_weight_observation_date": "2024-11-11",
        "hba1c": null,
        "hba1c_format": null,
        "hba1c_date": null,
        "treatment": null,
        "closed_loop_system": null,
        "glucose_monitoring": null,
        "systolic_blood_pressure": null,
        "diastolic_blood_pressure": null,
        "blood_pressure_observation_date": null,
        "foot_examination_observation_date": null,
        "retinal_screening_observation_date": null,
        "retinal_screening_result": null,
        "albumin_creatinine_ratio": null,
        "albumin_creatinine_ratio_date": null,
        "albuminuria_stage": null,
        "total_cholesterol": null,
        "total_cholesterol_date": null,
        "thyroid_function_date": null,
        "thyroid_treatment_status": null,
        "coeliac_screen_date": null,
        "gluten_free_diet": null,
        "psychological_screening_assessment_date": null,
        "psychological_additional_support_status": null,
        "smoking_status": null,
        "smoking_cessation_referral_date": null,
        "carbohydrate_counting_level_three_education_date": null,
        "dietician_additional_appointment_offered": null,
        "dietician_additional_appointment_date": null,
        "flu_immunisation_recommended_date": null,
        "ketone_meter_training": null,
        "sick_day_rules_training_date": null,
        "hospital_admission_date": null,
        "hospital_discharge_date": null,
        "hospital_admission_reason": null,
        "dka_additional_therapies": null,
        "hospital_admission_other": null,
        "height_centile": "0.00",
        "weight_centile": null,
        "bmi_centile": null
    }
]
```

Note the `visit_id` is included and would need to be persisted for any subsequent `PATCH` or `PUT` requests to update the visit.

The OpenAPI specification can be viewed at: `{{baseurl}}/api/v1/schema/docs/`