# Python imports
import logging

# Django imports
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import render
from django.core.exceptions import ValidationError

# HTMX imports
from django_htmx.http import trigger_client_event

# RCPCH imports
from ..general_functions.csv_upload import csv_upload, read_csv
from ..general_functions.session import get_new_session_fields
from ..general_functions.view_preference import get_or_update_view_preference
from ..general_functions.csv_summarize import csv_summarize
from ..forms.upload import UploadFileForm
from .decorators import login_and_otp_required


# Logging
logger = logging.getLogger(__name__)


def error_list(wrapper_error: ValidationError):
    ret = []

    for field, errors in wrapper_error.error_dict.items():
        for error in errors:
            ret.append(
                {
                    "field": field,
                    "message": error.message,
                    "original_row_index": error.original_row_index,
                }
            )

    return ret


@login_and_otp_required()
def home(request):
    """
    Home page view - contains the upload form.
    Only verified users can access this page.
    """
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        file = request.FILES["csv_upload"]
        pz_code = request.session.get("pz_code")

        summary = csv_summarize(csv_file=file)

        # You can't read the same file twice without resetting it
        file.seek(0)
        errors = []

        try:
            csv_upload(
                user=request.user,
                dataframe=read_csv(file),
                pdu_pz_code=pz_code,
                csv_file=file
            )
            messages.success(request=request, message="File uploaded successfully")
        except ValidationError as error:
            errors = error_list(error)

        return render(
            request=request,
            template_name="home.html",
            context={
                "file_uploaded": True,
                "summary": summary,
                "form": form,
                "errors": errors,
            },
        )
    else:
        form = UploadFileForm()

    context = {"file_uploaded": False, "form": form}
    template = "home.html"
    return render(request=request, template_name=template, context=context)


def view_preference(request):
    """
    HTMX callback from the button press in the view_preference.html template.
    """

    view_preference_selection = request.POST.get("view_preference", None)
    view_preference = get_or_update_view_preference(
        request.user, view_preference_selection
    )
    pz_code = request.POST.get("pz_code_select_name", None)

    if pz_code is not None:
        new_session_fields = get_new_session_fields(
            user=request.user, pz_code=pz_code
        )  # includes a validation step
    else:
        new_session = request.session
        pz_code = new_session["pz_code"]
        new_session_fields = get_new_session_fields(
            request.user, pz_code
        )  # includes a validation step

    request.session.update(new_session_fields)
    context = {
        "view_preference": view_preference,
        "chosen_pdu": pz_code,
        "pdu_choices": request.session["pdu_choices"],
    }

    response = render(
        request, template_name="partials/view_preference.html", context=context
    )

    patients_list_view_url = reverse("patients")
    submissions_list_view_url = reverse("submissions")
    npdauser_list_view_url = reverse("npda_users")

    trigger_client_event(
        response=response,
        name="npda_users",
        params={"method": "GET", "url": npdauser_list_view_url},
    )  # reloads the npdauser table

    trigger_client_event(
        response=response,
        name="submissions",
        params={"method": "GET", "url": submissions_list_view_url},
    )  # reloads the submissions table

    trigger_client_event(
        response=response,
        name="patients",
        params={"method": "GET", "url": patients_list_view_url},
    )  # reloads the patients table
    return response
