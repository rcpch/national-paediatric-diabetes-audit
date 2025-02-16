# progress.py
import redis
import json

# Django settings
from django.conf import settings


class ProgressTracker:
    def __init__(self, task_id):
        self.task_id = task_id
        self.redis_client = redis.StrictRedis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True,
        )

    def set_progress(self, current, total, patient_id):
        progress_data = {
            "patient_id": patient_id,
            "current": current,
            "total": total,
            "percent": (current / total) * 100,
            "errors": 0,
        }
        self.redis_client.set(self.task_id, json.dumps(progress_data))

    def get_progress(self):
        progress_data = self.redis_client.get(self.task_id)
        if progress_data:
            return json.loads(progress_data)
        return None
