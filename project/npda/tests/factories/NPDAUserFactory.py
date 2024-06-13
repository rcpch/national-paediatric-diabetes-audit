"""Factory function to create new NPDAUser."""

# Standard imports
import factory

# Project imports
from project.npda.models import NPDAUser
from project.npda.general_functions import get_nhs_organisation


class NPDAUserFactory(factory.django.DjangoModelFactory):
    """Factory for creating a minimum viable NPDAUser."""

    class Meta:
        model = NPDAUser
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"npda_test_user_{n}@nhs.net")
    first_name = "Mandel"
    surname = "Brot"
    is_active = True
    is_superuser = False
    email_confirmed = True
    organisation_employer = factory.LazyFunction(lambda: get_nhs_organisation(ods_code="RP401"))

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return

        # Set a default password
        self.set_password("pw")

        # Add the extracted groups if provided
        if extracted:
            for group in extracted:
                self.groups.add(group)

        self.save()
