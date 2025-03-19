import logging
from datetime import date


# Django imports

# Django imports
from django.shortcuts import render

from project.npda.kpi_class.kpis import CalculateKPIS
from project.npda.views.patient_report.helpers import (
    get_pt_level_table_data,
)
from project.npda.views.patient_report.template_data import KPI_CATEGORY_ATTR_MAP, TEXT
from project.npda.views.decorators import login_and_otp_required
from django.db.models import Case, When, Value, BooleanField, F, ExpressionWrapper, IntegerField

logger = logging.getLogger(__name__)


@login_and_otp_required()
def patient_report(request):

    pt_level_menu_tab_selected = request.GET.get("selected", "health_checks")

    # State vars
    # Colour the selected menu tab
    highlight = {f"{key}": key == pt_level_menu_tab_selected for key in TEXT.keys()}

    selected_data: dict = TEXT[pt_level_menu_tab_selected]

    # Gather the selected category's data

    # First need to get the relevant calculations
    pz_code = request.session.get("pz_code")

    selected_audit_year = int(request.session.get("selected_audit_year"))
    # TODO: remove min clamp once available audit year from preference filter sorted
    selected_audit_year = max(selected_audit_year, 2024)
    calculation_date = date(year=selected_audit_year, month=5, day=1)

    calculate_kpis = CalculateKPIS(calculation_date=calculation_date, return_pt_querysets=True)
    get_attribute_name = calculate_kpis.kpi_name_registry.get_attribute_name

    # Set relevant patients
    calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])

    # Run the relevant subset of calculations
    selected_kpis = KPI_CATEGORY_ATTR_MAP[pt_level_menu_tab_selected]
    kpi_calculations_object = calculate_kpis._calculate_kpis(selected_kpis)

    try:
        if pt_level_menu_tab_selected == "health_checks":
            # Get queryset for health check pts (annotated with True / False for each KPI
            # alongside total column, which excludes kpi_30_retinal_screening)
            # Get queryset for health check pts (annotated with True / False for each KPI)
            kpi_names = [
                get_attribute_name(kpi_idx) for kpi_idx in selected_kpis
            ]

            # Start with eligible patients from any KPI (using HbA1c as base)
            annotated_queryset = kpi_calculations_object['calculated_kpi_values']['kpi_25_hba1c']['patient_querysets']['eligible']

            # Annotate each KPI's pass/fail status
            annotations = {}
            for kpi_name in kpi_names:
                passed_patients = kpi_calculations_object['calculated_kpi_values'][kpi_name]['patient_querysets']['passed']
                
                annotations[f'passed_{kpi_name}'] = Case(
                    When(id__in=passed_patients.values('id'), then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                )

            # Apply all annotations at once
            annotated_queryset = annotated_queryset.annotate(**annotations)

            # Add total passed count (excluding retinal screening)
            annotated_queryset = annotated_queryset.annotate(
                total_passed=ExpressionWrapper(
                    F('passed_kpi_25_hba1c') + F('passed_kpi_26_bmi') + 
                    F('passed_kpi_27_thyroid_screen') + F('passed_kpi_28_blood_pressure') + 
                    F('passed_kpi_29_urinary_albumin') + F('passed_kpi_30_retinal_screening') + 
                    F('passed_kpi_31_foot_examination'),
                    output_field=IntegerField()
                )
            ).values('nhs_number', *[f'passed_{kpi_name}' for kpi_name in kpi_names], 'total_passed')

            selected_table_headers = [
                "NHS Number",
                "HbA1c",
                "BMI",
                "Thyroid Screen",
                "Blood Pressure",
                "Urinary Albumin",
                "Retinal Screening",
                "Foot Examination",
                "Total Passed",
            ]
                
    except Exception as e:
        logger.error(
            f"Error getting pt_level_table_data for {pt_level_menu_tab_selected=} {e=}",
            exc_info=True,
        )
        # messages.error(request, f"Error getting data!")

        selected_table_headers = []
        selected_table_data = []

    context = {
        "text": selected_data,
        "selected": pt_level_menu_tab_selected,
        "table_data": {
            "headers": selected_table_headers,
            "data": annotated_queryset,
            "ineligible_hover_reason": selected_data.get("ineligible_hover_reason", {}),
        },
    }

    return render(
        request,
        template_name="patient_report/patient_report.html",
        context=context,
    )
