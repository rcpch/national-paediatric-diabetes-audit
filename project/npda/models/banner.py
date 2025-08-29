from django.db import models

from project.constants import ROLES

class Banner(models.Model):
    url_matcher = models.CharField(max_length=255)
    html = models.TextField()
    disabled = models.BooleanField(default=False)

    # Only show the banner if the user has a given role.
    # RCPCH audit team members always see banners so they can check how they look.
    user_role_to_target = models.PositiveSmallIntegerField(choices=ROLES, blank=True, null=True)

    def __str__(self):
        return f"Banner for {self.url_matcher}"