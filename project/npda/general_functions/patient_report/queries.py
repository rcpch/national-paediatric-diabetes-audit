from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
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
from project.constants.hospital_admission_reasons import (
    HOSPITAL_ADMISSION_REASONS_2021,
    HOSPITAL_ADMISSION_REASONS_2026,
)
from project.constants.leave_pdu_reasons import LEAVE_PDU_REASONS
from project.constants.yes_no_unknown import YES_NO_UNKNOWN
from project.npda.general_functions.audit_period import get_quarters_for_audit_period
from project.npda.general_functions.quarter_for_date import retrieve_quarter_for_date
from project.npda.models import PaediatricDiabetesUnit, Patient, Transfer, Visit
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
            When(thyroid_exists, then=True),
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
                Q(is_gte_12yo=True) & retinal_exists,
                then=Value("complete"),
            ),
            When(Q(is_gte_12yo=False), then=Value("not_required")),
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
                smoking_vaping_status__in=[
                    2,
                    4,
                ],  # current smoker (with or without vaping)
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
            When(carb_on_time, then=True),
            default=False,
            output_field=BooleanField(),
        ),
        carbohydrate_counting_missed=Case(
            When(carb_missed, then=True),
            default=False,
            output_field=BooleanField(),
        ),
        coeliac_disease_screening=Case(
            When(coeliac_on_time, then=True),
            default=False,
            output_field=BooleanField(),
        ),
        coeliac_screen_missed=Case(
            When(coeliac_missed, then=True),
            default=False,
            output_field=BooleanField(),
        ),
        thyroid_disease_screening=Case(
            When(thyroid_on_time, then=True),
            default=False,
            output_field=BooleanField(),
        ),
        thyroid_screen_missed=Case(
            When(thyroid_missed, then=True),
            default=False,
            output_field=BooleanField(),
        ),
    )


def annotate_admissions(qs, audit_period):
    audit_range = (audit_period.start_date, audit_period.end_date)
    admission_reason_values = (
        [choice[0] for choice in HOSPITAL_ADMISSION_REASONS_2021]
        if audit_period.get_dataset_year() < 2026
        else [choice[0] for choice in HOSPITAL_ADMISSION_REASONS_2026]
    )  # Exclude 'Not admitted' reason for 2026 onwards

    admission_filter = Q(
        Q(visit__hospital_admission_date__range=audit_range)
        | Q(visit__hospital_discharge_date__range=audit_range)
    )
    if audit_period.get_dataset_year() < 2026:
        admission_filter &= Q(
            visit__hospital_admission_reason__in=admission_reason_values
        )
    elif audit_period.get_dataset_year() >= 2026:
        admission_filter &= Q(
            visit__hospital_admission_reason_2026__in=admission_reason_values
        )
    admission_filter &= Q(visit__visit_date__range=audit_range)
    admission_filter &= Q(
        visit__hospital_admission_date__gt=F("diagnosis_date")
        + Value(timedelta(days=90))
    )

    dka_filter = Q(
        Q(visit__hospital_admission_date__range=audit_range)
        | Q(visit__hospital_discharge_date__range=audit_range)
    )
    if audit_period.get_dataset_year() < 2026:
        dka_filter &= Q(
            visit__hospital_admission_reason=HOSPITAL_ADMISSION_REASONS_2021[1][
                0
            ]  # DKA
        )
    elif audit_period.get_dataset_year() >= 2026:
        dka_filter &= Q(
            visit__hospital_admission_reason_2026=HOSPITAL_ADMISSION_REASONS_2026[0][
                0
            ]  # DKA
        )
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

        # Anchored to the same visit as the latest treatment so that closed_loop_system
        # reflects the patient's current regimen, not a historical visit.
        latest_closed_loop = Subquery(
            Visit.objects.filter(
                patient=OuterRef("pk"),
                visit_date__range=audit_range,
                treatment__isnull=False,
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

        # HCL requires both a pump treatment AND a closed loop system on that same visit.
        hcl_case = Case(
            When(
                Q(latest_treatment__in=[3, 6]) & Q(latest_closed_loop__in=[2, 3, 4]),
                then=Value("Yes"),
            ),
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
                        then=(F("hba1c") - Round(Decimal("2.152")))
                        / Decimal("0.09148"),
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
                        then=(F("hba1c") - Round(Decimal("2.152")))
                        / Decimal("0.09148"),
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


# ---------------------------------------------------------------------------
# Dashboard aggregate query functions (replace CalculateKPIS in dashboard views)
# ---------------------------------------------------------------------------


def count_eligible_patients(pdu, audit_period) -> int:
    """Count of all patients eligible for the dashboard summary (equivalent to KPI 1).

    Includes all diabetes types. A patient is eligible if they:
    - Are in the active submission for this PDU and audit period
    - Have at least one visit within the audit period
    - Were under 25 at the start of the audit period
    """
    audit_range = (audit_period.start_date, audit_period.end_date)
    return (
        Patient.objects.filter(
            submissions__submission_active=True,
            submissions__audit_period=audit_period,
            submissions__paediatric_diabetes_unit=pdu,
            visit__visit_date__range=audit_range,
            date_of_birth__gt=audit_period.start_date - relativedelta(years=25),
        )
        .distinct()
        .count()
    )


def count_new_diagnoses_by_quarter(pdu, audit_period) -> dict:
    """New diagnoses split by quarter, equivalent to
    CalculateKPIS.calculate_kpi_2_total_new_diagnoses_stratified_by_quarter().

    Returns a dict keyed by quarter number (1–4 for a complete year, 1–N for
    an active period where N is the current quarter):

        {q: {"total_passed": int, "total_eligible": int, "pct": float}}

    total_eligible = total new diagnoses in the whole audit period.
    total_passed   = new diagnoses whose diagnosis_date falls within that quarter.
    Quarters beyond the current one are omitted for active audit periods.
    """
    audit_range = (audit_period.start_date, audit_period.end_date)
    today = date.today()

    eligible_qs = Patient.objects.filter(
        submissions__submission_active=True,
        submissions__audit_period=audit_period,
        submissions__paediatric_diabetes_unit=pdu,
        visit__visit_date__range=audit_range,
        date_of_birth__gt=audit_period.start_date - relativedelta(years=25),
    ).distinct()

    new_diagnoses_qs = eligible_qs.filter(diagnosis_date__range=audit_range)
    total_eligible = new_diagnoses_qs.count()

    quarter_end_dates = [
        q[1]
        for q in get_quarters_for_audit_period(
            audit_period.start_date, audit_period.end_date
        )
    ]

    # For a past period use the final quarter; for an active period use today.
    if today > audit_period.end_date:
        current_quarter = retrieve_quarter_for_date(audit_period.end_date)
    else:
        current_quarter = retrieve_quarter_for_date(today)
    quarter_end_dates = quarter_end_dates[:current_quarter]

    result = {}
    for q, q_end_date in enumerate(quarter_end_dates, start=1):
        q_start = q_end_date - relativedelta(months=3)
        total_passed = new_diagnoses_qs.filter(
            diagnosis_date__range=(q_start, q_end_date)
        ).count()
        result[q] = {
            "total_passed": total_passed,
            "total_eligible": total_eligible,
            "pct": round(
                (total_passed / total_eligible * 100) if total_eligible else 0,
                1,
            ),
        }

    return result


def count_hcl_use(pdu, audit_period) -> tuple[int, int]:
    """Returns (passed, eligible) for hybrid closed-loop use among T1DM patients.

    eligible = all T1DM patients in the submission.
    passed   = those whose most recent treatment entry indicates HCL:
        2021: closed_loop_system in [2, 3, 4]
        2026: insulin_regimen = 5
    """
    qs = build_base_queryset(pdu, audit_period, type1_only=True)
    qs = annotate_treatment(qs, audit_period)
    eligible = qs.count()
    passed = qs.filter(hcl="Yes").count()
    return passed, eligible


def count_pump_use(pdu, audit_period) -> tuple[int, int]:
    """Returns (passed, eligible) for insulin pump use among T1DM patients.

    eligible = all T1DM patients in the submission.
    passed   = those whose most recent treatment entry is a pump:
        2021: latest treatment in [3 (pump), 6 (pump + other)]
        2026: latest insulin_regimen in [4 (standalone pump), 5 (HCL, which uses pump)]
    """
    qs = build_base_queryset(pdu, audit_period, type1_only=True)
    qs = annotate_treatment(qs, audit_period)
    eligible = qs.count()
    if audit_period.get_dataset_year() == 2026:
        passed = qs.filter(latest_insulin_regimen__in=[4, 5]).count()
    else:
        passed = qs.filter(latest_treatment__in=[3, 6]).count()
    return passed, eligible


def count_cgm_use(pdu, audit_period) -> tuple[int, int]:
    """Returns (passed, eligible) for CGM use among T1DM patients.

    eligible = all T1DM patients in the submission.
    passed   = those on CGM at most recent entry:
        2021: glucose_monitoring = 4 (real-time CGM with alarms)
        2026: cgm_use = 1 (Yes)
    """
    qs = build_base_queryset(pdu, audit_period, type1_only=True)
    qs = annotate_treatment(qs, audit_period)
    eligible = qs.count()
    if audit_period.get_dataset_year() == 2026:
        passed = qs.filter(latest_cgm_use=1).count()
    else:
        passed = qs.filter(latest_glucose_monitoring=4).count()
    return passed, eligible


def count_admissions(pdu, audit_period) -> int:
    """Count of patients with at least one valid hospital admission in the audit period.

    Mirrors CalculateKPIS.calculate_kpi_46_number_of_admissions(). All diabetes types.
    A valid admission has a recognised admission reason AND either admission or
    discharge date within the audit period.
    """
    audit_range = (audit_period.start_date, audit_period.end_date)
    if audit_period.get_dataset_year() < 2026:
        valid_reasons = [choice[0] for choice in HOSPITAL_ADMISSION_REASONS_2021]
        visit_filter = Q(visit__hospital_admission_reason__in=valid_reasons)
    else:
        valid_reasons = [choice[0] for choice in HOSPITAL_ADMISSION_REASONS_2026]
        visit_filter = Q(visit__hospital_admission_reason_2026__in=valid_reasons)
    return (
        Patient.objects.filter(
            submissions__submission_active=True,
            submissions__audit_period=audit_period,
            submissions__paediatric_diabetes_unit=pdu,
            visit__visit_date__range=audit_range,
            date_of_birth__gt=audit_period.start_date - relativedelta(years=25),
        )
        .filter(visit_filter)
        .filter(
            Q(visit__hospital_admission_date__range=audit_range)
            | Q(visit__hospital_discharge_date__range=audit_range)
        )
        .distinct()
        .count()
    )


def count_admissions_by_quarter(pdu, audit_period) -> dict:
    """Hospital admissions split by quarter.

    Mirrors calculate_kpi_46_number_of_admissions_stratified_by_quarter().
    Returns {q: {total_passed, total_eligible, pct}}.
    total_eligible is the count of all KPI-1-eligible patients (denominator).
    """
    audit_range = (audit_period.start_date, audit_period.end_date)
    today = date.today()
    reasons = (
        HOSPITAL_ADMISSION_REASONS_2021
        if audit_period.get_dataset_year() < 2026
        else HOSPITAL_ADMISSION_REASONS_2026
    )
    valid_reasons = [choice[0] for choice in reasons]

    base_qs = Patient.objects.filter(
        submissions__submission_active=True,
        submissions__audit_period=audit_period,
        submissions__paediatric_diabetes_unit=pdu,
        visit__visit_date__range=audit_range,
        date_of_birth__gt=audit_period.start_date - relativedelta(years=25),
    ).distinct()
    total_eligible = base_qs.count()

    # Patients with at least one valid admission within the audit period
    if audit_period.get_dataset_year() < 2026:
        # 2021: filter by valid reasons here since the reason field is mandatory
        base_qs = base_qs.filter(visit__hospital_admission_reason__in=valid_reasons)
    else:
        base_qs = base_qs.filter(
            visit__hospital_admission_reason_2026__in=valid_reasons
        )
    admitted_qs = base_qs.filter(
        Q(visit__hospital_admission_date__range=audit_range)
        | Q(visit__hospital_discharge_date__range=audit_range)
    ).distinct()

    quarter_end_dates = [
        q[1]
        for q in get_quarters_for_audit_period(
            audit_period.start_date, audit_period.end_date
        )
    ]
    if today > audit_period.end_date:
        current_quarter = retrieve_quarter_for_date(audit_period.end_date)
    else:
        current_quarter = retrieve_quarter_for_date(today)
    quarter_end_dates = quarter_end_dates[:current_quarter]

    result = {}
    for q, q_end_date in enumerate(quarter_end_dates, start=1):
        q_start = q_end_date - relativedelta(months=3)
        total_passed = admitted_qs.filter(
            visit__hospital_admission_date__range=(q_start, q_end_date)
        ).count()
        result[q] = {
            "total_passed": total_passed,
            "total_eligible": total_eligible,
            "pct": round(
                (total_passed / total_eligible * 100) if total_eligible else 0,
                1,
            ),
        }

    return result


def count_service_transitions_by_quarter(pdu, audit_period) -> dict:
    """Transitions to adult care split by quarter.

    Mirrors calculate_total_service_transitions_to_adults_stratified_by_quarter().
    Returns {q: {total_passed, total_eligible, pct}}.
    """
    audit_range = (audit_period.start_date, audit_period.end_date)
    today = date.today()

    base_qs = Patient.objects.filter(
        submissions__submission_active=True,
        submissions__audit_period=audit_period,
        submissions__paediatric_diabetes_unit=pdu,
        visit__visit_date__range=audit_range,
        date_of_birth__gt=audit_period.start_date - relativedelta(years=25),
    ).distinct()

    transitioned_qs = base_qs.filter(
        paediatric_diabetes_units__date_leaving_service__range=audit_range,
        paediatric_diabetes_units__reason_leaving_service=LEAVE_PDU_REASONS[0][0],
    ).distinct()
    total_eligible = transitioned_qs.count()

    quarter_end_dates = [
        q[1]
        for q in get_quarters_for_audit_period(
            audit_period.start_date, audit_period.end_date
        )
    ]
    if today > audit_period.end_date:
        current_quarter = retrieve_quarter_for_date(audit_period.end_date)
    else:
        current_quarter = retrieve_quarter_for_date(today)
    quarter_end_dates = quarter_end_dates[:current_quarter]

    result = {}
    for q, q_end_date in enumerate(quarter_end_dates, start=1):
        q_start = q_end_date - relativedelta(months=3)
        total_passed = transitioned_qs.filter(
            paediatric_diabetes_units__date_leaving_service__range=(q_start, q_end_date)
        ).count()
        result[q] = {
            "total_passed": total_passed,
            "total_eligible": total_eligible,
            "pct": round(
                (total_passed / total_eligible * 100) if total_eligible else 0,
                1,
            ),
        }

    return result


def hba1c_stats_by_diabetes_type(pdu, audit_period) -> dict:
    """Mean and median HbA1c stratified by diabetes type for the dashboard.

    Mirrors CalculateKPIS.calculate_kpi_hba1c_vals_stratified_by_diabetes_type().

    Returns:
        {
            "all":   {"mean_mmol_mol": int|None, "median_mmol_mol": int|None,
                      "mean_percent": float|None, "median_percent": float|None},
            "t1dm":  {...},
            "t2dm":  {...},
            "other": {...},
        }

    2021 dataset: normalises via hba1c_format (mmol/mol vs %).
    2026 dataset: hba1c_format is absent; values are already in mmol/mol
                  (format is inferred from magnitude, but we treat them as
                  mmol/mol directly since the CSV pipeline stores them that way).
    """
    audit_range = (audit_period.start_date, audit_period.end_date)

    base_qs = Patient.objects.filter(
        submissions__submission_active=True,
        submissions__audit_period=audit_period,
        submissions__paediatric_diabetes_unit=pdu,
        visit__visit_date__range=audit_range,
        date_of_birth__gt=audit_period.start_date - relativedelta(years=25),
    ).distinct()

    t1dm_qs = base_qs.filter(diabetes_type=DIABETES_TYPES[0][0])
    t2dm_qs = base_qs.filter(diabetes_type=DIABETES_TYPES[1][0])
    other_qs = base_qs.exclude(
        diabetes_type__in=[DIABETES_TYPES[0][0], DIABETES_TYPES[1][0]]
    )

    result = {}
    for key, qs in (
        ("all", base_qs),
        ("t1dm", t1dm_qs),
        ("t2dm", t2dm_qs),
        ("other", other_qs),
    ):
        patient_ids = list(qs.values_list("pk", flat=True))

        # Normalise % → mmol/mol
        valid_visits = (
            Visit.objects.filter(
                patient__pk__in=patient_ids,
                visit_date__range=audit_range,
                hba1c__isnull=False,
                hba1c_date__gt=F("patient__diagnosis_date") + timedelta(days=90),
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
        hba1c_key = "hba1c_mmol_mol"

        values_by_patient = defaultdict(list)
        for visit in valid_visits:
            values_by_patient[visit["patient__pk"]].append(visit[hba1c_key])

        all_values = [v for vals in values_by_patient.values() for v in vals]

        if all_values:
            mean_mmol = float(sum(all_values) / len(all_values))
            sorted_vals = sorted(float(v) for v in all_values)
            mid = len(sorted_vals) // 2
            median_mmol = (
                (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
                if len(sorted_vals) % 2 == 0
                else sorted_vals[mid]
            )
            result[key] = {
                "mean_mmol_mol": round(mean_mmol),
                "median_mmol_mol": round(median_mmol),
                "mean_percent": round((0.09148 * mean_mmol) + 2.152, 1),
                "median_percent": round((0.09148 * median_mmol) + 2.152, 1),
            }
        else:
            result[key] = {
                "mean_mmol_mol": None,
                "median_mmol_mol": None,
                "mean_percent": None,
                "median_percent": None,
            }

    return result


def dashboard_health_check_totals(pdu, audit_period) -> dict:
    """Aggregate health-check pass/eligible counts for the measurements card.

    Replaces the ~20-query patient_health_check_totals() in patient_measurements.py
    with a single annotated aggregation.

    Returns the same dict shape:
        total_passed_bmi, total_eligible_bmi,
        total_passed_thyroid_screen, total_eligible_thyroid_screen,
        total_passed_blood_pressure, total_eligible_blood_pressure,
        total_passed_urinary_albumin, total_eligible_urinary_albumin,
        total_passed_foot_exam, total_eligible_foot_exam,
        total_passed_four_hba1cs, total_eligible_four_hba1cs,
        total_passed_all_care_processes, total_eligible_all_care_processes
    """
    audit_range = (audit_period.start_date, audit_period.end_date)
    qs = build_base_queryset(pdu, audit_period, type1_only=True)
    qs = annotate_health_checks(qs, audit_period)

    # Annotate per-patient HbA1c count within the audit period (for 4+ HbA1c tile)
    qs = qs.annotate(
        hba1c_count=Count(
            "visit",
            filter=Q(
                visit__hba1c__isnull=False,
                visit__hba1c_date__range=audit_range,
            ),
            distinct=True,
        )
    )

    # Aggregate all counts in a single query
    agg = qs.aggregate(
        # BMI — all complete-year T1DM patients
        total_passed_bmi=Count(
            "pk",
            filter=Q(passed_bmi=True, is_complete_year_of_care=True),
        ),
        total_eligible_bmi=Count(
            "pk",
            filter=Q(is_complete_year_of_care=True),
        ),
        # Thyroid — all complete-year T1DM patients
        total_passed_thyroid_screen=Count(
            "pk",
            filter=Q(passed_thyroid_screen=True, is_complete_year_of_care=True),
        ),
        total_eligible_thyroid_screen=Count(
            "pk",
            filter=Q(is_complete_year_of_care=True),
        ),
        # Blood pressure — complete-year AND aged 12+ at audit start
        total_passed_blood_pressure=Count(
            "pk",
            filter=Q(
                passed_blood_pressure=True,
                is_complete_year_of_care=True,
                is_gte_12yo=True,
            ),
        ),
        total_eligible_blood_pressure=Count(
            "pk",
            filter=Q(is_complete_year_of_care=True, is_gte_12yo=True),
        ),
        # Urinary albumin — same gate as BP
        total_passed_urinary_albumin=Count(
            "pk",
            filter=Q(
                passed_urinary_albumin=True,
                is_complete_year_of_care=True,
                is_gte_12yo=True,
            ),
        ),
        total_eligible_urinary_albumin=Count(
            "pk",
            filter=Q(is_complete_year_of_care=True, is_gte_12yo=True),
        ),
        # Foot exam — same gate as BP
        total_passed_foot_exam=Count(
            "pk",
            filter=Q(
                passed_foot_exam=True, is_complete_year_of_care=True, is_gte_12yo=True
            ),
        ),
        total_eligible_foot_exam=Count(
            "pk",
            filter=Q(is_complete_year_of_care=True, is_gte_12yo=True),
        ),
        # 4+ HbA1c measurements — all complete-year T1DM patients
        total_passed_four_hba1cs=Count(
            "pk",
            filter=Q(hba1c_count__gte=4, is_complete_year_of_care=True),
        ),
        total_eligible_four_hba1cs=Count(
            "pk",
            filter=Q(is_complete_year_of_care=True),
        ),
        # All applicable care processes complete:
        #   ≥12yo: all 6 (HbA1c, BMI, thyroid, BP, urinary albumin, foot exam)
        #   <12yo: all 3 (HbA1c, BMI, thyroid)
        total_passed_all_care_processes=Count(
            "pk",
            filter=Q(is_complete_year_of_care=True)
            & (Q(is_gte_12yo=True, num_passed=6) | Q(is_gte_12yo=False, num_passed=3)),
        ),
        total_eligible_all_care_processes=Count(
            "pk",
            filter=Q(is_complete_year_of_care=True),
        ),
    )
    return agg


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
            patient["mean_hba1c_pct"] = (
                round((Decimal("0.09148") * mean_val) + Decimal("2.152"), 1)
                if mean_val > 0
                else None
            )
            patient["median_hba1c_pct"] = (
                round((Decimal("0.09148") * median_val) + Decimal("2.152"), 1)
                if median_val > 0
                else None
            )
        else:
            patient["kpi_44_mean_hba1c"] = None
            patient["kpi_45_median_hba1c"] = None
            patient["mean_hba1c_pct"] = None
            patient["median_hba1c_pct"] = None

    return qs


def all_pdus_t1dm_bubble_map_data(audit_period) -> list[dict]:
    """Bubble map data for the national submissions overview (audit team only).

    Returns one entry per PDU that has an active submission with T1DM patients and
    a geocoordinate on record.  Each entry is a plain dict ready to be passed
    directly to the map library's ``setLeadCentres()`` call:

        {
            "lat": float,
            "lon": float,
            "label": str,            # lead_organisation_name or pz_code
            "pz_code": str,
            "patient_count": int,    # eligible T1DM patients in the audit period
            "median_hba1c": int | None,  # median HbA1c in mmol/mol
        }

    Uses the same eligibility filters as ``count_eligible_patients()`` and the
    same HbA1c normalisation logic as ``hba1c_stats_by_diabetes_type()``.
    Runs in ~4 DB round-trips regardless of the number of PDUs.
    """
    audit_range = (audit_period.start_date, audit_period.end_date)
    dataset_year = audit_period.get_dataset_year()

    # All active PDUs with a submission in this period and a geocoordinate
    pdus = {
        pdu.pz_code: pdu
        for pdu in PaediatricDiabetesUnit.objects.filter(
            active=True,
            pdu_submissions__submission_active=True,
            pdu_submissions__audit_period=audit_period,
            lead_organisation_geocoordinates__isnull=False,
        ).distinct()
    }
    if not pdus:
        return []

    # Eligible T1DM patients annotated with their PDU pz_code.
    # distinct() on (pk, pz_code) gives one row per patient per PDU.
    t1dm_rows = (
        Patient.objects.filter(
            submissions__submission_active=True,
            submissions__audit_period=audit_period,
            submissions__paediatric_diabetes_unit__pz_code__in=pdus.keys(),
            diabetes_type=DIABETES_TYPES[0][0],
            visit__visit_date__range=audit_range,
            date_of_birth__gt=audit_period.start_date - relativedelta(years=25),
        )
        .distinct()
        .values("pk", "submissions__paediatric_diabetes_unit__pz_code")
    )

    # Build patient→PDU map and per-PDU patient counts in one pass
    patient_pdu_map: dict[int, str] = {}
    patient_counts: dict[str, int] = defaultdict(int)
    for row in t1dm_rows:
        pk = row["pk"]
        pz = row["submissions__paediatric_diabetes_unit__pz_code"]
        if pk not in patient_pdu_map:
            patient_pdu_map[pk] = pz
            patient_counts[pz] += 1

    if not patient_pdu_map:
        return []

    # Fetch HbA1c values for all T1DM patients in one query
    if dataset_year == 2026:
        hba1c_rows = Visit.objects.filter(
            patient__pk__in=patient_pdu_map.keys(),
            visit_date__range=audit_range,
            hba1c__isnull=False,
            hba1c_date__gt=F("patient__diagnosis_date") + timedelta(days=90),
        ).values("patient__pk", "hba1c")
        hba1c_key = "hba1c"
    else:
        hba1c_rows = (
            Visit.objects.filter(
                patient__pk__in=patient_pdu_map.keys(),
                visit_date__range=audit_range,
                hba1c__isnull=False,
                hba1c_date__gt=F("patient__diagnosis_date") + timedelta(days=90),
            )
            .annotate(
                hba1c_mmol_mol=Case(
                    When(Q(hba1c_format=HBA1C_FORMATS[0][0]), then=F("hba1c")),
                    When(
                        Q(hba1c_format=HBA1C_FORMATS[1][0]),
                        then=(F("hba1c") - Round(Decimal("2.152")))
                        / Decimal("0.09148"),
                    ),
                    default=None,
                    output_field=DecimalField(max_digits=5, decimal_places=2),
                )
            )
            .filter(hba1c_mmol_mol__isnull=False)
            .values("patient__pk", "hba1c_mmol_mol")
        )
        hba1c_key = "hba1c_mmol_mol"

    # Group HbA1c values by PDU
    hba1c_by_pdu: dict[str, list] = defaultdict(list)
    for row in hba1c_rows:
        pz = patient_pdu_map.get(row["patient__pk"])
        if pz:
            hba1c_by_pdu[pz].append(row[hba1c_key])

    result = []
    for pz_code, pdu in pdus.items():
        count = patient_counts.get(pz_code, 0)
        if count == 0:
            continue

        hba1c_vals = hba1c_by_pdu.get(pz_code, [])
        if hba1c_vals:
            sorted_vals = sorted(float(v) for v in hba1c_vals)
            mid = len(sorted_vals) // 2
            median_hba1c = (
                (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
                if len(sorted_vals) % 2 == 0
                else sorted_vals[mid]
            )
            median_hba1c = round(median_hba1c)
        else:
            median_hba1c = None

        coords = pdu.lead_organisation_geocoordinates
        result.append(
            {
                "lat": coords.y,
                "lon": coords.x,
                "label": pdu.lead_organisation_name or pdu.pz_code,
                "pz_code": pz_code,
                "patient_count": count,
                "median_hba1c": median_hba1c,
            }
        )

    return result


def all_pdus_care_processes_map_data(audit_period) -> list[dict]:
    """% complete care processes per PDU for the national bubble map (T1DM only).

    Each entry:
        {
            "lat": float, "lon": float, "label": str, "pz_code": str,
            "eligible_count": int,   # T1DM patients with complete year of care
            "pct_complete": int,     # % who passed all required care processes (0-100)
        }

    Uses the same eligibility and care-process definitions as
    ``dashboard_health_check_totals`` (HbA1c, BMI, thyroid for all;
    + BP, albumin, foot exam for patients aged ≥12).
    """
    audit_range = (audit_period.start_date, audit_period.end_date)

    pdus = {
        pdu.pz_code: pdu
        for pdu in PaediatricDiabetesUnit.objects.filter(
            active=True,
            pdu_submissions__submission_active=True,
            pdu_submissions__audit_period=audit_period,
            lead_organisation_geocoordinates__isnull=False,
        ).distinct()
    }
    if not pdus:
        return []

    # Build patient → PDU mapping for T1DM patients with visits in this period
    t1dm_rows = (
        Patient.objects.filter(
            submissions__submission_active=True,
            submissions__audit_period=audit_period,
            submissions__paediatric_diabetes_unit__pz_code__in=pdus.keys(),
            diabetes_type=DIABETES_TYPES[0][0],
            visit__visit_date__range=audit_range,
            date_of_birth__gt=audit_period.start_date - relativedelta(years=25),
        )
        .distinct()
        .values("pk", "submissions__paediatric_diabetes_unit__pz_code")
    )
    patient_pdu_map: dict[int, str] = {}
    for row in t1dm_rows:
        pk = row["pk"]
        if pk not in patient_pdu_map:
            patient_pdu_map[pk] = row["submissions__paediatric_diabetes_unit__pz_code"]

    if not patient_pdu_map:
        return []

    # Annotate each patient with care-process pass/fail
    care_qs = (
        Patient.objects.filter(pk__in=patient_pdu_map.keys())
        .annotate(
            is_gte_12yo=Q(
                date_of_birth__lte=audit_period.start_date - relativedelta(years=12)
            ),
            is_incomplete_year_of_care=Case(
                When(Q(diagnosis_date__range=audit_range), then=True),
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
    care_qs = annotate_health_checks(care_qs, audit_period)

    eligible: dict[str, int] = defaultdict(int)
    passed_all: dict[str, int] = defaultdict(int)
    for row in care_qs.values(
        "pk", "is_complete_year_of_care", "is_gte_12yo", "num_passed"
    ):
        pz = patient_pdu_map.get(row["pk"])
        if pz is None or not row["is_complete_year_of_care"]:
            continue
        eligible[pz] += 1
        threshold = 6 if row["is_gte_12yo"] else 3
        if row["num_passed"] == threshold:
            passed_all[pz] += 1

    result = []
    for pz_code, pdu in pdus.items():
        eligible_count = eligible.get(pz_code, 0)
        if eligible_count == 0:
            continue
        passed_count = passed_all.get(pz_code, 0)
        coords = pdu.lead_organisation_geocoordinates
        result.append(
            {
                "lat": coords.y,
                "lon": coords.x,
                "label": pdu.lead_organisation_name or pdu.pz_code,
                "pz_code": pz_code,
                "eligible_count": eligible_count,
                "pct_complete": round(passed_count / eligible_count * 100),
            }
        )

    return result


def all_pdus_diabetes_type_map_data(audit_period) -> list[dict]:
    """Diabetes type breakdown per PDU for the national bubble map.

    Each entry:
        {
            "lat": float, "lon": float, "label": str, "pz_code": str,
            "total_patients": int,    # all eligible patients (all types)
            "dominant_type": str,     # 'type1' | 'type2' | 'other'
            "pct_type1": int,         # percentage type 1 (0-100)
            "pct_type2": int,         # percentage type 2 (0-100)
            "pct_other": int,         # percentage other (0-100)
        }

    Suitable for ``colorMode: 'categorical'`` in setLeadCentres().
    """
    audit_range = (audit_period.start_date, audit_period.end_date)

    pdus = {
        pdu.pz_code: pdu
        for pdu in PaediatricDiabetesUnit.objects.filter(
            active=True,
            pdu_submissions__submission_active=True,
            pdu_submissions__audit_period=audit_period,
            lead_organisation_geocoordinates__isnull=False,
        ).distinct()
    }
    if not pdus:
        return []

    rows = (
        Patient.objects.filter(
            submissions__submission_active=True,
            submissions__audit_period=audit_period,
            submissions__paediatric_diabetes_unit__pz_code__in=pdus.keys(),
            visit__visit_date__range=audit_range,
            date_of_birth__gt=audit_period.start_date - relativedelta(years=25),
        )
        .distinct()
        .values("pk", "diabetes_type", "submissions__paediatric_diabetes_unit__pz_code")
    )

    type_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    seen: set[int] = set()
    for row in rows:
        pk = row["pk"]
        if pk in seen:
            continue
        seen.add(pk)
        pz = row["submissions__paediatric_diabetes_unit__pz_code"]
        dtype = row["diabetes_type"]
        if dtype == DIABETES_TYPES[0][0]:
            cat = "type1"
        elif dtype == DIABETES_TYPES[1][0]:
            cat = "type2"
        else:
            cat = "other"
        type_counts[pz][cat] += 1

    result = []
    for pz_code, pdu in pdus.items():
        counts = type_counts.get(pz_code, {})
        total = sum(counts.values())
        if total == 0:
            continue
        t1 = counts.get("type1", 0)
        t2 = counts.get("type2", 0)
        other = total - t1 - t2
        if t1 >= t2 and t1 >= other:
            dominant = "type1"
        elif t2 >= other:
            dominant = "type2"
        else:
            dominant = "other"
        coords = pdu.lead_organisation_geocoordinates
        result.append(
            {
                "lat": coords.y,
                "lon": coords.x,
                "label": pdu.lead_organisation_name or pdu.pz_code,
                "pz_code": pz_code,
                "total_patients": total,
                "dominant_type": dominant,
                "pct_type1": round(t1 / total * 100),
                "pct_type2": round(t2 / total * 100),
                "pct_other": round(other / total * 100),
            }
        )

    return result


def all_pdus_age_map_data(audit_period) -> list[dict]:
    """Age-group breakdown per PDU for the national bubble map (T1DM only).

    Patients are split at their 16th birthday (at audit start date):
        - 'under_16': age < 16
        - 'over_16':  age >= 16

    Each entry:
        {
            "lat": float, "lon": float, "label": str, "pz_code": str,
            "total_patients": int,
            "dominant_age_group": "under_16" | "over_16",
            "pct_under_16": int,   # 0-100
            "pct_over_16": int,    # 0-100
        }
    """
    audit_range = (audit_period.start_date, audit_period.end_date)

    pdus = {
        pdu.pz_code: pdu
        for pdu in PaediatricDiabetesUnit.objects.filter(
            active=True,
            pdu_submissions__submission_active=True,
            pdu_submissions__audit_period=audit_period,
            lead_organisation_geocoordinates__isnull=False,
        ).distinct()
    }
    if not pdus:
        return []

    rows = (
        Patient.objects.filter(
            submissions__submission_active=True,
            submissions__audit_period=audit_period,
            submissions__paediatric_diabetes_unit__pz_code__in=pdus.keys(),
            diabetes_type=DIABETES_TYPES[0][0],
            visit__visit_date__range=audit_range,
            date_of_birth__gt=audit_period.start_date - relativedelta(years=25),
        )
        .distinct()
        .values("pk", "date_of_birth", "submissions__paediatric_diabetes_unit__pz_code")
    )

    cutoff_16 = audit_period.start_date - relativedelta(years=16)
    age_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    seen: set[int] = set()
    for row in rows:
        pk = row["pk"]
        if pk in seen:
            continue
        seen.add(pk)
        pz = row["submissions__paediatric_diabetes_unit__pz_code"]
        dob = row["date_of_birth"]
        group = "under_16" if (dob is None or dob > cutoff_16) else "over_16"
        age_counts[pz][group] += 1

    result = []
    for pz_code, pdu in pdus.items():
        counts = age_counts.get(pz_code, {})
        total = sum(counts.values())
        if total == 0:
            continue
        under = counts.get("under_16", 0)
        over = total - under
        dominant = "under_16" if under >= over else "over_16"
        coords = pdu.lead_organisation_geocoordinates
        result.append(
            {
                "lat": coords.y,
                "lon": coords.x,
                "label": pdu.lead_organisation_name or pdu.pz_code,
                "pz_code": pz_code,
                "total_patients": total,
                "dominant_age_group": dominant,
                "pct_under_16": round(under / total * 100),
                "pct_over_16": round(over / total * 100),
            }
        )

    return result
