"""conftest.py
Configures pytest fixtures for npda app tests.
"""

# standard imports

import logging

# third-party imports
from datetime import date

import pytest
from pytest_factoryboy import register

from project.npda.models import AuditPeriod

# rcpch imports
from project.npda.tests.factories import (
    NPDAUserFactory,
    OrganisationEmployerFactory,
    PaediatricsDiabetesUnitFactory,
    PatientFactory,
    TransferFactory,
    VisitFactory,
)

logger = logging.getLogger(__name__)
# register factories to be used across test directory

# factory object becomes lowercase-underscore form of the class name
register(PatientFactory)  # => patient_factory
register(VisitFactory)  # => patient_visit_factory
register(NPDAUserFactory)  # => npdauser_factory
register(OrganisationEmployerFactory)  # => npdauser_factory
register(PaediatricsDiabetesUnitFactory)  # => npdauser_factory
register(TransferFactory)  # => npdauser_factory


@pytest.fixture
def AUDIT_START_DATE():
    """AUDIT_START_DATE is Day 2 of the first audit period"""
    return date(year=2024, month=4, day=1)


@pytest.fixture
def AUDIT_END_DATE():
    """AUDIT_END_DATE"""
    return date(year=2025, month=3, day=31)


@pytest.fixture(scope="session")
def test_pz_codes_fixture():
    return ["PZ196", "PZ074", "PZ248", "PZ004"]  # GOSH, Alder Hey, Jersey, Northampton


@pytest.fixture(scope="function")
def test_pz_codes_function_fixture():
    return ["PZ196", "PZ074", "PZ248", "PZ004"]  # GOSH, Alder Hey, Jersey, Northampton


@pytest.fixture(autouse=True)
def ensure_audit_period(db, AUDIT_START_DATE, AUDIT_END_DATE):
    """Ensure an AuditPeriod exists for each test."""
    AuditPeriod.objects.get_or_create(
        start_date=AUDIT_START_DATE,
        end_date=AUDIT_END_DATE,
        is_open=True,
        is_visible=True,
        slug=f"{AUDIT_START_DATE.year}-{AUDIT_END_DATE.year}",
    )
