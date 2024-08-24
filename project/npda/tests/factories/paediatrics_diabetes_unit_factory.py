"""Factory fn to create new Visit, related to a Patient.
"""

# standard imports
from django.apps import apps

# third-party imports
import factory

# rcpch imports
from project.npda.models.paediatric_diabetes_unit import PaediatricDiabetesUnit


class PaediatricsDiabetesUnitFactory(factory.django.DjangoModelFactory):
    """PDU Factory.

    Defaults to Chelsea Westminster Hospital.
    """

    class Meta:
        model = PaediatricDiabetesUnit

    # Chelsea Westminster Hospital default
    pz_code = "PZ130"
    lead_organisation_ods_code = "RQM01"
    lead_organisation_name = "CHELSEA & WESTMINSTER HOSPITAL"
    parent_ods_code = "RQM"
    parent_name = "CHELSEA AND WESTMINSTER HOSPITAL NHS FOUNDATION TRUST"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Custom create method to handle get_or_create logic for PaediatricsDiabetesUnit.

        Each PDU has a composite unique constraint for pz_code and ods_code. This mimics
        a get or create operation every time a new PDUFactory instance is created.
        """
        pz_code = kwargs.pop("pz_code", None)
        parent_name = kwargs.pop("parent_name", None)
        parent_ods_code = kwargs.pop("parent_ods_code", None)
        lead_organisation_name = kwargs.pop("lead_organisation_name", None)
        lead_organisation_ods_code = kwargs.pop("lead_organisation_ods_code", None)

        if pz_code and lead_organisation_ods_code:
            pdu, created = PaediatricDiabetesUnit.objects.get_or_create(
                pz_code=pz_code,
                lead_organisation_ods_code=lead_organisation_ods_code,
                lead_organisation_name=lead_organisation_name,
                parent_ods_code=parent_ods_code,
                parent_name=parent_name,
            )
            return pdu

        return super()._create(model_class, *args, **kwargs)
