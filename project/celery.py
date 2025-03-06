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

app.conf.update(
    # Hacks to work around the lack of built in support for Redis cluster.
    # We don't use a cluster directly but Azure Managed Redis acts like one.
    # https://github.com/celery/celery/issues/8276#issuecomment-2082176893
    broker_transport_options={
        "global_keyprefix": "{queue}:"
    },
    result_backend_transport_options={
        "global_keyprefix": "{rest}:"
    }
)

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

class NPDATask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print(f"Task {task_id} failed with exception: {exc}")
        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        pass


app.Task = NPDATask