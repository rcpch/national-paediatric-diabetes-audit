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
)
from project.npda.tests.factories import PaediatricsDiabetesUnitFactory
from project.constants import SEX_TYPE

# Logging
logger = logging.getLogger(__name__)


MOCK_EXTERNAL_VALIDATION_RESULT = PatientExternalValidationResult(
    postcode=VALID_FIELDS["postcode"],
    gp_practice_ods_code=VALID_FIELDS["gp_practice_ods_code"],
    gp_practice_postcode=VALID_FIELDS_WITH_GP_POSTCODE["gp_practice_postcode"],
    index_of_multiple_deprivation_quintile=INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE,
    location_bng=VALID_FIELDS["location_bng"],
    location_wgs84=VALID_FIELDS["location_wgs84"],
)

ALDER_HEY_PZ_CODE = "PZ074"


@pytest.fixture
def mocked_pdu():
    return PaediatricsDiabetesUnitFactory(pz_code=ALDER_HEY_PZ_CODE)


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
def test_create_patient(mocked_pdu):
    form = PatientForm(VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu)
    assert len(form.errors.as_data()) == 0


@pytest.mark.django_db
def test_create_patient_with_death_date(mocked_pdu):
    form = PatientForm(
        VALID_FIELDS
        | {"death_date": VALID_FIELDS["diagnosis_date"] + relativedelta(years=1)},
        paediatric_diabetes_unit=mocked_pdu,
    )

    assert len(form.errors.as_data()) == 0


@pytest.mark.django_db
def test_missing_nhs_number(mocked_pdu):
    form = PatientForm({}, paediatric_diabetes_unit=mocked_pdu)
    assert "nhs_number" in form.errors.as_data()


@pytest.mark.django_db
def test_invalid_nhs_number(mocked_pdu):
    form = PatientForm(
        {"nhs_number": "123456789"},
        paediatric_diabetes_unit=mocked_pdu,
    )

    assert "nhs_number" in form.errors.as_data()


@pytest.mark.django_db
def test_date_of_birth_missing(mocked_pdu):
    form = PatientForm({}, paediatric_diabetes_unit=mocked_pdu)
    assert "date_of_birth" in form.errors.as_data()


@pytest.mark.django_db
def test_future_date_of_birth(mocked_pdu):
    form = PatientForm(
        {"date_of_birth": TODAY + relativedelta(days=1)},
        paediatric_diabetes_unit=mocked_pdu,
    )

    errors = form.errors.as_data()
    assert "date_of_birth" in errors

    error_message = errors["date_of_birth"][0].messages[0]
    assert error_message == "Cannot be in the future"


@pytest.mark.django_db
def test_over_25(mocked_pdu):
    form = PatientForm(
        {"date_of_birth": TODAY - relativedelta(years=25, days=1)},
        paediatric_diabetes_unit=mocked_pdu,
    )

    errors = form.errors.as_data()
    assert "date_of_birth" in errors

    error_message = errors["date_of_birth"][0].messages[0]
    assert error_message == "NPDA patients cannot be 25+ years old. This patient is 25"


@pytest.mark.django_db
def test_missing_diabetes_type(mocked_pdu):
    form = PatientForm({}, paediatric_diabetes_unit=mocked_pdu)
    assert "diabetes_type" in form.errors.as_data()


@pytest.mark.django_db
def test_invalid_diabetes_type(mocked_pdu):
    form = PatientForm(
        {"diabetes_type": 45},
        paediatric_diabetes_unit=mocked_pdu,
    )

    assert "diabetes_type" in form.errors.as_data()


@pytest.mark.django_db
def test_missing_diagnosis_date(mocked_pdu):
    form = PatientForm({}, paediatric_diabetes_unit=mocked_pdu)
    assert "diagnosis_date" in form.errors.as_data()


@pytest.mark.django_db
def test_future_diagnosis_date(mocked_pdu):
    form = PatientForm(
        {"diagnosis_date": TODAY + relativedelta(days=1)},
        paediatric_diabetes_unit=mocked_pdu,
    )

    errors = form.errors.as_data()
    assert "diagnosis_date" in errors

    error_message = errors["diagnosis_date"][0].messages[0]
    assert error_message == "Cannot be in the future"


@pytest.mark.django_db
def test_diagnosis_date_before_date_of_birth(mocked_pdu):
    form = PatientForm(
        {
            "date_of_birth": VALID_FIELDS["date_of_birth"],
            "diagnosis_date": VALID_FIELDS["date_of_birth"] - relativedelta(years=1),
        },
        paediatric_diabetes_unit=mocked_pdu,
    )

    errors = form.errors.as_data()
    assert "diagnosis_date" in errors

    error_message = errors["diagnosis_date"][0].messages[0]
    assert (
        error_message == "'Date of Diabetes Diagnosis' cannot be before 'Date of Birth'"
    )


@pytest.mark.django_db
def test_invalid_sex(mocked_pdu):
    form = PatientForm({"sex": 45})

    assert "sex" in form.errors.as_data()


@pytest.mark.django_db
def test_invalid_ethnicity(mocked_pdu):
    form = PatientForm(
        {"ethnicity": 45},
        paediatric_diabetes_unit=mocked_pdu,
    )

    assert "ethnicity" in form.errors.as_data()


@pytest.mark.django_db
def test_missing_gp_details(mocked_pdu):
    form = PatientForm({}, paediatric_diabetes_unit=mocked_pdu)

    errors = form.errors.as_data()
    assert "gp_practice_ods_code" in errors

    error_message = errors["gp_practice_ods_code"][0].messages[0]
    assert (
        error_message
        == "'GP Practice ODS code' and 'GP Practice postcode' cannot both be empty"
    )


@pytest.mark.django_db
def test_patient_creation_with_future_death_date(mocked_pdu):
    form = PatientForm(
        {"death_date": TODAY + relativedelta(years=1)},
        paediatric_diabetes_unit=mocked_pdu,
    )

    errors = form.errors.as_data()
    assert "death_date" in errors

    error_message = errors["death_date"][0].messages[0]
    assert error_message == "Cannot be in the future"


@pytest.mark.django_db
def test_patient_creation_with_death_date_before_date_of_birth(mocked_pdu):
    form = PatientForm(
        {
            "date_of_birth": VALID_FIELDS["date_of_birth"],
            "death_date": VALID_FIELDS["date_of_birth"] - relativedelta(years=1),
        },
        paediatric_diabetes_unit=mocked_pdu,
    )

    errors = form.errors.as_data()
    assert "death_date" in errors

    error_message = errors["death_date"][0].messages[0]
    assert error_message == "'Death Date' cannot be before 'Date of Birth'"


@pytest.mark.django_db
def test_multiple_date_validation_errors_returned(mocked_pdu):
    form = PatientForm(
        {
            "date_of_birth": VALID_FIELDS["date_of_birth"],
            "diagnosis_date": VALID_FIELDS["date_of_birth"] - relativedelta(years=1),
            "death_date": VALID_FIELDS["date_of_birth"] - relativedelta(years=1),
        },
        paediatric_diabetes_unit=mocked_pdu,
    )

    errors = form.errors.as_data()

    assert "death_date" in errors
    assert "diagnosis_date" in errors


@pytest.mark.django_db
def test_spaces_removed_from_postcode(mocked_pdu):
    with patch(
        "project.npda.forms.patient_form.validate_patient_sync"
    ) as mock_validate_patient_sync:
        form = PatientForm(
            VALID_FIELDS
            | {
                "postcode": "WC1X 8SH",
            },
            paediatric_diabetes_unit=mocked_pdu,
        )

        form.is_valid()

        mock_validate_patient_sync.assert_called_once_with(
            postcode="WC1X8SH",
            gp_practice_ods_code=VALID_FIELDS["gp_practice_ods_code"],
            gp_practice_postcode=None,
        )


@pytest.mark.django_db
def test_dashes_removed_from_postcode(mocked_pdu):
    with patch(
        "project.npda.forms.patient_form.validate_patient_sync"
    ) as mock_validate_patient_sync:
        form = PatientForm(
            VALID_FIELDS
            | {
                "postcode": "WC1X-8SH",
            },
            paediatric_diabetes_unit=mocked_pdu,
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
def test_normalised_postcode_saved(mocked_pdu):
    form = PatientForm(VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu)
    form.is_valid()

    assert form.cleaned_data["postcode"] == "W1A 1AA"


@pytest.mark.django_db
@patch(
    "project.npda.forms.patient_form.validate_patient_sync",
    mock_external_validation_result(postcode=ValidationError("Invalid postcode")),
)
def test_invalid_postcode(mocked_pdu):
    form = PatientForm(VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu)
    form.is_valid()

    assert "postcode" in form.errors.as_data()


@pytest.mark.django_db
@patch(
    "project.npda.forms.patient_form.validate_patient_sync",
    mock_external_validation_result(postcode=None),
)
def test_error_validating_postcode(mocked_pdu):
    # TODO MRB: report this back somehow rather than just eat it in the log? (https://github.com/rcpch/national-paediatric-diabetes-audit/issues/334)
    form = PatientForm(VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu)
    form.is_valid()

    assert len(form.errors.as_data()) == 0


@pytest.mark.django_db
@patch(
    "project.npda.forms.patient_form.validate_patient_sync",
    mock_external_validation_result(
        gp_practice_postcode=ValidationError("Invalid postcode")
    ),
)
def test_invalid_gp_postcode(mocked_pdu):
    form = PatientForm(
        VALID_FIELDS_WITH_GP_POSTCODE,
        paediatric_diabetes_unit=mocked_pdu,
    )
    form.is_valid()

    assert "gp_practice_postcode" in form.errors.as_data()


@pytest.mark.django_db
@patch(
    "project.npda.forms.patient_form.validate_patient_sync",
    mock_external_validation_result(gp_practice_postcode=None),
)
def test_error_validating_gp_postcode(mocked_pdu):
    # TODO MRB: report this back somehow rather than just eat it in the log? (https://github.com/rcpch/national-paediatric-diabetes-audit/issues/334)
    form = PatientForm(
        VALID_FIELDS_WITH_GP_POSTCODE,
        paediatric_diabetes_unit=mocked_pdu,
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
def test_invalid_gp_ods_code(mocked_pdu):
    form = PatientForm(VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu)
    form.is_valid()

    assert "gp_practice_ods_code" in form.errors.as_data()


@pytest.mark.django_db
@patch(
    "project.npda.forms.patient_form.validate_patient_sync",
    mock_external_validation_result(gp_practice_ods_code=None),
)
def test_error_validating_gp_ods_code(mocked_pdu):
    # TODO MRB: report this back somehow rather than just eat it in the log? (https://github.com/rcpch/national-paediatric-diabetes-audit/issues/334)
    form = PatientForm(VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu)
    form.is_valid()

    assert len(form.errors.as_data()) == 0


@pytest.mark.django_db
def test_lookup_index_of_multiple_deprivation(mocked_pdu):
    form = PatientForm(VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu)

    form.is_valid()
    assert len(form.errors.as_data()) == 0

    patient = form.save()
    assert (
        patient.index_of_multiple_deprivation_quintile
        == INDEX_OF_MULTIPLE_DEPRIVATION_QUINTILE
    )


@pytest.mark.django_db
def test_lookup_location(mocked_pdu):
    form = PatientForm(VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu)

    form.is_valid()
    assert len(form.errors.as_data()) == 0

    patient = form.save()
    assert patient.location_wgs84 == VALID_FIELDS["location_wgs84"]
    assert patient.location_bng == VALID_FIELDS["location_bng"]


@pytest.mark.django_db
@patch(
    "project.npda.forms.patient_form.validate_patient_sync",
    mock_external_validation_result(index_of_multiple_deprivation_quintile=None),
)
def test_error_looking_up_index_of_multiple_deprivation(mocked_pdu):
    # TODO MRB: report this back somehow rather than just eat it in the log? (https://github.com/rcpch/national-paediatric-diabetes-audit/issues/334)
    form = PatientForm(VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu)
    form.is_valid()

    patient = form.save()

    patient.index_of_multiple_deprivation_quintile = None


@pytest.mark.django_db
def test_date_leaving_service_missing(mocked_pdu):
    # Date leaving service is required if reason leaving service is provided
    form = PatientForm(
        {"reason_leaving_service": 1},
        paediatric_diabetes_unit=mocked_pdu,
    )
    assert "date_leaving_service" in form.errors.as_data()


@pytest.mark.django_db
def test_date_leaving_service_future(mocked_pdu):
    form = PatientForm(
        {"date_leaving_service": TODAY + relativedelta(days=1)},
        paediatric_diabetes_unit=mocked_pdu,
    )

    errors = form.errors.as_data()
    assert "date_leaving_service" in errors

    error_message = errors["date_leaving_service"][0].messages[0]
    assert error_message == "Cannot be in the future"


@pytest.mark.django_db
def test_date_leaving_service_before_diagnosis_date(mocked_pdu):
    form = PatientForm(
        {
            "diagnosis_date": VALID_FIELDS["diagnosis_date"],
            "date_leaving_service": VALID_FIELDS["diagnosis_date"]
            - relativedelta(years=1),
        },
        paediatric_diabetes_unit=mocked_pdu,
    )

    errors = form.errors.as_data()
    assert "date_leaving_service" in errors

    error_message = errors["date_leaving_service"][0].messages[0]
    assert (
        error_message
        == "'Date Leaving Service' cannot be before 'Date of Diabetes Diagnosis'"
    )


@pytest.mark.django_db
def test_date_leaving_service_before_date_of_birth(mocked_pdu):
    form = PatientForm(
        {
            "date_of_birth": VALID_FIELDS["date_of_birth"],
            "date_leaving_service": VALID_FIELDS["date_of_birth"]
            - relativedelta(years=1),
        },
        paediatric_diabetes_unit=mocked_pdu,
    )

    errors = form.errors.as_data()
    assert "date_leaving_service" in errors

    error_message = errors["date_leaving_service"][0].messages[0]
    assert error_message == "'Date Leaving Service' cannot be before 'Date of Birth'"


@pytest.mark.django_db
def test_reason_leaving_service_missing(mocked_pdu):
    # Reason leaving service is required if date leaving service is provided
    form = PatientForm(
        {"date_leaving_service": TODAY},
        paediatric_diabetes_unit=mocked_pdu,
    )
    assert "reason_leaving_service" in form.errors.as_data()


@pytest.mark.django_db
def test_reason_leaving_service_invalid(mocked_pdu):
    form = PatientForm(
        {"reason_leaving_service": 99},
        paediatric_diabetes_unit=mocked_pdu,
    )
    assert "reason_leaving_service" in form.errors.as_data()


@pytest.mark.django_db
def test_successful_patient_transfer(mocked_pdu):
    # Create patient
    form = PatientForm(
        VALID_FIELDS,
        paediatric_diabetes_unit=mocked_pdu,
    )

    assert len(form.errors.as_data()) == 0
    patient = form.save()

    # Create a transfer for the patient (initially created in the view)
    Transfer.objects.create(
        paediatric_diabetes_unit=mocked_pdu,
        patient=patient,
        date_leaving_service=None,
        reason_leaving_service=None,
    )

    # Update patient
    form = PatientForm(
        VALID_FIELDS | {"reason_leaving_service": 1, "date_leaving_service": TODAY},
        instance=patient,
    )

    assert len(form.errors.as_data()) == 0
    patient = form.save()

    transfer = Transfer.objects.get(patient=patient)

    assert len(form.errors.as_data()) == 0
    assert form.is_valid()

    assert transfer.patient == patient
    assert transfer.date_leaving_service == TODAY
    assert transfer.reason_leaving_service == 1


@pytest.mark.django_db
def test_fail_validation_if_same_patient_twice_in_same_submission(
    mocked_pdu,
    seed_groups_fixture,
    seed_users_fixture,
):
    NPDAUser = apps.get_model("npda", "NPDAUser")
    pdu_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=mocked_pdu.pz_code
    ).first()

    form = PatientForm(VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu)
    assert len(form.errors.as_data()) == 0
    patient = form.save()

    # add the patient to a submission
    Submission = apps.get_model("npda", "Submission")
    submission = Submission.objects.create(
        paediatric_diabetes_unit=mocked_pdu,
        submission_active=True,
        submission_date=TODAY,
        submission_by=pdu_user,
        audit_year=2024,
    )
    submission.patients.add(patient)

    # Create a new form with the same patient
    new_form = PatientForm(VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu)
    new_form.is_valid()

    assert "nhs_number" in new_form.errors.as_data()


@pytest.mark.django_db
def test_pass_validation_if_same_patient_twice_in_same_submission_but_different_pdu(
    mocked_pdu,
    seed_groups_fixture,
    seed_users_fixture,
):
    NPDAUser = apps.get_model("npda", "NPDAUser")
    pdu_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=mocked_pdu.pz_code
    ).first()

    form = PatientForm(VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu)
    assert len(form.errors.as_data()) == 0
    patient = form.save()

    # add the patient to a submission
    Submission = apps.get_model("npda", "Submission")
    submission = Submission.objects.create(
        paediatric_diabetes_unit=mocked_pdu,
        submission_active=True,
        submission_date=TODAY,
        submission_by=pdu_user,
        audit_year=2024,
    )
    submission.patients.add(patient)

    another_pdu = PaediatricsDiabetesUnitFactory(pz_code="PZ075")

    # Create a new form with the same patient but in a different PDU
    new_form = PatientForm(VALID_FIELDS, paediatric_diabetes_unit=another_pdu)
    assert new_form.is_valid(), (
        "Form should be valid even with the same patient in a different PDU"
    )
    assert "nhs_number" not in new_form.errors.as_data(), (
        "There should be no error for nhs_number when the patient is in a different PDU"
    )


@pytest.mark.django_db
def test_edit_patient(mocked_pdu):
    NPDAUser = apps.get_model("npda", "NPDAUser")
    pdu_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=mocked_pdu.pz_code
    ).first()

    form = PatientForm(VALID_FIELDS, paediatric_diabetes_unit=mocked_pdu)

    assert len(form.errors.as_data()) == 0
    patient = form.save()

    # Add the patient to a submission (required to reproduce https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1039)
    Submission = apps.get_model("npda", "Submission")
    submission = Submission.objects.create(
        paediatric_diabetes_unit=mocked_pdu,
        submission_active=True,
        submission_date=TODAY,
        submission_by=pdu_user,
        audit_year=2024,
    )
    submission.patients.add(patient)

    form = PatientForm(
        VALID_FIELDS | {"sex": SEX_TYPE[1][0]},
        instance=patient,
        paediatric_diabetes_unit=mocked_pdu,
    )

    assert len(form.errors.as_data()) == 0
    patient = form.save()

    assert patient.sex == SEX_TYPE[1][0]


# @pytest.mark.django_db
# def test_immunotherapy_date_before_visit_date_fails_validation(
#     audit_period_for_dataset_year,
# ):
#     """
#     Test that immunotherapy date before visit date should fail
#     """
#     if audit_period_for_dataset_year.start_date.year != 2026:
#         pytest.skip("Skipping test as audit period is not for dataset year 2026")
#     patient = PatientFactory()

#     form = VisitForm(
#         data={
#             "visit_date": "2026-01-10",  # Required for validation
#             "immunotherapy_date": "2026-01-01",
#         },
#         initial={"patient": patient},
#         audit_period=audit_period_for_dataset_year,
#     )

#     assert form.is_valid() is False, "Immunotherapy date before visit date should fail"
#     assert "immunotherapy_date" in form.errors


# @pytest.mark.django_db
# def test_immunotherapy_date_after_visit_date_passes_validation(
#     audit_period_for_dataset_year,
# ):
#     """
#     Test that immunotherapy date after visit date should pass
#     """
#     if audit_period_for_dataset_year.start_date.year != 2026:
#         pytest.skip("Skipping test as audit period is not for dataset year 2026")
#     patient = PatientFactory()

#     form = VisitForm(
#         data={
#             "visit_date": audit_period_for_dataset_year.end_date
#             - datetime.timedelta(days=1),
#             "immunotherapy_date": audit_period_for_dataset_year.start_date
#             + datetime.timedelta(days=1),
#             "immunotherapy_received": 1,  # Yes
#         },
#         initial={"patient": patient},
#         audit_period=audit_period_for_dataset_year,
#     )

#     assert form.is_valid(), "Immunotherapy date after visit date should pass"
#     assert "immunotherapy_date" not in form.errors


# @pytest.mark.django_db
# def test_immunotherapy_given_without_date_fails_validation(
#     audit_period_for_dataset_year,
# ):
#     """
#     Test that immunotherapy given without date should fail
#     """
#     if audit_period_for_dataset_year.start_date.year != 2026:
#         pytest.skip("Skipping test as audit period is not for dataset year 2026")
#     patient = PatientFactory()

#     form = VisitForm(
#         data={
#             "visit_date": audit_period_for_dataset_year.end_date
#             - datetime.timedelta(days=1),
#             "immunotherapy_received": 1,  # Yes
#             "immunotherapy_date": None,
#         },
#         initial={"patient": patient},
#         audit_period=audit_period_for_dataset_year,
#     )

#     assert form.is_valid() is False, "Immunotherapy given without date should fail"
#     assert "immunotherapy_date" in form.errors


# @pytest.mark.django_db
# def test_adhd_asd_diagnosis_invalid_value_form_fails_validation(
#     audit_period_for_dataset_year,
# ):
#     """
#     Test that invalid adhd_asd_diagnosis should fail
#     """
#     if audit_period_for_dataset_year.start_date.year != 2026:
#         pytest.skip("Skipping test as audit period is not for dataset year 2026")
#     patient = PatientFactory()

#     form = VisitForm(
#         data={
#             "visit_date": audit_period_for_dataset_year.end_date
#             - datetime.timedelta(days=1),
#             "adhd_asd_diagnosis": 24,  # Invalid value
#         },
#         initial={"patient": patient},
#         audit_period=audit_period_for_dataset_year,
#     )

#     # Trigger the cleaners
#     assert form.is_valid() is False, "Invalid adhd_asd_diagnosis but test passed"
#     assert "adhd_asd_diagnosis" in form.errors


# @pytest.mark.django_db
# def test_learning_disability_invalid_value_form_fails_validation(
#     audit_period_for_dataset_year,
# ):
#     """
#     Test that invalid learning_disability should fail
#     """
#     if audit_period_for_dataset_year.start_date.year != 2026:
#         pytest.skip("Skipping test as audit period is not for dataset year 2026")
#     patient = PatientFactory()

#     form = VisitForm(
#         data={
#             "visit_date": audit_period_for_dataset_year.end_date
#             - datetime.timedelta(days=1),
#             "learning_disability": 4,  # Invalid value
#         },
#         initial={"patient": patient},
#         audit_period=audit_period_for_dataset_year,
#     )

#     # Trigger the cleaners
#     assert form.is_valid() is False, "Invalid learning_disability but test passed"
#     assert "learning_disability" in form.errors
