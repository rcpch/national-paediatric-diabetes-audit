"""conftest.py
Configures pytest fixtures for npda app tests.
"""

# standard imports

import logging

# third-party imports
from datetime import date
from unittest.mock import patch

import pytest
from pytest_factoryboy import register

from celery import Celery
from celery.worker.worker import WorkController as CeleryWorker

# rcpch imports
from project.npda.tests.factories import (
    NPDAUserFactory,
    OrganisationEmployerFactory,
    PaediatricsDiabetesUnitFactory,
    PatientFactory,
    TransferFactory,
    VisitFactory,
    seed_groups_fixture,
    seed_patients_fixture,
    seed_users_fixture,
    seed_groups_per_function_fixture,
    seed_users_per_function_fixture,
    dummy_sheets_folder,
    dummy_sheet_csv,
)
from django.conf import settings

logger = logging.getLogger(__name__)
# register factories to be used across test directory

# factory object becomes lowercase-underscore form of the class name
register(PatientFactory)  # => patient_factory
register(VisitFactory)  # => patient_visit_factory
register(NPDAUserFactory)  # => npdauser_factory
register(OrganisationEmployerFactory)  # => npdauser_factory
register(PaediatricsDiabetesUnitFactory)  # => npdauser_factory
register(TransferFactory)  # => npdauser_factory

pytest_plugins = ("celery.contrib.pytest",)


@pytest.fixture
def AUDIT_START_DATE():
    """AUDIT_START_DATE is Day 2 of the first audit period"""
    return date(year=2024, month=4, day=1)


@pytest.fixture
def AUDIT_END_DATE():
    """AUDIT_END_DATE"""
    return date(year=2025, month=3, day=31)


@pytest.fixture(scope="session")
def celery_app():
    app = Celery(
        "project",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )
    app.config_from_object("django.conf:settings", namespace="CELERY")
    app.set_default()
    return app


@pytest.fixture(scope="session")
def celery_worker(celery_app):
    # Ensure the worker is started with the correct settings
    celery_worker = CeleryWorker(app=celery_app)
    celery_worker.start()
    yield  # This is where the test runs
    celery_worker.stop()


@pytest.fixture(scope="session", autouse=True)
def django_setup():
    # Ensure database is ready for tests
    if settings.DATABASES["default"]["ENGINE"].startswith("django.db.backends."):
        from django.core.management import call_command

        call_command("migrate")


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass  # This ensures that all tests have access to the database


@pytest.fixture(scope="session")
def test_pz_codes_fixture():
    return ["PZ196", "PZ074", "PZ248"]  # GOSH  # Alder Hey  # Jersey


@pytest.fixture(scope="function")
def test_pz_codes_function_fixture():
    return ["PZ196", "PZ074", "PZ248"]  # GOSH  # Alder Hey  # Jersey
