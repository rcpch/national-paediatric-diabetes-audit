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
        """Test that a non-DKA admission is counted."""
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
    def test_dka_admission_counted(
        self,
        get_audit_period,
        stabilisation_code,
        dka_code,
        is_2026,
        seed_groups_fixture,
        seed_users_fixture,
        seed_audit_periods_fixture,
    ):
        """Test that DKA admissions are counted correctly."""
        user, pdu = self._get_user_and_pdu()
        audit_period = get_audit_period()

        patient = PatientFactory(
            nhs_number=f"800{4 if not is_2026 else 14}444444",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=15),
            diagnosis_date=audit_period.start_date - relativedelta(days=200),
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
        assert rows[patient.pk]["number_of_admissions"] == 1
        assert rows[patient.pk]["number_of_dka_admissions"] == 1, (
            f"DKA admission (code {dka_code}) must be counted"
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
    def test_admission_too_soon_after_diagnosis_excluded(
        self,
        get_audit_period,
        stabilisation_code,
        dka_code,
        is_2026,
        seed_groups_fixture,
        seed_users_fixture,
        seed_audit_periods_fixture,
    ):
        """Test that admissions within 90 days of diagnosis are excluded."""
        user, pdu = self._get_user_and_pdu()
        audit_period = get_audit_period()

        patient = PatientFactory(
            nhs_number=f"800{6 if not is_2026 else 16}666666",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=15),
            diagnosis_date=audit_period.start_date + relativedelta(days=10),
        )
        # Admission only 60 days after diagnosis (should be excluded)
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
        rows = {row["pk"]: row for row in qs}

        assert patient.pk not in rows, (
            "Admission within 90 days of diagnosis should be excluded"
        )

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
        """Test that multiple admissions per patient are counted correctly."""
        user, pdu = self._get_user_and_pdu()
        audit_period = get_audit_period()

        patient = PatientFactory(
            nhs_number=f"800{7 if not is_2026 else 17}777777",
            diabetes_type=DIABETES_TYPES[0][0],
            date_of_birth=audit_period.start_date - relativedelta(years=15),
            diagnosis_date=audit_period.start_date - relativedelta(days=200),
        )
        # First admission: Stabilisation
        visit_kwargs_1 = {
            "patient": patient,
            "visit_date": audit_period.start_date + relativedelta(days=50),
            "hospital_admission_date": audit_period.start_date + relativedelta(days=50),
            "hospital_discharge_date": audit_period.start_date + relativedelta(days=55),
        }
        if is_2026:
            visit_kwargs_1["hospital_admission_reason_2026"] = stabilisation_code
        else:
            visit_kwargs_1["hospital_admission_reason"] = stabilisation_code
        VisitFactory(**visit_kwargs_1)

        # Second admission: DKA
        visit_kwargs_2 = {
            "patient": patient,
            "visit_date": audit_period.start_date + relativedelta(days=150),
            "hospital_admission_date": audit_period.start_date
            + relativedelta(days=150),
            "hospital_discharge_date": audit_period.start_date
            + relativedelta(days=155),
        }
        if is_2026:
            visit_kwargs_2["hospital_admission_reason_2026"] = dka_code
        else:
            visit_kwargs_2["hospital_admission_reason"] = dka_code
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
        assert rows[patient.pk]["number_of_admissions"] == 2, (
            "Both admissions should be counted"
        )
        assert rows[patient.pk]["number_of_dka_admissions"] == 1, (
            "Only DKA admission should be counted in DKA field"
        )
