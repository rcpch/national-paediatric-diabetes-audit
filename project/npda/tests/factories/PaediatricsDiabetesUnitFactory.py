"""Factory fn to create new Visit, related to a Patient.
"""

# standard imports
from django.apps import apps

# third-party imports
import factory

# rcpch imports
from project.npda.models.paediatric_diabetes_unit import PaediatricDiabetesUnit


class PaediatricsDiabetesUnitFactory(factory.django.DjangoModelFactory):
    """PDU Factory"""

    class Meta:
        model = PaediatricDiabetesUnit

    pz_code = "PZ130"
    ods_code = "RP426"
