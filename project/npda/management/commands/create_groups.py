from django.contrib.auth.management import create_permissions
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from ....constants import (
    GROUPS,
    # group names
    NPDA_AUDIT_TEAM_FULL_ACCESS,
    PATIENT_ACCESS,
    TRUST_AUDIT_TEAM_EDIT_ACCESS,
    TRUST_AUDIT_TEAM_FULL_ACCESS,
    TRUST_AUDIT_TEAM_VIEW_ONLY,
    # custom permissions
    CAN_CONSENT_TO_AUDIT_PARTICIPATION,
    CAN_ALLOCATE_NPDA_LEAD_CENTRE,
    CAN_TRANSFER_NPDA_LEAD_CENTRE,
    CAN_EDIT_NPDA_LEAD_CENTRE,
    CAN_DELETE_NPDA_LEAD_CENTRE,
    CAN_LOCK_CHILD_PATIENT_DATA_FROM_EDITING,
    CAN_UNLOCK_CHILD_PATIENT_DATA_FROM_EDITING,
    CAN_OPT_OUT_CHILD_FROM_INCLUSION_IN_AUDIT,
    CAN_PUBLISH_NPDA_DATA,
)
from ...models import NPDAUser, Patient, Visit, Site


def groups_seeder(
    run_create_groups=False, add_permissions_to_existing_groups=False, verbose=True
):
    patientContentType = ContentType.objects.get_for_model(Patient)
    visitContentType = ContentType.objects.get_for_model(Visit)
    npdaUserContentType = ContentType.objects.get_for_model(NPDAUser)
    siteContentType = ContentType.objects.get_for_model(Site)

    """
    Note view permissions include viewing users, but not creating, updating or deleting them
    View permissions include viewing but NOT updating or deleting case audit records

    NOTE Additional constraints are applied in view decorators to prevent users accessing 
    records of users or children in organisations other than their own
    """
    VIEW_PERMISSIONS = [
        {"codename": "view_npdauser", "content_type": npdaUserContentType},
        {"codename": "view_patient", "content_type": patientContentType},
        {"codename": "view_visit", "content_type": visitContentType},
        {"codename": "view_site", "content_type": siteContentType},
    ]

    """
    Administrators have additional privileges in relation to patient management
    Permissions include create, update and view cases, but not delete them
    """
    ADMIN_PATIENT_MANAGEMENT_PERMISSIONS = [
        {"codename": "change_patient", "content_type": patientContentType},
        {"codename": "add_patient", "content_type": patientContentType},
    ]
    """
    Editors inherit all view permissions
    Note editor access permissions do not include creating, updating or deleting Epilepsy12Users.
    Editor access include deleting patients
    Editor access permissions do include creating, updating or delete patient records
    
    Editors can create, update and delete neurology, general paediatric and surgical sites, but 
    cannot create, update or delete lead NPDA centre allocation, or transfer

    NOTE Additional constraints are applied in view decorators to prevent users accessing 
    records of users or children in organisations other than their own
    """
    EDITOR_PERMISSIONS = [
        {"codename": "delete_patient", "content_type": patientContentType},
        {"codename": "change_visit", "content_type": visitContentType},
        {"codename": "add_visit", "content_type": visitContentType},
        {"codename": "delete_visit", "content_type": visitContentType},
        # sites
        {"codename": "change_site", "content_type": siteContentType},
        {"codename": "add_site", "content_type": siteContentType},
        {"codename": "delete_site", "content_type": siteContentType},
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
            "content_type": siteContentType,
        },
    ]

    """
    Full access inherit all editor permissions
    In addition they can
    - create, change and delete NPDAUsers
    - transfer to another lead NPDA centre

    NOTE Additional constraints are applied in view decorators to prevent users accessing 
    records of users or children in organisations other than their own
    """
    FULL_ACCESS_PERMISSIONS = [
        # epilepsy12 user
        {"codename": "add_npdauser", "content_type": npdaUserContentType},
        {
            "codename": "change_npdauser",
            "content_type": npdaUserContentType,
        },
        {
            "codename": "delete_npdauser",
            "content_type": npdaUserContentType,
        },
        {
            "codename": CAN_DELETE_NPDA_LEAD_CENTRE[0],
            "content_type": siteContentType,
        },
        {
            "codename": CAN_EDIT_NPDA_LEAD_CENTRE[0],
            "content_type": siteContentType,
        },
        {
            "codename": CAN_TRANSFER_NPDA_LEAD_CENTRE[0],
            "content_type": siteContentType,
        },
    ]

    """
    NPDA Team inherit all view, edit and full access permissions. In addition they may:
    - opt children out of NPDA
    - allocate, update and delete NPDA lead site status
    - publish NPDA data to the public site
    
    NOTE RCPCH team are able to access all users and all children nationally.
    """
    NPDA_AUDIT_TEAM_ACCESS_PERMISSIONS = [
        # {
        #     "codename": CAN_PUBLISH_NPDA_DATA[0],
        #     "content_type": organisationKPIAggregationContentType,
        # },
    ]

    PATIENT_ACCESS_PERMISSIONS = [
        # currently not used
        {
            "codename": CAN_CONSENT_TO_AUDIT_PARTICIPATION[0],
            "content_type": npdaUserContentType,
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

    if add_permissions_to_existing_groups:
        for group in GROUPS:
            if verbose:
                print(f"...adding permissions to {group}...")
            # add permissions to group
            newGroup = Group.objects.filter(name=group).get()

            if group == NPDA_AUDIT_TEAM_FULL_ACCESS:
                # custom permissions
                add_permissions_to_group(NPDA_AUDIT_TEAM_ACCESS_PERMISSIONS, newGroup)
                # basic permissions
                add_permissions_to_group(VIEW_PERMISSIONS, newGroup)
                add_permissions_to_group(ADMIN_PATIENT_MANAGEMENT_PERMISSIONS, newGroup)
                add_permissions_to_group(EDITOR_PERMISSIONS, newGroup)
                add_permissions_to_group(FULL_ACCESS_PERMISSIONS, newGroup)

            elif group == TRUST_AUDIT_TEAM_VIEW_ONLY:
                # custom permissions

                # basic permissions
                add_permissions_to_group(VIEW_PERMISSIONS, newGroup)

            elif group == TRUST_AUDIT_TEAM_EDIT_ACCESS:
                # custom permissions

                # basic permissions
                add_permissions_to_group(VIEW_PERMISSIONS, newGroup)
                add_permissions_to_group(ADMIN_PATIENT_MANAGEMENT_PERMISSIONS, newGroup)
                add_permissions_to_group(EDITOR_PERMISSIONS, newGroup)

            elif group == TRUST_AUDIT_TEAM_FULL_ACCESS:
                # custom permissions

                # basic permissions
                add_permissions_to_group(VIEW_PERMISSIONS, newGroup)
                add_permissions_to_group(ADMIN_PATIENT_MANAGEMENT_PERMISSIONS, newGroup)
                add_permissions_to_group(EDITOR_PERMISSIONS, newGroup)
                add_permissions_to_group(FULL_ACCESS_PERMISSIONS, newGroup)

            elif group == PATIENT_ACCESS:
                # custom permissions
                add_permissions_to_group(PATIENT_ACCESS_PERMISSIONS, newGroup)
                # basic permissions
                add_permissions_to_group(VIEW_PERMISSIONS, newGroup)

            else:
                if verbose:
                    print("Error: group does not exist!")

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

                if group == NPDA_AUDIT_TEAM_FULL_ACCESS:
                    # custom permissions
                    add_permissions_to_group(
                        NPDA_AUDIT_TEAM_ACCESS_PERMISSIONS, newGroup
                    )
                    # basic permissions
                    add_permissions_to_group(VIEW_PERMISSIONS, newGroup)
                    add_permissions_to_group(
                        ADMIN_PATIENT_MANAGEMENT_PERMISSIONS, newGroup
                    )
                    add_permissions_to_group(EDITOR_PERMISSIONS, newGroup)
                    add_permissions_to_group(FULL_ACCESS_PERMISSIONS, newGroup)

                elif group == TRUST_AUDIT_TEAM_VIEW_ONLY:
                    # custom permissions

                    # basic permissions
                    add_permissions_to_group(VIEW_PERMISSIONS, newGroup)
                    add_permissions_to_group(
                        ADMIN_PATIENT_MANAGEMENT_PERMISSIONS, newGroup
                    )

                elif group == TRUST_AUDIT_TEAM_EDIT_ACCESS:
                    # custom permissions

                    # basic permissions
                    add_permissions_to_group(VIEW_PERMISSIONS, newGroup)
                    add_permissions_to_group(
                        ADMIN_PATIENT_MANAGEMENT_PERMISSIONS, newGroup
                    )
                    add_permissions_to_group(EDITOR_PERMISSIONS, newGroup)

                elif group == TRUST_AUDIT_TEAM_FULL_ACCESS:
                    # custom permissions

                    # basic permissions
                    add_permissions_to_group(VIEW_PERMISSIONS, newGroup)
                    add_permissions_to_group(
                        ADMIN_PATIENT_MANAGEMENT_PERMISSIONS, newGroup
                    )
                    add_permissions_to_group(EDITOR_PERMISSIONS, newGroup)
                    add_permissions_to_group(FULL_ACCESS_PERMISSIONS, newGroup)

                elif group == PATIENT_ACCESS:
                    # custom permissions
                    add_permissions_to_group(PATIENT_ACCESS_PERMISSIONS, newGroup)
                    # basic permissions
                    add_permissions_to_group(VIEW_PERMISSIONS, newGroup)

                else:
                    if verbose:
                        print("Error: group does not exist!")

                    else:
                        if verbose:
                            print("Error: group does not exist!")

        if not verbose:
            print("groups_seeder(verbose=False), no output, groups seeded.")
