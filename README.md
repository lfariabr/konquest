# Konquista
> Enterprise WhatsApp Marketing Automation Platform

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.1+-green.svg)](https://djangoproject.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview
Welcome to Konquista. This is an enterprise-grade WhatsApp marketing automation platform built with Django. It enables businesses to manage and automate customer communications through WhatsApp, integrating with CRM systems for lead management, appointment scheduling, and post-sale engagement.

## Business Impact & Value Proposition

- 20+ stores actively using it
- 100K+ contacts managed
- 250K+ WhatsApp messages sent (30K+/month)

## Fun Fact
https://dev.to/lfariaus/from-google-sheets-to-a-scalable-saas-building-konquista-with-python-and-django-46mh

## Version Control Strategy
Following **GitFlow** with feature branches and semantic versioning:

| Version | Milestone | Status | When |
|---------|-----------|--------|------|
| **0.0.0** | module *core + konquista setup* | ✅ Complete | Oct 2024 |
| **1.0.0** | module *apiCrm* | ✅ Complete | Nov 2024 |
| **2.0.0** | module *apiSocialHub* | ✅ Complete | Nov 2024 |
| **3.0.0** | module *messageShooter* | ✅ Complete | Dec 2024 |
| **4.0.0** | module *dataWrestler* | ✅ Complete | Dec 2024 |
| **5.0.0** | module *publicApi* | ✅ Complete | Jun 2025 |
| **6.0.0** | module *analytics* (reporting API + email) | 🔄 Planned | TBD |
| **tbd** | Github Actions for automatic deployment @ droplet | 🔄 Planned | TBD |
| **tbd** | AI Enhanced matching | 🔄 Planned | TBD |
| **tbd** | Multi-tenant architecture | 🔄 Planned | TBD |
| **tbd** | Stripe integration | 🔄 Planned | TBD |
| **tbd** | Webhook system for external integrations vs Django Signals | 🔄 Planned | TBD |

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

### 5. Public API
- **MessageLogs**: Track message delivery and status
- **Contacts**: Manage contact information and history

### 6. Technical Features
- **GraphQL API**: Flexible data querying and manipulation
- **Django Rest Framework**: RESTful API for CRM and Message Shooter
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
- Django Rest Framework for API endpoints
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
git clone https://github.com/yourusername/konquest.git

# 2-Install dependencies
pip install -r requirements.txt

# 3-Run development server
python manage.py runserver

# 4-Start Celery worker
celery -A konquist worker -l INFO -Q default,contact_processor,campaign_queue,queue_processor

# 5-Start Celery beat
celery -A konquist beat -l INFO

# 6-Setup .env file - current structure
@ env.example

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

## Support
For support and inquiries, contact lfariabr@gmail.com