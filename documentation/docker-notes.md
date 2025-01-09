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
docker exec -it k_celery_worker celery -A konquist inspect active

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
from django_celery_beat.models import PeriodicTask, CrontabSchedule
print("\nUpdated schedule:")
for task in PeriodicTask.objects.all():
    print(f"Name: {task.name}, Task: {task.task}, Schedule: {task.crontab if task.crontab else task.interval}")

# UPDATES TO THE SCHEDULE AND TASKS:

from django_celery_beat.models import PeriodicTask, CrontabSchedule

# 1. Delete celery.backend_cleanup
PeriodicTask.objects.filter(task='celery.backend_cleanup').delete()

# 2. Update cleanup_crm_tables to 19:30 (7:30 PM)
cleanup_crontab = CrontabSchedule.objects.get_or_create(
    minute='30', hour='19', day_of_week='*', day_of_month='*', month_of_year='*', timezone='America/Sao_Paulo'
)[0]
PeriodicTask.objects.filter(task='apiCrm.cleanup_crm_tables').update(crontab=cleanup_crontab)

# 3. Update fetch_all_data to 12:05 (0:05 PM)
fetch_crontab = CrontabSchedule.objects.get_or_create(
    minute='05', hour='12', day_of_week='*', day_of_month='*', month_of_year='*', timezone='America/Sao_Paulo'
)[0]
PeriodicTask.objects.filter(task='apiCrm.fetch_all_data').update(crontab=fetch_crontab)

# 4. Update check_contacts_in_crm to 02:00 AM
check_crontab = CrontabSchedule.objects.get_or_create(
    minute='0', hour='2', day_of_week='*', day_of_month='*', month_of_year='*', timezone='America/Sao_Paulo'
)[0]
PeriodicTask.objects.filter(task='apiCrm.check_contacts_in_crm').update(crontab=check_crontab)

# 5. Update process_scheduled_campaigns to 05:00 AM
campaign_crontab = CrontabSchedule.objects.get_or_create(
    minute='0', hour='5', day_of_week='*', day_of_month='*', month_of_year='*', timezone='America/Sao_Paulo'
)[0]
PeriodicTask.objects.filter(task='apiCrm.process_scheduled_campaigns').update(crontab=campaign_crontab)

# 6. Update process_queues to 07:30 AM
queue_crontab = CrontabSchedule.objects.get_or_create(
    minute='30', hour='7', day_of_week='*', day_of_month='*', month_of_year='*', timezone='America/Sao_Paulo'
)[0]
PeriodicTask.objects.filter(task='queue.process_queues').update(crontab=queue_crontab)

# Verify the changes
from django_celery_beat.models import PeriodicTask, CrontabSchedule
print("\nUpdated schedule:")
for task in PeriodicTask.objects.all():
    print(f"Name: {task.name}, Task: {task.task}, Schedule: {task.crontab if task.crontab else task.interval}")