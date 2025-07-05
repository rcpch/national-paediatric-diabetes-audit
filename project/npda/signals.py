# python imports
import logging

# django imports
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

# third party imports
from two_factor.signals import user_verified

# RCPCH
from .general_functions import create_session_object, send_email_to_recipients, get_client_ip
from .middleware import get_current_user
from .models import VisitActivity, NPDAUser

# Logging setup
logger = logging.getLogger(__name__)

"""
This file contains signals that are triggered when:
 - a user logs in, logs out, or fails to log in. (Stored in the VisitActivity model)
 - a user sets up two-factor authentication (Stored in the VisitActivity model)
 - a user is created
 - a user changes their role
 - a user changes their group membership
 - a user changes their employer
 Particularly sensitive fields are logged and trigger email notifications.
"""

# Fields that should trigger email notifications when changed
EMAIL_TRIGGER_FIELDS = [
    'is_rcpch_audit_team_member',
    'is_rcpch_staff',
    'is_superuser',
    'email'
]

# Fields that should be logged when changed
LOGGED_FIELDS = [
    'role',
    'is_active',
    'is_rcpch_audit_team_member', 
    'is_rcpch_staff',
    'email',
    'first_name',
    'surname',
    'title'
]

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    # Set up the session data so that views are filtered correctly (eg by PDU)
    # Default is to show all PDUs that the user has access to, including the PDU that the user is affiliated with
    new_session_object = create_session_object(user)
    request.session.update(new_session_object)

    logger.info(
        f"{user} ({user.email}) logged in from {get_client_ip(request)}. pz_code: {new_session_object['pz_code']}."
    )

    VisitActivity.objects.create(
        activity=1, ip_address=get_client_ip(request), npdauser=user
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, request, user=None, **kwargs):
    if user is not None:
        VisitActivity.objects.create(
            activity=2, ip_address=get_client_ip(request), npdauser=user
        )
        logger.info(
            f"{user} ({user.email}) failed log in from {get_client_ip(request)}."
        )
    elif "credentials" in kwargs:
        if NPDAUser.objects.filter(email=kwargs["credentials"]["username"]).exists():
            user = NPDAUser.objects.get(email=kwargs["credentials"]["username"])
            VisitActivity.objects.create(
                activity=2, ip_address=get_client_ip(request), npdauser=user
            )
            logger.info(
                f"{user} ({user.email}) failed log in from {get_client_ip(request)}."
            )
        else:
            logger.info("Login failure by unknown user")
    else:
        logger.info("Login failure by unknown user")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    # https://github.com/rcpch/national-paediatric-diabetes-audit/issues/679
    # Sometimes this fires without an email on the user.
    email_to_log = f"({user.email})" if user else ""
    logger.info(f"{user} {email_to_log} logged out from {get_client_ip(request)}.")

    VisitActivity.objects.create(
        activity=3, ip_address=get_client_ip(request), npdauser=user
    )


# Two factor auth receiver
@receiver(user_verified)
def two_factor_auth_setup(request, user, device, **kwargs):
    if (
        user_verified
        and VisitActivity.objects.filter(npdauser=user, activity=7).count() < 1
    ):
        logger.info(
            f"{user} ({user.email}) has logged in the for the first time with two factor authentication."
        )
        VisitActivity.objects.create(
            activity=7, ip_address=get_client_ip(request), npdauser=user
        )  # Two factor authentication set up


@receiver(pre_save, sender=NPDAUser)
def capture_user_changes(sender, instance, **kwargs):
    """
    Capture the original state before save to compare changes.
    """
    if instance.pk:  # Only for existing users (updates)
        try:
            # Store original values for comparison
            original = NPDAUser.objects.get(pk=instance.pk)
            instance._original_values = {
                field: getattr(original, field) for field in LOGGED_FIELDS
            }
        except NPDAUser.DoesNotExist:
            instance._original_values = {}
    else:
        # New user creation
        instance._original_values = {}

@receiver(post_save, sender=NPDAUser)
def log_and_notify_user_changes(sender, instance, created, **kwargs):
    """
    Log changes and send notifications after user is saved.
    """
    current_user = get_current_user()
    
    if created:
        # Log user creation
        _log_user_activity(
            user=instance,
            activity_type="user_created",
            details=f"User created by {current_user.email if current_user else 'system'}",
            current_user=current_user
        )
        
        # Send welcome email notification to admins
        _send_user_creation_notification(instance, current_user)
        
    else:
        # Handle user updates
        original_values = getattr(instance, '_original_values', {})
        if original_values:
            changes = _detect_changes(instance, original_values)
            
            if changes:
                # Log all changes
                _log_user_changes(instance, changes, current_user)
                
                # Send email notifications for critical changes
                _send_change_notifications(instance, changes, current_user)


"""
Helper functions
"""
def _detect_changes(instance, original_values):
    """
    Compare current instance with original values to detect changes.
    """
    changes = {}
    
    for field in LOGGED_FIELDS:
        original_value = original_values.get(field)
        current_value = getattr(instance, field)
        
        if original_value != current_value:
            changes[field] = {
                'old': original_value,
                'new': current_value
            }
    
    return changes

def _log_user_activity(user, activity_type, details, current_user=None):
    """
    Create a log entry for user activity.
    """
    logging.warning(f"Logging user activity: {activity_type} for user {user.email}: {details}. Current user: {current_user.email if current_user else 'system'}")

def _log_user_changes(user, changes, current_user):
    """
    Log specific field changes for a user.
    """
    change_details = []
    
    for field, change in changes.items():
        change_detail = f"{field}: '{change['old']}' → '{change['new']}'"
        change_details.append(change_detail)
    
    details = f"User updated by {current_user.email if current_user else 'system'}: {'; '.join(change_details)}"
    
    _log_user_activity(
        user=user,
        activity_type="user_updated", 
        details=details,
        current_user=current_user
    )

def _send_change_notifications(user, changes, current_user):
    """
    Send email notifications for critical field changes.
    """
    email_worthy_changes = {
        field: change for field, change in changes.items() 
        if field in EMAIL_TRIGGER_FIELDS
    }
    
    if not email_worthy_changes:
        return
    
    # Send notification to user if email changed
    if 'email' in email_worthy_changes:
        _send_email_change_notification(user, email_worthy_changes['email'], current_user)
    
    # Send notification to admins for role/permission changes
    role_permission_changes = {
        field: change for field, change in email_worthy_changes.items()
        if field in ['role', 'is_rcpch_audit_team_member', 'is_rcpch_staff', 'is_active']
    }
    
    if role_permission_changes:
        _send_admin_notification(user, role_permission_changes, current_user)

def _send_email_change_notification(user, email_change, current_user):
    """
    Notify user when their email address is changed.
    """
    old_email = email_change['old']
    new_email = email_change['new']
    
    subject = "NPDA Account Email Address Changed"
    message = f"""
    Your NPDA account email address has been changed.
    
    Previous email: {old_email}
    New email: {new_email}
    Changed by: {current_user.email if current_user else 'System'}
    
    If you did not request this change, please contact the NPDA team immediately.
    """
    
    # Send to both old and new email addresses
    recipients = [old_email, new_email] if old_email != new_email else [new_email]
    
    try:
        send_email_to_recipients(
            recipients=recipients,
            subject=subject,
            message=message
        )
        logger.info(f"Email change notification sent for user {user.email}")
    except Exception as e:
        logger.error(f"Failed to send email change notification for user {user.email}: {e}")

def _send_admin_notification(user, changes, current_user):
    """
    Send notification to admins when user roles/permissions change.
    """
    change_details = []
    for field, change in changes.items():
        change_details.append(f"{field}: '{change['old']}' → '{change['new']}'")
    
    subject = f"NPDA User Permission Changes - {user.get_full_name()}"
    message = f"""
    User permissions have been modified:
    
    User: {user.get_full_name()} ({user.email})
    Changed by: {current_user.email if current_user else 'System'}
    
    Changes:
    {chr(10).join(f'• {detail}' for detail in change_details)}
    """
    
    # Send to audit team members
    admin_emails = NPDAUser.objects.filter(
        is_rcpch_audit_team_member=True,
        is_active=True
    ).values_list('email', flat=True)
    
    try:
        send_email_to_recipients(
            recipients=list(admin_emails),
            subject=subject,
            message=message
        )
        logger.info(f"Admin notification sent for user changes: {user.email}")
    except Exception as e:
        logger.error(f"Failed to send admin notification for user {user.email}: {e}")

def _send_user_creation_notification(user, current_user):
    """
    Send notification when new user is created.
    """
    subject = f"New NPDA User Created - {user.get_full_name()}"
    message = f"""
    A new NPDA user has been created:
    
    User: {user.get_full_name()} ({user.email})
    Role: {user.get_role_display()}
    Created by: {current_user.email if current_user else 'System'}
    """
    
    # Send to audit team members  
    admin_emails = NPDAUser.objects.filter(
        is_rcpch_audit_team_member=True,
        is_active=True
    ).values_list('email', flat=True)
    
    try:
        send_email_to_recipients(
            recipients=list(admin_emails),
            subject=subject,
            message=message
        )
        logger.info(f"User creation notification sent for: {user.email}")
    except Exception as e:
        logger.error(f"Failed to send user creation notification for {user.email}: {e}")