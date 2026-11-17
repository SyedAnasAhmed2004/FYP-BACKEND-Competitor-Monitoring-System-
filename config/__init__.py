# Load the Celery app when Django starts so that @shared_task functions
# (and task.delay() calls from API views) use the Redis broker from settings.
from .celery import app as celery_app

__all__ = ('celery_app',)
