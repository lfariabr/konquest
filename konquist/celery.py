# konquista/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'konquist.settings')

app = Celery('konquist')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = { # Check what else I can put aside from task and schedule
    'cleaner_leads': {
        'task': 'apiCrm.tasks.clean_up_leads',
        'schedule': crontab(minute='*/15'),
    },
}