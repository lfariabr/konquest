# Konquista Django App

## Commands
python manage.py runserver
celery -A konquist worker -l INFO
celery -A konquist beat -l INFO

## Goal
Konquista Django App is designed to manage CRM-related data.
It is a system that focus on sending customized WhatsApp Messages for contacts, whether they're contacts from WhatsApp, Leads and/or Appointments. It integrates with Celery and Redis to support asynchronous task processing and scheduled data cleanup. The application also includes a GraphQL API for easy querying and interaction with all the data available.
On the frontend, using Django Admin, the App has a SaaS to manage contacts, messages, sent_messages, manage rules, shoot new messages.

## Run Server + Worker + Beat
To start the Django server, Celery worker, and Celery Beat for scheduled tasks, use the following commands:

## Overview
Konquista is a Django project configured with Celery and Redis to handle asynchronous and periodic tasks efficiently. It leverages GraphQL for dynamic querying and fetching data, and aiohttp for managing asynchronous HTTP requests within the application. This setup is designed to manage and periodically clean up leads data, ensuring high performance and scalability.

## Key Features
1. Organized Codebase Structure
- Modular Design: The application is organized into dedicated folders for models, schemas, resolvers, and tests.
- Models: Encapsulate CRM data, customer information, and UTM tracking details for organized data management.
- Schemas: Define GraphQL types and mutations using graphene-django.
- Resolvers: Contain the logic for fetching and processing data, ensuring a clean separation of concerns.
- Tests: Located in a specific folder, tests are split in a robust way to cover core functionalities.

2. Lead, Appointment, and Buyer Management
- Data Fetching: Concurrently fetches and temporarily stores leads, appointments, and buyers data in the database.
- Asynchronous Operations: Utilizes aiohttp and asyncio for efficient asynchronous HTTP requests and data fetching.
- Data Processing: Formats and processes data using serializers and custom utility functions.

3. WhatsApp Messaging System
- Automated Messaging: Sends customized WhatsApp messages to contacts based on specified rules.
    - Support for sending both **text messages** and **file messages** through SocialHub.
- Rule-Based Management: Enhances marketing efforts by targeting specific contacts through rule management.
    - Comprehensive logging with dedicated log files (`send_text_message.log` and `send_file_message.log`) to track message dispatches and errors.
    - Django Admin integration for managing and tracking sent messages directly from the interface.
- Message Tracking: Keeps track of sent messages, allowing for analytics and follow-up actions.

4. GraphQL API Integration
- Dynamic Querying: Uses graphene-django to create a robust GraphQL interface for efficient data retrieval.
- Custom Types and Resolvers: Includes custom types (LeadType, AppointmentType, BillChargeType, AllDataType) and resolvers within the Query class.
- Asynchronous Data Fetching: Integrates aiohttp within GraphQL operations to perform asynchronous data fetches, improving data retrieval efficiency from external APIs.

5. Asynchronous Task Processing with Celery
- Background Tasks: Manages background tasks such as data fetching and message dispatch using Celery.
- Redis Integration: Uses Redis as a message broker to queue tasks, enabling asynchronous task processing and scheduling.
- Scheduled Tasks: Implements periodic tasks for data cleanup and maintenance using Celery Beat.

6. Scheduled Data Cleanup
- Database Optimization: Periodically cleans up outdated records to maintain database integrity and performance.
- Clutter-Free System: Ensures the system remains efficient by deleting unnecessary data.

7. Comprehensive Testing Suite
- Pytest for Testing: Utilizes Pytest for powerful and straightforward syntax to handle unit tests and complex functional testing.
- Test Coverage on Core Features: Focuses on testing critical components like fetching all data and resolving all data.
- Mocking and Isolation: Ensures tests do not send real HTTP requests by mocking network interactions, leading to reliable and fast test execution.
- Asynchronous Testing: Handles asynchronous code testing effectively, avoiding common pitfalls like TypeError related to asynchronous context managers.

# Done
- messageShooter: create campaigns, target lists, queue 
- possibility to schedule messages and send them asynchronously
- feature/whatsapp-implementation
- feature mockup setup_test_data to make process easier
- feature enhancing message shooter speed processing at target list and queue process
- fixed behavior between target campaign, targetlist and queue
- implement campaign scheduler (run_scheduler)
- implemented async calls to run multiple queues
- data migration implementing flask postgresql database
- settings smart config to switch between sqlite and postgresql
- first shooting @ 11/december/2024 - 60 contacts
- fixed sending images and photos on the messages
- fixed counter (removed lead count from counter log) and timezone at database
- apiCrm optimization to process data in batches
- apiCrm optimization to check if lead or appointment exists (only pytest left)
- update images and videos + last trial and commit
- feature/appointment-implementation
- custom messages @messageShooter/resolvers/get_message
- delete data apiCrm
- feature worker to see if contacts are leads or appointments in worker
- feature worker to fetch data from apiCrm daily at midnight:15 BRT
- Check Contact Bill Charges

# In progress
- Run "Reminder" Campaign

## Backlog:
- dataWrestler: component that will have data displaying features such as tables, graphics, charts, etc
- publicApi: component that will serve existing graphQL api with MessageLogs based on reference_id

## Setup and Installation
### Requirements
- Python: 3.10+
- Django: 4.x
- Celery: 5.x
- Redis: For message brokering and task queuing
- aiohttp: For asynchronous HTTP requests handling
- Graphene-Django: For GraphQL API functionality
- Pytest: For test-driven development (TDD)

### Install Dependencies
```bash
pip install -r requirements.txt
pip freeze > requirements.txt