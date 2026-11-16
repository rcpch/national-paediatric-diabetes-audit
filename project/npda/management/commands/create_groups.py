from django.contrib.auth.management import create_permissions
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from project.npda.models import (
    AuditPeriod,
    Banner,
    NPDAUser,
    PaediatricDiabetesUnit,
    Patient,
    Submission,
    Transfer,
    Visit,
)

from ....constants import (  # group names; custom permissions
    CAN_ACCESS_ALL_PDUS,
    CAN_ALLOCATE_NPDA_LEAD_CENTRE,
    CAN_ASSIGN_RCPCH_AUDIT_TEAM_ROLE,
    CAN_CONSENT_TO_AUDIT_PARTICIPATION,
    CAN_DELETE_NPDA_LEAD_CENTRE,
    CAN_EDIT_CLOSED_AUDIT_PERIODS,
    CAN_EDIT_NPDA_LEAD_CENTRE,
    CAN_LOCK_CHILD_PATIENT_DATA_FROM_EDITING,
    CAN_MANAGE_INACTIVE_PDUS,
    CAN_MANAGE_USERS_IN_ANY_PDU,
    CAN_OPT_OUT_CHILD_FROM_INCLUSION_IN_AUDIT,
    CAN_OVERRIDE_DATA_UPLOAD_RULES,
    CAN_PREVIEW_FEATURES,
    CAN_RESET_USER_TWO_FACTOR,
    CAN_TRANSFER_NPDA_LEAD_CENTRE,
    CAN_UNLOCK_CHILD_PATIENT_DATA_FROM_EDITING,
    CAN_VIEW_HIDDEN_AUDIT_PERIODS,
    GROUPS,
    NPDA_AUDIT_TEAM_FULL_ACCESS,
    PATIENT_ACCESS,
    TRUST_AUDIT_TEAM_COORDINATOR_ACCESS,
    TRUST_AUDIT_TEAM_EDIT_ACCESS,
    TRUST_AUDIT_TEAM_VIEW_ONLY,
)


def groups_seeder(
    run_create_groups=False, add_permissions_to_existing_groups=False, verbose=True
):
    patientContentType = ContentType.objects.get_for_model(Patient)
    visitContentType = ContentType.objects.get_for_model(Visit)
    npdauserContentType = ContentType.objects.get_for_model(NPDAUser)
    transferContentType = ContentType.objects.get_for_model(Transfer)
    submissionContentType = ContentType.objects.get_for_model(Submission)
    pduContentType = ContentType.objects.get_for_model(PaediatricDiabetesUnit)
    auditPeriodContentType = ContentType.objects.get_for_model(AuditPeriod)
    bannerContentType = ContentType.objects.get_for_model(Banner)

    """
    Note view permissions include viewing users, but not creating, updating or deleting them
    View permissions include viewing but NOT updating or deleting case audit records

    NOTE Additional constraints are applied in view decorators to prevent users accessing
    records of users or children in organisations other than their own
    """

    COORDINATOR_PERMISSIONS = [
        # patient-related permissions
        {"codename": "view_patient", "content_type": patientContentType},
        {"codename": "change_patient", "content_type": patientContentType},
        {"codename": "add_patient", "content_type": patientContentType},
        # visit-related permissions
        {"codename": "view_visit", "content_type": visitContentType},
        {"codename": "change_visit", "content_type": visitContentType},
        {"codename": "add_visit", "content_type": visitContentType},
        # transfer-related permissions = None
        # NPDA-user related permissions
        {"codename": "view_npdauser", "content_type": npdauserContentType},
        {"codename": "change_npdauser", "content_type": npdauserContentType},
        {"codename": "add_npdauser", "content_type": npdauserContentType},
        {"codename": "delete_npdauser", "content_type": npdauserContentType},
        # submission
        {"codename": "view_submission", "content_type": submissionContentType},
    ]

    READER_PERMISSIONS = [
        # patient-related permissions
        {"codename": "view_patient", "content_type": patientContentType},
        # visit-related permissions
        {"codename": "view_visit", "content_type": visitContentType},
        # transfer-related permissions
        {"codename": "view_transfer", "content_type": transferContentType},
        # NPDA-user related permissions
        {"codename": "view_npdauser", "content_type": npdauserContentType},
        # submission
        {"codename": "view_submission", "content_type": submissionContentType},
    ]

    EDITOR_PERMISSIONS = [
        # patient-related permissions
        {"codename": "view_patient", "content_type": patientContentType},
        {"codename": "change_patient", "content_type": patientContentType},
        {"codename": "add_patient", "content_type": patientContentType},
        # visit-related permissions
        {"codename": "view_visit", "content_type": visitContentType},
        {"codename": "change_visit", "content_type": visitContentType},
        {"codename": "add_visit", "content_type": visitContentType},
        # transfer-related permissions = None
        # user-related permissions
        {"codename": "view_npdauser", "content_type": npdauserContentType},
        # submission
        {"codename": "view_submission", "content_type": submissionContentType},
    ]

    RCPCH_AUDIT_TEAM_PERMISSIONS = [
        # patient-related permissions
        {"codename": "view_patient", "content_type": patientContentType},
        {"codename": "change_patient", "content_type": patientContentType},
        {"codename": "add_patient", "content_type": patientContentType},
        {"codename": "delete_patient", "content_type": patientContentType},
        # visit-related permissions
        {"codename": "view_visit", "content_type": visitContentType},
        # visit-related permissions
        {"codename": "view_visit", "content_type": visitContentType},
        {"codename": "change_visit", "content_type": visitContentType},
        {"codename": "add_visit", "content_type": visitContentType},
        {"codename": "delete_visit", "content_type": visitContentType},
        # transfer-related permissions
        {"codename": "view_transfer", "content_type": transferContentType},
        # transfer-related permissions
        {"codename": "view_transfer", "content_type": transferContentType},
        {"codename": "change_transfer", "content_type": transferContentType},
        {"codename": "add_transfer", "content_type": transferContentType},
        {"codename": "delete_transfer", "content_type": transferContentType},
        # NPDA-user related permissions
        {"codename": "view_npdauser", "content_type": npdauserContentType},
        {"codename": "change_npdauser", "content_type": npdauserContentType},
        {"codename": "add_npdauser", "content_type": npdauserContentType},
        {"codename": "delete_npdauser", "content_type": npdauserContentType},
        # Submission
        {"codename": "view_submission", "content_type": submissionContentType},
        {"codename": "change_submission", "content_type": submissionContentType},
        {"codename": "add_submission", "content_type": submissionContentType},
        {"codename": "delete_submission", "content_type": submissionContentType},
    ]

    PATIENT_PERMISSIONS = [
        {"codename": "view_patient", "content_type": patientContentType},
    ]

    EDITOR_CUSTOM_PERMISSIONS = [
        # custom
        {
            "codename": CAN_OPT_OUT_CHILD_FROM_INCLUSION_IN_AUDIT[0],
            "content_type": patientContentType,
        },
        {
            "codename": CAN_LOCK_CHILD_PATIENT_DATA_FROM_EDITING[0],
            "content_type": patientContentType,
        },
        {
            "codename": CAN_UNLOCK_CHILD_PATIENT_DATA_FROM_EDITING[0],
            "content_type": patientContentType,
        },
        {
            "codename": CAN_ALLOCATE_NPDA_LEAD_CENTRE[0],
            "content_type": transferContentType,
        },
        {"codename": "can_submit_csv", "content_type": npdauserContentType},
        {"codename": "can_download_csv", "content_type": npdauserContentType},
    ]

    """
    Full access inherit all editor permissions
    - transfer to another lead NPDA centre

    NOTE Additional constraints are applied in view decorators to prevent users accessing
    records of users or children in organisations other than their own
    """

    FULL_ACCESS_CUSTOM_PERMISSIONS = [
        # npda user
        {
            "codename": CAN_DELETE_NPDA_LEAD_CENTRE[0],
            "content_type": transferContentType,
        },
        {
            "codename": CAN_EDIT_NPDA_LEAD_CENTRE[0],
            "content_type": transferContentType,
        },
        {
            "codename": CAN_TRANSFER_NPDA_LEAD_CENTRE[0],
            "content_type": transferContentType,
        },
        {"codename": "can_submit_csv", "content_type": npdauserContentType},
        {"codename": "can_download_csv", "content_type": npdauserContentType},
    ]

    """
    Replace the is_rcpch_audit_team_member / is_rcpch_staff flags.
    Only the RCPCH audit team group may hold these.
    See documentation/docs/developer/rcpch-flags-retirement-plan.md
    """
    RCPCH_AUDIT_TEAM_ONLY_PERMISSIONS = [
        {"codename": CAN_ACCESS_ALL_PDUS[0], "content_type": pduContentType},
        {"codename": CAN_MANAGE_INACTIVE_PDUS[0], "content_type": pduContentType},
        {
            "codename": CAN_VIEW_HIDDEN_AUDIT_PERIODS[0],
            "content_type": auditPeriodContentType,
        },
        {
            "codename": CAN_EDIT_CLOSED_AUDIT_PERIODS[0],
            "content_type": auditPeriodContentType,
        },
        {
            "codename": CAN_OVERRIDE_DATA_UPLOAD_RULES[0],
            "content_type": submissionContentType,
        },
        {
            "codename": CAN_MANAGE_USERS_IN_ANY_PDU[0],
            "content_type": npdauserContentType,
        },
        {
            "codename": CAN_ASSIGN_RCPCH_AUDIT_TEAM_ROLE[0],
            "content_type": npdauserContentType,
        },
        {
            "codename": CAN_RESET_USER_TWO_FACTOR[0],
            "content_type": npdauserContentType,
        },
        {"codename": CAN_PREVIEW_FEATURES[0], "content_type": npdauserContentType},
        # built-in: see banners targeted at any role, to check how they look
        {"codename": "view_banner", "content_type": bannerContentType},
    ]

    COORDINATOR_CUSTOM_PERMISSIONS = [
        {
            "codename": CAN_TRANSFER_NPDA_LEAD_CENTRE[0],
            "content_type": transferContentType,
        }
    ]

    PATIENT_ACCESS_PERMISSIONS = [
        # currently not used
        {
            "codename": CAN_CONSENT_TO_AUDIT_PARTICIPATION[0],
            "content_type": npdauserContentType,
        },
    ]

    def initialize_permissions(apps, schema_editor):
        """
        This function is run in migrations/0002_create_groups.py as an initial
        data migration at project initialization. it sets up some basic model-level
        permissions for different groups when the project is initialised.

        6 groups. Loop through and add custom
        """

        # Permissions have to be created before applying them
        for app_config in apps.get_app_configs(apps, schema_editor):
            app_config.models_module = True
            create_permissions(app_config, verbosity=0)
            app_config.models_module = None

    def add_permissions_to_group(permissions_list, group_to_add):
        for permission in permissions_list:
            codename = permission.get("codename")
            content_type = permission.get("content_type")
            newPermission = Permission.objects.get(
                codename=codename, content_type=content_type
            )
            if group_to_add.permissions.filter(codename=codename).exists():
                if verbose:
                    print(f"{codename} already exists for this group. Skipping...")
            else:
                if verbose:
                    print(f"...Adding {codename}")
                group_to_add.permissions.add(newPermission)

    if add_permissions_to_existing_groups:
        for group in GROUPS:
            if verbose:
                print(f"...adding permissions to {group}...")
            # add permissions to group
            newGroup = Group.objects.filter(name=group).get()

            # NPDA_AUDIT_TEAM_FULL_ACCESS = RCPCH AUDIT TEAM
            if group == NPDA_AUDIT_TEAM_FULL_ACCESS:
                # basic permissions
                add_permissions_to_group(RCPCH_AUDIT_TEAM_PERMISSIONS, newGroup)
                add_permissions_to_group(EDITOR_CUSTOM_PERMISSIONS, newGroup)
                add_permissions_to_group(FULL_ACCESS_CUSTOM_PERMISSIONS, newGroup)
                add_permissions_to_group(RCPCH_AUDIT_TEAM_ONLY_PERMISSIONS, newGroup)

            # TRUST_AUDIT_TEAM_VIEW_ONLY = READER
            elif group == TRUST_AUDIT_TEAM_VIEW_ONLY:
                # basic permissions
                add_permissions_to_group(READER_PERMISSIONS, newGroup)

            # TRUST_AUDIT_TEAM_EDIT_ACCESS = EDITOR
            elif group == TRUST_AUDIT_TEAM_EDIT_ACCESS:
                # basic permissions
                add_permissions_to_group(EDITOR_PERMISSIONS, newGroup)
                add_permissions_to_group(EDITOR_CUSTOM_PERMISSIONS, newGroup)

            # TRUST_AUDIT_TEAM_COORDINATOR_ACCESS = COORDINATOR
            elif group == TRUST_AUDIT_TEAM_COORDINATOR_ACCESS:
                # basic permissions
                add_permissions_to_group(COORDINATOR_PERMISSIONS, newGroup)
                add_permissions_to_group(COORDINATOR_CUSTOM_PERMISSIONS, newGroup)
                add_permissions_to_group(EDITOR_CUSTOM_PERMISSIONS, newGroup)

            elif group == PATIENT_ACCESS:
                # custom permissions
                add_permissions_to_group(PATIENT_ACCESS_PERMISSIONS, newGroup)
                # basic permissions
                add_permissions_to_group(PATIENT_PERMISSIONS, newGroup)
                add_permissions_to_group(PATIENT_PERMISSIONS, newGroup)

            else:
                if verbose:
                    print("Error: group does not exist!")

    if run_create_groups:
        for group in GROUPS:
            if not Group.objects.filter(name=group).exists():
                if verbose:
                    print(f"...creating group: {group}")
                try:
                    newGroup = Group.objects.create(name=group)
                except Exception as error:
                    if verbose:
                        print(error)
                    error = True

                if verbose:
                    print(f"...adding permissions to {group}...")
                # add permissions to group

                # NPDA_AUDIT_TEAM_FULL_ACCESS = RCPCH AUDIT TEAM
                if group == NPDA_AUDIT_TEAM_FULL_ACCESS:
                    # basic permissions
                    add_permissions_to_group(RCPCH_AUDIT_TEAM_PERMISSIONS, newGroup)
                    add_permissions_to_group(EDITOR_CUSTOM_PERMISSIONS, newGroup)
                    add_permissions_to_group(FULL_ACCESS_CUSTOM_PERMISSIONS, newGroup)
                    add_permissions_to_group(
                        RCPCH_AUDIT_TEAM_ONLY_PERMISSIONS, newGroup
                    )

                # TRUST_AUDIT_TEAM_VIEW_ONLY = VIEWER
                elif group == TRUST_AUDIT_TEAM_VIEW_ONLY:
                    # basic permissions
                    add_permissions_to_group(READER_PERMISSIONS, newGroup)

                # TRUST_AUDIT_TEAM_EDIT_ACCESS = EDITOR
                elif group == TRUST_AUDIT_TEAM_EDIT_ACCESS:
                    # basic permissions
                    add_permissions_to_group(EDITOR_PERMISSIONS, newGroup)
                    add_permissions_to_group(EDITOR_CUSTOM_PERMISSIONS, newGroup)

                # TRUST_AUDIT_TEAM_COORDINATOR_ACCESS = COORDINATOR
                elif group == TRUST_AUDIT_TEAM_COORDINATOR_ACCESS:
                    # basic permissions
                    add_permissions_to_group(COORDINATOR_PERMISSIONS, newGroup)
                    add_permissions_to_group(COORDINATOR_CUSTOM_PERMISSIONS, newGroup)
                    add_permissions_to_group(EDITOR_CUSTOM_PERMISSIONS, newGroup)

                elif group == PATIENT_ACCESS:
                    # custom permissions
                    add_permissions_to_group(PATIENT_ACCESS_PERMISSIONS, newGroup)
                    # basic permissions
                    add_permissions_to_group(PATIENT_PERMISSIONS, newGroup)

                else:
                    if verbose:
                        print("Error: group does not exist!")

        if not verbose:
            print("groups_seeder(verbose=False), no output, groups seeded.")
