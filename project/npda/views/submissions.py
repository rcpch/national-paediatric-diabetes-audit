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
from ..general_functions import download_csv


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
        PaediatricDiabetesUnit = apps.get_model(
            app_label="npda", model_name="PaediatricDiabetesUnit"
        )
        pdu = PaediatricDiabetesUnit.objects.get(
            pz_code=self.request.session.get("pz_code"),
        )
        queryset = (
            self.model.objects.filter(paediatric_diabetes_unit=pdu)
            .values("submission_date", "audit_year")
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
                "audit_year",
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
        Handle the HTMX GET request.
        """
        self.object_list = self.get_queryset()
        context = self.get_context_data(object_list=self.object_list)
        template = self.template_name
        if request.htmx:
            # If the request is an HTMX request from the PDU selector, returns the partial template
            template = "partials/submission_history.html"
        return render(request=request, template_name=template, context=context)

    def post(self, request, *args, **kwargs):
        """
        Handle the HTMX POST request.
        The button name "submit-data" is used to determine the action to be taken.
        If the value of "submit-data" is "delete-data", the submission is deleted.
        If the value of "submit-data" is "download-data", the original csv is downloaded.
        """
        button_name = request.POST.get("submit-data")
        if button_name == "delete-data":
            # retrieve the  submission instance
            submission = Submission.objects.filter(
                pk=request.POST.get("audit_id")
            ).get()

            # check if the submission is active - if so, do not allow deletion, and return an error message
            if submission.submission_active:
                self.object_list = self.get_queryset()
                context = self.get_context_data(object_list=self.object_list)
                messages.error(
                    request,
                    "Cannot delete an active submission. Please make another submission active before deleting this one",
                )
                return render(request, self.template_name, context=context)

            # delete the patients associated with the submission
            submission.patients.all().delete()
            # then delete the submission itself
            submission.delete()

            # set the submission_active flag to True for the most recent submission
            if Submission.objects.count() > 0:
                new_first = Submission.objects.order_by("-submission_date").first()
                new_first.submission_active = True
                new_first.save()
            messages.success(request, "Cohort submission deleted successfully")

        if button_name == "download-data":
            submission = Submission.objects.filter(
                pk=request.POST.get("audit_id")
            ).get()
            return download_csv(request, submission.id)

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
