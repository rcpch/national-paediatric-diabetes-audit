"""Factory fn to create new Patient.
"""

# standard imports
from datetime import date
import logging

# third-party imports
import factory
import nhs_number

# rcpch imports
from project.npda.models import Patient
from .TransferFactory import TransferFactory
from project.constants import (
    ETHNICITIES,
    DIABETES_TYPES,
    SEX_TYPE,
    UNKNOWN_POSTCODES_NO_SPACES,
    CAN_LOCK_CHILD_PATIENT_DATA_FROM_EDITING,
    CAN_UNLOCK_CHILD_PATIENT_DATA_FROM_EDITING,
    CAN_OPT_OUT_CHILD_FROM_INCLUSION_IN_AUDIT,
)

# Logging
logger = logging.getLogger(__name__)


class PatientFactory(factory.django.DjangoModelFactory):
    """Dependency factory for creating a minimum viable Patient.

    Fills in default values if not specified at object creation.
    """

    class Meta:
        model = Patient

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

    sex = SEX_TYPE[2][0]  # Female
    date_of_birth = date(2005, 1, 1)
    postcode = "NW1 2DB"  # The Alan Turing Institute
    ethnicity = ETHNICITIES[0][0]  # African
    diabetes_type = DIABETES_TYPES[0][0]  # Type 1 Insulin-Dependent Diabetes Mellitus
    diagnosis_date = date(2020, 1, 1)

    gp_practice_ods_code = "RP401"

    transfer = factory.SubFactory(
        TransferFactory,
    )
