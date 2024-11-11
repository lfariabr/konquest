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
Konquista is a Django project configured with Celery and Redis to handle asynchronous and periodic tasks efficiently. It leverages GraphQL for dynamic querying and fetching data, and aiohttp for managing asynchronous HTTP requests within the application. This setup is designed to manage and periodically clean up leads data, ensuring high performance and scalability.

## Key Features
1. **Lead and Appointment Management:**
   - Fetches and temporarily stores leads, appointment and buyers data in the database.
   - Uses models to encapsulate CRM data, customer information, and UTM tracking details, facilitating easy and organized data management.

2. **WhatsApp Messaging System:**
   - Enables automated and customized WhatsApp messaging to contacts based on specified rules.
   - Utilizes rule-based management to target specific contacts, enhancing marketing efforts.

3. **GraphQL API Integration:**
   - Utilizes the Graphene-Django library to create a robust GraphQL interface.
   - Includes custom types (LeadType, AppointmentType) and resolvers within the Query class for efficient data retrieval and management.
   - Integrates aiohttp within GraphQL operations to perform asynchronous data fetches, improving data retrieval efficiency from external APIs.

4. **Django Rest Framework Integration:**
   - Employs Django Rest Framework for a versatile API endpoint access, supporting both RESTful and GraphQL queries.
   - Enhances data accessibility and interaction capabilities within the app, allowing for extensive data operations and management.

5. **Asynchronous Task Processing with Celery:**
   - Uses Celery for managing background tasks, such as data fetching and message dispatch, which are crucial for maintaining application responsiveness and efficiency.
   - Redis is used as a message broker to queue tasks, enabling asynchronous task processing and scheduling.

6. **Scheduled Data Cleanup:**
   - Implements periodic cleanup tasks to manage database integrity and performance, using Celery Beat for scheduling.
   - Deletes outdated records and optimizes database usage, ensuring the system remains efficient and clutter-free.

* **Extra Cool Features**
   - Pytest: We utilize Pytest for our backend testing, valuing its powerful yet straightforward syntax and ability to handle both simple unit tests and complex functional testing.

## Setup and Installation

### Requirements
- Python 3.10+
- Django 3.x or 4.x
- Celery 5.x
- Redis
- aiohttp for asynchronous HTTP requests handling
- Graphene-Django for GraphQL API functionality
- Pytest for TDD

### Install Dependencies
```bash
pip install -r requirements.txt
pip freeze > requirements.txt