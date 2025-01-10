# Docker
- Create / Navigate to directory for Konquest
    mkdir -p /var/www/konquest
    cd /var/www/konquest

- Clone your Repository / Navigate into the cloned directory
    git clone https://github.com/lfariabr/konquest.git
    cd konquest

- Check if we have the necessary files
    ls -la

- Run docker-compose
    docker-compose build
    docker-compose up -d
    cd /var/www/konquest

- check running containers
    docker logs -f k_celery_beat
    docker logs -f k_celery_worker
    docker-compose logs -f

- droplet
    ssh root@209.38.90.25
    cd /var/www/konquest

## Docker useful commands

### View all active tasks
docker exec -it k_celery_beat celery -A konquist purge -f
### View scheduled tasks
docker exec -it k_celery_worker celery -A konquist inspect scheduled

### View registered tasks
docker exec -it k_celery_worker celery -A konquist inspect registered

### py shell in containers
docker exec -it konquest_django python manage.py shell
from django_celery_beat.models import PeriodicTask
for task in PeriodicTask.objects.all():
    print(f"Name: {task.name}, Task: {task.task}, Schedule: {task.crontab if task.crontab else task.interval}")

### Instant run tasks
docker exec -it k_celery_worker celery -A konquist call apiCrm.cleanup_crm_tables
docker exec -it k_celery_worker celery -A konquist call apiCrm.process_scheduled_campaigns
docker exec -it k_celery_worker celery -A konquist call queue.process_queues

### Clear the Redis lock
docker exec -it k_redis redis-cli -p 6380 -a YOUR_REDIS_PASSWORD DEL fetch_all_data_lock

### Clear the rate limit
docker exec -it k_redis redis-cli -p 6380 -a YOUR_REDIS_PASSWORD DEL "celery-rate-limit:apiCrm.fetch_all_data"
- Run task again
    docker exec -it k_celery_worker celery -A konquist call apiCrm.fetch_all_data
- TO SEE IT ALL: docker-compose logs -f

# Running commands
python manage.py runserver
celery -A konquist worker -l INFO
celery -A konquist beat -l INFO


docker exec -it konquest_django python manage.py shell

# Function to calculate the next runtime

from django_celery_beat.models import PeriodicTask
from datetime import datetime, timedelta
from celery.schedules import crontab

def get_next_runtime(cron_schedule, current_time):
    cron = crontab(
        minute=cron_schedule.minute,
        hour=cron_schedule.hour,
        day_of_week=cron_schedule.day_of_week,
        day_of_month=cron_schedule.day_of_month,
        month_of_year=cron_schedule.month_of_year,
    )
    remaining = cron.remaining_estimate(current_time)
    return remaining
    
current_time = datetime.utcnow()

for task in PeriodicTask.objects.all():
    if task.crontab:
        cron = task.crontab
        remaining_time = get_next_runtime(cron, current_time)
        remaining_hours = int(remaining_time.total_seconds() // 3600)
        remaining_minutes = int((remaining_time.total_seconds() % 3600) // 60)
        print(f"Name: {task.name}, Task: {task.task}, Next Runtime: {remaining_hours} hours and {remaining_minutes} minutes from now")
    else:
        print(f"Name: {task.name}, Task: {task.task}, Schedule: Interval or Not Set")