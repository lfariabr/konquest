from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from datetime import datetime
import logging
import unittest

# Set up console logging for tests
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Mock FileHandler before importing CampaignScheduler
with patch('logging.FileHandler') as mock_file_handler:
    mock_file_handler.return_value = console_handler
    from core.models.user import kUser
    from core.models.contact import Contact
    from core.models.message import Message
    from core.models.userphone import UserPhone
    from messageShooter.models.campaign import Campaign
    from messageShooter.models.target_list import TargetList
    from messageShooter.services.scheduler import CampaignScheduler
    from messageShooter.models.campaign import (
        FREQUENCY_ONCE,
        FREQUENCY_DAILY,
        FREQUENCY_WEEKLY,
        FREQUENCY_MONTHLY,
        STATUS_ACTIVE,
        STATUS_COMPLETED
    )
    from messageShooter.models.queue import Queue

# Mock logging setup for tests
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Mock the file handler setup in scheduler.py
@patch('logging.FileHandler')
def setUpModule(mock_file_handler):
    # This will run once before all tests
    mock_file_handler.side_effect = lambda x: console_handler

class TestCampaignScheduler(TransactionTestCase):
    """Test cases for CampaignScheduler using SQLite3"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = kUser.objects.create(
            name="Test User",
            email="test@example.com",
            company="Test Company",
            password="testpass"
        )
        
        # Create a user phone for testing
        self.user_phone = UserPhone.objects.create(
            user=self.user,
            phone_number="1234567890",
            phone_token="test_token",
            phone_description="Test Phone",
            relationship_tag="Preenchimento"
        )
        
        # Create test messages
        self.messages = []
        for i in range(5):
            self.messages.append(
                Message.objects.create(
                    user=self.user,
                    title=f"Message {i}",
                    text=f"Test message {i}",
                    relationship_tag="Preenchimento",  
                    contact_type="Whatsapp",  
                    counter=i
                )
            )
        
        # Create test contact
        self.contact = Contact.objects.create(
            user=self.user,
            name="Test Contact",
            phone="1234567890",
            source="Whatsapp",
            relationship_tag="Preenchimento",
            status="active"
        )
        
        # Get current time for testing
        current_time = timezone.now()
        
        # Create an active campaign
        self.campaign = Campaign.objects.create(
            user=self.user,
            name="Test Campaign",
            frequency=FREQUENCY_DAILY,
            active_days=['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
            campaign_status=STATUS_ACTIVE,
            contact_type="Whatsapp",
            contact_tag="Preenchimento",
            userphone=self.user_phone,
            next_run=current_time
        )
        
        # Add contact to campaign
        self.campaign.contacts.add(self.contact)
        
        # Create scheduler instance
        self.scheduler = CampaignScheduler()

    def tearDown(self):
        """Clean up after each test"""
        Queue.objects.all().delete()
        TargetList.objects.all().delete()
        Campaign.objects.all().delete()
        Contact.objects.all().delete()
        Message.objects.all().delete()
        UserPhone.objects.all().delete()
        kUser.objects.all().delete()

    def test_process_campaigns_creates_target_lists(self):
        """Test that process_campaigns creates target lists for active campaigns"""
        # Mock current time to be a Monday
        monday = datetime(2024, 1, 8, 8, 0, 0)  # A Monday
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.make_aware(monday)
            
            # Update campaign next_run time
            self.campaign.next_run = timezone.make_aware(monday)
            self.campaign.save()
            
            # Process campaigns
            with patch('messageShooter.resolvers.get_userphone.get_userphone') as mock_get_userphone:
                mock_get_userphone.return_value = (self.user_phone, "test_token")
                
                with patch('messageShooter.resolvers.get_counter.get_counter_whatsapp') as mock_get_counter:
                    mock_get_counter.return_value = 0
                    
                    with patch('messageShooter.resolvers.get_message.get_message') as mock_get_message:
                        mock_get_message.return_value = self.messages[0]
                        
                        # Run the scheduler
                        queued_count = self.scheduler.process_campaigns()
                        
                        # Verify results
                        self.assertEqual(queued_count, 1)
                        
                        # Check that target lists were created
                        target_lists = TargetList.objects.filter(campaign=self.campaign)
                        self.assertTrue(target_lists.exists())
                        
                        # Check that queue was created
                        queues = Queue.objects.filter(campaign=self.campaign)
                        self.assertTrue(queues.exists())
                        
                        queue = queues.first()
                        self.assertEqual(queue.message, self.messages[0])
                        self.assertEqual(queue.userphone, self.user_phone)
                        self.assertEqual(queue.phone_token, "test_token")
                        self.assertEqual(queue.status, "pending")
                        
                        # Check that target lists are marked as processing
                        for target_list in target_lists:
                            self.assertEqual(target_list.status, "processing")

    def test_process_campaigns_handles_missing_userphone(self):
        """Test that process_campaigns handles missing userphone gracefully"""
        monday = datetime(2024, 1, 8, 8, 0, 0)
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.make_aware(monday)
            
            self.campaign.next_run = timezone.make_aware(monday)
            self.campaign.save()
            
            # Create a mock target list
            target_list = MagicMock(spec=TargetList)
            target_list.campaign = self.campaign
            target_list.contact = self.contact
            target_list.contact_type = "Whatsapp"
            target_list.contact_tag = "Preenchimento"
            target_list.contact_phone = "1234567890"
            target_list.status = "pending"
            target_list.id = 1
            
            with patch('messageShooter.services.scheduler.generate_target_lists') as mock_generate:
                mock_generate.return_value = [target_list]
                
                with patch('messageShooter.resolvers.get_userphone.get_userphone') as mock_get_userphone:
                    mock_get_userphone.return_value = (None, None)
                    
                    queued_count = self.scheduler.process_campaigns()
                    
                    self.assertEqual(queued_count, 0)
                    self.assertFalse(Queue.objects.filter(campaign=self.campaign).exists())

    def test_process_campaigns_handles_missing_message(self):
        """Test that process_campaigns handles missing message gracefully"""
        monday = datetime(2024, 1, 8, 8, 0, 0)
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.make_aware(monday)
            
            self.campaign.next_run = timezone.make_aware(monday)
            self.campaign.save()
            
            # Create a mock target list
            target_list = MagicMock(spec=TargetList)
            target_list.campaign = self.campaign
            target_list.contact = self.contact
            target_list.contact_type = "Whatsapp"
            target_list.contact_tag = "Preenchimento"
            target_list.contact_phone = "1234567890"
            target_list.status = "pending"
            target_list.id = 1
            
            with patch('messageShooter.services.scheduler.generate_target_lists') as mock_generate:
                mock_generate.return_value = [target_list]
                
                with patch('messageShooter.resolvers.get_userphone.get_userphone') as mock_get_userphone:
                    mock_get_userphone.return_value = (self.user_phone, "test_token")
                    
                    with patch('messageShooter.resolvers.get_counter.get_counter_whatsapp') as mock_get_counter:
                        mock_get_counter.return_value = 0
                        
                        with patch('messageShooter.resolvers.get_message.get_message') as mock_get_message:
                            mock_get_message.return_value = None
                            
                            queued_count = self.scheduler.process_campaigns()
                            
                            self.assertEqual(queued_count, 0)
                            self.assertFalse(Queue.objects.filter(campaign=self.campaign).exists())

    def test_process_campaigns_updates_one_time_campaign_status(self):
        """Test that one-time campaigns are marked as completed after processing"""
        monday = datetime(2024, 1, 8, 8, 0, 0)
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.make_aware(monday)
            
            # Set campaign to one-time
            self.campaign.frequency = FREQUENCY_ONCE
            self.campaign.next_run = timezone.make_aware(monday)
            self.campaign.save()
            
            with patch('messageShooter.resolvers.get_userphone.get_userphone') as mock_get_userphone:
                mock_get_userphone.return_value = (self.user_phone, "test_token")
                
                with patch('messageShooter.resolvers.get_counter.get_counter_whatsapp') as mock_get_counter:
                    mock_get_counter.return_value = 0
                    
                    with patch('messageShooter.resolvers.get_message.get_message') as mock_get_message:
                        mock_get_message.return_value = self.messages[0]
                        
                        queued_count = self.scheduler.process_campaigns()
                        
                        self.assertEqual(queued_count, 1)
                        self.campaign.refresh_from_db()
                        self.assertEqual(self.campaign.campaign_status, STATUS_COMPLETED)
