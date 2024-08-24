import logging
from django.core.exceptions import PermissionDenied
from django.apps import apps

logger = logging.getLogger(__name__)


def get_or_update_view_preference(user, new_view_preference):
    new_view_preference = int(new_view_preference) if new_view_preference else None
    NPDAUser = apps.get_model("npda", "NPDAUser")
    if new_view_preference == 2 and not user.is_rcpch_audit_team_member:  # national
        logger.warning(
            f"User {user} requested national view preference but they are not a member of the audit team"
        )
        raise PermissionDenied()
    elif new_view_preference:
        user = NPDAUser.objects.get(pk=user.pk)
        user.view_preference = new_view_preference
        user.save(update_fields=["view_preference"])
    else:
        user = NPDAUser.objects.get(pk=user.pk)

    return int(user.view_preference)
