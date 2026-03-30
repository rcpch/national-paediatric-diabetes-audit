# Expose partials here
from project.npda.views.dashboard.partials import (
    get_cgm_partial,
    get_map_chart_partial,
    get_metric_scatter_plot,
    get_moved_out_of_area_partial,
    get_n_on_hcl_partial,
    get_new_admissions_partial,
    get_new_diagnoses_partial,
    get_pump_partial,
    get_selected_chart_data,
    get_transitioned_to_adult_service_partial,
)

# Dashboard view
from .dashboard.dashboard import dashboard as dashboard
from .errors import csrf_fail, error_400, error_403, error_404, error_500
from .home import (
    run_test_task,
    download_template,
    feature_flags,
    home,
    index,
    new_home,
)
from .npda_users import (
    NPDAUserCreateView,
    NPDAUserListView,
    NPDAUserLogsListView,
    NPDAUserUpdateView,
    RCPCHLoginView,
    ResetPasswordView,
    get_user_home_page,
    npdauser_pdu_update,
)
from .patient import (
    PatientCreateView,
    PatientDeleteView,
    PatientListView,
    PatientUpdateView,
)
from .submissions import SubmissionsListView, upload_csv, upload_csv_in_progress
from .visit import (
    PatientVisitsListView,
    VisitCreateView,
    VisitDeleteView,
    VisitUpdateView,
)
