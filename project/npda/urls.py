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
    npdauser_pdu_update
)

from .views import *
from .views.dashboard import dashboard, partials
from .views.dashboard.patient_measurements import patient_measurements
from .views.patient_report import patient_report
from .views.dashboard.patient_characteristics import (
    patient_ages,
    all_patient_charts,
)

data_prefix = "period/<str:audit_period>/pdu/<str:pz_code>"

urlpatterns = [
    path("", view=index, name="index"),
    path("home", view=home, name="home"),
    path("period/<str:audit_period>", view=new_home, name="new-home"),
    path(
        f"{data_prefix}/home/download_template",
        view=download_template,
        name="pdu-download-template",
    ),
    path("view_preference", view=view_preference, name="view_preference"),
    path("audit-year", view=audit_year, name="audit-year"),
    path(f"{data_prefix}/upload_csv", view=upload_csv, name="pdu-upload-csv"),
    path(f"{data_prefix}/upload_csv_in_progress", view=upload_csv_in_progress, name="pdu-upload-csv-in-progress"),
    path("feature_flags", view=feature_flags, name="feature-flags"),
    path(
        f"{data_prefix}/submissions",
        view=SubmissionsListView.as_view(),
        name="pdu-submissions",
    ),
    # Patient views
    path(
        f"{data_prefix}/patients",
        view=PatientListView.as_view(),
        name="pdu-patients",
    ),
    path(f"{data_prefix}/patient/add/", PatientCreateView.as_view(), name="pdu-patient-add"),
    path(
        f"{data_prefix}/patient/<int:pk>/update",
        PatientUpdateView.as_view(),
        name="pdu-patient-update",
    ),
    path(
        f"{data_prefix}/patient/<int:pk>/delete",
        PatientDeleteView.as_view(),
        name="pdu-patient-delete",
    ),
    # Visit views
    path(
        f"{data_prefix}/patient/<int:patient_id>/visits",
        view=PatientVisitsListView.as_view(),
        name="pdu-patient-visits",
    ),
    path(
        f"{data_prefix}/patient/<int:patient_id>/visits/create",
        view=VisitCreateView.as_view(),
        name="pdu-visit-create",
    ),
    path(
        f"{data_prefix}/patient/<int:patient_id>/visits/<int:pk>/update",
        view=VisitUpdateView.as_view(),
        name="pdu-visit-update",
    ),
    path(
        f"{data_prefix}/patient/<int:patient_id>/visits/<int:pk>/delete",
        view=VisitDeleteView.as_view(),
        name="pdu-visit-delete",
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
    path(
        "npda_users/<int:pk>/pdu_update",
        view=npdauser_pdu_update,
        name="npdauser-pdu-update",
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
        f"{data_prefix}/dashboard",
        view=dashboard.dashboard,
        name="pdu-dashboard",
    ),
    path(
        f"{data_prefix}/get_metric_scatter_plot",
        view=partials.get_metric_scatter_plot,
        name="pdu-get-metric-scatter-plot",
    ),
    path(
        f"{data_prefix}/get_map_chart_partial",
        view=partials.get_map_chart_partial,
        name="pdu-get-map-chart-partial",
    ),
    path(
        f"{data_prefix}/get_new_diagnoses_partial",
        view=partials.get_new_diagnoses_partial,
        name="pdu-get-new-diagnoses-partial",
    ),
    path(
        f"{data_prefix}/get_new_admissions_partial",
        view=partials.get_new_admissions_partial,
        name="pdu-get-new-admissions-partial",
    ),
    path(
        f"{data_prefix}/get_transitioned_to_adult_service_partial",
        view=partials.get_transitioned_to_adult_service_partial,
        name="pdu-get-transitioned-to-adult-service-partial",
    ),
    path(
        f"{data_prefix}/get_moved_out_of_area_partial",
        view=partials.get_moved_out_of_area_partial,
        name="pdu-get-moved-out-of-area-partial",
    ),
    path(
        f"{data_prefix}/get_n_on_hcl_partial",
        view=partials.get_n_on_hcl_partial,
        name="pdu-get-n-on-hcl-partial",
    ),
    path(
        f"{data_prefix}/get_pump_partial",
        view=partials.get_pump_partial,
        name="pdu-get-pump-partial",
    ),
    path(
        f"{data_prefix}/get_cgm_partial",
        view=partials.get_cgm_partial,
        name="pdu-get-cgm-partial",
    ),
    path(
        f"{data_prefix}/patient_ages",
        view=patient_ages,
        name="pdu-patient-ages",
    ),
    path(
        f"{data_prefix}/all_patient_charts",
        view=all_patient_charts,
        name="pdu-all-patient-charts",
    ),
    path(
        f"{data_prefix}/patient_measurements",
        view=patient_measurements,
        name="pdu-patient-measurements",
    ),
]

patient_report_urlpatterns = [
    path(
        f"{data_prefix}/patient_report",
        view=patient_report.PatientReportView.as_view(),
        name="pdu-patient-report",
    ),
    path(
        f"{data_prefix}/patient_table_partial",
        view=patient_report.PatientReportView.as_view(),
        name="pdu-patient-table-partial",
    ),
    path(
        f"{data_prefix}/patient_report/download",
        view=patient_report.download_patient_report,
        name="pdu-patient-report-download"
    )
]

# Collate all URL patterns
urlpatterns += dashboard_urlpatterns
urlpatterns += patient_report_urlpatterns
