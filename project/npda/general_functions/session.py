import logging
from django.core.exceptions import PermissionDenied
from django.apps import apps

# NPDA Imports
from project.npda.general_functions import (
    organisations_adapter,
)

logger = logging.getLogger(__name__)


def create_session_object(user):
    """
    Create a session object for the user, based on their permissions.
    This is called on login, and is used to filter the data the user can see.
    """

    OrganisationEmployer = apps.get_model("npda", "OrganisationEmployer")
    primary_organisation = OrganisationEmployer.objects.filter(
        npda_user=user, is_primary_employer=True
    ).get()
    pz_code = primary_organisation.paediatric_diabetes_unit.pz_code
    pdu_choices = (
        organisations_adapter.paediatric_diabetes_units_to_populate_select_field(
            requesting_user=user, user_instance=None
        )
    )

    session = {"pz_code": pz_code, "pdu_choices": list(pdu_choices)}

    return session


def update_session_object(request, pz_code):
    """
    Update the session object for the user, based on their permissions.
    This is called when the user changes their organisation.
    """

    request.session["pz_code"] = pz_code

    return request.session


def get_new_session_fields(user, pz_code):
    ret = {}

    if pz_code:
        can_see_organisations = (
            user.is_rcpch_audit_team_member
            or user.organisation_employers.filter(pz_code=pz_code).exists()
        )

        if not can_see_organisations:
            logger.warning(
                f"User {user} requested organisation {pz_code} they cannot see"
            )
            raise PermissionDenied()

        ret["pz_code"] = pz_code

    return ret
