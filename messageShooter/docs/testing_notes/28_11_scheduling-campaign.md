Now that we have successfully created relationship between:
Whatsapp > Message > Counter > Campaign > Target List > Queue > Send Message

We need to validate and test DEEPLY the process of scheduling a campaign, including:
1 - Campaign Creation: are we missing any critical fields?
2 - Is the campaign generating target lists as expected?
3 - Is the timing from target list to queue working as expected?
4 - Is the SENDING of messages from the queue working as expected?

Let's find out!

# Campaign Scheduling Testing Notes
Date: November 28, 2023

## Overview
Testing the campaign scheduling functionality to ensure proper message delivery timing and campaign management.

## Test Environment
- Local Development Environment
- Django Admin Interface
- Database: PostgreSQL
- Python Version: 3.10
- Django Version: Latest

## Test Cases
## 28/11/2024
### 1. Campaign Creation
- [X] Create new campaign with basic information
- [X] Set campaign name and description
- [X] Upload target list
- [X] Configure message template
- [X] Validate all required fields
Tests:
[ok] a. Campaign is askign to select "Contacts:". Not needed to be here. The contacts will be auto generated as campaign runs and populates contact list
[ok] b. "Start time" and "Execution time" are duplicated. Since HH:MM is being set on Start time, execution time is not needed
[ok] c. Active Days should be a multi select field with the names of the days instead of numbers
[ok] d. Sequential Order should be easily editable. Since "Contact tag" equals to = "Relationship tag", we just need to exhibit existing dictionary structure showing "counter" number and "message.text" to easily validate
[ok] e. Last run and Next run don't need to appear on campaign creation
[ok] f. UserPhone should display the phone number instead of "UserPhone object (1)"
EXTRA ITEMS: 
[ok] g. create "Forms" and "Admin" directories for better organization
setup test data: python manage.py setup_test_data
[ok] h. re-think about "Sequential Order" field - all right, we killed it!
[ok] i. pytest updates (oh boy!): 165 passed, 4 errors 

## 29/11/2024
### 2. Schedule Configuration
- [X] Set start date and time
- [X] Set end date and time (optional)
- [X] Configure time zone settings
- [X] Set message sending intervals
- [X] Test schedule validation rules
Tests:
[] a. Create campaign with "Once" frequency
[ok] b. Create campaign with "Daily" frequency
[] c. Create campaign with "Weekly" frequency
[] d. Create campaign with "Monthly" frequency
[ok] e. Set Next run and execute run_scheduler
[ok] f. Make sure Campaign creates Target List
[ok] g. Make sure Target List creates Queue
[ok] h. Make sure Queue sends appropriate counter message

### 3. Target List Management
- [ ] Validate phone number formats
- [ ] Check duplicate entries handling
- [ ] Test target list updates
- [X] Verify contact information parsing

### 4. Message Template Testing
- [ ] Create message template
- [ ] Test variable substitution
- [ ] Verify character count limits
- [ ] Test emoji support
- [ ] Check URL shortening (if applicable)

### 5. Campaign Execution
- [ ] Test immediate start
- [ ] Test scheduled start
- [ ] Verify message queuing
- [ ] Monitor sending progress
- [ ] Check rate limiting compliance

### 6. Error Handling
- [ ] Invalid phone numbers
- [ ] Failed message delivery
- [ ] Network connectivity issues
- [ ] Rate limit exceeded scenarios
- [ ] Database connection issues

### 7. Monitoring and Reporting
- [ ] Campaign status updates
- [ ] Delivery statistics
- [ ] Error logs
- [ ] Performance metrics
- [ ] Export functionality

## Known Issues
1. TBD - Document any issues discovered during testing

## Next Steps
1. Complete initial testing phase
2. Document any bugs or issues
3. Create JIRA tickets for identified problems
4. Schedule follow-up testing session

## Notes
- Remember to test with different time zones
- Verify compliance with messaging regulations
- Test both small and large target lists
- Document any unexpected behavior

## Test Results
(To be filled in during testing)