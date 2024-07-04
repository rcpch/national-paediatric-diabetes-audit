# python
# django
from django.contrib.auth.models import Group

# rcpch
from project.constants import (
    # groups
    AUDIT_CENTRE_EDITOR,
    AUDIT_CENTRE_READER,
    AUDIT_CENTRE_COORDINATOR,
    RCPCH_AUDIT_TEAM,
    RCPCH_AUDIT_PATIENT_FAMILY,
    # permissions
    TRUST_AUDIT_TEAM_VIEW_ONLY,
    TRUST_AUDIT_TEAM_EDIT_ACCESS,
    TRUST_AUDIT_TEAM_COORDINATOR_ACCESS,
    NPDA_AUDIT_TEAM_FULL_ACCESS,
    PATIENT_ACCESS,
)


def group_for_role(role_key):
    """
    Returns group for a role key
    """
    """
    Allocate Groups - the groups already have permissions allocated
    """
    if role_key == AUDIT_CENTRE_COORDINATOR:
        group = Group.objects.get(name=TRUST_AUDIT_TEAM_COORDINATOR_ACCESS)
    elif role_key == AUDIT_CENTRE_EDITOR:
        group = Group.objects.get(name=TRUST_AUDIT_TEAM_EDIT_ACCESS)
    elif role_key == AUDIT_CENTRE_READER:
        group = Group.objects.get(name=TRUST_AUDIT_TEAM_VIEW_ONLY)

    elif role_key == RCPCH_AUDIT_TEAM:
        group = Group.objects.get(name=NPDA_AUDIT_TEAM_FULL_ACCESS)

    elif role_key == RCPCH_AUDIT_PATIENT_FAMILY:
        group = Group.objects.get(name=PATIENT_ACCESS)
    else:
        # no group
        group = Group.objects.get(name=TRUST_AUDIT_TEAM_VIEW_ONLY)

    return group
