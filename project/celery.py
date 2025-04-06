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

# app.conf.update(
#     # Hacks to work around the lack of built in support for Redis cluster.
#     # We don't use a cluster directly but Azure Managed Redis acts like one.
#     # https://github.com/celery/celery/issues/8276#issuecomment-2082176893
#     broker_transport_options={
#         "global_keyprefix": "{queue}:"
#     },
#     result_backend_transport_options={
#         "global_keyprefix": "{rest}:"
#     }
# )

# def get_redis_token():
#     credential = DefaultAzureCredential()
#     redis_resource_id = "https://redis.azure.com"
#     token_object = credential.get_token(redis_resource_id)
#     return token_object.token

# broker_host = os.environ.get("REDIS_HOST")
# broker_port = os.environ.get("REDIS_PORT", 6379)
# broker_password = get_redis_token()
# broker_username = os.environ.get("MANAGED_IDENTITY_OBJECT_ID") # Set this as an environment variable

# broker_url = f"redis://{broker_username}:{broker_password}@{broker_host}:{broker_port}/0"

# CELERY_BROKER_URL = broker_url
# CELERY_RESULT_BACKEND = broker_url # If using Redis as result backend

REDIS_HOST = os.environ.get('REDIS_HOST')  # Your Redis hostname (e.g., <your-cache>.redis.cache.windows.net)
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_PASSWORD = None  # We will obtain this dynamically

credential = DefaultAzureCredential()

try:
    token = credential.get_token("https://redis.azure.com/.default")
    REDIS_PASSWORD = token.secret
except Exception as e:
    print(f"Error getting Azure AD token for Redis: {e}")
    # Handle the error appropriately, maybe fall back to a different configuration
    pass

broker_url = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
result_backend = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/1"


app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

class NPDATask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print(f"Task {task_id} failed with exception: {exc}")
        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        pass


app.Task = NPDATask