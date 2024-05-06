"""Factory fn to create new Patient.
"""

# standard imports
from datetime import timedelta

# third-party imports
import factory

# rcpch imports
from project.npda.models import Patient


class PatientFactory(factory.django.DjangoModelFactory):
    """Dependency factory for creating a minimum viable Patient."""

    class Meta:
        model = Patient
