# Docker
- Create / Navigate to directory for Konquest
    mkdir -p /var/www/konquest
    cd /var/www/konquest

- Clone your Repository
    git clone https://github.com/lfariabr/konquest.git

- Navigate into the cloned directory
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

## Docker useful commands

### View all active tasks
docker exec -it k_celery_worker celery -A konquist inspect active

### View scheduled tasks
docker exec -it k_celery_worker celery -A konquist inspect scheduled

### View registered tasks
docker exec -it k_celery_worker celery -A konquist inspect registered

### Clear the Redis lock
docker exec -it k_redis redis-cli -p 6380 -a YOUR_REDIS_PASSWORD DEL fetch_all_data_lock

### Clear the rate limit
docker exec -it k_redis redis-cli -p 6380 -a YOUR_REDIS_PASSWORD DEL "celery-rate-limit:apiCrm.fetch_all_data"
- Run task again
    docker exec -it k_celery_worker celery -A konquist call apiCrm.fetch_all_data
- Pitch Deck to earn my raise
- TO SEE IT ALL: docker-compose logs -f

# Running commands
python manage.py runserver
celery -A konquist worker -l INFO
celery -A konquist beat -l INFO