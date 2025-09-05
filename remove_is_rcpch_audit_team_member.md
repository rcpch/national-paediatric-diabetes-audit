- Should we have a custom permission for "read/write data across all PDUs"?
    - That way Justin can have a different employer to RCPCH but can see everything
    - Potentially also a "r/w data across all audit periods?"
        - although all users can read data for historical audit periods, although it might not be visible in the switcher

organisations_adapter.py
    - is_superuser or is_rcpch_audit_team_member or is_rcpch_staff
        - Filtering list of PDUs for switcher
        - REPLACE: employer is RCPCH

session.py
    - is_rcpch_audit_team_member or is_superuser
        - Filtering audit periods for switcher
        - REPLACE: employer is RCPCH

view_preference.py
    - is_rcpch_audit_team_member
        - Setting view preference to national
        - REPLACE: employer is RCPCH

audit_period.py
    - user.is_superuser or user.is_rcpch_audit_team_member
        - Upload data to audit period (override)
        - REPLACE: employer is RCPCH or r/w across all PDUs

npda_tags.py
    - user.is_superuser or user.is_rcpch_staff or user.is_rcpch_audit_team_member
        - employer_match
            - 
        - exclude_admin_user_field
            - can remove now it's not in the form at all?
        - include_admin_users

mixins.py
    - request.user.is_superuser or request.user.is_rcpch_audit_team_member
        - CheckPDUListMixin
        - CheckPDUInstanceMixin
        - CheckCanCompleteQuestionnaireMixin
    - request.user.is_superuser and not request.user.is_rcpch_audit_team_member
        - CheckCurrentAuditYearMixin

NPDAUserCreateView
NPDAUserUpdateView


NPDAUserLogsListView
- as a fall through!!

submission.py
    - request.user.is_superuser or request.user.is_rcpch_audit_team_member
        - CSV upload