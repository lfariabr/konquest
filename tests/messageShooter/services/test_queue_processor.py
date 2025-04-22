"""
Test Queue Processor
"""
import pytest
import time
from django.test import TestCase
from unittest.mock import AsyncMock, patch, MagicMock
from asgiref.sync import sync_to_async
from messageShooter.services.queue_processor import QueueProcessor
from core.models.contact import Contact
from core.models.message import Message
from core.models.userphone import UserPhone
from core.models.user import kUser
from django.utils import timezone
from messageShooter.services.messaging.message_sender import MessageSender
from messageShooter.services.messaging.rate_limiter import RateLimiter
from messageShooter.services.retry.retry_strategy import RetryStrategy, RetryStrategyType
import asyncio

@pytest.mark.django_db
class TestQueueProcessor(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test user
        cls.test_user = kUser.objects.create(
            name='Test User',
            email='test@example.com',
            password='test123',
            company='Test Company'
        )
        
        # Create test contact
        cls.test_contact = Contact.objects.create(
            phone='11999999999',
            name='Test Contact',
            botox_messages_sent=0,
            preenchimento_messages_sent=0,
            user=cls.test_user
        )
        
        # Create test message with required user field
        cls.test_message = Message.objects.create(
            text='Test message',
            relationship_tag='botox',
            user=cls.test_user,  # Add the required user field
            title='Test Title'   # Add title as it's a required field
        )
        
        # Create test userphone
        cls.test_userphone = UserPhone.objects.create(
            phone_number='11988888888',
            phone_token='dummy_token',
            relationship_tag='botox',
            user=cls.test_user
        )

    def setUp(self):
        self.queue_processor = QueueProcessor()
        self.queue_processor.set_test_mode(True)

    @pytest.mark.asyncio
    async def test_process_with_retry_success(self):
        """Test successful execution without retries"""
        async def mock_func():
            return {'success': True}

        result = await self.queue_processor.process_with_retry(mock_func)
        assert result == {'success': True}

    @pytest.mark.asyncio
    async def test_process_with_retry_handles_connection_error(self):
        """Test retry behavior on connection error"""
        attempt_count = 0
        async def mock_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:  # Fail first attempt
                raise ConnectionError("Test connection error")
            return {'success': True}

        result = await self.queue_processor.process_with_retry(mock_func)
        assert result == {'success': True}
        assert attempt_count == 2

    @pytest.mark.asyncio
    async def test_process_contact_async(self):
        """Test processing a contact with text message"""
        # Create a mock MessageSender to replace the real one
        mock_message_sender = MagicMock()
        # Configure the send_text_message method to return an awaitable that resolves to True
        # This is necessary because the actual method is async and returns a coroutine
        mock_message_sender.send_text_message.return_value = asyncio.Future()
        mock_message_sender.send_text_message.return_value.set_result(True)
        
        # Temporarily replace the real message_sender with our mock
        original_message_sender = self.queue_processor.message_sender
        self.queue_processor.message_sender = mock_message_sender
        
        try:
            # Execute the test
            success, error = await self.queue_processor.process_contact_async(
                self.test_contact,
                self.test_message,
                self.test_userphone
            )
            
            # Verify the text message was processed successfully
            assert success is True
            assert error is None
            
            # Verify that send_text_message was called with the expected parameters
            mock_message_sender.send_text_message.assert_called_once_with(
                self.test_contact, self.test_message, self.test_userphone
            )
        finally:
            # Restore the original message_sender
            self.queue_processor.message_sender = original_message_sender

    @pytest.mark.asyncio
    async def test_send_file_message_async(self):
        """Test sending a file message through the queue processor"""
        # Create a mock MessageSender to replace the real one
        mock_message_sender = MagicMock()
        # Configure the send_file_message method to return an awaitable that resolves to True
        # This is necessary because the actual method is async and returns a coroutine
        mock_message_sender.send_file_message.return_value = asyncio.Future()
        mock_message_sender.send_file_message.return_value.set_result(True)
        
        # Temporarily replace the real message_sender with our mock
        original_message_sender = self.queue_processor.message_sender
        self.queue_processor.message_sender = mock_message_sender
        
        try:
            # Execute the test
            contact = MagicMock()
            message = MagicMock()
            userphone = MagicMock()
            file_path = "/path/to/test/file.jpg"
            
            result = await self.queue_processor.send_file_message_async(
                contact, message, userphone, file_path=file_path
            )
            
            # Verify the result
            assert result is True
            
            # Verify that the correct method was called with the right parameters
            mock_message_sender.send_file_message.assert_called_once_with(
                contact, message, userphone, file_path
            )
        finally:
            # Restore the original message_sender
            self.queue_processor.message_sender = original_message_sender

    @pytest.mark.asyncio
    async def test_get_phone_lock(self):
        """Test phone lock mechanism"""
        userphone_id = 1
        
        # First call should set the lock
        await self.queue_processor.get_phone_lock(userphone_id)
        
        # Verify the lock was set
        assert userphone_id in self.queue_processor.rate_limiter._userphone_locks
        
        # Get the stored lock time
        lock_time = self.queue_processor.rate_limiter._userphone_locks[userphone_id]
        assert isinstance(lock_time, float)
        assert lock_time > 0
        
        # In test mode, verify that subsequent calls don't wait
        start_time = time.time()
        await self.queue_processor.get_phone_lock(userphone_id)
        elapsed_time = time.time() - start_time
        assert elapsed_time < 1  # Should be near-instant in test mode