from django.utils import timezone
from messageShooter.models.campaign import Campaign, FREQUENCY_ONCE
from messageShooter.models.target_list import TargetList
from messageShooter.resolvers.get_contacts import get_contact_whatsapp, get_contact_appointment
from messageShooter.resolvers.get_counter import get_counter_whatsapp, get_counter_appointment, bulk_get_counter_whatsapp, bulk_get_counter_appointment
from messageShooter.resolvers.get_message import get_message
from messageShooter.resolvers.get_userphone import get_userphone
from core.models.message import Message
from core.models.contact import Contact
import logging

logger = logging.getLogger(__name__)

def create_target_list(campaign_id, force_run=False):
    """
    Create target list entries for a campaign with optimized bulk operations
    Args:
        campaign_id: ID of the campaign
        force_run: If True, bypasses the ready-to-run checks
    Returns (created_count, skipped_count, error_count)
    """
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        # Get campaign
        campaign = Campaign.objects.get(id=campaign_id)
        logger.info(f"Processing campaign '{campaign.name}' (ID: {campaign_id})")

        # Bulk deletion of existing target lists and queue entries
        existing_target_lists = TargetList.objects.filter(campaign=campaign)
        if existing_target_lists.exists():
            count = existing_target_lists.count()
            from messageShooter.models.queue import Queue
            queue_count = Queue.objects.filter(target_list__in=existing_target_lists).delete()[0]
            target_count = existing_target_lists.delete()[0]
            logger.info(f"Cleaned up: Deleted {queue_count} queue entries and {target_count} target lists")

        # Early return checks
        if not force_run:
            if campaign.campaign_status != "Active" or not campaign.is_ready_to_run():
                logger.info(f"Campaign '{campaign.name}' is not active or not ready to run")
                return 0, 0, 0
            if not campaign.should_run_today():
                logger.info(f"Campaign '{campaign.name}' is not scheduled to run today")
                return 0, 0, 0

        # One-time campaign check
        if campaign.frequency == FREQUENCY_ONCE:
            if TargetList.objects.filter(
                campaign=campaign,
                contact_tag=campaign.contact_tag,
                status__in=['pending', 'processing']
            ).exists():
                logger.info(f"Target list already exists for one-time campaign '{campaign.name}'")
                return 0, 0, 0

        # Get all contacts
        contacts = (get_contact_whatsapp if campaign.contact_type == "Whatsapp" else get_contact_appointment)(
            contact_type=campaign.contact_type,
            contact_tag=campaign.contact_tag
        )
        
        if not contacts:
            logger.warning(f"No contacts found for campaign '{campaign.name}' with tag '{campaign.contact_tag}'")
            return created_count, skipped_count, error_count
        
        logger.info(f"Found {len(contacts)} contacts with tag '{campaign.contact_tag}'")
        
        # Pre-load counters for all contacts
        phones = [contact.phone for contact in contacts if contact.phone and contact.phone.isdigit()]
        if campaign.contact_type == "Whatsapp":
            counters = bulk_get_counter_whatsapp(phones, campaign.contact_tag)
        else:
            counters = bulk_get_counter_appointment(phones, campaign.contact_tag)
            
        # Pre-load all possible messages
        unique_counters = set(counters.values())
        messages = {
            counter: get_message(
                contact_type=campaign.contact_type,
                relationship_tag=campaign.contact_tag,
                counter=counter
            )
            for counter in unique_counters
        }
        
        # Pre-fetch existing target lists to avoid duplicate checks in loop
        existing_target_lists = set(
            TargetList.objects.filter(
                campaign=campaign,
                status__in=['pending', 'processing', 'retrying']
            ).values_list('contact_id', 'message__counter')
        )
        
        # Prepare bulk create list
        target_lists_to_create = []
        messages_to_update = set()
        
        # Process contacts
        for contact in contacts:
            try:
                if not contact.phone or not contact.phone.isdigit():
                    logger.debug(f"Invalid phone number for contact {contact.id} - skipping")
                    skipped_count += 1
                    continue

                counter = counters.get(contact.phone)
                message = messages.get(counter)
                
                if not message:
                    logger.debug(f"No message found for counter {counter} - skipping contact {contact.id}")
                    skipped_count += 1
                    continue
                    
                # Update message contact type if not set
                if not message.contact_type:
                    message.contact_type = campaign.contact_type
                    messages_to_update.add(message)
                    
                # Check for existing target list
                if (contact.id, counter) in existing_target_lists:
                    logger.debug(f"Target list already exists for contact {contact.id} - skipping")
                    skipped_count += 1
                    continue
                
                target_lists_to_create.append(
                    TargetList(
                        campaign=campaign,
                        contact=contact,
                        message=message,
                        contact_tag=campaign.contact_tag,
                        contact_type=campaign.contact_type,
                        contact_phone=contact.phone,
                        reference_id=str(contact.id),
                        userphone=campaign.userphone,
                        token=campaign.userphone.phone_token,
                        sent_messages_count=counter or 0,
                        status='pending'
                    )
                )
                created_count += 1
                
            except Exception as e:
                logger.error(f"Error processing contact {contact.id}: {str(e)}")
                error_count += 1
                continue
        
        # Bulk update messages
        if messages_to_update:
            Message.objects.bulk_update(list(messages_to_update), ['contact_type'])
            
        # Bulk create target lists
        if target_lists_to_create:
            TargetList.objects.bulk_create(target_lists_to_create, batch_size=1000)
            
        logger.info(f"Campaign processing complete. Created: {created_count}, Skipped: {skipped_count}, Errors: {error_count}")
        return created_count, skipped_count, error_count
        
    except Exception as e:
        logger.error(f"Error processing campaign {campaign_id}: {str(e)}")
        return created_count, skipped_count, error_count + 1

def clean_target_list():
    """
    Clean up old target list entries
    Returns number of entries deleted
    """
    # Delete entries older than 7 days
    cutoff_date = timezone.now() - timezone.timedelta(days=7)
    old_entries = TargetList.objects.filter(created_at__lt=cutoff_date)
    count = old_entries.count()
    old_entries.delete()
    return count

def reprioritize_by_tag(tag, new_priority):
    """
    Update priority for target list entries with specific tag.
    This is a placeholder for future tag-based priority adjustments.
    Currently, the system uses FIFO by default (priority=0).
    
    Args:
        tag (str): The contact_tag to reprioritize
        new_priority (int): The new priority value
    Returns:
        int: Number of entries updated
    """
    entries = TargetList.objects.filter(contact_tag=tag)
    count = entries.count()
    entries.update(priority=new_priority)
    return count

def generate_target_lists():
    """
    Generate target lists for all active campaigns that are ready to run.
    Returns the list of created target lists.
    """
    created_lists = []
    
    try:
        # Get active campaigns
        campaigns = Campaign.objects.filter(campaign_status="Active")
        logger.info(f"Found {len(campaigns)} active campaigns")
        
        for campaign in campaigns:
            try:
                if campaign.is_ready_to_run() and campaign.should_run_today():
                    created_count, skipped_count, error_count = create_target_list(campaign.id)
                    
                    if created_count > 0:
                        # Get newly created target lists for this campaign
                        new_lists = TargetList.objects.filter(
                            campaign=campaign,
                            status='pending'
                        ).order_by('created_at')
                        created_lists.extend(new_lists)
                        
                    logger.info(f"Campaign {campaign.name}: created={created_count}, skipped={skipped_count}, errors={error_count}")
                    
                    # Update campaign next run time
                    if campaign.frequency != FREQUENCY_ONCE:
                        campaign.update_next_run()
                        campaign.save()
                
            except Exception as e:
                logger.error(f"Error processing campaign {campaign.id}: {str(e)}")
                continue
        
        return created_lists
        
    except Exception as e:
        logger.error(f"Error in generate_target_lists: {str(e)}")
        return []
