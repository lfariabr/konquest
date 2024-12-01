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

## Test Cases
## 28/11/2024
### 1. Campaign Creation
- [X] Create new campaign with basic information
- [X] Set campaign name and description
- [X] Upload target list
- [X] Configure message template
- [X] Validate all required fields
- [X] a. Campaign is askign to select "Contacts:". Not needed to be here. The contacts will be auto generated as campaign runs and populates contact list
- [X] b. "Start time" and "Execution time" are duplicated. Since HH:MM is being set on Start time, execution time is not needed
- [X] c. Active Days should be a multi select field with the names of the days instead of numbers
- [X] d. Sequential Order should be easily editable. Since "Contact tag" equals to = "Relationship tag", we just need to exhibit existing dictionary structure showing "counter" number and "message.text" to easily validate
- [X] e. Last run and Next run don't need to appear on campaign creation
- [X] f. UserPhone should display the phone number instead of "UserPhone object (1)"
EXTRA ITEMS: 
- [X] g. create "Forms" and "Admin" directories for better organization
setup test data: python manage.py setup_test_data
- [X] h. re-think about "Sequential Order" field - all right, we killed it!
- [X] i. pytest updates (oh boy!): 165 passed, 4 errors 

## 29/11/2024
### 2. Schedule Configuration
- [X] Set start date and time
- [X] Set end date and time (optional)
- [X] Configure time zone settings
- [X] Set message sending intervals
- [X] Test schedule validation rules
Tests:
[X] a. Create campaign with "Once" frequency
[X] b. Create campaign with "Daily" frequency
[X] c. Create campaign with "Weekly" frequency
[X] d. Create campaign with "Monthly" frequency
[X] e. Set Next run and execute run_scheduler
[X] f. Make sure Campaign creates Target List
[X] g. Make sure Target List creates Queue
[X] h. Make sure Queue sends appropriate counter message?

# 30/11/2024
### 3. Target List Management
- [X] Validate phone number formats
- [X] Verify contact information parsing
- [X] a. Message logss to Message Log
- [X] b. Message Logs display Text Message instead of "Message object (1)"
- [X] c. Message Logs display "UserPhone" instead of "UserPhone object (1)"
- [X] d. Message Logs display "Phone Number" of contact instead of "Contact object (1)"
- [X] Test target list updates
- [ ] Check duplicate entries handling - FAILED. Should eliminate duplicates when creating the target list
- [ ] Check counter updates at different relationship tags on the messages

### 4. Message Template Testing
- [X] Create message template
- [X] Verify character count limits
- [X] Test emoji support
- [ ] Test variable substitution - only in appointment

### 5. Campaign Execution
- [X] Test immediate start
- [ ] Test scheduled start
- [ ] Verify message queuing
- [ ] Monitor sending progress (put 2 contacts and see if both target lists are working)
- [ ] Check rate limiting compliance

### 6. Error Handling
- [ ] Invalid phone numbers
- [ ] Failed message delivery
- [ ] Network connectivity issues
- [ ] Rate limit exceeded scenarios
- [ ] Database connection issues

### 8. Queue Processing
- [ ] Fix that one queue item should be the queue itself, not the target list individuals

### 7. Monitoring and Reporting
- [ ] Campaign status updates
- [ ] Delivery statistics
- [ ] Error logs
- [ ] Performance metrics
- [ ] Export functionality


## Next Steps 
1. Complete initial testing phase
2. Document any bugs or issues
3. Schedule follow-up testing session

## Notes
- Remember to test with different time zones
- Test both small and large target lists
- Document any unexpected behavior

## Test Results
(To be filled in during testing)