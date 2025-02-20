import logging
import os

from celery import Celery
from celery import Task
from django.conf import settings
import django

# Logging setup
logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()  # This is crucial!

app = Celery("project")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


class NPDATask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print(f"Task {task_id} failed with exception: {exc}")
        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        pass


@app.task(bind=True)
def debug_task(self):
    logger.debug("Request: {0!r}".format(self.request))


app.Task = NPDATask
