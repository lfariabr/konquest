# konquista/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_ready


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'konquist.settings')

app = Celery('konquist')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.broker_connection_retry_on_startup = True
app.conf.imports = ['apiCrm.tasks']
app.autodiscover_tasks()

@worker_ready.connect
def on_worker_ready(**_):
    print('\033[92m\n🚀 Celery worker is up and running!\033[0m\n')

app.conf.beat_schedule = {
    'cleaner_crm_tables': {
        'task': 'apiCrm.cleanup_crm_tables',
        'schedule': crontab(hour=2, minute=54),
    },

    'fetch_all_data': {
        'task': 'apiCrm.fetch_all_data',
        'schedule': crontab(hour=2, minute=55),
    },

    'check_contacts_in_crm': {
        'task': 'apiCrm.check_contacts_in_crm',
        'schedule': crontab(hour=3, minute=40),
    },

    'process_scheduled_campaigns': {
        'task': 'campaign.process_scheduled_campaigns',
        'schedule': 150.0,
    },
}