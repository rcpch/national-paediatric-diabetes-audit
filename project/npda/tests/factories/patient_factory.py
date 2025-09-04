"""Factory fn to create new Patient.
"""

# standard imports
from datetime import date, datetime
from enum import Enum
import logging
import random

# third-party imports
from django.contrib.gis.geos import Point
import factory
import nhs_number
from dateutil.relativedelta import relativedelta

# rcpch imports
from project.npda.general_functions.audit_period import get_audit_period_for_date
from project.npda.general_functions.random_date import get_random_date
from project.npda.models import Patient
from project.npda.tests.factories.visit_factory import VisitFactory
from project.npda.general_functions.validate_postcode import ValidatedPostcode, random_postcode_under_outcode_sync
from .transfer_factory import TransferFactory
from project.constants import (
    ETHNICITIES,
    DIABETES_TYPES,
    SEX_TYPE,
)

# Logging
logger = logging.getLogger(__name__)


TODAY = date.today()
DATE_OF_BIRTH = TODAY - relativedelta(years=10)

GP_POSTCODE_NO_SPACES = "SE135PJ"
GP_POSTCODE_WITH_SPACES = "SE13 5PJ"

VALID_GP_POSTCODE = ValidatedPostcode(
    normalised_postcode=GP_POSTCODE_WITH_SPACES,
    lon=0.004522,
    lat=51.458513
)

JERSEY_GP_POSTCODE_NO_SPACES = "JE27LA"
JERSEY_GP_POSTCODE_WITH_SPACES = "JE2 7LA"

VALID_JERSEY_GP_POSTCODE = ValidatedPostcode(
    normalised_postcode=JERSEY_GP_POSTCODE_WITH_SPACES,
    lon=-2.0968,
    lat=49.1909
)

PATIENT_POSTCODE_WITH_SPACES = "NW1 2DB"
PATIENT_POSTCODE_NO_SPACES = "NW12DB"

VALID_PATIENT_POSTCODE = ValidatedPostcode(
    normalised_postcode=PATIENT_POSTCODE_WITH_SPACES,
    lon=-0.127014,
    lat=51.529985,
)

JERSEY_PATIENT_POSTCODE_NO_SPACES = "JE17XP"
JERSEY_PATIENT_POSTCODE_WITH_SPACES = "JE1 7XP"

VALID_JERSEY_PATIENT_POSTCODE = ValidatedPostcode(
    normalised_postcode=JERSEY_PATIENT_POSTCODE_WITH_SPACES,
    lon=-2.0955,
    lat=49.1908
)

VALID_FIELDS = {
    "nhs_number": "6239431915",
    "sex": SEX_TYPE[0][0],
    "date_of_birth": TODAY - relativedelta(years=10),
    "postcode": VALID_PATIENT_POSTCODE.normalised_postcode,
    "ethnicity": ETHNICITIES[0][0],
    "diabetes_type": DIABETES_TYPES[0][0],
    "diagnosis_date": DATE_OF_BIRTH + relativedelta(years=8),
    "gp_practice_ods_code": "G85023",
    "location_bng": VALID_PATIENT_POSTCODE.location_bng,
    "location_wgs84": VALID_PATIENT_POSTCODE.location_wgs84,
}

VALID_FIELDS_WITH_GP_POSTCODE = VALID_FIELDS | {
    "gp_practice_ods_code": None,
    "gp_practice_postcode": VALID_GP_POSTCODE.normalised_postcode,
}

INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE = 4


class AgeRange(Enum):
    """
    Enum class to represent the range of ages for children.
    """

    AGE_0_4 = (0, 4)
    AGE_5_10 = (5, 10)
    AGE_11_15 = (11, 15)
    AGE_16_19 = (16, 19)
    AGE_20_25 = (20, 25)


class Sex(Enum):
    """
    Enum class to represent sexes for children
    """
    MALE = SEX_TYPE[0][0]
    FEMALE = SEX_TYPE[1][0]
    # Removed not known and unspecified just to make demo files map clearer
    # Patients not specified as male or female are omitted from the reports


class PatientFactory(factory.django.DjangoModelFactory):
    """Dependency factory for creating a minimum viable Patient.

    Fills in default values if not specified at object creation.
    """

    class Meta:
        model = Patient
        skip_postgeneration_save = True

    gp_practice_ods_code = VALID_FIELDS["gp_practice_ods_code"]

    diabetes_type = DIABETES_TYPES[0][0]
    sex = factory.lazy_attribute(lambda x: random.choice([sex.value for sex in Sex]))
    ethnicity = factory.lazy_attribute(lambda x: random.choice(ETHNICITIES)[0])

    @factory.lazy_attribute
    def nhs_number(self):
        """Returns a unique NHS number which has not been used in the db yet."""

        # First generate 5 numbers and check if they exist in the db
        candidate_nums = nhs_number.generate(
            quantity=5, for_region=nhs_number.REGION_ENGLAND
        )

        not_found_unique_nhs_number = True
        while not_found_unique_nhs_number:
            for nhs_num in candidate_nums:
                if not Patient.objects.filter(nhs_number=nhs_num).exists():
                    not_found_unique_nhs_number = False
                    return nhs_num

            # If all 5 numbers are already in the db, generate 5 more
            candidate_nums = nhs_number.generate(
                quantity=5, for_region=nhs_number.REGION_ENGLAND
            )

    @factory.lazy_attribute
    def unique_reference_number(self):
        """Returns a unique reference number which has not been used in the db yet."""
        unique_reference_number = random.randint(100000, 999999)
        while Patient.objects.filter(
            unique_reference_number=unique_reference_number
        ).exists():
            unique_reference_number = random.randint(100000, 999999)
        return unique_reference_number

    @factory.lazy_attribute
    def date_of_birth(self):
        """Set date_of_birth based on the selected age_range."""
        min_age, max_age = self.age_range.value

        # Has to be at least 0 years old to be in the audit
        today = self.audit_start_date
        # Pick a random age within the range
        age = random.randint(min_age, max_age)

        # if 0 years, then age needs to be in months (minimum 1 month)
        if age == 0:
            age = random.randint(1, 11)
            return today - relativedelta(months=age)
        else:
            # Otherwise, age is in years
            return today - relativedelta(years=age)

    @factory.lazy_attribute
    def diagnosis_date(self):
        """Set diagnosis_date between date_of_birth and audit end date."""
        ret = get_random_date(
            start_date=self.date_of_birth, end_date=self.latest_diagnosis_date or self.audit_start_date
        )
        return ret
    
    @factory.lazy_attribute
    def postcode(self):
        if self.postcode_outcode:
            return random_postcode_under_outcode_sync(self.postcode_outcode).normalised_postcode

        return VALID_FIELDS["postcode"]

    # Once a Patient is created, we must create a Transfer object
    transfer = factory.RelatedFactory(TransferFactory, factory_related_name="patient")

    # We also create a Visit object
    visit = factory.RelatedFactory(
        VisitFactory,
        factory_related_name="patient",
    )

    # Attributes to control factory behavior
    class Params:
        audit_start_date = get_audit_period_for_date(TODAY)[
            0
        ]  # Default audit_start_date; can be overridden
        audit_end_date = get_audit_period_for_date(TODAY)[
            1
        ]  # Default audit_end_date; can be overridden
        
        # Opt in to generating patients diagnosed in audit year
        # Can't reference audit_end_date as a default in case overridden
        latest_diagnosis_date = None

        age_range = AgeRange.AGE_11_15  # Default age range

        # Random postcode under given outcode
        postcode_outcode = None
