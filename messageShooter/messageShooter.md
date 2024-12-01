# MessageShooter Documentation

## Overview
MessageShooter is a robust campaign management and message scheduling system designed to handle automated message distribution through various channels. The system supports campaign creation, target list management, message templating, and scheduled message delivery.

## Core Components

### 1. Campaign Management
- **Campaign Creation**: Define campaigns with specific goals and target audiences
- **Scheduling**: Set campaign start dates, end dates, and execution intervals
- **Status Tracking**: Monitor campaign progress and completion status

### 2. Target List Management
- **Contact Import**: Support for importing contact lists
- **Duplicate Handling**: Automatic detection and removal of duplicate entries
- **Contact Validation**: Verification of phone numbers and contact information
- **Relationship Tags**: Categorization of contacts based on relationship types

### 3. Message Templates
- **Template Creation**: Create reusable message templates
- **Variable Support**: Dynamic content insertion using variables
- **Character Limits**: Automatic validation of message length
- **Counter System**: Track message sequence numbers per relationship tag

### 4. Queue Processing
- **Queue Management**: Efficient processing of message queues
- **Rate Limiting**: Handle API rate limits and throttling
- **Error Handling**: Robust error management and retry mechanisms
- **Status Updates**: Real-time status tracking of message delivery

## Technical Implementation

### Models
1. **Campaign**
   - Title, description, status
   - Schedule configuration
   - Target list associations

2. **TargetList**
   - Contact information
   - Campaign association
   - Relationship tags
   - Duplicate handling logic

3. **Message**
   - Template content
   - Variable placeholders
   - Counter tracking
   - Character limit validation

4. **MessageLogs**
   - Delivery status
   - Timestamp information
   - Error tracking
   - Performance metrics

### Key Features
1. **Scheduling System**
   - Cron-based execution
   - Configurable intervals
   - Priority handling

2. **Contact Management**
   - Phone number validation
   - Duplicate detection
   - Relationship tagging

3. **Message Processing**
   - Template rendering
   - Counter management
   - Queue optimization

## Usage Guidelines

### Campaign Setup
1. Create a new campaign
2. Define schedule parameters
3. Upload or select target list
4. Choose message template
5. Configure counters and tags
6. Activate campaign

### Target List Management
1. Prepare contact data
2. Import contacts
3. Verify duplicate handling
4. Assign relationship tags
5. Review final list

### Message Template Creation
1. Write template content
2. Add variable placeholders
3. Verify character limits
4. Test template rendering

## Best Practices

1. **Campaign Planning**
   - Plan campaigns in advance
   - Set realistic schedules
   - Monitor rate limits

2. **Contact Management**
   - Regular list cleanup
   - Validate contact data
   - Update relationship tags

3. **Message Design**
   - Keep messages concise
   - Test all variables
   - Verify counter logic

4. **Performance Optimization**
   - Monitor queue size
   - Track delivery rates
   - Optimize processing intervals

## Troubleshooting

### Common Issues
1. **Queue Processing**
   - Rate limit exceeded
   - Database connection issues
   - Template rendering errors

2. **Contact Management**
   - Duplicate entries
   - Invalid phone numbers
   - Missing relationship tags

3. **Campaign Execution**
   - Scheduling conflicts
   - Counter synchronization
   - Template variables not resolved

### Solutions
1. **Queue Issues**
   - Implement exponential backoff
   - Monitor connection pool
   - Validate template data

2. **Contact Problems**
   - Enhanced validation
   - Automated cleanup
   - Tag verification

3. **Campaign Fixes**
   - Schedule verification
   - Counter reset options
   - Template testing

## Monitoring and Reporting

### Key Metrics
1. **Campaign Performance**
   - Delivery rates
   - Error rates
   - Processing times

2. **System Health**
   - Queue size
   - Processing speed
   - Resource usage

3. **Contact Analytics**
   - List growth
   - Tag distribution
   - Engagement rates

### Reporting Tools
1. **Dashboard**
   - Real-time monitoring
   - Performance graphs
   - Status updates

2. **Export Options**
   - Campaign reports
   - Delivery logs
   - Analytics data

## Future Enhancements

1. **Planned Features**
   - Advanced scheduling options
   - Enhanced template editor
   - Improved analytics

2. **Performance Improvements**
   - Queue optimization
   - Batch processing
   - Caching strategies

3. **Integration Options**
   - Additional channels
   - API extensions
   - Third-party services

___**Please note that this is a work in progress and is subject to change.**___

# Goal
Process messages from core>message into queue and send using social hub API according to Campaign Rules

# Details of usage:
- core
-- to get contacts, messages, phone_token
- apiCrm
-- to check if these contacts are leads, appointments or buyers
- apiSocialHub
-- to send messages to contacts

# What it will serve back to the app
- core
-- message logs with status and sent_at

# Step by step
1. Have contacts, messages, phone_token using setup_test_data
2. Run_scheduler to generate target lists out of campaigns
3. Check it target lists are created and sent to Queue
4. Monitore Queue processing to send messsages
5. Verify that messages are sent on the console log and saved at Core>message Logs

# Future ideas
- Machine learnign to understand patterns: more messages = more contacts that are appointment or that buy?
- AB testing of message templates, time and frequency
- Allow users to schedule messages like offering Indique Multiplique to clients that were appointments in certain status or interval
- Allow users to create a monthly campaign to send _PROMO_ message to certain types of billcharges, like who bought more than R$ 1000 in a month

# NOW
1. Queue Processing Fix:
Fix that one queue item should be the queue itself, not the target list individuals: This is crucial for ensuring the correct functionality of your queue processing. Fixing this will likely resolve related issues and improve overall system reliability.

2. Duplicate Handling:
Check duplicate entries handling: Ensure that duplicates are eliminated when creating the target list. This is important to maintain data integrity and prevent redundant processing.
3. Counter Updates:
Check counter updates at different relationship tags on the messages: Verify that counters are correctly updated for different relationship tags to ensure accurate message sequencing.
4. Error Handling and Stability:
Rate limit exceeded scenarios: Implement handling for rate limits to prevent disruptions in message sending.
Database connection issues: Ensure robust handling of database connection issues to prevent data loss or corruption.
5. Monitoring and Reporting:
Campaign status updates: Implement real-time updates for campaign statuses to provide accurate feedback to users.
6. Delivery statistics: Track and report on message delivery statistics to assess campaign effectiveness.
Performance metrics: Monitor system performance to identify bottlenecks and optimize resource usage.
Export functionality: Enable data export features for reporting and analysis.