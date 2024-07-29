"""Factory fn to create new Visit, related to a Patient.
"""

# standard imports
from datetime import date
from django.apps import apps

# third-party imports
import factory

# rcpch imports
from project.npda.models import Transfer

PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")


class TransferFactory(factory.django.DjangoModelFactory):
    """Dependency factory for creating a minimum viable NPDAManagement.

    This Factory is generated AFTER a Patient has been generated.
    """

    class Meta:
        model = Transfer

    # alderhey_pdu = PaediatricDiabetesUnit.objects.create(
    #     ods_code="RP426", pz_code="PZ130"
    # )

    # paediatric_diabetes_unit = alderhey_pdu

    # date_leaving_service = date(2021, 1, 1)
    # reason_leaving_service = None
    # previous_pz_code = "PZ215"
