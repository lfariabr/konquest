from django.utils import timezone
from messageShooter.models.target_list import TargetList
from messageShooter.models.campaign import Campaign
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
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        logger.info(f"Processing campaign {campaign.id} - {campaign.name}")
        
        # Check if campaign is active and ready to run
        if not force_run and (campaign.campaign_status != "Active" or not campaign.is_ready_to_run()):
            logger.info("Campaign not active or not ready to run")
            return 0, 0, 0

        # Check if campaign should run today based on active days
        if not force_run and not campaign.should_run_today():
            logger.info("Campaign should not run today")
            return 0, 0, 0

        # Get contacts using appropriate resolver
        if campaign.contact_type == "Whatsapp":
            if campaign.contacts.exists():
                contacts = campaign.contacts.all()
                logger.info(f"Using {len(contacts)} contacts from campaign")
            else:
                contacts = get_contact_whatsapp(campaign.contact_type, campaign.contact_tag)
                logger.info(f"Using {len(contacts)} contacts from resolver")
        elif campaign.contact_type == "Appointment":
            if campaign.contacts.exists():
                contacts = campaign.contacts.all()
                logger.info(f"Using {len(contacts)} contacts from campaign")
            else:
                contacts = get_contact_appointment(campaign.contact_type, campaign.contact_tag)
                logger.info(f"Using {len(contacts)} contacts from resolver")
        else:
            raise ValueError(f"Invalid contact type: {campaign.contact_type}")

        created_count = 0
        skipped_count = 0
        error_count = 0

        # Process each contact
        for contact in contacts:
            try:
                # Get message based on campaign type
                if campaign.contact_type == "Whatsapp":
                    # For WhatsApp, use the next message in sequence based on counter
                    counter = get_counter_whatsapp(contact.phone, campaign.contact_tag)
                    message = get_message(campaign.contact_type, campaign.contact_tag, counter)
                    logger.info(f"Got message {message.id if message else 'None'} for counter {counter}")
                elif campaign.contact_type == "Appointment":
                    # For appointments, get message based on appointment status
                    counter = get_counter_appointment(contact.phone, campaign.contact_tag)
                    message = get_message(campaign.contact_type, campaign.contact_tag, counter)
                    logger.info(f"Got message {message.id if message else 'None'} for counter {counter}")
                else:
                    raise ValueError(f"Invalid contact type: {campaign.contact_type}")

                if not message:
                    logger.info(f"No message found for counter {counter}")
                    skipped_count += 1
                    continue

                # Get user phone for sending
                userphone, token = get_userphone(campaign.contact_tag)
                if not userphone:
                    logger.error("No userphone found")
                    error_count += 1
                    continue
                
                # First try to find a contact that already has the right tag
                existing_contact = Contact.objects.filter(
                    phone=contact.phone,
                    relationship_tag=campaign.contact_tag
                ).first()
                
                if existing_contact:
                    contact_to_use = existing_contact
                else:
                    # If no contact found with right tag, update this one
                    contact.relationship_tag = campaign.contact_tag
                    contact.save()
                    contact_to_use = contact
                
                # Create target list entry
                target = TargetList.objects.create(
                    contact=contact_to_use,
                    contact_phone=contact_to_use.phone,
                    contact_type=campaign.contact_type,
                    contact_tag=campaign.contact_tag,
                    reference_id=str(contact_to_use.id),
                    message=message,
                    userphone=userphone,
                    sequence_order=counter,
                    token=token,
                    sent_messages_count=0  # Initialize to 0, will be updated by signal handler
                )
                logger.info(f"Created target list {target.id} for contact {contact_to_use.name}")
                created_count += 1

            except Exception as e:
                logger.error(f"Error processing contact: {str(e)}")
                error_count += 1

        # Update campaign's last run time
        campaign.last_run = timezone.now()
        campaign.save()

        logger.info(f"Campaign {campaign.name} finished: {created_count} created, {skipped_count} skipped, {error_count} errors")
        return created_count, skipped_count, error_count

    except Exception as e:
        logger.error(f"Error processing campaign: {str(e)}")
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
