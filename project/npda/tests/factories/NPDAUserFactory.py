"""Factory fn to create new NPDAUser.
"""

# standard imports
from datetime import timedelta

# third-party imports
import factory

# rcpch imports
from project.npda.models import NPDAUser


class NPDAUserFactory(factory.django.DjangoModelFactory):
    """Dependency factory for creating a minimum viable NPDAUser."""

    class Meta:
        model = NPDAUser
