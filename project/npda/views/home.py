# Python imports
from datetime import date

# Django imports
from django.apps import apps
from django.contrib import messages
from django.db.models import Count, F
from django.shortcuts import redirect, render
from django.urls import reverse

# RCPCH imports
from ..general_functions import csv_upload, csv_summarise, retrieve_cohort_for_date
from ..forms.upload import UploadFileForm
from .decorators import login_and_otp_required

@login_and_otp_required()
def home(request):
    """
    Home page view - contains the upload form.
    Only verified users can access this page.
    """
    file_uploaded = False
    AuditCohort = apps.get_model(app_label='npda', model_name='AuditCohort')
    auditcohort = AuditCohort.objects.filter(
        pz_code=request.session.get("sibling_organisations").get("pz_code"),
        ods_code=request.session.get('ods_code')
    ).values(
        'submission_date', 'pz_code', 'ods_code', 'cohort_number', 'audit_year'
    ).annotate(
        patient_count=Count('id'),
        submission_active=F('submission_active'),
        submission_by=F('submission_by'),
    ).order_by('submission_date', 'pz_code', 'ods_code', 'audit_year', 'cohort_number', 'submission_active')

    if request.method == "POST":
        button_name = request.POST.get('submit-data')
        if button_name == "submit-data":
            AuditCohort.objects.filter(audit_year=date.today().year, cohort_number=retrieve_cohort_for_date(date_instance=date.today()), pz_code=request.session.get("sibling_organisations").get("pz_code"),ods_code=request.session.get('ods_code')).update(user_confirmed=True, submission_active=True)
            messages.success(request=request, message="File uploaded successfully")
            return redirect(reverse('patients'))
        elif button_name == "overwrite-data":
            AuditCohort = apps.get_model(app_label='npda', model_name='AuditCohort')
            AuditCohort.objects.filter(user_confirmed=True, audit_year=date.today().year, cohort_number=retrieve_cohort_for_date(date_instance=date.today()), pz_code=request.session.get("sibling_organisations").get("pz_code"),ods_code=request.session.get('ods_code')).update(submission_active=False, user_confirmed=True)
            AuditCohort.objects.filter(user_confirmed=False, audit_year=date.today().year, cohort_number=retrieve_cohort_for_date(date_instance=date.today()), pz_code=request.session.get("sibling_organisations").get("pz_code"),ods_code=request.session.get('ods_code')).update(submission_active=True, user_confirmed=True)
            messages.success(request=request, message="File uploaded successfully")
            return redirect(reverse('patients'))
        elif button_name == "view-data":
            AuditCohort.objects.filter(user_confirmed=False, audit_year=date.today().year, cohort_number=retrieve_cohort_for_date(date_instance=date.today()), pz_code=request.session.get("sibling_organisations").get("pz_code"),ods_code=request.session.get('ods_code')).update(user_confirmed=True)
            return redirect(reverse('patients'))
        form = UploadFileForm(request.POST, request.FILES)
        file = request.FILES["csv_upload"]
        pz_code = request.session.get("sibling_organisations").get("pz_code")
        summary = csv_summarise(csv_file=file)
        file_uploaded = csv_upload(user=request.user, csv_file=file, organisation_ods_code=request.user.organisation_employer, pdu_pz_code=pz_code)
        if file_uploaded["status"]==422:
            messages.error(request=request,message=f"{file_uploaded["errors"]}")
            return redirect('home')
        else:
            messages.success(request=request, message="File uploaded successfully")
            return render(request=request,template_name="home.html", context={"file_uploaded": file_uploaded, "summary": summary, "form": form, "auditcohort": auditcohort})
    else:
        form = UploadFileForm()
    
    context = {"file_uploaded": file_uploaded, "form": form, "auditcohort": auditcohort}
    template = "home.html"
    return render(request=request, template_name=template, context=context)
