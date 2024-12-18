from django.test import TransactionTestCase
from django.utils import timezone
from asgiref.sync import sync_to_async
from unittest.mock import patch, AsyncMock, MagicMock, ANY, call
import pytest
import asyncio
import logging
import time

from core.models.user import kUser
from core.models.userphone import UserPhone
from core.models.message import Message
from core.models.contact import Contact
from messageShooter.models.target_list import TargetList
from messageShooter.models.queue import Queue, QUEUE_STATUS
from messageShooter.services.queue_processor import QueueProcessor
from messageShooter.resolvers.get_contacts import get_contact_whatsapp
from messageShooter.models.campaign import Campaign

logger = logging.getLogger(__name__)

@pytest.mark.django_db(transaction=True)
class TestQueueProcessor(TransactionTestCase):
    """Test queue processing functionality with focus on sequential processing and breath time"""
    
    def setUp(self):
        """Setup test data synchronously first"""
        super().setUp()
        
        # Create user first
        self.user = kUser.objects.create(
            name='Test User',
            email='test@example.com',
            company='Test Company'
        )
        
        # Create userphone with user
        self.userphone = UserPhone.objects.create(
            user=self.user,
            phone_number='+1234567890',
            phone_token='test_token',
            phone_description='Test Phone'
        )
        
        # Create default test message
        self.message = Message.objects.create(
            user=self.user,
            text='Default test message',
            title='Test Message',
            relationship_tag='Botox',
            contact_type='Whatsapp',
            counter=0
        )
        
        # Create campaign with correct fields
        self.campaign = Campaign.objects.create(
            name="Test Campaign",
            contact_type="Whatsapp",
            contact_tag="Botox",  # Updated to use valid tag
            frequency="Once",
            execution_time=timezone.now().time(),
            campaign_status="Active",
            active_days=['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
            userphone=self.userphone,
            user=self.user
        )
        
        # Initialize processor with test settings
        self.processor = QueueProcessor()
        self.processor._test_mode = True  # Enable test mode
        self.processor.breath_time = 0  # No delays between contacts in tests

    async def create_test_contacts(self, count: int) -> list:
        """Create multiple test contacts"""
        contacts = []
        create_contact = sync_to_async(Contact.objects.create)
        for i in range(count):
            contact = await create_contact(
                user=self.user,
                phone=f'+1234567890{i}',
                name=f'Test Contact {i}',
                source='Whatsapp',
                relationship_tag='Test',
                status='active'
            )
            contacts.append(contact)
        return contacts

    async def create_test_queue(self, contact_count=1, message=None):
        """Helper to create a test queue with contacts"""
        # Use provided message or default message
        message = message or self.message
        
        contacts = []
        create_contact = sync_to_async(Contact.objects.create)
        for i in range(contact_count):
            contact = await create_contact(
                user=self.user,
                name=f"Test Contact {i}",
                phone=f"+1234567890{i}",
                source="Whatsapp",
                relationship_tag="Botox",
                status="active"
            )
            contacts.append(contact)

        # Create target list
        create_target_list = sync_to_async(TargetList.objects.create)
        target_list = await create_target_list(
            contact=contacts[0],  # Use first contact
            contact_phone=contacts[0].phone,
            contact_type="Whatsapp",
            contact_tag="Botox",
            campaign=self.campaign,
            message=message,
            userphone=self.userphone,
            status="pending"
        )

        # Create queue
        create_queue = sync_to_async(Queue.objects.create)
        queue = await create_queue(
            target_list=target_list,
            message=message,
            userphone=self.userphone,
            status="pending"
        )

        return queue

    @patch('messageShooter.services.queue_processor.send_text_message', new_callable=AsyncMock)
    @patch('messageShooter.services.queue_processor.asyncio.sleep', new_callable=AsyncMock)
    async def test_sequential_processing_with_breath_time(self, mock_sleep, mock_send):
        """Test that contacts are processed sequentially with breath time between contacts"""
        # Setup success response
        mock_send.return_value = {'success': True}
        
        # Create queue with multiple contacts
        queue = await self.create_test_queue(contact_count=3)
        
        # Configure processor for this test
        self.processor._test_mode = True  # Disable real breath time for this test
        self.processor.breath_time = 1  # Set breath time to 1 second
        
        # Process queue
        await self.processor.process_queue_item_async(queue)
        
        # Verify sequential processing
        self.assertEqual(mock_send.call_count, 3)  # All contacts processed
        self.assertEqual(mock_sleep.call_count, 0)  # No sleep in test mode

    @patch('messageShooter.services.queue_processor.send_text_message', new_callable=AsyncMock)
    @patch('messageShooter.services.queue_processor.asyncio.sleep', new_callable=AsyncMock)
    async def test_rate_limiting_with_phone_lock(self, mock_sleep, mock_send):
        """Test that rate limiting is enforced per userphone"""
        # Setup success response
        mock_send.return_value = {'success': True}
        
        # Create queue with multiple contacts but same userphone
        queue = await self.create_test_queue(contact_count=3)
        
        # Configure processor for this test
        self.processor._test_mode = False  # Enable real rate limiting for this test
        self.processor.breath_time = 1  # Set breath time to 1 second
        
        # Process queue
        await self.processor.process_queue_item_async(queue)
        
        # Count rate limiting sleeps (from get_phone_lock)
        rate_limit_sleeps = len([
            call for call in mock_sleep.mock_calls 
            if call.args == (self.processor.breath_time,)
        ])
        
        # We expect rate limiting between each contact
        self.assertEqual(rate_limit_sleeps, 2)  # Rate limiting between contacts

    @patch('messageShooter.services.queue_processor.send_text_message', new_callable=AsyncMock)
    async def test_concurrent_queue_processing(self, mock_send):
        """Test that different queues process concurrently"""
        mock_send.return_value = {'success': True}
        
        # Create processor for this test
        processor = QueueProcessor()
        processor._test_mode = True
        processor.breath_time = 0  # No delays in test
        
        # Create two messages with different counters
        create_message = sync_to_async(Message.objects.create)
        message1 = await create_message(
            user=self.user,
            text='Test message 1',
            title='Test Message 1',
            relationship_tag='Botox',  # Match the contact tag
            contact_type='Whatsapp',
            counter=0
        )

        message2 = await create_message(
            user=self.user,
            text='Test message 2',
            title='Test Message 2',
            relationship_tag='Botox',  # Match the contact tag
            contact_type='Whatsapp',
            counter=1  # Set to 1 to test different message counters
        )

        # Create two contacts
        create_contact = sync_to_async(Contact.objects.create)
        contacts = []
        for i in range(2):
            contact = await create_contact(
                user=self.user,
                name=f"Test Contact {i+1}",
                phone=f"+1234567890{i+1}",
                source="Whatsapp",
                relationship_tag="Botox",  # Both contacts have Botox tag
                status="active"
            )
            contacts.append(contact)

        # Create target lists and queues for each message
        create_target_list = sync_to_async(TargetList.objects.create)
        create_queue = sync_to_async(Queue.objects.create)
        queues = []

        # Create a queue for each message
        for message in [message1, message2]:
            # Create target list for this message
            target_list = await create_target_list(
                contact=contacts[0],  # Use first contact as reference
                contact_phone=contacts[0].phone,
                contact_type="Whatsapp",
                contact_tag="Botox",  # Match the contacts' tag
                campaign=self.campaign,
                message=message,
                userphone=self.userphone,
                status="pending"
            )

            # Create queue for this message
            queue = await create_queue(
                target_list=target_list,
                message=message,
                userphone=self.userphone,
                status="pending",
                total_contacts=2  # Both contacts should receive this message
            )
            queues.append(queue)

        # Process both queues concurrently
        await processor.process_queues_async(queues)

        # Verify both queues completed
        refresh_from_db = sync_to_async(lambda x: x.refresh_from_db())
        for queue in queues:
            await refresh_from_db(queue)
            assert queue.status == 'sent', (
                f"Queue {queue.id} has status '{queue.status}' instead of 'sent'. "
                f"Processed contacts: {queue.processed_contacts}"
            )

        # Verify correct number of messages sent
        expected_calls = len(queues) * len(contacts)  # Each queue sends to all contacts
        assert mock_send.call_count == expected_calls, (
            f"Expected {expected_calls} messages to be sent "
            f"({len(contacts)} contacts per queue * {len(queues)} queues), "
            f"but got {mock_send.call_count} calls"
        )

        # Verify messages were sent with correct text and to correct contacts
        calls = mock_send.call_args_list
        expected_messages = {
            '+12345678901': ['Test message 1', 'Test message 2'],  # Each contact receives both messages
            '+12345678902': ['Test message 1', 'Test message 2']   # Each contact receives both messages
        }

        # Group calls by phone number to verify each contact received the correct messages
        actual_messages = {}
        for call in calls:
            phone = call[1]['phone']
            message = call[1]['message']
            if phone not in actual_messages:
                actual_messages[phone] = []
            actual_messages[phone].append(message)

        # Log the actual calls for debugging
        print("\nDebug: Mock send calls:")
        for call in mock_send.call_args_list:
            print(f"  - Phone: {call[1]['phone']}, Message: {call[1]['message']}")

        # Sort messages for comparison
        for phone in actual_messages:
            actual_messages[phone].sort()
            if phone in expected_messages:
                expected_messages[phone].sort()

        assert actual_messages == expected_messages, (
            f"Messages were not sent correctly to contacts.\n"
            f"Expected: {expected_messages}\n"
            f"Got: {actual_messages}"
        )

    @patch('messageShooter.services.queue_processor.send_text_message', new_callable=AsyncMock)
    async def test_detailed_progress_logging(self, mock_send):
        """Test that detailed progress is logged for each contact"""
        mock_send.return_value = {'success': True}
        
        # Create queue with multiple contacts
        queue = await self.create_test_queue(contact_count=2)
        
        # Process queue and capture logs
        with self.assertLogs(logger='messageShooter.services.queue_processor', level='INFO') as log:
            await self.processor.process_queue_item_async(queue)
            
            # Verify log messages
            log_messages = '\n'.join(log.output)
            self.assertIn('Starting to process 2 contacts', log_messages)
            self.assertIn('Processing contact 1/2', log_messages)
            self.assertIn('Queue', log_messages)  # Updated assertion
            self.assertIn('Processing contact 2/2', log_messages)
            self.assertIn('Queue', log_messages)  # Updated assertion
            self.assertIn('messages sent', log_messages)  # Updated assertion

    @patch('messageShooter.services.queue_processor.send_text_message', new_callable=AsyncMock)
    async def test_mixed_success_failure_handling(self, mock_send):
        """Test handling of mixed successes and failures in a queue"""
        # Setup mock to alternate between success and failure
        mock_send.side_effect = [
            {'success': True},
            {'success': False, 'error': 'Test error'},
            {'success': True}
        ]
        
        # Create queue with three contacts
        queue = await self.create_test_queue(contact_count=3)
        
        # Process queue
        await self.processor.process_queue_item_async(queue)
        
        # Verify queue status
        refresh_from_db = sync_to_async(lambda x: x.refresh_from_db())
        await refresh_from_db(queue)
        
        self.assertEqual(queue.status, 'sent')  # Updated from 'partially_completed'
        
        # Verify processed contacts
        processed = queue.processed_contacts
        self.assertEqual(len([c for c in processed if processed[c]['status'] == 'sent']), 2)
        self.assertEqual(len([c for c in processed if processed[c]['status'] == 'failed']), 1)

    @patch('messageShooter.services.queue_processor.send_text_message', new_callable=AsyncMock)
    @patch('messageShooter.services.queue_processor.asyncio.sleep', new_callable=AsyncMock)
    async def test_retry_on_connection_error(self, mock_sleep, mock_send):
        """Test that connection errors are retried"""
        # Setup mock to fail with connection error first, then succeed
        mock_send.side_effect = [
            ConnectionResetError(54, 'Connection reset by peer'),  # First attempt fails
            {'success': True}  # Second attempt succeeds
        ]
        
        # Create test message for this test
        create_message = sync_to_async(Message.objects.create)
        test_message = await create_message(
            user=self.user,
            text='Test message',
            title='Test Message',
            relationship_tag='Botox',
            contact_type='Whatsapp',
            counter=0
        )

        # Create queue with one contact
        queue = await self.create_test_queue(contact_count=1, message=test_message)
        
        # Configure processor for this test
        self.processor._test_mode = True  # Skip actual delays
        
        # Process queue
        await self.processor.process_queue_item_async(queue)
        
        # Verify retry behavior
        self.assertEqual(mock_send.call_count, 2)  # Called twice (fail + success)
        self.assertEqual(queue.status, 'sent')  # Updated from 'completed'
        
        # Verify the order of calls
        expected_call = call(
            phone='+12345678900',
            message='Test message',
            token_socialhub='test_token'
        )
        mock_send.assert_has_calls([expected_call, expected_call])
