"""Factory fn to create new Visit, related to a Patient.
"""

# standard imports

# third-party imports
import factory

# rcpch imports
from project.npda.models import Site


class SiteFactory(factory.django.DjangoModelFactory):
    """Dependency factory for creating a minimum viable NPDAManagement.

    This Factory is generated AFTER a Patient has been generated.
    """

    class Meta:
        model = Site



    paediatric_diabetes_unit_pz_code = 'PZ130'
    organisation_ods_code = 'RP426'
