"""Factory fn to create new Visit, related to a Patient.
"""

# standard imports
from datetime import timedelta

# third-party imports
import factory

# rcpch imports
from project.npda.models import Visit


class VisitFactory(factory.django.DjangoModelFactory):
    """Dependency factory for creating a minimum viable NPDAManagement.

    This Factory is generated AFTER a Patient has been generated.
    """

    class Meta:
        model = Visit

    # Once Patient instance made, it will attach to this instance
    patient = None
    
    class Params:
        """Factory parameters for VisitFactory.
        """

        # KPI 1