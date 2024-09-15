# django
from django.contrib.gis.db import models
from django.utils import timezone


class VisitActivity(models.Model):
    SUCCESSFUL_LOGIN = 1
    UNSUCCESSFUL_LOGIN = 2
    LOGOUT = 3
    PASSWORD_RESET_LINK_SENT = 4
    PASSWORD_RESET = 5
    PASSWORD_LOCKOUT = 6
    SETUP_TWO_FACTOR_AUTHENTICATION = 7
    UPLOADED_CSV = 8
    TOUCHED_PATIENT_RECORD = 9

    ACTIVITY = (
        (SUCCESSFUL_LOGIN, "Successful login"),
        (UNSUCCESSFUL_LOGIN, "Login failed"),
        (LOGOUT, "Logout"),
        (PASSWORD_RESET_LINK_SENT, "Password reset link sent"),
        (PASSWORD_RESET, "Password reset successfully"),
        (PASSWORD_LOCKOUT, "Password lockout"),
        (SETUP_TWO_FACTOR_AUTHENTICATION, "Two factor authentication set up"),
        (UPLOADED_CSV, "Uploaded CSV"),
        (TOUCHED_PATIENT_RECORD, "Touched patient record"),
    )

    activity_datetime = models.DateTimeField(auto_created=True, default=timezone.now)

    activity = models.PositiveSmallIntegerField(choices=ACTIVITY, default=1)

    ip_address = models.CharField(max_length=250, blank=True, null=True)

    npdauser = models.ForeignKey("npda.NPDAUser", on_delete=models.CASCADE)

    class Meta:
        indexes = [models.Index(fields=["-activity_datetime"])]
        verbose_name = "User Access Log"
        verbose_name_plural = "User Access Logs"
        ordering = ("activity_datetime",)

    def __str__(self) -> str:
        return f"{self.npdauser} on {self.activity_datetime}"
