# Job to be done feature/queue-integration

# Please read through testing notes from 23_11_shooter_architecture.md and 24_11_shoot_messages.md to better understand what has been done.
# It is crucial to point out that this system is a work in progress of a huge software engineer project that will become a SaaS and make us earn a lot of money due to its simplicity and high performance.

# We are at the feature/queue-integration stage, which happens after we:

# - created apiCrm to grab data from existing system
# - created core to have users, messages, contacts, admin, message logs
# - created apiSocialHub to send messages via SocialHub, our partner
# - created (in progress) messageShooter to create campaigns, queues, target lists and send messages
# - we'll create dataWrestler component to serve data from core to users and provide relevant insights
# - we'll create publicApi component to serve existing graphQL api with MessageLogs based on reference_id
# - we'll create genAi component to analyze data and create new messages, tests A/B, variation, frequency

# for item in progress at messageShooter, we need to organize the hierarchy between Queue, Campaign, TargetList and Token. For better context, here's the function of each:
# - Queue: represents ONE message to ONE recipient using ONE token
# - Campaign: represents one set of rules that apply for each token (counter, frequency, time, relationship tag)
# - TargetList: represents a list of recipients elligible to receive messages from a campaign
# - UserPhone: represents a token that can be used to send messages

# The goal of this part is to have its separate parts.
# Next desired steps are:
# - If Campaign is frequency = Once, it should create a target list accordingly to its rules. Then this campaign should appear on queue and be processed when we want to.
# - If Campaign is frequency = Daily, it should create a target list too every day at X time. This means creating target list to receive messages. Then this campaign should appear on queue and be processed when we want to. 
# The idea is that "target list" will be unique for each campaign/token and will have its own queue entries. We'll have multiple queues running everyday.abs

# On the current scenario with Botox and Preenchimento, we will have 2 Campaigns that will be triggered Daily (from monday to saturday) at 8am BRT. 
# Each time they run, they'll create 2 Target Lists (one for Botox and one for Preenchimento) and 2 Queue Entries (one for each Target List).
# Each Queue will have a list of Target Lists to process. Each list will have Contacts and Messages to be processed according to resolvers rule (each 7 seconds..)
# Each queue needs to be able to be processed async

Technical Briefing: MessageShooter Queue Integration
=================================================

Architecture Analysis
-------------------

1. Component Hierarchy and Relationships:

Campaign (1) ---> (n) TargetList (1) ---> (n) Queue
UserPhone (1) ---> (n) Campaign
Message (1) ---> (n) Queue

Key Observations:
- Campaign is the top-level entity that orchestrates message delivery
- Each Campaign can have multiple TargetLists (e.g., daily lists)
- Each TargetList generates multiple Queue entries
- UserPhone (token) is associated with Campaign for authentication
- Message content is linked to Queue for actual delivery

2. Data Flow:

Campaign Creation:
    Campaign(frequency="daily", time="08:00", tag="Botox")
    └── Scheduled Task (Celery)
        └── Daily Target List Generation
            └── Queue Entry Creation
                └── Message Processing (async)

3. Critical Components:

a) Campaign Manager:
   - Handles campaign scheduling
   - Manages frequency rules
   - Validates token associations

b) Target List Generator:
   - Creates recipient lists based on campaign rules
   - Handles filtering and segmentation
   - Maintains sent message history

c) Queue Processor:
   - Asynchronous message sending
   - Rate limiting (7-second intervals)
   - Error handling and retries
   - Status tracking

4. Technical Requirements:

Database:
- Campaign: frequency, timing, status, rules
- TargetList: campaign_id, contacts, date
- Queue: target_list_id, message_id, status, retries
- MessageLog: queue_id, status, response

Celery Tasks:
- create_daily_target_lists (8 AM trigger)
- process_queue_entries (continuous)
- cleanup_old_entries (daily)

API Endpoints:
- /campaign/create
- /campaign/status
- /queue/process
- /logs/view

Implementation Strategy
----------------------

1. Phase 1: Core Structure
   - Enhance Campaign model with frequency/timing
   - Implement TargetList generation logic
   - Test Target List generation logic
    - changed target list model
    - changed campaign model
    - changed target list resolver
    # Target List Generation System Changes:
    # 1. Campaign Model Enhancements:
    #    - Added should_run_today() method to check campaign's active days
    #    - Implemented is_ready_to_run() to validate campaign status and timing
    #    - Added execution_time field for precise scheduling
    #    - Added active_days field to specify which days the campaign should run
    #
    # 2. Target List Model Updates:
    #    - Added contact ForeignKey for proper relationship with contacts
    #    - Improved fields structure with contact_type and contact_tag
    #    - Added status tracking for pending/processing/completed states
    #    - Added relationship with UserPhone and Message models
    #
    # 3. Target List Resolver Improvements:
    #    - Implemented generate_target_lists() for processing all active campaigns
    #    - Added proper contact filtering based on campaign settings
    #    - Added message frequency validation using MessageLogs
    #    - Improved error handling and logging for better debugging
    #    - Added timezone awareness for proper datetime handling
    #
    # 4. Testing Infrastructure:
    #    - Created comprehensive test suite for target list generation
    #    - Added tests for campaign status validation
    #    - Added tests for active days validation
    #    - Used freezegun for time-dependent testing
    #    - Ensured proper timezone handling in tests
   - Set up basic queue processing

2. Phase 2: Scheduling
   - Configure Celery for daily tasks
   - Implement campaign scheduling
   - Add retry mechanisms

3. Phase 3: Monitoring
   - Add comprehensive logging
   - Create monitoring dashboard
   - Implement alerts

4. Phase 4: Optimization
   - Add caching layer
   - Optimize database queries
   - Implement batch processing

Testing Strategy
---------------

1. Unit Tests:
   - Campaign creation/validation
   - Target list generation
   - Queue processing logic

2. Integration Tests:
   - End-to-end campaign flow
   - Scheduling accuracy
   - Error handling

3. Load Tests:
   - Multiple concurrent campaigns
   - High-volume message processing
   - Rate limiting verification

Risk Assessment
--------------

1. Technical Risks:
   - Database bottlenecks
   - Message delivery delays
   - Token authentication issues

2. Mitigation Strategies:
   - Implement connection pooling
   - Add message queuing
   - Regular token validation

Next Steps
---------

1. Immediate:
   - Update Campaign model
   - Create scheduling infrastructure
   - Implement basic queue processing

2. Short-term:
   - Add monitoring
   - Enhance error handling
   - Implement retries

3. Long-term:
   - Scale horizontally
   - Add analytics
   - Implement A/B testing