"""Factory fn to create new Visit, related to a Patient.
"""

# standard imports
from datetime import date
from django.apps import apps

# third-party imports
import factory

# rcpch imports
from project.npda.models import Transfer
from project.npda.tests.factories import PaediatricsDiabetesUnitFactory


class TransferFactory(factory.django.DjangoModelFactory):
    """Dependency factory for creating a minimum viable NPDA Patient.

    This Factory is generated AFTER a Patient has been generated.
    """

    class Meta:
        model = Transfer

    # Relationships
    paediatric_diabetes_unit = factory.SubFactory(PaediatricsDiabetesUnitFactory)
    # Once a PatientFactory instance is created, it will attach here
    patient = None
