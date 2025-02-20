Don't change URLs at all to start - do it after (can be query params if easier code changes)

project.npda.context_processors
    session_data
        - requested_audit_year -> audit period id
        - audit_years -> all audit periods
            (do we need a visibility flag too? for testing new and old audit years)
    can_alter_this_audit_year_submission
        - get_current_audit_year -> audit_period.open


project.npda.general_functions.audit_period
    SUPPORTED_AUDIT_YEARS -> all audit periods
    get_audit_period_for_date
        - TODO: check usage. still useful for tests, migrate to test folder
    get_current_audit_year
        - TODO: check usage, should come from requested audit period
    get_quarters_for_audit_period
    get_quarter_for_visit
        - probably don't need to change, TODO: check usage anyway though


project.npda.general_functions.map
    get_children_by_pdu_audit_year
        - should take a submission instead, push up the audit filtering higher


project.npda.general_functions.quarter_for_date
    retrieve_quarter_for_date
        - TODO: dupe of get_quarter_for_visit


project.npda.general_functions.session
    get_submission_actions
        - filters submission: audit_year -> audit_period_id
    create_session_object
    refresh_session_filters
        - get_current_audit_year -> earliest open audit period
        - SUPPORTED_AUDIT_YEARS -> all audit periods


project.npda.general_functions.csv_upload
    csv_upload
        - audit_year -> audit_period_id


project.npda.models.patient
    Patient.is_in_transfer_in_the_last_year
        - TODO: needs the audit period passing in from above, consider becoming a method on AuditPeriod?


project.npda.models.patientsubmissions
    PatientSubmission.save
        - submission__audit_year -> submission__audit_period


project.npda.models.submission
    - audit_year -> audit_period ref


project.npda.views.home
    - audit_year -> audit_period
    - calls down into the session functions


project.npda.views.mixins
    - CheckCurrentAuditYearMixin
        - check audit period open