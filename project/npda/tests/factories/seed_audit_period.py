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

        for start_year in [2024, 2025]:
            end_year = start_year + 1

            logger.info(f"Seeding test audit period {start_year}-{end_year}.")

            AuditPeriod.objects.create(
                is_open=True,
                start_date="{start_year}-04-01",
                end_date="{end_year}-03-31",
            )


@pytest.fixture(scope="session")
def seed_audit_periods_fixture(django_db_setup, django_db_blocker):
    _seed_audit_periods_fixture(django_db_setup, django_db_blocker)

# Required if multiple tests use transactional_db
@pytest.fixture(scope="function")
def seed_audit_periods_per_function_fixture(django_db_setup, django_db_blocker):
    _seed_audit_periods_fixture(django_db_setup, django_db_blocker)