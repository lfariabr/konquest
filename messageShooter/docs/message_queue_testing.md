# Message Queue Testing Documentation

## Overview
This document outlines the step-by-step process of testing the message queue system for both Botox and Preenchimento campaigns.

## Test Setup
1. Initial setup using `setup_test_data.py`:
   - Creates test user
   - Sets up UserPhones with valid tokens
   - Creates contacts
   - Creates messages with counters 0-2
   - Creates campaigns and target lists
   - Creates initial queue entries

## Testing Process

### Step 1: Test Counter 0 Messages
```python
# Verify queue entries
from messageShooter.models.queue import Queue

for q in Queue.objects.filter(status='pending'):
    print(f"Campaign: {q.target_list.contact_tag}")
    print(f"Message: {q.message.text}")
    print(f"Counter: {q.message.counter}")

# Process queue
python manage.py process_queue
```

### Step 2: Test Counter 1 Messages
```python
# Create queue entries for counter 1
from messageShooter.models.queue import Queue
from core.models.message import Message
from messageShooter.models.target_list import TargetList
from core.models.contact import Contact
from django.utils import timezone

# Get messages and related data
botox_msg = Message.objects.get(counter=1, relationship_tag='Botox')
preench_msg = Message.objects.get(counter=1, relationship_tag='Preenchimento')
target_botox = TargetList.objects.filter(contact_tag='Botox').first()
target_preench = TargetList.objects.filter(contact_tag='Preenchimento').first()
contact_botox = Contact.objects.get(relationship_tag='Botox')
contact_preench = Contact.objects.get(relationship_tag='Preenchimento')

# Create queue entries
Queue.objects.create(
    target_list=target_botox,
    contact=contact_botox,
    message=botox_msg,
    userphone=target_botox.userphone,
    phone_token=target_botox.userphone.phone_token,
    status='pending',
    scheduled_time=timezone.now()
)

Queue.objects.create(
    target_list=target_preench,
    contact=contact_preench,
    message=preench_msg,
    userphone=target_preench.userphone,
    phone_token=target_preench.userphone.phone_token,
    status='pending',
    scheduled_time=timezone.now()
)

# Process queue
python manage.py process_queue
```

### Step 3: Test Counter 2 Messages
```python
# Same process as Counter 1, but with counter=2 messages
botox_msg = Message.objects.get(counter=2, relationship_tag='Botox')
preench_msg = Message.objects.get(counter=2, relationship_tag='Preenchimento')
# ... rest of the code same as Counter 1
```

### Step 4: Verify Results
```python
# Check message logs
from core.models.messagelog import MessageLogs

print("\nAll Message Logs by Counter:")
for counter in [0, 1, 2]:
    print(f"\n=== Counter {counter} Messages ===")
    logs = MessageLogs.objects.filter(message__counter=counter).order_by('message__relationship_tag')
    for log in logs:
        print(f"Campaign: {log.relationship_tag}")
        print(f"Message: {log.message.text}")
        print(f"Status: {log.status}")
        print(f"Phone: {log.user_phone.phone_description}")
```

## Test Results
- All messages (counters 0-2) were sent successfully
- Both campaigns (Botox and Preenchimento) processed correctly
- Messages were logged with 'sent' status
- Proper tokens were used for each campaign

## Configuration Details
- Botox Campaign Token: rmvYoOnWD5WjcH7Bx5lYTZkGMX2vweN1
- Preenchimento Campaign Token: MOOygXTIL373eLY4YTgbJvyjvW6fswp6
- Contact Phone: 11963546222

## Next Steps
1. Test campaign scheduling
2. Test message delivery timing
3. Monitor actual message delivery in WhatsApp
4. Test error handling scenarios
