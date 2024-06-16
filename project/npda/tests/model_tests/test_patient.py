"""Tests for the Patient model."""

# Standard imports
import pytest
import logging

# 3rd Party imports

# E12 Imports
from project.npda.models import Patient

# Logging
logger = logging.getLogger(__name__)


def test_patient_creation(
    seed_groups_fixture,
    seed_users_fixture,
    seed_patients_fixture,
):
    """Test Patient creation."""

    new_patient = Patient()
    logger.info(f"New Patient: {new_patient}")

    assert new_patient is not None
