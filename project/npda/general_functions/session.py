import logging
from django.core.exceptions import PermissionDenied
from django.apps import apps

# NPDA Imports
from project.npda.general_functions import (
    get_single_pdu_from_ods_code,
    get_all_pdus_list_choices,
    organisations_adapter,
)

logger = logging.getLogger(__name__)


def create_session_object(user):
    """
    Create a session object for the user, based on their permissions.
    This is called on login, and is used to filter the data the user can see.
    """

    pz_codes = [org["pz_code"] for org in user.organisation_employers.values()]

    session = {
        "pz_code": pz_codes[0],
    }

    return session


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
