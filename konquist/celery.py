# konquista/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_ready, setup_logging, task_success, task_failure
from celery import signals
from django.db import connection
from celery.signals import task_prerun, task_postrun
import logging
from celery.signals import after_task_publish

logger = logging.getLogger(__name__)

@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    """Ensure clean database connection at start and log task start"""
    logger.info('Task starting: %s[%s]', task.name, task_id)
    connection.close()

@task_postrun.connect
def task_postrun_handler(task_id, task, *args, retval=None, state=None, **kwargs):
    """Close database connection after task and log completion"""
    logger.info('Task complete: %s[%s] -> %s', task.name, task_id, state)
    connection.close()

@after_task_publish.connect
def task_sent_handler(sender=None, headers=None, body=None, **kwargs):
    """Log when task is sent to queue"""
    logger.info('Task sent to queue: %s', sender)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'konquist.settings')

app = Celery('konquist')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.broker_connection_retry_on_startup = True

# Enable task autodiscovery
app.autodiscover_tasks()

# Add the new configuration here
app.conf.update(
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s",
    worker_redirect_stdouts_level='DEBUG',
    broker_transport_options={
        'visibility_timeout': 43200,    # 12 hours
        'socket_timeout': 60,           # 1 minute
        'socket_connect_timeout': 30,   # 30 seconds
        'socket_keepalive': True,
        'max_retries': 3,
        'retry_on_timeout': True,
        'retry_backoff': 5,            # Start with 5 second backoff
        'retry_backoff_max': 300       # Max backoff of 5 minutes
    },
    broker_connection_retry=True,      # Retry connection on startup
    broker_connection_max_retries=None,  # Retry forever
    broker_connection_timeout=30,      # Connection timeout
    broker_heartbeat=10,              # Heartbeat every 10 seconds
    task_acks_late=True,              # Only acknowledge after task completion
    task_reject_on_worker_lost=True,   # Reject tasks if worker disconnects
    worker_prefetch_multiplier=1,      # One task at a time per worker
    worker_max_tasks_per_child=10000,  # Restart worker after 10000 tasks
    worker_lost_wait=60,              # Wait 1 minute for lost workers
    task_track_started=True,          # Track task states for better timeout handling
    task_ignore_result=True,          # Don't store task results
    worker_send_task_events=False,    # Don't send task events
    worker_disable_rate_limits=True,  # Disable rate limits since we handle them in QueueProcessor
    task_store_errors_even_if_ignored=False,  # Don't store errors,
    redis_max_connections=10,
    redis_socket_connect_timeout=30,
    broker_pool_limit=10,  # Limit Redis connections
    redis_socket_keepalive=True,
    redis_retry_on_timeout=True
)
app.conf.imports = ['apiCrm.tasks']

# Configure timezone to match Django settings
app.conf.timezone = 'America/Sao_Paulo'
app.conf.enable_utc = False

# Configure task queues
app.conf.task_routes = {
    # 'apiCrm.process_scheduled_campaigns': {'queue': 'campaign_queue'},
    'apiCrm.tasks.test_redis': {'queue': 'default'},
    # 'apiCrm.fetch_all_data': {'queue': 'default'},
    # 'apiCrm.check_contacts_in_crm': {'queue': 'default'},
    # 'queue.process_queues': {'queue': 'default'}  # Updated task name
}

@signals.setup_logging.connect
def setup_celery_logging(**kwargs):
    print('\033[92m\n🚀 Celery worker is up and running!\033[0m\n')

@task_success.connect
def task_success_handler(**kwargs):
    """Log successful task completion"""
    pass

@task_failure.connect
def task_failure_handler(**kwargs):
    """Log task failures"""
    pass

app.conf.beat_schedule = {
    'test_redis_connection': {
        'task': 'apiCrm.test_redis',
        'schedule': crontab(minute='*/1')
    },

    'cleaner_crm_tables': {
        'task': 'apiCrm.cleanup_crm_tables',
        'schedule': crontab(hour=0, minute=5),  # 5:30 AM
        'options': {'expires': 3600}  # Task expires after 1 hour
    },

    # Daily data pipeline sequence
    'fetch_all_data': {
        'task': 'apiCrm.fetch_all_data',
        'schedule': crontab(hour=0, minute=10),  # 5:30 AM
        'options': {'expires': 3600}  # Task expires after 1 hour
    },

    'check_contacts_in_crm': {
        'task': 'apiCrm.check_contacts_in_crm',
        'schedule': crontab(hour=4, minute=00),  # 6:00 AM
        'options': {'expires': 270000}  
    },

    'process_scheduled_campaigns': {
        'task': 'apiCrm.process_scheduled_campaigns',
        'schedule': crontab(hour=5, minute=30),  # 7:00 AM
        'options': {'expires': 1800} 
    },

    'process_queues': {
        'task': 'queue.process_queues',
        'schedule': crontab(hour=7, minute=15),  # 8:00 AM
        'options': {'expires': 270000}
    }
}

