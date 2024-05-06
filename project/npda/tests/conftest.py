"""conftest.py
Configures pytest fixtures for npda app tests.
"""

# standard imports

# third-party imports
from pytest_factoryboy import register
import pytest


# rcpch imports
from project.npda.tests.factories import (
    seed_groups_fixture,
    seed_users_fixture,
    seed_cases_fixture,
    PatientFactory,
    PatientVisitFactory,
    NPDAUserFactory,
)
from project.npda.models import Patient


# register factories to be used across test directory

# factory object becomes lowercase-underscore form of the class name
register(PatientFactory)  # => patient_factory
register(PatientVisitFactory)  # => patient_visit_factory
register(NPDAUserFactory)  # => npdauser_factory


# @pytest.fixture
# @pytest.mark.django_db
# def GOSH():
#     return Organisation.objects.get(
#         ods_code="RP401",
#         trust__ods_code="RP4",
#     )


# @pytest.fixture
# @pytest.mark.django_db
# def PATIENT_GOSH():
#     return Patient.objects.get(first_name=f"child_{GOSH.name}")


# @pytest.fixture
# @pytest.mark.django_db
# def ADDENBROOKES():
#     Organisation.objects.get(
#         ods_code="RGT01",
#         trust__ods_code="RGT",
#     )


# @pytest.fixture
# @pytest.mark.django_db
# def PATIENT_ADDENBROOKES():
#     Patient.objects.get(first_name=f"child_{ADDENBROOKES.name}")
