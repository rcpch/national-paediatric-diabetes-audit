# python imports
from django.apps import apps
from django.db.models import F, Value, Case, When, CharField, Q
from django.db.models.functions import Concat, Upper

# RCPCH imports
import logging


# Logging
logger = logging.getLogger(__name__)


def paediatric_diabetes_units_to_populate_select_field(
    requesting_user, user_instance=None
):
    """
    This function is used to populate any select field with paediatric diabetes units: their PZ code and name, based on requesting_user permissions.
    The user_instance is used to filter out paediatric diabetes units that that user is already affiliated with, if it is used for selects in forms.
    If no user_instance is provided, the function will return all paediatric diabetes units that the requesting_user has access to, irrespective of affiliation.

    This is because in the create and update user forms particularly, the user creating or updating the form  might have different permissions to the user being created or updated.
    """

    PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")

    if user_instance:
        # populate the select field with paediatric diabetes units that the user is not already affiliated with
        if (
            requesting_user.is_superuser
            or requesting_user.is_rcpch_audit_team_member
            or requesting_user.is_rcpch_staff
        ):
            # return all paediatric diabetes units excluding those were the user is employed
            filtered_pdus = PaediatricDiabetesUnit.objects.all().exclude(
                npda_users__npda_user=user_instance,
                active=True
            )
        else:
            # return only those paediatric diabetes units that a user is already affiliated with
            filtered_pdus = PaediatricDiabetesUnit.objects.filter(
                npda_users__npda_user=user_instance
            )
    else:
        # no user instance is provided - therefore need the organisation_choices to be populated with all organisations based on requesting_user user permissions
        if (
            requesting_user.is_superuser
            or requesting_user.is_rcpch_audit_team_member
            or requesting_user.is_rcpch_staff
        ):
            # return all paediatric diabetes units
            filtered_pdus = PaediatricDiabetesUnit.objects.filter(active=True).all()

        else:
            # return all organisations that are associated with the same paediatric diabetes unit as the requesting_user
            filtered_pdus = PaediatricDiabetesUnit.objects.filter(
                npda_users__npda_user=requesting_user
            )

    filtered_pdus = filtered_pdus.order_by("pz_code")

    pdu_choices = [
        (pdu.pz_code, f"{pdu.lead_organisation_name} - {pdu.parent_name}") for pdu in filtered_pdus
    ]

    return pdu_choices
