from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from unittest.mock import patch, MagicMock
from io import StringIO
from messageShooter.models.campaign import Campaign, STATUS_ACTIVE, FREQUENCY_ONCE
from messageShooter.models.target_list import TargetList
from messageShooter.models.queue import Queue
from core.models.message import Message
from core.models.contact import Contact
from core.models.user import kUser
from core.models.userphone import UserPhone
from datetime import datetime, time
import logging
import urllib3
import warnings

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class TestRunSchedulerCommand(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = kUser.objects.create(
            name="Test User",
            email="test@example.com",
            company="Test Company",
            password="testpass"
        )
        
        self.userphone = UserPhone.objects.create(
            user=self.user,
            phone_number="11988446710",
            phone_token="test_token",
            phone_description="Test Phone",
            relationship_tag="Botox"
        )
        
        self.contact = Contact.objects.create(
            user=self.user,
            name="Test Contact",
            phone="11963546222",
            source="Whatsapp",
            relationship_tag="Botox",
            status="active"
        )
        
        self.message = Message.objects.create(
            user=self.user,
            title="Test Message",
            text="Hello test message",
            counter=0,
            relationship_tag="Botox",
            contact_type="Whatsapp"
        )
        
        # Set execution_time to a time object
        execution_time = time(12, 0)  # 12:00 PM
        
        self.campaign = Campaign.objects.create(
            user=self.user,
            name="Test Campaign",
            contact_type="Whatsapp",
            contact_tag="Botox",
            frequency=FREQUENCY_ONCE,
            userphone=self.userphone,
            campaign_status=STATUS_ACTIVE,
            active_days=['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
            execution_time=execution_time
        )

    @patch('messageShooter.services.queue_processor.QueueProcessor.process_queue')
    def test_command_processes_queue(self, mock_process):
        """Test that command processes queue"""
        # Mock process_queue to return some results
        mock_process.return_value = (1, 1, 0)
        
        # Run command
        call_command('run_scheduler')
        
        # Check that process_queue was called
        mock_process.assert_called_once()

    def test_command_handles_keyboard_interrupt(self):
        """Test that command handles keyboard interrupt gracefully"""
        # Run command and capture output
        out = StringIO()
        
        with patch('messageShooter.services.queue_processor.QueueProcessor.process_queue') as mock_process:
            mock_process.side_effect = KeyboardInterrupt()
            # Run with max_iterations=1 to avoid infinite loop
            call_command('run_scheduler', max_iterations=1, stdout=out)
            
            # Check output
            output = out.getvalue()
            self.assertIn("Error in scheduler: ", output)

    def test_command_handles_processing_error(self):
        """Test that command handles processing errors gracefully"""
        # Run command and capture output
        out = StringIO()
        
        with patch('messageShooter.services.queue_processor.QueueProcessor.process_queue') as mock_process:
            mock_process.side_effect = Exception("Test error")
            call_command('run_scheduler', stdout=out)
            
            # Check output
            output = out.getvalue()
            self.assertIn("Error in scheduler: Test error", output)

    def test_command_continuous_mode(self):
        """Test that command runs continuously"""
        with patch('time.sleep') as mock_sleep, \
             patch('messageShooter.services.queue_processor.QueueProcessor.process_queue') as mock_process:
            
            # Setup mock to return some processed messages
            mock_process.return_value = (1, 1, 0)
            
            # Run command in continuous mode with max 2 iterations
            out = StringIO()
            call_command('run_scheduler', continuous=True, sleep=1, max_iterations=2, stdout=out)
            
            # Check that sleep was called once (after first iteration)
            mock_sleep.assert_called_once_with(1)
            
            # Check that process_queue was called twice
            self.assertEqual(mock_process.call_count, 2)
            
            # Check output
            output = out.getvalue()
            self.assertIn("Processed 1 messages (1 successful, 0 errors)", output)
            self.assertIn("Scheduler stopped", output)

    @patch('messageShooter.services.scheduler.timezone.now')
    def test_command_processes_campaigns_and_queue(self, mock_now):
        """Test that command processes both campaigns and queue"""
        # Mock current time to be after execution time
        mock_now.return_value = timezone.datetime(2024, 1, 1, 13, 0, tzinfo=timezone.get_current_timezone())
        
        # Run command
        call_command('run_scheduler', test_mode=True)
        
        # Check that target list was created
        self.assertEqual(TargetList.objects.count(), 1)
        
        # Check that queue entry was created
        self.assertEqual(Queue.objects.count(), 1)

    @patch('messageShooter.services.scheduler.timezone.now')
    def test_command_processes_multiple_campaigns(self, mock_now):
        """Test that command processes multiple campaigns"""
        # Mock current time to be after execution time
        mock_now.return_value = timezone.datetime(2024, 1, 1, 13, 0, tzinfo=timezone.get_current_timezone())
        
        # Create another campaign
        Campaign.objects.create(
            user=self.user,
            name="Test Campaign 2",
            contact_type="Whatsapp",
            contact_tag="Botox",
            frequency=FREQUENCY_ONCE,
            userphone=self.userphone,
            campaign_status=STATUS_ACTIVE,
            active_days=['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
            execution_time=time(12, 0)  # 12:00 PM
        )
        
        # Run command
        call_command('run_scheduler', test_mode=True)
        
        # Check that target lists were created for both campaigns
        self.assertEqual(TargetList.objects.count(), 2)
        self.assertEqual(Queue.objects.count(), 2)

    @patch('messageShooter.services.scheduler.timezone.now')
    def test_command_full_integration(self, mock_now):
        """Test full integration of campaign processing and queue processing"""
        # Mock current time to be after execution time
        mock_now.return_value = timezone.datetime(2024, 1, 1, 13, 0, tzinfo=timezone.get_current_timezone())

        # Create test user and related objects
        test_user = kUser.objects.create(
            name="Test User 2",
            email="test2@example.com",
            company="Test Company 2",
            password="testpass2"
        )
        test_userphone = UserPhone.objects.create(
            user=test_user,
            phone_number="11988446711",
            phone_token="test_token_2",
            phone_description="Test Phone 2",
            relationship_tag="Botox"
        )
        test_contact = Contact.objects.create(
            user=test_user,
            name="Test Contact 2",
            phone="11963546223",
            source="Whatsapp",
            relationship_tag="Botox",
            status="active"
        )

        # Create test messages
        message1 = Message.objects.create(
            user=test_user,
            title="Message 1",
            text="Test message 1",
            counter=1,
            relationship_tag="Botox",
            contact_type="Whatsapp"
        )
        message2 = Message.objects.create(
            user=test_user,
            title="Message 2",
            text="Test message 2",
            counter=2,
            relationship_tag="Botox",
            contact_type="Whatsapp"
        )

        # Create campaign
        from messageShooter.models.campaign import Campaign
        campaign = Campaign.objects.create(
            user=test_user,
            name="Test Campaign",
            contact_tag="Botox",
            contact_type="Whatsapp",
            campaign_status="Active",
            execution_time=timezone.datetime(2024, 1, 1, 12, 0, tzinfo=timezone.get_current_timezone()).time(),
            userphone=test_userphone,
            active_days=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        )

        # Create target list
        target_list = TargetList.objects.create(
            contact=test_contact,
            contact_phone=test_contact.phone,
            contact_type="Whatsapp",
            contact_tag="Botox",
            message=message1,
            userphone=test_userphone,
            campaign=campaign
        )

        # Create message logs to simulate previous messages
        from core.models.messagelog import MessageLogs
        MessageLogs.objects.create(
            message=message2,
            user=test_user,
            user_phone=test_userphone,
            contact=test_contact,
            status="sent",
            relationship_tag="Botox"
        )

        # Mock get_counter_whatsapp to return counter 1
        with patch('messageShooter.resolvers.target_list_resolver.get_counter_whatsapp') as mock_counter1, \
             patch('messageShooter.resolvers.get_counter.get_counter_whatsapp') as mock_counter2:
            mock_counter1.return_value = 1  # This will match message1's counter
            mock_counter2.return_value = 1  # This will match message1's counter
            
            # Run command with max 1 iteration
            out = StringIO()
            call_command('run_scheduler', max_iterations=1, stdout=out)
            
            # Check output
            output = out.getvalue()
            self.assertIn("Starting queue processing", output)
            
            # Check that a queue entry was created
            queue_entry = Queue.objects.first()
            self.assertIsNotNone(queue_entry)
            self.assertEqual(queue_entry.message, message1)
