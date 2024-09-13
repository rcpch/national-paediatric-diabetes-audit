from datetime import date
from unittest.mock import Mock

from dateutil.relativedelta import relativedelta

from project.constants import (
    ETHNICITIES,
    DIABETES_TYPES,
    SEX_TYPE,
)
from project.npda.forms.patient_form import PatientFormWithSynchronousRemoteCalls

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

VALID_FIELDS_WITH_GP_POSTCODE = VALID_FIELDS | {
    "gp_practice_ods_code": None,
    "gp_practice_postcode": "SE13 5PJ"
}

# We don't want to call remote services during unit tests
def patient_form_with_mock_remote_calls(
    data,
    validate_postcode=Mock(return_value=True),
    gp_details_for_ods_code=Mock(return_value = True),
    gp_ods_code_for_postcode=Mock(return_value = "G85023"),
    imd_for_postcode=Mock(return_value = 4)
):
    return PatientFormWithSynchronousRemoteCalls(
        data,
        validate_postcode=validate_postcode,
        gp_details_for_ods_code=gp_details_for_ods_code,
        gp_ods_code_for_postcode=gp_ods_code_for_postcode,
        imd_for_postcode=imd_for_postcode
    ) 