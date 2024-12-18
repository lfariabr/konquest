import pytest
from django.test import TestCase
from django.db import utils as django_db_utils
from django.core.exceptions import ValidationError
from core.models.user import kUser
from messageShooter.models.campaign import Campaign
from messageShooter.models.target_list import TargetList
from core.models.contact import Contact
from core.models.userphone import UserPhone
from core.models.messagelog import MessageLogs
from core.models.message import Message
from django.utils import timezone

class TargetListResolverTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
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
            user=self.user
        )
        
        # Create test contact
        self.contact = Contact.objects.create(
            name="Test Contact",
            phone="5511888888888",
            relationship_tag="Botox",
            user=self.user
        )
        
        # Create test message
        self.message = Message.objects.create(
            title="Test Message",
            text="Hello Botox message",
            relationship_tag="Botox",
            counter=0,
            user=self.user
        )
        
        # Create test campaign
        self.campaign = Campaign.objects.create(
            name="Test Campaign",
            contact_type="Whatsapp",
            contact_tag="Botox",
            frequency="Once",
            userphone=self.userphone,
            campaign_status="Active",
            active_days=['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
            execution_time=timezone.now().time(),
            user=self.user
        )

    def test_create_target_list(self):
        """Test target list creation with basic data"""
        target_list = TargetList.objects.create(
            contact=self.contact,
            contact_tag="Botox",
            contact_type="Whatsapp",
            contact_phone=self.contact.phone,
            userphone=self.userphone,
            message=self.message,
            reference_id=str(self.contact.id),  # Add reference_id for Whatsapp type
            campaign=self.campaign
        )
        
        # Refresh target list to get updated count from signal
        target_list.refresh_from_db()
        
        self.assertIsNotNone(target_list)
        self.assertEqual(target_list.contact_type, "Whatsapp")
        self.assertEqual(target_list.contact_tag, "Botox")
        self.assertEqual(target_list.contact, self.contact)
        self.assertEqual(target_list.userphone, self.userphone)
        self.assertEqual(target_list.contact_phone, "5511888888888")
        self.assertEqual(target_list.message, self.message)
        self.assertEqual(target_list.reference_id, str(self.contact.id))
        self.assertEqual(target_list.campaign, self.campaign)

    def test_create_target_list_with_message_history(self):
        """Test target list creation with existing message history"""
        # Create some message history
        MessageLogs.objects.create(
            contact=self.contact,
            message=self.message,
            status="sent",
            relationship_tag="Botox",
            sent_at=timezone.now(),
            user=self.user,
            user_phone=self.userphone
        )
        
        # Get message count from logs
        message_count = MessageLogs.objects.filter(
            contact=self.contact,
            relationship_tag="Botox",
            status="sent"
        ).count()
        
        target_list = TargetList.objects.create(
            contact=self.contact,
            contact_tag="Botox",
            contact_type="Whatsapp",
            contact_phone=self.contact.phone,
            userphone=self.userphone,
            message=self.message,
            reference_id=str(self.contact.id),  # Add reference_id
            campaign=self.campaign
        )
        
        # Refresh target list to get updated count from signal
        target_list.refresh_from_db()
        
        # Verify sent_messages_count matches logs
        self.assertEqual(target_list.sent_messages_count, message_count)

    def test_create_target_list_duplicate(self):
        """Test handling of duplicate target list creation"""
        # Create first target list
        target_list1 = TargetList.objects.create(
            contact=self.contact,
            contact_tag="Botox",
            contact_type="Whatsapp",
            contact_phone=self.contact.phone,
            userphone=self.userphone,
            message=self.message,
            reference_id=str(self.contact.id),  # Add reference_id
            campaign=self.campaign
        )
        
        # Refresh target list to get updated count from signal
        target_list1.refresh_from_db()
        
        # Attempt to create duplicate target list
        target_list2 = TargetList.objects.create(
            contact=self.contact,
            contact_tag="Botox",
            contact_type="Whatsapp",
            contact_phone=self.contact.phone,
            userphone=self.userphone,
            message=self.message,
            reference_id=str(self.contact.id),  # Add reference_id
            campaign=self.campaign
        )
        
        # Refresh target list to get updated count from signal
        target_list2.refresh_from_db()
        
        # Verify both target lists exist but are different objects
        self.assertNotEqual(target_list1.id, target_list2.id)

    def test_create_target_list_invalid_data(self):
        """Test target list creation with invalid data"""
        # Test with missing required fields
        with self.assertRaises(ValidationError):
            target_list = TargetList.objects.create(
                contact_type="Whatsapp",
                contact_phone=self.contact.phone,
                # Missing contact field which is required for Whatsapp
                message=self.message,
                userphone=self.userphone,
                campaign=self.campaign,
                reference_id=str(self.contact.id)
            )
            target_list.full_clean()

        # Test with invalid contact type
        with self.assertRaises(ValidationError):
            target_list = TargetList.objects.create(
                contact_type="InvalidType",  # Invalid contact type
                contact=self.contact,
                contact_phone="5511888888888",
                message=self.message,
                userphone=self.userphone,
                campaign=self.campaign,
                reference_id=str(self.contact.id)
            )
            target_list.full_clean()

        # Test with missing message
        with self.assertRaises(ValidationError):
            target_list = TargetList.objects.create(
                contact_type="Whatsapp",
                contact=self.contact,
                contact_phone=self.contact.phone,
                userphone=self.userphone,
                campaign=self.campaign,
                reference_id=str(self.contact.id)
                # Missing message field which is required
            )
            target_list.full_clean()

    def test_message_sequence_progression(self):
        """Test that target lists handle message sequence progression correctly"""
        # Create initial target list
        target_list = TargetList.objects.create(
            contact=self.contact,
            contact_tag="Botox",
            contact_type="Whatsapp",
            contact_phone=self.contact.phone,
            userphone=self.userphone,
            message=self.message,
            campaign=self.campaign,
            reference_id=str(self.contact.id)
        )

        # Create message log
        MessageLogs.objects.create(
            contact=self.contact,
            message=self.message,
            status="sent",
            relationship_tag="Botox",
            sent_at=timezone.now(),
            user=self.user,
            user_phone=self.userphone
        )

        # Create another target list for the same contact
        target_list2 = TargetList.objects.create(
            contact=self.contact,
            contact_tag="Botox",
            contact_type="Whatsapp",
            contact_phone=self.contact.phone,
            userphone=self.userphone,
            message=self.message,
            campaign=self.campaign,
            reference_id=str(self.contact.id)
        )

        # Verify sent_messages_count is incremented
        self.assertEqual(target_list2.sent_messages_count, 1)
