Don't change URLs at all to start - do it after (can be query params if easier code changes)


project.npda.general_functions.audit_period
    get_audit_period_for_date
        - TODO: check usage. still useful for tests, migrate to test folder
    get_quarters_for_audit_period


project.npda.general_functions.map
    get_children_by_pdu_audit_year
        - should take a submission instead, push up the audit filtering higher


project.npda.general_functions.session
    selected_audit_year

    get_submission_actions
        - filters submission: audit_year -> audit_period_id
    create_session_object
    refresh_session_filters
        - get_current_audit_year -> earliest open audit period


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