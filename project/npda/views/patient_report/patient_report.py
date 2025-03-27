from enum import Enum
import logging
from datetime import date

# Django imports
from django.shortcuts import render
from django.views.generic import ListView
from project.npda.models import Patient
from project.npda.kpi_class.kpis import CalculateKPIS
from project.npda.views.decorators import login_and_otp_required
from django.db.models import (
    Case,
    When,
    Value,
    BooleanField,
    F,
    ExpressionWrapper,
    IntegerField,
    Count,
)
from project.npda.views.patient_report.helpers import get_pt_level_table_data
from project.npda.views.patient_report.template_data import KPI_CATEGORY_ATTR_MAP, TEXT

# Django imports


logger = logging.getLogger(__name__)


class TableCategories(Enum):
    HEALTH_CHECKS = "health_checks"
    ADDITIONAL_CARE_PROCESSES = "additional_care_processes"
    CARE_AT_DIAGNOSIS = "care_at_diagnosis"
    ADMISSIONS = "admissions"
    TREATMENT = "treatment"

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
        ]

    @classmethod
    def default(cls):
        return cls.HEALTH_CHECKS.value


class PatientReportView(ListView):
    model = Patient
    template_name = "patient_report/new_patient_report.html"
    context_object_name = "patients"
    paginate_by = 10

    def get_queryset(self):
        request = self.request

        # Get the category from the request
        category = request.GET.get("category", TableCategories.default())

        # Validate and set the category
        if category not in TableCategories.values():
            raise ValueError(f"Invalid category: {category}")
        self.selected_category = category

        # First need to get the relevant calculations
        pz_code = request.session.get("pz_code")

        selected_audit_year = int(request.session.get("selected_audit_year"))
        # TODO: remove min clamp once available audit year from preference filter sorted
        selected_audit_year = max(selected_audit_year, 2024)
        calculation_date = date(year=selected_audit_year, month=5, day=1)

        calculate_kpis = CalculateKPIS(
            calculation_date=calculation_date, return_pt_querysets=True
        )
        get_attribute_name = calculate_kpis.kpi_name_registry.get_attribute_name

        # Set relevant patients
        calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])

        # Run the relevant subset of calculations
        selected_kpis = KPI_CATEGORY_ATTR_MAP[self.selected_category]

        pt_qs = Patient.objects.all()
        if self.selected_category == "health_checks":
            pt_qs = pt_qs.values(
                "nhs_number",
                "visit__hba1c",
            )
        elif self.selected_category == "additional_care_processes":
            pt_qs = pt_qs.values(
                "nhs_number",
                "visit__psychological_screening_assessment_date",
            )

        return pt_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # All categories
        context["table_categories"] = TableCategories.choices()
        # Selected category
        context["selected_category"] = self.selected_category
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
            else:
                return ["patient_report/health_checks_table_partial.html"]

        return ["patient_report/new_patient_report.html"]


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

    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=True
    )

    # Set relevant patients
    calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])

    # Run the relevant subset of calculations
    selected_kpis = KPI_CATEGORY_ATTR_MAP[pt_level_menu_tab_selected]
    kpi_calculations_object = calculate_kpis._calculate_kpis(selected_kpis)

    try:
        selected_table_headers, selected_table_data = get_pt_level_table_data(
            category=pt_level_menu_tab_selected,
            calculate_kpis_object=calculate_kpis,
            kpi_calculations_object=kpi_calculations_object,
        )
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
        "highlight": highlight,
        "table_data": {
            "headers": selected_table_headers,
            "row_data": selected_table_data,
            "ineligible_hover_reason": selected_data.get("ineligible_hover_reason", {}),
        },
    }

    return render(
        request,
        template_name="patient_report/patient_report.html",
        context=context,
    )
