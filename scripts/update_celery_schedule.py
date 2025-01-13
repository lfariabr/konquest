# Run on docker;
# docker exec -it konquest_django python manage.py shell < /app/scripts/update_celery_schedule.py

import json
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from django.conf import settings

def get_or_create_schedule(hour, minute, timezone='America/Sao_Paulo'):
    return CrontabSchedule.objects.get_or_create(
        minute=str(minute),
        hour=str(hour),
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
        timezone=timezone
    )[0]

def update_or_create_task(name, task_path, schedule, enabled=True, expires=None):
    defaults = {
        'task': task_path,
        'crontab': schedule,
        'enabled': enabled,
        'expires': expires,
        'kwargs': json.dumps({})
    }
    
    task, created = PeriodicTask.objects.update_or_create(
        name=name,
        defaults=defaults
    )
    
    action = "Created" if created else "Updated"
    print(f"{action} task: {name}")
    print(f"  Schedule: {schedule}")
    print(f"  Enabled: {enabled}")
    if expires:
        print(f"  Expires: {expires} seconds")
    print("-" * 50)

# Clear existing tasks (optional, comment out if you want to keep other tasks)
# PeriodicTask.objects.all().delete()

# Create/update all scheduled tasks
tasks = [
    {
        'name': 'test_redis_connection',
        'task': 'apiCrm.test_redis',
        'schedule': get_or_create_schedule(hour='*', minute='*/1'),
        'expires': None
    },
    {
        'name': 'cleaner_crm_tables',
        'task': 'apiCrm.cleanup_crm_tables',
        'schedule': get_or_create_schedule(hour=19, minute=0),
        'expires': 3600
    },
    {
        'name': 'fetch_all_data',
        'task': 'apiCrm.fetch_all_data',
        'schedule': get_or_create_schedule(hour=0, minute=10),
        'expires': 3600
    },
    {
        'name': 'check_contacts_in_crm',
        'task': 'apiCrm.check_contacts_in_crm',
        'schedule': get_or_create_schedule(hour=1, minute=30),
        'expires': 7200
    },
    {
        'name': 'process-campaigns',  # Note: using hyphen to match existing name
        'task': 'apiCrm.process_scheduled_campaigns',
        'schedule': get_or_create_schedule(hour=5, minute=00),  # Set for 04:48 AM
        'expires': 1800
    },
    {
        'name': 'process_queues',
        'task': 'queue.process_queues',
        'schedule': get_or_create_schedule(hour=7, minute=15),
        'expires': 7200
    }
]

print("Updating Celery Beat schedule in database...")
print("=" * 50)

for task_config in tasks:
    update_or_create_task(
        name=task_config['name'],
        task_path=task_config['task'],
        schedule=task_config['schedule'],
        expires=task_config['expires']
    )

print("\nAll tasks updated successfully!")
print("Don't forget to restart Celery Beat:")
