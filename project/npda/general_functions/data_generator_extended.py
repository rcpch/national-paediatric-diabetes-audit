from datetime import date, timedelta
from enum import Enum

from django.db import transaction
from project.npda.general_functions.audit_period import (
    get_audit_period_for_date,
    get_quarters_for_audit_period,
)
from project.npda.general_functions.random_date import get_random_date
from project.npda.models.patient import Patient
from project.npda.models.visit import Visit
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory


class AgeRange(Enum):
    """
    Enum class to represent the range of ages for children.
    """

    AGE_0_4 = (0, 4)
    AGE_5_10 = (5, 10)
    AGE_11_15 = (11, 15)
    AGE_16_19 = (16, 19)
    AGE_20_25 = (20, 25)


class FakePatientCreator:

    def __init__(self, date_in_audit: date):
        """Uses `date_in_audit` to determine the audit period for the fake patient(s)."""

        self.audit_start_date, self.audit_end_date = get_audit_period_for_date(
            date_in_audit
        )

        self.fake_patients_built: list[Patient] = []

    def build_fake_patients(self, n: int, age_range: AgeRange):
        """Builds `n` fake patients, that are NOT yet stored to db."""
        new_pts = PatientFactory.build_batch(
            size=n,
            age_range=age_range,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )
        self.fake_patients_built.extend(new_pts)

    def create_and_save_fake_patients(self, n: int, age_range: AgeRange):
        """Creates and saves `n` fake patients to the db."""
        # Use a transaction to speed up bulk insertions
        with transaction.atomic():
            # Step 1: Create `n` patients in batch
            patients = PatientFactory.create_batch(
                size=n,
                age_range=age_range,
                audit_start_date=self.audit_start_date,
                audit_end_date=self.audit_end_date,
                # We're going to manually create visits for each patient
                visit=None,
            )

            # Step 2: Build 4 visits per patient
            visits = []
            for patient in patients:

                audit_quarters = get_quarters_for_audit_period(
                    self.audit_start_date, self.audit_end_date
                )

                for quarter_start_date, quarter_end_date in audit_quarters:
                    visit_date = get_random_date(quarter_start_date, quarter_end_date)
                    visit = VisitFactory.build(
                        patient=patient,
                        visit_date=visit_date,
                    )
                    visits.append(visit)

            # Step 3: Bulk create all visits at once
            Visit.objects.bulk_create(visits)

        return patients
