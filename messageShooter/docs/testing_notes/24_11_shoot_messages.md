# Step by step guide to create test data (user, messages, campaigns, target list, queue entries)

1. Run python manage.py setup_test_data
2. Run python manage.py process_queue
This will send the messages with counter 0 to contacts and register on the logs

3. To send counter 1 messages:
```bash
# Create queue entries for counter 1
python manage.py process_campaign Botox --counter 1
python manage.py process_campaign Preenchimento --counter 1

# Process the queue to send messages
python manage.py process_queue
```

4. To send counter 2 messages:
```bash
# Create queue entries for counter 2
python manage.py process_campaign Botox --counter 2
python manage.py process_campaign Preenchimento --counter 2

# Process the queue to send messages
python manage.py process_queue
```

## Verifying Messages

After each step, you can verify the message logs in Django Admin or using the shell:

```python
from core.models.messagelog import MessageLogs

# Check message logs for a specific counter
counter = 0  # Change this to check different counters (0, 1, or 2)
for log in MessageLogs.objects.filter(message__counter=counter):
    print(f"\nCampaign: {log.relationship_tag}")
    print(f"Message: {log.message.text}")
    print(f"Status: {log.status}")
    print(f"Phone: {log.user_phone.phone_description}")
```

## Expected Results

1. After step 2: Counter 0 messages sent
   - Botox campaign: "Hello 0 message Botox"
   - Preenchimento campaign: "Hello 0 message Preenchimento"

2. After step 3: Counter 1 messages sent
   - Botox campaign: "Hello 1 message Botox"
   - Preenchimento campaign: "Hello 1 message Preenchimento"

3. After step 4: Counter 2 messages sent
   - Botox campaign: "Hello 2 message Botox"
   - Preenchimento campaign: "Hello 2 message Preenchimento"

## Troubleshooting

If messages are not being sent:
1. Check that the UserPhone tokens are correct
2. Verify that the Campaigns are marked as "Active"
3. Check the Queue entries status in Django Admin
4. Review the message logs for any error messages