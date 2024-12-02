from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from messageShooter.models.queue import Queue
from messageShooter.models.target_list import TargetList
from messageShooter.services.queue_processor import QueueProcessor
from core.models.message import Message
from core.models.contact import Contact
from core.models.user import kUser
from core.models.userphone import UserPhone
from core.models.messagelog import MessageLogs
import logging
import requests

logger = logging.getLogger(__name__)

class TestQueueProcessor(TestCase):
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
            relationship_tag="Botox"
        )
        
        self.target_list = TargetList.objects.create(
            contact=self.contact,
            contact_phone=self.contact.phone,
            contact_type="Whatsapp",
            contact_tag="Botox",  # This is used as the relationship_tag in MessageLogs
            reference_id=str(self.contact.id),
            sent_messages_count=0,
            userphone=self.userphone,
            message=self.message,
            token=self.userphone.phone_token
        )
        
        self.queue_processor = QueueProcessor()

    @patch('messageShooter.services.queue_processor.send_text_message')
    def test_process_queue_sends_message(self, mock_send):
        """Test that process_queue sends messages successfully"""
        # Setup mock
        mock_send.return_value = True
        
        # Create queue entry
        queue_entry = Queue.objects.create(
            target_list=self.target_list,
            message=self.message,
            userphone=self.userphone,
            phone_token=self.userphone.phone_token,
            status='pending',
            scheduled_time=timezone.now()
        )
        
        # Process queue
        processed, success, error = self.queue_processor.process_queue()
        
        # Check results
        self.assertEqual(processed, 1)
        self.assertEqual(success, 1)
        self.assertEqual(error, 0)
        
        # Check that message was sent
        mock_send.assert_called_once_with(
            phone=self.contact.phone,
            message=self.message.text,
            token_socialhub=self.userphone.phone_token
        )
        
        # Check queue entry status
        queue_entry.refresh_from_db()
        self.assertEqual(queue_entry.status, 'sent')
        
        # Check message log
        self.assertEqual(MessageLogs.objects.count(), 1)
        log = MessageLogs.objects.first()
        self.assertEqual(log.status, 'sent')

    @patch('messageShooter.services.queue_processor.send_text_message')
    def test_process_queue_handles_send_failure(self, mock_send):
        """Test that process_queue handles message send failures"""
        # Setup mock to simulate failure
        mock_send.return_value = False
        
        # Create queue entry
        queue_entry = Queue.objects.create(
            target_list=self.target_list,
            message=self.message,
            userphone=self.userphone,
            phone_token=self.userphone.phone_token,
            status='pending',
            scheduled_time=timezone.now()
        )
        
        # Process queue
        processed, success, error = self.queue_processor.process_queue()
        
        # Check results
        self.assertEqual(processed, 1)
        self.assertEqual(success, 0)
        self.assertEqual(error, 1)
        
        # Check queue entry status
        queue_entry.refresh_from_db()
        self.assertEqual(queue_entry.status, 'retrying')
        self.assertEqual(queue_entry.retry_count, 1)
        
        # Check message log
        self.assertEqual(MessageLogs.objects.count(), 1)
        log = MessageLogs.objects.first()
        self.assertEqual(log.status, 'failed')

    def test_process_queue_respects_scheduled_time(self):
        """Test that process_queue only processes messages scheduled for now or earlier"""
        # Create future queue entry
        future_time = timezone.now() + timezone.timedelta(hours=1)
        Queue.objects.create(
            target_list=self.target_list,
            message=self.message,
            userphone=self.userphone,
            phone_token=self.userphone.phone_token,
            status='pending',
            scheduled_time=future_time
        )
        
        # Process queue
        processed, success, error = self.queue_processor.process_queue()
        
        # Check that no messages were processed
        self.assertEqual(processed, 0)
        self.assertEqual(success, 0)
        self.assertEqual(error, 0)

    @patch('messageShooter.services.queue_processor.send_text_message')
    def test_process_queue_handles_multiple_retries(self, mock_send):
        """Test that process_queue handles multiple retries correctly"""
        # Setup mock to always fail
        mock_send.return_value = False
        
        # Create queue entry
        queue_entry = Queue.objects.create(
            target_list=self.target_list,
            message=self.message,
            userphone=self.userphone,
            phone_token=self.userphone.phone_token,
            status='pending',
            scheduled_time=timezone.now()
        )
        
        # Process queue multiple times
        current_time = timezone.now()
        for i in range(4):  # More than max retries
            with patch('django.utils.timezone.now') as mock_now:
                mock_now.return_value = current_time
                
                # Process queue
                self.queue_processor.process_queue()
                queue_entry.refresh_from_db()
                
                if i < self.queue_processor.max_retries:  # First three retries
                    self.assertEqual(queue_entry.status, 'retrying')
                    self.assertEqual(queue_entry.retry_count, i + 1)
                else:  # After max retries
                    self.assertEqual(queue_entry.status, 'failed')
                    self.assertEqual(queue_entry.retry_count, self.queue_processor.max_retries)
                
                # Advance time by 5 minutes for next iteration
                current_time += timezone.timedelta(minutes=5)
                
                # Save the queue entry with updated scheduled_time
                if queue_entry.status == 'retrying':
                    queue_entry.scheduled_time = current_time
                    queue_entry.save()

    @patch('messageShooter.services.queue_processor.send_file_message')
    def test_process_queue_handles_file_messages(self, mock_send):
        """Test that process_queue correctly handles messages with files"""
        # Update message to be a file message
        self.message.file_type = 'image'
        self.message.save()
        
        # Setup mock
        mock_send.return_value = True, None
        
        # Create queue entry
        queue_entry = Queue.objects.create(
            target_list=self.target_list,
            message=self.message,
            userphone=self.userphone,
            phone_token=self.userphone.phone_token,
            status='pending',
            scheduled_time=timezone.now()
        )
        
        # Process queue
        processed, success, errors = self.queue_processor.process_queue()
        
        # Check results
        self.assertEqual(processed, 1)
        self.assertEqual(success, 1)
        self.assertEqual(errors, 0)
        
        # Check that file message was sent
        mock_send.assert_called_once_with(
            phone=self.contact.phone,
            message=self.message.text,
            token_socialhub=self.userphone.phone_token,
            file_path=None  # No actual file in test
        )
        
        # Check queue entry status
        queue_entry.refresh_from_db()
        self.assertEqual(queue_entry.status, 'sent')
        
        # Check message log was created
        message_log = MessageLogs.objects.last()
        self.assertEqual(message_log.status, 'sent')

    @patch('messageShooter.services.queue_processor.send_text_message')
    def test_invalid_phone_token(self, mock_send):
        """Test handling of invalid phone token when sending messages"""
        # Setup mock to simulate failure
        mock_send.return_value = False
        
        # Set invalid token on userphone
        self.userphone.phone_token = "invalid_token"
        self.userphone.save()
        
        # Create queue entry
        queue_entry = Queue.objects.create(
            target_list=self.target_list,
            message=self.message,
            userphone=self.userphone,
            phone_token=self.userphone.phone_token,  # Use userphone's token
            status='pending',
            scheduled_time=timezone.now()
        )
        
        # Process queue
        processed, success, error = self.queue_processor.process_queue()
        
        # Check results
        self.assertEqual(processed, 1)
        self.assertEqual(success, 0)
        self.assertEqual(error, 1)
        
        # Check that message was attempted with invalid token
        mock_send.assert_called_once_with(
            phone=self.contact.phone,
            message=self.message.text,
            token_socialhub="invalid_token"
        )
        
        # Check queue entry status - should be retrying after first failure
        queue_entry.refresh_from_db()
        self.assertEqual(queue_entry.status, 'retrying')
        self.assertEqual(queue_entry.retry_count, 1)
        
        # Check message log was created with failed status
        self.assertEqual(MessageLogs.objects.count(), 1)
        message_log = MessageLogs.objects.first()
        self.assertEqual(message_log.status, 'failed')
        self.assertEqual(message_log.user, self.user)
        self.assertEqual(message_log.contact, self.contact)
        self.assertEqual(message_log.message, self.message)
