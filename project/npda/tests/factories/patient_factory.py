"""Factory fn to create new Patient.
"""

# standard imports
from datetime import date
import logging

# third-party imports
import factory
import nhs_number
from dateutil.relativedelta import relativedelta

# rcpch imports
from project.npda.models import Patient
from .transfer_factory import TransferFactory
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


TODAY = date.today()
DATE_OF_BIRTH = TODAY - relativedelta(years=10)

VALID_FIELDS = {
    "nhs_number": "6239431915",
    "sex": SEX_TYPE[0][0],
    "date_of_birth": TODAY - relativedelta(years=10),
    "postcode": "NW1 2DB",
    "ethnicity":  ETHNICITIES[0][0],
    "diabetes_type":  DIABETES_TYPES[0][0],
    "diagnosis_date": DATE_OF_BIRTH + relativedelta(years=8),
    "gp_practice_ods_code": "G85023"
}

GP_POSTCODE_NO_SPACES = "SE135PJ"
GP_POSTCODE_WITH_SPACES = "SE13 5PJ"

VALID_FIELDS_WITH_GP_POSTCODE = VALID_FIELDS | {
    "gp_practice_ods_code": None,
    "gp_practice_postcode": GP_POSTCODE_WITH_SPACES
}

INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE=4


class PatientFactory(factory.django.DjangoModelFactory):
    """Dependency factory for creating a minimum viable Patient.

    Fills in default values if not specified at object creation.
    """

    class Meta:
        model = Patient
        skip_postgeneration_save=True

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

    sex = VALID_FIELDS["sex"]
    date_of_birth = VALID_FIELDS["date_of_birth"]
    postcode = VALID_FIELDS["postcode"]
    ethnicity = VALID_FIELDS["ethnicity"]
    diabetes_type = VALID_FIELDS["diabetes_type"]
    diagnosis_date = VALID_FIELDS["diagnosis_date"]

    gp_practice_ods_code = VALID_FIELDS["gp_practice_ods_code"]

    # Once a Patient is created, we must create a Transfer object
    transfer = factory.RelatedFactory(
        TransferFactory,
        factory_related_name='patient'
    )
