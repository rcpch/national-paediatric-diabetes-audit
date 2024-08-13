# Python imports
import logging

# Django imports
from django.contrib import messages
from django.shortcuts import render
from django.core.exceptions import ValidationError

# RCPCH imports
from ..general_functions.csv_upload import csv_upload, csv_summarise
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

        summary = csv_summarise(csv_file=file)

        # You can't read the same file twice without resetting it
        file.seek(0)
        print(file.name, file.size)
        errors = []

        try:
            csv_upload(
                user=request.user,
                csv_file=file,
                organisation_ods_code=request.user.organisation_employers.first().ods_code,
                pdu_pz_code=pz_code,
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
