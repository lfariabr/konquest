# December 2024 Sprint Completion Report

## Core Infrastructure Achievements
- Docker deployment pipeline established
  - Docker Compose setup with 7 containers
  - Successfully deployed to Digital Ocean droplet
  - DNS configuration completed

## Message Shooter System
- Campaign Management
  - create campaigns, target lists, queue 
  - possibility to schedule messages and send them asynchronously
  - feature/whatsapp-implementation
  - feature mockup setup_test_data to make process easier
  - feature enhancing message shooter speed processing at target list and queue process
  - fixed behavior between target campaign, targetlist and queue
  - implement campaign scheduler (run_scheduler)
  - implemented async calls to run multiple queues

- Message Handling
  - fixed sending images and photos on the messages
  - fixed counter (removed lead count from counter log) and timezone at database
  - custom messages @messageShooter/resolvers/get_message

## API CRM Integration
- Data Synchronization
  - apiCrm optimization to process data in batches
  - apiCrm optimization to check if lead or appointment exists (only pytest left)
  - delete data apiCrm
  - feature worker to see if contacts are leads or appointments in worker
  - feature worker to fetch data from apiCrm daily at midnight:15 BRT
  - Check Contact Bill Charges

## Campaign Implementation
- Campaign Types
  - Test deeply Appointment Campaigns
  - Run "Reminder" Campaign + "Reschedule" and "NPS"
  - Reminder and Reschedule Plastica
  - Reminder Plástica campaigns + Reschedule Plástica campaigns

## Performance & Optimization
- System Enhancements
  - Performance Boost
  - data migration implementing flask postgresql database
  - settings smart config to switch between sqlite and postgresql

## Data Management
- Data Operations
  - Import data from spreadsheet history rpdprocorpo@gmail.com
  - migrate data from ReschedulePL csvs
  - publicApi: update spreadsheet data so that marketing can have access to it

## Testing & Quality Assurance
- Testing Framework
  - first shooting @ 11/december/2024 - 60 contacts
  - check issue with get-message-pl **FIXED**

## Documentation
- System Documentation
  - dataWrestler: component that will have data displaying features such as tables, graphics, charts, etc

## Key Metrics
- First campaign: December 11, 2024 (60 contacts)

## Technical Tips
```bash
# Cache clearing
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
# Null contact names update
python manage.py update_null_contact_names --dry-run