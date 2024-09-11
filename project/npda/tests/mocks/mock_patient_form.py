from unittest.mock import Mock
from project.npda.forms.patient_form import PatientFormWithSynchronousRemoteCalls

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