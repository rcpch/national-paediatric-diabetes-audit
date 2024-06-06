"""Factory fn to create new NPDAUser.
"""

# standard imports
from datetime import timedelta

# third-party imports
import factory

# rcpch imports
from project.npda.models import NPDAUser
from project.npda.general_functions import get_nhs_organisation


class NPDAUserFactory(factory.django.DjangoModelFactory):
    """Dependency factory for creating a minimum viable NPDAUser."""

    class Meta:
        model = NPDAUser
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"npda_test_user_{n}@nhs.net")
    first_name = "Mandel"
    surname = "Brot"
    is_active = True
    is_superuser = False
    email_confirmed = True
    organisation_employer = factory.LazyFunction(
        lambda: get_nhs_organisation(ods_code="RP401")
    )

    # Add Groups
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return

        # hook into post gen hook to set pass
        self.set_password("pw")

        if extracted:
            for group in extracted:
                self.groups.add(group)

            self.save()
