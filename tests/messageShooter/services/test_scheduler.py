from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch
from datetime import datetime

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
import logging

logger = logging.getLogger(__name__)

class TestCampaignScheduler(TestCase):
    def setUp(self):
        """Set up test data"""
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
        
        # Create an active campaign with next_run set to now
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
            created_count = self.scheduler.process_campaigns()
            
            # Check that target lists were created
            self.assertEqual(created_count, 1)
            self.assertEqual(TargetList.objects.count(), 1)
            
            # Check target list details
            target_list = TargetList.objects.first()
            self.assertEqual(target_list.contact_tag, "Preenchimento")
            self.assertEqual(target_list.message, self.messages[0])  # Should use first message (counter=0)
            self.assertEqual(target_list.sent_messages_count, 0)

    def test_process_campaigns_skips_inactive_campaign(self):
        """Test that process_campaigns skips inactive campaigns"""
        # Make campaign inactive
        self.campaign.campaign_status = "Paused"
        self.campaign.save()
        
        # Process campaigns
        created_count = self.scheduler.process_campaigns()
        
        # Check that no target lists were created
        self.assertEqual(created_count, 0)
        self.assertEqual(TargetList.objects.count(), 0)

    def test_process_campaigns_respects_message_counter(self):
        """Test that process_campaigns respects message counter when creating target lists"""
        # Create a message log to simulate previous messages
        from core.models.messagelog import MessageLogs
        
        # Mock current time to be a Monday
        monday = datetime(2024, 1, 8, 8, 0, 0)  # A Monday
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.make_aware(monday)
            
            # Update campaign next_run time
            self.campaign.next_run = timezone.make_aware(monday)
            self.campaign.save()
            
            # Create message logs to simulate previous messages sent
            MessageLogs.objects.create(
                message=self.messages[0],
                user=self.user,
                user_phone=self.user_phone,
                contact=self.contact,  
                status="sent",
                relationship_tag="Preenchimento",
                sent_at=timezone.now()  # Add sent_at timestamp
            )
            
            # Process campaigns
            created_count = self.scheduler.process_campaigns()
            
            # Verify target list was created
            self.assertEqual(created_count, 1, "Expected one target list to be created")
            
            # Check that target list was created with correct message
            target_list = TargetList.objects.first()
            self.assertIsNotNone(target_list, "Target list not created")
            self.assertEqual(target_list.message, self.messages[1], "Wrong message selected - expected message with counter=1")
            
            # Update sent_messages_count based on message logs
            target_list.sent_messages_count = MessageLogs.objects.filter(
                contact=self.contact,
                status="sent",
                relationship_tag="Preenchimento"
            ).count()
            target_list.save()
            
            # Verify message logs
            message_logs = MessageLogs.objects.filter(contact=self.contact, status="sent").order_by('sent_at')
            self.assertEqual(message_logs.count(), 1, "Expected one message log")
            self.assertEqual(message_logs[0].message, self.messages[0], "Wrong message in log")
            self.assertEqual(target_list.sent_messages_count, message_logs.count(), "Wrong sent_messages_count")

    def test_process_campaigns_skips_when_no_matching_message(self):
        """Test that process_campaigns skips when no message exists for the counter"""
        # Create multiple message logs to exceed available messages
        from core.models.messagelog import MessageLogs
        for _ in range(6):  # More than available messages
            MessageLogs.objects.create(
                message=self.messages[0],
                user=self.user,
                user_phone=self.user_phone,
                contact=self.contact,  
                status="sent",
                relationship_tag="Preenchimento"  
            )
        
        # Process campaigns
        created_count = self.scheduler.process_campaigns()
        
        # Check that no target list was created (no message with counter=5)
        self.assertEqual(created_count, 0)
        self.assertEqual(TargetList.objects.count(), 0)

    def test_process_campaigns_creates_queue_entries(self):
        """Test that process_campaigns creates queue entries for target lists"""
        # Mock current time to be a Monday
        monday = datetime(2024, 1, 8, 8, 0, 0)  # A Monday
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.make_aware(monday)
            
            # Update campaign next_run time
            self.campaign.next_run = timezone.make_aware(monday)
            self.campaign.save()
            
            # Process campaigns
            created_count = self.scheduler.process_campaigns()
            
            # Check that both target list and queue entry were created
            self.assertEqual(created_count, 1)
            self.assertEqual(Queue.objects.count(), 1)
            
            # Check queue entry details
            queue_entry = Queue.objects.first()
            self.assertEqual(queue_entry.target_list, TargetList.objects.first())
            self.assertEqual(queue_entry.message, self.messages[0])
            self.assertEqual(queue_entry.status, "pending")

    def test_process_campaigns_respects_active_days(self):
        """Test that process_campaigns respects campaign active days"""
        # Set campaign to run only on Mondays
        self.campaign.active_days = ['monday']
        self.campaign.save()
        
        # Mock timezone.now to return a Tuesday
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.datetime(2024, 1, 2, 12, 0, tzinfo=timezone.get_current_timezone())  # A Tuesday
            
            # Process campaigns
            created_count = self.scheduler.process_campaigns()
            
            # Check that no target list was created since it's not a Monday
            self.assertEqual(created_count, 0)
            self.assertEqual(TargetList.objects.count(), 0)

    def test_process_campaigns_handles_recurring_campaigns(self):
        """Test that process_campaigns correctly handles recurring campaigns"""
        # Create message with matching relationship tag
        message = Message.objects.create(
            user=self.user,
            title="Test Message",
            text="Test message content",
            relationship_tag="Preenchimento",  
            contact_type="Whatsapp",  
            counter=0  
        )
        
        # Make campaign daily recurring
        self.campaign.frequency = FREQUENCY_DAILY
        self.campaign.execution_time = "12:00"
        self.campaign.active_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        self.campaign.next_run = timezone.datetime(2024, 1, 1, 12, 0, tzinfo=timezone.get_current_timezone())  # Set next_run to today
        self.campaign.save()
        
        # Mock timezone.now to return a time after execution_time
        with patch('django.utils.timezone.now') as mock_now:
            # Set current time to 13:00 (after execution_time)
            test_time = timezone.datetime(2024, 1, 1, 13, 0, tzinfo=timezone.get_current_timezone())
            mock_now.return_value = test_time
            
            # Process campaigns
            created_count = self.scheduler.process_campaigns()
            
            # Check that target list was created
            self.assertEqual(created_count, 1)
            self.assertEqual(TargetList.objects.count(), 1)
            
            # Check next_run was updated to tomorrow
            self.campaign.refresh_from_db()
            expected_next_run = test_time.replace(hour=12, minute=0) + timezone.timedelta(days=1)
            self.assertEqual(
                self.campaign.next_run,
                expected_next_run
            )

    def test_process_campaigns_handles_once_frequency(self):
        """Test that process_campaigns correctly handles once frequency campaigns"""
        # Create message with matching relationship tag
        message = Message.objects.create(
            user=self.user,
            title="Test Message",
            text="Test message content",
            relationship_tag="Preenchimento",  
            contact_type="Whatsapp",  
            counter=0
        )
        
        # Setup campaign for one-time execution
        self.campaign.frequency = FREQUENCY_ONCE
        self.campaign.execution_time = "12:00"
        self.campaign.next_run = timezone.datetime(2024, 1, 1, 12, 0, tzinfo=timezone.get_current_timezone())
        self.campaign.contact_tag = "Preenchimento"  
        self.campaign.save()

        # Process campaigns
        with patch('django.utils.timezone.now') as mock_now:
            test_time = timezone.datetime(2024, 1, 1, 13, 0, tzinfo=timezone.get_current_timezone())
            mock_now.return_value = test_time
            created_count = self.scheduler.process_campaigns()
            
            # Should create one target list
            self.assertEqual(created_count, 1)
            
            # Campaign should be marked as completed
            self.campaign.refresh_from_db()
            self.assertEqual(self.campaign.campaign_status, STATUS_COMPLETED)

    def test_process_campaigns_handles_weekly_frequency(self):
        """Test that process_campaigns correctly handles weekly frequency campaigns"""
        # Create message with matching relationship tag
        message = Message.objects.create(
            user=self.user,
            title="Test Message",
            text="Test message content",
            relationship_tag="Preenchimento",  
            contact_type="Whatsapp",  
            counter=0
        )
        
        # Setup campaign for weekly execution
        self.campaign.frequency = FREQUENCY_WEEKLY
        self.campaign.execution_time = "12:00"
        self.campaign.active_days = ['monday']  # Only run on Mondays
        self.campaign.next_run = timezone.datetime(2024, 1, 1, 12, 0, tzinfo=timezone.get_current_timezone())  # Monday
        self.campaign.save()

        # Test on Monday after execution time
        with patch('django.utils.timezone.now') as mock_now:
            test_time = timezone.datetime(2024, 1, 1, 13, 0, tzinfo=timezone.get_current_timezone())  # Monday 1pm
            mock_now.return_value = test_time
            created_count = self.scheduler.process_campaigns()
            
            # Should create one target list
            self.assertEqual(created_count, 1)
            
            # Next run should be set to next Monday
            self.campaign.refresh_from_db()
            expected_next_run = test_time.replace(day=8, hour=12, minute=0)  # Next Monday
            self.assertEqual(self.campaign.next_run, expected_next_run)

        # Test on a non-active day (Tuesday)
        with patch('django.utils.timezone.now') as mock_now:
            test_time = timezone.datetime(2024, 1, 2, 13, 0, tzinfo=timezone.get_current_timezone())  # Tuesday 1pm
            mock_now.return_value = test_time
            created_count = self.scheduler.process_campaigns()
            
            # Should not create any target lists
            self.assertEqual(created_count, 0)

    def test_process_campaigns_handles_monthly_frequency(self):
        """Test that process_campaigns correctly handles monthly campaigns"""
        # Create message with matching relationship tag
        message = Message.objects.create(
            user=self.user,
            title="Test Message",
            text="Test message content",
            relationship_tag="Preenchimento",  
            contact_type="Whatsapp",  
            counter=0
        )
        
        # Setup campaign for monthly execution on the 1st
        self.campaign.frequency = FREQUENCY_MONTHLY
        self.campaign.execution_time = "12:00"
        self.campaign.active_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        self.campaign.next_run = timezone.datetime(2024, 1, 1, 12, 0, tzinfo=timezone.get_current_timezone())  # Set next_run to today (1st of month)
        self.campaign.save()
        
        # Test on 1st of month after execution time
        with patch('django.utils.timezone.now') as mock_now:
            test_time = timezone.datetime(2024, 1, 1, 13, 0, tzinfo=timezone.get_current_timezone())
            mock_now.return_value = test_time
            created_count = self.scheduler.process_campaigns()
            self.assertEqual(created_count, 1)
            
            # Check next_run is set to 1st of next month
            self.campaign.refresh_from_db()
            expected_next_run = timezone.datetime(2024, 2, 1, 12, 0, tzinfo=timezone.get_current_timezone())
            self.assertEqual(self.campaign.next_run, expected_next_run)
        
        # Test on a different day of the month
        with patch('django.utils.timezone.now') as mock_now:
            test_time = timezone.datetime(2024, 1, 2, 13, 0, tzinfo=timezone.get_current_timezone())
            mock_now.return_value = test_time
            created_count = self.scheduler.process_campaigns()
            self.assertEqual(created_count, 0)
