import logging
from django.core.exceptions import PermissionDenied, BadRequest
from django.apps import apps

logger = logging.getLogger(__name__)


def get_or_update_view_preference(user, new_view_preference):
    new_view_preference = int(new_view_preference) if new_view_preference else None
    NPDAUser = apps.get_model("npda", "NPDAUser")

    if new_view_preference is None:
        return int(user.view_preference)

    # View preference 0 was for organisation level view but that has been removed
    if new_view_preference not in [1, 2]:
        logger.warning(
            f"User {user} requested an invalid view preference: {new_view_preference}"
        )
        raise BadRequest()
    
    if new_view_preference == 2 and not user.is_rcpch_audit_team_member:  # national
        logger.warning(
            f"User {user} requested national view preference but they are not a member of the audit team"
        )
        raise PermissionDenied()
    
    user = NPDAUser.objects.get(pk=user.pk)
    user.view_preference = new_view_preference
    user.save(update_fields=["view_preference"])

    return int(user.view_preference)
