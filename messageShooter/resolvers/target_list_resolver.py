from django.utils import timezone
from messageShooter.models.target_list import TargetList
from messageShooter.models.campaign import Campaign
from messageShooter.resolvers.get_contacts import get_contact_whatsapp, get_contact_appointment
from messageShooter.resolvers.get_counter import get_counter_whatsapp, get_counter_appointment
from messageShooter.resolvers.get_message import get_message
from messageShooter.resolvers.get_userphone import get_userphone
from core.models.message import Message
import logging

logger = logging.getLogger(__name__)

def create_target_list(campaign_id):
    """
    Create target list entries for a campaign
    Returns (created_count, skipped_count, error_count)
    """
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        logger.info(f"Processing campaign {campaign.name} (ID: {campaign.id})")
        
        # Check if campaign is active and ready to run
        if campaign.campaign_status != "Active" or not campaign.is_ready_to_run():
            logger.info(f"Campaign {campaign.name} is not active or not ready to run")
            return 0, 0, 0

        # Check if campaign should run today based on active days
        if not campaign.should_run_today():
            logger.info(f"Campaign {campaign.name} should not run today")
            return 0, 0, 0

        # Get contacts using appropriate resolver
        if campaign.contact_type == "Whatsapp":
            contacts = get_contact_whatsapp(campaign.contact_type, campaign.contact_tag)
        elif campaign.contact_type == "Appointment":
            contacts = get_contact_appointment(campaign.contact_type, campaign.contact_tag)
        else:
            raise ValueError(f"Invalid contact type: {campaign.contact_type}")

        logger.info(f"Found {len(contacts)} contacts for campaign {campaign.name}")

        created_count = 0
        skipped_count = 0
        error_count = 0

        # Process each contact
        for contact in contacts:
            try:
                # Get message based on campaign type
                if campaign.contact_type == "Whatsapp":
                    # For WhatsApp, use the next message in sequence based on counter
                    counter = get_counter_whatsapp(contact.id)
                    if counter >= len(campaign.sequential_order):
                        logger.info(f"Skipping contact {contact.id} - no more messages in sequence")
                        skipped_count += 1
                        continue
                        
                    message_id = campaign.sequential_order[counter]['message_id']
                    message = Message.objects.get(id=message_id)
                    sequence_order = counter
                    
                elif campaign.contact_type == "Appointment":
                    # For Appointment, check days_interval
                    for sequence_idx, order in enumerate(campaign.sequential_order):
                        days_interval = order['days_interval']
                        reference_date = contact.appointment_date if hasattr(contact, 'appointment_date') else contact.created_at
                        target_date = reference_date + timezone.timedelta(days=days_interval)
                        
                        if target_date.date() == timezone.now().date():
                            message_id = order['message_id']
                            message = Message.objects.get(id=message_id)
                            sequence_order = sequence_idx
                            break
                    else:
                        logger.info(f"Skipping contact {contact.id} - not the right day for any interval")
                        skipped_count += 1
                        continue

                # Skip if target list already exists for this contact and message
                if TargetList.objects.filter(
                    contact=contact,
                    message=message,
                    status__in=['pending', 'processing']
                ).exists():
                    skipped_count += 1
                    continue

                # Create target list entry
                target_list = TargetList.objects.create(
                    contact=contact,
                    contact_type=campaign.contact_type,
                    contact_tag=campaign.contact_tag,
                    contact_phone=contact.phone,
                    message=message,
                    userphone=campaign.userphone,
                    token=campaign.userphone.phone_token,
                    sequence_order=sequence_order,
                    days_interval=days_interval if campaign.contact_type == "Appointment" else None
                )
                created_count += 1
                logger.info(f"Created target list for contact {contact.id}, message {message.id}, sequence {sequence_order}")

            except Exception as e:
                logger.error(f"Error creating target list for contact {contact.id}: {str(e)}")
                error_count += 1

        # Update campaign's last run time
        campaign.last_run = timezone.now()
        campaign.save()

        return created_count, skipped_count, error_count

    except Exception as e:
        logger.error(f"Error processing campaign {campaign_id}: {str(e)}")
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
    logger.info("Starting target list generation")
    created_lists = []
    
    # Get all campaigns
    campaigns = Campaign.objects.all()
    logger.info(f"Found {len(campaigns)} campaigns")
    
    for campaign in campaigns:
        logger.info(f"Processing campaign {campaign.name}")
        # Check if campaign should run
        if campaign.campaign_status != "Active" or not campaign.is_ready_to_run():
            logger.info(f"Campaign {campaign.name} is not active or not ready to run")
            continue
            
        if not campaign.should_run_today():
            logger.info(f"Campaign {campaign.name} should not run today")
            continue
            
        # Generate target list for this campaign
        created, skipped, errors = create_target_list(campaign.id)
        logger.info(f"Campaign {campaign.name}: {created} created, {skipped} skipped, {errors} errors")
        
        if created > 0:
            # Get the newly created target lists for this campaign
            new_lists = TargetList.objects.filter(
                contact_tag=campaign.contact_tag,
                status='pending'
            ).order_by('-created_at')[:created]
            
            created_lists.extend(new_lists)
    
    logger.info(f"Target list generation complete. Created {len(created_lists)} lists")
    return created_lists
