"""Factory function to create new NPDAUser."""

# Standard imports
import factory

# Project imports
from project.npda.models import NPDAUser, OrganisationEmployer
from project.npda.general_functions.rcpch_nhs_organisations import get_nhs_organisation


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


    @factory.post_generation
    def organisation_employers(self, create, extracted, **kwargs):
        if not create:
            return

        # Add the extracted org ods_codes if provided
        if extracted:
            orgs = []
            for ods_code in extracted:
                org_obj = get_nhs_organisation(ods_code=ods_code)
                org, created = OrganisationEmployer.objects.get_or_create(
                    name=org_obj.name,
                    ods_code=org_obj.ods_code,
                    pz_code=org_obj.paediatric_diabetes_unit.pz_code,
                )
                orgs.append(org)
            self.organisation_employers.set(orgs)

        self.save()
