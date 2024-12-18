from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from unittest.mock import patch, MagicMock
from io import StringIO
from core.models.user import kUser
from core.models.userphone import UserPhone
from core.models.contact import Contact
from core.models.messagelog import MessageLogs
from core.models.message import Message
from messageShooter.models.queue import Queue
from messageShooter.models.campaign import Campaign, STATUS_ACTIVE, FREQUENCY_DAILY
from messageShooter.models.target_list import TargetList
from datetime import datetime, time
import logging
import urllib3
import warnings
from django.db import transaction

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class TestRunSchedulerCommand(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = kUser.objects.create(
            name='Test User',
            email='test@example.com',
            company='Test Company'
        )
        self.userphone = UserPhone.objects.create(
            user=self.user,
            phone_token="test_token",
            relationship_tag="Botox"
        )
        self.contact = Contact.objects.create(
            user=self.user,
            name="Test Contact",
            phone="11963546222",
            source="Whatsapp",
            relationship_tag="Botox",
            status="landing page"
        )
        self.message = Message.objects.create(
            title="Test Message",
            text="Hello test message",
            relationship_tag="Botox",
            contact_type="Whatsapp",
            counter=0,
            user=self.user
        )
        current_time = timezone.now()
        weekday_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        current_weekday = weekday_names[current_time.weekday()]
        self.campaign = Campaign.objects.create(
            name="Test Campaign",
            user=self.user,
            userphone=self.userphone,
            contact_type="Whatsapp",
            contact_tag="Botox",
            campaign_status=STATUS_ACTIVE,
            frequency=FREQUENCY_DAILY,
            execution_time=timezone.now().time(),
            active_days=weekday_names
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
    def test_command_full_integration(self, mock_now):
        """Test full integration of campaign processing and queue processing"""
        test_time = timezone.datetime(2024, 12, 18, 2, 21, 34, tzinfo=timezone.get_current_timezone())
        mock_now.return_value = test_time
        
        with transaction.atomic():
            self.campaign.execution_time = (test_time - timezone.timedelta(minutes=1)).time()
            self.campaign.campaign_status = STATUS_ACTIVE
            self.campaign.active_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            self.campaign.save()

            # Run command
            out = StringIO()
            call_command('run_scheduler', max_iterations=1, stdout=out)

            # Verify campaign was processed
            self.campaign.refresh_from_db()
            self.assertIsNotNone(self.campaign.next_run)

    @patch('messageShooter.services.scheduler.timezone.now')
    def test_command_processes_campaigns_and_queue(self, mock_now):
        """Test that command processes both campaigns and queue"""
        test_time = timezone.datetime(2024, 12, 18, 2, 21, 34, tzinfo=timezone.get_current_timezone())
        mock_now.return_value = test_time
        
        with transaction.atomic():
            self.campaign.execution_time = (test_time - timezone.timedelta(minutes=1)).time()
            self.campaign.campaign_status = STATUS_ACTIVE
            self.campaign.active_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            self.campaign.save()

            # Create target list
            target_list = TargetList.objects.create(
                contact=self.contact,
                contact_tag="Botox",
                contact_type="Whatsapp",
                contact_phone=self.contact.phone,
                userphone=self.userphone,
                message=self.message,
                campaign=self.campaign,
                status='pending'
            )

            # Run command
            out = StringIO()
            call_command('run_scheduler', max_iterations=1, stdout=out)

            # Verify campaign was processed
            self.campaign.refresh_from_db()
            self.assertIsNotNone(self.campaign.next_run)

    @patch('messageShooter.services.scheduler.timezone.now')
    def test_command_processes_multiple_campaigns(self, mock_now):
        """Test that command processes multiple campaigns"""
        test_time = timezone.datetime(2024, 12, 18, 2, 21, 34, tzinfo=timezone.get_current_timezone())
        mock_now.return_value = test_time
        
        with transaction.atomic():
            self.campaign.execution_time = (test_time - timezone.timedelta(minutes=1)).time()
            self.campaign.campaign_status = STATUS_ACTIVE
            self.campaign.active_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            self.campaign.save()

            # Create second campaign
            campaign2 = Campaign.objects.create(
                name="Test Campaign 2",
                contact_type="Whatsapp",
                contact_tag="Botox",
                frequency=FREQUENCY_DAILY,
                execution_time=(test_time - timezone.timedelta(minutes=1)).time(),
                campaign_status=STATUS_ACTIVE,
                active_days=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
                userphone=self.userphone,
                user=self.user
            )

            # Run command
            out = StringIO()
            call_command('run_scheduler', max_iterations=1, stdout=out)

            # Verify campaigns were processed
            self.campaign.refresh_from_db()
            campaign2.refresh_from_db()
            self.assertIsNotNone(self.campaign.next_run)
            self.assertIsNotNone(campaign2.next_run)

    @patch('messageShooter.services.scheduler.timezone.now')
    def test_command_full_integration2(self, mock_now):
        """Test full integration of campaign processing and queue processing"""
        # Clean up any existing data
        Campaign.objects.all().delete()
        Message.objects.all().delete()
        Queue.objects.all().delete()
        TargetList.objects.all().delete()
        Contact.objects.all().delete()
        UserPhone.objects.all().delete()
        kUser.objects.all().delete()
        MessageLogs.objects.all().delete()

        # Mock current time
        test_time = timezone.datetime(2024, 12, 18, 2, 21, 34, tzinfo=timezone.get_current_timezone())
        mock_now.return_value = test_time
    
        # Create test user and related objects
        test_user = kUser.objects.create(
            name="Test User 2",
            email="test2@example.com",
            company="Test Company 2",
            password="testpass2"
        )
        test_userphone = UserPhone.objects.create(
            phone_number="+1234567890",
            phone_token="test_token_2",
            user=test_user
        )
        test_contact = Contact.objects.create(
            user=test_user,
            name="Test Contact 2",
            phone="11963546223",
            source="Whatsapp",
            relationship_tag="Botox",
            status="active"  # Make sure contact is active
        )
    
        # Create test messages
        message1 = Message.objects.create(
            title="Message 1",
            text="Test message 1",
            relationship_tag="Botox",
            contact_type="Whatsapp",
            counter=0,
            user=test_user
        )
        message2 = Message.objects.create(
            title="Message 2",
            text="Test message 2",
            relationship_tag="Botox",
            contact_type="Whatsapp",
            counter=1,
            user=test_user
        )
    
        # Create campaign with execution time before current time
        campaign = Campaign.objects.create(
            user=test_user,
            name="Test Campaign",
            contact_tag="Botox",
            contact_type="Whatsapp",
            campaign_status=STATUS_ACTIVE,
            frequency=FREQUENCY_DAILY,
            execution_time=(test_time - timezone.timedelta(minutes=1)).time(),
            userphone=test_userphone,
            active_days=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        )

        # Set next_run to a time in the past
        campaign.next_run = test_time - timezone.timedelta(minutes=5)
        campaign.save(update_fields=['next_run'])

        # Debug: Check campaign status
        print(f"\nDebug campaign status:")
        print(f"- Campaign ID: {campaign.id}")
        print(f"- Status: {campaign.campaign_status}")
        print(f"- Frequency: {campaign.frequency}")
        print(f"- Execution time: {campaign.execution_time}")
        print(f"- Active days: {campaign.active_days}")
        print(f"- Next run: {campaign.next_run}")
        print(f"- Is ready to run: {campaign.is_ready_to_run()}")
        print(f"- Should run today: {campaign.should_run_today()}")
    
        # Run command with max 1 iteration
        out = StringIO()
        call_command('run_scheduler', max_iterations=1, stdout=out)
    
        # Check output
        output = out.getvalue()
        self.assertIn("Starting queue processing", output)
    
        # Check that a queue entry was created with message1
        queue_entry = Queue.objects.first()
        self.assertIsNotNone(queue_entry)
        self.assertEqual(queue_entry.message, message1)  # Should use message1 since counter is 0
