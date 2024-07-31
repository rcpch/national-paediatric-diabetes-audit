"""Factory function to create new OrganisationEmployerFactory."""

# Standard imports
import factory

# Project imports
from project.npda.models import OrganisationEmployer


class OrganisationEmployerFactory(factory.django.DjangoModelFactory):
    """Dependency for creating a minimum viable NPDAUser.

    Organisation Employer will to PaediatricsDiabetesUnitFactory Default.
    """

    class Meta:
        model = OrganisationEmployer
        skip_postgeneration_save = True

    # Use a local import to avoid circular dependency issues
    paediatric_diabetes_unit = factory.SubFactory(
        "project.npda.tests.factories.PaediatricsDiabetesUnitFactory"
    )

    # Once an NPDAUser is created, it will attach to this attribute
    npda_user = None
