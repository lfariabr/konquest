# Run on docker;
# docker exec -it konquest_django python manage.py shell < /app/scripts/update_celery_schedule.py

from celery.schedules import crontab
from django.conf import settings
from konquist.celery import app

new_schedule = {
    'test_redis_connection': {
        'task': 'apiCrm.test_redis',
        'schedule': crontab(minute='*/1')
    },
    'cleaner_crm_tables': {
        'task': 'apiCrm.cleanup_crm_tables',
        'schedule': crontab(hour=19, minute=0),
        'options': {'expires': 3600}
    },
    'fetch_all_data': {
        'task': 'apiCrm.fetch_all_data',
        'schedule': crontab(hour=0, minute=10),
        'options': {'expires': 3600}
    },
    'check_contacts_in_crm': {
        'task': 'apiCrm.check_contacts_in_crm',
        'schedule': crontab(hour=1, minute=0),
        'options': {'expires': 7200}
    },
    'process_scheduled_campaigns': {
        'task': 'apiCrm.process_scheduled_campaigns',
        'schedule': crontab(hour=3, minute=0),
        'options': {'expires': 1800}
    },
    'process_queues': {
        'task': 'queue.process_queues',
        'schedule': crontab(hour=7, minute=15),
        'options': {'expires': 7200}
    }
}

# Update the beat schedule
app.conf.beat_schedule = new_schedule
print("Celery beat schedule has been updated successfully!")
print("\nNew schedule:")
for task, config in new_schedule.items():
    print(f"\n{task}:")
    print(f"  Schedule: {config['schedule']}")
    if 'options' in config:
        print(f"  Expires: {config['options'].get('expires')} seconds")
