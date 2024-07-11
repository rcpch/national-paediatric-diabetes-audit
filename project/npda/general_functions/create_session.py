# NPDA Imports
from project.npda.general_functions import (
    get_single_pdu_from_ods_code,
    get_all_pdus_list_choices,
)
from project.npda.models.organisation_employer import OrganisationEmployer


def create_session_object_from_organisation_employer(
    organisation_employer: OrganisationEmployer,
) -> dict:
    """Helper function to create a session object from an organisation employer isntance."""

    ods_code = organisation_employer.ods_code
    pz_code = organisation_employer.pz_code
    sibling_organisations = get_single_pdu_from_ods_code(ods_code)

    session = {
        "ods_code": ods_code,
        "pz_code": pz_code,
        "organisation_choices": [
            (choice["ods_code"], choice["name"])
            for choice in sibling_organisations["organisations"]
        ],
        "pdu_choices": get_all_pdus_list_choices(),
    }

    return session
