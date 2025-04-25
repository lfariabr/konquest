# messageShooter/services/messaging/message_sender.py
import asyncio
import logging
from typing import Optional, Tuple, Any
from asgiref.sync import sync_to_async
from django.utils import timezone

from core.models.contact import Contact
from core.models.message import Message
from core.models.userphone import UserPhone
from core.models.messagelog import MessageLogs

from messageShooter.services.messaging.text_sender import TextSender
from messageShooter.services.messaging.file_sender import FileSender
from messageShooter.services.messaging.rate_limiter import RateLimiter
from messageShooter.services.retry.retry_strategy import RetryStrategy, RetryStrategyType

logger = logging.getLogger(__name__)

class MessageSender:
    """
    Unified interface for sending messages through various channels.
    Integrates rate limiting and retry mechanisms.
    """

    def __init__(self, rate_limiter: Optional[RateLimiter] = None, 
                 retry_strategy: Optional[RetryStrategy] = None):
        """
        Initialize the message sender with rate limiting and retry capabilities.
        
        Args:
            rate_limiter: Optional custom rate limiter, creates default if None
            retry_strategy: Optional custom retry strategy, creates default if None
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize components or use provided ones
        self.rate_limiter = rate_limiter or RateLimiter(breath_time=30)
        self.retry_strategy = retry_strategy or RetryStrategy(
            max_retries=5, 
            base_delay=20,  # 20 seconds base delay
            strategy_type=RetryStrategyType.EXPONENTIAL
        )
        
        # Initialize sender implementations
        self.text_sender = TextSender(self.rate_limiter, self.retry_strategy)
        self.file_sender = FileSender(self.rate_limiter, self.retry_strategy)
        
        # Test mode flag for executing dry runs
        self._test_mode = False
    
    async def send_message(self, contact: Contact, message: Message, userphone: UserPhone) -> bool:
        """
        Send a message (text or file) to a contact.
        
        Args:
            contact: The contact to send the message to
            message: The message content to send
            userphone: The userphone to use for sending
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        try:
            # Check if the message has a media file
            if message.file:
                return await self.send_file_message(contact, message, userphone)
            else:
                return await self.send_text_message(contact, message, userphone)
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}", exc_info=True)
            return False
    
    async def send_text_message(self, contact: Contact, message: Message, userphone: UserPhone) -> bool:
        """
        Send a text-only message to a contact.
        
        Args:
            contact: The contact to send the message to
            message: The message content to send
            userphone: The userphone to use for sending
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        # Acquire a lock based on userphone to respect rate limits
        await self.rate_limiter.acquire_lock(userphone.id)
        
        # Delegate to the text sender implementation
        success = await self.text_sender.send(contact, message, userphone)
        
        if success:
            # Log the successful message
            await self._log_message(contact, message, userphone)
            
        return success

    async def send_file_message(self, contact: Contact, message: Message, userphone: UserPhone) -> bool:
        """
        Send a message with a file attachment to a contact.
        
        Args:
            contact: The contact to send the message to
            message: The message content and file to send
            userphone: The userphone to use for sending
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        # Acquire a lock based on userphone to respect rate limits
        await self.rate_limiter.acquire_lock(userphone.id)
        
        # Get the file path
        file_path = message.file.path if message.file else None
        
        if not file_path:
            self.logger.error(f"No file path available for message {message.id}")
            return False
            
        # Delegate to the file sender implementation
        success = await self.file_sender.send(contact, message, userphone, file_path)
        
        if success:
            # Log the successful message
            await self._log_message(contact, message, userphone)
            
        return success
    
    @sync_to_async
    def _log_message(self, contact: Contact, message: Message, 
                    userphone: UserPhone, target_list=None) -> None:
        """
        Log a successful message in the message logs.
        
        Args:
            contact: The contact the message was sent to
            message: The message that was sent
            userphone: The userphone used for sending
            target_list: Optional target list the contact belongs to
        """
        if self._test_mode:
            self.logger.info(f"TEST MODE: Would log message to {contact.phone}")
            return
            
        # Create message log entry
        log_entry = MessageLogs.objects.create(
            contact=contact,
            message=message,
            user=userphone.user,
            user_phone=userphone,
            status="sent",
            relationship_tag=target_list.contact_tag if target_list else contact.relationship_tag or '',
            sent_at=timezone.now()
        )
        self.logger.info(f"Message logged: {log_entry.id} to {contact.phone}")
    
    def set_test_mode(self, enabled: bool) -> None:
        """
        Enable or disable test mode for dry runs without actual sending.
        
        Args:
            enabled: True to enable test mode, False to disable
        """
        self._test_mode = enabled
        self.text_sender.set_test_mode(enabled)
        self.file_sender.set_test_mode(enabled)
        self.rate_limiter.set_test_mode(enabled)
        self.retry_strategy.set_test_mode(enabled)
    
    @property
    def test_mode(self) -> bool:
        """Get the current test mode status"""
        return self._test_mode