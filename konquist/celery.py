# konquista/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'konquist.settings')

app = Celery('konquist')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.imports = ['apiCrm.tasks']
app.autodiscover_tasks()

app.conf.beat_schedule = { # Check what else I can put aside from task and schedule
    # Clean up tables - run at midnight daily
    'cleaner_crm_tables': {
    'task': 'apiCrm.cleanup_crm_tables',
    'schedule': crontab(hour=0, minute=0),
    },
    # Contact check task - runs daily right after yet to be implemented fetch_all_data
    'check_contacts_in_crm': {
    'task': 'apiCrm.check_contacts_in_crm',
    'schedule': crontab(minute=30), # for instant testing.
    },
    # Fetch all data task - runs daily right after yet to be implemented check_contacts_in_crm
    # 'fetch_all_data': {
    # 'task': 'apiCrm.fetch_all_data',
    # 'schedule': crontab(minute='*'), 
    # },
}