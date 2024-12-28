# messageShooter/services/queue_processor.py
import time
import logging
import asyncio
import aiohttp
from django.utils import timezone
from django.db import transaction
from asgiref.sync import sync_to_async
from messageShooter.models.queue import Queue
from apiSocialHub.resolvers.send_text_message import send_text_message
from apiSocialHub.resolvers.send_file_message import send_file_message
from core.models.messagelog import MessageLogs
from core.models.message import Message
from django.db.models import Q
from typing import List, Tuple, Dict, Any
from apiCrm.models.lead import Lead
from apiCrm.utils.create_store import create_store
from apiCrm.utils.create_region import create_region
from messageShooter.services.get_message_for_contact import get_message_for_contact
from core.models.userphone import UserPhone

logger = logging.getLogger(__name__)

class QueueProcessor:
    def __init__(self):
        """Initialize the queue processor"""
        self.max_retries = 3
        self.base_retry_delay = 5  # Base delay in minutes
        self.breath_time = 15  # Increased from 8s to 15s between processing each contact
        self._userphone_locks = {}  # Track last send time per userphone
        self._locks = {}  # Track locks per phone
        self.logger = logging.getLogger(__name__)
        self._test_mode = False  # Flag for test mode
        
        # Command in progress handling
        self.command_in_progress_delay = 5  # Seconds to wait when command in progress
        
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
                
                # For successful responses
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
                    
            except retryable_errors as e:
                last_error = e
                self.logger.warning(
                    f"Attempt {attempt + 1} failed with retryable error: {str(e)}. "
                    f"Retrying..."
                )
                
                # Increment attempt and apply backoff
                attempt += 1
                if attempt < self.max_retries:
                    delay = await self.calculate_retry_delay(attempt)
                    if delay > 0 and not self._test_mode:
                        self.logger.info(f"Waiting {delay} seconds before retry...")
                        await asyncio.sleep(delay)
                continue
                
            except Exception as e:
                self.logger.error(f"Non-retryable error: {str(e)}")
                raise  # Don't retry non-connection errors
            
            attempt += 1

        if isinstance(last_error, Exception):
            raise last_error
        return False, last_error

    async def process_contact_async(self, contact, message, userphone):
        """Process a single contact with rate limiting per userphone"""
        try:
            # If message text indicates lead creation, create lead instead of sending message
            if message.text in ["Lead da campanha Botox", "Lead da campanha Preenchimento"]:
                try:
                    campaign_name = "Botox" if "Botox" in message.text else "Preenchimento"
                    
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
                            time.sleep(60)
                            print("Resting 60 seconds before creating next lead...")
                            return True, None
                        return False, "Failed to create lead in CRM"

                    lead_success, lead_error = await create_campaign_lead()
                    if not lead_success:
                        self.logger.error(f"Failed to create lead for {contact.phone}: {lead_error}")
                        return False, lead_error
                    
                    # Return here after successful lead creation to prevent message sending
                    return True, None
                    
                except Exception as e:
                    error_message = f"Error creating lead for {contact.phone}: {str(e)}"
                    self.logger.error(error_message)
                    return False, error_message
            
            ##### NEW
            elif message.file:  # Check if there is a file associated with the message
                if message.file:  # Ensure the file field is not empty
                    try:
                        file_path = message.file.path
                        success, error_message = await self.process_with_retry(
                            self.send_file_message_async,
                            contact,
                            message,
                            userphone,
                            file_path
                        )
                        return success, error_message
                    except Exception as e:
                        self.logger.error(f"Error sending file message to {contact.phone}: {str(e)}")
                else:
                    error_message = f"No file associated with message for {contact.phone}"
                    self.logger.error(error_message)
                    return False, error_message

            # else, if just a text message:
            else:
                success, error_message = await self.process_with_retry(
                    self.send_message_async,
                    contact,
                    message,
                    userphone
                )
                
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
                
                return success, error_message

        except Exception as e:
            error_message = f"Error processing contact {contact.phone}: {str(e)}"
            self.logger.error(error_message)
            return False, error_message

    async def send_message_async(self, contact, message, userphone):
        """Send message asynchronously by wrapping sync functions in to_thread"""
        try:
            # Wrap the synchronous send_text_message in to_thread
            result = await asyncio.to_thread(
                send_text_message,
                phone=contact.phone,
                message=message.text,
                token_socialhub=userphone.phone_token
            )
            
            # Handle async mock in tests
            if hasattr(result, '__await__'):
                result = await result
            
            if isinstance(result, dict) and result.get('success', False):
                return True, None
            else:
                error_msg = f"Failed to send message to {contact.phone}: {result.get('message', 'Unknown error')}"
                self.logger.error(error_msg)
                return False, error_msg

        except Exception as e:
            error_msg = f"Failed to send message to {contact.phone}: {str(e)}"
            self.logger.error(error_msg)
            if isinstance(e, (ConnectionError, ConnectionResetError)):
                raise  # Let process_with_retry handle connection errors
            return False, error_msg
    
    ######## NEW
    async def send_file_message_async(self, contact, message, userphone, file_path):
        """Send file message asynchronously by wrapping sync functions in to_thread"""
        try:
            result = await asyncio.to_thread(
                send_file_message,
                phone=contact.phone,
                message=message.text,
                token_socialhub=userphone.phone_token,
                file_path=file_path,
            )

            if isinstance(result, dict) and result.get('success', False):
                return True, None
            else:
                error_msg = result.get('error', 'Unknown error')
                self.logger.error(f"Failed to send message to {contact.phone}: {error_msg}")
                return False, error_msg

        except Exception as e:
            error_msg = f"Exception while sending file message to {contact.phone}: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    async def process_queues_async(self, pending_queues=None, max_concurrent: int = 3, batch_size: int = 50):
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
            
            return success_count, error_count, exception_count
            
        except Exception as e:
            self.logger.error(f"❌ Error in batch queue processing: {str(e)}")
            return 0, 0, 1

    async def process_queue_item_async(self, queue_item: Queue):
        """Process a single queue item asynchronously with enhanced error handling"""
        try:
            from messageShooter.resolvers.get_counter import get_counter_whatsapp
            from messageShooter.resolvers.get_message import get_message
            from messageShooter.resolvers.get_userphone import get_userphone, get_userphone_nps

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
                    
                    @sync_to_async
                    def get_message_for_contact_wrapper():
                        return get_message_for_contact(contact, target_list)
                    counter, message = await get_message_for_contact_wrapper()
                    
                    if not message:
                        self.logger.info(f"📭 Queue {queue_item.id}: Skipping contact {idx}/{total_contacts} ({contact.phone}) - no message found for counter {counter}")
                        processed_contacts[str(contact.id)] = {
                            "status": "skipped",
                            "processed_at": timezone.now().isoformat(),
                            "message_counter": counter
                        }
                        continue

                    # Get appropriate userphone based on contact tag
                    @sync_to_async
                    def get_userphone_wrapper():
                        if target_list.contact_tag == 'NPS':
                            # For NPS, get store-specific userphone
                            phone, token = get_userphone_nps(target_list.contact_tag, contact.store)
                            if phone and token:
                                try:
                                    # Try to get existing UserPhone
                                    userphone = UserPhone.objects.get(
                                        phone_number=phone,
                                        relationship_tag=target_list.contact_tag
                                    )
                                    return userphone
                                except UserPhone.DoesNotExist:
                                    # Create new UserPhone if it doesn't exist
                                    userphone = UserPhone.objects.create(
                                        phone_number=phone,
                                        phone_token=token,
                                        relationship_tag=target_list.contact_tag,
                                        user=contact.user
                                    )
                                    logger.info(f"Created new UserPhone for NPS store {contact.store}")
                                    return userphone
                        else:
                            # For non-NPS, use regular get_userphone
                            userphone, token = get_userphone(target_list.contact_tag)
                            return userphone
                        return None

                    userphone = await get_userphone_wrapper()
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
                        if success and message.text not in ["Lead da campanha Botox", "Lead da campanha Preenchimento"]:
                            await sync_to_async(self._log_message)(contact, message, userphone, target_list)
                        
                    finally:
                        if phone_key in self._locks:
                            self._locks[phone_key].release()
                            # Add breath time after release
                            if not self._test_mode and idx < total_contacts:
                                await asyncio.sleep(self.breath_time)
                    
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
    def send_message(self, contact, message, userphone):
        """Send a message (sync version)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.send_message_async(contact, message, userphone))