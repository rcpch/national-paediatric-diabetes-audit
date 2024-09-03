"""
This file contains classes and functions to generate fictional children and fictional visits for the NPDA project.
"""

# python imports
import random
from datetime import date
from dateutil.relativedelta import relativedelta
from enum import Enum
from typing import List

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
from project.constants.visit_categories import VisitCategories, VISIT_FIELDS


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


class Child:

    sex = random.choice(SEX_TYPE)[0]
    diabetes_type = random.choice(DIABETES_TYPES)[0]
    age_range = random.choice(list(AgeRange))
    ethnicity = random.choice(ETHNICITIES)[0]
    diabetes_type = random.choice(DIABETES_TYPES)[0]
    postcode = "SW1A 1AA"  # random postcode
    is_alive = True

    def __init__(
        self,
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

        # Set a random ethnicity if not provided
        if ethnicity is not None:
            self.ethnicity = ethnicity[0]

        # Set the age range of the child to generate randomly if not provided
        if age_range is not None:
            self.age_range = age_range

        # Use the age range to generate a date of birth
        self.date_of_birth = self._random_date_of_birth(self.age_range)

        # Use the date of birth to generate a date of diagnosis
        if diagnosis_date is not None:
            self.diagnosis_date = diagnosis_date
        else:
            self.diagnosis_date = self._random_date(self.date_of_birth, date.today())

        # Set a random diabetes type if not provided
        if diabetes_type is not None:
            self.diabetes_type = diabetes_type[0]

        # Generate a random date of death if the child is not alive
        if is_alive is not None:
            self.is_alive = is_alive
            if not is_alive:
                death_date = self._random_date(self.diagnosis_date, date.today())
            else:
                death_date = None
        else:
            death_date = None

        # Create the child object
        self.sex = sex if sex is not None else self.sex

        self.death_date = death_date
        self.nhs_number = nhs_number.generate(
            quantity=1, for_region=nhs_number.REGION_ENGLAND
        )[0]

        self.index_of_multiple_deprivation_quintile = random.randint(1, 5)
        self.gp_practice_ods_code = "G85004"  # random gp_practice_ods_code
        self.gp_practice_postcode = "SE23 1HU"  # random gp_practice_postcode
        self.is_valid = True
        self.errors = []

    def _random_date_of_birth(self, age_range):
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

    def _random_date(self, start_date, end_date):
        """
        Returns a random date between the start and end dates.
        """
        random_days = random.randint(0, (end_date - start_date).days)
        return start_date + relativedelta(days=random_days)


def generate_valid_patients(
    number_of_children: int,
    sex=None,
    ethnicity=None,
    age_range=None,
    diabetes_type=None,
    diagnosis_date=None,
    is_alive=None,
):
    """
    Generates a list of fictional children as Patient objects.
    Note that the children are not saved as records in the database and  therefore do not have a primary key.
    """
    children = []
    for _ in range(number_of_children):
        child = Child(
            sex=sex,
            ethnicity=ethnicity,
            age_range=age_range,
            diabetes_type=diabetes_type,
            diagnosis_date=diagnosis_date,
            is_alive=is_alive,
        )
        Patient = apps.get_model("npda", "Patient")
        children.append(Patient(**child.__dict__))
    return children


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


def generate_valid_attendance(
    patient,
    visit_date=None,
    hba1_target_range=None,
    visit_type=VisitType.CLINIC,
):
    """
    Generates a valid attendance for a patient.
    """
    attendance = Attendance(
        patient=patient,
        visit_date=visit_date,
        hba1_target_range=hba1_target_range,
        visit_type=visit_type,
    )
    return attendance


class Attendance:
    """
    Class to represent an attendance for a child.
    """

    visit_date = date.today()
    hba1_target_range = random.choice(list(HbA1cTargetRange))

    def __init__(
        self,
        patient: Child,
        visit_date: date = None,
        hba1_target_range: HbA1cTargetRange = None,  # one of ["On Target", "Above Target", "Well Above Target"]
        visit_type: VisitType = VisitType.CLINIC,
    ) -> None:
        """
        Constructor for the Attendance class.
        It creates a valid attendance object using these parameters as seed values to generate an instance with random values.
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
        self.patient = patient

        self.age_range = self.age_range(patient)

        if hba1_target_range:
            self.hba1_target_range = hba1_target_range

        self.visit_date = (
            visit_date
            if visit_date is not None
            else self._random_date(self.patient.diagnosis_date, date.today())
        )

        """
        The visit category determines the fields that need to be completed for the visit.
        If no visit category is provided, it will be assumed this is a clinic visit.
        """
        if visit_type == VisitType.CLINIC:
            (
                self.height,
                self.weight,
                self.height_weight_observation_date,
                self.hba1c,
                self.hba1c_format,
                self.hba1c_date,
                self.glucose_monitoring,
                self.treatment,
                self.closed_loop_system,
                self.diastolic_blood_pressure,
                self.systolic_blood_pressure,
                self.blood_pressure_observation_date,
            ) = self._clinic_measures(self.age_range)
        else:
            self.height = None
            self.weight = None
            self.height_weight_observation_date = None
            self.hba1c = None
            self.hba1c_format = None
            self.hba1c_date = None
            self.glucose_monitoring = None
            self.treatment = None
            self.closed_loop_system = None
            self.diastolic_blood_pressure = None
            self.systolic_blood_pressure = None
            self.blood_pressure_observation_date = None

        if visit_type == VisitType.ANNUAL_REVIEW:
            (
                self.foot_examination_observation_date,
                self.retinal_screening_result,
                self.retinal_screening_observation_date,
                self.albumin_creatinine_ratio,
                self.albumin_creatinine_ratio_date,
                self.albuminuria_stage,
                self.total_cholesterol,
                self.total_cholesterol_date,
                self.thyroid_function_date,
                self.thyroid_treatment_status,
                self.coeliac_screen_date,
                self.gluten_free_diet,
                self.smoking_status,
                self.smoking_cessation_referral_date,
                self.carbohydrate_counting_level_three_education_date,
                self.flu_immunisation_recommended_date,
                self.ketone_meter_training,
                self.sick_day_rules_training_date,
            ) = self._annual_review_measures()
        else:
            self.foot_examination_observation_date = None
            self.retinal_screening_result = None
            self.retinal_screening_observation_date = None
            self.albumin_creatinine_ratio = None
            self.albumin_creatinine_ratio_date = None
            self.albuminuria_stage = None
            self.total_cholesterol = None
            self.total_cholesterol_date = None
            self.thyroid_function_date = None
            self.thyroid_treatment_status = None
            self.coeliac_screen_date = None
            self.gluten_free_diet = None
            self.smoking_status = None
            self.smoking_cessation_referral_date = None
            self.carbohydrate_counting_level_three_education_date = None
            self.flu_immunisation_recommended_date = None
            self.ketone_meter_training = None
            self.sick_day_rules_training_date = None

        if visit_type == VisitType.DIETICIAN:
            (
                self.dietician_additional_appointment_offered,
                self.dietician_additional_appointment_date,
            ) = self._dietician_observations()
        else:
            self.dietician_additional_appointment_offered = None
            self.dietician_additional_appointment_date = None

        if visit_type == VisitType.PSYCHOLOGY:
            (
                self.psychological_screening_assessment_date,
                self.psychological_additional_support_status,
            ) = self._psychological_observations()
        else:
            self.psychological_screening_assessment_date = None
            self.psychological_additional_support_status = None

        if visit_type == VisitType.HOSPITAL_ADMISSION:
            (
                self.hospital_admission_date,
                self.hospital_discharge_date,
                self.hospital_admission_reason,
                self.dka_additional_therapies,
                self.hospital_admission_other,
            ) = self._hospital_admission_observations()
        else:
            self.hospital_admission_date = None
            self.hospital_discharge_date = None
            self.hospital_admission_reason = None
            self.dka_additional_therapies = None
            self.hospital_admission_other = None

        # set the attendance as valid
        self.is_valid = True
        self.errors = []

        """
        Private methods to generate random values for the observations. 
        Some of these methods are specific to the age range of the child or the diabetes type or the level of diabetes control they have.
        """

    def _clinic_measures(self, age_range: AgeRange):
        """
        Gather all the measures for a clinic visit. These include height, weight, HbA1c, treatment, CGM, and BP.
        """
        height, weight, height_weight_observation_date = (
            self._height_weight_observations(age_range)
        )
        hba1c, hba1c_format, hba1c_date = self._hba1c_observations(
            hba1_target_range=self.hba1_target_range
        )
        glucose_monitoring = self._continuous_glucose_monitoring_observations()
        treatment, closed_loop_system = self._treatment_observations()
        (
            diastolic_blood_pressure,
            systolic_blood_pressure,
            blood_pressure_observation_date,
        ) = self._bp_observations(age_range)
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

    def _annual_review_measures(self):
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
        foot_examination_observation_date = self._foot_observations()
        retinal_screening_result, retinal_screening_observation_date = (
            self._decs_observations()
        )
        (
            albumin_creatinine_ratio,
            albumin_creatinine_ratio_date,
            albuminuria_stage,
        ) = self._acr_observations()
        total_cholesterol, total_cholesterol_date = self._cholesterol_observations()
        thyroid_function_date, thyroid_treatment_status = self._thyroid_observations()
        coeliac_screen_date, gluten_free_diet = self._coeliac_observations()
        smoking_status, smoking_cessation_referral_date = self._smoking_observations()
        carbohydrate_counting_level_three_education_date = (
            self._carbohydrate_counting_observations()
        )
        flu_immunisation_recommended_date = self._flu_immunisation_observations()
        ketone_meter_training = self._ketone_meter_observations()
        sick_day_rules_training_date = self._sick_day_rules_observations()

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

    def _height_weight_observations(self, age_range: AgeRange):
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
            self.visit_date
        )  # set the date of the observation to the visit date
        return height, weight, height_weight_observation_date

    def _hba1c_observations(
        self, hba1_target_range: str = ["target", "above", "well-above"]
    ):
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
        hba1c_date = self.visit_date
        return hba1c, hba1c_format, hba1c_date

    def _continuous_glucose_monitoring_observations(self):
        """
        Generates random continuous glucose monitoring observations for a child.
        Allocate the visit date to the date of the observation.
        """
        glucose_monitoring = random.choice(GLUCOSE_MONITORING_TYPES)[0]
        return glucose_monitoring

    def _treatment_observations(self):
        """
        Generates random treatment observations for a child.
        Use the diabetes type to determine the range of values for treatment.
        Allocate the visit date to the date of the observation.
        """
        if self.patient.diabetes_type == 1:
            treatment = random.choice(TREATMENT_TYPES[0:6])[0]  # MDI or pump options
        else:
            treatment = random.choice(
                [1, 2, 4, 5, 7, 8, 9]
            )  # insulin or non-insulin options compatible with type 2 diabetes

        if self.patient.diabetes_type == 1:
            closed_loop_system = random.choice([True, False])
        else:
            closed_loop_system = YES_NO_UNKNOWN[0][0]  # No

        return treatment, closed_loop_system

    def _bp_observations(self, age_range: AgeRange):
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
        blood_pressure_observation_date = self.visit_date
        return (
            diastolic_blood_pressure,
            systolic_blood_pressure,
            blood_pressure_observation_date,
        )

    def _foot_observations(self):
        """
        Generates random foot examination observations for a child.
        Allocate the visit date to the date of the observation.
        """
        foot_examination_observation_date = self.visit_date
        return foot_examination_observation_date

    def _decs_observations(self):
        """
        Generates random DECS observations for a child.
        Allocate the visit date to the date of the observation.
        """
        retinal_screening_observation_date = self.visit_date
        retinal_screening_result = random.choice(RETINAL_SCREENING_RESULTS)[0]
        return retinal_screening_result, retinal_screening_observation_date

    def _acr_observations(self):
        """
        Generates random ACR observations for a child.
        Allocate the visit date to the date of the observation.
        """
        albumin_creatinine_ratio = random.randint(0, 300)
        albumin_creatinine_ratio_date = self.visit_date
        albuminuria_stage = random.choice(ALBUMINURIA_STAGES)[0]
        return (
            albumin_creatinine_ratio,
            albumin_creatinine_ratio_date,
            albuminuria_stage,
        )

    def _cholesterol_observations(self):
        """
        Generates random cholesterol observations for a child.
        Allocate the visit date to the date of the observation.
        """
        total_cholesterol = round(random.uniform(2, 7), 2)
        total_cholesterol_date = self.visit_date
        return total_cholesterol, total_cholesterol_date

    def _thyroid_observations(self):
        """
        Generates random thyroid function observations for a child.
        Allocate the visit date to the date of the observation.
        """
        thyroid_function_date = self.visit_date
        thyroid_treatment_status = random.choice(THYROID_TREATMENT_STATUS)[0]
        return thyroid_function_date, thyroid_treatment_status

    def _coeliac_observations(self):
        """
        Generates random coeliac screening observations for a child.
        Allocate the visit date to the date of the observation.
        """
        coeliac_screen_date = self.visit_date
        gluten_free_diet = random.choice(YES_NO_UNKNOWN)[0]
        return coeliac_screen_date, gluten_free_diet

    def _psychological_observations(self):
        """
        Generates random psychological screening observations for a child.
        Allocate the visit date to the date of the observation.
        """
        psychological_screening_assessment_date = self.visit_date
        psychological_additional_support_status = random.choice(YES_NO_UNKNOWN)[0]
        return (
            psychological_screening_assessment_date,
            psychological_additional_support_status,
        )

    def _smoking_observations(self):
        """
        Generates random smoking status observations for a child.
        Allocate the visit date to the date of the observation.
        """
        smoking_status = random.choice(SMOKING_STATUS)[0]
        smoking_cessation_referral_date = self.visit_date
        return smoking_status, smoking_cessation_referral_date

    def _carbohydrate_counting_observations(self):
        """
        Generates random carbohydrate counting observations for a child.
        Allocate the visit date to the date of the observation.
        """
        carbohydrate_counting_level_three_education_date = self.visit_date
        return carbohydrate_counting_level_three_education_date

    def _dietician_observations(self):
        """
        Generates random dietician observations for a child.
        Allocate the visit date to the date of the observation.
        """
        dietician_additional_appointment_offered = random.choice(YES_NO_UNKNOWN)[0]
        dietician_additional_appointment_date = self.visit_date
        return (
            dietician_additional_appointment_offered,
            dietician_additional_appointment_date,
        )

    def _flu_immunisation_observations(self):
        """
        Generates random flu immunisation observations for a child.
        Allocate the visit date to the date of the observation.
        """
        flu_immunisation_recommended_date = self.visit_date
        return flu_immunisation_recommended_date

    def _ketone_meter_observations(self):
        """
        Generates random ketone meter observations for a child.
        """
        ketone_meter_training = random.choice(YES_NO_UNKNOWN)[0]
        return ketone_meter_training

    def _sick_day_rules_observations(self):
        """
        Generates random sick day rules observations for a child.
        Allocate the visit date to the date of the observation.
        """
        sick_day_rules_training_date = self.visit_date
        return sick_day_rules_training_date

    def _hospital_admission_observations(self):
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

    def _random_date(self, start_date, end_date):
        """
        Returns a random date between the start and end dates.
        """
        random_days = random.randint(0, (end_date - start_date).days)
        return start_date + relativedelta(days=random_days)

    def age_range(self, patient):
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
