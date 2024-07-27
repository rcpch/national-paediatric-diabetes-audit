# Python imports
from typing import Any, Iterable

# Django imports
from django.apps import apps
from django.contrib import messages
from django.db.models import Count, F, Value
from django.db.models.functions import Concat
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import ListView

# RCPCH imports
from .mixins import LoginAndOTPRequiredMixin
from ..models import Submission


class SubmissionsListView(LoginAndOTPRequiredMixin, ListView):
    """
    The SubmissionsListView class.

    This class is used to display a list of submissions.
    """

    model = apps.get_model(app_label="npda", model_name="Submission")
    template_name = "submissions_list.html"
    context_object_name = "Submissions"

    def get_queryset(self) -> Iterable[Any]:
        """
        Get the queryset for the view.

        :return: The queryset for the view
        """
        queryset = (
            self.model.objects.filter(
                pz_code=self.request.session.get("pz_code"),
                ods_code=self.request.session.get("ods_code"),
            )
            .values("submission_date", "pz_code", "ods_code", "quarter", "audit_year")
            .annotate(
                patient_count=Count("patients"),
                submission_active=F("submission_active"),
                submission_by=Concat(
                    "submission_by__first_name", Value(" "), "submission_by__surname"
                ),
                pk=F("id"),
            )
            .order_by(
                "-submission_date",
                "pz_code",
                "ods_code",
                "audit_year",
                "quarter",
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
        context["pz_code"] = self.request.session.get("pz_code")
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
        :return: the updated table data
        """
        button_name = request.POST.get("submit-data")
        if button_name == "delete-data":

            # delete the cohort submission patients
            submission = Submission.objects.filter(
                pk=request.POST.get("audit_id")
            ).get()
            submission.patients.all().delete()
            # then delete the cohort submission itself
            submission.delete()
            # set the submission_active flag to True for the most recent submission
            if Submission.objects.count() > 0:
                new_first = Submission.objects.order_by("-submission_date").first()
                new_first.submission_active = True
                new_first.save()
            messages.success(request, "Cohort submission deleted successfully")
        # POST is not supported for this view
        # Must therefore return the queryset as an obect_list and context
        self.object_list = self.get_queryset()
        context = self.get_context_data(object_list=self.object_list)
        return render(request, self.template_name, context=context)

    def render_to_response(self, context: dict) -> HttpResponse:
        """
        Render the response.

        :param context: The context
        :return: The response
        """
        return super().render_to_response(context)
