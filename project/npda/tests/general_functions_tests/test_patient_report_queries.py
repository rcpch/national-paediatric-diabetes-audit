from datetime import date
from decimal import Decimal

import pytest
from dateutil.relativedelta import relativedelta

from project.constants.diabetes_types import DIABETES_TYPES
from project.constants.hba1c_format import HBA1C_FORMATS
from project.npda.general_functions.patient_report.queries import (
    annotate_admissions,
    annotate_health_checks,
    build_base_queryset,
    count_admissions,
)
from project.npda.models import AuditPeriod, NPDAUser, Submission, Transfer
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.factories import test_user_audit_centre_editor_data
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory


@pytest.mark.django_db
class TestPatientReportHealthCheckQueries:
    def _get_user_and_pdu(self):
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
            role=test_user_audit_centre_editor_data.role,
        ).first()
        return user, user.organisation_employers.first()

    def _create_submission(self, pdu, audit_period, user, patients):
        submission = Submission.objects.create(
            paediatric_diabetes_unit=pdu,
            audit_period=audit_period,
            audit_year=audit_period.start_date.year,
            submission_date=audit_period.start_date,
            submission_by=user,
            submission_active=True,
        )
        submission.patients.add(*patients)
        return submission

    def _get_health_check_rows(self, pdu, audit_period):
        qs = annotate_health_checks(
            build_base_queryset(pdu, audit_period), audit_period
        )
        return {
            row["pk"]: row
            for row in qs.values(
                "pk",
                "patient_identifier",
                "is_gte_12yo",
                "passed_hba1c",
                "passed_bmi",
                "passed_thyroid_screen",
                "passed_blood_pressure",
                "passed_urinary_albumin",
                "passed_foot_exam",
                "passed_retinal_screening",
                "num_passed",
                "num_total",
                "is_incomplete_year_of_care",
                "is_complete_year_of_care",
            )
        }

    def test_under_12_ineligible_for_age_based_checks(
        self, seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
    ):
        user, pdu = self._get_user_and_pdu()
        audit_period = AuditPeriod.objects.get_default_audit_period()

        patient = PatientFactory(
            nhs_number="1111111111",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=11, days=2),
            diagnosis_date=audit_period.start_date - relativedelta(days=400),
        )
        VisitFactory(
            patient=patient,
            visit_date=audit_period.start_date + relativedelta(days=10),
            hba1c=50,
            hba1c_format=HBA1C_FORMATS[0][0],
            hba1c_date=audit_period.start_date + relativedelta(days=10),
        )
        self._create_submission(pdu, audit_period, user, [patient])

        rows = self._get_health_check_rows(pdu, audit_period)
        row = rows[patient.pk]

        assert row["is_gte_12yo"] is False
        assert row["passed_thyroid_screen"] is False
        assert row["passed_blood_pressure"] is None
        assert row["passed_urinary_albumin"] is None
        assert row["passed_foot_exam"] is None
        assert row["num_total"] == 3

    def test_thyroid_screening_required_within_first_year_of_diagnosis(
        self, seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
    ):
        """Thyroid screen is always required regardless of diabetes duration."""
        user, pdu = self._get_user_and_pdu()
        audit_period = AuditPeriod.objects.get_default_audit_period()

        patient = PatientFactory(
            nhs_number="1111111122",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=11, days=2),
            diagnosis_date=audit_period.start_date + relativedelta(days=30),
        )
        VisitFactory(
            patient=patient,
            visit_date=audit_period.start_date + relativedelta(days=10),
            hba1c=50,
            hba1c_format=HBA1C_FORMATS[0][0],
            hba1c_date=audit_period.start_date + relativedelta(days=10),
        )
        self._create_submission(pdu, audit_period, user, [patient])

        rows = self._get_health_check_rows(pdu, audit_period)
        row = rows[patient.pk]

        assert row["is_gte_12yo"] is False
        assert row["passed_thyroid_screen"] is False

    # https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1399
    def test_thyroid_screening_required_after_first_year_of_diagnosis(
        self, seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
    ):
        user, pdu = self._get_user_and_pdu()
        audit_period = AuditPeriod.objects.get_default_audit_period()

        patient = PatientFactory(
            nhs_number="1111111122",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=11, days=2),
            diagnosis_date=audit_period.start_date - relativedelta(days=10),
        )
        VisitFactory(
            patient=patient,
            visit_date=audit_period.start_date + relativedelta(days=10),
            hba1c=50,
            hba1c_format=HBA1C_FORMATS[0][0],
            hba1c_date=audit_period.start_date + relativedelta(days=10),
        )
        self._create_submission(pdu, audit_period, user, [patient])

        rows = self._get_health_check_rows(pdu, audit_period)
        row = rows[patient.pk]

        assert row["passed_thyroid_screen"] is False

    def test_retinal_screening_under_12_is_not_required(
        self, seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
    ):
        user, pdu = self._get_user_and_pdu()
        audit_period = AuditPeriod.objects.get_default_audit_period()

        patient = PatientFactory(
            nhs_number="2222222222",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=10),
            diagnosis_date=audit_period.start_date - relativedelta(days=365),
        )
        VisitFactory(
            patient=patient,
            visit_date=audit_period.start_date + relativedelta(days=10),
            retinal_screening_result=1,
            retinal_screening_observation_date=audit_period.start_date
            + relativedelta(days=10),
        )
        self._create_submission(pdu, audit_period, user, [patient])

        rows = self._get_health_check_rows(pdu, audit_period)
        row = rows[patient.pk]

        assert row["is_gte_12yo"] is False
        assert row["passed_retinal_screening"] == "not_required"

    def test_retinal_screening_over_12_with_data_passes(
        self, seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
    ):
        user, pdu = self._get_user_and_pdu()
        audit_period = AuditPeriod.objects.get_default_audit_period()

        patient = PatientFactory(
            nhs_number="3333333333",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=14),
            diagnosis_date=audit_period.start_date - relativedelta(years=2),
        )
        VisitFactory(
            patient=patient,
            visit_date=audit_period.start_date + relativedelta(days=10),
            retinal_screening_result=1,
            retinal_screening_observation_date=audit_period.start_date
            + relativedelta(days=10),
        )
        self._create_submission(pdu, audit_period, user, [patient])

        rows = self._get_health_check_rows(pdu, audit_period)
        row = rows[patient.pk]

        assert row["is_gte_12yo"] is True
        assert row["passed_retinal_screening"] == "complete"

    def test_retinal_screening_over_12_without_data_is_blank(
        self, seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
    ):
        user, pdu = self._get_user_and_pdu()
        audit_period = AuditPeriod.objects.get_default_audit_period()

        patient = PatientFactory(
            nhs_number="4444444444",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=15),
            diagnosis_date=audit_period.start_date - relativedelta(years=2),
        )
        VisitFactory(
            patient=patient,
            visit_date=audit_period.start_date + relativedelta(days=10),
            retinal_screening_result=None,
            retinal_screening_observation_date=None,
        )
        self._create_submission(pdu, audit_period, user, [patient])

        rows = self._get_health_check_rows(pdu, audit_period)
        row = rows[patient.pk]

        assert row["is_gte_12yo"] is True
        assert row["passed_retinal_screening"] == ""

    def test_retinal_screening_blank_with_previous_audit_period_data(
        self, seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
    ):
        user, pdu = self._get_user_and_pdu()
        audit_period = AuditPeriod.objects.get(slug="2025-2026")
        previous_period = audit_period.previous_audit_period()

        patient = PatientFactory(
            nhs_number="8888888888",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=14),
            diagnosis_date=audit_period.start_date - relativedelta(years=2),
        )

        # Current period visit to make patient eligible in base queryset
        VisitFactory(
            patient=patient,
            visit_date=audit_period.start_date + relativedelta(days=10),
            hba1c=50,
            hba1c_format=HBA1C_FORMATS[0][0],
            hba1c_date=audit_period.start_date + relativedelta(days=10),
        )

        # Retinal screening in previous audit period no longer counts
        VisitFactory(
            patient=patient,
            visit_date=previous_period.start_date + relativedelta(days=60),
            retinal_screening_result=1,
            retinal_screening_observation_date=previous_period.start_date
            + relativedelta(days=60),
        )

        self._create_submission(pdu, audit_period, user, [patient])

        rows = self._get_health_check_rows(pdu, audit_period)
        row = rows[patient.pk]

        assert row["passed_retinal_screening"] == ""

    def test_retinal_screening_blank_with_no_data_across_two_periods(
        self, seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
    ):
        user, pdu = self._get_user_and_pdu()
        audit_period = AuditPeriod.objects.get(slug="2025-2026")

        patient = PatientFactory(
            nhs_number="9999999999",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=15),
            diagnosis_date=audit_period.start_date - relativedelta(years=2),
        )

        VisitFactory(
            patient=patient,
            visit_date=audit_period.start_date + relativedelta(days=10),
            hba1c=55,
            hba1c_format=HBA1C_FORMATS[0][0],
            hba1c_date=audit_period.start_date + relativedelta(days=10),
        )

        self._create_submission(pdu, audit_period, user, [patient])

        rows = self._get_health_check_rows(pdu, audit_period)
        row = rows[patient.pk]

        assert row["passed_retinal_screening"] == ""

    def test_retinal_screening_required_within_first_year_of_diagnosis(
        self, seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
    ):
        user, pdu = self._get_user_and_pdu()
        audit_period = AuditPeriod.objects.get_default_audit_period()

        patient = PatientFactory(
            nhs_number="1212121212",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=14),
            diagnosis_date=audit_period.start_date + relativedelta(days=30),
        )

        VisitFactory(
            patient=patient,
            visit_date=audit_period.start_date + relativedelta(days=10),
            hba1c=55,
            hba1c_format=HBA1C_FORMATS[0][0],
            hba1c_date=audit_period.start_date + relativedelta(days=10),
        )

        self._create_submission(pdu, audit_period, user, [patient])

        rows = self._get_health_check_rows(pdu, audit_period)
        row = rows[patient.pk]

        assert row["is_gte_12yo"] is True
        assert row["passed_retinal_screening"] == ""

    def test_retinal_screening_required_after_first_year_of_diagnosis(
        self, seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
    ):
        user, pdu = self._get_user_and_pdu()
        audit_period = AuditPeriod.objects.get_default_audit_period()

        patient = PatientFactory(
            nhs_number="1212121212",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=14),
            diagnosis_date=audit_period.start_date - relativedelta(days=30),
        )

        VisitFactory(
            patient=patient,
            visit_date=audit_period.start_date + relativedelta(days=10),
            hba1c=55,
            hba1c_format=HBA1C_FORMATS[0][0],
            hba1c_date=audit_period.start_date + relativedelta(days=10),
        )

        self._create_submission(pdu, audit_period, user, [patient])

        rows = self._get_health_check_rows(pdu, audit_period)
        row = rows[patient.pk]

        assert row["is_gte_12yo"] is True
        assert (
            row["passed_retinal_screening"] == ""
        )  # we don't fail, just blank (see #1272)

    def test_retinal_screening_with_date_but_no_result_is_blank(
        self, seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
    ):
        user, pdu = self._get_user_and_pdu()
        audit_period = AuditPeriod.objects.get_default_audit_period()

        patient = PatientFactory(
            nhs_number="1313131313",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=14),
            diagnosis_date=audit_period.start_date - relativedelta(years=2),
        )

        VisitFactory(
            patient=patient,
            visit_date=audit_period.start_date + relativedelta(days=10),
            hba1c=55,
            hba1c_format=HBA1C_FORMATS[0][0],
            hba1c_date=audit_period.start_date + relativedelta(days=10),
        )

        VisitFactory(
            patient=patient,
            visit_date=audit_period.start_date + relativedelta(days=20),
            retinal_screening_result=None,
            retinal_screening_observation_date=audit_period.start_date
            + relativedelta(days=20),
        )

        self._create_submission(pdu, audit_period, user, [patient])

        rows = self._get_health_check_rows(pdu, audit_period)
        row = rows[patient.pk]

        assert row["is_gte_12yo"] is True
        assert row["passed_retinal_screening"] == ""

    def test_retinal_screening_previous_period_date_without_result_is_blank(
        self, seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
    ):
        user, pdu = self._get_user_and_pdu()
        audit_period = AuditPeriod.objects.get(slug="2025-2026")
        previous_period = audit_period.previous_audit_period()

        patient = PatientFactory(
            nhs_number="1414141414",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=14),
            diagnosis_date=audit_period.start_date - relativedelta(years=2),
        )

        VisitFactory(
            patient=patient,
            visit_date=audit_period.start_date + relativedelta(days=10),
            hba1c=55,
            hba1c_format=HBA1C_FORMATS[0][0],
            hba1c_date=audit_period.start_date + relativedelta(days=10),
        )

        VisitFactory(
            patient=patient,
            visit_date=previous_period.start_date + relativedelta(days=60),
            retinal_screening_result=None,
            retinal_screening_observation_date=previous_period.start_date
            + relativedelta(days=60),
        )

        self._create_submission(pdu, audit_period, user, [patient])

        rows = self._get_health_check_rows(pdu, audit_period)
        row = rows[patient.pk]

        assert row["is_gte_12yo"] is True
        assert row["passed_retinal_screening"] == ""

    def test_incomplete_year_of_care_still_passes_hba1c(
        self, seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
    ):
        user, pdu = self._get_user_and_pdu()
        audit_period = AuditPeriod.objects.get_default_audit_period()

        patient = PatientFactory(
            nhs_number="5555555555",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=14),
            diagnosis_date=audit_period.start_date - relativedelta(days=2),
        )
        VisitFactory(
            patient=patient,
            visit_date=audit_period.start_date + relativedelta(days=10),
            hba1c=50,
            hba1c_format=HBA1C_FORMATS[0][0],
            hba1c_date=audit_period.start_date + relativedelta(days=10),
        )
        Transfer.objects.create(
            patient=patient,
            paediatric_diabetes_unit=pdu,
            date_leaving_service=audit_period.start_date + relativedelta(days=30),
        )
        self._create_submission(pdu, audit_period, user, [patient])

        rows = self._get_health_check_rows(pdu, audit_period)
        row = rows[patient.pk]

        assert row["is_incomplete_year_of_care"] is True
        assert row["is_complete_year_of_care"] is False
        assert row["passed_hba1c"] is True

    def test_incomplete_year_of_care_when_diagnosed_within_audit_year(
        self, seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
    ):
        """Test that a patient diagnosed within the audit year has incomplete year of care."""
        user, pdu = self._get_user_and_pdu()
        audit_period = AuditPeriod.objects.get_default_audit_period()

        patient = PatientFactory(
            nhs_number="8888888888",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=14),
            diagnosis_date=audit_period.start_date
            + relativedelta(days=30),  # Diagnosed within audit year
        )
        VisitFactory(
            patient=patient,
            visit_date=audit_period.start_date + relativedelta(days=35),
            hba1c=50,
            hba1c_format=HBA1C_FORMATS[0][0],
            hba1c_date=audit_period.start_date + relativedelta(days=35),
        )
        # No Transfer created - incomplete year of care should be True due to diagnosis date only
        self._create_submission(pdu, audit_period, user, [patient])

        rows = self._get_health_check_rows(pdu, audit_period)
        row = rows[patient.pk]

        assert row["is_incomplete_year_of_care"] is True
        assert row["is_complete_year_of_care"] is False
        assert row["passed_hba1c"] is True

    def test_bmi_passes_only_when_bmi_and_observation_date_present(
        self, seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
    ):
        user, pdu = self._get_user_and_pdu()
        audit_period = AuditPeriod.objects.get_default_audit_period()

        patient_with_bmi = PatientFactory(
            nhs_number="6666666666",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=14),
            diagnosis_date=audit_period.start_date - relativedelta(days=400),
        )
        VisitFactory(
            patient=patient_with_bmi,
            visit_date=audit_period.start_date + relativedelta(days=10),
            bmi=Decimal("18.5"),
            height_weight_observation_date=audit_period.start_date
            + relativedelta(days=10),
        )

        patient_without_bmi = PatientFactory(
            nhs_number="7777777777",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=14),
            diagnosis_date=audit_period.start_date - relativedelta(days=400),
        )
        VisitFactory(
            patient=patient_without_bmi,
            visit_date=audit_period.start_date + relativedelta(days=10),
            bmi=None,
            height_weight_observation_date=audit_period.start_date
            + relativedelta(days=10),
        )

        self._create_submission(
            pdu, audit_period, user, [patient_with_bmi, patient_without_bmi]
        )

        rows = self._get_health_check_rows(pdu, audit_period)
        assert rows[patient_with_bmi.pk]["passed_bmi"] is True
        assert rows[patient_without_bmi.pk]["passed_bmi"] is False


@pytest.mark.django_db
class TestPatientReportAdmissionQueries:
    """Test annotate_admissions for both 2021 and 2026 datasets using parameterization."""

    @staticmethod
    def _get_audit_period_2021():
        """Get the default audit period (2024-2025, uses 2021 dataset)."""
        return AuditPeriod.objects.get_default_audit_period()

    @staticmethod
    def _get_audit_period_2026():
        """Get the first audit period that uses 2026 dataset (start_date >= 2026-04-01)."""
        ap = AuditPeriod.objects.filter(start_date__gte=date(2026, 4, 1)).first()
        if not ap:
            pytest.skip("No 2026 audit period available")
        return ap

    def _get_user_and_pdu(self):
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
            role=test_user_audit_centre_editor_data.role,
        ).first()
        return user, user.organisation_employers.first()

    def _create_submission(self, pdu, audit_period, user, patients):
        submission = Submission.objects.create(
            paediatric_diabetes_unit=pdu,
            audit_period=audit_period,
            audit_year=audit_period.start_date.year,
            submission_date=audit_period.start_date,
            submission_by=user,
            submission_active=True,
        )
        submission.patients.add(*patients)
        return submission

    @pytest.mark.parametrize(
        "get_audit_period,stabilisation_code,dka_code,is_2026",
        [
            (_get_audit_period_2021.__func__, 1, 2, False),  # 2021 dataset
            (_get_audit_period_2026.__func__, 5, 1, True),  # 2026 dataset
        ],
        ids=["2021", "2026"],
    )
    def test_basic_admission_counted(
        self,
        get_audit_period,
        stabilisation_code,
        dka_code,
        is_2026,
        seed_groups_fixture,
        seed_users_fixture,
        seed_audit_periods_fixture,
    ):
        """A non-DKA admission outside the +/- 10 day diagnosis window is counted as
        'Admissions not associated with diagnosis'."""
        user, pdu = self._get_user_and_pdu()
        audit_period = get_audit_period()

        patient = PatientFactory(
            nhs_number=f"800{3 if not is_2026 else 13}333333",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=15),
            diagnosis_date=audit_period.start_date - relativedelta(days=200),
        )
        # Stabilisation admission
        visit_kwargs = {
            "patient": patient,
            "visit_date": audit_period.start_date + relativedelta(days=50),
            "hospital_admission_date": audit_period.start_date + relativedelta(days=50),
            "hospital_discharge_date": audit_period.start_date + relativedelta(days=55),
        }
        if is_2026:
            visit_kwargs["hospital_admission_reason_2026"] = stabilisation_code
        else:
            visit_kwargs["hospital_admission_reason"] = stabilisation_code
        VisitFactory(**visit_kwargs)

        self._create_submission(pdu, audit_period, user, [patient])

        qs = annotate_admissions(
            build_base_queryset(pdu, audit_period, type1_only=False), audit_period
        )
        rows = {
            row["pk"]: row
            for row in qs.values(
                "pk", "number_of_admissions", "number_of_dka_admissions"
            )
        }

        assert patient.pk in rows
        assert rows[patient.pk]["number_of_admissions"] == 1
        assert rows[patient.pk]["number_of_dka_admissions"] == 0

    @pytest.mark.parametrize(
        "get_audit_period,stabilisation_code,dka_code,is_2026",
        [
            (_get_audit_period_2021.__func__, 1, 2, False),  # 2021 dataset
            (_get_audit_period_2026.__func__, 5, 1, True),  # 2026 dataset
        ],
        ids=["2021", "2026"],
    )
    def test_dka_admission_within_10_days_of_diagnosis_counted(
        self,
        get_audit_period,
        stabilisation_code,
        dka_code,
        is_2026,
        seed_groups_fixture,
        seed_users_fixture,
        seed_audit_periods_fixture,
    ):
        """A DKA admission within +/- 10 days of diagnosis is counted as
        'Admissions - DKA at diagnosis', and NOT as 'Admissions not associated
        with diagnosis'."""
        user, pdu = self._get_user_and_pdu()
        audit_period = get_audit_period()

        patient = PatientFactory(
            nhs_number=f"800{4 if not is_2026 else 14}444444",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=15),
            # Diagnosed 5 days before the admission: within the +/- 10 day window
            diagnosis_date=audit_period.start_date + relativedelta(days=45),
        )
        # DKA admission
        visit_kwargs = {
            "patient": patient,
            "visit_date": audit_period.start_date + relativedelta(days=50),
            "hospital_admission_date": audit_period.start_date + relativedelta(days=50),
            "hospital_discharge_date": audit_period.start_date + relativedelta(days=55),
        }
        if is_2026:
            visit_kwargs["hospital_admission_reason_2026"] = dka_code
        else:
            visit_kwargs["hospital_admission_reason"] = dka_code
        VisitFactory(**visit_kwargs)

        self._create_submission(pdu, audit_period, user, [patient])

        qs = annotate_admissions(
            build_base_queryset(pdu, audit_period, type1_only=False), audit_period
        )
        rows = {
            row["pk"]: row
            for row in qs.values(
                "pk", "number_of_admissions", "number_of_dka_admissions"
            )
        }

        assert patient.pk in rows
        assert rows[patient.pk]["number_of_admissions"] == 0, (
            "DKA admission at diagnosis must not count as 'not associated with diagnosis'"
        )
        assert rows[patient.pk]["number_of_dka_admissions"] == 1, (
            f"DKA admission (code {dka_code}) within +/- 10 days of diagnosis "
            "must be counted as 'DKA at diagnosis'"
        )

    @pytest.mark.parametrize(
        "get_audit_period,stabilisation_code,dka_code,is_2026",
        [
            (_get_audit_period_2021.__func__, 1, 2, False),  # 2021 dataset
            (_get_audit_period_2026.__func__, 5, 1, True),  # 2026 dataset
        ],
        ids=["2021", "2026"],
    )
    def test_admission_outside_audit_period_excluded(
        self,
        get_audit_period,
        stabilisation_code,
        dka_code,
        is_2026,
        seed_groups_fixture,
        seed_users_fixture,
        seed_audit_periods_fixture,
    ):
        """Test that admissions outside the audit period are excluded."""
        user, pdu = self._get_user_and_pdu()
        audit_period = get_audit_period()

        patient = PatientFactory(
            nhs_number=f"800{5 if not is_2026 else 15}555555",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=15),
            diagnosis_date=audit_period.start_date - relativedelta(days=200),
        )
        # Admission before audit period
        visit_kwargs = {
            "patient": patient,
            "visit_date": audit_period.start_date - relativedelta(days=10),
            "hospital_admission_date": audit_period.start_date - relativedelta(days=10),
            "hospital_discharge_date": audit_period.start_date - relativedelta(days=5),
        }
        if is_2026:
            visit_kwargs["hospital_admission_reason_2026"] = stabilisation_code
        else:
            visit_kwargs["hospital_admission_reason"] = stabilisation_code
        VisitFactory(**visit_kwargs)

        self._create_submission(pdu, audit_period, user, [patient])

        qs = annotate_admissions(
            build_base_queryset(pdu, audit_period, type1_only=False), audit_period
        )
        rows = {row["pk"]: row for row in qs}

        assert patient.pk not in rows, (
            "Admission before audit period should be excluded"
        )

    @pytest.mark.parametrize(
        "get_audit_period,stabilisation_code,dka_code,is_2026",
        [
            (_get_audit_period_2021.__func__, 1, 2, False),  # 2021 dataset
            (_get_audit_period_2026.__func__, 5, 1, True),  # 2026 dataset
        ],
        ids=["2021", "2026"],
    )
    def test_admission_outside_10_day_diagnosis_window_counted_as_not_associated(
        self,
        get_audit_period,
        stabilisation_code,
        dka_code,
        is_2026,
        seed_groups_fixture,
        seed_users_fixture,
        seed_audit_periods_fixture,
    ):
        """An admission outside the +/- 10 day diagnosis window is counted as
        'Admissions not associated with diagnosis', even when it happens
        shortly after diagnosis."""
        user, pdu = self._get_user_and_pdu()
        audit_period = get_audit_period()

        patient = PatientFactory(
            nhs_number=f"800{6 if not is_2026 else 16}666666",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=15),
            diagnosis_date=audit_period.start_date + relativedelta(days=10),
        )
        # Admission 60 days after diagnosis: outside the +/- 10 day window
        visit_kwargs = {
            "patient": patient,
            "visit_date": audit_period.start_date + relativedelta(days=70),
            "hospital_admission_date": audit_period.start_date + relativedelta(days=70),
            "hospital_discharge_date": audit_period.start_date + relativedelta(days=75),
        }
        if is_2026:
            visit_kwargs["hospital_admission_reason_2026"] = stabilisation_code
        else:
            visit_kwargs["hospital_admission_reason"] = stabilisation_code
        VisitFactory(**visit_kwargs)

        self._create_submission(pdu, audit_period, user, [patient])

        qs = annotate_admissions(
            build_base_queryset(pdu, audit_period, type1_only=False), audit_period
        )
        rows = {
            row["pk"]: row
            for row in qs.values(
                "pk", "number_of_admissions", "number_of_dka_admissions"
            )
        }

        assert patient.pk in rows, (
            "Admission outside the +/- 10 day diagnosis window should be "
            "counted as 'not associated with diagnosis'"
        )
        assert rows[patient.pk]["number_of_admissions"] == 1
        assert rows[patient.pk]["number_of_dka_admissions"] == 0

    @pytest.mark.parametrize(
        "get_audit_period,stabilisation_code,dka_code,is_2026",
        [
            (_get_audit_period_2021.__func__, 1, 2, False),  # 2021 dataset
            (_get_audit_period_2026.__func__, 5, 1, True),  # 2026 dataset
        ],
        ids=["2021", "2026"],
    )
    def test_multiple_admissions_per_patient_counted(
        self,
        get_audit_period,
        stabilisation_code,
        dka_code,
        is_2026,
        seed_groups_fixture,
        seed_users_fixture,
        seed_audit_periods_fixture,
    ):
        """Multiple admissions per patient are categorised per column: a DKA
        admission within +/- 10 days of diagnosis counts as 'DKA at
        diagnosis', a later admission counts as 'not associated with
        diagnosis'."""
        user, pdu = self._get_user_and_pdu()
        audit_period = get_audit_period()

        patient = PatientFactory(
            nhs_number=f"800{7 if not is_2026 else 17}777777",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=15),
            diagnosis_date=audit_period.start_date + relativedelta(days=100),
        )
        # First admission: DKA, 5 days after diagnosis (within +/- 10 days)
        visit_kwargs_1 = {
            "patient": patient,
            "visit_date": audit_period.start_date + relativedelta(days=105),
            "hospital_admission_date": audit_period.start_date
            + relativedelta(days=105),
            "hospital_discharge_date": audit_period.start_date
            + relativedelta(days=110),
        }
        if is_2026:
            visit_kwargs_1["hospital_admission_reason_2026"] = dka_code
        else:
            visit_kwargs_1["hospital_admission_reason"] = dka_code
        VisitFactory(**visit_kwargs_1)

        # Second admission: Stabilisation, 100 days after diagnosis
        # (outside +/- 10 days)
        visit_kwargs_2 = {
            "patient": patient,
            "visit_date": audit_period.start_date + relativedelta(days=200),
            "hospital_admission_date": audit_period.start_date
            + relativedelta(days=200),
            "hospital_discharge_date": audit_period.start_date
            + relativedelta(days=205),
        }
        if is_2026:
            visit_kwargs_2["hospital_admission_reason_2026"] = stabilisation_code
        else:
            visit_kwargs_2["hospital_admission_reason"] = stabilisation_code
        VisitFactory(**visit_kwargs_2)

        self._create_submission(pdu, audit_period, user, [patient])

        qs = annotate_admissions(
            build_base_queryset(pdu, audit_period, type1_only=False), audit_period
        )
        rows = {
            row["pk"]: row
            for row in qs.values(
                "pk", "number_of_admissions", "number_of_dka_admissions"
            )
        }

        assert patient.pk in rows
        assert rows[patient.pk]["number_of_admissions"] == 1, (
            "Only the admission outside the +/- 10 day window should count "
            "as 'not associated with diagnosis'"
        )
        assert rows[patient.pk]["number_of_dka_admissions"] == 1, (
            "Only the DKA admission within +/- 10 days of diagnosis should "
            "count as 'DKA at diagnosis'"
        )

    @pytest.mark.parametrize(
        "get_audit_period,stabilisation_code,dka_code,is_2026",
        [
            (_get_audit_period_2021.__func__, 1, 2, False),  # 2021 dataset
            (_get_audit_period_2026.__func__, 5, 1, True),  # 2026 dataset
        ],
        ids=["2021", "2026"],
    )
    def test_non_dka_admission_within_10_day_window_in_neither_column(
        self,
        get_audit_period,
        stabilisation_code,
        dka_code,
        is_2026,
        seed_groups_fixture,
        seed_users_fixture,
        seed_audit_periods_fixture,
    ):
        """A non-DKA admission within +/- 10 days of diagnosis counts in
        neither column, but the patient is still listed (they have had a
        valid admission, so the row count matches count_admissions / KPI 46)."""
        user, pdu = self._get_user_and_pdu()
        audit_period = get_audit_period()

        patient = PatientFactory(
            nhs_number=f"800{8 if not is_2026 else 18}888888",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=15),
            # Diagnosed 5 days before the admission: within the +/- 10 day window
            diagnosis_date=audit_period.start_date + relativedelta(days=45),
        )
        visit_kwargs = {
            "patient": patient,
            "visit_date": audit_period.start_date + relativedelta(days=50),
            "hospital_admission_date": audit_period.start_date + relativedelta(days=50),
            "hospital_discharge_date": audit_period.start_date + relativedelta(days=55),
        }
        if is_2026:
            visit_kwargs["hospital_admission_reason_2026"] = stabilisation_code
        else:
            visit_kwargs["hospital_admission_reason"] = stabilisation_code
        VisitFactory(**visit_kwargs)

        self._create_submission(pdu, audit_period, user, [patient])

        qs = annotate_admissions(
            build_base_queryset(pdu, audit_period, type1_only=False), audit_period
        )
        rows = {
            row["pk"]: row
            for row in qs.values(
                "pk", "number_of_admissions", "number_of_dka_admissions"
            )
        }

        assert patient.pk in rows, (
            "Patient with a valid admission within +/- 10 days of diagnosis "
            "should still be listed (parity with count_admissions / KPI 46)"
        )
        assert rows[patient.pk]["number_of_admissions"] == 0, (
            "Admission within +/- 10 days of diagnosis must not count as "
            "'not associated with diagnosis'"
        )
        assert rows[patient.pk]["number_of_dka_admissions"] == 0, (
            "Non-DKA admission must not count as 'DKA at diagnosis'"
        )

    @pytest.mark.parametrize(
        "get_audit_period,stabilisation_code,dka_code,is_2026",
        [
            (_get_audit_period_2021.__func__, 1, 2, False),  # 2021 dataset
            (_get_audit_period_2026.__func__, 5, 1, True),  # 2026 dataset
        ],
        ids=["2021", "2026"],
    )
    def test_dka_admission_outside_10_day_window_not_dka_at_diagnosis(
        self,
        get_audit_period,
        stabilisation_code,
        dka_code,
        is_2026,
        seed_groups_fixture,
        seed_users_fixture,
        seed_audit_periods_fixture,
    ):
        """A DKA admission outside the +/- 10 day diagnosis window counts as
        'Admissions not associated with diagnosis', not as 'DKA at diagnosis'."""
        user, pdu = self._get_user_and_pdu()
        audit_period = get_audit_period()

        patient = PatientFactory(
            nhs_number=f"800{9 if not is_2026 else 19}999999",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=15),
            diagnosis_date=audit_period.start_date + relativedelta(days=10),
        )
        # DKA admission 60 days after diagnosis: outside the +/- 10 day window
        visit_kwargs = {
            "patient": patient,
            "visit_date": audit_period.start_date + relativedelta(days=70),
            "hospital_admission_date": audit_period.start_date + relativedelta(days=70),
            "hospital_discharge_date": audit_period.start_date + relativedelta(days=75),
        }
        if is_2026:
            visit_kwargs["hospital_admission_reason_2026"] = dka_code
        else:
            visit_kwargs["hospital_admission_reason"] = dka_code
        VisitFactory(**visit_kwargs)

        self._create_submission(pdu, audit_period, user, [patient])

        qs = annotate_admissions(
            build_base_queryset(pdu, audit_period, type1_only=False), audit_period
        )
        rows = {
            row["pk"]: row
            for row in qs.values(
                "pk", "number_of_admissions", "number_of_dka_admissions"
            )
        }

        assert patient.pk in rows
        assert rows[patient.pk]["number_of_admissions"] == 1, (
            "DKA admission outside the +/- 10 day window counts as "
            "'not associated with diagnosis'"
        )
        assert rows[patient.pk]["number_of_dka_admissions"] == 0, (
            "Only DKA admissions within +/- 10 days of diagnosis count as "
            "'DKA at diagnosis'"
        )

    @pytest.mark.parametrize(
        "get_audit_period,stabilisation_code,dka_code,is_2026",
        [
            (_get_audit_period_2021.__func__, 1, 2, False),  # 2021 dataset
            (_get_audit_period_2026.__func__, 5, 1, True),  # 2026 dataset
        ],
        ids=["2021", "2026"],
    )
    def test_dka_admission_before_diagnosis_counted_as_dka_at_diagnosis(
        self,
        get_audit_period,
        stabilisation_code,
        dka_code,
        is_2026,
        seed_groups_fixture,
        seed_users_fixture,
        seed_audit_periods_fixture,
    ):
        """The diagnosis window is symmetric: a DKA admission up to 10 days
        BEFORE diagnosis also counts as 'DKA at diagnosis'."""
        user, pdu = self._get_user_and_pdu()
        audit_period = get_audit_period()

        patient = PatientFactory(
            nhs_number=f"800{2 if not is_2026 else 12}222222",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=15),
            # Diagnosed 5 days after the admission: within the +/- 10 day window
            diagnosis_date=audit_period.start_date + relativedelta(days=55),
        )
        visit_kwargs = {
            "patient": patient,
            "visit_date": audit_period.start_date + relativedelta(days=50),
            "hospital_admission_date": audit_period.start_date + relativedelta(days=50),
            "hospital_discharge_date": audit_period.start_date + relativedelta(days=55),
        }
        if is_2026:
            visit_kwargs["hospital_admission_reason_2026"] = dka_code
        else:
            visit_kwargs["hospital_admission_reason"] = dka_code
        VisitFactory(**visit_kwargs)

        self._create_submission(pdu, audit_period, user, [patient])

        qs = annotate_admissions(
            build_base_queryset(pdu, audit_period, type1_only=False), audit_period
        )
        rows = {
            row["pk"]: row
            for row in qs.values(
                "pk", "number_of_admissions", "number_of_dka_admissions"
            )
        }

        assert patient.pk in rows
        assert rows[patient.pk]["number_of_admissions"] == 0
        assert rows[patient.pk]["number_of_dka_admissions"] == 1, (
            "DKA admission 5 days before diagnosis is within the +/- 10 day window"
        )

    @pytest.mark.parametrize(
        "get_audit_period,stabilisation_code,dka_code,is_2026",
        [
            (_get_audit_period_2021.__func__, 1, 2, False),  # 2021 dataset
            (_get_audit_period_2026.__func__, 5, 1, True),  # 2026 dataset
        ],
        ids=["2021", "2026"],
    )
    def test_10_day_diagnosis_window_boundary_is_inclusive(
        self,
        get_audit_period,
        stabilisation_code,
        dka_code,
        is_2026,
        seed_groups_fixture,
        seed_users_fixture,
        seed_audit_periods_fixture,
    ):
        """An admission exactly 10 days from diagnosis is within the window;
        an admission 11 days from diagnosis is outside it."""
        user, pdu = self._get_user_and_pdu()
        audit_period = get_audit_period()

        # DKA admission exactly 10 days after diagnosis: within the window
        at_boundary = PatientFactory(
            nhs_number=f"800{3 if not is_2026 else 13}333333",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=15),
            diagnosis_date=audit_period.start_date + relativedelta(days=40),
        )
        visit_kwargs_1 = {
            "patient": at_boundary,
            "visit_date": audit_period.start_date + relativedelta(days=50),
            "hospital_admission_date": audit_period.start_date + relativedelta(days=50),
            "hospital_discharge_date": audit_period.start_date + relativedelta(days=55),
        }
        if is_2026:
            visit_kwargs_1["hospital_admission_reason_2026"] = dka_code
        else:
            visit_kwargs_1["hospital_admission_reason"] = dka_code
        VisitFactory(**visit_kwargs_1)

        # DKA admission 11 days after diagnosis: outside the window
        past_boundary = PatientFactory(
            nhs_number=f"800{5 if not is_2026 else 15}555555",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=15),
            diagnosis_date=audit_period.start_date + relativedelta(days=39),
        )
        visit_kwargs_2 = {
            "patient": past_boundary,
            "visit_date": audit_period.start_date + relativedelta(days=50),
            "hospital_admission_date": audit_period.start_date + relativedelta(days=50),
            "hospital_discharge_date": audit_period.start_date + relativedelta(days=55),
        }
        if is_2026:
            visit_kwargs_2["hospital_admission_reason_2026"] = dka_code
        else:
            visit_kwargs_2["hospital_admission_reason"] = dka_code
        VisitFactory(**visit_kwargs_2)

        self._create_submission(pdu, audit_period, user, [at_boundary, past_boundary])

        qs = annotate_admissions(
            build_base_queryset(pdu, audit_period, type1_only=False), audit_period
        )
        rows = {
            row["pk"]: row
            for row in qs.values(
                "pk", "number_of_admissions", "number_of_dka_admissions"
            )
        }

        assert rows[at_boundary.pk]["number_of_dka_admissions"] == 1, (
            "Admission exactly 10 days after diagnosis is within the window"
        )
        assert rows[at_boundary.pk]["number_of_admissions"] == 0
        assert rows[past_boundary.pk]["number_of_dka_admissions"] == 0, (
            "Admission 11 days after diagnosis is outside the window"
        )
        assert rows[past_boundary.pk]["number_of_admissions"] == 1

    @pytest.mark.parametrize(
        "get_audit_period,stabilisation_code,dka_code,is_2026",
        [
            (_get_audit_period_2021.__func__, 1, 2, False),  # 2021 dataset
            (_get_audit_period_2026.__func__, 5, 1, True),  # 2026 dataset
        ],
        ids=["2021", "2026"],
    )
    def test_patient_aged_25_or_over_excluded(
        self,
        get_audit_period,
        stabilisation_code,
        dka_code,
        is_2026,
        seed_groups_fixture,
        seed_users_fixture,
        seed_audit_periods_fixture,
    ):
        """Patients aged 25 or over at audit period start are excluded.

        Mirrors the KPI 1 eligibility filter in count_admissions().
        """
        user, pdu = self._get_user_and_pdu()
        audit_period = get_audit_period()

        patient = PatientFactory(
            nhs_number=f"800{8 if not is_2026 else 18}888888",
            diabetes_type=DIABETES_TYPES[0][0],
            # Exactly 25 at the start of the audit period
            date_of_birth=audit_period.start_date - relativedelta(years=25),
            diagnosis_date=audit_period.start_date - relativedelta(days=200),
        )
        visit_kwargs = {
            "patient": patient,
            "visit_date": audit_period.start_date + relativedelta(days=50),
            "hospital_admission_date": audit_period.start_date + relativedelta(days=50),
            "hospital_discharge_date": audit_period.start_date + relativedelta(days=55),
        }
        if is_2026:
            visit_kwargs["hospital_admission_reason_2026"] = stabilisation_code
        else:
            visit_kwargs["hospital_admission_reason"] = stabilisation_code
        VisitFactory(**visit_kwargs)

        self._create_submission(pdu, audit_period, user, [patient])

        qs = annotate_admissions(
            build_base_queryset(pdu, audit_period, type1_only=False), audit_period
        )
        rows = {row["pk"]: row for row in qs}

        assert patient.pk not in rows, (
            "Patients aged 25 or over at audit period start should be excluded"
        )

    @pytest.mark.parametrize(
        "get_audit_period,stabilisation_code,dka_code,is_2026",
        [
            (_get_audit_period_2021.__func__, 1, 2, False),  # 2021 dataset
            (_get_audit_period_2026.__func__, 5, 1, True),  # 2026 dataset
        ],
        ids=["2021", "2026"],
    )
    def test_admissions_tab_matches_count_admissions(
        self,
        get_audit_period,
        stabilisation_code,
        dka_code,
        is_2026,
        seed_groups_fixture,
        seed_users_fixture,
        seed_audit_periods_fixture,
    ):
        """The Admissions tab lists exactly the patients counted by count_admissions.

        count_admissions powers the "Hospital Admissions" panel in the unit
        report, so the number of rows in the patient report Admissions tab
        must equal it: all diabetes types, under 25 at audit period start,
        any valid admission regardless of its timing relative to diagnosis
        (including DKA at diagnosis and non-DKA admissions within the
        +/- 10 day diagnosis window, which appear in neither column).
        """
        user, pdu = self._get_user_and_pdu()
        audit_period = get_audit_period()

        def admission_visit(patient, **kwargs):
            visit_kwargs = {
                "patient": patient,
                "visit_date": audit_period.start_date + relativedelta(days=50),
                "hospital_admission_date": audit_period.start_date
                + relativedelta(days=50),
                "hospital_discharge_date": audit_period.start_date
                + relativedelta(days=55),
            }
            if is_2026:
                visit_kwargs["hospital_admission_reason_2026"] = kwargs["reason"]
            else:
                visit_kwargs["hospital_admission_reason"] = kwargs["reason"]
            VisitFactory(**visit_kwargs)

        # Counted: T1DM patient admitted
        admitted_t1dm = PatientFactory(
            nhs_number=f"800{9 if not is_2026 else 19}999999",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=10),
            diagnosis_date=audit_period.start_date - relativedelta(days=200),
        )
        admission_visit(admitted_t1dm, reason=stabilisation_code)

        # Counted: non-T1DM patient admitted (all diabetes types)
        admitted_t2dm = PatientFactory(
            nhs_number=f"800{0 if not is_2026 else 10}000000",
            diabetes_type=DIABETES_TYPES[1][0],
            date_of_birth=audit_period.start_date - relativedelta(years=10),
            diagnosis_date=audit_period.start_date - relativedelta(days=200),
        )
        admission_visit(admitted_t2dm, reason=dka_code)

        # Counted: diagnosed during the audit year with a DKA admission
        # within +/- 10 days of diagnosis (only appears in the 'DKA at
        # diagnosis' column)
        dka_at_diagnosis = PatientFactory(
            nhs_number=f"800{1 if not is_2026 else 11}111111",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=10),
            diagnosis_date=audit_period.start_date + relativedelta(days=45),
        )
        admission_visit(dka_at_diagnosis, reason=dka_code)

        # Counted: diagnosed during the audit year with a non-DKA admission
        # within +/- 10 days of diagnosis (appears in neither column but must
        # still be listed)
        stabilisation_at_diagnosis = PatientFactory(
            nhs_number=f"800{4 if not is_2026 else 14}444444",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=10),
            diagnosis_date=audit_period.start_date + relativedelta(days=45),
        )
        admission_visit(stabilisation_at_diagnosis, reason=stabilisation_code)

        # Not counted: aged 25 at audit period start
        over_25 = PatientFactory(
            nhs_number=f"800{2 if not is_2026 else 12}222222",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=25),
            diagnosis_date=audit_period.start_date - relativedelta(days=200),
        )
        admission_visit(over_25, reason=stabilisation_code)

        # Not counted: visit but no admission
        not_admitted = PatientFactory(
            nhs_number=f"800{3 if not is_2026 else 13}333333",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=10),
            diagnosis_date=audit_period.start_date - relativedelta(days=200),
        )
        VisitFactory(
            patient=not_admitted,
            visit_date=audit_period.start_date + relativedelta(days=50),
        )

        self._create_submission(
            pdu,
            audit_period,
            user,
            [
                admitted_t1dm,
                admitted_t2dm,
                dka_at_diagnosis,
                stabilisation_at_diagnosis,
                over_25,
                not_admitted,
            ],
        )

        qs = annotate_admissions(
            build_base_queryset(pdu, audit_period, type1_only=False), audit_period
        )
        listed_pks = set(qs.values_list("pk", flat=True))

        assert listed_pks == {
            admitted_t1dm.pk,
            admitted_t2dm.pk,
            dka_at_diagnosis.pk,
            stabilisation_at_diagnosis.pk,
        }
        assert count_admissions(pdu, audit_period) == 4
        assert qs.count() == count_admissions(pdu, audit_period)
