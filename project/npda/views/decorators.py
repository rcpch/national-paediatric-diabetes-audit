import logging
from functools import wraps

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from ..models import AuditPeriod, PaediatricDiabetesUnit

logger = logging.getLogger(__name__)


def login_and_otp_required():
    """
    Must have verified via 2FA
    """

    def check_otp(view, request):
        # Then, ensure 2fa verified
        user = request.user
        # Bypass 2fa if local dev, with warning message
        if settings.LOCAL_DEV_BYPASS_2FA_AND_CAPTCHA and user.is_authenticated:
            logger.warning(
                "User %s has bypassed 2FA for %s as settings.LOCAL_DEV_BYPASS_2FA_AND_CAPTCHA is %s",
                user,
                view,
                settings.LOCAL_DEV_BYPASS_2FA_AND_CAPTCHA,
            )
            return True

        if not user.is_authenticated:
            logger.info(
                "User %s is not authenticated. Tried accessing %s",
                user,
                view.__qualname__,
            )
            return False

        # Prevent unverified (from otp) users
        if hasattr(user, "is_verified") and not user.is_verified():
            logger.info(
                "User %s is unverified. Tried accessing %s",
                user,
                view.__qualname__,
            )
            return False

        return True

    def decorator(view):
        @wraps(view)
        def sync_login_and_otp_required(request, *args, **kwargs):
            if check_otp(view, request):
                return view(request, *args, **kwargs)
            else:
                return redirect("two_factor:setup")

        return login_required(sync_login_and_otp_required)

    return decorator


def check_data_permissions():
    def _check_data_permissions(request, *args, **kwargs):
        audit_period = AuditPeriod.objects.get_audit_period_for_request(request)
        pdu = PaediatricDiabetesUnit.objects.get_pdu_for_request(request)

        return (audit_period, pdu)

    def decorator(view):
        @wraps(view)
        def sync_check_data_permissions(request, *args, **kwargs):
            audit_period, pdu = _check_data_permissions(request, *args, **kwargs)

            next_kwargs = kwargs | {"audit_period": audit_period, "pdu": pdu}

            if "pz_code" in next_kwargs:
                del next_kwargs["pz_code"]

            return view(request, *args, **next_kwargs)

        return sync_check_data_permissions

    return decorator
