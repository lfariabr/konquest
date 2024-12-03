# messageShooter/services/queue_processor.py
import logging
import asyncio
from django.utils import timezone
from django.db import transaction
from asgiref.sync import sync_to_async
from messageShooter.models.queue import Queue
from apiSocialHub.resolvers.send_text_message import send_text_message
from apiSocialHub.resolvers.send_file_message import send_file_message
from core.models.messagelog import MessageLogs
from django.db.models import Q
from typing import List, Tuple, Dict, Any
import aiohttp
import time

logger = logging.getLogger(__name__)

class QueueProcessor:
    def __init__(self):
        """Initialize the queue processor"""
        self.max_retries = 3
        self.base_retry_delay = 5  # Base delay in minutes
        self.breath_time = 1  # Reduce from 10s to 1s between processing each contact
        self._userphone_locks = {}  # Track last send time per userphone
        self.logger = logging.getLogger(__name__)
        self._test_mode = False  # Flag for test mode
        
        # File upload settings
        self.max_file_size = 10 * 1024 * 1024  # 10MB limit
        self.large_file_threshold = 1 * 1024 * 1024  # 1MB threshold for progress logging
        self.chunk_size = 256 * 1024  # 256KB chunks for progress tracking

    async def get_phone_lock(self, userphone_id: int) -> float:
        """Get the last send time for a userphone and enforce breath time"""
        current_time = time.time()
        last_send_time = self._userphone_locks.get(userphone_id, 0)
        
        if not self._test_mode and current_time - last_send_time < self.breath_time:
            wait_time = self.breath_time - (current_time - last_send_time)
            await asyncio.sleep(wait_time)
        
        self._userphone_locks[userphone_id] = time.time()
        return current_time

    async def calculate_retry_delay(self, attempt: int) -> int:
        """Calculate exponential backoff delay in seconds"""
        if hasattr(self, '_test_mode') and self._test_mode:
            return 0  # No delays in test mode
        return min(300, (2 ** attempt) * self.base_retry_delay)

    async def process_with_retry(self, func, *args, **kwargs):
        """Execute a function with retry logic and exponential backoff"""
        attempt = 0
        last_error = None
        retryable_errors = (
            ConnectionError,
            ConnectionResetError,
            aiohttp.ClientError,
            TimeoutError
        )

        while attempt < self.max_retries:
            try:
                self.logger.info(f"Attempt {attempt + 1} of {self.max_retries}")
                result = await func(*args, **kwargs)
                if isinstance(result, tuple):
                    success, error = result
                    if success:
                        return result
                    # Only retry on connection errors
                    if isinstance(error, retryable_errors):
                        last_error = error
                    else:
                        return result  # Don't retry non-connection errors
                else:
                    return result
            except Exception as e:
                if isinstance(e, retryable_errors):
                    last_error = e
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed with retryable error: {str(e)}. "
                        f"Retrying..."
                    )
                else:
                    self.logger.error(f"Non-retryable error: {str(e)}")
                    raise  # Don't retry non-connection errors
            
            attempt += 1
            if attempt < self.max_retries:
                delay = await self.calculate_retry_delay(attempt)
                if delay > 0 and not self._test_mode:
                    self.logger.info(f"Waiting {delay} seconds before retry...")
                    await asyncio.sleep(delay)

        if isinstance(last_error, Exception):
            raise last_error
        return False, last_error

    async def process_contact_async(self, contact, message, userphone):
        """Process a single contact with rate limiting per userphone"""
        try:
            # Apply rate limiting per userphone
            await self.get_phone_lock(userphone.id)
            
            # Wrap send_message_async in process_with_retry
            success, error_message = await self.process_with_retry(
                self.send_message_async,
                contact=contact,
                message=message,
                userphone=userphone
            )
            
            return success, error_message

        except Exception as e:
            error_msg = f"Exception sending message to {contact.phone}: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    async def process_queues_async(self, max_concurrent: int = 3, batch_size: int = 50):
        """Process multiple queues concurrently and independently"""
        try:
            # Get pending queues
            pending_queues = await sync_to_async(list)(
                Queue.objects.filter(
                    status__in=['pending', 'retrying', 'interrupted']
                ).order_by('-priority', 'scheduled_time')[:batch_size]
            )
            
            if not pending_queues:
                self.logger.info("No pending queues to process")
                return 0, 0, 0

            total_queues = len(pending_queues)
            self.logger.info(f"🎯 Starting batch processing of {total_queues} queues independently...")
            
            # Process queues concurrently without semaphore
            tasks = [
                asyncio.create_task(self.process_queue_item_async(queue))
                for queue in pending_queues
            ]
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successes and errors
            success_count = len([r for r in results if isinstance(r, tuple) and r[0]])
            error_count = len([r for r in results if isinstance(r, tuple) and not r[0]])
            exception_count = len([r for r in results if isinstance(r, Exception)])
            
            self.logger.info(
                f"✅ Batch processing complete:\n"
                f"   - Total Queues: {total_queues}\n"
                f"   - Successful: {success_count}\n"
                f"   - Failed: {error_count}\n"
                f"   - Exceptions: {exception_count}"
            )
            
            return success_count, error_count, exception_count
            
        except Exception as e:
            self.logger.error(f"❌ Error in batch queue processing: {str(e)}")
            return 0, 0, 0
    
    async def process_queue_item_async(self, queue_item: Queue):
        """Process a single queue item asynchronously with enhanced error handling"""
        try:
            # Get related objects using sync_to_async
            @sync_to_async
            def get_related():
                if not queue_item.message or not queue_item.target_list:
                    raise ValueError("Queue item missing message or target list")
                contacts = list(queue_item.target_list.get_contacts())  # Evaluate queryset here
                return queue_item.message, queue_item.target_list, queue_item.userphone, contacts

            message, target_list, userphone, contacts = await get_related()
            total_contacts = len(contacts)
            
            self.logger.info(f"🔄 Queue {queue_item.id}: Starting to process {total_contacts} contacts...")

            processed_contacts = {}
            success_count = 0
            error_count = 0

            # Process contacts sequentially with breath time
            for idx, contact in enumerate(contacts):
                try:
                    self.logger.info(f"📱 Queue {queue_item.id}: Processing contact {idx + 1}/{total_contacts} ({contact.phone})")
                    success, error_message = await self.process_contact_async(contact, message, userphone)
                    
                    result = {
                        "status": "sent" if success else "failed",
                        "processed_at": timezone.now().isoformat(),
                        "error": error_message if not success else None
                    }
                    
                    processed_contacts[str(contact.id)] = result
                    
                    if success:
                        self.logger.info(f"✅ Queue {queue_item.id}: Successfully sent to contact {idx + 1}/{total_contacts} ({contact.phone})")
                        success_count += 1
                    else:
                        self.logger.error(f"❌ Queue {queue_item.id}: Failed to send to contact {idx + 1}/{total_contacts} ({contact.phone}): {error_message}")
                        error_count += 1

                    # Add breath time between contacts, but not after the last one
                    if idx < total_contacts - 1 and not self._test_mode:
                        self.logger.info(f"⏳ Queue {queue_item.id}: Waiting {self.breath_time} seconds before processing next contact...")
                        await asyncio.sleep(self.breath_time)
                        
                except Exception as e:
                    error_msg = str(e)
                    self.logger.error(
                        f"❌ Queue {queue_item.id}: Failed to process contact {idx + 1}/{total_contacts} ({contact.phone}): {error_msg}",
                        exc_info=True
                    )
                    processed_contacts[str(contact.id)] = {
                        "status": "failed",
                        "processed_at": timezone.now().isoformat(),
                        "error": error_msg
                    }
                    error_count += 1

            # Update queue status based on results
            if error_count == 0:
                status = 'completed'
                self.logger.info(f"✨ Queue {queue_item.id}: Completed successfully! {success_count}/{total_contacts} messages sent")
            elif success_count == 0:
                status = 'failed'
                self.logger.error(f"💥 Queue {queue_item.id}: Failed completely. {error_count}/{total_contacts} messages failed")
            else:
                status = 'partially_completed'
                self.logger.warning(f"⚠️ Queue {queue_item.id}: Partially completed. {success_count}/{total_contacts} sent, {error_count}/{total_contacts} failed")
            
            await sync_to_async(self._update_queue_status)(
                queue_item,
                status=status,
                processed_contacts=processed_contacts,
                sent_at=timezone.now()
            )

            self.logger.info(
                f"Queue {queue_item.id} processing completed. "
                f"Status: {status}, "
                f"Successful: {success_count}, "
                f"Failed: {error_count}"
            )
            
            return success_count > 0, None if success_count > 0 else "All messages failed"

        except Exception as e:
            error_msg = str(e)
            self.logger.error(
                f"Critical error processing queue {queue_item.id}: {error_msg}",
                exc_info=True
            )
            await sync_to_async(self._update_queue_status)(
                queue_item,
                status='failed',
                error_message=error_msg
            )
            return False, error_msg

    async def send_message_async(self, contact, message, userphone) -> Tuple[bool, str]:
        """Send a message to a contact asynchronously with proper error handling"""
        try:
            if message.file:
                file_size = message.file.size
                if file_size > self.max_file_size:
                    error_msg = f"File size ({file_size} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)"
                    self.logger.error(error_msg)
                    return False, error_msg
                
                if file_size > self.large_file_threshold:
                    self.logger.info(f"Large file detected ({file_size} bytes). This may take a while...")
                
                result = await send_file_message(
                    phone=contact.phone,
                    message=message.text,
                    token_socialhub=userphone.phone_token,
                    file_path=message.file.path
                )
            else:
                result = await send_text_message(
                    phone=contact.phone,
                    message=message.text,
                    token_socialhub=userphone.phone_token
                )
            
            if isinstance(result, dict) and result.get('success'):
                self.logger.info(f"Successfully sent message to {contact.phone}")
                return True, None
            else:
                error_msg = f"Failed to send message: {result}"
                self.logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Failed to send message to {contact.phone}: {str(e)}"
            self.logger.error(error_msg)
            raise  # Re-raise so process_with_retry can handle it

    async def resume_interrupted_queue(self, queue_item: Queue) -> Tuple[bool, bool]:
        """Resume an interrupted queue"""
        if queue_item.status != 'interrupted':
            return False, False

        try:
            # Update status to pending to allow reprocessing
            await sync_to_async(self._update_queue_status)(queue_item, 'pending')
            
            # Process the queue item
            success, error = await self.process_queue_item_async(queue_item)
            
            return success, error
            
        except Exception as e:
            self.logger.error(f"Error resuming queue {queue_item.id}: {str(e)}")
            await sync_to_async(self._update_queue_status)(
                queue_item,
                'interrupted',
                error_message=str(e)
            )
            return False, True

    @staticmethod
    def _update_queue_status(queue_item: Queue, status: str, processed_contacts: Dict = None, 
                           sent_at: Any = None, error_message: str = None) -> None:
        """Update queue status and related fields"""
        try:
            queue_item.status = status
            if processed_contacts is not None:
                queue_item.processed_contacts = processed_contacts
                queue_item.processed_count = len([c for c in processed_contacts.values() if c["status"] == "sent"])
            if sent_at:
                queue_item.sent_at = sent_at
            if error_message:
                queue_item.last_error = error_message
                logger.error(f"Queue {queue_item.id} error: {error_message}")
            queue_item.save()
            logger.info(f"Queue {queue_item.id} status updated to {status}")
        except Exception as e:
            logger.error(f"Error updating queue {queue_item.id} status: {str(e)}")
            raise

    @staticmethod
    def _log_message(contact, message, userphone) -> None:
        """Log a successful message send"""
        MessageLogs.objects.create(
            user=userphone.user,
            user_phone=userphone,
            contact=contact,
            message=message,
            status="sent",
            relationship_tag=contact.relationship_tag
        )
    
    # Keep existing sync methods for backward compatibility
    def process_queue(self, batch_size=50):
        """Process pending queue items (sync version)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.process_queues_async(batch_size=batch_size))
    
    def process_queue_item(self, queue_item):
        """Process a single queue item (sync version)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.process_queue_item_async(queue_item))
    
    def send_message(self, contact, message, userphone):
        """Send a message (sync version)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.send_message_async(contact, message, userphone))