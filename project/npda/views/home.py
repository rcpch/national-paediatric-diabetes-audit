# Python imports
from datetime import date
from typing import Any, Iterable
import logging

# Django imports
from django.apps import apps
from django.contrib import messages
from django.db.models import Count, F
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import ListView

from asgiref.sync import async_to_sync, sync_to_async

# RCPCH imports
from ..general_functions import csv_upload, csv_summarise
from ..forms.upload import UploadFileForm
from .decorators import login_and_otp_required


# Logging
logger = logging.getLogger(__name__)


@sync_to_async
@login_and_otp_required()
@async_to_sync
async def home(request):
    """
    Home page view - contains the upload form.
    Only verified users can access this page.
    """
    file_uploaded = False

    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        file = request.FILES["csv_upload"]
        pz_code = request.session.get("pz_code")
        
        summary = await csv_summarise(csv_file=file)

        # You can't read the same file twice without resetting it
        file.seek(0)
        
        organisation = await request.user.organisation_employers.afirst()
        file_uploaded = await csv_upload(user=request.user, csv_file=file, organisation_ods_code=organisation.ods_code, pdu_pz_code=pz_code)

        if file_uploaded["status"]==422 or file_uploaded["status"]==500:
            messages.error(request=request,message=f"{file_uploaded["errors"]}")
            return redirect('home')
        else:
            messages.success(request=request, message="File uploaded successfully")
            return render(request=request,template_name="home.html", context={"file_uploaded": file_uploaded, "summary": summary, "form": form})
    else:
        form = UploadFileForm()
    
    context = {"file_uploaded": file_uploaded, "form": form}
    template = "home.html"
    return render(request=request, template_name=template, context=context)
