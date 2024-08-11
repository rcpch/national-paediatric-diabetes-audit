"""Tests for the testing environment and the test database.
"""

import pytest
import logging
import os

from django.contrib.auth.models import Group
from django.db.models import F, Value

from project.npda.models import NPDAUser, OrganisationEmployer, Patient
from project.npda.models.paediatric_diabetes_unit import PaediatricDiabetesUnit
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory
from project.npda.tests.UserDataClasses import (
    test_user_audit_centre_reader_data,
)
from project.constants import VIEW_PREFERENCES
from project.npda.tests.factories.paediatrics_diabetes_unit_factory import (
    PaediatricsDiabetesUnitFactory,
)
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.general_functions import print_instance_field_attrs
from project.settings import LOGGING

# logging
logger = logging.getLogger(__name__)


def test_logging_effective_level_is_same_as_env_var():
    """Ensures that the logger level is set to the same level as the environment variable.

    Error most likely due to config issue.
    """

    environment_log_level = os.getenv("CONSOLE_LOG_LEVEL")
    if environment_log_level is None:
        pytest.fail("Environment variable 'CONSOLE_LOG_LEVEL' not set.")

    effective_logger_level = logging.getLevelName(logger.getEffectiveLevel())

    assert (
        effective_logger_level == environment_log_level
    ), f"Effective logger level: {effective_logger_level} | Environment log level: {environment_log_level}"


@pytest.mark.django_db
def test__seed_test_db(
    seed_groups_fixture,
    seed_users_fixture,
    seed_patients_fixture,
):
    assert Group.objects.all().exists()
    assert OrganisationEmployer.objects.all().exists()
    assert NPDAUser.objects.all().exists()


@pytest.mark.django_db
def test__multiple_PaediatricsDiabetesUnitFactory_instances_not_created(
    seed_groups_fixture,
    seed_users_fixture,
    seed_patients_fixture,
):
    """
    Both Patient and NPDAUser factories eventually create and are associated with a PaediatricsDiabetesUnit instance.

    This test ensures that only one PaediatricsDiabetesUnit instance exists in the db - checking the 'get or create'
    functionality of the PaediatricsDiabetesUnitFactory.
    """
    # GOSH User
    user_data = test_user_audit_centre_reader_data
    GOSH_PZ_CODE = "PZ196"
    GOSH_ODS_CODE = "RP416"

    for _ in range(2):

        # User factory with no organisation employer specified
        new_user_default_pdu = NPDAUserFactory(
            first_name="test",
            role=user_data.role,
            # Assign flags based on user role
            is_active=user_data.is_active,
            is_staff=user_data.is_staff,
            is_rcpch_audit_team_member=user_data.is_rcpch_audit_team_member,
            is_rcpch_staff=user_data.is_rcpch_staff,
            groups=[user_data.group_name],
            view_preference=(VIEW_PREFERENCES[0][0]),
        )

        # Patient with default PDU
        new_patient = PatientFactory()

        # User factory with organisation employer specified
        new_user_gosh = NPDAUserFactory(
            first_name="test",
            role=user_data.role,
            # Assign flags based on user role
            is_active=user_data.is_active,
            is_staff=user_data.is_staff,
            is_rcpch_audit_team_member=user_data.is_rcpch_audit_team_member,
            is_rcpch_staff=user_data.is_rcpch_staff,
            groups=[user_data.group_name],
            view_preference=(VIEW_PREFERENCES[0][0]),
            # Assign to PDU via organisation employer by passing in list of pz_codes
            organisation_employers=[GOSH_PZ_CODE],
        )

        # Patient with specified PDU
        # First create the specific PDU
        gosh_pdu = PaediatricsDiabetesUnitFactory(
            pz_code=GOSH_PZ_CODE, ods_code=GOSH_ODS_CODE
        )
        # Then assign a Patient with to this PDU using the TransferFactory
        patient_with_custom_pdu = PatientFactory(
            transfer__paediatric_diabetes_unit=gosh_pdu
        )

    # Check that only one PDU exists in the db for the default PDU user and new patient
    #     (default defined in PaediatricsDiabetesUnitFactory in pz_code="PZ130", ods_code="RQM01")
    assert (
        PaediatricDiabetesUnit.objects.filter(pz_code="PZ130", ods_code="RQM01").count()
        == 1
    )

    # For the specified PDU user at GOSH
    gosh_pdus_filterset = PaediatricDiabetesUnit.objects.filter(
        pz_code=GOSH_PZ_CODE, ods_code=GOSH_ODS_CODE
    )
    assert gosh_pdus_filterset.count() == 1
