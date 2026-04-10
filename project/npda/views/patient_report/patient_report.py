import io
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum

import pandas as pd
from django.db.models import QuerySet

# Django imports
from django.http import HttpResponse
from django.views.generic import ListView

from project.npda.general_functions.breadcrumbs import data_breadcrumbs
from project.npda.general_functions.patient_report import (
    queries as patient_report_queries,
)
from project.npda.models import AuditPeriod, Patient
from project.npda.views.decorators import check_data_permissions, login_and_otp_required
from project.npda.views.mixins import LoginAndOTPRequiredMixin, PDUPermissionMixin

logger = logging.getLogger(__name__)


def apply_care_at_diagnosis_display(patients, reference_date):
    def apply_status(patient, diagnosis_date, *, due_days, result_key, prefix):
        due_date = diagnosis_date + timedelta(days=due_days)
        patient[f"{prefix}_due_date"] = due_date

        if patient.get(result_key) is True:
            patient[f"{prefix}_status"] = "on_time"
            return

        if reference_date > due_date:
            patient[f"{prefix}_status"] = "overdue"
            return

        days_remaining = (due_date - reference_date).days
        patient[f"{prefix}_status"] = "countdown"
        patient[f"{prefix}_days_remaining"] = days_remaining
        if days_remaining == 0:
            label = "Due today"
        elif days_remaining == 1:
            label = "Due in 1 day"
        else:
            label = f"Due in {days_remaining} days"
        patient[f"{prefix}_countdown_label"] = label

    for patient in patients:
        diagnosis_date = patient.get("diagnosis_date")
        if not diagnosis_date:
            continue

        apply_status(
            patient,
            diagnosis_date,
            due_days=14,
            result_key="carbohydrate_counting_education",
            prefix="carb_counting",
        )
        apply_status(
            patient,
            diagnosis_date,
            due_days=90,
            result_key="coeliac_disease_screening",
            prefix="coeliac_screening",
        )
        apply_status(
            patient,
            diagnosis_date,
            due_days=90,
            result_key="thyroid_disease_screening",
            prefix="thyroid_screening",
        )

    return patients


def apply_carb_counting_display(patients, reference_date):
    for patient in patients:
        diagnosis_date = patient.get("diagnosis_date")
        if not diagnosis_date:
            continue

        due_date = diagnosis_date + timedelta(days=14)
        patient["carb_counting_due_date"] = due_date

        if patient.get("carbohydrate_counting_education") is True:
            patient["carb_counting_status"] = "on_time"
            continue

        if reference_date > due_date:
            patient["carb_counting_status"] = "overdue"
            continue

        days_remaining = (due_date - reference_date).days
        patient["carb_counting_status"] = "countdown"
        patient["carb_counting_days_remaining"] = days_remaining
        if days_remaining == 0:
            patient["carb_counting_countdown_label"] = "Due today"
        elif days_remaining == 1:
            patient["carb_counting_countdown_label"] = "Due in 1 day"
        else:
            patient["carb_counting_countdown_label"] = f"Due in {days_remaining} days"

    return patients


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


def calculate_queryset(
    pdu, audit_period: AuditPeriod, selected_category: str
) -> QuerySet[Patient]:
    base_qs = patient_report_queries.build_base_queryset(pdu, audit_period)
    patient_identifier = patient_report_queries._patient_identifier_field(pdu)

    if selected_category == TableCategories.HEALTH_CHECKS.value:
        pt_qs = (
            patient_report_queries.annotate_health_checks(base_qs, audit_period)
            .order_by(
                "-is_complete_year_of_care",
                "-passed_hba1c",
                "-passed_bmi",
                "-passed_thyroid_screen",
                "-passed_blood_pressure",
                "-passed_urinary_albumin",
                "-passed_foot_exam",
                "patient_identifier",
            )
            .values(
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
                "latest_retinal_screening_date",
            )
        )
        return pt_qs, patient_identifier

    if selected_category == TableCategories.ADDITIONAL_CARE_PROCESSES.value:
        pt_qs = (
            patient_report_queries.annotate_additional_care_processes(
                base_qs, audit_period
            )
            .order_by(
                "-is_complete_year_of_care",
                "-hba1c_4plus",
                "-psychological_assessment",
                "-smoking_status",
                "-smoking_cessation_referral",
                "-additional_dietetic_appt_offered",
                "-pts_attending_additional_dietetic_appt",
                "-influenza_immunisation_recommended",
                "-sick_day_rules_advice",
                "patient_identifier",
            )
            .values(
                "pk",
                "patient_identifier",
                "is_complete_year_of_care",
                "is_gte_12yo",
                "hba1c_4plus",
                "psychological_assessment",
                "smoking_status",
                "smoking_cessation_referral",
                "additional_dietetic_appt_offered",
                "pts_attending_additional_dietetic_appt",
                "influenza_immunisation_recommended",
                "sick_day_rules_advice",
            )
        )
        return pt_qs, patient_identifier

    if selected_category == TableCategories.CARE_AT_DIAGNOSIS.value:
        pt_qs = (
            patient_report_queries.annotate_care_at_diagnosis(base_qs, audit_period)
            .order_by(
                "-coeliac_disease_screening",
                "-thyroid_disease_screening",
                "-carbohydrate_counting_education",
                "patient_identifier",
            )
            .values(
                "pk",
                "patient_identifier",
                "diagnosis_date",
                "coeliac_disease_screening",
                "thyroid_disease_screening",
                "carbohydrate_counting_education",
            )
        )
        return pt_qs, patient_identifier

    if selected_category == TableCategories.ADMISSIONS.value:
        pt_qs = patient_report_queries.annotate_admissions(
            base_qs, audit_period
        ).values(
            "pk",
            "patient_identifier",
            "is_complete_year_of_care",
            "number_of_admissions",
            "number_of_dka_admissions",
        )
        pt_qs = patient_report_queries.calculate_hba1c_values(pt_qs, audit_period)
        return pt_qs, patient_identifier

    if selected_category == TableCategories.TREATMENT.value:
        pt_qs = patient_report_queries.annotate_treatment(base_qs, audit_period).values(
            "pk",
            "patient_identifier",
            "is_complete_year_of_care",
            "treatment_regimen",
            "glucose_monitoring",
            "hcl",
        )
        return pt_qs, patient_identifier

    if selected_category == TableCategories.OUTCOMES.value:
        outcomes_qs = patient_report_queries.build_base_queryset(
            pdu, audit_period, type1_only=False
        )
        pt_qs = patient_report_queries.annotate_outcomes(
            outcomes_qs, audit_period
        ).values(
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
        return pt_qs, patient_identifier

    raise ValueError(f"Unknown category: {selected_category}")


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

    def get_queryset(self):
        request = self.request
        category = request.GET.get("category", TableCategories.default())
        sort_field = request.GET.get("sort")
        sort_order = request.GET.get("order", "asc")
        if category not in TableCategories.values():
            raise ValueError(f"Invalid category: {category}")
        self.selected_category = category
        pz_code = self.pdu.pz_code

        pt_qs, patient_identifier = calculate_queryset(
            self.pdu, self.audit_period, category
        )

        allowed_sort_fields = {
            TableCategories.HEALTH_CHECKS.value: {
                "passed_hba1c",
                "passed_bmi",
                "passed_thyroid_screen",
                "passed_blood_pressure",
                "passed_urinary_albumin",
                "passed_foot_exam",
            },
            TableCategories.ADDITIONAL_CARE_PROCESSES.value: {
                "hba1c_4plus",
                "psychological_assessment",
                "smoking_status",
                "smoking_cessation_referral",
                "additional_dietetic_appt_offered",
                "pts_attending_additional_dietetic_appt",
                "influenza_immunisation_recommended",
                "sick_day_rules_advice",
            },
            TableCategories.CARE_AT_DIAGNOSIS.value: {
                "diagnosis_date",
                "carbohydrate_counting_education",
                "coeliac_disease_screening",
                "thyroid_disease_screening",
            },
            TableCategories.ADMISSIONS.value: {
                "kpi_44_mean_hba1c",
                "kpi_45_median_hba1c",
                "number_of_admissions",
                "number_of_dka_admissions",
            },
            TableCategories.TREATMENT.value: {
                "treatment_regimen",
                "glucose_monitoring",
                "hcl",
            },
            TableCategories.OUTCOMES.value: {
                "latest_hba1c_mmol_mol",
                "hba1c_delta",
                "kpi_45_median_hba1c",
                "kpi_44_mean_hba1c",
            },
        }
        if sort_field:
            allowed = allowed_sort_fields.get(self.selected_category, set())
            allowed = allowed | {"nhs_number", "unique_identifier"}
            if sort_field not in allowed:
                sort_field = None

        # Sort the queryset based on the selected sort field and order
        if sort_field:
            # Handle sort direction
            if sort_field == "unique_identifier":
                sort_field = (
                    "unique_reference_number" if pz_code == "PZ248" else "nhs_number"
                )
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
                pt_qs = patient_report_queries.calculate_hba1c_values(
                    pt_qs, self.audit_period
                )

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
                pt_qs = patient_report_queries.calculate_hba1c_values(
                    pt_qs, self.audit_period
                )
        else:
            # Default ordering
            order_by = ["-is_complete_year_of_care", patient_identifier]

            if self.selected_category == TableCategories.CARE_AT_DIAGNOSIS.value:
                order_by = [patient_identifier]

            pt_qs = pt_qs.order_by(*order_by)
            pt_qs = patient_report_queries.calculate_hba1c_values(
                pt_qs, self.audit_period
            )

        if self.selected_category == TableCategories.CARE_AT_DIAGNOSIS.value:
            reference_date = self.audit_period.kpi_calculation_date()
            pt_qs = apply_care_at_diagnosis_display(list(pt_qs), reference_date)

        return pt_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["audit_period"] = self.audit_period.slug
        context["pz_code"] = self.pdu.pz_code
        context["is_jersey"] = self.pdu.pz_code == "PZ248"

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
                "thyroid_screen": "Not required as within 1 year of diagnosis",
            }

            qs = self.object_list
            complete_year = qs.filter(is_complete_year_of_care=True)
            complete_year_12plus = complete_year.filter(is_gte_12yo=True)

            context["total_passed_hba1c"] = complete_year.filter(
                passed_hba1c=True
            ).count()
            context["total_eligible_hba1c"] = complete_year.count()

            context["total_passed_bmi"] = complete_year.filter(passed_bmi=True).count()
            context["total_eligible_bmi"] = complete_year.count()

            context["total_passed_thyroid_screen"] = complete_year.filter(
                passed_thyroid_screen=True
            ).count()
            context["total_eligible_thyroid_screen"] = complete_year.count()

            context["total_passed_blood_pressure"] = complete_year_12plus.filter(
                passed_blood_pressure=True
            ).count()
            context["total_eligible_blood_pressure"] = complete_year_12plus.count()

            context["total_passed_urinary_albumin"] = complete_year_12plus.filter(
                passed_urinary_albumin=True
            ).count()
            context["total_eligible_urinary_albumin"] = complete_year_12plus.count()

            context["total_passed_foot_exam"] = complete_year_12plus.filter(
                passed_foot_exam=True
            ).count()
            context["total_eligible_foot_exam"] = complete_year_12plus.count()

            context["total_passed_retinal_screening"] = complete_year.filter(
                passed_retinal_screening="complete"
            ).count()
            context["total_eligible_retinal_screening"] = complete_year.count()

        elif self.selected_category == TableCategories.ADDITIONAL_CARE_PROCESSES.value:
            context["ineligible_reasons"] = {
                "smoking_status": "Not required as less than 12 years old",
                "smoking_cessation_referral": {
                    "under_12": "Not required as less than 12 years old",
                    "non_smoker_no_referral": "Not required as non-smoker",
                },
            }

            qs = self.object_list
            complete_year = qs.filter(is_complete_year_of_care=True)
            complete_year_12plus = complete_year.filter(is_gte_12yo=True)
            # Smokers ≥12: "True" = referred, "False" = eligible but not referred
            complete_year_smokers_12plus = complete_year_12plus.filter(
                smoking_cessation_referral__in=["True", "False"]
            )

            context["total_passed_hba1c_4plus"] = complete_year.filter(
                hba1c_4plus=True
            ).count()
            context["total_eligible_hba1c_4plus"] = complete_year.count()

            context["total_passed_psychological_assessment"] = complete_year.filter(
                psychological_assessment=True
            ).count()
            context["total_eligible_psychological_assessment"] = complete_year.count()

            context["total_passed_additional_dietetic_appt_offered"] = (
                complete_year.filter(additional_dietetic_appt_offered=True).count()
            )
            context["total_eligible_additional_dietetic_appt_offered"] = (
                complete_year.count()
            )

            context["total_passed_pts_attending_additional_dietetic_appt"] = (
                complete_year.filter(
                    pts_attending_additional_dietetic_appt=True
                ).count()
            )
            context["total_eligible_pts_attending_additional_dietetic_appt"] = (
                complete_year.count()
            )

            context["total_passed_influenza_immunisation_recommended"] = (
                complete_year.filter(influenza_immunisation_recommended=True).count()
            )
            context["total_eligible_influenza_immunisation_recommended"] = (
                complete_year.count()
            )

            context["total_passed_sick_day_rules_advice"] = complete_year.filter(
                sick_day_rules_advice=True
            ).count()
            context["total_eligible_sick_day_rules_advice"] = complete_year.count()

            context["total_passed_smoking_status"] = complete_year_12plus.filter(
                smoking_status=True
            ).count()
            context["total_eligible_smoking_status"] = complete_year_12plus.count()

            context["total_passed_smoking_cessation_referral"] = (
                complete_year_smokers_12plus.filter(
                    smoking_cessation_referral="True"
                ).count()
            )
            context["total_eligible_smoking_cessation_referral"] = (
                complete_year_smokers_12plus.count()
            )

        context["breadcrumbs"] = data_breadcrumbs(
            self.pdu, self.audit_period, [("Patient Report", "pdu-patient-report")]
        )

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


def measure_status(complete: bool | None) -> str:
    match complete:
        case True:
            return "COMPLETE"
        case False:
            return "INCOMPLETE"
        case None:
            return "NA"


@login_and_otp_required()
@check_data_permissions()
def download_patient_report(request, audit_period, pdu):
    contents = io.BytesIO()

    with pd.ExcelWriter(contents, engine="openpyxl") as writer:
        for category in TableCategories:
            pt_qs, patient_identifier = calculate_queryset(
                pdu=pdu,
                audit_period=audit_period,
                selected_category=category.value,
            )

            data = defaultdict(list)

            for row in pt_qs:
                data[patient_identifier].append(row["patient_identifier"])

                match category:
                    case TableCategories.HEALTH_CHECKS:
                        data["complete_year_of_care"].append(
                            row["is_complete_year_of_care"]
                        )
                        data["gte_12yo_at_start_of_audit_year"].append(
                            row["is_gte_12yo"]
                        )

                        data["passed_yearly_checks"].append(row["num_passed"])
                        data["total_yearly_checks"].append(row["num_total"])

                        fields = [
                            "hba1c",
                            "bmi",
                            "thyroid_screen",
                            "blood_pressure",
                            "urinary_albumin",
                            "foot_exam",
                        ]

                        for field in fields:
                            status = measure_status(row[f"passed_{field}"])
                            data[field].append(status)

                        # Retinal screening uses string-based status
                        retinal = row["passed_retinal_screening"]
                        if retinal == "complete":
                            data["retinal_screening"].append("COMPLETE")
                        elif retinal == "not_required":
                            data["retinal_screening"].append("NA")
                        else:
                            data["retinal_screening"].append("")

                    case TableCategories.ADDITIONAL_CARE_PROCESSES:
                        data["complete_year_of_care"].append(
                            row["is_complete_year_of_care"]
                        )
                        data["gte_12yo_at_start_of_audit_year"].append(
                            row["is_gte_12yo"]
                        )

                        fields = [
                            "psychological_assessment",
                            "smoking_status",
                            "smoking_cessation_referral",
                            "additional_dietetic_appt_offered",
                            "pts_attending_additional_dietetic_appt",
                            "influenza_immunisation_recommended",
                            "sick_day_rules_advice",
                        ]

                        for field in fields:
                            data[field].append(measure_status(row[field]))

                    case TableCategories.CARE_AT_DIAGNOSIS:
                        data["diagnosis_date"].append(row["diagnosis_date"])

                        fields = [
                            "coeliac_disease_screening",
                            "thyroid_disease_screening",
                            "carbohydrate_counting_education",
                        ]

                        for field in fields:
                            data[field].append(measure_status(row[field]))

                    case TableCategories.ADMISSIONS:
                        data["complete_year_of_care"].append(
                            row["is_complete_year_of_care"]
                        )

                        data["mean_hba1c_mmolmol"].append(row["kpi_44_mean_hba1c"])
                        data["mean_hba1c_pct"].append(row["mean_hba1c_pct"])

                        data["median_hba1c_mmolmol"].append(row["kpi_45_median_hba1c"])
                        data["median_hba1c_pct"].append(row["median_hba1c_pct"])

                        for field in [
                            "number_of_admissions",
                            "number_of_dka_admissions",
                        ]:
                            data[field].append(row[field])

                    case TableCategories.TREATMENT:
                        for field in ["treatment_regimen", "glucose_monitoring", "hcl"]:
                            data[field].append(row[field])

                    case TableCategories.OUTCOMES:
                        data["complete_year_of_care"].append(
                            row["is_complete_year_of_care"]
                        )

                        fields = [
                            "latest_hba1c_mmol_mol",
                            "latest_hba1c_pct",
                            "previous_to_latest_hba1c_mmol_mol",
                            "previous_to_latest_hba1c_pct",
                            "latest_hba1c_date",
                            "previous_to_latest_hba1c_date",
                            "days_delta_between_latest_and_previous_hba1c",
                        ]

                        for field in fields:
                            data[field].append(row[field])

                        data["hba1c_percent_change"].append(row["hba1c_delta"])

            df = pd.DataFrame(data=data)

            df.to_excel(writer, sheet_name=category.value, index=False)

    timestamp = datetime.now().strftime("%y%m%d-%H%M")
    filename = f"{pdu.pz_code}-{audit_period.slug}-patient-report-{timestamp}.xlsx"

    return HttpResponse(
        contents.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
