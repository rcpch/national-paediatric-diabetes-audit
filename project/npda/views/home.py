from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages

from ..general_functions import csv_upload
from ..forms.upload import UploadFileForm
from ..models import AuditCohort
from .decorators import login_and_otp_required


@login_and_otp_required()
def home(request):
    """
    Home page view - contains the upload form.
    Only verified users can access this page.
    """
    file_uploaded = False
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        file = request.FILES["csv_upload"]
        pz_code = request.session.get("sibling_organisations").get("pz_code")
        file_uploaded = csv_upload(user=request.user, csv_file=file, organisation_ods_code=request.user.organisation_employer, pdu_pz_code=pz_code)
        if file_uploaded["status"]==500:
            messages.error(request=request,message=f"{file_uploaded["errors"]}")
            return redirect('home')
        else:
            messages.success(request=request, message="File uploaded successfully")
            return render(request=request,template_name="home.html", context={"file_uploaded": file_uploaded, "form": form})
    else:
        form = UploadFileForm()
    context = {"file_uploaded": file_uploaded, "form": form}
    template = "home.html"
    return render(request=request, template_name=template, context=context)
