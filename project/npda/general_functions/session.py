import logging

from django.apps import apps
from django.core.exceptions import PermissionDenied
from django.utils import timezone

# NPDA Imports
from project.constants.feature_flags import FEATURE_FLAGS
from project.npda.general_functions import get_client_ip

logger = logging.getLogger(__name__)


def get_default_feature_flags():
    feature_flags = []
    for flag, opts in FEATURE_FLAGS.items():
        if opts.get("default"):
            feature_flags.append(flag)
    return feature_flags


def get_user_feature_flags(user):
    if user is None:
        return get_default_feature_flags()

    user_flags = getattr(user, "feature_flags", None)
    if user_flags is None:
        return get_default_feature_flags()

    return list(user_flags)


def create_session_object(user):
    return {
        "feature_flags": get_user_feature_flags(user),
    }


def save_csv_uploading_user_to_visitactivity(request):
    """
    Save the user who is uploading a CSV to the VisitActivity model.
    This is used to track who is uploading CSVs and when.
    """
    VisitActivity = apps.get_model("npda", "VisitActivity")

    # Create VisitActivity entry for the user
    VisitActivity.objects.create(
        npdauser=request.user,
        activity=8,  # UPLOADED_CSV
        ip_address=get_client_ip(request=request),
        activity_datetime=timezone.now(),
    )
