"""
This file contains classes and functions to generate fictional children and fictional visits for the NPDA project.
"""

# python imports
import random
from datetime import date
from dateutil.relativedelta import relativedelta
from enum import Enum

# django imports
from django.apps import apps

# third-party imports
import nhs_number

# Importing constants
from project.constants import (
    SEX_TYPE,
    DIABETES_TYPES,
    ETHNICITIES,
    HBA1C_FORMATS,
    GLUCOSE_MONITORING_TYPES,
    TREATMENT_TYPES,
    YES_NO_UNKNOWN,
    RETINAL_SCREENING_RESULTS,
    ALBUMINURIA_STAGES,
    THYROID_TREATMENT_STATUS,
    SMOKING_STATUS,
    HOSPITAL_ADMISSION_REASONS,
    DKA_ADDITIONAL_THERAPIES,
)

from project.npda.general_functions.quarter_for_date import (
    current_audit_year_start_date,
)
from project.npda.general_functions.utils import random_date


# create an Enum for the range of ages
class AgeRange(Enum):
    """
    Enum class to represent the range of ages for children.
    """

    AGE_0_4 = "Birth to primary school age (0-4)"
    AGE_5_10 = "Primary school age (5-10)"
    AGE_11_15 = "Early secondary school age (11-15)"
    AGE_16_19 = "Late secondary school age (16-19): transition to adult services"
    AGE_20_25 = "Young adult (20-25)"


class VisitType(Enum):
    """
    Enum class to represent the type of visit for a child.
    """

    CLINIC = "Clinic"
    ANNUAL_REVIEW = "Annual Review"
    DIETICIAN = "Dietician"
    PSYCHOLOGY = "Psychology"
    HOSPITAL_ADMISSION = "Hospital Admission"


class HbA1cTargetRange(Enum):
    """
    Enum class to represent the level of diabetes control for a child.
    """

    TARGET = "On Target"
    ABOVE = "Above Target"
    WELL_ABOVE = "Well Above Target"


def create_fictional_patient(
    sex=None,
    ethnicity=None,
    age_range=None,
    diabetes_type=None,
    diagnosis_date=None,
    is_alive=None,
):
    """
    Constructor for the Child class.
    It creates a valid child object using these parameters as seed values to generate an instance with random values.
    Optional parameters are randomised if not provided.
    sex: int - 0, 1, 2, 9
    age_range: AgeRange - Enum class representing the range of ages for children (0-4, 5-10, 11-15, 16-19, 20-25) y
    diabetes_type: int - 1,2,3,4,5,99 ("Type 1 Insulin-Dependent Diabetes Mellitus", "Type 2 Non-Insulin Dependent Diabetes Mellitus", "Cystic Fibrosis Related Diabetes", "MODY (monogenic forms of diabetes)", "Other specified Diabetes Mellitus", "Unknown/unspecified")
    diagnosis_date: date - date of diagnosis of the child: if not provided, a valid random date is generated. If provided, the date must be valid, and left here as a parameter so that the user can provide a specific date, for example in the latest quarter or audit year.
    is_alive: bool - True or False

    Returns a Patient object - note it has not been saved as a record in the database. If invalid records are required, this instance can be modified to be invalid.
    """

    # Set the age range of the child to generate randomly if not provided
    if age_range is None:
        age_range = random.choice(list(AgeRange))

    # Private nested functions

    def _random_date_of_birth(age_range):
        """
        Returns a random date of birth within the age range requested.
        """
        today = date.today()

        if age_range == AgeRange.AGE_0_4:
            start_date = today - relativedelta(years=4)
            end_date = today
        elif age_range == AgeRange.AGE_5_10:
            start_date = today - relativedelta(years=10)
            end_date = today - relativedelta(years=5)
        elif age_range == AgeRange.AGE_11_15:
            start_date = today - relativedelta(years=15)
            end_date = today - relativedelta(years=11)
        elif age_range == AgeRange.AGE_16_19:
            start_date = today - relativedelta(years=19)
            end_date = today - relativedelta(years=16)
        elif age_range == AgeRange.AGE_20_25:
            start_date = today - relativedelta(years=25)
            end_date = today - relativedelta(years=20)
        else:
            return today

        random_days = random.randint(0, (end_date - start_date).days)
        return start_date + relativedelta(days=random_days)

    def _random_date(start_date, end_date):
        """
        Returns a random date between the start and end dates.
        """
        random_days = random.randint(0, (end_date - start_date).days)
        return start_date + relativedelta(days=random_days)

    Patient = apps.get_model("npda", "Patient")

    postcode = "SW1A 1AA"  # random postcode

    # Set a random ethnicity if not provided
    if ethnicity is None:
        ethnicity = random.choice(ETHNICITIES)[0]

    # Use the age range to generate a date of birth
    date_of_birth = _random_date_of_birth(age_range=age_range)

    # Use the date of birth to generate a date of diagnosis
    if diagnosis_date is None:
        diagnosis_date = _random_date(date_of_birth, date.today())

    # Set a random diabetes type if not provided
    if diabetes_type is None:
        diabetes_type = random.choice(DIABETES_TYPES)[0]

    # Generate a random date of death if the child is not alive
    death_date = None
    if is_alive is None:
        is_alive = True
    else:
        if not is_alive:
            death_date = _random_date(diagnosis_date, date.today())

    # Create the child object
    sex = sex if sex is None else random.choice(SEX_TYPE)[0]

    _nhs_number = nhs_number.generate(quantity=1, for_region=nhs_number.REGION_ENGLAND)[
        0
    ]

    index_of_multiple_deprivation_quintile = random.randint(1, 5)
    gp_practice_ods_code = "G85004"  # random gp_practice_ods_code
    gp_practice_postcode = "SE23 1HU"  # random gp_practice_postcode
    is_valid = True
    errors = []

    return Patient(
        nhs_number=_nhs_number,
        postcode=postcode,
        sex=sex,
        date_of_birth=date_of_birth,
        ethnicity=ethnicity,
        index_of_multiple_deprivation_quintile=index_of_multiple_deprivation_quintile,
        diabetes_type=diabetes_type,
        diagnosis_date=diagnosis_date,
        death_date=death_date,
        gp_practice_ods_code=gp_practice_ods_code,
        gp_practice_postcode=gp_practice_postcode,
        is_valid=is_valid,
        errors=errors,
    )


def generate_transfer_instance(patient, paediatric_diabetes_unit=None):
    """
    Generates a transfer instance for a patient to a paediatric diabetes unit.
    If not provided, the paediatric diabetes unit is randomly selected.
    """
    PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")

    paediatric_diabetes_unit = (
        paediatric_diabetes_unit
        if paediatric_diabetes_unit is not None
        else PaediatricDiabetesUnit.objects.all().order_by("?").first()
    )

    Transfer = apps.get_model("npda", "Transfer")
    return Transfer(
        patient=patient,
        paediatric_diabetes_unit=paediatric_diabetes_unit,
        date=date.today(),
    )


def create_fictional_visit(
    patient,
    visit_date=None,
    hba1_target_range: HbA1cTargetRange = None,  # one of ["On Target", "Above Target", "Well Above Target"]
    visit_type: VisitType = VisitType.CLINIC,
):
    """
    Creates a valid Visit object using these parameters as seed values to generate an instance with random values.
    Optional parameters are randomised if not provided.
    patient: Patient - the patient object for which the attendance is created
    visit_date: date - the date of the attendance: if not provided, a valid random date is generated. If provided, the date must be valid, and left here as a parameter so that the user can provide a specific date, for example in the latest quarter or audit year.
    hba1_target_range: enum - one of ["On Target", "Above Target", "Well Above Target"] - to determine the range of HbA1c values anticipated. if not provided, a random range is selected.
    visit_type: enum - one of ["Clinic", "Annual Review", "Dietician", "Psychology", "Hospital Admission"]
        - to determine the type of visit. The default is a clinic visit.
        - different visit types have different fields that need to be completed

    # A typical visit will either be on of "Clinic", "Annual Review", "Dietician", "Psychology", "Hospital Admission"
    # A clinic visit will have the following fields:
    # - measurements
    # - HbA1c
    # - treatment
    # - CGM
    # - BP

    # An annual review will have the following fields:
    # - foot
    # - DECS
    # - ACR
    # - cholesterol
    # - thyroid
    # - coeliac
    # - smoking
    # - sick day rules
    # - flu
    # - ketone meter training
    # - carbohydrate counting

    # There also addtional visits for:
    # - dietician
    # - psychology
    # - hospital admissions

    """

    if visit_date is None:
        # Generate a random date for the visit if one is not provided. The date selected is random but must be after the diagnosis date or in the current audit year.
        start_date = current_audit_year_start_date(date_instance=date.today())
        if patient.diagnosis_date > start_date:
            start_date = patient.diagnosis_date
        visit_date = random_date(start_date=start_date, end_date=date.today())

    def _calculate_age_range(patient):
        """
        Returns the age range of the child.
        """
        age = date.today().year - patient.date_of_birth.year
        if age <= 4:
            return AgeRange.AGE_0_4
        elif age <= 10:
            return AgeRange.AGE_5_10
        elif age <= 15:
            return AgeRange.AGE_11_15
        elif age <= 19:
            return AgeRange.AGE_16_19
        else:
            return AgeRange.AGE_20_25

    hba1_target_range = random.choice(list(HbA1cTargetRange))
    _age_range = _calculate_age_range(patient)

    """
    Private methods to generate random values for the observations. 
    Some of these methods are specific to the age range of the child or the diabetes type or the level of diabetes control they have.
    """

    def _clinic_measures(age_range: AgeRange, diabetes_type: int, visit_date: date):
        """
        Gather all the measures for a clinic visit. These include height, weight, HbA1c, treatment, CGM, and BP.
        """
        height, weight, height_weight_observation_date = _height_weight_observations(
            age_range=age_range, visit_date=visit_date
        )
        hba1c, hba1c_format, hba1c_date = _hba1c_observations(
            hba1_target_range=hba1_target_range,
            visit_date=visit_date,
        )
        glucose_monitoring = _continuous_glucose_monitoring_observations()
        treatment, closed_loop_system = _treatment_observations(
            diabetes_type=diabetes_type
        )
        (
            diastolic_blood_pressure,
            systolic_blood_pressure,
            blood_pressure_observation_date,
        ) = _bp_observations(age_range=age_range, visit_date=visit_date)
        return (
            height,
            weight,
            height_weight_observation_date,
            hba1c,
            hba1c_format,
            hba1c_date,
            glucose_monitoring,
            treatment,
            closed_loop_system,
            diastolic_blood_pressure,
            systolic_blood_pressure,
            blood_pressure_observation_date,
        )

    def _annual_review_measures(visit_date: date):
        """
        Gather all the measures for an annual review visit.
        These include:
            foot
            DECS
            ACR
            cholesterol
            thyroid
            coeliac
            smoking
            carbohydrate counting
            sick day rules
            flu
            ketone meter training
            carbohydrate counting
        """
        foot_examination_observation_date = _foot_observations(visit_date=visit_date)
        retinal_screening_result, retinal_screening_observation_date = (
            _decs_observations(visit_date=visit_date)
        )
        (
            albumin_creatinine_ratio,
            albumin_creatinine_ratio_date,
            albuminuria_stage,
        ) = _acr_observations(visit_date=visit_date)
        total_cholesterol, total_cholesterol_date = _cholesterol_observations(
            visit_date=visit_date
        )
        thyroid_function_date, thyroid_treatment_status = _thyroid_observations(
            visit_date=visit_date
        )
        coeliac_screen_date, gluten_free_diet = _coeliac_observations(
            visit_date=visit_date
        )
        smoking_status, smoking_cessation_referral_date = _smoking_observations(
            visit_date=visit_date
        )
        carbohydrate_counting_level_three_education_date = (
            _carbohydrate_counting_observations(visit_date=visit_date)
        )
        flu_immunisation_recommended_date = _flu_immunisation_observations(
            visit_date=visit_date
        )
        ketone_meter_training = _ketone_meter_observations(visit_date=visit_date)
        sick_day_rules_training_date = _sick_day_rules_observations(
            visit_date=visit_date
        )

        return (
            foot_examination_observation_date,
            retinal_screening_result,
            retinal_screening_observation_date,
            albumin_creatinine_ratio,
            albumin_creatinine_ratio_date,
            albuminuria_stage,
            total_cholesterol,
            total_cholesterol_date,
            thyroid_function_date,
            thyroid_treatment_status,
            coeliac_screen_date,
            gluten_free_diet,
            smoking_status,
            smoking_cessation_referral_date,
            carbohydrate_counting_level_three_education_date,
            flu_immunisation_recommended_date,
            ketone_meter_training,
            sick_day_rules_training_date,
        )

    def _height_weight_observations(age_range: AgeRange, visit_date: date):
        """
        Generates random height and weight observations for a child.
        Use the age_range to determine the range of values for height and weight.
        Allocate the visit date to the date of the observation.
        """
        height_weight_observations = {
            AgeRange.AGE_0_4: (50, 110, 10, 20),
            AgeRange.AGE_5_10: (110, 150, 20, 40),
            AgeRange.AGE_11_15: (150, 170, 40, 70),
            AgeRange.AGE_16_19: (170, 190, 60, 90),
            AgeRange.AGE_20_25: (170, 190, 60, 90),
        }

        height_min, height_max, weight_min, weight_max = height_weight_observations[
            age_range
        ]
        height = round(random.uniform(height_min, height_max), 2)
        weight = round(random.uniform(weight_min, weight_max), 2)
        height_weight_observation_date = (
            visit_date  # set the date of the observation to the visit date
        )
        return height, weight, height_weight_observation_date

    def _hba1c_observations(hba1_target_range: HbA1cTargetRange, visit_date: date):
        """
        Generates random HbA1c observations for a child.
        Use the diabetes type to determine the range of values for HbA1c in mmol/mol.
        Allocate the visit date to the date of the observation.
        """
        hba1c_observations = {
            HbA1cTargetRange.TARGET: (48, 58),
            HbA1cTargetRange.ABOVE: (58, 85),
            HbA1cTargetRange.WELL_ABOVE: (85, 120),
        }

        hba1c_min, hba1c_max = hba1c_observations[hba1_target_range]
        hba1c = random.randint(hba1c_min, hba1c_max)
        hba1c_format = HBA1C_FORMATS[0][0]  # mmol/mol
        hba1c_date = visit_date
        return hba1c, hba1c_format, hba1c_date

    def _continuous_glucose_monitoring_observations():
        """
        Generates random continuous glucose monitoring observations for a child.
        Allocate the visit date to the date of the observation.
        """
        glucose_monitoring = random.choice(GLUCOSE_MONITORING_TYPES)[0]
        return glucose_monitoring

    def _treatment_observations(diabetes_type: int):
        """
        Generates random treatment observations for a child.
        Use the diabetes type to determine the range of values for treatment.
        Allocate the visit date to the date of the observation.
        """
        if diabetes_type == 1:
            treatment = random.choice(TREATMENT_TYPES[0:6])[0]  # MDI or pump options
        else:
            treatment = random.choice(
                [1, 2, 4, 5, 7, 8, 9]
            )  # insulin or non-insulin options compatible with type 2 diabetes

        if diabetes_type == 1:
            closed_loop_system = random.choice([True, False])
        else:
            closed_loop_system = YES_NO_UNKNOWN[0][0]  # No

        return treatment, closed_loop_system

    def _bp_observations(age_range: AgeRange, visit_date: date):
        """
        Generates random blood pressure observations for a child based on the age range.
        Allocate the visit date to the date of the observation.
        """
        bp_ranges = {
            AgeRange.AGE_0_4: (40, 50, 80, 90),
            AgeRange.AGE_5_10: (40, 50, 90, 100),
            AgeRange.AGE_11_15: (50, 60, 95, 105),
            AgeRange.AGE_16_19: (60, 70, 110, 130),
            AgeRange.AGE_20_25: (60, 70, 110, 130),
        }
        diastolic_blood_pressure = random.randint(
            (bp_ranges[age_range])[0], (bp_ranges[age_range])[1]
        )
        systolic_blood_pressure = random.randint(
            (bp_ranges[age_range])[2], (bp_ranges[age_range])[3]
        )
        blood_pressure_observation_date = visit_date
        return (
            diastolic_blood_pressure,
            systolic_blood_pressure,
            blood_pressure_observation_date,
        )

    def _foot_observations(visit_date: date):
        """
        Generates random foot examination observations for a child.
        Allocate the visit date to the date of the observation.
        """
        foot_examination_observation_date = visit_date
        return foot_examination_observation_date

    def _decs_observations(visit_date: date):
        """
        Generates random DECS observations for a child.
        Allocate the visit date to the date of the observation.
        """
        retinal_screening_observation_date = visit_date
        retinal_screening_result = random.choice(RETINAL_SCREENING_RESULTS)[0]
        return retinal_screening_result, retinal_screening_observation_date

    def _acr_observations(visit_date: date):
        """
        Generates random ACR observations for a child.
        Allocate the visit date to the date of the observation.
        """
        albumin_creatinine_ratio = random.randint(0, 300)
        albumin_creatinine_ratio_date = visit_date
        albuminuria_stage = random.choice(ALBUMINURIA_STAGES)[0]
        return (
            albumin_creatinine_ratio,
            albumin_creatinine_ratio_date,
            albuminuria_stage,
        )

    def _cholesterol_observations(visit_date: date):
        """
        Generates random cholesterol observations for a child.
        Allocate the visit date to the date of the observation.
        """
        total_cholesterol = round(random.uniform(2, 7), 2)
        total_cholesterol_date = visit_date
        return total_cholesterol, total_cholesterol_date

    def _thyroid_observations(visit_date: date):
        """
        Generates random thyroid function observations for a child.
        Allocate the visit date to the date of the observation.
        """
        thyroid_function_date = visit_date
        thyroid_treatment_status = random.choice(THYROID_TREATMENT_STATUS)[0]
        return thyroid_function_date, thyroid_treatment_status

    def _coeliac_observations(visit_date: date):
        """
        Generates random coeliac screening observations for a child.
        Allocate the visit date to the date of the observation.
        """
        coeliac_screen_date = visit_date
        gluten_free_diet = random.choice(YES_NO_UNKNOWN)[0]
        return coeliac_screen_date, gluten_free_diet

    def _psychological_observations(visit_date: date):
        """
        Generates random psychological screening observations for a child.
        Allocate the visit date to the date of the observation.
        """
        psychological_screening_assessment_date = visit_date
        psychological_additional_support_status = random.choice(YES_NO_UNKNOWN)[0]
        return (
            psychological_screening_assessment_date,
            psychological_additional_support_status,
        )

    def _smoking_observations(visit_date: date):
        """
        Generates random smoking status observations for a child.
        Allocate the visit date to the date of the observation.
        """
        smoking_status = random.choice(SMOKING_STATUS)[0]
        smoking_cessation_referral_date = visit_date
        return smoking_status, smoking_cessation_referral_date

    def _carbohydrate_counting_observations(visit_date: date):
        """
        Generates random carbohydrate counting observations for a child.
        Allocate the visit date to the date of the observation.
        """
        carbohydrate_counting_level_three_education_date = visit_date
        return carbohydrate_counting_level_three_education_date

    def _dietician_observations(visit_date: date):
        """
        Generates random dietician observations for a child.
        Allocate the visit date to the date of the observation.
        """
        dietician_additional_appointment_offered = random.choice(YES_NO_UNKNOWN)[0]
        dietician_additional_appointment_date = visit_date
        return (
            dietician_additional_appointment_offered,
            dietician_additional_appointment_date,
        )

    def _flu_immunisation_observations(visit_date: date):
        """
        Generates random flu immunisation observations for a child.
        Allocate the visit date to the date of the observation.
        """
        flu_immunisation_recommended_date = visit_date
        return flu_immunisation_recommended_date

    def _ketone_meter_observations():
        """
        Generates random ketone meter observations for a child.
        """
        ketone_meter_training = random.choice(YES_NO_UNKNOWN)[0]
        return ketone_meter_training

    def _sick_day_rules_observations(visit_date: date):
        """
        Generates random sick day rules observations for a child.
        Allocate the visit date to the date of the observation.
        """
        sick_day_rules_training_date = visit_date
        return sick_day_rules_training_date

    def _hospital_admission_observations():
        """
        Generates random hospital admission observations for a child.
        Allocate the visit date to the date of the observation.
        """
        hospital_admission_date = self.visit_date
        hospital_discharge_date = self.visit_date
        hospital_admission_reason = random.choice(HOSPITAL_ADMISSION_REASONS)[0]
        dka_additional_therapies = random.choice(DKA_ADDITIONAL_THERAPIES)[0]
        hospital_admission_other = None
        return (
            hospital_admission_date,
            hospital_discharge_date,
            hospital_admission_reason,
            dka_additional_therapies,
            hospital_admission_other,
        )

    # Create the visit object
    Visit = apps.get_model("npda", "Visit")

    """
    The visit category determines the fields that need to be completed for the visit.
    If no visit category is provided, it will be assumed this is a clinic visit.
    """
    if visit_type == VisitType.CLINIC:
        (
            height,
            weight,
            height_weight_observation_date,
            hba1c,
            hba1c_format,
            hba1c_date,
            glucose_monitoring,
            treatment,
            closed_loop_system,
            diastolic_blood_pressure,
            systolic_blood_pressure,
            blood_pressure_observation_date,
        ) = _clinic_measures(
            age_range=_age_range,
            diabetes_type=patient.diabetes_type,
            visit_date=visit_date,
        )
    else:
        height = None
        weight = None
        height_weight_observation_date = None
        hba1c = None
        hba1c_format = None
        hba1c_date = None
        glucose_monitoring = None
        treatment = None
        closed_loop_system = None
        diastolic_blood_pressure = None
        systolic_blood_pressure = None
        blood_pressure_observation_date = None

    if visit_type == VisitType.ANNUAL_REVIEW:
        (
            foot_examination_observation_date,
            retinal_screening_result,
            retinal_screening_observation_date,
            albumin_creatinine_ratio,
            albumin_creatinine_ratio_date,
            albuminuria_stage,
            total_cholesterol,
            total_cholesterol_date,
            thyroid_function_date,
            thyroid_treatment_status,
            coeliac_screen_date,
            gluten_free_diet,
            smoking_status,
            smoking_cessation_referral_date,
            carbohydrate_counting_level_three_education_date,
            flu_immunisation_recommended_date,
            ketone_meter_training,
            sick_day_rules_training_date,
        ) = _annual_review_measures(visit_date=visit_date)
    else:
        foot_examination_observation_date = None
        retinal_screening_result = None
        retinal_screening_observation_date = None
        albumin_creatinine_ratio = None
        albumin_creatinine_ratio_date = None
        albuminuria_stage = None
        total_cholesterol = None
        total_cholesterol_date = None
        thyroid_function_date = None
        thyroid_treatment_status = None
        coeliac_screen_date = None
        gluten_free_diet = None
        smoking_status = None
        smoking_cessation_referral_date = None
        carbohydrate_counting_level_three_education_date = None
        flu_immunisation_recommended_date = None
        ketone_meter_training = None
        sick_day_rules_training_date = None

    if visit_type == VisitType.DIETICIAN:
        (
            dietician_additional_appointment_offered,
            dietician_additional_appointment_date,
        ) = _dietician_observations()
    else:
        dietician_additional_appointment_offered = None
        dietician_additional_appointment_date = None

    if visit_type == VisitType.PSYCHOLOGY:
        (
            psychological_screening_assessment_date,
            psychological_additional_support_status,
        ) = _psychological_observations()
    else:
        psychological_screening_assessment_date = None
        psychological_additional_support_status = None

    if visit_type == VisitType.HOSPITAL_ADMISSION:
        (
            hospital_admission_date,
            hospital_discharge_date,
            hospital_admission_reason,
            dka_additional_therapies,
            hospital_admission_other,
        ) = _hospital_admission_observations()
    else:
        hospital_admission_date = None
        hospital_discharge_date = None
        hospital_admission_reason = None
        dka_additional_therapies = None
        hospital_admission_other = None

    # set the attendance as valid
    is_valid = True
    errors = []

    return Visit(
        visit_date=visit_date,
        height=height,
        weight=weight,
        height_weight_observation_date=height_weight_observation_date,
        hba1c=hba1c,
        hba1c_format=hba1c_format,
        hba1c_date=hba1c_date,
        glucose_monitoring=glucose_monitoring,
        treatment=treatment,
        closed_loop_system=closed_loop_system,
        diastolic_blood_pressure=diastolic_blood_pressure,
        systolic_blood_pressure=systolic_blood_pressure,
        blood_pressure_observation_date=blood_pressure_observation_date,
        foot_examination_observation_date=foot_examination_observation_date,
        retinal_screening_result=retinal_screening_result,
        retinal_screening_observation_date=retinal_screening_observation_date,
        albumin_creatinine_ratio=albumin_creatinine_ratio,
        albumin_creatinine_ratio_date=albumin_creatinine_ratio_date,
        albuminuria_stage=albuminuria_stage,
        total_cholesterol=total_cholesterol,
        total_cholesterol_date=total_cholesterol_date,
        thyroid_function_date=thyroid_function_date,
        thyroid_treatment_status=thyroid_treatment_status,
        coeliac_screen_date=coeliac_screen_date,
        gluten_free_diet=gluten_free_diet,
        smoking_status=smoking_status,
        smoking_cessation_referral_date=smoking_cessation_referral_date,
        carbohydrate_counting_level_three_education_date=carbohydrate_counting_level_three_education_date,
        flu_immunisation_recommended_date=flu_immunisation_recommended_date,
        ketone_meter_training=ketone_meter_training,
        sick_day_rules_training_date=sick_day_rules_training_date,
        dietician_additional_appointment_offered=dietician_additional_appointment_offered,
        dietician_additional_appointment_date=dietician_additional_appointment_date,
        psychological_screening_assessment_date=psychological_screening_assessment_date,
        psychological_additional_support_status=psychological_additional_support_status,
        hospital_admission_date=hospital_admission_date,
        hospital_discharge_date=hospital_discharge_date,
        hospital_admission_reason=hospital_admission_reason,
        dka_additional_therapies=dka_additional_therapies,
        hospital_admission_other=hospital_admission_other,
        is_valid=is_valid,
        errors=errors,
        patient=patient,
    )
