# Python imports
from datetime import date
from typing import Any, Iterable

# Django imports
from django.apps import apps
from django.contrib import messages
from django.db.models import Count, F, Value
from django.db.models.functions import Concat
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import ListView

# RCPCH imports
from ..general_functions import csv_upload, csv_summarise, retrieve_cohort_for_date
from .mixins import LoginAndOTPRequiredMixin


class AuditCohortsListView(LoginAndOTPRequiredMixin, ListView):
    """
    The AuditCohortsListView class.

    This class is used to display a list of audit cohorts.
    """

    model = apps.get_model(app_label="npda", model_name="AuditCohort")
    template_name = "audit_cohort_list.html"
    context_object_name = "auditcohorts"

    def get_queryset(self) -> Iterable[Any]:
        """
        Get the queryset for the view.

        :return: The queryset for the view
        """
        queryset = (
            self.model.objects.filter(
                pz_code=self.request.session.get("sibling_organisations").get(
                    "pz_code"
                ),
                ods_code=self.request.session.get("ods_code"),
            )
            .values(
                "submission_date", "pz_code", "ods_code", "cohort_number", "audit_year"
            )
            .annotate(
                patient_count=Count("patients"),
                submission_active=F("submission_active"),
                submission_by=Concat(
                    "submission_by__first_name", Value(" "), "submission_by__surname"
                ),
            )
            .order_by(
                "submission_date",
                "pz_code",
                "ods_code",
                "audit_year",
                "cohort_number",
                "submission_active",
            )
        )
        return queryset

    def get_context_data(self, **kwargs: Any) -> dict:
        """
        Get the context data for the view.

        :param kwargs: The keyword arguments
        :return: The context data for the view
        """
        context = super().get_context_data(**kwargs)
        context["pz_code"] = self.request.session.get("sibling_organisations").get(
            "pz_code"
        )
        return context

    def get(self, request, *args, **kwargs):
        """
        Handle the GET request.

        :param request: The request
        :param args: The arguments
        :param kwargs: The keyword arguments
        :return: The response
        """
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Handle the POST request.

        :param request: The request
        :param args: The arguments
        :param kwargs: The keyword arguments
        :return: The response
        """
        return super().post(request, *args, **kwargs)

    def render_to_response(self, context: dict) -> HttpResponse:
        """
        Render the response.

        :param context: The context
        :return: The response
        """
        return super().render_to_response(context)
