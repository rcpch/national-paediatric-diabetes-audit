"""Factory fn to create new Visit, related to a Patient.
"""

# standard imports
from datetime import timedelta

# third-party imports
import factory

# rcpch imports
from project.npda.models import Patient, Visit


class PatientVisitFactory(factory.django.DjangoModelFactory):
    """Dependency factory for creating a minimum viable E12Management.

    This Factory is generated AFTER a Patient has been generated.
    """

    class Meta:
        model = Visit

    # Once Patient instance made, it will attach to this instance
    patient = None
