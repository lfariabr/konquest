from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from unittest.mock import patch, MagicMock
from messageShooter.models.campaign import Campaign, STATUS_ACTIVE, FREQUENCY_ONCE
from messageShooter.models.target_list import TargetList
from messageShooter.models.queue import Queue
from core.models.message import Message
from core.models.contact import Contact
from core.models.user import kUser
from core.models.userphone import UserPhone
from datetime import datetime, time
import logging

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

    def test_command_handles_keyboard_interrupt(self):
        """Test that command handles keyboard interrupt gracefully"""
        # Run command and capture output
        from io import StringIO
        out = StringIO()
        
        with patch('messageShooter.services.scheduler.CampaignScheduler.process_campaigns') as mock_process:
            mock_process.side_effect = KeyboardInterrupt()
            call_command('run_scheduler', test_mode=True, stdout=out)
            
            # Check output
            output = out.getvalue()
            self.assertIn("Starting campaign scheduler service", output)
            self.assertIn("Stopping campaign scheduler service", output)

    def test_command_handles_processing_error(self):
        """Test that command handles processing errors gracefully"""
        # Mock scheduler to raise an error
        with patch('messageShooter.management.commands.run_scheduler.CampaignScheduler') as mock_scheduler:
            mock_scheduler_instance = MagicMock()
            mock_scheduler_instance.process_campaigns.side_effect = Exception("Campaign processing error")
            mock_scheduler.return_value = mock_scheduler_instance
            
            # Run command and capture output
            from io import StringIO
            out = StringIO()
            call_command('run_scheduler', test_mode=True, stdout=out)
            
            # Check output
            output = out.getvalue()
            self.assertIn("Starting campaign scheduler service", output)
            self.assertIn("Error processing campaigns: Campaign processing error", output)
            self.assertIn("Stopping campaign scheduler service", output)

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
        
        # Create messages with different counters
        Message.objects.create(
            user=self.user,
            title="Message 1",
            text="Test message 1",
            counter=1,
            relationship_tag="Botox",
            contact_type="Whatsapp"
        )
        
        # Create message logs to simulate previous messages
        from core.models.messagelog import MessageLogs
        MessageLogs.objects.create(
            message=self.message,
            user=self.user,
            user_phone=self.userphone,
            contact=self.contact,
            status="sent",
            relationship_tag="Botox"
        )
        
        # Run command
        call_command('run_scheduler', test_mode=True)
        
        # Check that correct message was used (counter=1)
        target_list = TargetList.objects.first()
        self.assertIsNotNone(target_list)
        self.assertEqual(target_list.message.counter, 1)
        self.assertEqual(target_list.sent_messages_count, 1)
        
        # Check queue entry was created
        self.assertEqual(Queue.objects.count(), 1)
