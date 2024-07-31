import logging
from django.core.exceptions import PermissionDenied

# NPDA Imports
from project.npda.general_functions import (
    get_single_pdu_from_ods_code,
    get_all_pdus_list_choices,
    organisations_adapter,
)

logger = logging.getLogger(__name__)


def create_session_object(user):
    organisation_employer = user.organisation_employers.first()

    ods_code = organisation_employer.ods_code
    pz_codes = [org["pz_code"] for org in user.organisation_employers.values()]

    sibling_organisations = get_single_pdu_from_ods_code(ods_code)

    organisation_choices = [
        (choice.ods_code, choice.name)
        for choice in sibling_organisations.organisations
    ]

    can_see_all_pdus = user.is_superuser or user.is_rcpch_audit_team_member

    pdu_choices = [
        choice
        for choice in get_all_pdus_list_choices()
        if can_see_all_pdus or choice[0] in pz_codes
    ]

    session = {
        "ods_code": ods_code,
        "pz_code": pz_codes[0],
        "organisation_choices": organisation_choices,
        "pdu_choices": pdu_choices,
    }

    return session


def get_new_session_fields(user, ods_code, pz_code):
    ret = {}

    if ods_code:
        can_see_organisations = (
            user.is_rcpch_audit_team_member
            or user.organisation_employers.filter(ods_code=ods_code).exists()
        )

        if not can_see_organisations:
            logger.warning(
                f"User {user} requested organisation {ods_code} they cannot see"
            )
            raise PermissionDenied()

        ret["ods_code"] = ods_code

        pdu = organisations_adapter.get_single_pdu_from_ods_code(ods_code)
        ret["pz_code"] = pdu["pz_code"]
    elif pz_code:
        can_see_pdu = (
            user.is_rcpch_audit_team_member
            or user.organisation_employers.filter(pz_code=pz_code).exists()
        )

        if not can_see_pdu:
            logger.warning(f"User {user} requested PDU {pz_code} they cannot see")
            raise PermissionDenied()

        ret["pz_code"] = pz_code

        sibling_organisations = organisations_adapter.get_single_pdu_from_pz_code(
            pz_number=pz_code
        )
        ret["ods_code"] = sibling_organisations.organisations[0].ods_code

    return ret
