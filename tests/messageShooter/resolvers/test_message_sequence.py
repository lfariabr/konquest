import pytest
from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from core.models.user import kUser
from messageShooter.models.campaign import Campaign, FREQUENCY_ONCE
from messageShooter.models.target_list import TargetList
from messageShooter.models.queue import Queue
from core.models.contact import Contact
from core.models.message import Message
from core.models.messagelog import MessageLogs
from core.models.userphone import UserPhone
from messageShooter.admin import CampaignAdmin, TargetListAdmin
from messageShooter.resolvers.get_counter import get_counter_whatsapp
from django.utils import timezone
from django.contrib.messages.storage.fallback import FallbackStorage

class MockRequest:
    def __init__(self):
        self.user = None
        self.META = {}
        self.session = {}
        self._messages = FallbackStorage(self)
        
    def add_message(self, level, message):
        self._messages.add(level, message)

class MessageSequenceTestCase(TestCase):
    def setUp(self):
        # Create test user
        self.user = kUser.objects.create(
            name='Admin User',
            email='admin@test.com',
            company='Test Company'
        )
        self.user.set_password('password')
        
        # Create test userphone
        self.userphone = UserPhone.objects.create(
            phone_number="5511999999999",
            phone_token="test_token",
            relationship_tag="Botox",  # Add relationship_tag matching the campaign
            user=self.user
        )
        
        # Create test contact
        self.contact = Contact.objects.create(
            name="Test Contact",
            phone="5511888888888",
            relationship_tag="Botox",
            user=self.user
        )
        
        # Create test campaign
        self.campaign = Campaign.objects.create(
            name="Test Campaign",
            contact_type="Whatsapp",
            contact_tag="Botox",
            frequency=FREQUENCY_ONCE,  # Use imported FREQUENCY_ONCE constant
            campaign_status="Active",
            userphone=self.userphone,
            user=self.user,
            active_days=[0, 1, 2, 3, 4]  # Monday through Friday
        )
        
        # Add contact to campaign
        self.campaign.contacts.add(self.contact)
        
        # Create test messages
        self.messages = []
        for i in range(3):
            msg = Message.objects.create(
                title=f"Message {i}",
                text=f"Hello {i} message Botox",
                relationship_tag="Botox",
                counter=i,
                user=self.user
            )
            self.messages.append(msg)
        
        # Setup admin
        self.site = AdminSite()
        self.campaign_admin = CampaignAdmin(Campaign, self.site)
        self.target_list_admin = TargetListAdmin(TargetList, self.site)
        self.mock_request = MockRequest()
        self.mock_request.user = self.user

    def test_message_sequence_flow(self):
        """Test the entire message sequence flow from Campaign to Queue"""
        
        # 1. Test campaign to target list creation
        self.campaign_admin.instant_generate_tlist(self.mock_request, Campaign.objects.filter(pk=self.campaign.pk))
        
        # Verify target list was created
        target_list = TargetList.objects.filter(contact_tag="Botox").first()
        self.assertIsNotNone(target_list)
        self.assertEqual(target_list.contact, self.contact)
        self.assertEqual(target_list.message, self.messages[0])  # Should use first message
        self.assertEqual(target_list.reference_id, str(self.contact.id))  # Verify reference_id is set correctly
        
        # 2. Test initial counter (should be 0 for new contact)
        counter = get_counter_whatsapp(self.contact.phone, "Botox")
        self.assertEqual(counter, 0)
        
        # 3. Test target list to queue
        self.target_list_admin.instant_process_tlist_to_queue(
            self.mock_request, 
            TargetList.objects.filter(pk=target_list.pk)
        )
        
        # Verify queue entry was created with message 0
        queue_entry = Queue.objects.filter(target_list=target_list).first()
        self.assertIsNotNone(queue_entry)
        self.assertEqual(queue_entry.message.counter, 0)
        self.assertEqual(queue_entry.message, self.messages[0])
        
        # 4. Simulate message sent
        MessageLogs.objects.create(
            contact=self.contact,
            message=queue_entry.message,
            status="sent",
            relationship_tag="Botox",
            sent_at=timezone.now(),
            user=self.user,
            user_phone=self.userphone
        )
        
        # 5. Test counter after first message (should be 1)
        counter = get_counter_whatsapp(self.contact.phone, "Botox")
        self.assertEqual(counter, 1)
        
        # 6. Process target list again to create next queue entry
        self.target_list_admin.instant_process_tlist_to_queue(
            self.mock_request, 
            TargetList.objects.filter(pk=target_list.pk)
        )
        
        # Verify new queue entry has message 1
        queue_entry = Queue.objects.filter(target_list=target_list).order_by('-created_at').first()
        self.assertIsNotNone(queue_entry)
        self.assertEqual(queue_entry.message.counter, 1)

    def test_multiple_contacts_sequence(self):
        """Test message sequencing with multiple contacts at different stages"""
        
        # Create second contact
        contact2 = Contact.objects.create(
            name="Test Contact 2",
            phone="5511777777777",
            relationship_tag="Botox",
            user=self.user
        )
        
        # Add contact to campaign
        self.campaign.contacts.add(contact2)
        
        # Add message history for second contact
        MessageLogs.objects.create(
            contact=contact2,
            message=self.messages[0],
            status="sent",
            relationship_tag="Botox",
            sent_at=timezone.now(),
            user=self.user,
            user_phone=self.userphone
        )
        
        # Create target lists
        target_list1 = TargetList.objects.create(
            contact=self.contact,
            contact_type="Whatsapp",
            contact_tag="Botox",
            contact_phone=self.contact.phone,
            userphone=self.userphone,
            message=self.messages[0],  # First contact starts with message 0
            token=self.userphone.phone_token,
            reference_id=str(self.contact.id)  # Add reference_id for first contact
        )
        
        target_list2 = TargetList.objects.create(
            contact=contact2,
            contact_type="Whatsapp",
            contact_tag="Botox",
            contact_phone=contact2.phone,
            userphone=self.userphone,
            message=self.messages[1],  # Second contact gets message 1 since they already received message 0
            token=self.userphone.phone_token,
            reference_id=str(contact2.id)  # Add reference_id for second contact
        )
        
        # Process target lists to queue
        self.target_list_admin.instant_process_tlist_to_queue(
            self.mock_request, 
            TargetList.objects.all()
        )
        
        # Verify queue entries have correct message counters
        queue_entries = Queue.objects.all().order_by('message__counter')
        self.assertEqual(len(queue_entries), 2)
        
        # First contact should get message 0
        self.assertEqual(queue_entries[0].contact, self.contact)
        self.assertEqual(queue_entries[0].message.counter, 0)
        
        # Second contact should get message 1
        self.assertEqual(queue_entries[1].contact, contact2)
        self.assertEqual(queue_entries[1].message.counter, 1)
