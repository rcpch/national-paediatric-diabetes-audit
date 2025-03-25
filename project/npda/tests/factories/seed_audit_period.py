"""
Seeds NPDA Users in test db once per session.
"""

# Standard imports
import pytest

from django.apps import apps


# NPDA Imports
from project.npda.models import AuditPeriod
import logging

logger = logging.getLogger(__name__)


def _seed_audit_periods_fixture(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():

        if AuditPeriod.objects.exists():
            logger.info('NOTE: Test audit periods already seeded! Not re-seeding.')
            return

        logger.info(f"Seeding test audit period 2024-2025.")

        AuditPeriod.objects.create(
            is_open=True,
            start_date="2024-01-01",
            end_date="2025-01-01",
        )


@pytest.fixture(scope="session")
def seed_audit_periods_fixture(django_db_setup, django_db_blocker):
    _seed_audit_periods_fixture(django_db_setup, django_db_blocker)

# Required if multiple tests use transactional_db
@pytest.fixture(scope="function")
def seed_audit_periods_per_function_fixture(django_db_setup, django_db_blocker):
    _seed_audit_periods_fixture(django_db_setup, django_db_blocker)