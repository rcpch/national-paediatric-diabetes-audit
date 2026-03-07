"""conftest.py
Configures pytest fixtures for npda app tests.
"""

# standard imports

import logging
import os

# third-party imports
from datetime import date
from unittest.mock import patch

import pytest
from pytest_factoryboy import register

# rcpch imports
from project.npda.tests.factories import (
    NPDAUserFactory,
    OrganisationEmployerFactory,
    PaediatricsDiabetesUnitFactory,
    PatientFactory,
    TransferFactory,
    VisitFactory,
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    seed_groups_per_function_fixture,
    seed_users_per_function_fixture,
    seed_audit_periods_per_function_fixture,
    dummy_sheets_folder,
    dummy_sheet_csv,
    dummy_sheet_csv_jersey,
    dummy_sheet_csv_old_headers,
)

from project.npda.models import AuditPeriod

logger = logging.getLogger(__name__)
# register factories to be used across test directory

# factory object becomes lowercase-underscore form of the class name
register(PatientFactory)  # => patient_factory
register(VisitFactory)  # => patient_visit_factory
register(NPDAUserFactory)  # => npdauser_factory
register(OrganisationEmployerFactory)  # => npdauser_factory
register(PaediatricsDiabetesUnitFactory)  # => npdauser_factory
register(TransferFactory)  # => npdauser_factory


def pytest_addoption(parser):
    parser.addoption(
        "--dataset-year",
        action="append",
        default=[],
        help="Dataset year(s) to test (e.g. --dataset-year=2021)",
    )


def _dataset_years_from_config(pytestconfig):
    opt = pytestconfig.getoption("--dataset-year")
    if opt:
        return [int(y) for y in opt]

    env = os.getenv("NPDA_DATASET_YEARS")
    if env:
        return [int(y.strip()) for y in env.split(",") if y.strip()]

    return [2021, 2026]


def pytest_generate_tests(metafunc):
    if "dataset_year" in metafunc.fixturenames:
        years = _dataset_years_from_config(metafunc.config)
        metafunc.parametrize("dataset_year", years)


@pytest.fixture
def dataset_year(request):
    return request.param


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
