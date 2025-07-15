import datetime
from functools import wraps
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from asgiref.sync import sync_to_async
import asyncio
import logging

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
        if settings.DEBUG and user.is_authenticated:
            logger.warning(
                "User %s has bypassed 2FA for %s as settings.DEBUG is %s",
                user,
                view,
                settings.DEBUG,
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
        async def async_login_and_otp_required(request, *args, **kwargs):
            async_check_otp = sync_to_async(check_otp)

            if await async_check_otp(view, request):
                response = await view(request, *args, **kwargs)
                return response
            else:
                return redirect("two_factor:setup")

        @wraps(view)
        def sync_login_and_otp_required(request, *args, **kwargs):
            if check_otp(view, request):
                return view(request, *args, **kwargs)
            else:
                return redirect("two_factor:setup")

        login_required(view)

        if asyncio.iscoroutinefunction(view):
            return async_login_and_otp_required
        else:
            return sync_login_and_otp_required

    return decorator


def check_data_permissions():
    def _check_data_permissions(view, request, *args, **kwargs):
        can_view_all_data = request.user.is_superuser or request.user.is_rcpch_audit_team_member

        if "audit_period" in kwargs:
            try:
                audit_period = AuditPeriod.objects.get(slug=kwargs["audit_period"])
            except AuditPeriod.DoesNotExist as e:
                if not can_view_all_data:
                    raise PermissionDenied(f"Audit period {kwargs['audit_period']} does not exist")

                raise e
        else:
            selected_audit_year = request.session.get("selected_audit_year", None)

            audit_period = AuditPeriod.objects.filter(
                start_date__year=selected_audit_year
            ).first()

        if not audit_period.is_visible and not can_view_all_data:
            raise PermissionDenied(f"Audit period {kwargs['audit_period']} is not visible")

        if "pz_code" in kwargs:
            try:
                pdu = PaediatricDiabetesUnit.objects.get(pz_code=kwargs["pz_code"])
            except PaediatricDiabetesUnit.DoesNotExist as e:
                if not can_view_all_data:
                    raise PermissionDenied(f"PDU {kwargs['pz_code']} does not exist")

                raise e
        else:
            pdu = PaediatricDiabetesUnit.objects.get(pz_code=request.session["pz_code"])

        if not can_view_all_data:
            can_view_this_pdu = request.user.organisation_employers.filter(
                pz_code=pdu.pz_code
            ).exists()

            if not can_view_this_pdu:
                raise PermissionDenied(
                    f"User {request.user} does not have permission to view PDU {pdu.pz_code}"
                )
        
        return (audit_period, pdu)

    def decorator(view):
        @wraps(view)
        async def async_check_data_permissions(request, *args, **kwargs):
            (audit_period, pdu) = await sync_to_async(_check_data_permissions)(view, request, *args, **kwargs)

            next_kwargs = kwargs | {
                "audit_period": audit_period,
                "pdu": pdu
            }

            if "pz_code" in next_kwargs:
                del next_kwargs["pz_code"]

            return await view(request, *args, **next_kwargs)

        @wraps(view)
        def sync_check_data_permissions(request, *args, **kwargs):
            (audit_period, pdu) = _check_data_permissions(view, request, *args, **kwargs)

            next_kwargs = kwargs | {
                "audit_period": audit_period,
                "pdu": pdu
            }

            if "pz_code" in next_kwargs:
                del next_kwargs["pz_code"]

            return view(request, *args, **next_kwargs)

        if asyncio.iscoroutinefunction(view):
            return async_check_data_permissions
        else:
            return sync_check_data_permissions

    return decorator