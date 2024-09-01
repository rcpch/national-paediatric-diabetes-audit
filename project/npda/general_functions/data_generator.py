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
from project.constants import SEX_TYPE, DIABETES_TYPES, ETHNICITIES


# create an Enum for the range of ages
class AgeRange(Enum):
    """
    Enum class to represent the range of ages for children.
    """

    AGE_0_4 = 0
    AGE_5_10 = 1
    AGE_11_15 = 2
    AGE_16_19 = 3
    AGE_20_25 = 4


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
        Patient = apps.get_model("npda", "Patient")

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
        self.sex = (sex if sex is not None else self.sex,)
        # self.date_of_birth=self.date_of_birth,
        # self.diagnosis_date=self.diagnosis_date,
        # self.diabetes_type=self.diabetes_type,
        self.death_date = (death_date,)
        self.nhs_number = (
            nhs_number.generate(quantity=1, for_region=nhs_number.REGION_ENGLAND),
        )
        # self.ethnicity=self.ethnicity,
        self.index_of_multiple_deprivation_quintile = (random.randint(1, 5),)
        self.gp_practice_ods_code = ("G85004",)  # random gp_practice_ods_code
        self.gp_practice_postcode = ("SE23 1HU",)  # random gp_practice_postcode
        self.is_valid = (True,)
        self.errors = ([],)

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
