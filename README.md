# Konquista
Enterprise WhatsApp Marketing Automation

## Overview
Konquista is an enterprise-grade WhatsApp marketing automation platform built with Django. It enables businesses to manage and automate customer communications through WhatsApp, integrating with CRM systems for lead management, appointment scheduling, and post-sale engagement.

## Core Features

### 1. Intelligent Message Management
- **Campaign Management**: Create and manage targeted WhatsApp campaigns with customizable schedules
- **Smart Targeting**: Filter contacts based on tags, appointment status, and customer journey stage
- **Dynamic Content**: Personalize messages with variables like customer name, appointment time, and location
- **Multi-Queue Processing**: Parallel message processing with rate limiting and error handling
- **File Support**: Send images, videos, and documents through WhatsApp

### 2. CRM Integration (apiCrm)
- **Real-time Sync**: Bi-directional sync with CRM for leads, appointments, and customer data
- **Automated Lead Management**: Track and update lead status automatically
- **Appointment Handling**: Manage appointment confirmations, reminders, and follow-ups
- **Payment Processing**: Track and manage bill charges and payment status

### 3. Message Shooter System
- **Campaign Engine**: 
  - Create and schedule targeted campaigns
  - Define execution times and active days
  - Set campaign frequencies (one-time, daily, weekly)
- **Target List Management**:
  - Dynamic contact filtering
  - Progress tracking
  - Message counter management
- **Queue Processing**:
  - Asynchronous message delivery
  - Rate limiting and retry logic
  - Error handling and logging

### 4. Core System
- **Contact Management**: 
  - Centralized contact database
  - Tag-based organization
  - History tracking
- **Message Templates**: 
  - Variable substitution
  - Multi-media support
  - Counter-based sequencing
- **User Management**:
  - Role-based access control
  - WhatsApp number management
  - Activity logging

### 5. Technical Features
- **GraphQL API**: Flexible data querying and manipulation
- **Asynchronous Processing**: Celery for task management
- **Caching**: Redis for performance optimization
- **Monitoring**: Comprehensive logging and error tracking
- **Testing**: Pytest-based test suite with mocking
- **Docker Support**: Containerized deployment with 7 containers

## Architecture
- Django + Celery + Redis stack
- PostgreSQL/SQLite database support
- Docker containerization
- GraphQL API layer
- Asynchronous task processing

## Deployment
The system runs in a containerized environment with:
- Django web server
- Celery workers
- Celery beat scheduler
- Redis cache
- PostgreSQL database
- Nginx reverse proxy
- Monitoring services

## Development Setup
### Prerequisites
- Python 3.10+
- Docker and Docker Compose
- Redis
- PostgreSQL (optional)

### Installation Instructions
```bash
# 1-Clone repository
git clone https://github.com/yourusername/konquista.git

# 2-Install dependencies
pip install -r requirements.txt

# 3-Run development server
python manage.py runserver

# 4-Start Celery worker
celery -A konquist worker -l INFO -Q default,contact_processor,campaign_queue,queue_processor

# 5-Start Celery beat
celery -A konquist beat -l INFO

# 6-Setup .env file - current structure

TOKEN=XXXXX # CRM Pró-Corpo - for apiCrm module
SECRET_KEY=XXXXX # Django

# Database - production (I used Supabase, which is FREE!)
DB_NAME=XXXX
DB_USER=XXXX
DB_PASSWORD=XXXX
DB_HOST=XXXX
DB_PORT=XXXX
URI=postgresql://XXXX
SUPABASE_URL=XXXX
SUPABASE_KEY=XXXXX

DATABASE_ENGINE=sqlite3 # use sqlite for dev


REDIS_HOST=localhost # Redis Info
REDIS_PORT=6379 
REDIS_DB=0
REDIS_PASSWORD=XXXXXXXX

# Don't use ${} syntax in .env files
CELERY_BROKER_URL=redis://:XXXXXXXX@localhost:6379/0
CELERY_RESULT_BACKEND=redis://:XXXXXXXX@localhost:6379/0
CACHE_LOCATION=redis://:XXXXXXXX@localhost:6379/1

EMAIL_PW=######## # Email Password to use google native
WEBHOOK_DISCORD=XXXXXXX

# 7-Change settings DATABASE_ENGINE to 'sqlite3' for dev
DATABASE_ENGINE = 'sqlite3'
```

### Docker Deployment
```bash
# Build and start containers
docker-compose up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Testing
```bash
# Run test suite
pytest

# Run with coverage
pytest --cov=.
```

## License
Luis Faria, Self-Made Software Engineer @ 2025. All rights reserved.

## Support
For support and inquiries, contact lfariabr@gmail.com
