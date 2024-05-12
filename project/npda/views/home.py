from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django_otp.decorators import otp_required
from django.contrib import messages
from ..general_functions import csv_upload
from ..forms.upload import UploadFileForm
from ..models import Patient, Visit


@login_required
def home(request):
    if request.user.is_verified():
        file_uploaded = False
        if request.method == "POST":
            form = UploadFileForm(request.POST, request.FILES)
            file = request.FILES["csv_upload"]
            file_uploaded = csv_upload(csv_file=file)
            if file_uploaded["status"]==500:
                messages.error(request=request,message=f"{file_uploaded["errors"]}")
                return redirect('home')
        else:
            form = UploadFileForm()
        context = {"file_uploaded": file_uploaded, "form": form}
        template = "home.html"
        return render(request=request, template_name=template, context=context)
    else:
        return redirect(reverse("two_factor:profile"))
