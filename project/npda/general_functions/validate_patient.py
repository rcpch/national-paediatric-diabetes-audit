import nhs_number

from project.npda.general_functions import (
    stringify_time_elapsed,
    imd_for_postcode,
    validate_postcode,
    gp_details_for_ods_code,
    gp_ods_code_for_postcode
)

"""
We have two ways patients are created:
    - Manually in the UI via Django Forms
    - For each unique NHS number in a CSV upload

In the future we would also like to support direct integration with EHR systems,
which would probably take the form of an API call to Django Rest Framework.

Validating some of the fields within a patient requires network calls to third party services:
    - Postcodes -> postcodes.io
    - GP ODS code (or postcode) -> NHS Spine

We also use our Census API to lookup the index of multiple deprivation score using the patients postcode.
We save this in the database so can report on it.

Implementing all this using the normal Django model methods and Django form validators leads to CSV upload
being quite slow, as we do everything sequentially. If it takes 1/3 of a second to call each API endpoint,
that's 1 second to process a row in the CSV. We want to support around 10,000 rows in a CSV file so that
would be unacceptably slow.

We can take advantage of Python async support to in theory issue all of the validation requests in parallel,
although in practice we would probably want to limit them to batches to be fair to the third party APIs.
With batches of 500, it would take 20 seconds to handle 10,000 rows.

However async support is not baked in to Django model validators or Django form cleaners. We could naively
process batches of rows but this would require a Python ThreadPoolExecutor and our threads would simply sit
spending most of their time waiting for network responses. It would be possible to spin up as many threads
as we have items in the batch size but if we write our own code to perform the validation instead we can
use async support all the way up to the view level and control the batch size with a Python async TaskGroup.

The Visit model does not currently have any cross-network validation so there we can simply use the existing
form.
"""
def validate_date_not_in_future(value):
    today = date.today()

    if value > today:
        raise ValidationError("Date cannot be in the future")

async def validate_patient(patient):
    if not nhs_number.is_valid(value):
        raise ValidationError(
            "%(value)s is not a valid NHS number.",
            params={"value": value},
        )
    
