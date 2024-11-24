Message Shooter Architecture and Flow

1. DATA COLLECTION & VALIDATION
============================
a) Contact Data (Whatsapp Only)
   - Source: core.models.contact
   - Key Fields: phone, relationship_tag, status
   - Validation: Must be active and have valid phone number
   - Filtered by: get_contact_whatsapp() resolver

b) Message Data
   - Source: core.models.message
   - Key Fields: text, relationship_tag, counter
   - Validation: Must match campaign tag and have appropriate counter
   - Filtered by: get_message() resolver

c) UserPhone Data (Critical for Token)
   - Source: core.models.userphone
   - Key Fields: phone_token, relationship_tag
   - Validation: Must have valid token and match campaign tag
   - Filtered by: get_userphone() resolver

2. TARGET LIST CREATION
=====================
Purpose: Acts as a validated pool of message recipients
Model: messageShooter.models.target_list.TargetList

Key Fields:
- contact_phone: Recipient's phone
- contact_type: "Whatsapp"
- contact_tag: Matches campaign.contact_tag
- reference_id: Links to original contact
- userphone: Links to token source
- message: Specific message to be sent
- status: Tracks processing state

Validation Rules:
- One entry per unique (contact_phone, contact_tag, reference_id)
- Must have valid userphone token
- Must have matching message

3. CAMPAIGN VALIDATION
====================
Model: messageShooter.models.campaign.Campaign

Key Validations:
- campaign_status must be "Active"
- contact_type must be "Whatsapp"
- contact_tag must match:
  * Contact's relationship_tag
  * Message's relationship_tag
  * UserPhone's relationship_tag

4. QUEUE GENERATION
=================
Model: messageShooter.models.queue.Queue

CRITICAL RULE: 1 QUEUE ENTRY = 1 USER_PHONE_TOKEN

Fields:
- target_list: Links to validated recipient
- contact: Original contact reference
- message: Specific message to send
- userphone: Token source
- phone_token: Actual token for API
- status: Processing state
- scheduled_time: When to send

Flow:
1. Campaign triggers target list creation
2. Target list entries trigger queue creation
3. Each queue entry represents ONE message to ONE recipient using ONE token
4. Queue processor handles actual message sending

_____ 

Now we have both Target List and Queue entries created correctly.

1 - Two Target List entries:
    One for Botox campaign
    One for Preenchimento campaign

2 - Two Queue entries:

    Botox: ID 1
        Contact: Luis (11963546222)
        Message: "Hello 0 message Botox"
        UserPhone: 5511999999991
        Status: pending
    Preenchimento: ID 2
        Contact: Luis (11963546222)
        Message: "Hello 0 message Preenchimento"
        UserPhone: 5511999999992
        Status: pending

The test data setup is now complete and working correctly. The system is ready for:

    1. Processing messages in the queue
        ??? 
    2. Testing campaign flows
    3. Testing message delivery
    4. Testing the relationship between campaigns, target lists, and queues