"""conftest.py
Configures pytest fixtures for npda app tests.
"""

# standard imports

# third-party imports
import logging
from unittest.mock import patch

import pytest
from pytest_factoryboy import register

# rcpch imports
from project.npda.tests.factories import (NPDAUserFactory,
                                          OrganisationEmployerFactory,
                                          PaediatricsDiabetesUnitFactory,
                                          PatientFactory, TransferFactory,
                                          VisitFactory, seed_groups_fixture,
                                          seed_patients_fixture,
                                          seed_users_fixture)

logger = logging.getLogger(__name__)
# register factories to be used across test directory

# factory object becomes lowercase-underscore form of the class name
register(PatientFactory)  # => patient_factory
register(VisitFactory)  # => patient_visit_factory
register(NPDAUserFactory)  # => npdauser_factory
register(OrganisationEmployerFactory)  # => npdauser_factory
register(PaediatricsDiabetesUnitFactory)  # => npdauser_factory
register(TransferFactory)  # => npdauser_factory

@pytest.fixture(autouse=True)
def patch_imd_for_postcode():
    """Automatically patch `imd_for_postcode` for all tests."""
    logger.debug("Patched imd_for_postcode returning 4")
    with patch('project.npda.models.patient.imd_for_postcode', return_value=4) as mock_model:
        print("Patching imd_for_postcode at models.patient:", mock_model)
        yield