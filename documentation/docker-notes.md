# Docker
- Stop all containers: docker stop $(docker ps -a -q) && docker rm $(docker ps -a -q)

# 1. Clone and build
rm -rf konquest
cd /var/www/konquest
git clone https://github.com/lfariabr/konquest.git
cd konquest
docker-compose build

# 2. Controlled shutdown
docker-compose down

# 3. Start core services first
docker-compose up -d redis django

# 4. Start worker without tasks
docker-compose up -d celery_worker

# 5. Start remaining services (except beat)
docker-compose up -d redis_commander nginx certbot

# 6. Finally, start beat after everything is stable
docker-compose up -d celery_beat

- check running containers
    docker logs -f k_celery_beat
    docker logs -f k_celery_worker
    local: celery -A konquist worker -l INFO -Q default,contact_processor,campaign_queue,queue_processor
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
docker exec -it k_celery_worker celery -A konquist inspect registered

### Instant run tasks
docker exec -it k_celery_worker celery -A konquist call apiCrm.tasks.cleanup_crm_tables
docker exec -it k_celery_worker celery -A konquist call apiCrm.tasks.fetch_all_data

docker exec -it k_celery_worker celery -A konquist call core.tasks.check_contacts_in_crm

docker exec -it k_celery_worker celery -A konquist call messageShooter.tasks.run_daily_organizer
docker exec -it k_celery_worker celery -A konquist call messageShooter.tasks.process_scheduled_campaigns
docker exec -it k_celery_worker celery -A konquist call messageShooter.tasks.process_queues

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

# Permission Handling 20/01

sudo chown -R 1000:1000 apiSocialHub/logs/* logs/*
sudo chmod -R 775 apiSocialHub/logs logs

docker-compose build --no-cache

### 'Task already running'
#### Enter the Django shell in the celery worker container
docker exec -it k_celery_worker python manage.py shell

#### Then in the Python shell, run these commands:
from django.core.cache import cache
cache.delete("fetch_all_data_lock")
exit()