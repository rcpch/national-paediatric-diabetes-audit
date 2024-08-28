"""
This file contains tests for the submissions model and views.

Model classes tested:
- Only one submissions for a PDU & ODS code in the session for a given audit year/quarter should be active

View classes tested:
 -  SubmissionsListView GET request should return all submissions for the PDU & ODS code in the session for all audit years/quarters
 -  SubmissionsListView GET request should NOT return the active submissions for a PDU & ODS code not in the session for all audit years/quarters
- SubmissionsListView POST request with param "submit-data" of value "delete-data" should delete the submission for the PDU & ODS code in the session
- SubmissionsListView POST request with param "submit-data" of value "delete-data" should NOT delete the submission for a different PDU & ODS code to that in the session
- SubmissionsListView POST request with param "submit-data" of value "delete-data" should NOT delete the submission for the PDU & ODS code in the session if the submission is not active
"""
