from django.contrib.auth import urls as auth_urls
from django.contrib.auth.views import PasswordResetConfirmView
from django.urls import include, path

from project.npda.forms.npda_user_form import NPDAUpdatePasswordForm
from project.npda.views import (
    PatientListView,
    PatientVisitsListView,
    SubmissionsListView,
    VisitCreateView,
    VisitDeleteView,
    VisitUpdateView,
)
from project.npda.views.dashboard.dashboard import temp_set_eligible_kpi_7

from .views import *
from .views.dashboard import dashboard, partials
from .views.dashboard.patient_measurements import patient_measurements
from .views.patient_report import patient_report
from .views.dashboard.patient_characteristics import (
    patient_ages,
    all_patient_charts,
)

urlpatterns = [
    path("", view=home, name="home"),
    path("home", view=home, name="home"),
    path(
        "home/download_template",
        view=download_template,
        name="download_template",
    ),
    path("view_preference", view=view_preference, name="view_preference"),
    path("audit-year", view=audit_year, name="audit-year"),
    path("upload_csv", view=upload_csv, name="upload_csv"),
    path("upload_csv_in_progress", view=upload_csv_in_progress, name="upload-csv-in-progress"),
    path(
        "switch_paediatric_diabetes_unit",
        view=switch_paediatric_diabetes_unit,
        name="switch_paediatric_diabetes_unit",
    ),
    # Submission views
    path(
        "submissions",
        view=SubmissionsListView.as_view(),
        name="submissions",
    ),
    # Patient views
    path(
        "patients",
        view=PatientListView.as_view(),
        name="patients",
    ),
    path("patient/add/", PatientCreateView.as_view(), name="patient-add"),
    path(
        "patient/<int:pk>/update",
        PatientUpdateView.as_view(),
        name="patient-update",
    ),
    path(
        "patient/<int:pk>/delete",
        PatientDeleteView.as_view(),
        name="patient-delete",
    ),
    # Visit views
    path(
        "patient/<int:patient_id>/visits",
        view=PatientVisitsListView.as_view(),
        name="patient_visits",
    ),
    path(
        "patient/<int:patient_id>/visits/create",
        view=VisitCreateView.as_view(),
        name="visit-create",
    ),
    path(
        "patient/<int:patient_id>/visits/<int:pk>/update",
        view=VisitUpdateView.as_view(),
        name="visit-update",
    ),
    path(
        "patient/<int:patient_id>/visits/<int:pk>/delete",
        view=VisitDeleteView.as_view(),
        name="visit-delete",
    ),
    # NPDAUser views
    path("npda_users", view=NPDAUserListView.as_view(), name="npda_users"),
    path("npda_users/add", view=NPDAUserCreateView.as_view(), name="npdauser-create"),
    path(
        "npda_users/<int:npdauser_id>/logs",
        view=NPDAUserLogsListView.as_view(),
        name="npdauser-logs",
    ),
    path(
        "npda_users/<int:pk>/update",
        view=NPDAUserUpdateView.as_view(),
        name="npdauser-update",
    ),
    # Authentication -> NOTE: 2FA is implemented in project-level URLS with tf_urls
    path("captcha/", include("captcha.urls")),
    path("account/", include(auth_urls)),
    path(
        "account/password-reset/",
        view=ResetPasswordView.as_view(),
        name="password_reset",
    ),
    path(
        "account/password-reset-confirm/<uidb64>/<token>",
        view=PasswordResetConfirmView.as_view(
            form_class=NPDAUpdatePasswordForm,
            template_name="registration/password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    path("csrf_fail/", csrf_fail, name="csrf_fail"),
    # Debugging
    path("celery_test_task/", celery_test_task, name="celery_test_task"),
]

dashboard_urlpatterns = [
    path(
        "dashboard",
        view=dashboard.dashboard,
        name="dashboard",
    ),
    path(
        "get_metric_scatter_plot",
        view=partials.get_metric_scatter_plot,
        name="get_metric_scatter_plot",
    ),
    path(
        "get_map_chart_partial",
        view=partials.get_map_chart_partial,
        name="get_map_chart_partial",
    ),
    path(
        "get_new_diagnoses_partial",
        view=partials.get_new_diagnoses_partial,
        name="get_new_diagnoses_partial",
    ),
    path(
        "get_new_admissions_partial",
        view=partials.get_new_admissions_partial,
        name="get_new_admissions_partial",
    ),
    path(
        "get_transitioned_to_adult_service_partial",
        view=partials.get_transitioned_to_adult_service_partial,
        name="get_transitioned_to_adult_service_partial",
    ),
    path(
        "get_moved_out_of_area_partial",
        view=partials.get_moved_out_of_area_partial,
        name="get_moved_out_of_area_partial",
    ),
    path(
        "get_n_on_hcl_partial",
        view=partials.get_n_on_hcl_partial,
        name="get_n_on_hcl_partial",
    ),
    path(
        "get_pump_partial",
        view=partials.get_pump_partial,
        name="get_pump_partial",
    ),
    path(
        "get_cgm_partial",
        view=partials.get_cgm_partial,
        name="get_cgm_partial",
    ),
	path(
        "patient_ages",
        view=patient_ages,
        name="patient_ages",
    ),
    path(
        "all_patient_charts",
        view=all_patient_charts,
        name="all_patient_charts",
    ),
	path(
        "patient_measurements",
        view=patient_measurements,
        name="patient_measurements",
    ),
]

patient_report_urlpatterns = [
    path(
        "patient_report",
        view=patient_report.PatientReportView.as_view(),
        name="patient_report",
    ),
	path(
        "patient_table_partial",
        view=patient_report.PatientReportView.as_view(),
        name="patient_table_partial",
    ),
]

# Collate all URL patterns
urlpatterns += dashboard_urlpatterns
urlpatterns += patient_report_urlpatterns
