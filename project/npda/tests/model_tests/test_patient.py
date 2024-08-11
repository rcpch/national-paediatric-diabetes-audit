"""Tests for the Patient model.

Suggested tests for the Patient model:


- A patient cannot be created without a date of birth
- A patient cannot be created with an invalid date of birth (e.g. in the future or in the wrong format or over or equal to 19 years old)
- A patient cannot be created without a diabetes type
- A patient cannot be created with an invalid diabetes type (e.g with a key that does not exist)
- A patient cannot be created without a date of diagnosis
- A patient cannot be created with an invalid date of diagnosis (e.g. in the future, before the date of birth or in the wrong format)
- A patient cannot be created with an invalid postcode (e.g. with spaces, with special characters, with letters, with more than 8 characters and not in the list of NHS digital postcodes that denote unknown postcode or no fixed abode)
- A patient can be created with a valid index of multiple deprivation quintile if a valid NHS number, date of birth, diabetes type, date of diagnosis are also provided
 - An index of multiple deprivation quintile is calculated on save and persisted in the database
 - If an index of multiple deprivation quintile cannot be calculated, the field should be set to None
 - A patient can be created with a valid sex (e.g. with a key that does exist) if a valid NHS number, date of birth, diabetes type, date of diagnosis are also provided
 - A patient cannot be create with an invalid sex (e.g. with a key that does not exist) if a valid NHS number, date of birth, diabetes type, date of diagnosis are also provided
 - A patient can be created with a valid ethnicity (e.g. with a key that does exist) if a valid NHS number, date of birth, diabetes type, date of diagnosis are also provided
 - A patient cannot be created with an invalid ethnicity (e.g. with a key that does not exist)
- A patient can be created with a valid death date if a valid NHS number, date of birth, diabetes type, date of diagnosis are also provided
- A patient cannot be created with an invalid death date (e.g. in the future, before the date of birth, before the date of diagnosis or in the wrong format)
- A patient can be created with a valid GP practice ODS code if a valid NHS number, date of birth, diabetes type, date of diagnosis are also provided
- A patient cannot be created with an invalid GP practice ODS code (e.g. with spaces, with special characters, not in the list of NHS digital GP practice ODS codes on the NHS digital Spine API)
- A patient can be created if a Paediatric Diabetes Unit instance is associated with it (via the Transfer model) if a valid NHS number, date of birth, diabetes type, date of diagnosis are also provided
- A patient cannot be created if a Paediatric Diabetes Unit instance is not associated with it (via the Transfer model) if a valid NHS number, date of birth, diabetes type, date of diagnosis are also provided
"""

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
def test_patient_nhs_number_validations(
):
    
    # A patient cannot be created without an NHS number
    PatientFactory(nhs_number=None)
    
    
# - A patient cannot be created with an invalid NHS number
# - A patient cannot be created with a duplicate NHS number