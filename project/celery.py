import logging
import os

from celery import Celery
from celery import Task
from django.conf import settings
import django

from azure.identity import DefaultAzureCredential

# Logging setup
logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()  # This is crucial!

app = Celery("project")

app.config_from_object("django.conf:settings", namespace="CELERY")

# Default Redis configuration for local development
broker_url = os.environ.get('CELERY_BROKER_URL')
result_backend = os.environ.get('CELERY_RESULT_BACKEND')


REDIS_HOST = os.environ.get('REDIS_HOST')  # Your Redis hostname (e.g., <your-cache>.redis.cache.windows.net)
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')  # Your Redis password
# Local development Redis configuration
# Default Redis configuration for local development

broker_url = f"redis://{':' + REDIS_PASSWORD + '@' if REDIS_PASSWORD else ''}{REDIS_HOST}:{REDIS_PORT}/0"
result_backend = f"redis://{':' + REDIS_PASSWORD + '@' if REDIS_PASSWORD else ''}{REDIS_HOST}:{REDIS_PORT}/1"

# Conditional configuration for Azure environment
# Conditional configuration for Azure environment
if "AZURE_CONTAINER_ENVIRONMENT" in os.environ:
    REDIS_HOST_AZURE = os.environ.get('REDIS_HOST_AZURE')  # Azure-specific host
    REDIS_PORT_AZURE = os.environ.get('REDIS_PORT_AZURE', '6379') # Azure-specific port
    REDIS_PASSWORD_AZURE = None

    credential = DefaultAzureCredential()

    try:
        token = credential.get_token("https://redis.azure.com/.default")
        REDIS_PASSWORD_AZURE = token.secret
        broker_url = f"redis://:{REDIS_PASSWORD_AZURE}@{REDIS_HOST_AZURE}:{REDIS_PORT_AZURE}/0"
        result_backend = f"redis://:{REDIS_PASSWORD_AZURE}@{REDIS_HOST_AZURE}:{REDIS_PORT_AZURE}/1"
        app.conf.update(
            broker_transport_options={
                "global_keyprefix": "{queue}:"
            },
            result_backend_transport_options={
                "global_keyprefix": "{rest}:"
            }
        )
    except Exception as e:
        print(f"Error getting Azure AD token for Redis: {e}")
        # Consider a fallback mechanism or raising an exception
        pass

app.conf.broker_url = broker_url
app.conf.result_backend = result_backend

# Tasks start here

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

class NPDATask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print(f"Task {task_id} failed with exception: {exc}")
        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        pass


app.Task = NPDATask