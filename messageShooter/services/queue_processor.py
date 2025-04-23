# messageShooter/services/queue_processor.py
import logging
import asyncio
from asgiref.sync import sync_to_async
from messageShooter.models.queue import Queue
from core.models.messagelog import MessageLogs
from typing import Tuple, Dict, Any
from apiCrm.models.lead import Lead
from apiCrm.utils.create_store import create_store
from apiCrm.utils.create_region import create_region
from core.models.userphone import UserPhone
from django.utils import timezone

# NEW - Refactoring Queue Processor
from messageShooter.services.messaging.rate_limiter import RateLimiter
from messageShooter.services.retry.retry_strategy import RetryStrategy, RetryStrategyType
from messageShooter.services.messaging.message_sender import MessageSender

from messageShooter.services.contact_processor import ContactProcessor

# Process async
from messageShooter.services.get_message_for_contact import get_message_for_contact
from messageShooter.resolvers.get_userphone import get_userphone, get_userphone_nps, get_userphone_vip, get_userphone_reminder
from messageShooter.helpers.queue_suporter import get_userphone_async


logger = logging.getLogger(__name__)

class QueueProcessor:
    def __init__(self):
        """Initialize the queue processor"""
        self.max_retries = 5
        self.base_retry_delay = 6  # Base delay in minutes
        self._locks = {}  # Track locks per phone
        self.logger = logging.getLogger(__name__)

        # Command in progress handling
        self.command_in_progress_delay = 5  # Seconds to wait when command in progress 
        # File upload settings
        self.max_file_size = 10 * 1024 * 1024  # 10MB limit
        self.large_file_threshold = 1 * 1024 * 1024  # 1MB threshold for progress logging
        self.chunk_size = 256 * 1024  # 256KB chunks for progress tracking

        # Create rate limiter and retry strategy
        self.rate_limiter = RateLimiter(breath_time=30)
        self.retry_strategy = RetryStrategy(
            max_retries=self.max_retries,
            base_delay=self.base_retry_delay,
            strategy_type=RetryStrategyType.EXPONENTIAL
        )
        
        # create message sender
        self.message_sender = MessageSender(
            rate_limiter=self.rate_limiter,
            retry_strategy=self.retry_strategy
        )

        # NEW - create contact processor
        self.contact_processor = ContactProcessor(logger=self.logger)

    
    async def get_phone_lock(self, userphone_id: int) -> float:
        """
        Legacy method maintained for compatibility, delegates to rate_limiter
        """
        return await self.rate_limiter.acquire_lock(userphone_id)

    async def calculate_retry_delay(self, attempt: int) -> int:
        """
        Calculate exponential backoff delay in seconds
        This is a legacy method maintained for compatibility,
        delegates to retry_strategy.calculate_delay
        """
        return await self.retry_strategy.calculate_delay(attempt)

    async def process_with_retry(self, func, *args, **kwargs):
        """
        Execute a function with retry logic and exponential backoff
        This is a legacy method maintained for compatibility,
        delegates to retry_strategy.execute
        """
        return await self.retry_strategy.execute(func, *args, **kwargs)

    async def process_contact_async(self, contact, message, userphone):
        """Process a single contact with rate limiting per userphone"""
        try:
            # If message text indicates lead creation, create lead instead of sending message
            if message.text in ["Lead da campanha Botox", "Lead da campanha Preenchimento", "Lead da bio do Instagram"]:
                try:
                    if "Botox" in message.text:
                        campaign_name = "Botox"
                    elif "Preenchimento" in message.text:
                        campaign_name = "Preenchimento"
                    elif "Instagram" in message.text:
                        campaign_name = "Instagram"
                                        
                    @sync_to_async
                    def create_campaign_lead():
                        # Create new Lead instance and set its attributes
                        lead = Lead()
                        lead.name = contact.name
                        lead.phone = contact.phone
                        lead.email = "campanha@whatsapp.com"
                        lead.message = message.text
                        
                        # Use utility functions to determine store and region
                        store = create_store(contact.store)
                        region = create_region(contact.region)
                        
                        # Call create_leads_at_crm with the determined store and region
                        response = lead.create_leads_at_crm(
                            name=contact.name,
                            phone=contact.phone,
                            email="campanha@whatsapp.com",
                            message=message.text,
                            store=store,
                            region=region
                        )
                        
                        if response and 'data' in response and 'createLead' in response['data']:
                            contact.is_lead = True
                            contact.lead_created_at = timezone.now()
                            contact.save()
                            
                            MessageLogs.objects.create(
                                message=message,
                                user=contact.user,
                                user_phone=None,  # Since this is a lead creation, no user phone
                                contact=contact,
                                status="sent",
                                relationship_tag=f"{campaign_name}"
                            )
                            self.logger.info(f"Lead created and logged for {contact.phone} in campaign {campaign_name}")
                            return True, None
                        return False, "Failed to create lead in CRM"

                    lead_success, lead_error = await create_campaign_lead()
                    if not lead_success:
                        self.logger.error(f"Failed to create lead for {contact.phone}: {lead_error}")
                        return False, lead_error
                    
                    # Add delay after successful lead creation
                    self.logger.info("Resting 8 minutes before creating next lead...")
                    await asyncio.sleep(480)
                    
                    # Return here after successful lead creation to prevent message sending
                    return True, None
                    
                except Exception as e:
                    error_message = f"Error creating lead for {contact.phone}: {str(e)}"
                    self.logger.error(error_message)
                    return False, error_message
            
            elif message.file:  # Check if there is a file associated with the message
                try:
                    # Use the new message_sender for file messages
                    success = await self.message_sender.send_file_message(contact, message, userphone)
                    return success, None if success else "Failed to send file message"
                except Exception as e:
                    error_message = f"Error sending file message to {contact.phone}: {str(e)}"
                    self.logger.error(error_message)
                    return False, error_message

            # else, if just a text message:
            else:
                try:
                    # Use the new message_sender for text messages 
                    success = await self.message_sender.send_text_message(contact, message, userphone)

                    if success:
                        # Update contact message counter
                        @sync_to_async
                        def update_contact_counter():
                            if "botox" in message.relationship_tag.lower():
                                contact.botox_messages_sent += 1
                            elif "preenchimento" in message.relationship_tag.lower():
                                contact.preenchimento_messages_sent += 1
                            contact.last_message_sent_at = timezone.now()
                            contact.save(update_fields=['botox_messages_sent', 'preenchimento_messages_sent', 'last_message_sent_at'])
                        
                        await update_contact_counter()
                    
                    return success, None if success else "Failed to send text message"
                except Exception as e:
                    error_message = f"Error sending text message to {contact.phone}: {str(e)}"
                    self.logger.error(error_message)
                    return False, error_message

        except Exception as e:
            error_message = f"Error processing contact {contact.phone}: {str(e)}"
            self.logger.error(error_message)
            return False, error_message

    async def send_message_async(self, contact, message, userphone):
        """Send message asynchronously by delegating to message_sender"""
        return await self.message_sender.send_text_message(contact, message, userphone)

    
    ######## NEW
    async def send_file_message_async(self, contact, message, userphone, file_path=None):
        """Send file message asynchronously by delegating to message_sender"""
        return await self.message_sender.send_file_message(contact, message, userphone, file_path)

    async def process_queues_async(self, pending_queues=None, max_concurrent: int = 10, batch_size: int = 50):
        """Process multiple queues concurrently and independently"""
        try:
            # Get pending queues if not provided
            if pending_queues is None:
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
            
            # Create a semaphore to limit concurrent queues
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def process_with_semaphore(queue: Queue) -> None:
                """Wrapper to process a queue using the semaphore for concurrency control"""
                async with semaphore:
                    try:
                        success, error = await self.process_queue_item_async(queue)
                        return success, error, queue.id
                    except Exception as e:
                        self.logger.error(f"❌ Error processing queue {queue.id}: {str(e)}")
                        await sync_to_async(self._update_queue_status)(
                            queue,
                            'failed',
                            error_message=str(e)
                        )
                        return False, str(e), queue.id
            
            # Create tasks with semaphore control
            tasks = [
                asyncio.create_task(process_with_semaphore(queue))
                for queue in pending_queues
            ]
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            success_count = 0
            error_count = 0
            exception_count = 0
            
            for result in results:
                if isinstance(result, Exception):
                    exception_count += 1
                    self.logger.error(f"❌ Queue processing exception: {str(result)}")
                else:
                    success, error, queue_id = result
                    if success:
                        success_count += 1
                        self.logger.info(f"✅ Queue {queue_id} completed successfully")
                    else:
                        error_count += 1
                        self.logger.error(f"❌ Queue {queue_id} failed: {error}")
            
            self.logger.info(
                f"✅ Batch processing complete:\n"
                f"   - Total Queues: {total_queues}\n"
                f"   - Successful: {success_count}\n"
                f"   - Failed: {error_count}\n"
                f"   - Exceptions: {exception_count}"
            )

            # Import both functions and the stores list
            from apiSocialHub.resolvers.monitor import (
                send_invalid_tokens_notification,
                queue_finished,
                stores_with_invalid_token
            )
            
            # Send invalid tokens notification if there are any invalid tokens
            if len(stores_with_invalid_token) > 0:
                self.logger.info(f"Found {len(stores_with_invalid_token)} stores with invalid tokens. Sending notification...")
                send_invalid_tokens_notification()
            
            # Always send the queue completion notification
            queue_finished()

            return success_count, error_count, exception_count
            
        except Exception as e:
            self.logger.error(f"❌ Error in batch queue processing: {str(e)}")
            return 0, 0, 1

    async def process_queue_item_async(self, queue_item: Queue):
        """Process a single queue item asynchronously with enhanced error handling"""
        try:
            
            # Get related objects using sync_to_async
            @sync_to_async
            def get_related():
                if not queue_item.target_list:
                    raise ValueError("Queue item missing target list")
                contacts = list(queue_item.target_list.get_contacts())  # Evaluate queryset here
                return queue_item.target_list, contacts

            target_list, contacts = await get_related()
            total_contacts = len(contacts)
            
            self.logger.info(f"🔄 Queue {queue_item.id}: Starting to process {total_contacts} contacts...")

            processed_contacts = {}
            success_count = 0
            error_count = 0

            # Process contacts sequentially with breath time
            for idx, contact in enumerate(contacts, 1):
                try:
                    self.logger.info(f"📱 Queue {queue_item.id}: Processing contact {idx}/{total_contacts} ({contact.phone})")
                    
                    counter, message = await sync_to_async(get_message_for_contact)(contact, target_list)
                    
                    if not message:
                        self.logger.info(f"📭 Queue {queue_item.id}: Skipping contact {idx}/{total_contacts} ({contact.phone}) - no message found for counter {counter}")
                        processed_contacts[str(contact.id)] = {
                            "status": "skipped",
                            "processed_at": timezone.now().isoformat(),
                            "message_counter": counter
                        }
                        continue

                    userphone, token = await get_userphone_async(contact, target_list)

                    if not userphone:
                        self.logger.error(f"❌ Queue {queue_item.id}: No userphone found for contact {contact.phone}")
                        processed_contacts[str(contact.id)] = {
                            "status": "error",
                            "error": "No userphone found",
                            "processed_at": timezone.now().isoformat()
                        }
                        error_count += 1
                        continue
                    
                    # Apply rate limiting per phone
                    phone_key = f"phone_lock_{contact.phone}"
                    if phone_key in self._locks:
                        self.logger.info(f"⏳ Waiting for rate limit on phone {contact.phone}...")
                        await self._locks[phone_key].acquire()
                    else:
                        self._locks[phone_key] = asyncio.Lock()
                        await self._locks[phone_key].acquire()
                    
                    try:
                        success, error_message = await self.process_contact_async(contact, message, userphone)
                        
                        # Log successful message send only if it's not a lead creation message
                        if success and message.text not in ["Lead da campanha Botox", "Lead da campanha Preenchimento", "Lead da bio do Instagram"]:
                            await sync_to_async(self._log_message)(contact, message, userphone, target_list)
                        
                    finally:
                        if phone_key in self._locks:
                            self._locks[phone_key].release()
                            # Add breath time after release
                            if not self.rate_limiter._test_mode and idx < total_contacts:
                                # await asyncio.sleep(self.rate_limiter.breath_time)
                                await self.rate_limiter.acquire_lock(userphone.id)
                    
                    result = {
                        "status": "sent" if success else "failed",
                        "processed_at": timezone.now().isoformat(),
                        "error": error_message if not success else None,
                        "message_counter": counter
                    }
                    
                    processed_contacts[str(contact.id)] = result
                    
                    if success:
                        self.logger.info(f"✅ Queue {queue_item.id}: Successfully sent message {counter} to contact {idx}/{total_contacts} ({contact.phone})")
                        success_count += 1
                    else:
                        self.logger.error(f"❌ Queue {queue_item.id}: Failed to send to contact {idx}/{total_contacts} ({contact.phone}): {error_message}")
                        error_count += 1

                except Exception as e:
                    error_msg = f"Failed to process contact {idx}/{total_contacts}: {str(e)}"
                    self.logger.error(error_msg)
                    error_count += 1
                    processed_contacts[str(contact.id)] = {
                        "status": "failed",
                        "processed_at": timezone.now().isoformat(),
                        "error": error_msg
                    }

            # Determine final status
            final_status = 'sent'
            if success_count == 0:
                final_status = 'failed'
            elif error_count > 0:
                final_status = 'sent'

            # Update queue status
            await sync_to_async(self._update_queue_status)(
                queue_item,
                final_status,
                processed_contacts,
                sent_at=timezone.now() if success_count > 0 else None
            )

            # Use consistent log message format
            status_msg = (
                f"✨ Queue {queue_item.id}: Completed successfully! {success_count}/{total_contacts} messages sent"
                if final_status == 'sent' and success_count == total_contacts
                else f"⚠️ Queue {queue_item.id}: Partially completed. {success_count}/{total_contacts} sent, {error_count}/{total_contacts} failed"
                if final_status == 'sent' and error_count > 0
                else f"💥 Queue {queue_item.id}: Failed completely. {error_count}/{total_contacts} messages failed"
            )
            self.logger.info(status_msg)

            return True, None

        except Exception as e:
            error_msg = f"Error processing queue {queue_item.id}: {str(e)}"
            self.logger.error(error_msg)
            await sync_to_async(self._update_queue_status)(
                queue_item,
                'failed',
                error_message=error_msg
            )
            return False, error_msg

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
    def _log_message(contact, message, userphone, target_list=None) -> None:
        """Log a successful message send"""
        MessageLogs.objects.create(
            user=userphone.user,
            user_phone=userphone,
            contact=contact,
            message=message,
            status="sent",
            relationship_tag=target_list.contact_tag if target_list else contact.relationship_tag  # Use contact_tag here
        )
    
    # Keep existing sync methods for backward compatibility
    def process_queue(self, batch_size=50):
        """Process pending queue items (sync version)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.process_queues_async(batch_size=batch_size))
    
    def send_message(self, contact, message, userphone):
        """Send a message (sync version)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.send_message_async(contact, message, userphone))
    
    @property
    def test_mode(self):
        return self.rate_limiter._test_mode
        
    def set_test_mode(self, enabled: bool) -> None:
        self.rate_limiter.set_test_mode(enabled)
        self.retry_strategy.set_test_mode(enabled)  