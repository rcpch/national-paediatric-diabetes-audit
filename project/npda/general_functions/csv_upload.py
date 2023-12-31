from django.apps import apps
import pandas as pd
from ...constants import CSV_HEADINGS, ALL_DATES
from django.conf import settings
import os


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
            raise Exception(f"Could not save visit {obj}: {error}")

    dataframe.apply(save_row, axis=1)
