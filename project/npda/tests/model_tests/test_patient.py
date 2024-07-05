"""Tests for the Patient model."""

# Standard imports
import pytest
import logging

# 3rd Party imports

# NPDA Imports
from project.npda.tests.factories import PatientFactory
from project.npda.general_functions import print_instance_field_attrs

# Logging
logger = logging.getLogger(__name__)


@pytest.mark.django_db
def test_patient_creation(
    seed_groups_fixture,
    seed_users_fixture,
    seed_patients_fixture,
):
    """Test Patient creation."""

    new_patient = PatientFactory()
    print_instance_field_attrs(new_patient)

    assert new_patient is not None
