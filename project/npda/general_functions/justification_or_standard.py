"""
Field configuration for NPDA dataset across different years.
Provides notes and justification/standard text for both Patient and Visit models.

Note: sex_assigned_at_birth field added in 2026 dataset and has been coerced into the sex field for consistency.
"""

# Field notes mapping for 2021-2025 dataset
FIELD_NOTES_2021 = {
    # Patient Details/Information
    "postcode": (
        "Enter the postcode in upper case and with a space in the correct place i.e. 'E13 0RJ'."
    ),
    "sex": (
        "'Not Specified' means indeterminate, i.e. the patient is unable to be classified as either male or female.\n\n"
        "'Unknown' means that the sex of the patient has not been recorded."
    ),
    "ethnicity": (
        "Ethnicity should be self-reported by the family.\n\n"
        "The Information Standards Board for Health and Social Care Dataset Change Notice (DSCN) 11/2008 states: "
        "\"the national code of 'Z- not stated' means that the person had been asked and had declined, either refusing "
        "to provide this information, or a genuine inability to choose, and should only be used in this circumstance "
        "and not to represent an unknown ethnicity.\n\n"
        "'Not Known' should be used where the patient had not been asked or the patient was not in a condition to be "
        "asked, e.g. unconscious. If the ethnic category is 'Not Known' use code 99.\n\n"
        "In some hospitals this information is collected at registration and recorded on your Patient Management System (PMS). "
        "Therefore, this data should be available to you."
    ),
    "diabetes_type": (
        "If you are unable to classify your patient into any of the categories 1-4:\n\n"
        "Use category 5 where there is a recognised cause of diabetes (e.g. post organ transplantation, steroid induced "
        "diabetes, post pancreatitis/pancreatectomy) or related to a syndrome (e.g. Prader Willi or Lawrence Moon Biedl Syndrome).\n\n"
        "Use code 99 when the patient has diabetes but the cause is unknown."
    ),
    "diagnosis_date": (
        "If you are unable to classify your patient's diagnosis date as they were diagnosed elsewhere and exact date cannot "
        "be ascertained, insert the first day in the month of diagnosis and year. E.g. diagnosed in March 2014, enter 01/03/2014."
    ),
    "date_leaving_service": (
        "Enter date if patient left the service during the audit year otherwise leave blank."
    ),
    "reason_leaving_service": (
        "Enter reason for leaving if patient has left your service during the audit year."
    ),
    "death_date": ("Mandatory if patient dies from any cause in audit year."),
    "gp_practice_ods_code": (
        "You can download GP Practice code data here:\n\n"
        "Once you have downloaded and opened the GP Practices full file (.csv) you will see that the GP Practice Codes are "
        "listed in Column A. You are able to search the Excel file by selecting Ctrl + F to search for Name, Address, Postcode "
        "etc. to look for the relevant GP Practice Code."
    ),
    "pdu": (
        "This is the number used on your NPDA registration form as in previous years (previously PZ XXX) and is on your NPDA "
        "log in. If you do not know your organisation code, please find it here on the NPDA website under 'NPDA PZ numbers list'."
    ),
    "visit_date": (
        "Defines a row of data by a visit date.\n\n"
        "N.B. the date of any care process or outcome measure within a row may not always be identical to the visit date."
    ),
    # Routine Measurements
    "height": (
        "At least one height/weight measurement should be recorded during the audit year.\n\n"
        "BMI will be calculated centrally.\n\n"
        "Combined observation date for height and weight. If only height or weight measured still enter date."
    ),
    "weight": (
        "At least one height/weight measurement should be recorded during the audit year.\n\n"
        "BMI will be calculated centrally.\n\n"
        "Combined observation date for height and weight. If only height or weight measured still enter date."
    ),
    "height_weight_observation_date": (
        "Combined observation date for height and weight. If only height or weight measured still enter date."
    ),
    "hba1c": (
        "Collect and submit ALL the measurements with dates taken throughout the audit cycle.\n\n"
        "Use a new row for each with visit date for each measurement.\n\n"
        "Values in either mmol/mol or % will be accepted."
    ),
    "hba1c_date": (
        "Date performed (within the audit year) is mandatory if observation value provided is to be accepted."
    ),
    "treatment": (
        "Enter the treatment at the time of the visit for all types of diabetes.\n\n"
        "Options 1-6 usually will relate to children and young people with Type 1 diabetes.\n\n"
        "Options 7-8 usually will relate to children and young people with non-Type 1 diabetes."
    ),
    "closed_loop_system": (
        "Leave blank if insulin pump not used at time of HbA1c measurement."
    ),
    "glucose_monitoring": (
        "Choose the modified flash glucose monitor option if the patient is using their flash monitor in combination with "
        "a separate device or app so that it functions as a continuous glucose monitor, with or without alarms.\n\n"
        "2023 update: The Flash Libre 2 system can now be considered a rtCGM if used with a smart phone. However, if the "
        "patient is using the reader and scanning, it will still be considered as a flash monitor. Please code according to "
        "how the system is being used by the patient."
    ),
    # Annual Review/Diagnosis
    "systolic_blood_pressure": (
        "Mandatory for Blood Pressure care process completion.\n\n"
        "Enter Systolic BP and Diastolic BP (if collected)\n\n"
        "Please use the methodology from the Diagnosis, Evaluation, and Treatment of High Blood Pressure in Children and "
        "Adolescents Report if performed."
    ),
    "diastolic_blood_pressure": (
        "Mandatory for Blood Pressure care process completion.\n\n"
        "Enter Systolic BP and Diastolic BP (if collected)\n\n"
        "Please use the methodology from the Diagnosis, Evaluation, and Treatment of High Blood Pressure in Children and "
        "Adolescents Report if performed."
    ),
    "blood_pressure_observation_date": (
        "Provide an observation date within the audit period. Date relates to both the systolic AND/OR diastolic pressure measurement."
    ),
    "foot_examination_observation_date": (
        "Complete only if screen performed.\n\n"
        "Mandatory care process if 12 years or older."
    ),
    "retinal_screening_observation_date": (
        "Complete only if screen performed.\n\n"
        "Mandatory care process if 12 years or older"
    ),
    "retinal_screening_result": (
        "Provide a result for retinal screening only if screen performed. Abnormal is defined as any level of retinopathy in either eye."
    ),
    "albumin_creatinine_ratio": (
        "Mandatory for children with type 1 diabetes aged 12 years and above and optional before 12 years.\n\n"
        "Mandatory for children with type 2 diabetes from diagnosis."
    ),
    "albumin_creatinine_ratio_date": (
        "Provide and observation date if a value provided."
    ),
    "albuminuria_stage": (
        "Submit your interpretation of the urinary albumin level based on your local laboratory reference ranges. "
        "Mandatory if level submitted."
    ),
    "total_cholesterol": (
        "Mandatory only for children with type 2 diabetes annually from diagnosis.\n\n"
        "Entry for patient with type 1 s is optional and will not be included as an essential care process but will be "
        "reported as an outcome measure. Report if performed."
    ),
    "total_cholesterol_date": ("Observation date mandatory if value provided."),
    "thyroid_function_date": (
        "This measure is for all children with type 1 diabetes annually.\n\n"
        "Mandatory to provide an observation date if performed."
    ),
    "thyroid_treatment_status": (
        "Mandatory if thyroid testing performed.\n\n"
        "Data for this item can be entered into the audit if prescribed at a video/telephone appointment."
    ),
    "coeliac_screen_date": (
        "Date of coeliac disease screening only to be completed if patient was diagnosed within audit year. Process complete "
        "if date is within 90 days of diagnosis for patient with Type 1 diabetes."
    ),
    "gluten_free_diet": (
        "Provide dietary status for all patients: A 'yes' response will be interpreted as the patient having a diagnosis of "
        "coeliac disease.\n\n"
        "Dietary status should be reported for every patient within each audit year to allow prevalence of coeliac disease to "
        "be calculated.\n\n"
        "Data for this item can be entered into the audit if a gluten-free diet was recommended at a video/telephone appointment."
    ),
    "psychological_screening_assessment_date": (
        "Enter a date that a formal assessment has taken place for the 'need of additional psychological support' (beyond that "
        "which might be routinely be provided within clinic). An assumption will be made that no assessment has taken place if "
        "no date entered.\n\n"
        "If a patient is already receiving additional support, but their assessment was in the previous audit year, please enter "
        "a date of one of their psychological therapy appointments within the current audit year.\n\n"
        "N.B this is a process measure, establishing whether the patient has been assessed for psychological distress.\n\n"
        "Data for this item can be entered into the audit if an assessment was performed remotely e.g. via video/telephone."
    ),
    "psychological_additional_support_status": (
        "Applicable if the patient was assessed as needing additional psychological support outside of routine clinical care "
        "provided by your PDU. If the patient is already receiving psychological support (including through CAMHS), record 'yes'.\n\n"
        "N.B. this is an outcome measure, following on from the process measure above (item 38), i.e. was the patient assessed "
        "as experiencing a level of psychological distress necessitating additional support (regardless of whether or not the "
        "patient has yet received support, and regardless of whether this distress is primarily related to their diabetes).\n\n"
        "Data for this item can be entered into the audit if determined following a remote assessment."
    ),
    "smoking_status": (
        "Enter smoking status of the patient.\n\n"
        "Data for this item can be entered into the audit if collected at a video/telephone appointment."
    ),
    "smoking_cessation_referral_date": (
        "Leave blank if not made.\n\n"
        "Data for this item can be entered into the audit if offered at a video/telephone appointment."
    ),
    "carbohydrate_counting_level_three_education_date": (
        "Level 3 carbohydrate counting is defined as carbohydrate counting with adjustment of insulin dosage according to an "
        "insulin:carbohydrate ratio. Enter date when provided. Process complete if date is within 14 days of diagnosis for "
        "patient with Type 1 diabetes.\n\n"
        "To be reported for patients diagnosed with type 1 diabetes during the audit year. If no date entered during the audit "
        "year then an assumption of incomplete care process will be made.\n\n"
        "Data for this item can be entered into the audit if received at a video/telephone appointment."
    ),
    "dietician_additional_appointment_offered": (
        "The additional appointment could be 1:1 or group session, via phone call, video call or face to face."
    ),
    "dietician_additional_appointment_date": (
        "Leave blank if appointment not attended.\n\n"
        "The additional appointment could be 1:1 or group session, via phone call, video call or face to face."
    ),
    "ketone_meter_training": (
        "Type 1 diabetes only\n\n"
        "Data for this item can be entered into the audit if collected at a video/telephone appointment."
    ),
    "flu_immunisation_recommended_date": (
        "If no date entered during the audit year then an assumption of incomplete care process will be made.\n\n"
        "Data for this item can be entered into the audit if the influenza immunisation was recommended at a video/telephone appointment."
    ),
    "sick_day_rules_training_date": (
        "Applies to patients with type 1 and type 2 diabetes. If no date entered during the audit year then an assumption of "
        "incomplete care process will be made.\n\n"
        "Data for this item can be entered into the audit if given at a video/telephone appointment."
    ),
    # In-patient Entry
    "hospital_admission_date": (
        "Please enter every diabetes-related hospital admission the patient has had (day case or longer) on separate rows. "
        "These should include admissions for stabilisation of diabetes (at diagnosis and/or in established patients), DKA "
        "(new and/or established patients), ketosis without acidosis, hypoglycaemia, surgical procedures or other causes."
    ),
    "hospital_discharge_date": ("For calculating number of bed days."),
    "hospital_admission_reason": (
        "Use option 1: Stabilisation of diabetes for new patients admitted without DKA or other admissions where the purpose "
        "was to stabilise blood glucose such as recurrent hyperglycaemia without acidosis."
    ),
    "dka_additional_therapies": (
        "Mandatory only if 'DKA' selected as Reason for admission."
    ),
    "hospital_admission_other": (
        "Mandatory only if 'Other causes' selected as Reason for admission."
    ),
}

# Field notes mapping for 2026+ dataset
FIELD_NOTES_2026 = {
    # Patient Details/Information
    "postcode": (
        "Enter the postcode in upper case and with a space in the correct place i.e. 'E13 ORI'."
    ),
    "sex_assigned_at_birth": (
        "Sex assigned at birth. 'Not Specified' means indeterminate, i.e. the patient is unable to be classified as either "
        "male or female.\n\n"
        "'Unknown' means that the sex of the patient has not been recorded."
    ),
    "ethnicity": (
        "Ethnicity should be self-reported by the family.\n\n"
        'The Information Standards Board for Health and Social Care Dataset Change Notice (DSCN) 11/2008 states: "the national '
        "code of 'Z- not stated' means that the person had been asked and had declined, either refusing to provide this information, "
        "or a genuine inability to choose, and should only be used in this circumstance and not to represent an unknown ethnicity.\n\n"
        "'Not Known' should be used where the patient had not been asked or the patient was not in a condition to be asked, e.g. "
        "unconscious. If the ethnic category is 'Not Known' use code 99.\n\n"
        "In some hospitals this information is collected at registration and recorded on your Patient Management System (PMS). "
        "Therefore, this data should be available to you."
    ),
    "adhd_asd_status": (
        "This should only include diagnoses confirmed by a healthcare professional qualified to make such a diagnosis."
    ),
    "learning_disability_status": (
        "This should only include diagnoses confirmed by a healthcare professional qualified to assess mental health conditions "
        "and/or learning disabilities.\n\n"
        "This includes intellectual disability, learning disabilities, and global developmental delay."
    ),
    "diabetes_type": (
        "If you are unable to classify your patient into any of the categories 1-4:\n\n"
        "Use category 5 where there is a recognised cause of diabetes (e.g. post organ transplantation, steroid induced diabetes, "
        "post pancreatitis/pancreatectomy) or related to a syndrome (e.g. Prader Willi or Lawrence Moon Biedl Syndrome).\n\n"
        "Use code 99 when the patient has diabetes but the cause is unknown.\n\n"
        "Do not include patients with preclinical type 1 diabetes (stages 1 and 2)."
    ),
    "diagnosis_date": (
        "If you are unable to classify your patient's diagnosis date as they were diagnosed elsewhere and exact date cannot be "
        "ascertained, insert the first day in the month of diagnosis and year. E.g. diagnosed in March 2014, enter 01/03/2014."
    ),
    "date_leaving_service": (
        "Enter date if patient left the service during the audit year otherwise leave blank."
    ),
    "reason_leaving_service": (
        "Enter reason for leaving if patient has left your service during the audit year."
    ),
    "death_date": ("Mandatory if patient dies from any cause in audit year."),
    "gp_practice_ods_code": (
        "You can download GP Practice code data here:\n\n"
        "Once you have downloaded and opened the GP Practices full file (.csv) you will see that the GP Practice Codes are listed "
        "in Column A. You are able to search the Excel file by selecting Ctrl + F to search for Name, Address, Postcode etc. to "
        "look for the relevant GP Practice Code."
    ),
    "pdu": (
        "This is the number used on your NPDA registration form as in previous years (previously PZ XXX) and is on your NPDA log in. "
        "If you do not know your organisation code, please find it here on the NPDA website under 'NPDA PZ numbers list'."
    ),
    "visit_date": (
        "Defines a row of data by a visit date.\n\n"
        "N.B. the date of any care process or outcome measure within a row may not always be identical to the visit date."
    ),
    # Routine Measurements
    "height": (
        "At least one height/weight measurement should be recorded during the audit year.\n\n"
        "BMI will be calculated centrally."
    ),
    "weight": (
        "At least one height/weight measurement should be recorded during the audit year.\n\n"
        "BMI will be calculated centrally."
    ),
    "height_weight_observation_date": (
        "Combined observation date for height and weight. If only height or weight measured still enter date."
    ),
    "hba1c": (
        "Collect and submit ALL the measurements with dates taken throughout the audit cycle.\n\n"
        "Use a new row for each with visit date for each measurement.\n\n"
        "Values in either mmol/mol or % will be accepted. Values between 3.98 and <20 will be treated as %, whereas values "
        "between 20 and 195 will be treated as mmol/mol."
    ),
    "hba1c_date": (
        "Date performed (within the audit year) is mandatory if observation value provided is to be accepted."
    ),
    # Treatment/Monitoring
    "insulin_regime": (
        "This question should be answered for all children and young people for all types of diabetes."
    ),
    "non_insulin_medication": (
        "This question will usually relate to children and young people with type 2 diabetes.\n\n"
        "Select GLP-1 agonist if it's prescribed alone or as an adjunct to metformin. GLP-1 agonists include liraglutide, "
        "dulaglutide, semaglutide, tirzepatide, exenatide, and lixisenatide.\n\n"
        "Select SGTL2 inhibitor if it's prescribed alone or as an adjunct to metformin. SGTL2 inhibitors include empagliflozin, "
        "dapagliflozin, canagliflozin, and ertugliflozin."
    ),
    "lifestyle_dietary_modification": (
        "This question will usually relate to children and young people with Type 2 and other forms of diabetes where dietary "
        "lifestyle modification has been advised.\n\n"
        "It does NOT refer to dietary advice related to carbohydrate counting and insulin dose adjustment."
    ),
    "cgm_use": (
        "This question should be answered for all children and young people for all types of diabetes.\n\n"
        "This can include all types of CGM which allow real time functionality."
    ),
    "ketone_meter_training": (
        "Data for this item can be entered into the audit if collected at a video/telephone appointment."
    ),
    "immunotherapy_received": (
        "Complete for all newly diagnosed patients with Type 1 diabetes.\n\n"
        "Answer 'Yes' if immunotherapy was provided before or shortly after the diagnosis of stage 3 Type 1 diabetes, including "
        "as part of a trial or early adoption scheme."
    ),
    # Annual Review - Health Checks
    "systolic_blood_pressure": (
        "Mandatory for Blood Pressure care process completion.\n\n"
        "Enter Systolic BP and Diastolic BP (if collected)\n\n"
        "Please use the methodology from the Diagnosis, Evaluation, and Treatment of High Blood Pressure in Children and Adolescents "
        "Report if performed."
    ),
    "diastolic_blood_pressure": (
        "Mandatory for Blood Pressure care process completion.\n\n"
        "Enter Systolic BP and Diastolic BP (if collected)\n\n"
        "Please use the methodology from the Diagnosis, Evaluation, and Treatment of High Blood Pressure in Children and Adolescents "
        "Report if performed."
    ),
    "blood_pressure_observation_date": (
        "Provide an observation date within the audit period. Date relates to both the systolic AND/OR diastolic pressure measurement."
    ),
    "foot_examination_observation_date": (
        "Complete only if screen performed.\n\n"
        "Mandatory care process if 12 years or older."
    ),
    "retinal_screening_observation_date": (
        "Complete only if screen performed.\n\n"
        "Mandatory care process if 12 years or older"
    ),
    "retinal_screening_result": (
        "Provide a result for retinal screening only if screen performed. Abnormal is defined as any level of retinopathy in either eye."
    ),
    "albumin_creatinine_ratio": (
        "Mandatory for children with type 1 diabetes aged 12 years and above and optional before 12 years.\n\n"
        "Mandatory for children with type 2 diabetes from diagnosis."
    ),
    "albumin_creatinine_ratio_date": (
        "Provide and observation date if a value provided."
    ),
    "albuminuria_stage": (
        "Submit your interpretation of the urinary albumin level based on your local laboratory reference ranges.\n\n"
        "Mandatory if level submitted."
    ),
    "total_cholesterol": (
        "Mandatory only for children with type 2 diabetes annually from diagnosis.\n\n"
        "Entry for patient with type 1 diabetes is optional and will not be included as an essential care process but will be "
        "reported as an outcome measure. Report if performed."
    ),
    "total_cholesterol_date": ("Observation date mandatory if value provided."),
    "thyroid_function_date": (
        "This measure is for all children with type 1 diabetes annually.\n\n"
        "Mandatory to provide an observation date if performed."
    ),
    "thyroid_treatment_status": (
        "Mandatory if thyroid testing performed.\n\n"
        "Data for this item can be entered into the audit if prescribed at a video/telephone appointment."
    ),
    "coeliac_screen_date": (
        "Date of coeliac disease screening only to be completed if patient was diagnosed within audit year.\n\n"
        "Process complete if date is within 90 days of diagnosis for patient with Type 1 diabetes."
    ),
    "gluten_free_diet": (
        "Provide dietary status for all patients at least one per audit year, even if a screening wasn't completed. A 'yes' "
        "response will be interpreted as the patient having a diagnosis of coeliac disease.\n\n"
        "Data for this item can be entered into the audit if a gluten-free diet was recommended at a video/telephone appointment."
    ),
    # Annual Review - Psychology
    "psychological_screening_assessment_date": (
        "Enter a date that a formal assessment has taken place for the 'need of additional psychological support' (beyond that "
        "which might be routinely provided within clinic). An assumption will be made that no assessment has taken place if no "
        "date entered.\n\n"
        "Only include assessments performed by a member of the paediatric diabetes MDT. This can be performed remotely.\n\n"
        "N.B this is a process measure, establishing whether the patient has been screened annually for psychological distress."
    ),
    "psychological_additional_support_status": (
        "Complete if annual psychological screening was performed at visit.\n\n"
        "Applicable if the patient was assessed as needing additional psychological support outside of routine clinical care "
        "provided by your PDU. i.e. was the patient assessed as experiencing a level of psychological distress necessitating "
        "additional support (regardless of whether or not the patient has yet received support, and regardless of whether this "
        "distress is primarily related to their diabetes).\n\n"
        "N.B. this is an outcome measure, following on from the process measure above (item 47)."
    ),
    "mental_health_appointment_offered": (
        "Answer 'Offered and attended' if the patient or a family member has received support from a mental health professional "
        "as part of the diabetes MDT at any point in the audit year.\n\n"
        "Only include appointments scheduled for this audit year.\n\n"
        "Include input as part of routine clinical care or additional support.\n\n"
        "'Mental health professionals' as part of the diabetes MDT can include, but are not limited to, clinical psychologists, "
        "counselling psychologists, neuropsychologists, psychotherapists, CBT therapists, and family therapists. It does NOT include "
        "school counsellors or educational psychologists."
    ),
    "smoking_vaping_status": (
        "Data for this item can be entered into the audit if collected at a video/telephone appointment."
    ),
    "smoking_cessation_referral_date": (
        "Data for this item can be entered into the audit if offered at a video/telephone appointment."
    ),
    # Annual Review - Dietetics
    "carbohydrate_counting_level_three_education_date": (
        "Level 3 carbohydrate counting is defined as carbohydrate counting with adjustment of insulin dosage according to an "
        "insulin:carbohydrate ratio. Enter date when provided. Process complete if date is within 14 days of diagnosis for patient "
        "with Type 1 diabetes.\n\n"
        "Data for this item can be entered into the audit if received at a video/telephone appointment."
    ),
    "dietician_additional_appointment_offered": (
        "This is an annual requirement. The additional appointment could be 1:1 or group session, via phone call, video call or "
        "face to face."
    ),
    "dietician_additional_appointment_date": (
        "Leave blank if appointment not attended."
    ),
    "flu_immunisation_recommended_date": (
        "Data for this item can be entered into the audit if the influenza immunisation was recommended at a video/telephone appointment."
    ),
    "sick_day_rules_training_date": (
        "Data for this item can be entered into the audit if given at a video/telephone appointment."
    ),
    # Admissions/Inpatient Entry
    "hospital_admission_date": (
        "Please enter every diabetes-related hospital admission the patient has had (day case or longer) on separate rows. These "
        "should include admissions for stabilisation of diabetes (at diagnosis and/or in established patients), DKA (new and/or "
        "established patients), ketosis without acidosis, hypoglycaemia, surgical procedures or other causes."
    ),
    "hospital_discharge_date": ("For calculating number of bed days."),
    "hospital_admission_reason_2026": (
        "Record all diabetes related admissions.\n\n"
        "Option 1: Admissions for DKA either at the time of diagnosis or not at diagnosis\n\n"
        "Option 2: Acute admission, but not in DKA. This could include vomiting, diarrhoea, ketosis without acidosis, and unable "
        "to manage a sick child with diabetes at home.\n\n"
        "Option 3: Hypoglycaemia requiring hospital admission for management.\n\n"
        "Option 4: Surgical admissions either acute or routine. E.g. endoscopy for coeliac disease confirmation.\n\n"
        "Option 5: Routine admission to help stabilise diabetes, including diabetes education post-diagnosis.\n\n"
        "Option 6: Other causes"
    ),
    "hospital_admission_other": (
        "Mandatory only if 'Other causes' selected as Reason for admission."
    ),
    "dka_additional_therapies": (
        "Mandatory only if 'DKA' (option 2) selected as Reason for admission."
    ),
    "blood_gas_ph": (
        "If a blood gas was performed during the admission, either in DKA or not, please enter the initial (first recorded during "
        "this admission) pH and standard bicarbonate results.\n\n"
        "If multiple blood gas tests were performed, please enter the first one."
    ),
    "blood_gas_bicarbonate": (
        "If a blood gas was performed during the admission, either in DKA or not, please enter the initial (first recorded during "
        "this admission) pH and standard bicarbonate results.\n\n"
        "If multiple blood gas tests were performed, please enter the first one."
    ),
}

# Field justification/standard texts mapping for 2021-2025 dataset
FIELD_JUSTIFICATION_STANDARDS_2021 = {
    # Patient Details/Information
    "nhs_number": (
        "This is a unique identifier and necessary to collect for linkage analysis with other databases such as Hospital Episode "
        "Statistics (HES) for England and the Patient Episode Database for Wales (PEDW)."
    ),
    "date_of_birth": (
        "Full D.O.B. is required to calculate an accurate decimal age for each patient. This allows interpretation of data collected "
        "on height, weight, calculated BMI and BP since these are age and gender specific. This also allows case-mix adjustment."
    ),
    "postcode": (
        "This allows analysis of the effect of deprivation on outcome measures and analysis of population statistics."
    ),
    "sex": (
        "To allow analysis of the effect of gender on outcomes and for interpretation of height, weight, calculated BMI and BP "
        "collected data. This also allows case-mix adjustment."
    ),
    "ethnicity": (
        "Necessary to examine the influence of ethnic origin on outcomes. Also allows for case-mix adjustment."
    ),
    "diabetes_type": (
        "Important to know about the heterogeneity of diabetes in children and young people."
    ),
    "diagnosis_date": (
        "Will allow accurate analysis of age bands. Will allow data from newly diagnosed patients to be analysed independently. "
        "Accurate date of diagnosis is required to provide relationships of outcome with duration of diabetes, and permits case-mix adjustment."
    ),
    "death_date": (
        "This is important information to collect to establish mortality rates in children and young people with diabetes."
    ),
    "gp_practice_ods_code": (
        "Necessary to produce an atlas of variation for outcomes for GP practices across England and Wales and for reporting at "
        "CCG level in England and Health Board level in Wales."
    ),
    # Routine Measurements
    "height": (
        "NG18: 1.2.45 At each clinic visit for children and young people with type 1 diabetes measure height and weight and plot on "
        "an appropriate growth chart. Check for normal growth and/or significant changes in weight because these may reflect changes "
        "in blood glucose control. [2004, amended 2015]\n\n"
        "NG18: 1.3.20 At each clinic visit for children and young people with type 2 diabetes: measure height and weight and plot on "
        "an appropriate growth chart, calculate BMI. Check for normal growth and/or significant changes in weight because these may "
        "reflect changes in blood glucose control. [2004, amended 2015]"
    ),
    "weight": (
        "NG18: 1.2.45 At each clinic visit for children and young people with type 1 diabetes measure height and weight and plot on "
        "an appropriate growth chart. Check for normal growth and/or significant changes in weight because these may reflect changes "
        "in blood glucose control. [2004, amended 2015]\n\n"
        "NG18: 1.3.20 At each clinic visit for children and young people with type 2 diabetes: measure height and weight and plot on "
        "an appropriate growth chart, calculate BMI. Check for normal growth and/or significant changes in weight because these may "
        "reflect changes in blood glucose control. [2004, amended 2015]"
    ),
    "hba1c": (
        "By providing ALL measurements of HbA1c a more powerful data analysis can be performed centrally. Allows means/median values "
        "for the year to be calculated. Data from first 3 months following diagnosis should be supplied but will be analysed "
        "independently as early measurements of HbA1c are not representative of overall diabetes control.\n\n"
        "NG18: 1 1.2.71 Offer children and young people with type 1 diabetes measurement of their HbA1c level 4 times a year (more "
        "frequent testing may be appropriate if there is concern about suboptimal blood glucose control).\n\n"
        "NG18: 1.3.28 Measure HbA1c levels every 3 months in children and young people with type 2 diabetes."
    ),
    "treatment": (
        "Important to get information that can relate intensification of insulin regimen to diabetes outcomes."
    ),
    "closed_loop_system": (
        "Collected for national monitoring of diabetes related technology usage and associated outcomes."
    ),
    "glucose_monitoring": (
        "Collected for national monitoring of diabetes related technology usage and associated outcomes.\n\n"
        "NG18: 1.2.62 Offer ongoing real-time continuous glucose monitoring with alarms to children and young people with type 1 "
        "diabetes who have: frequent severe hypoglycaemia or impaired awareness of hypoglycaemia associated with adverse consequences "
        "(for example, seizures or anxiety) or inability to recognise, or communicate about, symptoms of hypoglycaemia (for example, "
        "because of cognitive or neurological disabilities)."
    ),
    # Annual Review/Diagnosis
    "systolic_blood_pressure": (
        "To assess cardiovascular risk.\n\n"
        "NG18: 1.2.110 Offer children and young people with type 1 diabetes monitoring for: hypertension annually from 12 years.\n\n"
        "NG18: 1.3.43 Offer children and young people with type 2 diabetes annual monitoring for: hypertension starting at diagnosis."
    ),
    "diastolic_blood_pressure": (
        "To assess cardiovascular risk.\n\n"
        "NG18: 1.2.110 Offer children and young people with type 1 diabetes monitoring for: hypertension annually from 12 years.\n\n"
        "NG18: 1.3.43 Offer children and young people with type 2 diabetes annual monitoring for: hypertension starting at diagnosis."
    ),
    "foot_examination_observation_date": (
        "NG19: 1.3.2 For young people with diabetes who are 12–17 years, the paediatric care team or the transitional care team should "
        "assess the young person's feet as part of their annual assessment, and provide information about foot care. If a diabetic foot "
        "problem is found or suspected, the paediatric care team or the transitional care team should refer the young person to an "
        "appropriate specialist."
    ),
    "retinal_screening_observation_date": (
        "NG18: 1.2.110 Offer children and young people with type 1 diabetes monitoring for: diabetic retinopathy annually from 12 years\n\n"
        "NG18: 1.3.43 Offer children and young people with type 2 diabetes annual monitoring for: diabetic retinopathy from 12 years"
    ),
    "albumin_creatinine_ratio": (
        "Albuminuria is a marker for future microvascular complications and early mortality but is rare during pre-puberty. Its presence "
        "requires intensification of both monitoring and diabetes therapy which can result in lower albuminuria levels and reduced risk "
        "of future complications.\n\n"
        "NG18: 1.2.110 Offer children and young people with type 1 diabetes monitoring for moderately increased albuminuria "
        "(albumin:creatinine ratio [ACR] 3–30 mg/mmol; 'microalbuminuria') to detect diabetic kidney disease, annually from 12 years.\n\n"
        "NG18: 1.3.43 Offer children and young people with type 2 diabetes annual monitoring for moderately increased albuminuria "
        "(albumin:creatinine ratio [ACR] 3–30 mg/mmol; 'microalbuminuria') to detect diabetic kidney disease, starting at diagnosis.\n\n"
        "Necessary to determine national prevalence of albuminuria."
    ),
    "total_cholesterol": (
        "NG18: 1.3.43 Offer children and young people with type 2 diabetes annual monitoring for dyslipidaemia starting at diagnosis."
    ),
    "thyroid_function_date": (
        "Monitoring for complications and associated conditions of type 1 diabetes\n\n"
        "NG18: 1.2.110 Offer children and young people with type 1 diabetes monitoring for: thyroid disease at diagnosis and annually "
        "thereafter until transfer to adult services (NG18)."
    ),
    "thyroid_treatment_status": (
        "Thyroid treatment allows prevalence of thyroid autoimmunity associated with Type 1 diabetes to be calculated."
    ),
    "coeliac_screen_date": (
        "NG 20: 1.1.1 Offer serological testing for coeliac disease to people with: Type 1 diabetes, at diagnosis."
    ),
    "psychological_screening_assessment_date": (
        "Regular assessment of a broad range of psychological and behavioural problems in children and adults with type 1 diabetes is "
        "recommended.\n\n"
        "SIGN Guideline 16: In children this should include eating disorders, behavioural, emotional and family functioning problems "
        "(Management of diabetes, p5).\n\n"
        "NG18: 1.2.94. Diabetes teams should be aware that children and young people with type 1 diabetes have a greater risk of "
        "emotional and behavioural difficulties. [2004, amended 2015]\n\n"
        "NG18: 1.2.95 Offer children and young people with type 1 diabetes and their family members or carers (as appropriate) emotional "
        "support after diagnosis, which should be tailored to their emotional, social, cultural and age-dependent needs. [2004]"
    ),
    "psychological_additional_support_status": (
        "NG18: 1.2.96 Assess the emotional and psychological wellbeing of young people with type 1 diabetes who present with frequent "
        "episodes of diabetic ketoacidosis (DKA). [2004, amended 2015]\n\n"
        "NG18: 1.2.97 Be aware that a lack of adequate psychosocial support has a negative effect on various outcomes, including blood "
        "glucose control in children and young people with type 1 diabetes, and that it can also reduce their self-esteem. [2004, amended 2015]\n\n"
        "NG18: 1.2.98 Offer children and young people with type 1 diabetes and their family members or carers (as appropriate) timely and "
        "ongoing access to mental health professionals with an understanding of diabetes because they may experience psychological problems "
        "(such as anxiety, depression, behavioural and conduct disorders and family conflict) or psychosocial difficulties that can impact "
        "on the management of diabetes and wellbeing. [2004, amended 2015]\n\n"
        "NG18: 1.3.37 Offer children and young people with type 2 diabetes and their family members or carers (as appropriate) timely and "
        "ongoing access to mental health professionals with an understanding of diabetes because they may experience psychological problems "
        "(such as anxiety, depression, behavioural and conduct disorders and family conflict) or psychosocial difficulties that can impact "
        "on the management of diabetes and wellbeing. [2004, amended 2015]"
    ),
    "smoking_status": (
        "Smoking plays a significant contribution to micro and macrovascular disease development. Important to ascertain prevalence of "
        "smoking amongst the diabetic population."
    ),
    "smoking_cessation_referral_date": (
        "NG18: 1.2.14 Offer smoking cessation programmes to children and young people with type 1 diabetes who smoke. See also the NICE "
        "guidelines on brief interventions and referral for smoking cessation, smoking cessation services, harm reduction approaches to "
        "smoking, and smoking cessation in secondary care. [2004, amended 2015]\n\n"
        "NG18: 1.3.10 Offer smoking cessation programmes to children and young people with type 2 diabetes who smoke. See also the NICE "
        "guidelines on brief interventions and referral for smoking cessation, smoking cessation services, harm reduction approaches to "
        "smoking, and smoking cessation in secondary care. [2004, amended 2015]"
    ),
    "carbohydrate_counting_level_three_education_date": (
        "NG18: 1.2.37 Offer level 3 carbohydrate-counting education from diagnosis to children and young people with type 1 diabetes who "
        "are using a multiple daily insulin injection regimen or continuous subcutaneous insulin infusion (CSII or insulin pump) therapy, "
        "and to their family members or carers (as appropriate), and repeat the offer at intervals thereafter.\n\n"
        "Will be reported for patients diagnosed within audit year."
    ),
    "dietician_additional_appointment_offered": (
        "BPT indicator: Each patient should be offered at least one additional appointment per year with a paediatric dietitian (outside "
        "of the MDT clinic) with training in diabetes (or equivalent appropriate experience)."
    ),
    "ketone_meter_training": (
        "NG18: 1.2.74 Offer children and young people with type 1 diabetes blood ketone testing strips and a meter, and advise them and "
        "their family members or carers (as appropriate) to test for ketonaemia if they are ill or have hyperglycaemia."
    ),
    "flu_immunisation_recommended_date": (
        "NG18: 1.2.16 Explain to children and young people with type 1 diabetes and their family members or carers (as appropriate) that "
        "the Department of Health's Green Book recommends annual immunisation against influenza for children and young people with diabetes "
        "over the age of 6months. [2004]\n\n"
        "NG18: 1.3.12 Explain to children and young people with type 2 diabetes and their family members or carers (as appropriate) that "
        "the Department of Health's Green Book recommends annual immunisation against influenza for children and young people with diabetes. "
        "[2004, amended 2015]"
    ),
    "sick_day_rules_training_date": (
        "NG18: 1.2.73 Provide each child and young person with type 1 diabetes and their family members or carers (as appropriate) with "
        "clear individualised oral and written advice ('sick-day rules') about managing type 1 diabetes during inter-current illness or "
        "episodes of hyperglycaemia, including: monitoring blood glucose, monitoring and interpreting blood ketones (beta-hydroxybutyrate), "
        "adjusting their insulin regimen, food and fluid intake, when and where to seek further advice or help. Revisit the advice with the "
        "child or young person and their family members or carers, (as appropriate) at least annually.\n\n"
        "NG18: 1.3.1 Offer children and young people with type 2 diabetes and their family members or carers (as appropriate) a continuing "
        "programme of education from diagnosis. Ensure that the programme includes the following core topics: HbA1c monitoring and targets, "
        "the effects of inter-current illness on blood glucose control, the aims of metformin therapy and possible adverse effects, the "
        "complications of type 2 diabetes and how to prevent them."
    ),
    # In-patient Entry
    "hospital_admission_reason": (
        "Important to know why a child is admitted to hospital for reasons of having diabetes but not related to DKA or hypoglycaemia. "
        "Also to record incidence of DKA and hypoglycaemia complications.\n\n"
        "With Best Practice Tariff it is envisaged that this type of admission will decrease and this is of interest to commissioners.\n\n"
        "Please only record diabetes-related admissions."
    ),
}

# Field justification/standard texts mapping for 2026+ dataset
FIELD_JUSTIFICATION_STANDARDS_2026 = {
    # Patient Details/Information
    "nhs_number": (
        "This is a unique identifier and necessary to collect for linkage analysis with other databases such as Hospital Episode "
        "Statistics (HES) for England and the Patient Episode Database for Wales (PEDW)."
    ),
    "date_of_birth": (
        "Full D.O.B. is required to calculate an accurate decimal age for each patient and linkage with other databases. This allows "
        "interpretation of data collected on height, weight, calculated BMI and BP since these are age and gender specific."
    ),
    "postcode": (
        "This allows analysis of the effect of deprivation on outcome measures and analysis of population statistics."
    ),
    "sex_assigned_at_birth": (
        "To allow analysis of the effect of sex assigned at birth on outcomes and for interpretation of height, weight, calculated BMI "
        "and BP collected data."
    ),
    "ethnicity": ("Necessary to examine the influence of ethnic origin on outcomes."),
    "adhd_asd_status": (
        "To examine the relationship between the presence of ADHD and/or ASD on care and outcomes."
    ),
    "learning_disability_status": (
        "To examine the relationship between the presence of learning disabilities on care and outcomes"
    ),
    "diabetes_type": (
        "Important to know about the heterogeneity of types of diabetes in children and young people."
    ),
    "diagnosis_date": (
        "Will allow data from newly diagnosed patients to be analysed independently. Accurate date of diagnosis is required to provide "
        "relationships of outcome with duration of diabetes."
    ),
    "death_date": (
        "This is important information to collect to establish mortality rates in children and young people with diabetes."
    ),
    "gp_practice_ods_code": (
        "Necessary to produce an atlas of variation for outcomes for GP practices across England and Wales and for reporting at ICB level "
        "in England and Health Board level in Wales."
    ),
    # Routine Measurements
    "height": (
        "NG18: 1.2.46 At each clinic visit for children and young people with type 1 diabetes measure height and weight and plot on an "
        "appropriate growth chart. Check for normal growth or significant changes in weight because these may reflect changes in blood "
        "glucose control. [2004, amended 2015]\n\n"
        "NG18: 1.3.21 At each clinic visit for children and young people with type 2 diabetes: measure height and weight and plot on an "
        "appropriate growth chart and calculate BMI. Check for normal growth or significant changes in weight because these may reflect "
        "changes in blood glucose control. [2004, amended 2015]"
    ),
    "weight": (
        "NG18: 1.2.46 At each clinic visit for children and young people with type 1 diabetes measure height and weight and plot on an "
        "appropriate growth chart. Check for normal growth or significant changes in weight because these may reflect changes in blood "
        "glucose control. [2004, amended 2015]\n\n"
        "NG18: 1.3.21 At each clinic visit for children and young people with type 2 diabetes: measure height and weight and plot on an "
        "appropriate growth chart and calculate BMI. Check for normal growth or significant changes in weight because these may reflect "
        "changes in blood glucose control. [2004, amended 2015]"
    ),
    "hba1c": (
        "By providing ALL measurements of HbA1c a more powerful data analysis can be performed centrally. Allows means/median values for "
        "the year to be calculated. Data from first 3 months following diagnosis should be supplied but will be analysed independently as "
        "early measurements of HbA1c are not representative of overall diabetes control.\n\n"
        "NG18: 1.2.80 Measure HbA1c level 4 times a year in children and young people with type 1 diabetes. Think about more frequent "
        "testing if they are having difficulty with blood glucose management. [2004, amended 2015]\n\n"
        "NG18: 1.3.35 Measure HbA1c levels every 3 months in children and young people with type 2 diabetes. [2015]"
    ),
    # Treatment/Monitoring
    "insulin_regime": (
        "Important to get information that can relate intensification of insulin regime and insulin delivery methods to diabetes outcomes. "
        "Use of insulin as a treatment modality is no longer confined to just Type 1 diabetes."
    ),
    "non_insulin_medication": (
        "Important to get information that can relate medication regime to diabetes outcomes.\n\n"
        "NG18: 1.3.26: Four weeks after diagnosing type 2 diabetes and starting metformin in a child or young person, review data from "
        "glucose monitoring and, if needed, change treatment (see recommendations on adding liraglutide, dulaglutide, or empagliflozin for "
        "people on metformin only or for people on metformin and insulin). [2023]\n\n"
        "NG18: 1.3.24 Offer children and young people with type 2 diabetes a metformin monotherapy formulation in line with their own preferences"
    ),
    "lifestyle_dietary_modification": (
        "Important to get information that can relate dietary management to diabetes outcomes.\n\n"
        "NG18; 1.3.24 Offer children and young people with type 2 diabetes: advice and support on dietary management."
    ),
    "cgm_use": (
        "Collected for national monitoring of diabetes related technology usage and associated outcomes.\n\n"
        "NG18: 1.2.60 Offer real-time continuous glucose monitoring (rtCGM) to all children and young people with type 1 diabetes, alongside "
        "education to support children and young people, and their families and carers, to use it. [2022]\n\n"
        "NG18: 1.2.61 Offer intermittently scanned continuous glucose monitoring (isCGM, commonly referred to as 'flash') to children and "
        "young people with type 1 diabetes aged 4 years and over who are unable to use rtCGM or who express a clear preference for isCGM. [2022]"
    ),
    "ketone_meter_training": (
        "NG18; 1.2.83 Offer children and young people with type 1 diabetes blood ketone testing strips and a meter, and advise them and "
        "their family members or carers (as appropriate) to test for ketonaemia if they are ill or have hyperglycaemia. [2015]"
    ),
    "immunotherapy_received": (
        "GID-TA10981: NICE is currently appraising the clinical and cost effectiveness of teplizumab for delaying the onset of stage 3 Type 1 "
        "diabetes in people aged 8 years and older.\n\n"
        "Will be reported for patients diagnosed with type 1 diabetes within the audit year."
    ),
    # Annual Review - Health Checks
    "systolic_blood_pressure": (
        "To assess cardiovascular risk.\n\n"
        "NG18: 1.2.119 Offer children and young people with type 1 diabetes monitoring for: hypertension annually from 12 years. [2015]\n\n"
        "NG18; 1.3.74 Offer children and young people with type 2 diabetes annual monitoring for: hypertension starting at diagnosis. [2015]"
    ),
    "diastolic_blood_pressure": (
        "To assess cardiovascular risk.\n\n"
        "NG18: 1.2.119 Offer children and young people with type 1 diabetes monitoring for: hypertension annually from 12 years. [2015]\n\n"
        "NG18; 1.3.74 Offer children and young people with type 2 diabetes annual monitoring for: hypertension starting at diagnosis. [2015]"
    ),
    "foot_examination_observation_date": (
        "NG19: 1.3.2 For young people with diabetes who are 12 to 17 years, the paediatric care team or the transitional care team should "
        "assess the young person's feet as part of their annual assessment, and provide information about foot care. If a diabetic foot "
        "problem is found or suspected, the paediatric care team or the transitional care team should refer the young person to an appropriate "
        "specialist. [2015]"
    ),
    "retinal_screening_observation_date": (
        "NG18:1.2.120 and 1.3.76 Refer children and young people with type 1/type 2 diabetes for diabetic retinopathy screening from 12 years. [2015]"
    ),
    "albumin_creatinine_ratio": (
        "Necessary to determine national prevalence of albuminuria. Albuminuria is a marker for future microvascular complications and early "
        "mortality but is rare during pre-puberty. Its presence requires intensification of both monitoring and diabetes therapy which can "
        "result in lower albuminuria levels and reduced risk of future complications.\n\n"
        "NG18; 1.2.119 Offer children and young people with type 1 diabetes monitoring for moderately increased albuminuria (albumin:creatinine "
        "ratio [ACR] 3-30 mg/mmol; 'microalbuminuria') to detect diabetic kidney disease, annually from 12 years. [2015]\n\n"
        "NG18; 1.3.74 Offer children and young people with type 2 diabetes annual monitoring for moderately increased albuminuria "
        "(albumin:creatinine ratio [ACR] 3-30 mg/mmol; 'microalbuminuria') to detect diabetic kidney disease, starting at diagnosis. [2015]"
    ),
    "total_cholesterol": (
        "NG18: 1.3.74 Offer children and young people with type 2 diabetes annual monitoring for dyslipidaemia starting at diagnosis. [2015]"
    ),
    "thyroid_function_date": (
        "Monitoring for complications and associated conditions of type 1 diabetes\n\n"
        "NG18; 1.2.119 Offer children and young people with type 1 diabetes monitoring for thyroid disease, at diagnosis and annually "
        "thereafter until transfer to adult services."
    ),
    "thyroid_treatment_status": (
        "Thyroid treatment allows prevalence of thyroid autoimmunity associated with Type 1 diabetes to be calculated."
    ),
    "coeliac_screen_date": (
        "NG 20: 1.1.1 Offer serological testing for coeliac disease to people with: Type 1 diabetes, at diagnosis."
    ),
    # Annual Review - Psychology
    "psychological_screening_assessment_date": (
        "Regular assessment of a broad range of psychological and behavioural problems in children and adults with type 1 diabetes is "
        "recommended.\n\n"
        "NG18: 1.2.103 and 1.3.64 Diabetes teams should be aware that children and young people with type 1/type 2 diabetes have a greater "
        "risk of emotional and behavioural difficulties. [2004, amended 2015]\n\n"
        "NG18: 1.2.104 and 1.3.65 Offer children and young people with type 1/type 2 diabetes and their family members or carers (as "
        "appropriate) emotional support after diagnosis, which should be tailored to their emotional, social, cultural and age-dependent "
        "needs. [2004]\n\n"
        "NG18: 1.2.105 Assess the emotional and psychological wellbeing of young people with type 1 diabetes who present with frequent episodes "
        "of diabetic ketoacidosis (DKA). [2004, amended 2015]\n\n"
        "NG18: 1.2.106 and 1.3.67 Be aware that a lack of adequate psychosocial support has a negative effect on various outcomes, including "
        "blood glucose control in children and young people with type 1/type 2 diabetes, and that it can also reduce their self-esteem. [2004, "
        "amended 2015]\n\n"
        "NG18: 1.2.107 and 1.3.68 Offer children and young people with type 1/type 2 diabetes and their family members or carers (as appropriate) "
        "timely and ongoing access to mental health professionals with an understanding of diabetes because they may experience psychological "
        "problems (such as anxiety, depression, behavioural and conduct disorders and family conflict) or psychosocial difficulties that can "
        "impact on the management of diabetes and wellbeing. [2004, amended 2015]"
    ),
    "mental_health_appointment_offered": (
        "NHS England Best Practice Tariff: Discussion of the mental health and wellbeing of a patient should be an integral part of a patient's "
        "review with their MDT. Each patient must be assessed at least annually by their MDT as to whether additional psychological support is "
        "needed. The provider of formal psychological support for diabetes related problems must be an integral part of the MDT."
    ),
    # Annual Review - Dietetics
    "carbohydrate_counting_level_three_education_date": (
        "NG18; 1.2.38 For children and young people who are using a multiple daily insulin injection regimen or an insulin pump, offer level 3 "
        "carbohydrate counting education from diagnosis to them and their families or carers. Repeat this offer regularly. [2015]\n\n"
        "Will be reported for patients diagnosed within audit year."
    ),
    "dietician_additional_appointment_offered": (
        "NHS England Best Practice Tariff: Each patient should be offered at least one additional appointment per year with a paediatric "
        "dietitian (outside of the MDT clinic) with training in diabetes (or equivalent appropriate experience)."
    ),
    # Admissions/Inpatient Entry
    "hospital_admission_reason": (
        "Important to know why a child is admitted to hospital for reasons of having diabetes but not related to DKA or hypoglycaemia. Also "
        "to record incidence of DKA and hypoglycaemia complications.\n\n"
        "With Best Practice Tariff it is envisaged that this type of admission will decrease and this is of interest to commissioners."
    ),
    "dka_additional_therapies": ("To assess if cerebral oedema in DKA was suspected."),
    "blood_gas_ph": (
        "To assess whether an admission meets DKA diagnostic criteria. To assess the level of severity of DKA."
    ),
    "blood_gas_bicarbonate": (
        "To assess whether an admission meets DKA diagnostic criteria. To assess the level of severity of DKA."
    ),
}


def get_field_notes(field_name, dataset_year):
    """
    Returns the notes for a field based on dataset year.
    Works for both Patient and Visit models.

    Args:
        field_name: Name of the field to get notes for
        dataset_year: The dataset year (e.g., 2021, 2026)

    Returns:
        str: The appropriate notes text for the field, or empty string if not found
    """
    if dataset_year and dataset_year >= 2026:
        return FIELD_NOTES_2026.get(field_name, "")
    else:
        return FIELD_NOTES_2021.get(field_name, "")


def get_field_justification_standard(field_name, dataset_year):
    """
    Returns the justification or standard help text for a field based on dataset year.
    Works for both Patient and Visit models.

    Args:
        field_name: Name of the field to get justification/standard text for
        dataset_year: The dataset year (e.g., 2021, 2026)

    Returns:
        str: The appropriate justification/standard text for the field, or empty string if not found
    """
    if dataset_year and dataset_year >= 2026:
        return FIELD_JUSTIFICATION_STANDARDS_2026.get(field_name, "")
    else:
        return FIELD_JUSTIFICATION_STANDARDS_2021.get(field_name, "")


NEW_FIELDS_2026 = {
    "adhd_asd_status",
    "learning_disability_status",
    "immunotherapy_received",
    "immunotherapy_date",
    "blood_gas_ph",
    "blood_gas_bicarbonate",
    "insulin_regimen",
    "non_insulin_medication",
    "dietary_lifestyle_modification",
    "cgm_use",
    "psychological_support_outcome",
}
