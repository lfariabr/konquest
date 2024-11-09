# Konquista Django App

## Goal
The Konquista Django App is designed to manage CRM-related data.
It is a system that focus on sending customized WhatsApp Messages for contacts, whether they're contacts from WhatsApp, Leads and/or Appointments. It integrates with Celery and Redis to support asynchronous task processing and scheduled data cleanup. The application also includes a GraphQL API for easy querying and interaction with all the data available.
On the frontend, using Django Admin, the App has a SaaS to manage contacts, messages, sent_messages, manage rules, shoot new messages.

## Run Server + Worker + Beat
To start the Django server, Celery worker, and Celery Beat for scheduled tasks, use the following commands:

python manage.py runserver
celery -A konquist worker -l info
celery -A konquist beat -l info

## Overview
Konquista is a Django project configured with Celery and Redis to handle asynchronous and periodic tasks. The main functionality is to manage and periodically clean up leads data, utilizing GraphQL for querying and fetching data.

## Key Features
1. **Lead and Appointment Management:**
   - Fetches and temporarily stores lead and appointment data in the database.
	- Uses Lead and Appointment models that include fields for CRM data, customer information, and UTM tracking details.

2.	**WhatsApp Messaging System:**
   - Enables sending customized WhatsApp messages to contacts from various sources.
   - Provides rule-based management for targeting specific contacts.

3.	**GraphQL API:**
   - Powered by the graphene library, allowing efficient GraphQL querying.
   - Provides custom types (LeadType, AppointmentType) and resolvers in the Query class to retrieve and manage leads and appointments.

4.	**Django Rest Framework:**
   - In usage to provide a different alternative for accessing data endpoints from our app.
   - Provides possibility to check Leads, will eventually allow to grab more data from API.

4.	**Asynchronous Task Processing:**
   - Configured with Celery to handle background tasks, such as fetching data and sending WhatsApp messages.
   - Redis acts as the message broker, queuing tasks for processing.

5.	**Scheduled Data Cleanup:**
	- The clean_up_leads task deletes old lead records periodically, managed by Celery Beat to keep the database organized.
   
## Setup and Installation

### Requirements
- Python 3.10+
- Django 3.x or 4.x
- Celery 5.x
- Redis

### Install Dependencies
```bash
pip install -r requirements.txt
pip freeze > requirements.txt