# setup_test_data.py
import os
import django
from django.core.management.base import BaseCommand
from core.models.user import kUser
from core.models.contact import Contact
from core.models.message import Message
from core.models.userphone import UserPhone
from messageShooter.models.campaign import Campaign
from messageShooter.models.target_list import TargetList
from messageShooter.models.queue import Queue
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'konquist.settings')
django.setup()

class Command(BaseCommand):
    help = 'Create test data for message queue testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...')
        
        # Clear existing data
        self.stdout.write('Clearing existing data...')
        UserPhone.objects.all().delete()
        Contact.objects.all().delete()
        Message.objects.all().delete()
        Campaign.objects.all().delete()
        TargetList.objects.all().delete()
        Queue.objects.all().delete()

        # Get or create user
        self.stdout.write('Creating test user...')
        user = kUser.objects.first()
        if not user:
            user = kUser.objects.create(
                name="Test User",
                email="test@example.com",
                company="Test Company",
                password="testpass"
            )

        # Create UserPhones
        self.stdout.write('Creating UserPhones...')
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
        self.stdout.write('Creating Contacts...')
        contact_botox = Contact.objects.create(
            user=user,
            name="Test Contact Botox",
            phone="11963546222",
            source="Whatsapp",
            relationship_tag="Botox",
            status="active"
        )

        contact_preench = Contact.objects.create(
            user=user,
            name="Test Contact Preenchimento",
            phone="11963546222",
            source="Whatsapp",
            relationship_tag="Preenchimento",
            status="active"
        )

        # Create Messages
        self.stdout.write('Creating Messages...')
        for counter in range(3):  # Create messages with counters 0-2
            Message.objects.create(
                user=user,
                title=f"Botox Message {counter}",
                text=f"Hello {counter} message Botox",
                relationship_tag="Botox",
                counter=counter
            )
            Message.objects.create(
                user=user,
                title=f"Preenchimento Message {counter}",
                text=f"Hello {counter} message Preenchimento",
                relationship_tag="Preenchimento",
                counter=counter
            )

        # Create Campaigns
        self.stdout.write('Creating Campaigns...')
        campaign_botox = Campaign.objects.create(
            user=user,
            name="Botox Campaign",
            contact_type="Whatsapp",
            contact_tag="Botox",
            frequency="Once",
            userphone=userphone_botox,
            campaign_status="Active"  # Make sure campaign is active
        )

        campaign_preench = Campaign.objects.create(
            user=user,
            name="Preenchimento Campaign",
            contact_type="Whatsapp",
            contact_tag="Preenchimento",
            frequency="Once",
            userphone=userphone_preench,
            campaign_status="Active"  # Make sure campaign is active
        )

        # Create Target Lists
        self.stdout.write('Creating Target Lists...')
        message_botox = Message.objects.get(relationship_tag="Botox", counter=0)
        message_preench = Message.objects.get(relationship_tag="Preenchimento", counter=0)

        target_list_botox = TargetList.objects.create(
            contact_phone=contact_botox.phone,
            contact_type="Whatsapp",
            contact_tag="Botox",
            reference_id=str(contact_botox.id),
            sent_messages_count=0,
            userphone=userphone_botox,
            message=message_botox
        )

        target_list_preench = TargetList.objects.create(
            contact_phone=contact_preench.phone,
            contact_type="Whatsapp",
            contact_tag="Preenchimento",
            reference_id=str(contact_preench.id),
            sent_messages_count=0,
            userphone=userphone_preench,
            message=message_preench
        )

        # Create Queue entries
        self.stdout.write('Creating Queue entries...')
        
        # Validate and create Botox Queue
        if target_list_botox.userphone.phone_token != userphone_botox.phone_token:
            raise ValueError("Mismatch in phone tokens for Botox queue")
            
        queue_botox = Queue.objects.create(
            target_list=target_list_botox,
            contact=contact_botox,
            message=target_list_botox.message,
            userphone=userphone_botox,
            phone_token=userphone_botox.phone_token,
            status='pending',
            scheduled_time=timezone.now()
        )

        # Validate and create Preenchimento Queue
        if target_list_preench.userphone.phone_token != userphone_preench.phone_token:
            raise ValueError("Mismatch in phone tokens for Preenchimento queue")
            
        queue_preench = Queue.objects.create(
            target_list=target_list_preench,
            contact=contact_preench,
            message=target_list_preench.message,
            userphone=userphone_preench,
            phone_token=userphone_preench.phone_token,
            status='pending',
            scheduled_time=timezone.now()
        )

        # Final validation
        self.stdout.write('Validating Queue entries...')
        for queue in Queue.objects.all():
            if queue.phone_token != queue.target_list.userphone.phone_token:
                raise ValueError(f"Queue {queue.id} has mismatched phone tokens")
            if queue.target_list.contact_tag != queue.userphone.relationship_tag:
                raise ValueError(f"Queue {queue.id} has mismatched campaign tags")

        self.stdout.write(self.style.SUCCESS('Test data created successfully with proper Queue relationships!'))