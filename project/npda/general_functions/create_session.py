# NPDA Imports
from project.npda.general_functions import (
    get_single_pdu_from_ods_code,
    get_all_pdus_list_choices,
)
from project.npda.models.organisation_employer import OrganisationEmployer


def create_session_object(
    user
):
    organisation_employer = user.organisation_employers.first()

    ods_code = organisation_employer.ods_code
    pz_codes = [org['pz_code'] for org in user.organisation_employers.values()]

    sibling_organisations = get_single_pdu_from_ods_code(ods_code)

    organisation_choices = [
        (choice["ods_code"], choice["name"])
        for choice in sibling_organisations["organisations"]
    ]

    pdu_choices = [
        choice for choice in get_all_pdus_list_choices()
            if choice[0] in pz_codes
    ]

    session = {
        "ods_code": ods_code,
        "pz_code": pz_codes[0],
        "organisation_choices": organisation_choices,
        "pdu_choices": pdu_choices,
    }

    return session
