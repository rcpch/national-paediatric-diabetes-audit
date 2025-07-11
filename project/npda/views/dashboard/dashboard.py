# Python imports
import json
import logging
from datetime import date

from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.contrib import messages
from django.db.models import (
    BooleanField,
    Case,
    Exists,
    F,
    OuterRef,
    When,
    IntegerField
)
from django.shortcuts import render

from project import constants
from project.npda.general_functions.audit_period import audit_period_for_audit_year
from project.npda.general_functions.quarter_for_date import retrieve_quarter_for_date
from project.npda.kpi_class.kpis import CalculateKPIS
from project.npda.models.paediatric_diabetes_unit import (
    PaediatricDiabetesUnit as PaediatricDiabetesUnitClass,
)
from project.npda.models.patient import Patient
from project.npda.models.audit_period import AuditPeriod
from project.npda.views.decorators import login_and_otp_required

# LOGGING
logger = logging.getLogger(__name__)


# 🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨
# 🚨 TODO SHOULD BE REMOVED, JUST DURING DEV  🚨
# 🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨
@login_and_otp_required()
def temp_set_eligible_kpi_7(request):
    """Temporary util to set some seeded patients attrs manually

    KPI7
        to be eligible for kpi 7 (T1DM diagnosed
        during the audit period) which is denominator for kpis 41-43.

        This is because the default behaviour of the `PatientFactory` .build method (used in the
        csv seeder) is to choose a random diabetes_diagnosis between the pt's DoB and audit_start_date.

    """
    if not request.user.is_superuser:
        logger.error("User %s tried to run temp util to set KPI 7", request.user)
        raise PermissionError("Only superusers can run this util")

    from django.http import HttpResponse

    _ = 10
    logger.error(f"🔥 Setting {_} patients to be eligible for KPI 7")
    to_set_kpi_7_eligible = Patient.objects.filter(
        diabetes_type=constants.diabetes_types.DIABETES_TYPES[0][0]
    )[:_]
    for pt in to_set_kpi_7_eligible:
        pt.diagnosis_date = CalculateKPIS().audit_start_date + relativedelta(months=4)
        pt.save()
        logger.warning(f"Succesfully set {pt} to be eligible for KPI 7")

    return HttpResponse(
        f"Set {_} patients to be eligible for KPI 7: {''.join([f'<p>{pt.nhs_number}</p>' for pt in to_set_kpi_7_eligible])}",
        status=200,
    )


# 🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨
# 🚨 TODO SHOULD BE REMOVED, JUST DURING DEV  🚨
# 🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨


@login_and_otp_required()
def dashboard(request):
    """
    Dashboard view for the KPIs.
    """
    template = "dashboard.html"
    if request.htmx:
        template = "dashboard/dashboard_base.html"
    pz_code = request.session.get("pz_code")

    PaediatricDiabetesUnit: PaediatricDiabetesUnitClass = apps.get_model(
        "npda", "PaediatricDiabetesUnit"
    )
    try:
        pdu = PaediatricDiabetesUnit.objects.get(pz_code=pz_code)
    except PaediatricDiabetesUnit.DoesNotExist:
        messages.error(
            request=request,
            message=f"Paediatric Diabetes Unit with PZ code {pz_code} does not exist",
        )
        return render(request, "dashboard.html")

    audit_period = AuditPeriod.objects.get_audit_period_for_request(request)
    
    current_date = date.today()
    calculation_date = audit_period.kpi_calculation_date()

    if audit_period.start_date > current_date:
        # Future audit period - likely no data yet but you can still select it
        current_quarter = None
        days_remaining_until_audit_end_date = (audit_period.end_date - current_date).days
    elif current_date > audit_period.end_date:
        # Past audit period
        current_quarter = None
        days_remaining_until_audit_end_date = None
    else:
        # Current audit period
        current_quarter = retrieve_quarter_for_date(current_date)
        days_remaining_until_audit_end_date = (audit_period.end_date - current_date).days

    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=True
    )

    kpi_calculations_object = calculate_kpis.calculate_kpis_for_pdus(pz_codes=[pz_code])

    # From this, gather specific chart data required

    # new diagnoses
    new_diagnosis_per_quarter_value_counts_pct = (
        calculate_kpis.calculate_kpi_2_total_new_diagnoses_stratified_by_quarter()
    )

    context = {
        "scatter_plot_select_list": _scatter_plot_select_list("new_diagnoses"),
        "pdu_object": pdu,
        # "pdu_lead_organisation": pdu_lead_organisation,
        "kpi_calculations_object": kpi_calculations_object,
        "current_date": calculation_date,
        "current_quarter": current_quarter,
        "days_remaining_until_audit_end_date": days_remaining_until_audit_end_date,
        "charts": {
            "new_diagnoses_per_quarter_value_counts_pct": {
                "no_eligible_patients": kpi_calculations_object[
                    "calculated_kpi_values"
                ]["kpi_1_total_eligible"]["total_eligible"]
                == 0,
                "data": json.dumps(new_diagnosis_per_quarter_value_counts_pct),
            },
            "map": json.dumps(
                dict(
                    pdu_pk=pdu.pk,
                    selected_audit_year=audit_period.audit_year(),
                )
            ),
        },
        # TODO: this should be an enum but we're currently not doing benchmarking so can update
        # at that point
        "aggregation_level": "pdu",
    }

    # Gather totals for the patient health check KPIs
    patient_health_check_totals_to_return = patient_health_check_totals(
        calculate_kpis=calculate_kpis,
        pz_code=pz_code,
        calculation_date=calculation_date,
    )
    context.update(patient_health_check_totals_to_return)

    return render(request, template_name=template, context=context)


def _scatter_plot_select_list(button_name_selected: str):
    """
    Keeps track of which filter buttons are selected in the scatter plot
    """
    scatter_buttons = [
        {
            "name": "new_diagnoses",
            "selected": button_name_selected == "new_diagnoses",
            "enabled": True,
            "title": "New diagnoses",
        },
        {
            "name": "new_admissions",
            "selected": button_name_selected == "new_admissions",
            "enabled": True,
            "title": "Hospital Admissions",
        },
        {
            "name": "transitioned_to_adult_service",
            "selected": button_name_selected == "transitioned_to_adult_service",
            "enabled": True,
            "title": "Transitioned",
        },
    ]
    return scatter_buttons

def patient_health_check_totals(calculate_kpis, pz_code, calculation_date):
    """
    Returns the totals for the patient health check KPIs.
    """
    calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])
    # Select all T1DM patients for PZ code - Note that Jersey (PZ248) has a different patient identifier field
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

    # Use the patient querysets to calculate totals
    # Pre-calculate totals for the health checks from the base queryset before adding category-specific annotations
    complete_year_patients = pt_qs.filter(is_complete_year_of_care=True)
    
    # Calculate totals using the KPI methods directly
    total_passed_hba1c = calculate_kpis.calculate_kpi_25_hba1c().patient_querysets["passed"].filter(
        pk__in=complete_year_patients.values_list("pk", flat=True)
    ).count()
    total_eligible_hba1c = complete_year_patients.count()
    
    total_passed_bmi = calculate_kpis.calculate_kpi_26_bmi().patient_querysets["passed"].filter(
        pk__in=complete_year_patients.values_list("pk", flat=True)
    ).count()
    total_eligible_bmi = complete_year_patients.count()
    
    total_passed_thyroid_screen = calculate_kpis.calculate_kpi_27_thyroid_screen().patient_querysets["passed"].filter(
        pk__in=complete_year_patients.values_list("pk", flat=True)
    ).count()
    total_eligible_thyroid_screen = complete_year_patients.count()
    
    # For age-specific checks (12+ years old)
    complete_year_12plus = complete_year_patients.filter(
        date_of_birth__lte=calculation_date - relativedelta(years=12)
    )
    
    total_passed_blood_pressure = calculate_kpis.calculate_kpi_28_blood_pressure().patient_querysets["passed"].filter(
        pk__in=complete_year_12plus.values_list("pk", flat=True)
    ).count()
    total_eligible_blood_pressure = complete_year_12plus.count()
    
    total_passed_urinary_albumin = calculate_kpis.calculate_kpi_29_urinary_albumin().patient_querysets["passed"].filter(
        pk__in=complete_year_12plus.values_list("pk", flat=True)
    ).count()
    total_eligible_urinary_albumin = complete_year_12plus.count()
    
    total_passed_foot_exam = calculate_kpis.calculate_kpi_31_foot_examination().patient_querysets["passed"].filter(
        pk__in=complete_year_12plus.values_list("pk", flat=True)
    ).count()
    total_eligible_foot_exam = complete_year_12plus.count()
    # pt_qs = pt_qs.annotate(
    #     is_gte_12yo=Q(
    #         date_of_birth__lte=calculation_date - relativedelta(years=12)
    #     ),
    #     passed_hba1c=Case(
    #         When(
    #             Exists(
    #                 kpi_calculations_object.calculate_kpi_25_hba1c()
    #                 .patient_querysets["passed"]
    #                 .filter(pk=OuterRef("pk"))
    #             ),
    #             then=True,
    #         ),
    #         default=False,
    #         output_field=BooleanField(),
    #     ),
    #     passed_bmi=Case(
    #         When(
    #             Exists(
    #                 kpi_calculations_object.calculate_kpi_26_bmi()
    #                 .patient_querysets["passed"]
    #                 .filter(pk=OuterRef("pk"))
    #             ),
    #             then=True,
    #         ),
    #         default=False,
    #         output_field=BooleanField(),
    #     ),
    #     passed_thyroid_screen=Case(
    #         When(
    #             Exists(
    #                 kpi_calculations_object.calculate_kpi_27_thyroid_screen()
    #                 .patient_querysets["passed"]
    #                 .filter(pk=OuterRef("pk"))
    #             ),
    #             then=True,
    #         ),
    #         default=False,
    #         output_field=BooleanField(),
    #     ),
    #     passed_blood_pressure=Case(
    #         When(
    #             Exists(
    #                 kpi_calculations_object.calculate_kpi_28_blood_pressure()
    #                 .patient_querysets["passed"]
    #                 .filter(pk=OuterRef("pk"))
    #             ),
    #             then=True,
    #         ),
    #         default=Case(
    #             When(is_gte_12yo=True, then=False),
    #             default=None,
    #             output_field=BooleanField(),
    #         ),
    #         output_field=BooleanField(),
    #     ),
    #     passed_urinary_albumin=Case(
    #         When(
    #             Exists(
    #                 kpi_calculations_object.calculate_kpi_29_urinary_albumin()
    #                 .patient_querysets["passed"]
    #                 .filter(pk=OuterRef("pk"))
    #             ),
    #             then=True,
    #         ),
    #         default=Case(
    #             When(is_gte_12yo=True, then=False),
    #             default=None,
    #             output_field=BooleanField(),
    #         ),
    #         output_field=BooleanField(),
    #     ),
    #     passed_retinal_screening=Case(
    #         When(
    #             Exists(
    #                 kpi_calculations_object.calculate_kpi_30_retinal_screening()
    #                 .patient_querysets["passed"]
    #                 .filter(pk=OuterRef("pk"))
    #             ),
    #             then=True,
    #         ),
    #         default=Case(
    #             When(is_gte_12yo=True, then=False),
    #             default=None,
    #             output_field=BooleanField(),
    #         ),
    #         output_field=BooleanField(),
    #     ),
    #     passed_foot_exam=Case(
    #         When(
    #             Exists(
    #                 kpi_calculations_object.calculate_kpi_31_foot_examination()
    #                 .patient_querysets["passed"]
    #                 .filter(pk=OuterRef("pk"))
    #             ),
    #             then=True,
    #         ),
    #         default=Case(
    #             When(is_gte_12yo=True, then=False),
    #             default=None,
    #             output_field=BooleanField(),
    #         ),
    #         output_field=BooleanField(),
    #     ),
    #     num_passed=Case(
    #         When(
    #             is_gte_12yo=True,
    #             then=(
    #                 Case(When(passed_hba1c=True, then=1), default=0)
    #                 + Case(When(passed_bmi=True, then=1), default=0)
    #                 + Case(When(passed_thyroid_screen=True, then=1), default=0)
    #                 + Case(When(passed_blood_pressure=True, then=1), default=0)
    #                 + Case(When(passed_urinary_albumin=True, then=1), default=0)
    #                 + Case(When(passed_foot_exam=True, then=1), default=0)
    #             ),
    #         ),
    #         When(
    #             is_gte_12yo=False,
    #             then=(
    #                 Case(When(passed_hba1c=True, then=1), default=0)
    #                 + Case(When(passed_bmi=True, then=1), default=0)
    #                 + Case(When(passed_thyroid_screen=True, then=1), default=0)
    #             ),
    #         ),
    #         default=0,
    #         output_field=IntegerField(),
    #     ),
    #     num_total=Case(
    #         When(is_gte_12yo=True, then=6),
    #         When(is_gte_12yo=False, then=3),
    #         default=0,
    #         output_field=IntegerField(),
    #     ),
    # ).values(
    #     "pk",
    #     "patient_identifier",
    #     "is_gte_12yo",
    #     "is_complete_year_of_care",
    #     "passed_hba1c",
    #     "passed_bmi",
    #     "passed_thyroid_screen",
    #     "passed_blood_pressure",
    #     "passed_urinary_albumin",
    #     "passed_foot_exam",
    #     "num_passed",
    #     "num_total",
    #     "passed_retinal_screening",
    # )

    # Gather totals
    return {
        "total_passed_hba1c": total_passed_hba1c,
        "total_eligible_hba1c": total_eligible_hba1c,
        "total_passed_bmi": total_passed_bmi,
        "total_eligible_bmi": total_eligible_bmi,
        "total_passed_thyroid_screen": total_passed_thyroid_screen,
        "total_eligible_thyroid_screen": total_eligible_thyroid_screen,
        "total_passed_blood_pressure": total_passed_blood_pressure,
        "total_eligible_blood_pressure": total_eligible_blood_pressure,
        "total_passed_urinary_albumin": total_passed_urinary_albumin,
        "total_eligible_urinary_albumin": total_eligible_urinary_albumin,
        "total_passed_foot_exam": total_passed_foot_exam,
        "total_eligible_foot_exam": total_eligible_foot_exam,
    }