# Standard imports
import pytest
import logging
import dataclasses
from unittest.mock import Mock, patch
from unittest import skip

# 3rd Party imports
from django.apps import apps
from django.core.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

# NPDA Imports
from project.npda.models import Patient, Transfer
from project.npda.forms.patient_form import PatientForm
from project.npda.forms.external_patient_validators import (
    PatientExternalValidationResult,
)
from project.npda.tests.factories.patient_factory import (
    TODAY,
    VALID_FIELDS,
    VALID_FIELDS_WITH_GP_POSTCODE,
    INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE,
    PATIENT_LOCATION_BNG,
    PATIENT_LOCATION_WGS84
)
from project.npda.tests.factories import PaediatricsDiabetesUnitFactory

# Logging
logger = logging.getLogger(__name__)


MOCK_EXTERNAL_VALIDATION_RESULT = PatientExternalValidationResult(
    postcode=VALID_FIELDS["postcode"],
    gp_practice_ods_code=VALID_FIELDS["gp_practice_ods_code"],
    gp_practice_postcode=VALID_FIELDS_WITH_GP_POSTCODE["gp_practice_postcode"],
    index_of_multiple_deprivation_quintile=INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE,
    location_bng=PATIENT_LOCATION_BNG,
    location_wgs84=PATIENT_LOCATION_WGS84,
)

ALDER_HEY_PZ_CODE = "PZ074"


@pytest.fixture
def mocked_pdu():
    return PaediatricsDiabetesUnitFactory(pz_code=ALDER_HEY_PZ_CODE)


@pytest.fixture
def mocked_audit_year():
    return 2024


def mock_external_validation_result(**kwargs):
    return Mock(
        return_value=dataclasses.replace(MOCK_EXTERNAL_VALIDATION_RESULT, **kwargs)
    )


# We don't want to call remote services in unit tests
@pytest.fixture(autouse=True)
def mock_remote_calls():
    with patch(
        "project.npda.forms.patient_form.validate_patient_sync",
        Mock(return_value=MOCK_EXTERNAL_VALIDATION_RESULT),
    ):
        yield None


@pytest.mark.django_db
def test_create_patient(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu, audit_year=mocked_audit_year
    )
    assert len(form.errors.as_data()) == 0


@pytest.mark.django_db
def test_create_patient_with_death_date(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        VALID_FIELDS
        | {"death_date": VALID_FIELDS["diagnosis_date"] + relativedelta(years=1)},
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )

    assert len(form.errors.as_data()) == 0


@pytest.mark.django_db
def test_missing_nhs_number(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {}, paediatric_diabetes_unit=mocked_pdu, audit_year=mocked_audit_year
    )
    assert "nhs_number" in form.errors.as_data()


@pytest.mark.django_db
def test_invalid_nhs_number(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {"nhs_number": "123456789"},
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )

    assert "nhs_number" in form.errors.as_data()


@pytest.mark.django_db
def test_date_of_birth_missing(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {}, paediatric_diabetes_unit=mocked_pdu, audit_year=mocked_audit_year
    )
    assert "date_of_birth" in form.errors.as_data()


@pytest.mark.django_db
def test_future_date_of_birth(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {"date_of_birth": TODAY + relativedelta(days=1)},
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )

    errors = form.errors.as_data()
    assert "date_of_birth" in errors

    error_message = errors["date_of_birth"][0].messages[0]
    assert error_message == "Cannot be in the future"


@pytest.mark.django_db
def test_over_25(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {"date_of_birth": TODAY - relativedelta(years=25, days=1)},
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )

    errors = form.errors.as_data()
    assert "date_of_birth" in errors

    error_message = errors["date_of_birth"][0].messages[0]
    assert error_message == "NPDA patients cannot be 25+ years old. This patient is 25"


@pytest.mark.django_db
def test_missing_diabetes_type(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {}, paediatric_diabetes_unit=mocked_pdu, audit_year=mocked_audit_year
    )
    assert "diabetes_type" in form.errors.as_data()


@pytest.mark.django_db
def test_invalid_diabetes_type(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {"diabetes_type": 45},
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )

    assert "diabetes_type" in form.errors.as_data()


@pytest.mark.django_db
def test_missing_diagnosis_date(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {}, paediatric_diabetes_unit=mocked_pdu, audit_year=mocked_audit_year
    )
    assert "diagnosis_date" in form.errors.as_data()


@pytest.mark.django_db
def test_future_diagnosis_date(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {"diagnosis_date": TODAY + relativedelta(days=1)},
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )

    errors = form.errors.as_data()
    assert "diagnosis_date" in errors

    error_message = errors["diagnosis_date"][0].messages[0]
    assert error_message == "Cannot be in the future"


@pytest.mark.django_db
def test_diagnosis_date_before_date_of_birth(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {
            "date_of_birth": VALID_FIELDS["date_of_birth"],
            "diagnosis_date": VALID_FIELDS["date_of_birth"] - relativedelta(years=1),
        },
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )

    errors = form.errors.as_data()
    assert "diagnosis_date" in errors

    error_message = errors["diagnosis_date"][0].messages[0]
    assert (
        error_message == "'Date of Diabetes Diagnosis' cannot be before 'Date of Birth'"
    )


@pytest.mark.django_db
def test_invalid_sex(mocked_pdu, mocked_audit_year):
    form = PatientForm({"sex": 45})

    assert "sex" in form.errors.as_data()


@pytest.mark.django_db
def test_invalid_ethnicity(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {"ethnicity": 45},
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )

    assert "ethnicity" in form.errors.as_data()


@pytest.mark.django_db
def test_missing_gp_details(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {}, paediatric_diabetes_unit=mocked_pdu, audit_year=mocked_audit_year
    )

    errors = form.errors.as_data()
    assert "gp_practice_ods_code" in errors

    error_message = errors["gp_practice_ods_code"][0].messages[0]
    assert (
        error_message
        == "'GP Practice ODS code' and 'GP Practice postcode' cannot both be empty"
    )


@pytest.mark.django_db
def test_patient_creation_with_future_death_date(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {"death_date": TODAY + relativedelta(years=1)},
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )

    errors = form.errors.as_data()
    assert "death_date" in errors

    error_message = errors["death_date"][0].messages[0]
    assert error_message == "Cannot be in the future"


@pytest.mark.django_db
def test_patient_creation_with_death_date_before_date_of_birth(
    mocked_pdu, mocked_audit_year
):
    form = PatientForm(
        {
            "date_of_birth": VALID_FIELDS["date_of_birth"],
            "death_date": VALID_FIELDS["date_of_birth"] - relativedelta(years=1),
        },
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )

    errors = form.errors.as_data()
    assert "death_date" in errors

    error_message = errors["death_date"][0].messages[0]
    assert error_message == "'Death Date' cannot be before 'Date of Birth'"


@pytest.mark.django_db
def test_multiple_date_validation_errors_returned(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {
            "date_of_birth": VALID_FIELDS["date_of_birth"],
            "diagnosis_date": VALID_FIELDS["date_of_birth"] - relativedelta(years=1),
            "death_date": VALID_FIELDS["date_of_birth"] - relativedelta(years=1),
        },
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )

    errors = form.errors.as_data()

    assert "death_date" in errors
    assert "diagnosis_date" in errors


@pytest.mark.django_db
def test_spaces_removed_from_postcode(mocked_pdu, mocked_audit_year):
    with patch(
        "project.npda.forms.patient_form.validate_patient_sync"
    ) as mock_validate_patient_sync:
        form = PatientForm(
            VALID_FIELDS
            | {
                "postcode": "WC1X 8SH",
            },
            paediatric_diabetes_unit=mocked_pdu,
            audit_year=mocked_audit_year,
        )

        form.is_valid()

        mock_validate_patient_sync.assert_called_once_with(
            postcode="WC1X8SH",
            gp_practice_ods_code=VALID_FIELDS["gp_practice_ods_code"],
            gp_practice_postcode=None,
        )


@pytest.mark.django_db
def test_dashes_removed_from_postcode(mocked_pdu, mocked_audit_year):
    with patch(
        "project.npda.forms.patient_form.validate_patient_sync"
    ) as mock_validate_patient_sync:
        form = PatientForm(
            VALID_FIELDS
            | {
                "postcode": "WC1X-8SH",
            },
            paediatric_diabetes_unit=mocked_pdu,
            audit_year=mocked_audit_year,
        )

        form.is_valid()

        mock_validate_patient_sync.assert_called_once_with(
            postcode="WC1X8SH",
            gp_practice_ods_code=VALID_FIELDS["gp_practice_ods_code"],
            gp_practice_postcode=None,
        )


@pytest.mark.django_db
@patch(
    "project.npda.forms.patient_form.validate_patient_sync",
    mock_external_validation_result(postcode="W1A 1AA"),
)
def test_normalised_postcode_saved(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu, audit_year=mocked_audit_year
    )
    form.is_valid()

    assert form.cleaned_data["postcode"] == "W1A 1AA"


@pytest.mark.django_db
@patch(
    "project.npda.forms.patient_form.validate_patient_sync",
    mock_external_validation_result(postcode=ValidationError("Invalid postcode")),
)
def test_invalid_postcode(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu, audit_year=mocked_audit_year
    )
    form.is_valid()

    assert "postcode" in form.errors.as_data()


@pytest.mark.django_db
@patch(
    "project.npda.forms.patient_form.validate_patient_sync",
    mock_external_validation_result(postcode=None),
)
def test_error_validating_postcode(mocked_pdu, mocked_audit_year):
    # TODO MRB: report this back somehow rather than just eat it in the log? (https://github.com/rcpch/national-paediatric-diabetes-audit/issues/334)
    form = PatientForm(
        VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu, audit_year=mocked_audit_year
    )
    form.is_valid()

    assert len(form.errors.as_data()) == 0


@pytest.mark.django_db
@patch(
    "project.npda.forms.patient_form.validate_patient_sync",
    mock_external_validation_result(
        gp_practice_postcode=ValidationError("Invalid postcode")
    ),
)
def test_invalid_gp_postcode(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        VALID_FIELDS_WITH_GP_POSTCODE,
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )
    form.is_valid()

    assert "gp_practice_postcode" in form.errors.as_data()


@pytest.mark.django_db
@patch(
    "project.npda.forms.patient_form.validate_patient_sync",
    mock_external_validation_result(gp_practice_postcode=None),
)
def test_error_validating_gp_postcode(mocked_pdu, mocked_audit_year):
    # TODO MRB: report this back somehow rather than just eat it in the log? (https://github.com/rcpch/national-paediatric-diabetes-audit/issues/334)
    form = PatientForm(
        VALID_FIELDS_WITH_GP_POSTCODE,
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )
    form.is_valid()

    assert len(form.errors.as_data()) == 0


@pytest.mark.django_db
@patch(
    "project.npda.forms.patient_form.validate_patient_sync",
    mock_external_validation_result(
        gp_practice_ods_code=ValidationError("Invalid ODS code")
    ),
)
def test_invalid_gp_ods_code(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu, audit_year=mocked_audit_year
    )
    form.is_valid()

    assert "gp_practice_ods_code" in form.errors.as_data()


@pytest.mark.django_db
@patch(
    "project.npda.forms.patient_form.validate_patient_sync",
    mock_external_validation_result(gp_practice_ods_code=None),
)
def test_error_validating_gp_ods_code(mocked_pdu, mocked_audit_year):
    # TODO MRB: report this back somehow rather than just eat it in the log? (https://github.com/rcpch/national-paediatric-diabetes-audit/issues/334)
    form = PatientForm(
        VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu, audit_year=mocked_audit_year
    )
    form.is_valid()

    assert len(form.errors.as_data()) == 0


@pytest.mark.django_db
def test_lookup_index_of_multiple_deprivation(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu, audit_year=mocked_audit_year
    )

    form.is_valid()
    assert len(form.errors.as_data()) == 0

    patient = form.save()
    assert (
        patient.index_of_multiple_deprivation_quintile
        == INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE
    )


@pytest.mark.django_db
def test_lookup_location(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu, audit_year=mocked_audit_year
    )

    form.is_valid()
    assert len(form.errors.as_data()) == 0

    patient = form.save()
    assert patient.location_wgs84 == PATIENT_LOCATION_WGS84
    assert patient.location_bng == PATIENT_LOCATION_BNG


@pytest.mark.django_db
@patch(
    "project.npda.forms.patient_form.validate_patient_sync",
    mock_external_validation_result(index_of_multiple_deprivation_quintile=None),
)
def test_error_looking_up_index_of_multiple_deprivation(mocked_pdu, mocked_audit_year):
    # TODO MRB: report this back somehow rather than just eat it in the log? (https://github.com/rcpch/national-paediatric-diabetes-audit/issues/334)
    form = PatientForm(
        VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu, audit_year=mocked_audit_year
    )
    form.is_valid()

    patient = form.save()

    patient.index_of_multiple_deprivation_quintile = None


@pytest.mark.django_db
def test_date_leaving_service_missing(mocked_pdu, mocked_audit_year):
    # Date leaving service is required if reason leaving service is provided
    form = PatientForm(
        {"reason_leaving_service": 1},
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )
    assert "date_leaving_service" in form.errors.as_data()


@pytest.mark.django_db
def test_date_leaving_service_future(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {"date_leaving_service": TODAY + relativedelta(days=1)},
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )

    errors = form.errors.as_data()
    assert "date_leaving_service" in errors

    error_message = errors["date_leaving_service"][0].messages[0]
    assert error_message == "Cannot be in the future"


@pytest.mark.django_db
def test_date_leaving_service_before_diagnosis_date(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {
            "diagnosis_date": VALID_FIELDS["diagnosis_date"],
            "date_leaving_service": VALID_FIELDS["diagnosis_date"]
            - relativedelta(years=1),
        },
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )

    errors = form.errors.as_data()
    assert "date_leaving_service" in errors

    error_message = errors["date_leaving_service"][0].messages[0]
    assert (
        error_message
        == "'Date Leaving Service' cannot be before 'Date of Diabetes Diagnosis'"
    )


@pytest.mark.django_db
def test_date_leaving_service_before_date_of_birth(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {
            "date_of_birth": VALID_FIELDS["date_of_birth"],
            "date_leaving_service": VALID_FIELDS["date_of_birth"]
            - relativedelta(years=1),
        },
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )

    errors = form.errors.as_data()
    assert "date_leaving_service" in errors

    error_message = errors["date_leaving_service"][0].messages[0]
    assert error_message == "'Date Leaving Service' cannot be before 'Date of Birth'"


@pytest.mark.django_db
def test_reason_leaving_service_missing(mocked_pdu, mocked_audit_year):
    # Reason leaving service is required if date leaving service is provided
    form = PatientForm(
        {"date_leaving_service": TODAY},
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )
    assert "reason_leaving_service" in form.errors.as_data()


@pytest.mark.django_db
def test_reason_leaving_service_invalid(mocked_pdu, mocked_audit_year):
    form = PatientForm(
        {"reason_leaving_service": 99},
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
    )
    assert "reason_leaving_service" in form.errors.as_data()


@skip("This test is failing")
@pytest.mark.django_db
@patch(
    "project.npda.forms.patient_form.validate_patient_sync",
    mock_external_validation_result(index_of_multiple_deprivation_quintile=None),
)
def test_successful_patient_transfer(mocked_pdu, mocked_audit_year):
    # Create patient
    patient = Patient.objects.create(
        **VALID_FIELDS,
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year
    )

    # Update patient
    form = PatientForm(
        VALID_FIELDS | {"reason_leaving_service": 1, "date_leaving_service": TODAY},
        instance=patient,
    )

    patient = form.save()

    transfer = Transfer.objects.get(patient=patient)

    assert len(form.errors.as_data()) == 0
    assert form.is_valid()
    # assert form.save().date_leaving_service == TODAY
    # assert form.save().reason_leaving_service == 1
    assert transfer.patient == patient
    assert transfer.date_leaving_service == TODAY
    assert transfer.reason_leaving_service == 1


@pytest.mark.django_db
def test_fail_validation_if_same_patient_twice_in_same_submission(
    mocked_pdu,
    mocked_audit_year,
    seed_groups_fixture,
    seed_users_fixture,
):
    NPDAUser = apps.get_model("npda", "NPDAUser")
    pdu_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=mocked_pdu.pz_code
    ).first()

    form = PatientForm(
        VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu, audit_year=mocked_audit_year
    )
    assert len(form.errors.as_data()) == 0
    patient = form.save()

    # add the patient to a submission
    Submission = apps.get_model("npda", "Submission")
    submission = Submission.objects.create(
        paediatric_diabetes_unit=mocked_pdu,
        audit_year=mocked_audit_year,
        submission_active=True,
        submission_date=TODAY,
        submission_by=pdu_user,
    )
    submission.patients.add(patient)

    # Create a new form with the same patient
    new_form = PatientForm(
        VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu, audit_year=mocked_audit_year
    )
    new_form.is_valid()

    assert "nhs_number" in new_form.errors.as_data()
