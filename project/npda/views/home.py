from django.shortcuts import get_object_or_404, redirect, render
from ..general_functions import csv_upload
from ..forms.upload import UploadFileForm
from ..models import Patient, Visit


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


def patients(request):
    template_name = "patients.html"
    patients = Patient.objects.all()
    context = {"patients": patients}
    return render(request=request, template_name=template_name, context=context)


def patient(request, patient_id):
    template_name = "patient.html"
    patient = Patient.objects.get(pk=patient_id)
    visits = Visit.objects.filter(patient=patient)
    context = {"visits": visits}
    return render(request=request, template_name=template_name, context=context)
