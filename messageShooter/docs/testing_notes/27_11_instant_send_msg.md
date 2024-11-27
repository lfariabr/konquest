Hello, I believe we have some organizing to do:

1) Organize views on admin:
Queue ID | Contact Type | Status | Recipients (Count of Target List) | UserPhone.Number 
Then, when clicking on Queue ID, I want to see the target list id by ID, being redirected directly to target list.

2) Have an action called "Instant Process Queue" to send messages to selected queue originitaed from target list

DOES IT MAKE SENSE?

Yes, that makes perfect sense! Let's improve the Queue admin interface to make it more informative and actionable. I'll help you implement both 

## Progress Update - Nov 27, 2023

### Admin Queue Improvements
- Enhanced Queue admin interface to show more relevant information
- Added better filtering and search capabilities
- Improved display of relationships between Queue entries and Target Lists
- Added clear success/error messages for queue processing

### Queue Resolver & Message Handling
- Fixed message text generation to properly include counter in templates
- Ensured proper handling of phone tokens for message sending
- Improved error handling and logging for message sending process

### Target List Resolver Updates
- Simplified logging in `create_target_list` function
- Improved handling of sent message counts
- Better error messages for target list creation process
- Removed redundant logging statements for better clarity

### Process Campaign Command Enhancements
- **Major Fix**: Updated counter calculation logic to work per-contact
- Now correctly tracks message sequence for each contact individually
- Moved counter calculation inside target loop for accurate sequencing
- Fixed `get_counter_whatsapp` usage to properly pass contact phone
- Improved error handling and reporting for missing messages/contacts

### Campaign > Target List > Queue Flow
- Fixed the entire flow to maintain proper message sequencing
- Target Lists now correctly show sent message counts
- Queue entries are created with proper counter values based on contact history
- Both paths (Campaign > Target List and Target List > Queue) now correctly track message sequences
- Instant actions provide better feedback and error reporting

### Testing Results
Successfully tested the full flow:
1. Creating campaign with multiple messages (counter 0, 1, 2)
2. Creating target list from campaign
3. Adding target list to queue
4. Processing queue entries
5. Verified that contacts receive correct sequential messages:
   - New contacts start with message 0
   - Contacts with previous messages get next in sequence
   - Counter properly increments based on contact's message history

### Target List Test Updates (March 2024)

### Test Fixes
- Added proper `reference_id` handling in message sequence tests
- Updated `test_multiple_contacts_sequence` to include `reference_id` when creating target lists
- Added validation in `test_message_sequence_flow` to verify correct `reference_id` assignment
- Both tests now pass successfully, confirming proper message sequence handling for multiple contacts

### Key Test Validations
- Target lists are created with correct reference IDs (using contact.id)
- Message sequences work correctly across multiple contacts
- Campaign to target list flow maintains data integrity
- Message counter initialization and updates work as expected

### Test Coverage
- Single contact message flow
- Multiple contact sequence handling
- Campaign to target list conversion
- Message counter initialization and updates

### Known Issues
- InsecureRequestWarning when making HTTPS requests to socialhub.pro API
  - Consider adding proper certificate verification in future update

### Next Steps
- Consider adding certificate verification for API requests
- Monitor message sequencing for edge cases
- Consider adding more detailed logging for debugging purposes