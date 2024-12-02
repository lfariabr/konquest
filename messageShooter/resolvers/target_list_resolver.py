from django.utils import timezone
from messageShooter.models.campaign import Campaign, FREQUENCY_ONCE
from messageShooter.models.target_list import TargetList
from messageShooter.resolvers.get_contacts import get_contact_whatsapp, get_contact_appointment
from messageShooter.resolvers.get_counter import get_counter_whatsapp, get_counter_appointment
from messageShooter.resolvers.get_message import get_message
from messageShooter.resolvers.get_userphone import get_userphone
from core.models.message import Message
from core.models.contact import Contact
import logging

logger = logging.getLogger(__name__)

def create_target_list(campaign_id, force_run=False):
    """
    Create target list entries for a campaign
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

        # Deletion of existing target list for this campaign
        existing_target_lists = TargetList.objects.filter(campaign=campaign)
        if existing_target_lists.exists():
            count = existing_target_lists.count()
            
            # First delete associated queue entries
            from messageShooter.models.queue import Queue
            queue_entries = Queue.objects.filter(target_list__in=existing_target_lists)
            queue_count = queue_entries.count()
            if queue_count > 0:
                logger.info(f"Cleaning up: Deleting {queue_count} queue entries and {count} target lists")
                queue_entries.delete()
                existing_target_lists.delete()
            else:
                logger.info(f"Cleaning up: Deleting {count} target lists")
                existing_target_lists.delete()
        
        # Check if campaign is active and ready to run
        if not force_run and (campaign.campaign_status != "Active" or not campaign.is_ready_to_run()):
            logger.info(f"Campaign '{campaign.name}' is not active or not ready to run")
            return 0, 0, 0

        # Check if campaign should run today based on active days
        if not force_run and not campaign.should_run_today():
            logger.info(f"Campaign '{campaign.name}' is not scheduled to run today")
            return 0, 0, 0

        # Get contacts based on campaign type
        if campaign.contact_type == "Whatsapp":
            contacts = get_contact_whatsapp(contact_type=campaign.contact_type, contact_tag=campaign.contact_tag)
        else:
            contacts = get_contact_appointment(contact_type=campaign.contact_type, contact_tag=campaign.contact_tag)
            
        if not contacts:
            logger.warning(f"No contacts found for campaign '{campaign.name}' with tag '{campaign.contact_tag}'")
            return created_count, skipped_count, error_count
        
        logger.info(f"Found {len(contacts)} contacts with tag '{campaign.contact_tag}'")
        
        # Process each contact
        for contact in contacts:
            try:
                # Get current message counter for contact
                if campaign.contact_type == "Whatsapp":
                    counter = get_counter_whatsapp(contact.phone, campaign.contact_tag)
                else:
                    counter = get_counter_appointment(contact.phone, campaign.contact_tag)
                    
                # Get message for current counter
                message = Message.objects.filter(
                    user=campaign.user,
                    relationship_tag=campaign.contact_tag,
                    counter=counter
                ).first()
                
                if not message:
                    logger.debug(f"No message found for counter {counter} - skipping contact {contact.id}")
                    skipped_count += 1
                    continue
                    
                # Update message contact type if not set
                if not message.contact_type:
                    message.contact_type = campaign.contact_type
                    message.save()
                    
                # Check if target list already exists
                existing = TargetList.objects.filter(
                    campaign=campaign,
                    contact=contact,
                    message__counter=counter,
                    status__in=['pending', 'processing', 'retrying']
                ).exists()
                
                if existing:
                    logger.debug(f"Target list already exists for contact {contact.id} - skipping")
                    skipped_count += 1
                    continue
                
                # Create target list entry
                target_list = TargetList.objects.create(
                    campaign=campaign,
                    contact=contact,
                    message=message,
                    contact_tag=campaign.contact_tag,
                    contact_type=campaign.contact_type,
                    contact_phone=contact.phone,
                    reference_id=str(contact.id),
                    userphone=campaign.userphone,
                    token=campaign.userphone.phone_token,
                    status='pending'
                )
                
                created_count += 1
                
                # If this is a one-time campaign and we've processed all contacts,
                # mark the campaign as completed
                if campaign.frequency == FREQUENCY_ONCE and created_count == len(contacts):
                    campaign.campaign_status = 'Completed'
                    campaign.save()
                    logger.info(f"One-time campaign '{campaign.name}' marked as completed")
                
            except Exception as e:
                logger.error(f"Error processing contact {contact.id}: {str(e)}")
                error_count += 1
                continue
        
        logger.info(f"Campaign '{campaign.name}' processing complete: {created_count} created, {skipped_count} skipped, {error_count} errors")
        return created_count, skipped_count, error_count
        
    except Exception as e:
        logger.error(f"Error in create_target_list: {str(e)}")
        return 0, 0, 1

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
