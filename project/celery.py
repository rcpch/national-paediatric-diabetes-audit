import logging
import os
from logging.config import dictConfig

import django
from celery import Celery, Task
from celery.signals import setup_logging
from django.conf import settings

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
    broker_transport_options={"global_keyprefix": "{queue}:"},
    result_backend_transport_options={"global_keyprefix": "{rest}:"},
)

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@setup_logging.connect
def setup_celery_logging(*args, **kwargs):
    dictConfig(settings.LOGGING)


class NPDATask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print(f"Task {task_id} failed with exception: {exc}")
        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        pass


app.Task = NPDATask
