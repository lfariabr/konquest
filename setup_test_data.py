# setup_test_data.py
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'konquist.settings')
django.setup()

from django.core.management import call_command
from core.models.user import kUser
from core.models.contact import Contact
from core.models.message import Message
from core.models.userphone import UserPhone
from messageShooter.models.campaign import Campaign
from messageShooter.models.target_list import TargetList
from messageShooter.models.queue import Queue
from django.utils import timezone

def create_test_data():
    """Create a complete test setup with campaigns, contacts, messages, and userphones."""
    
    # Clear existing data
    UserPhone.objects.all().delete()
    Contact.objects.all().delete()
    Message.objects.all().delete()
    Campaign.objects.all().delete()
    TargetList.objects.all().delete()
    Queue.objects.all().delete()

    # Get or create user
    user = kUser.objects.first()
    if not user:
        user = kUser.objects.create(
            name="Test User",
            email="test@example.com",
            company="Test Company",
            password="testpass"
        )

    # Create UserPhones
    userphone_botox = UserPhone.objects.create(
        user=user,
        phone_number="11988446710",
        phone_token="rmvYoOnWD5WjcH7Bx5lYTZkGMX2vweN1",
        phone_description="Botox Phone",
        relationship_tag="Botox"
    )

    userphone_preench = UserPhone.objects.create(
        user=user,
        phone_number="11975193585",
        phone_token="MOOygXTIL373eLY4YTgbJvyjvW6fswp6",
        phone_description="Preenchimento Phone",
        relationship_tag="Preenchimento"
    )

    # Create Contacts
    contact_botox = Contact.objects.create(
        user=user,
        name="Luis",
        phone="11963546222",
        source="Whatsapp",  # Make sure source is correct
        tag="Botox",
        relationship_tag="Botox",
        status="active"  # Make sure status is valid
    )

    contact_preench = Contact.objects.create(
        user=user,
        name="Luis",
        phone="11963546222",
        source="Whatsapp",  # Make sure source is correct
        tag="Preenchimento",
        relationship_tag="Preenchimento",
        status="active"  # Make sure status is valid
    )

    # Create Messages for Botox
    botox_messages = []
    for i in range(3):
        msg = Message.objects.create(
            user=user,
            title=f"Botox Message {i}",
            text=f"Hello {i} message Botox",
            relationship_tag="Botox",
            counter=i
        )
        botox_messages.append(msg)

    # Create Messages for Preenchimento
    preench_messages = []
    for i in range(3):
        msg = Message.objects.create(
            user=user,
            title=f"Preenchimento Message {i}",
            text=f"Hello {i} message Preenchimento",
            relationship_tag="Preenchimento",
            counter=i
        )
        preench_messages.append(msg)

    # Create Campaigns
    campaign_botox = Campaign.objects.create(
        user=user,
        name="Botox Campaign",
        contact_type="Whatsapp",
        contact_tag="Botox",
        frequency="Daily",
        execution_time="08:00",
        active_days=[0,1,2,3,4,5,6],  # All days
        sequential_order=[
            {'message_id': msg.id} for msg in botox_messages
        ],
        userphone=userphone_botox,
        campaign_status="Active"  # Make sure campaign is active
    )

    campaign_preench = Campaign.objects.create(
        user=user,
        name="Preenchimento Campaign",
        contact_type="Whatsapp",
        contact_tag="Preenchimento",
        frequency="Daily",
        execution_time="08:00",
        active_days=[0,1,2,3,4,5,6],  # All days
        sequential_order=[
            {'message_id': msg.id} for msg in preench_messages
        ],
        userphone=userphone_preench,
        campaign_status="Active"  # Make sure campaign is active
    )

    # Create Target List entries
    target_list_botox = TargetList.objects.create(
        contact=contact_botox,
        contact_phone=contact_botox.phone,
        contact_type="Whatsapp",
        contact_tag="Botox",
        reference_id=str(contact_botox.id),
        userphone=userphone_botox,
        message=botox_messages[0],  # First message in sequence
        sequence_order=0,  # First in sequence
        token=userphone_botox.phone_token
    )

    target_list_preench = TargetList.objects.create(
        contact=contact_preench,
        contact_phone=contact_preench.phone,
        contact_type="Whatsapp",
        contact_tag="Preenchimento",
        reference_id=str(contact_preench.id),
        userphone=userphone_preench,
        message=preench_messages[0],  # First message in sequence
        sequence_order=0,  # First in sequence
        token=userphone_preench.phone_token
    )

    # Create Queue entries
    queue_botox = Queue.objects.create(
        target_list=target_list_botox,
        contact=contact_botox,
        message=target_list_botox.message,
        userphone=userphone_botox,
        phone_token=userphone_botox.phone_token,
        status='pending',
        scheduled_time=timezone.now()
    )

    queue_preench = Queue.objects.create(
        target_list=target_list_preench,
        contact=contact_preench,
        message=target_list_preench.message,
        userphone=userphone_preench,
        phone_token=userphone_preench.phone_token,
        status='pending',
        scheduled_time=timezone.now()
    )

    # Print summary
    print("\nCreated Test Data:")
    print(f"UserPhones: Botox ({userphone_botox.id}), Preenchimento ({userphone_preench.id})")
    print(f"Contacts: Botox ({contact_botox.id}), Preenchimento ({contact_preench.id})")
    print(f"Messages: {Message.objects.count()} (3 for each campaign)")
    print(f"Campaigns: Botox ({campaign_botox.id}), Preenchimento ({campaign_preench.id})")
    print(f"Target Lists: Botox ({target_list_botox.id}), Preenchimento ({target_list_preench.id})")
    print(f"Queue Entries: Botox ({queue_botox.id}), Preenchimento ({queue_preench.id})")

    return {
        'user': user,
        'userphone_botox': userphone_botox,
        'userphone_preench': userphone_preench,
        'contact_botox': contact_botox,
        'contact_preench': contact_preench,
        'campaign_botox': campaign_botox,
        'campaign_preench': campaign_preench,
        'target_list_botox': target_list_botox,
        'target_list_preench': target_list_preench,
        'queue_botox': queue_botox,
        'queue_preench': queue_preench
    }

if __name__ == '__main__':
    create_test_data()

# django shell
# python manage.py shell
# from setup_test_data import create_test_data
# test_objects = create_test_data()

# command line:
# python setup_test_data.py