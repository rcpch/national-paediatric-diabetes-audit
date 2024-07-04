"""Test the setup of the test database.

Seeds the test database with test data and checks that the data has been seeded.
"""

import pytest

from django.contrib.auth.models import Group
from project.npda.models import NPDAUser, OrganisationEmployer


@pytest.mark.skip("Test is not implemented")
# @pytest.mark.django_db
def test__seed_test_db(
    seed_groups_fixture,
    seed_users_fixture,
    seed_patients_fixture,
):
    assert Group.objects.all().exists()
    # assert OrganisationEmployer.objects.all().exists()
    assert NPDAUser.objects.all().exists()
