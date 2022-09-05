
import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FileProject.settings')

app = Celery(
    'FileProject',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings')

# Load task modules from all registered Django apps.
app.autodiscover_tasks(settings.INSTALLED_APPS)

CELERY_CACHE_BACKEND = 'default'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# from celery import Celery
#
# app = Celery('proj',
#              broker='redis://localhost:6379/0',
#              backend='redis://localhost:6379/0',
#              # include=['FileProject.tasks']
#              )
#
#
# if __name__ == '__main__':
#     app.start()
