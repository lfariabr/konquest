# # messageShooter/services/queue_processor_v2.py
# import asyncio
# import logging
# from dataclasses import dataclass
# from datetime import datetime, timedelta
# from asgiref.sync import sync_to_async
# from django.utils import timezone

# from apiCrm.lead import Lead
# from apiCrm.utils.create_store import create_store
# from apiCrm.utils.create_region import create_region
# from messageShooter.services.get_message_for_contact import get_message_for_contact
# from core.models.userphone import UserPhone
# from messageShooter.utils.get_userphone import get_userphone, get_userphone_nps, get_userphone_reminder, get_userphone_vip

# logger = logging.getLogger(__name__)

# class QueueProcessor:
#     def __init__(self, test_mode=False):
#         self.logger = logger
#         self._locks = {}  # Phone locks for rate limiting
#         self._test_mode = test_mode
#         self.breath_time = 2  # seconds between messages to same phone
#         self.CONTACT_BATCH_SIZE = 200  # Default batch size

#     async def process_contacts_in_batches(self, contacts, target_list, batch_size=None):
#         """
#         Process contacts in batches to reduce IO pressure.
#         Returns aggregated results of the batched operations.
        
#         Args:
#             contacts: List of contacts to process
#             target_list: The target list containing the contacts
#             batch_size: Optional batch size override (default: self.CONTACT_BATCH_SIZE)
            
#         Returns:
#             Tuple of (processed_results, success_count, error_count)
#         """
#         if batch_size is None:
#             batch_size = self.CONTACT_BATCH_SIZE
            
#         total_contacts = len(contacts)
#         self.logger.info(f"Starting batch processing of {total_contacts} contacts")
        
#         # Split contacts into batches
#         batches = [contacts[i:i+batch_size] for i in range(0, total_contacts, batch_size)]
        
#         processed_results = {}
#         success_count = 0
#         error_count = 0
#         skipped_count = 0
        
#         for i, batch in enumerate(batches):
#             self.logger.info(f"Processing batch {i+1}/{len(batches)} ({len(batch)} contacts)")
            
#             # Process batch with all existing business logic
#             batch_results = await self._process_batch(batch, target_list)
            
#             # Parse results
#             for result in batch_results:
#                 contact_id = result.get("contact_id")
#                 if contact_id:
#                     processed_results[contact_id] = result
#                     if result.get("status") == "sent":
#                         success_count += 1
#                     elif result.get("status") == "skipped":
#                         skipped_count += 1
#                     elif result.get("status") in ["failed", "error"]:
#                         error_count += 1
            
#             # Add a small breath between batches to prevent IO spikes
#             if i < len(batches) - 1:  # Don't sleep after the last batch
#                 await asyncio.sleep(self.breath_time)
        
#         self.logger.info(f"Completed batch processing: {success_count} successful, {skipped_count} skipped, {error_count} errors")
#         return processed_results, success_count, error_count

#     async def _process_batch(self, contacts_batch, target_list):
#         """
#         Process a single batch of contacts, implementing bulk operations
#         for database writes where possible.
        
#         Args:
#             contacts_batch: List of contacts in this batch
#             target_list: The target list containing the contacts
            
#         Returns:
#             List of results, one per contact
#         """
#         results = []
        
#         # Use asyncio.gather for concurrent processing within the batch
#         tasks = [self._process_contact_in_batch(contact, target_list) for contact in contacts_batch]
#         batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
#         for result in batch_results:
#             if isinstance(result, Exception):
#                 # Log error but continue processing the batch
#                 self.logger.error(f"Error in batch processing: {str(result)}", exc_info=True)
#                 results.append({"status": "error", "error": str(result)})
#             else:
#                 results.append(result)
        
#         return results

#     async def _process_contact_in_batch(self, contact, target_list):
#         """
#         Optimized version of process_contact_async for batch context.
#         Maintains all essential business logic from the original process.
        
#         Args:
#             contact: The contact to process
#             target_list: The target list containing the contact
            
#         Returns:
#             Dict with processing results and status
#         """
#         try:
#             # Get message for this contact - reusing original logic
#             @sync_to_async
#             def get_message_for_contact_wrapper():
#                 return get_message_for_contact(contact, target_list)
            
#             counter, message = await get_message_for_contact_wrapper()
            
#             if not message:
#                 self.logger.info(f"📭 Skipping contact ({contact.phone}) - no message found for counter {counter}")
#                 return {
#                     "contact_id": str(contact.id),
#                     "status": "skipped",
#                     "processed_at": timezone.now().isoformat(),
#                     "message_counter": counter
#                 }

#             # Get appropriate userphone - reusing original logic
#             @sync_to_async
#             def get_userphone_wrapper():
#                 if target_list.contact_tag == 'NPS':
#                     # For NPS, get store-specific userphone
#                     phone, token = get_userphone_nps(target_list.contact_tag, contact.store)
#                     if phone and token:
#                         try:
#                             # Try to get existing UserPhone
#                             userphone = UserPhone.objects.get(
#                                 phone_number=phone,
#                                 relationship_tag=target_list.contact_tag
#                             )
#                             logger.info(f"Found existing UserPhone for NPS store {contact.store}")
#                             return userphone
#                         except UserPhone.DoesNotExist:
#                             # Create new UserPhone if it doesn't exist
#                             userphone = UserPhone.objects.create(
#                                 phone_number=phone,
#                                 phone_token=token,
#                                 relationship_tag=target_list.contact_tag,
#                                 user=contact.user
#                             )
#                             logger.info(f"Created new UserPhone for NPS store {contact.store}")
#                             return userphone
                
#                 elif target_list.contact_tag == 'Reminder':
#                     phone, token = get_userphone_reminder(target_list.contact_tag, contact.store)
                    
#                     if phone and token:
#                         try:
#                             # Try to get existing UserPhone
#                             userphone = UserPhone.objects.get(
#                                 phone_number=phone,
#                                 relationship_tag=target_list.contact_tag
#                             )
#                             logger.info(f"Found existing UserPhone for Reminder store {contact.store}")
#                             return userphone
#                         except UserPhone.DoesNotExist:
#                             # Create new UserPhone if it doesn't exist
#                             userphone = UserPhone.objects.create(
#                                 phone_number=phone,
#                                 phone_token=token,
#                                 relationship_tag=target_list.contact_tag,
#                                 user=contact.user,
#                                 phone_description=contact.store
#                             )
#                             logger.info(f"Created new UserPhone for Reminder store {contact.store}")
#                             return userphone

#                 elif target_list.contact_tag == 'VIP':
#                     phone, token = get_userphone_vip(target_list.contact_tag, contact.store)
                    
#                     if phone and token:
#                         try:
#                             # Try to get existing UserPhone
#                             userphone = UserPhone.objects.get(
#                                 phone_number=phone,
#                                 relationship_tag=target_list.contact_tag
#                             )
#                             logger.info(f"Found existing UserPhone for VIP store {contact.store}")
#                             return userphone
#                         except UserPhone.DoesNotExist:
#                             # Create new UserPhone if it doesn't exist
#                             userphone = UserPhone.objects.create(
#                                 phone_number=phone,
#                                 phone_token=token,
#                                 relationship_tag=target_list.contact_tag,
#                                 user=contact.user,
#                                 phone_description=contact.store
#                             )
#                             logger.info(f"Created new UserPhone for VIP store {contact.store}")
#                             return userphone
#                 else:
#                     # For non-NPS, use regular get_userphone
#                     userphone, token = get_userphone(target_list.contact_tag)
#                     return userphone
#                 return None

#             userphone = await get_userphone_wrapper()
#             if not userphone:
#                 self.logger.error(f"❌ No userphone found for contact {contact.phone}")
#                 return {
#                     "contact_id": str(contact.id),
#                     "status": "error",
#                     "error": "No userphone found",
#                     "processed_at": timezone.now().isoformat()
#                 }
            
#             # Apply rate limiting per phone - reusing original logic with minor batch optimizations
#             phone_key = f"phone_lock_{contact.phone}"
#             if phone_key in self._locks:
#                 self.logger.info(f"⏳ Waiting for rate limit on phone {contact.phone}...")
#                 await self._locks[phone_key].acquire()
#             else:
#                 self._locks[phone_key] = asyncio.Lock()
#                 await self._locks[phone_key].acquire()
            
#             try:
#                 # Use the process_contact_async method or its logic
#                 success, error_message = await self.process_contact_async(contact, message, userphone)
                
#                 # Log successful message send only if it's not a lead creation message
#                 if success and message.text not in ["Lead da campanha Botox", "Lead da campanha Preenchimento", "Lead da bio do Instagram"]:
#                     await sync_to_async(self._log_message)(contact, message, userphone, target_list)
                    
#                 return {
#                     "contact_id": str(contact.id),
#                     "status": "sent" if success else "failed",
#                     "processed_at": timezone.now().isoformat(),
#                     "error": error_message if not success else None,
#                     "message_counter": counter
#                 }
                
#             finally:
#                 if phone_key in self._locks:
#                     self._locks[phone_key].release()
#                     # The breath time is now managed at the batch level
                    
#         except Exception as e:
#             error_msg = f"Failed to process contact {contact.phone}: {str(e)}"
#             self.logger.error(error_msg, exc_info=True)
#             return {
#                 "contact_id": str(contact.id),
#                 "status": "failed",
#                 "processed_at": timezone.now().isoformat(),
#                 "error": error_msg
#             }

#     async def process_contact_async(self, contact, message, userphone):
#         """Process a single contact with rate limiting per userphone"""
#         try:
#             # If message text indicates lead creation, create lead instead of sending message
#             if message.text in ["Lead da campanha Botox", "Lead da campanha Preenchimento", "Lead da bio do Instagram"]:
#                 try:
#                     if "Botox" in message.text:
#                         campaign_name = "Botox"
#                     elif "Preenchimento" in message.text:
#                         campaign_name = "Preenchimento"
#                     elif "Instagram" in message.text:
#                         campaign_name = "Instagram"
                                        
#                     @sync_to_async
#                     def create_campaign_lead():
#                         # Create new Lead instance and set its attributes
#                         lead = Lead()
#                         lead.name = contact.name
#                         lead.phone = contact.phone
#                         lead.email = "campanha@whatsapp.com"
#                         lead.message = message.text
                        
#                         # Use utility functions to determine store and region
#                         store = create_store(contact.store)
#                         region = create_region(contact.region)
                        
#                         # Call create_leads_at_crm with the determined store and region
#                         response = lead.create_leads_at_crm(
#                             name=contact.name,
#                             phone=contact.phone,
#                             email="campanha@whatsapp.com",
#                             message=message.text,
#                             store=store,
#                             region=region,
#                             campaign=campaign_name
#                         )
                        
#                         return True, None
                    
#                     return await create_campaign_lead()
                    
#                 except Exception as e:
#                     error_msg = f"Error creating campaign lead: {str(e)}"
#                     self.logger.error(error_msg)
#                     return False, error_msg
#             else:
#                 # Regular message send logic
#                 if "file://" in message.text:
#                     # File message handling
#                     file_path = message.text.split("file://")[1].strip()
#                     return await self.send_file_message_async(contact, userphone, file_path)
#                 else:
#                     # Text message handling
#                     return await self.send_message_async(contact, userphone, message.text)
                
#         except Exception as e:
#             error_msg = f"Error processing contact: {str(e)}"
#             self.logger.error(error_msg)
#             return False, error_msg

#     async def send_message_async(self, contact, userphone, text):
#         """Send a text message to a contact"""
#         # Implementation of sending text message
#         # This would be your existing implementation
#         try:
#             # Your message sending implementation
#             return True, None
#         except Exception as e:
#             return False, str(e)

#     async def send_file_message_async(self, contact, userphone, file_path):
#         """Send a file message to a contact"""
#         # Implementation of sending file message
#         # This would be your existing implementation
#         try:
#             # Your file message sending implementation
#             return True, None
#         except Exception as e:
#             return False, str(e)

#     def _log_message(self, contact, message, userphone, target_list=None):
#         """Log a successful message send to the database"""
#         # Implementation of message logging
#         # This would be your existing implementation
#         pass