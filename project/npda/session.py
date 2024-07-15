from dataclasses import dataclass
from typing import List

# Users are constrained by some session variables:
#
#  What you are currently looking at:
#  - ods_code
#  - pz_code
#  - sibling_organisations
#    - pz_code (dupe of root pz_code?)
#    - organisations
#      - ods_code
#      - name
#
#  What you can switch to look at:
#  - organisation_choices
#    - (ods_code, name)
#  - pdu_choices
#    - (pz_code, name)
#
# ods_code
#  - NPDAUserListView context (to pass to view_preference)
#
# pz_code
#  - unused I think
#
# sibling_organisations
#  - pz_code
#    - AuditCohortsListView
#     - pz_code to filter visible cohorts
#     - pz_code in context to render title on page
#    - home
#      - pz_code for CSV upload
#    - CheckPDUListMixin
#      - pz_code to match against organisation employer
#    - NPDAUserListView
#      - pz_code to pass to view_preference
#      - also as chosen_pdu (what's the difference? - nothing, just used in different places in the template)
#    and probably same again for PatientListView
#
#  - organisations
#    - NPDAUserListView
#      - ods_code to filter user list to all orgs in the pdu
#    - NPDAUserForm
#      - ods_code to filter OrganisationEmployer for the add_employer option

# consider refactoring sibling_organisations.organisations to an on-demand lookup

@dataclass
class NPDASession:
    # The organisation the user currently wants to see (defaults to their first employing organisation)
    ods_code: str
    # The PDU that organisation belongs too
    pz_code: str