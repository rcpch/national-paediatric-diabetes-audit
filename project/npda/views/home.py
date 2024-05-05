from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from ..general_functions import csv_upload
from ..forms.upload import UploadFileForm
from ..models import Patient, Visit


@login_required
def home(request):
    file_uploaded = False
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        file = request.FILES["csv_upload"]
        file_uploaded, errors = csv_upload(csv_file=file)
        print(f"Valid file {file_uploaded}")
    else:
        form = UploadFileForm()

    context = {"file_uploaded": file_uploaded, "form": form}
    template = "home.html"
    return render(request=request, template_name=template, context=context)
