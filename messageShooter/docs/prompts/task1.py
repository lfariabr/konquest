# Message Queue Testing Script

from messageShooter.models.queue import Queue
from core.models.message import Message
from messageShooter.models.target_list import TargetList
from core.models.contact import Contact
from core.models.messagelog import MessageLogs
from django.utils import timezone

def check_queue_status():
    """Check current queue status"""
    print("\nCurrent Queue Status:")
    for status in ['pending', 'processing', 'completed', 'failed', 'retrying']:
        count = Queue.objects.filter(status=status).count()
        print(f"{status}: {count}")

def verify_queue_entries():
    """Verify pending queue entries"""
    print("\nPending Queue Entries:")
    for q in Queue.objects.filter(status='pending'):
        print(f"\nCampaign: {q.target_list.contact_tag}")
        print(f"Message: {q.message.text}")
        print(f"Counter: {q.message.counter}")
        print(f"Status: {q.status}")
        print(f"Phone Token: {q.phone_token}")
        print("---")

def create_queue_entries(counter):
    """Create queue entries for a specific counter"""
    # Get messages for the counter
    botox_msg = Message.objects.get(counter=counter, relationship_tag='Botox')
    preench_msg = Message.objects.get(counter=counter, relationship_tag='Preenchimento')

    # Get target lists and contacts
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

def check_message_logs():
    """Check message logs for all counters"""
    print("\nAll Message Logs by Counter:")
    for counter in [0, 1, 2]:
        print(f"\n=== Counter {counter} Messages ===")
        logs = MessageLogs.objects.filter(message__counter=counter).order_by('message__relationship_tag')
        for log in logs:
            print(f"\nCampaign: {log.relationship_tag}")
            print(f"Message: {log.message.text}")
            print(f"Status: {log.status}")
            print(f"Phone: {log.user_phone.phone_description}")

# Example usage in Django shell:
"""
# Check initial queue status
check_queue_status()

# Create and process counter 1 messages
create_queue_entries(1)
verify_queue_entries()
# Run: python manage.py process_queue

# Create and process counter 2 messages
create_queue_entries(2)
verify_queue_entries()
# Run: python manage.py process_queue

# Check final results
check_message_logs()
"""