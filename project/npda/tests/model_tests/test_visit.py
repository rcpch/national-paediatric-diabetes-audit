"""
This file contains tests for the visit model.

Suggested tests for the Visit model:
- A visit can be created if all required fields are valid and the visit is associated with a valid patient.
- A visit cannot be created if any required fields are invalid.
- A visit cannot be created if the visit is associated with an invalid patient or no patient.
- A visit cannot be created if the visit date is in the future.
- A visit cannot be created if the visit date is before the patient's date of diagnosis.
- A visit cannot be created if the visit date is before the patient's date of birth.
- A visit cannot be created if the visit date is after the patient's death date.
- A visit cannot be created if the visit date is not supplied or is in the wrong format.
- A visit cannot be created if a height is supplied and is not a positive number.
- A visit cannot be created if a height is supplied and is not in cm.
- A visit cannot be created if a height is supplied and is not in the correct format (ie a number).
- A visit cannot be created if a weight is supplied and is not a positive number.
- A visit cannot be created if a weight is supplied and is not in kg.
- A visit cannot be created if a weight is supplied and is not in the correct format (ie a number).
- A visit can be created if a height is supplied and a valid height_weight_date is supplied, and a visit date is supplied.
- A visit can be created if a height is supplied but not height_weight_date but an error is stored in the errors field.
- A visit cannot be created if a height is supplied but not height_weight_date and an error is not stored in the errors field.
- A visit can be created if a weight is supplied and a valid height_weight_date is supplied, and a visit date is supplied.
- A visit can be created if a weight is supplied but not height_weight_date and an error is stored in the errors field.
- A visit cannot be created if a weight is supplied but not height_weight_date and no error is stored in the errors field.
- A visit can be created if a height_weight_date is supplied but not a height or a weight but an error is stored in the errors field.
- A visit cannot be created if a height_weight_date is supplied but not a height or a weight and an error is not stored in the errors field.
- A visit cannot be created if a height_weight_date is supplied but not in the correct format.
- A visit cannot be created if a height_weight_date is supplied but in the future.
- A visit cannot be created if a height_weight_date is supplied but before the patient's date of birth.
- A visit cannot be created if a height_weight_date is supplied but after the patient's date of death.
- A visit can be created if a height_weight_date is supplied and is different to the visit date.
- A visit can be created if an hbA1c is supplied and is a valid number (must be positive).
- A visit cannot be created if an hbA1c is supplied but is not a number.
- A visit cannot be created if an hbA1c is supplied but an invalid or empty hba1c_format and an empty or invalid hba1c_date is also supplied.
- A visit can be created if an hbA1c is supplied and a valid hba1c_format and hba1c_date are also supplied.
- A visit cannot be created if a valid hba1c_format is supplied but no hba1c or hba1c_date.
- A visit cannot be created if a valid hba1c_date is supplied but no hba1c or hba1c_format.
- A visit cannot be created if an hba1c_date is supplied but not in the correct format.
- A visit cannot be created if an hba1c_date is supplied but in the future.
- A visit cannot be created if an hba1c_date is supplied but before the patient's date of birth.
- A visit cannot be created if an hba1c_date is supplied but after the patient's date of death.
- A visit can be created if the hba1c_format is supplied and in the correct format (a correct key) and the other hba1c fields are also supplied and valid.
- A visit cannot be created if the hba1c_format is supplied but not in the correct format (an incorrect key).
- A visit can be created if an hba1c_date is supplied and is different to the visit date.
- A visit can be created if a valid treatment is supplied (correct key).
- A visit cannot be created if an invalid treatment is supplied (incorrect key).
- A visit can be created if a valid closed_loop_system is supplied (correct key).
- A visit cannot be created if an invalid closed_loop_system is supplied (incorrect key).
- A visit can be created if a valid glucose_monitoring is supplied (correct key).
- A visit cannot be created if an invalid glucose_monitoring is supplied (incorrect key).
- A visit can be created if a valid systolic_blood_pressure is supplied (integer) and a blood_pressure_observation_date.
- A visit can be created if a valid systolic_blood_pressure is supplied (integer) and no blood_pressure_observation_date but an error is stored in the errors field.
- A visit cannot be created if a valid systolic_blood_pressure is supplied (integer) and no blood_pressure_observation_date but an error is NOT stored in the errors field.
- A visit can be created if a valid diastolic_blood_pressure is supplied (integer) and a blood_pressure_observation_date.
- A visit can be created if a valid diastolic_blood_pressure is supplied (integer) and no blood_pressure_observation_date but an error is stored in the errors field.
- A visit cannot be created if a valid diastolic_blood_pressure is supplied (integer) and no blood_pressure_observation_date but an error is NOT stored in the errors field.
- A visit can be created if a valid blood_pressure_observation_date is supplied and is different to the visit date.
- A visit cannot be created if a valid blood_pressure_observation_date is supplied but not in the correct format (a date).
- A visit cannot be created if a valid blood_pressure_observation_date is supplied but in the future.
- A visit cannot be created if a valid blood_pressure_observation_date is supplied but before the patient's date of birth.
- A visit cannot be created if a valid blood_pressure_observation_date is supplied but after the patient's date of death.
- A visit can be created if a valid foot_examination_observation_date is supplied and is different to the visit date.
- A visit cannot be created if a valid foot_examination_observation_date is supplied but not in the correct format (a date).
- A visit cannot be created if a valid foot_examination_observation_date is supplied but in the future.
- A visit cannot be created if a valid foot_examination_observation_date is supplied but before the patient's date of birth.
- A visit cannot be created if a valid foot_examination_observation_date is supplied but after the patient's date of death.
- A visit can be created if a valid retinal_screening_observation_date and a valid retinal_screening_result are supplied (correct key) and are different to the visit date.
- A visit cannot be created if a valid retinal_screening_observation_date is supplied but not in the correct format (a date).
- A visit cannot be created if a valid retinal_screening_observation_date is supplied but in the future.
- A visit cannot be created if a valid retinal_screening_observation_date is supplied but before the patient's date of birth.
- A visit cannot be created if a valid retinal_screening_observation_date is supplied but after the patient's date of death.
- A visit cannot be created if a valid retinal_screening_result is supplied but not in the correct format (an incorrect key).
- A visit can be created if a valid retinal_screening_result is supplied and is in the correct format (a correct key) and albuminuria_stage is supplied and in the correct format (correct key) but no date is supplied if an error is stored in the errors field.
- A visit can be created if a valid retinal_screening_result is supplied and is in the correct format (a correct key) and albuminuria_stage is NOT supplied and a valid date is supplied if an error is stored in the errors field.
- A visit can be created if a valid retinal_screening_result is NOT supplied and albuminuria_stage is and is in the correct format (a correct key) and a valid date is supplied if an error is stored in the errors field.
- A visit cannot be created if a valid retinal_screening_result is supplied and is in the correct format (a correct key) and albuminuria_stage is supplied and in the correct format (correct key) but no date is supplied if an error is NOT stored in the errors field.
- A visit can be created if a valid albumin_creatinine_ratio is supplied (decimal) and an albumin_creatinine_ratio_date.
- A visit can be created if a valid albumin_creatinine_ratio is supplied (decimal) and no albumin_creatinine_ratio_date but an error is stored in the errors field.
- A visit cannot be created if a valid albumin_creatinine_ratio is supplied (decimal) and no albumin_creatinine_ratio_date but an error is NOT stored in the errors field.
- A visit can be created if a valid albumin_creatinine_ratio_date is supplied and is different to the visit date.
- A visit cannot be created if a valid albumin_creatinine_ratio_date is supplied but not in the correct format (a date).
- A visit cannot be created if a valid albumin_creatinine_ratio_date is supplied but in the future.
- A visit cannot be created if a valid albumin_creatinine_ratio_date is supplied but before the patient's date of birth.
- A visit cannot be created if a valid albumin_creatinine_ratio_date is supplied but after the patient's date of death.
- A visit can be created if a valid total_cholesterol is supplied (integer) and a total_cholesterol_date.
- A visit can be created if a valid total_cholesterol is supplied (decimal) and no total_cholesterol_date but an error is stored in the errors field.
- A visit cannot be created if a valid total_cholesterol is supplied (decimal) and no total_cholesterol_date but an error is NOT stored in the errors field.
- A visit can be created if a valid total_cholesterol_date is supplied and is different to the visit date.
- A visit cannot be created if a valid total_cholesterol_date is supplied but not in the correct format (a date).
- A visit cannot be created if a valid total_cholesterol_date is supplied but in the future.
- A visit cannot be created if a valid total_cholesterol_date is supplied but before the patient's date of birth.
- A visit cannot be created if a valid total_cholesterol_date is supplied but after the patient's date of death.
- A visit can be created if a valid thyroid_function_date and a valid thyroid_treatment_status are supplied (correct key) and are different to the visit date.
- A visit cannot be created if a valid thyroid_function_date is supplied but not in the correct format (a date).
- A visit cannot be created if a valid thyroid_function_date is supplied but in the future.
- A visit cannot be created if a valid thyroid_function_date is supplied but before the patient's date of birth.
- A visit cannot be created if a valid thyroid_function_date is supplied but after the patient's date of death.
- A visit cannot be created if a valid thyroid_treatment_status is supplied but not in the correct format (an incorrect key).
- A visit can be created if a valid thyroid_treatment_status is supplied and is in the correct format (a correct key) but no date is supplied if an error is stored in the errors field.
- A visit cannot be created if a valid thyroid_treatment_status is supplied and is in the correct format (a correct key) but no date is supplied if an error is NOT stored in the errors field.
- A visit can be created if a valid coeliac_screen_date and a valid gluten_free_diet are supplied (correct key) and are different to the visit date.
- A visit cannot be created if a valid coeliac_screen_date is supplied but not in the correct format (a date).
- A visit cannot be created if a valid coeliac_screen_date is supplied but in the future.
- A visit cannot be created if a valid coeliac_screen_date is supplied but before the patient's date of birth.
- A visit cannot be created if a valid coeliac_screen_date is supplied but after the patient's date of death.
- A visit cannot be created if a valid gluten_free_diet is supplied but not in the correct format (an incorrect key).
- A visit can be created if a valid gluten_free_diet is supplied and is in the correct format (a correct key) but no date is supplied if an error is stored in the errors field.
- A visit cannot be created if a valid gluten_free_diet is supplied and is in the correct format (a correct key) but no date is supplied if an error is NOT stored in the errors field.
- A visit can be created if a valid psychological_screening_assessment_date and a valid psychological_additional_support_status are supplied (correct key) and are different to the visit date.
- A visit cannot be created if a valid psychological_screening_assessment_date is supplied but not in the correct format (a date).
- A visit cannot be created if a valid psychological_screening_assessment_date is supplied but in the future.
- A visit cannot be created if a valid psychological_screening_assessment_date is supplied but before the patient's date of birth.
- A visit cannot be created if a valid psychological_screening_assessment_date is supplied but after the patient's date of death.
- A visit cannot be created if a valid psychological_additional_support_status is supplied but not in the correct format (an incorrect key).
- A visit can be created if a valid psychological_additional_support_status is supplied and is in the correct format (a correct key) but no date is supplied if an error is stored in the errors field.
- A visit cannot be created if a valid psychological_additional_support_status is supplied and is in the correct format (a correct key) but no date is supplied if an error is NOT stored in the errors field.
- A visit can be created if a valid smoking_status is supplied (correct key) and a valid smoking_cessation_referral_date.
- A visit cannot be created if a valid smoking_status is supplied but not in the correct format (an incorrect key).
- A visit can be created if a valid smoking_cessation_referral_date is supplied and is different to the visit date.
- A visit cannot be created if a valid smoking_cessation_referral_date is supplied but not in the correct format (a date).
- A visit cannot be created if a valid smoking_cessation_referral_date is supplied but in the future.
- A visit cannot be created if a valid smoking_cessation_referral_date is supplied but before the patient's date of birth.
- A visit cannot be created if a valid smoking_cessation_referral_date is supplied but after the patient's date of death.
- A visit can be created if a valid smoking_cessation_referral_date is supplied and a valid smoking_status is supplied (correct key) but no date is supplied if an error is stored in the errors field.
- A visit cannot be created if a valid smoking_cessation_referral_date is supplied and a valid smoking_status is supplied (correct key) but no date is supplied if an error is NOT stored in the errors field.
- A vist can be created if a valid carbohydrate_counting_level_three_education_date is supplied.
- A visit cannot be created if a valid carbohydrate_counting_level_three_education_date is supplied but not in the correct format (a date).
- A visit cannot be created if a valid carbohydrate_counting_level_three_education_date is supplied but in the future.
- A visit cannot be created if a valid carbohydrate_counting_level_three_education_date is supplied but before the patient's date of birth.
- A visit cannot be created if a valid carbohydrate_counting_level_three_education_date is supplied but after the patient's date of death.
- A visit can be created if a valid carbohydrate_counting_level_three_education_date is supplied and is different to the visit date.
 - A visit can be created if a valid dietician_additional_appointment_offered is supplied (correct key) and a valid dietician_additional_appointment_date.
- A visit cannot be created if a valid dietician_additional_appointment_offered is supplied but not in the correct format (an incorrect key).
- A visit can be created if a valid dietician_additional_appointment_date is supplied and is different to the visit date.
- A visit cannot be created if a valid dietician_additional_appointment_date is supplied but not in the correct format (a date).
- A visit cannot be created if a valid dietician_additional_appointment_date is supplied but in the future.
- A visit cannot be created if a valid dietician_additional_appointment_date is supplied but before the patient's date of birth.
- A visit cannot be created if a valid dietician_additional_appointment_date is supplied but after the patient's date of death.
- A visit can be created if a valid dietician_additional_appointment_date is supplied and a valid dietician_additional_appointment_offered is supplied (correct key) but no date is supplied if an error is stored in the errors field.
- A visit cannot be created if a valid dietician_additional_appointment_date is supplied and a valid dietician_additional_appointment_offered is supplied (correct key) but no date is supplied if an error is NOT stored in the errors field.
- A visit can be created if a valid flu_immunisation_recommended_date is supplied.
- A visit cannot be created if a valid flu_immunisation_recommended_date is supplied but not in the correct format (a date).
- A visit cannot be created if a valid flu_immunisation_recommended_date is supplied but in the future.
- A visit cannot be created if a valid flu_immunisation_recommended_date is supplied but before the patient's date of birth.
- A visit cannot be created if a valid flu_immunisation_recommended_date is supplied but after the patient's date of death.
- A visit can be created if a valid flu_immunisation_recommended_date is supplied and is different to the visit date.
- A visit can be created if a valid ketone_meter_training entry is supplied (correct key).
- A visit cannot be created if an invalid ketone_meter_training entry is supplied (incorrect key).
- A visit can be created if a valid sick_day_rules_training_date is supplied.
- A visit cannot be created if a valid sick_day_rules_training_date is supplied but not in the correct format (a date).
- A visit cannot be created if a valid sick_day_rules_training_date is supplied but in the future.
- A visit cannot be created if a valid sick_day_rules_training_date is supplied but before the patient's date of birth.
- A visit cannot be created if a valid sick_day_rules_training_date is supplied but after the patient's date of death.
- A visit can be created if a valid sick_day_rules_training_date is supplied and is different to the visit date.
- A visit can be created if a valid hospital_admission_date and a valid hospital_admission_reason (correct key) and a valid hospital_admission_discharge_date are supplied.
- A visit cannot be created if a valid hospital_admission_date is supplied but not in the correct format (a date).
- A visit cannot be created if a valid hospital_admission_date is supplied but in the future.
- A visit cannot be created if a valid hospital_admission_date is supplied but before the patient's date of birth.
- A visit cannot be created if a valid hospital_admission_date is supplied but after the patient's date of death.
- A visit cannot be created if a valid hospital_admission_date is supplied but before the patient's date of diagnosis.
- A visit cannot be created if a hospital_admission_reason is supplied but not in the correct format (an incorrect key).
- A visit can be created if a valid hospital_admission_discharge_date is supplied and is different to the visit date.
- A visit cannot be created if a valid hospital_admission_discharge_date is supplied but not in the correct format (a date).
- A visit cannot be created if a valid hospital_admission_discharge_date is supplied but in the future.
- A visit cannot be created if a valid hospital_admission_discharge_date is supplied but before the patient's date of birth.
- A visit cannot be created if a valid hospital_admission_discharge_date is supplied but after the patient's date of death.
- A visit cannot be created if a valid hospital_admission_discharge_date is supplied but before the patient's date of diagnosis.
- A visit can be created if a valid hospital_admission_discharge_date is supplied and a valid hospital_admission_date is also supplied but no hospital_admission_reason if an error is stored in the errors field.
- A visit can be created if a valid hospital_admission_discharge_date is supplied and a valid hospital_admission_reason is also supplied but no hospital_admission_date if an error is stored in the errors field.
- A visit can be created if a valid hospital_admission_date is supplied and a valid hospital_admission_reason is also supplied but no hospital_admission_discharge_date if an error is stored in the errors field.
- A visit cannot be created if a valid hospital_admission_date is supplied but no hospital_admission_reason and no hospital_admission_discharge_date if an error is NOT stored in the errors field.
- A visit cannot be created if a valid hospital_admission_reason is supplied but no hospital_admission_date and no hospital_admission_discharge_date if an error is NOT stored in the errors field.
- A visit cannot be created if a valid hospital_admission_discharge_date is supplied but no hospital_admission_date and no hospital_admission_reason if an error is NOT stored in the errors field.
- A visit can be created if a valid hospital_admission_date is supplied and is different to the visit date.
- A visit can be created if a valid hospital_admission_reason is supplied and is in the correct format (a correct key).
- A visit can be created if a valid hospital_admission_discharge_date is supplied and is different to the visit date.
- A visit can be created if a valid dka_additional_therapies is supplied (correct key) and a value of 2 ('DKA') for hospital_admission_reason has been supplied.
- A visit cannot be created if an invalid dka_additional_therapies is supplied (incorrect key) and a value of 2 ('DKA') for hospital_admission_reason has been supplied.
- A visit cannot be created if a valid dka_additional_therapies is supplied (correct key) and a value of 2 ('DKA') for hospital_admission_reason has not been supplied if an error is NOT stored in the errors field. 
- A visit can be created if a a valid dka_additional_therapies is supplied (correct key) and a value of 2 ('DKA') for hospital_admission_reason has not been supplied if an error is stored in the errors field.
- A visit can be created if a valid hospital_admission_other is supplied and a value of 6 ('Other causes') for hospital_admission_reason has been supplied.
- A visit cannot be created if a valid hospital_admission_other is supplied and a value of 6 ('Other causes') for hospital_admission_reason has not been supplied if an error is NOT stored in the errors field.
- A visit can be created if a valid hospital_admission_other is supplied and a value of 6 ('Other causes') for hospital_admission_reason has not been supplied if an error is stored in the errors field.
- A visit can be created if a valid hospital_admission_other is supplied and is in the correct format (correct key).
- A visit can be created if a patient has a visit and a visit has a patient.
- A visit can be created if a patient has multiple visits.
- A visit cannot be created if it is associated with more than one patient.
"""
