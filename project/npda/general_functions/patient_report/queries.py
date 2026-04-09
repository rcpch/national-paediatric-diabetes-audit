from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import (
    BooleanField,
    Case,
    CharField,
    Count,
    DateField,
    DecimalField,
    DurationField,
    Exists,
    ExpressionWrapper,
    F,
    Func,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)

from project.constants import TREATMENT_TYPES
from project.constants.diabetes_treatment import INSULIN_TREATMENT
from project.constants.diabetes_types import DIABETES_TYPES
from project.constants.glucose_monitoring_types import GLUCOSE_MONITORING_TYPES
from project.constants.hba1c_format import HBA1C_FORMATS
from project.constants.hospital_admission_reasons import HOSPITAL_ADMISSION_REASONS
from project.constants.yes_no_unknown import YES_NO_UNKNOWN
from project.npda.models import Patient, Transfer, Visit
from project.npda.models.db_functions import Round


def _patient_identifier_field(pdu) -> str:
    return "unique_reference_number" if pdu.pz_code == "PZ248" else "nhs_number"


def build_base_queryset(pdu, audit_period, *, type1_only=True):
    audit_range = (audit_period.start_date, audit_period.end_date)
    patient_identifier = _patient_identifier_field(pdu)

    filters = Q(
        submissions__submission_active=True,
        submissions__audit_period=audit_period,
        submissions__paediatric_diabetes_unit=pdu,
        visit__visit_date__range=audit_range,
    )
    if type1_only:
        filters &= Q(diabetes_type=DIABETES_TYPES[0][0])

    base_qs = (
        Patient.objects.filter(filters)
        .distinct()
        .annotate(
            patient_identifier=F(patient_identifier),
            is_gte_12yo=Q(
                date_of_birth__lte=audit_period.start_date - relativedelta(years=12)
            ),
            dx_over_1y=Q(
                diagnosis_date__lte=audit_period.start_date - relativedelta(years=1)
            ),
            is_incomplete_year_of_care=Case(
                # Diagnosed within the audit year
                When(
                    Q(diagnosis_date__range=audit_range),
                    then=True,
                ),
                # Transferred out during the audit year
                When(
                    Exists(
                        Transfer.objects.filter(
                            patient=OuterRef("pk"),
                            date_leaving_service__range=audit_range,
                        )
                    ),
                    then=True,
                ),
                default=False,
                output_field=BooleanField(),
            ),
        )
        .annotate(
            is_complete_year_of_care=Case(
                When(is_incomplete_year_of_care=True, then=False),
                default=True,
                output_field=BooleanField(),
            )
        )
    )

    return base_qs


def annotate_health_checks(qs, audit_period):
    audit_range = (audit_period.start_date, audit_period.end_date)

    hba1c_exists = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            hba1c__isnull=False,
            hba1c_date__range=audit_range,
        )
    )
    bmi_exists = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            bmi__isnull=False,
            height_weight_observation_date__range=audit_range,
        )
    )
    thyroid_exists = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            thyroid_function_date__range=audit_range,
        )
    )
    bp_exists = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            systolic_blood_pressure__isnull=False,
            blood_pressure_observation_date__range=audit_range,
        )
    )
    acr_exists = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            albumin_creatinine_ratio__isnull=False,
            albumin_creatinine_ratio_date__range=audit_range,
        )
    )
    foot_exists = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            foot_examination_observation_date__range=audit_range,
        )
    )
    retinal_exists = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            retinal_screening_observation_date__range=audit_range,
            retinal_screening_result__isnull=False,
        )
    )

    latest_retinal_screening_date = Subquery(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            retinal_screening_observation_date__range=audit_range,
            retinal_screening_result__isnull=False,
        )
        .order_by("-retinal_screening_observation_date")
        .values("retinal_screening_observation_date")[:1]
    )

    return qs.annotate(
        passed_hba1c=Case(
            When(hba1c_exists, then=True),
            default=False,
            output_field=BooleanField(),
        ),
        passed_bmi=Case(
            When(bmi_exists, then=True),
            default=False,
            output_field=BooleanField(),
        ),
        passed_thyroid_screen=Case(
            When(Q(dx_over_1y=True) & thyroid_exists, then=True),
            When(Q(dx_over_1y=False), then=None),
            default=False,
            output_field=BooleanField(),
        ),
        passed_blood_pressure=Case(
            When(Q(is_gte_12yo=True) & bp_exists, then=True),
            When(Q(is_gte_12yo=False), then=None),
            default=False,
            output_field=BooleanField(),
        ),
        passed_urinary_albumin=Case(
            When(Q(is_gte_12yo=True) & acr_exists, then=True),
            When(Q(is_gte_12yo=False), then=None),
            default=False,
            output_field=BooleanField(),
        ),
        passed_foot_exam=Case(
            When(Q(is_gte_12yo=True) & foot_exists, then=True),
            When(Q(is_gte_12yo=False), then=None),
            default=False,
            output_field=BooleanField(),
        ),
        passed_retinal_screening=Case(
            When(
                Q(is_gte_12yo=True) & Q(dx_over_1y=True) & retinal_exists,
                then=Value("complete"),
            ),
            When(
                Q(is_gte_12yo=False) | Q(dx_over_1y=False), then=Value("not_required")
            ),
            default=Value(""),
            output_field=CharField(),
        ),
        latest_retinal_screening_date=latest_retinal_screening_date,
    ).annotate(
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
    )


def annotate_additional_care_processes(qs, audit_period):
    audit_range = (audit_period.start_date, audit_period.end_date)
    dataset_year = audit_period.get_dataset_year()

    hba1c_count = Count(
        "visit",
        filter=Q(
            visit__hba1c__isnull=False,
            visit__hba1c_date__range=audit_range,
        ),
        distinct=True,
    )

    psych_exists = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            psychological_screening_assessment_date__range=audit_range,
        )
    )

    if dataset_year == 2026:
        # 2026: smoking_vaping_status replaces smoking_status
        # Values: 1=non-smoker/non-vaper, 2=smoker/non-vaper, 3=vaper/non-smoker, 4=smoker+vaper
        smoking_status_exists = Exists(
            Visit.objects.filter(
                patient=OuterRef("pk"),
                visit_date__range=audit_range,
                smoking_vaping_status__in=[1, 2, 3, 4],
            )
        )
        smoker_exists = Exists(
            Visit.objects.filter(
                patient=OuterRef("pk"),
                visit_date__range=audit_range,
                smoking_vaping_status__in=[2, 4],  # current smoker (with or without vaping)
            )
        )
        smoking_referral_exists = Exists(
            Visit.objects.filter(
                patient=OuterRef("pk"),
                visit_date__range=audit_range,
                smoking_vaping_status__in=[2, 4],
                smoking_cessation_referral_date__range=audit_range,
            )
        )
    else:
        # 2021: smoking_status field
        smoking_status_exists = Exists(
            Visit.objects.filter(
                patient=OuterRef("pk"),
                visit_date__range=audit_range,
                smoking_status__in=[1, 2],
            )
        )
        smoker_exists = Exists(
            Visit.objects.filter(
                patient=OuterRef("pk"),
                visit_date__range=audit_range,
                smoking_status=2,
            )
        )
        smoking_referral_exists = Exists(
            Visit.objects.filter(
                patient=OuterRef("pk"),
                visit_date__range=audit_range,
                smoking_status=2,
                smoking_cessation_referral_date__range=audit_range,
            )
        )

    dietetic_offered_exists = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            visit_date__range=audit_range,
            dietician_additional_appointment_offered=1,
        )
    )

    dietetic_attended_exists = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            visit_date__range=audit_range,
            dietician_additional_appointment_date__range=audit_range,
        )
    )

    flu_exists = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            visit_date__range=audit_range,
            flu_immunisation_recommended_date__range=audit_range,
        )
    )

    sick_day_exists = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            visit_date__range=audit_range,
            sick_day_rules_training_date__range=audit_range,
        )
    )

    return qs.annotate(
        hba1c_valid_count=hba1c_count,
    ).annotate(
        hba1c_4plus=Case(
            When(hba1c_valid_count__gte=4, then=True),
            default=False,
            output_field=BooleanField(),
        ),
        psychological_assessment=Case(
            When(psych_exists, then=True),
            default=False,
            output_field=BooleanField(),
        ),
        smoking_status=Case(
            When(Q(is_gte_12yo=False), then=None),
            When(smoking_status_exists, then=True),
            default=False,
            output_field=BooleanField(),
        ),
        smoking_cessation_referral=Case(
            When(Q(is_gte_12yo=False), then=Value("under_12")),
            When(smoker_exists & smoking_referral_exists, then=Value("True")),
            When(smoker_exists, then=Value("False")),
            When(smoking_status_exists, then=Value("non_smoker_no_referral")),
            default=Value("False"),
            output_field=CharField(),
        ),
        additional_dietetic_appt_offered=Case(
            When(dietetic_offered_exists, then=True),
            default=False,
            output_field=BooleanField(),
        ),
        pts_attending_additional_dietetic_appt=Case(
            When(dietetic_attended_exists, then=True),
            default=False,
            output_field=BooleanField(),
        ),
        influenza_immunisation_recommended=Case(
            When(flu_exists, then=True),
            default=False,
            output_field=BooleanField(),
        ),
        sick_day_rules_advice=Case(
            When(sick_day_exists, then=True),
            default=False,
            output_field=BooleanField(),
        ),
    )


def annotate_care_at_diagnosis(qs, audit_period):
    audit_range = (audit_period.start_date, audit_period.end_date)

    carb_on_time = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            carbohydrate_counting_level_three_education_date__gte=F(
                "patient__diagnosis_date"
            )
            - Value(timedelta(days=7)),
            carbohydrate_counting_level_three_education_date__lte=F(
                "patient__diagnosis_date"
            )
            + Value(timedelta(days=14)),
        )
    )

    carb_missed = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            carbohydrate_counting_level_three_education_date__isnull=False,
        ).filter(
            Q(
                carbohydrate_counting_level_three_education_date__lt=F(
                    "patient__diagnosis_date"
                )
                - Value(timedelta(days=7))
            )
            | Q(
                carbohydrate_counting_level_three_education_date__gt=F(
                    "patient__diagnosis_date"
                )
                + Value(timedelta(days=14))
            )
        )
    )

    coeliac_on_time = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            coeliac_screen_date__gte=F("patient__diagnosis_date")
            - Value(timedelta(days=90)),
            coeliac_screen_date__lte=F("patient__diagnosis_date")
            + Value(timedelta(days=90)),
        )
    )

    coeliac_missed = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            coeliac_screen_date__isnull=False,
        ).filter(
            Q(
                coeliac_screen_date__lt=F("patient__diagnosis_date")
                - Value(timedelta(days=90))
            )
            | Q(
                coeliac_screen_date__gt=F("patient__diagnosis_date")
                + Value(timedelta(days=90))
            )
        )
    )

    thyroid_on_time = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            thyroid_function_date__gte=F("patient__diagnosis_date")
            - Value(timedelta(days=90)),
            thyroid_function_date__lte=F("patient__diagnosis_date")
            + Value(timedelta(days=90)),
        )
    )

    thyroid_missed = Exists(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            thyroid_function_date__isnull=False,
        ).filter(
            Q(
                thyroid_function_date__lt=F("patient__diagnosis_date")
                - Value(timedelta(days=90))
            )
            | Q(
                thyroid_function_date__gt=F("patient__diagnosis_date")
                + Value(timedelta(days=90))
            )
        )
    )

    return qs.filter(diagnosis_date__range=audit_range).annotate(
        carb_due_date=ExpressionWrapper(
            F("diagnosis_date") + Value(timedelta(days=14)),
            output_field=DateField(),
        ),
        coeliac_due_date=ExpressionWrapper(
            F("diagnosis_date") + Value(timedelta(days=90)),
            output_field=DateField(),
        ),
        thyroid_due_date=ExpressionWrapper(
            F("diagnosis_date") + Value(timedelta(days=90)),
            output_field=DateField(),
        ),
        carbohydrate_counting_education=Case(
            When(Q(dx_over_1y=False) & carb_on_time, then=True),
            When(Q(dx_over_1y=True), then=None),
            default=False,
            output_field=BooleanField(),
        ),
        carbohydrate_counting_missed=Case(
            When(Q(dx_over_1y=False) & carb_missed, then=True),
            default=False,
            output_field=BooleanField(),
        ),
        coeliac_disease_screening=Case(
            When(Q(dx_over_1y=False) & coeliac_on_time, then=True),
            When(Q(dx_over_1y=True), then=None),
            default=False,
            output_field=BooleanField(),
        ),
        coeliac_screen_missed=Case(
            When(Q(dx_over_1y=False) & coeliac_missed, then=True),
            default=False,
            output_field=BooleanField(),
        ),
        thyroid_disease_screening=Case(
            When(Q(dx_over_1y=False) & thyroid_on_time, then=True),
            When(Q(dx_over_1y=True), then=None),
            default=False,
            output_field=BooleanField(),
        ),
        thyroid_screen_missed=Case(
            When(Q(dx_over_1y=False) & thyroid_missed, then=True),
            default=False,
            output_field=BooleanField(),
        ),
    )


def annotate_admissions(qs, audit_period):
    audit_range = (audit_period.start_date, audit_period.end_date)
    admission_reason_values = [choice[0] for choice in HOSPITAL_ADMISSION_REASONS]

    admission_filter = Q(
        Q(visit__hospital_admission_date__range=audit_range)
        | Q(visit__hospital_discharge_date__range=audit_range)
    )
    admission_filter &= Q(visit__hospital_admission_reason__in=admission_reason_values)
    admission_filter &= Q(visit__visit_date__range=audit_range)
    admission_filter &= Q(
        visit__hospital_admission_date__gt=F("diagnosis_date")
        + Value(timedelta(days=90))
    )

    dka_filter = Q(
        Q(visit__hospital_admission_date__range=audit_range)
        | Q(visit__hospital_discharge_date__range=audit_range)
    )
    dka_filter &= Q(visit__hospital_admission_reason=HOSPITAL_ADMISSION_REASONS[1][0])
    dka_filter &= Q(visit__visit_date__range=audit_range)
    dka_filter &= Q(
        visit__hospital_admission_date__gt=F("diagnosis_date")
        + Value(timedelta(days=90))
    )

    return qs.annotate(
        number_of_admissions=Count("visit", filter=admission_filter, distinct=True),
        number_of_dka_admissions=Count("visit", filter=dka_filter, distinct=True),
    ).filter(Q(number_of_admissions__gt=0) | Q(number_of_dka_admissions__gt=0))


def annotate_treatment(qs, audit_period):
    audit_range = (audit_period.start_date, audit_period.end_date)
    dataset_year = audit_period.get_dataset_year()

    if dataset_year == 2026:
        # 2026 dataset: insulin_regimen (INSULIN_TREATMENT), cgm_use (YES_NO_UNKNOWN)
        # HCL is encoded as insulin_regimen == 5 (Hybrid closed loop)
        latest_insulin_regimen = Subquery(
            Visit.objects.filter(
                patient=OuterRef("pk"),
                visit_date__range=audit_range,
                insulin_regimen__isnull=False,
            )
            .order_by("-visit_date")
            .values("insulin_regimen")[:1]
        )

        latest_cgm_use = Subquery(
            Visit.objects.filter(
                patient=OuterRef("pk"),
                visit_date__range=audit_range,
                cgm_use__isnull=False,
            )
            .order_by("-visit_date")
            .values("cgm_use")[:1]
        )

        treatment_case = Case(
            *[
                When(latest_insulin_regimen=val, then=Value(label))
                for val, label in INSULIN_TREATMENT
            ],
            default=Value("No treatment regimen"),
            output_field=CharField(),
        )

        glucose_case = Case(
            *[
                When(latest_cgm_use=val, then=Value(label))
                for val, label in YES_NO_UNKNOWN
            ],
            default=Value("No glucose monitoring"),
            output_field=CharField(),
        )

        hcl_case = Case(
            When(latest_insulin_regimen=5, then=Value("Yes")),  # 5 = Hybrid closed loop
            default=Value("No"),
            output_field=CharField(),
        )

        return qs.annotate(
            latest_insulin_regimen=latest_insulin_regimen,
            latest_cgm_use=latest_cgm_use,
            treatment_regimen=treatment_case,
            glucose_monitoring=glucose_case,
            hcl=hcl_case,
        )

    else:
        # 2021 dataset: treatment (TREATMENT_TYPES), glucose_monitoring (GLUCOSE_MONITORING_TYPES)
        # HCL: closed_loop_system in [2, 3, 4]
        latest_visit = (
            Visit.objects.filter(
                patient=OuterRef("pk"),
                visit_date__range=audit_range,
            )
            .order_by("-visit_date")
            .values("visit_date")
        )

        latest_treatment = Subquery(
            Visit.objects.filter(
                patient=OuterRef("pk"),
                visit_date__range=audit_range,
                treatment__isnull=False,
            )
            .order_by("-visit_date")
            .values("treatment")[:1]
        )

        latest_glucose_monitoring = Subquery(
            Visit.objects.filter(
                patient=OuterRef("pk"),
                visit_date__range=audit_range,
                glucose_monitoring__isnull=False,
            )
            .order_by("-visit_date")
            .values("glucose_monitoring")[:1]
        )

        latest_closed_loop = Subquery(
            Visit.objects.filter(
                patient=OuterRef("pk"),
                visit_date__range=audit_range,
                closed_loop_system__isnull=False,
            )
            .order_by("-visit_date")
            .values("closed_loop_system")[:1]
        )

        treatment_case = Case(
            *[
                When(latest_treatment=val, then=Value(label))
                for val, label in TREATMENT_TYPES
            ],
            default=Value("No treatment regimen"),
            output_field=CharField(),
        )

        glucose_case = Case(
            *[
                When(latest_glucose_monitoring=val, then=Value(label))
                for val, label in GLUCOSE_MONITORING_TYPES
            ],
            default=Value("No glucose monitoring"),
            output_field=CharField(),
        )

        hcl_case = Case(
            When(latest_closed_loop__in=[2, 3, 4], then=Value("Yes")),
            default=Value("No"),
            output_field=CharField(),
        )

        return qs.annotate(
            latest_visit_date=Subquery(latest_visit[:1]),
            latest_treatment=latest_treatment,
            latest_glucose_monitoring=latest_glucose_monitoring,
            latest_closed_loop=latest_closed_loop,
            treatment_regimen=treatment_case,
            glucose_monitoring=glucose_case,
            hcl=hcl_case,
        )


def annotate_outcomes(qs, audit_period):
    audit_range = (audit_period.start_date, audit_period.end_date)
    dataset_year = audit_period.get_dataset_year()

    latest_hba1c_date = Subquery(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            visit_date__range=audit_range,
            hba1c__isnull=False,
        )
        .order_by("-visit_date")
        .values("visit_date")[:1]
    )

    previous_hba1c_date = Subquery(
        Visit.objects.filter(
            patient=OuterRef("pk"),
            visit_date__range=audit_range,
            hba1c__isnull=False,
        )
        .order_by("-visit_date")
        .values("visit_date")[1:2]
    )

    if dataset_year == 2026:
        # 2026: hba1c_format deprecated — values always stored as mmol/mol
        latest_hba1c_mmol_mol = Subquery(
            Visit.objects.filter(
                patient=OuterRef("pk"),
                visit_date__range=audit_range,
                hba1c__isnull=False,
            )
            .annotate(hba1c_mmol_mol=F("hba1c"))
            .order_by("-visit_date")
            .values("hba1c_mmol_mol")[:1]
        )

        previous_hba1c_mmol_mol = Subquery(
            Visit.objects.filter(
                patient=OuterRef("pk"),
                visit_date__range=audit_range,
                hba1c__isnull=False,
            )
            .annotate(hba1c_mmol_mol=F("hba1c"))
            .order_by("-visit_date")
            .values("hba1c_mmol_mol")[1:2]
        )
    else:
        latest_hba1c_mmol_mol = Subquery(
            Visit.objects.filter(
                patient=OuterRef("pk"),
                visit_date__range=audit_range,
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
                        then=(F("hba1c") - Round(Decimal("2.152"))) / Decimal("0.09148"),
                    ),
                    default=None,
                    output_field=DecimalField(max_digits=5, decimal_places=2),
                )
            )
            .order_by("-visit_date")
            .values("hba1c_mmol_mol")[:1]
        )

        previous_hba1c_mmol_mol = Subquery(
            Visit.objects.filter(
                patient=OuterRef("pk"),
                visit_date__range=audit_range,
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
                        then=(F("hba1c") - Round(Decimal("2.152"))) / Decimal("0.09148"),
                    ),
                    default=None,
                    output_field=DecimalField(max_digits=5, decimal_places=2),
                )
            )
            .order_by("-visit_date")
            .values("hba1c_mmol_mol")[1:2]
        )

    return qs.annotate(
        latest_hba1c_date=latest_hba1c_date,
        previous_to_latest_hba1c_date=previous_hba1c_date,
        days_delta_between_latest_and_previous_hba1c=Case(
            When(
                Q(latest_hba1c_date__isnull=False)
                & Q(previous_to_latest_hba1c_date__isnull=False),
                then=Func(
                    ExpressionWrapper(
                        F("latest_hba1c_date") - F("previous_to_latest_hba1c_date"),
                        output_field=DurationField(),
                    ),
                    function="EXTRACT",
                    template="EXTRACT(DAY FROM %(expressions)s)",
                    output_field=IntegerField(),
                ),
            ),
            default=None,
            output_field=IntegerField(),
        ),
        latest_hba1c_mmol_mol=latest_hba1c_mmol_mol,
        previous_to_latest_hba1c_mmol_mol=previous_hba1c_mmol_mol,
        latest_hba1c_pct=Case(
            When(
                Q(latest_hba1c_mmol_mol__isnull=False) & Q(latest_hba1c_mmol_mol__gt=0),
                then=(Decimal("0.09148") * F("latest_hba1c_mmol_mol"))
                + Decimal("2.152"),
            ),
            default=None,
            output_field=DecimalField(max_digits=4, decimal_places=1),
        ),
        previous_to_latest_hba1c_pct=Case(
            When(
                Q(previous_to_latest_hba1c_mmol_mol__isnull=False)
                & Q(previous_to_latest_hba1c_mmol_mol__gt=0),
                then=(Decimal("0.09148") * F("previous_to_latest_hba1c_mmol_mol"))
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


def calculate_hba1c_values(qs, audit_period):
    audit_range = (audit_period.start_date, audit_period.end_date)
    patient_ids = set(qs.values_list("pk", flat=True))

    valid_visits = (
        Visit.objects.filter(
            patient__pk__in=patient_ids,
            visit_date__range=audit_range,
            hba1c_date__gt=F("patient__diagnosis_date") + timedelta(days=90),
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
                    then=(F("hba1c") - Round(Decimal("2.152"))) / Decimal("0.09148"),
                ),
                default=None,
                output_field=DecimalField(max_digits=5, decimal_places=2),
            )
        )
        .values("hba1c_mmol_mol", "patient__pk")
        .filter(hba1c_mmol_mol__isnull=False)
    )

    values_by_patient = defaultdict(list)
    for visit in valid_visits:
        values_by_patient[visit["patient__pk"]].append(visit["hba1c_mmol_mol"])

    for patient in qs:
        hba1c_values = values_by_patient.get(patient["pk"], [])
        if hba1c_values:
            mean_val = sum(hba1c_values) / len(hba1c_values)
            sorted_vals = sorted(hba1c_values)
            mid = len(sorted_vals) // 2
            if len(sorted_vals) % 2 == 0:
                median_val = (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
            else:
                median_val = sorted_vals[mid]

            patient["kpi_44_mean_hba1c"] = round(mean_val)
            patient["kpi_45_median_hba1c"] = round(median_val)
            patient["mean_hba1c_pct"] = round(
                (
                    (Decimal("0.09148") * mean_val) + Decimal("2.152")
                    if mean_val > 0
                    else None
                ),
                1,
            )
            patient["median_hba1c_pct"] = round(
                (
                    (Decimal("0.09148") * median_val) + Decimal("2.152")
                    if median_val > 0
                    else None
                ),
                1,
            )
        else:
            patient["kpi_44_mean_hba1c"] = None
            patient["kpi_45_median_hba1c"] = None
            patient["mean_hba1c_pct"] = None
            patient["median_hba1c_pct"] = None

    return qs
