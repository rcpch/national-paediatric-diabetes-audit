import logging
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum

from dateutil.relativedelta import relativedelta
from django.db.models import (
    BooleanField,
    Case,
    CharField,
    Count,
    DecimalField,
    Exists,
    F,
    IntegerField,
    OuterRef,
    Q,
    Value,
    When,
    Subquery,
    ExpressionWrapper,
    DurationField,
    Func,
)

# Django imports
from django.views.generic import ListView
from project.constants.hba1c_format import HBA1C_FORMATS
from project.constants.hospital_admission_reasons import HOSPITAL_ADMISSION_REASONS
from project.npda.kpi_class.kpis import CalculateKPIS
from project.npda.models import Patient, AuditPeriod, Visit
from project.npda.models.db_functions import Round
from project.npda.views.mixins import PDUPermissionMixin, LoginAndOTPRequiredMixin
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


class TableCategories(Enum):
    HEALTH_CHECKS = "health_checks"
    ADDITIONAL_CARE_PROCESSES = "additional_care_processes"
    CARE_AT_DIAGNOSIS = "care_at_diagnosis"
    ADMISSIONS = "admissions"
    TREATMENT = "treatment"
    OUTCOMES = "outcomes"

    @classmethod
    def values(cls):
        return [c.value for c in cls]

    @classmethod
    def choices(cls):
        # Return a list of tuples (value, label)
        return [
            (cls.HEALTH_CHECKS.value, "Health Checks"),
            (cls.ADDITIONAL_CARE_PROCESSES.value, "Additional Care Processes"),
            (cls.CARE_AT_DIAGNOSIS.value, "Care at Diagnosis"),
            (cls.ADMISSIONS.value, "Admissions"),
            (cls.TREATMENT.value, "Treatment"),
            (cls.OUTCOMES.value, "Outcomes"),
        ]

    @classmethod
    def default(cls):
        return cls.HEALTH_CHECKS.value


class PatientReportView(
    LoginAndOTPRequiredMixin,
    PDUPermissionMixin,
    ListView,
):
    # Perms
    permission_denied_message = "You must be logged in to view this page."

    # Context
    model = Patient
    template_name = "patient_report/patient_report.html"
    context_object_name = "patients"
    paginate_by = 50

    def _calculate_hba1c_values(
        self, pt_qs: QuerySet[Patient], calculate_kpis: CalculateKPIS
    ):
        """Helper function to calculate HbA1c values for a queryset."""
        patient_ids = set(pt_qs.values_list("pk", flat=True))

        valid_visits_with_hba1c = (
            calculate_kpis._get_valid_visits_for_kpi_44_and_45(
                Patient.objects.filter(pk__in=patient_ids)
            )
            .annotate(
                hba1c_mmol_mol=Case(
                    When(
                        Q(hba1c_format=HBA1C_FORMATS[0][0]),
                        then=F("hba1c"),
                    ),
                    When(
                        Q(hba1c_format=HBA1C_FORMATS[1][0]),
                        then=(F("hba1c") - Round(Decimal("2.152")))
                        / Decimal("0.09148"),
                    ),
                    default=None,
                    output_field=DecimalField(max_digits=5, decimal_places=2),
                )
            )
            .values("hba1c_mmol_mol", "patient__pk")
            .filter(hba1c_mmol_mol__isnull=False)
        )
        hba1c_values_by_patient = defaultdict(list)
        for visit in valid_visits_with_hba1c:
            hba1c_values_by_patient[visit["patient__pk"]].append(
                visit["hba1c_mmol_mol"]
            )
        for patient in pt_qs:
            hba1c_values = hba1c_values_by_patient.get(patient["pk"], [])
            if hba1c_values:
                mean_hba1c_mmol_mol = calculate_kpis.calculate_mean(hba1c_values)
                median_hba1c_mmol_mol = calculate_kpis.calculate_median(hba1c_values)
                patient["kpi_44_mean_hba1c"] = round(mean_hba1c_mmol_mol)
                patient["kpi_45_median_hba1c"] = round(median_hba1c_mmol_mol)
                patient["mean_hba1c_pct"] = round(
                    (0.09148 * mean_hba1c_mmol_mol) + 2.152
                    if mean_hba1c_mmol_mol > 0 and mean_hba1c_mmol_mol is not None
                    else None,
                    1,
                )
                patient["median_hba1c_pct"] = round(
                    (0.09148 * median_hba1c_mmol_mol) + 2.152
                    if median_hba1c_mmol_mol > 0 and median_hba1c_mmol_mol is not None
                    else None,
                    1,
                )
            else:
                patient["kpi_44_mean_hba1c"] = None
                patient["kpi_45_median_hba1c"] = None
                patient["mean_hba1c_pct"] = None
                patient["median_hba1c_pct"] = None
        return pt_qs

    def get_queryset(self):
        request = self.request
        category = request.GET.get("category", TableCategories.default())
        sort_field = request.GET.get("sort")
        sort_order = request.GET.get("order", "asc")
        if category not in TableCategories.values():
            raise ValueError(f"Invalid category: {category}")
        self.selected_category = category
        pz_code = request.session.get("pz_code")
        calculation_date = AuditPeriod.objects.get_audit_period_for_request(
            self.request
        ).kpi_calculation_date()
        calculate_kpis = CalculateKPIS(
            calculation_date=calculation_date, return_pt_querysets=True
        )
        calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])
        patient_identifier = (
            "nhs_number" if pz_code != "PZ248" else "unique_reference_number"
        )
        all_t1dm_pts = (
            calculate_kpis.calculate_kpi_3_total_t1dm()
            .patient_querysets["eligible"]
            .annotate(patient_identifier=F(patient_identifier))
        )
        all_t1dm_pts_with_complete_year_of_care = (
            calculate_kpis.calculate_kpi_5_total_t1dm_complete_year().patient_querysets[
                "eligible"
            ]
        )
        pt_qs = all_t1dm_pts.annotate(
            is_complete_year_of_care=Case(
                When(
                    Exists(
                        all_t1dm_pts_with_complete_year_of_care.filter(
                            pk=OuterRef("pk")
                        )
                    ),
                    then=True,
                ),
                default=False,
                output_field=BooleanField(),
            )
        )
        if self.selected_category == TableCategories.HEALTH_CHECKS.value:
            # Pre-calculate totals for the health checks from the base queryset before adding category-specific annotations
            complete_year_patients = pt_qs.filter(is_complete_year_of_care=True)
            
            # Calculate totals using the KPI methods directly
            self.total_passed_hba1c = calculate_kpis.calculate_kpi_25_hba1c().patient_querysets["passed"].filter(
                pk__in=complete_year_patients.values_list("pk", flat=True)
            ).count()
            self.total_eligible_hba1c = complete_year_patients.count()
            
            self.total_passed_bmi = calculate_kpis.calculate_kpi_26_bmi().patient_querysets["passed"].filter(
                pk__in=complete_year_patients.values_list("pk", flat=True)
            ).count()
            self.total_eligible_bmi = complete_year_patients.count()
            
            self.total_passed_thyroid_screen = calculate_kpis.calculate_kpi_27_thyroid_screen().patient_querysets["passed"].filter(
                pk__in=complete_year_patients.values_list("pk", flat=True)
            ).count()
            self.total_eligible_thyroid_screen = complete_year_patients.count()
            
            # For age-specific checks (12+ years old)
            complete_year_12plus = complete_year_patients.filter(
                date_of_birth__lte=calculation_date - relativedelta(years=12)
            )
            
            self.total_passed_blood_pressure = calculate_kpis.calculate_kpi_28_blood_pressure().patient_querysets["passed"].filter(
                pk__in=complete_year_12plus.values_list("pk", flat=True)
            ).count()
            self.total_eligible_blood_pressure = complete_year_12plus.count()
            
            self.total_passed_urinary_albumin = calculate_kpis.calculate_kpi_29_urinary_albumin().patient_querysets["passed"].filter(
                pk__in=complete_year_12plus.values_list("pk", flat=True)
            ).count()
            self.total_eligible_urinary_albumin = complete_year_12plus.count()
            
            self.total_passed_foot_exam = calculate_kpis.calculate_kpi_31_foot_examination().patient_querysets["passed"].filter(
                pk__in=complete_year_12plus.values_list("pk", flat=True)
            ).count()
            self.total_eligible_foot_exam = complete_year_12plus.count()
            pt_qs = pt_qs.annotate(
                is_gte_12yo=Q(
                    date_of_birth__lte=calculation_date - relativedelta(years=12)
                ),
                passed_hba1c=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_25_hba1c()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=True,
                    ),
                    default=False,
                    output_field=BooleanField(),
                ),
                passed_bmi=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_26_bmi()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=True,
                    ),
                    default=False,
                    output_field=BooleanField(),
                ),
                passed_thyroid_screen=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_27_thyroid_screen()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=True,
                    ),
                    default=False,
                    output_field=BooleanField(),
                ),
                passed_blood_pressure=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_28_blood_pressure()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=True,
                    ),
                    default=Case(
                        When(is_gte_12yo=True, then=False),
                        default=None,
                        output_field=BooleanField(),
                    ),
                    output_field=BooleanField(),
                ),
                passed_urinary_albumin=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_29_urinary_albumin()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=True,
                    ),
                    default=Case(
                        When(is_gte_12yo=True, then=False),
                        default=None,
                        output_field=BooleanField(),
                    ),
                    output_field=BooleanField(),
                ),
                passed_retinal_screening=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_30_retinal_screening()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=True,
                    ),
                    default=Case(
                        When(is_gte_12yo=True, then=False),
                        default=None,
                        output_field=BooleanField(),
                    ),
                    output_field=BooleanField(),
                ),
                passed_foot_exam=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_31_foot_examination()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=True,
                    ),
                    default=Case(
                        When(is_gte_12yo=True, then=False),
                        default=None,
                        output_field=BooleanField(),
                    ),
                    output_field=BooleanField(),
                ),
                num_passed=Case(
                    When(
                        is_gte_12yo=True,
                        then=(
                            Case(When(passed_hba1c=True, then=1), default=0)
                            + Case(When(passed_bmi=True, then=1), default=0)
                            + Case(When(passed_thyroid_screen=True, then=1), default=0)
                            + Case(When(passed_blood_pressure=True, then=1), default=0)
                            + Case(When(passed_urinary_albumin=True, then=1), default=0)
                            + Case(When(passed_foot_exam=True, then=1), default=0)
                        ),
                    ),
                    When(
                        is_gte_12yo=False,
                        then=(
                            Case(When(passed_hba1c=True, then=1), default=0)
                            + Case(When(passed_bmi=True, then=1), default=0)
                            + Case(When(passed_thyroid_screen=True, then=1), default=0)
                        ),
                    ),
                    default=0,
                    output_field=IntegerField(),
                ),
                num_total=Case(
                    When(is_gte_12yo=True, then=6),
                    When(is_gte_12yo=False, then=3),
                    default=0,
                    output_field=IntegerField(),
                ),
            ).values(
                "pk",
                "patient_identifier",
                "is_gte_12yo",
                "is_complete_year_of_care",
                "passed_hba1c",
                "passed_bmi",
                "passed_thyroid_screen",
                "passed_blood_pressure",
                "passed_urinary_albumin",
                "passed_foot_exam",
                "num_passed",
                "num_total",
                "passed_retinal_screening",
            )
        elif self.selected_category == TableCategories.ADDITIONAL_CARE_PROCESSES.value:
            pt_qs = pt_qs.annotate(
                hba1c_4plus=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_33_hba1c_4plus()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=True,
                    ),
                    default=False,
                    output_field=BooleanField(),
                ),
                psychological_assessment=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_34_psychological_assessment()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=True,
                    ),
                    default=False,
                    output_field=BooleanField(),
                ),
                is_gte_12yo=Q(
                    date_of_birth__lte=calculation_date - relativedelta(years=12)
                ),
                smoking_status=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_35_smoking_status_screened()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=True,
                    ),
                    default=Case(
                        When(is_gte_12yo=True, then=False),
                        default=None,
                        output_field=BooleanField(),
                    ),
                    output_field=BooleanField(),
                ),
                smoking_cessation_referral=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_36_referral_to_smoking_cessation_service()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=True,
                    ),
                    default=Case(
                        When(is_gte_12yo=True, then=False),
                        default=None,
                        output_field=BooleanField(),
                    ),
                    output_field=BooleanField(),
                ),
                additional_dietetic_appt_offered=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_37_additional_dietetic_appointment_offered()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=True,
                    ),
                    default=False,
                    output_field=BooleanField(),
                ),
                pts_attending_additional_dietetic_appt=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_38_patients_attending_additional_dietetic_appointment()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=True,
                    ),
                    default=False,
                    output_field=BooleanField(),
                ),
                influenza_immunisation_recommended=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_39_influenza_immunisation_recommended()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=True,
                    ),
                    default=False,
                    output_field=BooleanField(),
                ),
                sick_day_rules_advice=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_39_influenza_immunisation_recommended()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=True,
                    ),
                    default=False,
                    output_field=BooleanField(),
                ),
            ).values(
                "pk",
                "patient_identifier",
                "is_complete_year_of_care",
                "hba1c_4plus",
                "psychological_assessment",
                "smoking_status",
                "smoking_cessation_referral",
                "additional_dietetic_appt_offered",
                "pts_attending_additional_dietetic_appt",
                "influenza_immunisation_recommended",
                "sick_day_rules_advice",
            )
        elif self.selected_category == TableCategories.CARE_AT_DIAGNOSIS.value:
            today = date.today()
            all_t1dm_pts = all_t1dm_pts.filter(
                Q(diagnosis_date__gte=today - relativedelta(days=90))
            )
            all_t1dm_pts_with_complete_year_of_care = (
                all_t1dm_pts_with_complete_year_of_care.filter(
                    Q(diagnosis_date__gte=today - relativedelta(days=90))
                )
            )

            pt_qs = (
                pt_qs.filter(Q(diagnosis_date__gte=today - relativedelta(days=90)))
                .annotate(
                    coeliac_disease_screening=Case(
                        When(
                            Exists(
                                calculate_kpis.calculate_kpi_41_coeliac_disease_screening()
                                .patient_querysets["passed"]
                                .filter(pk=OuterRef("pk"))
                            ),
                            then=True,
                        ),
                        default=False,
                        output_field=BooleanField(),
                    ),
                    thyroid_disease_screening=Case(
                        When(
                            Exists(
                                calculate_kpis.calculate_kpi_42_thyroid_disease_screening()
                                .patient_querysets["passed"]
                                .filter(pk=OuterRef("pk"))
                            ),
                            then=True,
                        ),
                        default=False,
                        output_field=BooleanField(),
                    ),
                    carbohydrate_counting_education=Case(
                        When(
                            Exists(
                                calculate_kpis.calculate_kpi_43_carbohydrate_counting_education()
                                .patient_querysets["passed"]
                                .filter(pk=OuterRef("pk"))
                            ),
                            then=True,
                        ),
                        default=False,
                        output_field=BooleanField(),
                    ),
                )
                .values(
                    "pk",
                    "patient_identifier",
                    "is_complete_year_of_care",
                    "coeliac_disease_screening",
                    "thyroid_disease_screening",
                    "carbohydrate_counting_education",
                )
            )
        elif self.selected_category == TableCategories.ADMISSIONS.value:
            pt_qs = (
                pt_qs.annotate(
                    number_of_admissions=Count(
                        "visit",
                        filter=Q(
                            Q(
                                visit__hospital_admission_date__range=calculate_kpis.AUDIT_DATE_RANGE
                            )
                            | Q(
                                visit__hospital_discharge_date__range=calculate_kpis.AUDIT_DATE_RANGE
                            )
                        )
                        & Q(
                            visit__hospital_admission_reason__in=[
                                choice[0] for choice in HOSPITAL_ADMISSION_REASONS
                            ]
                        )
                        & Q(visit__visit_date__range=calculate_kpis.AUDIT_DATE_RANGE),
                        distinct=True,
                    ),
                    number_of_dka_admissions=Count(
                        "visit",
                        filter=Q(
                            Q(
                                visit__hospital_admission_date__range=calculate_kpis.AUDIT_DATE_RANGE
                            )
                            | Q(
                                visit__hospital_discharge_date__range=calculate_kpis.AUDIT_DATE_RANGE
                            )
                        )
                        & Q(
                            visit__hospital_admission_reason=HOSPITAL_ADMISSION_REASONS[
                                1
                            ][0]
                        )
                        & Q(visit__visit_date__range=calculate_kpis.AUDIT_DATE_RANGE),
                        distinct=True,
                    ),
                )
                .filter(
                    Q(number_of_admissions__gt=0) | Q(number_of_dka_admissions__gt=0)
                )
                .values(
                    "pk",
                    "patient_identifier",
                    "is_complete_year_of_care",
                    "number_of_admissions",
                    "number_of_dka_admissions",
                )
            )
            pt_qs = self._calculate_hba1c_values(pt_qs, calculate_kpis)

        elif self.selected_category == TableCategories.OUTCOMES.value:
            # get ALL patients for current submission
            pt_qs = (
                calculate_kpis.calculate_kpi_1_total_eligible()
                .patient_querysets["eligible"]
                .annotate(
                    patient_identifier=F(patient_identifier),
                    is_complete_year_of_care=Case(
                        When(
                            Exists(
                                all_t1dm_pts_with_complete_year_of_care.filter(
                                    pk=OuterRef("pk")
                                )
                            ),
                            then=True,
                        ),
                        default=False,
                        output_field=BooleanField(),
                    ),
                    latest_hba1c_date=Subquery(
                        Visit.objects.filter(
                            patient=OuterRef("pk"),
                            visit_date__range=calculate_kpis.AUDIT_DATE_RANGE,
                            hba1c__isnull=False,
                        )
                        .order_by("-visit_date")
                        .values("visit_date")[:1]
                    ),
                    previous_to_latest_hba1c_date=Subquery(
                        Visit.objects.filter(
                            patient=OuterRef("pk"),
                            visit_date__range=calculate_kpis.AUDIT_DATE_RANGE,
                            hba1c__isnull=False,
                        )
                        .order_by("-visit_date")
                        .values("visit_date")[1:2]
                    ),
                    days_delta_between_latest_and_previous_hba1c=Case(
                        When(
                            Q(latest_hba1c_date__isnull=False) & Q(previous_to_latest_hba1c_date__isnull=False),
                            then=Func(
                                ExpressionWrapper(
                                    F("latest_hba1c_date") - F("previous_to_latest_hba1c_date"),
                                    output_field=DurationField()
                                ),
                                function='EXTRACT',
                                template="EXTRACT(DAY FROM %(expressions)s)",
                                output_field=IntegerField()
                            )
                        ),
                        default=None,
                        output_field=IntegerField(),
                    ),
                    latest_hba1c_mmol_mol=Subquery(
                        Visit.objects.filter(
                            patient=OuterRef("pk"),
                            visit_date__range=calculate_kpis.AUDIT_DATE_RANGE,
                            hba1c__isnull=False,
                        )
                        .annotate(
                            hba1c_mmol_mol=Case(
                                When(
                                    Q(hba1c_format=HBA1C_FORMATS[0][0]),
                                    then=F("hba1c"),
                                ),
                                When(
                                    Q(hba1c_format=HBA1C_FORMATS[1][0]),
                                    then=(F("hba1c") - Round(Decimal("2.152")))
                                    / Decimal("0.09148"),
                                ),
                                default=None,
                                output_field=IntegerField(),
                            )
                        )
                        .order_by("-hba1c_date")
                        .values("hba1c_mmol_mol")[:1]
                    ),
                    latest_hba1c_pct=Case(
                        When(
                            Q(latest_hba1c_mmol_mol__isnull=False)
                            & Q(latest_hba1c_mmol_mol__gt=0),
                            then=(Decimal("0.09148") * F("latest_hba1c_mmol_mol"))
                            + Decimal("2.152"),
                        ),
                        default=None,
                        output_field=DecimalField(max_digits=4, decimal_places=1),
                    ),
                    previous_to_latest_hba1c_mmol_mol=Subquery(
                        Visit.objects.filter(
                            patient=OuterRef("pk"),
                            visit_date__range=calculate_kpis.AUDIT_DATE_RANGE,
                            hba1c__isnull=False,
                        )
                        .annotate(
                            hba1c_mmol_mol=Case(
                                When(
                                    Q(hba1c_format=HBA1C_FORMATS[0][0]),
                                    then=F("hba1c"),
                                ),
                                When(
                                    Q(hba1c_format=HBA1C_FORMATS[1][0]),
                                    then=(F("hba1c") - Round(Decimal("2.152")))
                                    / Decimal("0.09148"),
                                ),
                                default=None,
                                output_field=IntegerField(),
                            )
                        )
                        .order_by("-hba1c_date")
                        .values("hba1c_mmol_mol")[1:2]
                    ),
                    previous_to_latest_hba1c_pct=Case(
                        When(
                            Q(previous_to_latest_hba1c_mmol_mol__isnull=False)
                            & Q(previous_to_latest_hba1c_mmol_mol__gt=0),
                            then=(
                                Decimal("0.09148")
                                * F("previous_to_latest_hba1c_mmol_mol")
                            )
                            + Decimal("2.152"),
                        ),
                        default=None,
                        output_field=DecimalField(max_digits=4, decimal_places=1),
                    ),
                    hba1c_delta=Case(
                        When(
                            Q(latest_hba1c_mmol_mol__isnull=False)
                            & Q(previous_to_latest_hba1c_mmol_mol__isnull=False),
                            then=Round(
                                (
                                    F("latest_hba1c_mmol_mol")
                                    - F("previous_to_latest_hba1c_mmol_mol")
                                )
                                * Decimal("100.0")
                                / F("previous_to_latest_hba1c_mmol_mol")
                            ),
                        ),
                        default=None,
                        output_field=DecimalField(max_digits=3, decimal_places=1),
                    ),
                )
                .values(
                    "pk",
                    "patient_identifier",
                    "is_complete_year_of_care",
                    "latest_hba1c_mmol_mol",
                    "latest_hba1c_pct",
                    "previous_to_latest_hba1c_mmol_mol",
                    "previous_to_latest_hba1c_pct",
                    "hba1c_delta",
                    "latest_hba1c_date",
                    "previous_to_latest_hba1c_date",
                    "days_delta_between_latest_and_previous_hba1c",
                )
            )

        elif self.selected_category == TableCategories.TREATMENT.value:
            pt_qs = pt_qs.annotate(
                treatment_regimen=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_13_one_to_three_injections_per_day()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=Value("1-3 injections/day"),
                    ),
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_14_four_or_more_injections_per_day()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=Value("4+ injections/day"),
                    ),
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_15_insulin_pump()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=Value("Insulin pump"),
                    ),
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_16_one_to_three_injections_plus_other_medication()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=Value("1-3 injections + blood glucose lowering meds"),
                    ),
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_17_four_or_more_injections_plus_other_medication()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=Value("4+ injections + blood glucose lowering meds"),
                    ),
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_18_insulin_pump_plus_other_medication()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=Value("Insulin pump + blood glucose lowering meds"),
                    ),
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_19_dietary_management_alone()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=Value("Dietary management alone"),
                    ),
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_20_dietary_management_plus_other_medication()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=Value("Dietary management + blood glucose lowering meds"),
                    ),
                    default=Value("No treatment regimen"),
                    output_field=CharField(),
                ),
                glucose_monitoring=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_21_flash_glucose_monitor()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=Value("Flash glucose monitor"),
                    ),
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_22_real_time_cgm_with_alarms()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=Value("Continuous glucose monitor with alarms"),
                    ),
                    default=Value("No glucose monitoring"),
                    output_field=CharField(),
                ),
                hcl=Case(
                    When(
                        Exists(
                            calculate_kpis.calculate_kpi_24_hybrid_closed_loop_system()
                            .patient_querysets["passed"]
                            .filter(pk=OuterRef("pk"))
                        ),
                        then=Value("Yes"),
                    ),
                    default=Value("No"),
                    output_field=CharField(),
                ),
            ).values(
                "pk",
                "patient_identifier",
                "is_complete_year_of_care",
                "treatment_regimen",
                "glucose_monitoring",
                "hcl",
            )

        # Sort the queryset based on the selected sort field and order
        if sort_field:
            # Handle sort direction
            if sort_order == "desc":
                sort_field = f"-{sort_field}"

            # Handle HbA1c sorting
            if sort_field.replace("-", "") in [
                "kpi_44_mean_hba1c",
                "kpi_45_median_hba1c",
            ]:
                reverse = sort_order == "desc"
                field_name = sort_field.replace("-", "")
                # Calculate HbA1c values
                pt_qs = self._calculate_hba1c_values(pt_qs, calculate_kpis)
                
                pt_qs = sorted(
                    pt_qs,
                    key=lambda p: (
                        p.get(field_name) is None, 
                        p.get(field_name) or 0,
                    ),
                    reverse=reverse,
                )
            else:
                pt_qs = pt_qs.order_by(sort_field)
                pt_qs = self._calculate_hba1c_values(pt_qs, calculate_kpis)
        else:
            # Default ordering
            pt_qs = pt_qs.order_by("-is_complete_year_of_care", "nhs_number")
            pt_qs = self._calculate_hba1c_values(pt_qs, calculate_kpis)

        return pt_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Jersey
        if self.request.session.get("pz_code") == "PZ248":
            context["is_jersey"] = True
        else:
            context["is_jersey"] = False

        # Add table categories to the context
        context["table_categories"] = TableCategories.choices()
        context["selected_category"] = self.selected_category

        # Add sorting parameters to the context for pagination links
        context["sort_field"] = self.request.GET.get("sort", "")
        context["sort_order"] = self.request.GET.get("order", "asc")

        if self.selected_category == TableCategories.HEALTH_CHECKS.value:
            # Set ineligible reasons
            context["ineligible_reasons"] = {
                "blood_pressure": "Not required as less than 12 years old",
                "urinary_albumin": "Not required as less than 12 years old",
                "foot_exam": "Not required as less than 12 years old",
                "retinal_screening": "Not required as less than 12 years old",
            }
            
            # Use the totals calculated in get_queryset()
            context["total_passed_bmi"] = getattr(self, 'total_passed_bmi', 0)
            context["total_eligible_bmi"] = getattr(self, 'total_eligible_bmi', 0)
            context["total_passed_hba1c"] = getattr(self, 'total_passed_hba1c', 0)
            context["total_eligible_hba1c"] = getattr(self, 'total_eligible_hba1c', 0)
            context["total_passed_thyroid_screen"] = getattr(self, 'total_passed_thyroid_screen', 0)
            context["total_eligible_thyroid_screen"] = getattr(self, 'total_eligible_thyroid_screen', 0)
            context["total_passed_blood_pressure"] = getattr(self, 'total_passed_blood_pressure', 0)
            context["total_eligible_blood_pressure"] = getattr(self, 'total_eligible_blood_pressure', 0)
            context["total_passed_urinary_albumin"] = getattr(self, 'total_passed_urinary_albumin', 0)
            context["total_eligible_urinary_albumin"] = getattr(self, 'total_eligible_urinary_albumin', 0)
            context["total_passed_foot_exam"] = getattr(self, 'total_passed_foot_exam', 0)
            context["total_eligible_foot_exam"] = getattr(self, 'total_eligible_foot_exam', 0)
        elif self.selected_category == TableCategories.ADDITIONAL_CARE_PROCESSES.value:
            context["ineligible_reasons"] = {
                "smoking_status": "Not required as less than 12 years old",
                "smoking_cessation_referral": "Not required as less than 12 years old",
            }

        return context

    def get_template_names(self) -> list[str]:
        if self.request.htmx:
            # Just render buttons and rows
            if self.selected_category == TableCategories.HEALTH_CHECKS.value:
                return ["patient_report/health_checks_table_partial.html"]
            elif (
                self.selected_category
                == TableCategories.ADDITIONAL_CARE_PROCESSES.value
            ):
                return ["patient_report/additional_care_processes_table_partial.html"]
            elif self.selected_category == TableCategories.CARE_AT_DIAGNOSIS.value:
                return ["patient_report/care_at_diagnosis_table_partial.html"]
            elif self.selected_category == TableCategories.ADMISSIONS.value:
                return ["patient_report/admissions_table_partial.html"]
            elif self.selected_category == TableCategories.TREATMENT.value:
                return ["patient_report/treatment_table_partial.html"]
            elif self.selected_category == TableCategories.OUTCOMES.value:
                return ["patient_report/outcomes_table_partial.html"]
            else:
                return ["patient_report/health_checks_table_partial.html"]

        return ["patient_report/patient_report.html"]
