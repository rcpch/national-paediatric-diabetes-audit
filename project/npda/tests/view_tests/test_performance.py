"""Performance testing views"""

from datetime import date
import json
import re
import time
from typing import Literal

from bs4 import BeautifulSoup
import pytest
from project.npda.general_functions.data_generator_extended import (
    AgeRange,
    FakePatientCreator,
    HbA1cTargetRange,
    VisitType,
)
from freezegun import freeze_time

from project.npda.models.npda_user import NPDAUser
from project.npda.models.submission import Submission
from project.npda.tests.test_csv_upload import ALDER_HEY_PZ_CODE
from project.npda.tests.utils import login_and_verify_user
import logging

# Logging
logger = logging.getLogger(__name__)


@pytest.mark.django_db
@pytest.mark.performance
def test_dashboard_view_response_time(
    AUDIT_START_DATE,
    AUDIT_END_DATE,
    seed_groups_fixture,
    seed_users_fixture,
    seed_patients_fixture,
    client,
):
    """Basic performance test for the dashboard view response time with lots of patients."""

    # Define constants
    N_PATIENTS = 1000
    VISIT_TYPES = [
        VisitType.CLINIC,
        VisitType.CLINIC,
        VisitType.ANNUAL_REVIEW,
        VisitType.DIETICIAN,
        VisitType.CLINIC,
        VisitType.CLINIC,
        VisitType.DIETICIAN,
        VisitType.CLINIC,
        VisitType.CLINIC,
        VisitType.HOSPITAL_ADMISSION,
        VisitType.PSYCHOLOGY,
    ]

    # Put work into these functions to read more easily (hopefully)
    def seed_patients():
        fake_patient_creator = FakePatientCreator(
            audit_start_date=AUDIT_START_DATE,
            audit_end_date=AUDIT_END_DATE,
        )
        logger.info(f'Seeding {N_PATIENTS} patients with {len(VISIT_TYPES)} visit types...')
        new_pts = fake_patient_creator.create_and_save_fake_patients(
            n=N_PATIENTS,
            age_range=AgeRange.AGE_11_15,
            hb1ac_target_range=HbA1cTargetRange.TARGET,
            patient_kwargs={
                "transfer__paediatric_diabetes_unit": ah_user.organisation_employers.first(),
            },
            visit_types=VISIT_TYPES,
            visit_kwargs={"is_valid": True},
        )
        logger.info('DONE!')
        logger.info('Creating submission...')
        new_submission = Submission.objects.create(
            paediatric_diabetes_unit=ah_user.organisation_employers.first(),
            audit_year=AUDIT_START_DATE.year,
            submission_date=AUDIT_START_DATE,
            submission_by=ah_user,
            submission_active=True,
        )

        # Add patients to submission
        new_submission.patients.add(*new_pts)
        logger.info('DONE!')

    def get_top_level_dashboard_view_response():
        start_dashboard = time.time()
        logger.info("\t⏳ Getting top-level dashboard view response...")
        response = client.get("/dashboard")
        elapsed_dashboard = time.time() - start_dashboard

        logger.info(f"N_PATIENTS: {N_PATIENTS} * VISIT_TYPES: {len(VISIT_TYPES)}".center(80, "*"))

        # Check valid overall response within some leeway upperbound
        assert response.status_code == 200
        # assert (
        #     elapsed_dashboard < 1
        # ), f"Dashboard response time took too long (> 1 seconds), took: {elapsed_dashboard} seconds"
        logger.info(f"\tDashboard view response time: {elapsed_dashboard} seconds.")
        return response, elapsed_dashboard

    def extract_htmx_requests(soup) -> list[dict]:
        htmx_requests = []
        # Extract All HTMX Requests + hx-vals from the rendered HTML
        for tag in soup.find_all(attrs={"hx-get": True}):
            url = tag["hx-get"]
            hx_vals = tag.get("hx-vals", "{}")
            try:
                hx_vals_json = json.loads(hx_vals)
            except json.JSONDecodeError:
                hx_vals_json = {}

            htmx_requests.append({"url": url, "hx_vals": hx_vals_json})

        return htmx_requests

    def make_htmx_requests(client, htmx_requests) -> list[tuple[int, str]]:
        request_times = []
        total_htmx_time = 0
        for htmx_request in htmx_requests:
            url: str = htmx_request["url"]
            print(f"\t ✅ {url.ljust(10)} response in ", end="")
            hx_vals = htmx_request.get("hx_vals", {})
            logger.debug(f"HTMX Request: {url} with hx-vals: {hx_vals}")

            # Regex pattern to extract 'color' query param
            color_pattern = re.compile(r"([\?&])color=([0-9A-Fa-f]+)")
            # Search for the color parameter in the URL -> sub it out into hx-vals to mock htmx
            # request with color parameter
            match = color_pattern.search(url)
            if match:
                color = match.group(2)  # Extract the color value
                hx_vals["color"] = color  # Add to hx-vals

                # Remove the color parameter from the URL
                url = re.sub(color_pattern, "", url).rstrip("?&")

            logger.debug(f"Processed HTMX Request: {url} with hx-vals: {hx_vals}")

            # Prepare request parameters
            request_params = {"HTTP_HX_REQUEST": "true"}  # Simulate an HTMX request

            # Convert `hx_vals` dictionary into individual query parameters (skipping strings)
            query_params = {
                key: json.dumps(value) if not isinstance(value, str) else value
                for key, value in hx_vals.items()
            }

            start_htmx = time.time()
            response_htmx = client.get(url, query_params, **request_params)
            elapsed_htmx = time.time() - start_htmx

            assert response_htmx.status_code == 200
            # assert elapsed_htmx < RESPONSE_TIME_UPPERBOUND_SECONDS.get(
            #     url, 1
            # ), f"HTMX request {url} took too long: {elapsed_htmx:.3f} seconds"
            request_times.append((elapsed_htmx, url))
            print(f"{elapsed_htmx:.3f} seconds", flush=True)

            total_htmx_time += elapsed_htmx
        return request_times, total_htmx_time

    # First get user
    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    # Login
    client = login_and_verify_user(client, ah_user)

    # Now create patients
    seed_patients()

    # GET the top level view response
    response, elapsed_dashboard = get_top_level_dashboard_view_response()
    logger.info("\t⏳ Rendering htmx partials...")

    # Check sub-views
    # Extract All HTMX Requests + hx-vals from the rendered HTML
    soup = BeautifulSoup(response.content, "html.parser")
    htmx_requests = extract_htmx_requests(soup)

    # Measure All HTMX Requests (with hx-vals)
    # Collate data in request_times for output at end (each is (url, load_time))
    request_times, total_htmx_time = make_htmx_requests(client, htmx_requests)

    # Compute Total Page Load Time (Dashboard + HTMX Requests)
    total_elapsed = elapsed_dashboard + total_htmx_time

    # Display sorted individual request times
    logger.info("\n\tSORTED dashboard view request times:")
    for elapsed, url in sorted(request_times, key=lambda x: x[0], reverse=True):
        logger.info(f"\t⏳ {url.ljust(40)}: {elapsed:.3f} seconds")
    logger.info(f"\tTotal Page Load Time: {total_elapsed:.3f} seconds")
    # assert total_elapsed < 12, f"Total load time too high: {total_elapsed:.3f} seconds"
