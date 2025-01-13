# Docker
- Stop all containers: docker stop $(docker ps -a -q) && docker rm $(docker ps -a -q)

- Create / Navigate to directory for Konquest
    mkdir -p /var/www/konquest
    cd /var/www/konquest
    git clone https://github.com/lfariabr/konquest.git
    cd konquest
    docker-compose build
    docker-compose down
    docker-compose up --build -d

- check running containers
    docker logs -f k_celery_beat
    docker logs -f k_celery_worker
    docker logs -f konquest_django
    docker-compose logs -f

- droplet
    ssh root@209.38.90.25
    cd /var/www/konquest
    docker-compose build --no-cache
    docker-compose up -d

## Docker useful commands

### View all active tasks
docker exec k_celery_worker celery -A konquist inspect active

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


# Simple way:
from konquist.celery import app
app.conf.beat_schedule


# When a task is running nonstop in restart: 
docker stop k_celery_beat

# Stop the worker
docker stop k_celery_worker

# Start the worker
docker start k_celery_worker

# Purge all pending tasks
docker exec k_celery_worker celery -A konquist purge -f

# Restart the beat
docker start k_celery_beat

docker exec -it konquest_django python manage.py shell
from django_celery_beat.models import PeriodicTask, CrontabSchedule; [(lambda t: setattr(t, 'crontab', CrontabSchedule.objects.get_or_create(minute=m, hour=h, day_of_week='*', day_of_month='*', month_of_year='*', timezone='America/Sao_Paulo')[0]) or t.save())(PeriodicTask.objects.get(name=name)) for name, m, h in [('check_contacts_in_crm', '0', '2'), ('process-campaigns', '0', '4'), ('process_queues', '15', '7')]]

# check
[print(f"{t.name}: {t.crontab}") for t in PeriodicTask.objects.all()]

check last run schedule:
docker exec -it konquest_django python manage.py shell -c "from django_celery_beat.models import PeriodicTask; [print(f'{t.name}: {t.enabled}, {t.crontab}, Last Run: {t.last_run_at}') for t in PeriodicTask.objects.all()]"

docker exec konquest_django python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
tasks = PeriodicTask.objects.all()
for task in tasks:
    print(f'\nTask: {task.name}')
    print(f'Path: {task.task}')
    print(f'Schedule: {task.crontab}')
    print(f'Enabled: {task.enabled}')
    print('-' * 50)
"

## Permission Handling 14/01

To prevent permission issues with Docker volumes and logs:

1. The application runs as `appuser` (UID 1000, GID 1000) inside containers
2. All required directories are created during image build with proper permissions:
   - `/app/apiSocialHub/logs`: 775 permissions
   - `/app/logs`: 775 permissions
3. Volume mounts in docker-compose.yml use `:rw` flag and explicit user mapping
4. If permission issues occur on a new deployment, run:
   ```bash
   sudo chown -R 1000:1000 apiSocialHub/logs/* logs/*
   sudo chmod -R 775 apiSocialHub/logs logs

# Create directories and set permissions before switching to appuser
RUN mkdir -p /app/apiSocialHub/logs && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app && \
    chmod -R 775 /app/apiSocialHub/logs && \
    chmod -R 775 /app/logs

# Switch to non-root user
USER appuser

{{ ... }}
    volumes:
      - ./apiSocialHub:/app/apiSocialHub:rw
      - ./logs:/app/logs:rw
      - ./static:/app/static:rw
      - ./media:/app/media:rw
    user: "1000:1000"  # Explicitly set user to match appuser
{{ ... }}

### Quick Permission Fix
If you encounter permission issues, just run:
```bash
sudo chown -R root:root .
sudo chmod -R 775 .
```

This works because our container's appuser is part of the root group and directories are group-writable.