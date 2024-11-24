from django.utils import timezone
from messageShooter.models.target_list import TargetList
from messageShooter.models.campaign import Campaign
from messageShooter.resolvers.get_contacts import get_contact_whatsapp, get_contact_appointment
from messageShooter.resolvers.get_counter import get_counter_whatsapp, get_counter_appointment
from messageShooter.resolvers.get_message import get_message
from messageShooter.resolvers.get_userphone import get_userphone
from core.models.messagelog import MessageLogs
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
            counter = get_counter_whatsapp(campaign.contact_type, campaign.contact_tag)
        elif campaign.contact_type == "Appointment":
            contacts = get_contact_appointment(campaign.contact_type, campaign.contact_tag)
            counter = get_counter_appointment(campaign.contact_type, campaign.contact_tag)
        else:
            raise ValueError(f"Invalid contact type: {campaign.contact_type}")

        logger.info(f"Found {len(contacts)} contacts for campaign {campaign.name}")

        # Get message and userphone
        message = get_message(campaign.contact_type, campaign.contact_tag, counter)
        if not message:
            logger.error(f"No message found for {campaign.contact_type}/{campaign.contact_tag}")
            raise ValueError(f"No message found for {campaign.contact_type}/{campaign.contact_tag}")

        userphone, token = get_userphone(campaign.contact_tag)
        if not userphone or not token:
            logger.error(f"No userphone/token found for tag: {campaign.contact_tag}")
            raise ValueError(f"No userphone/token found for tag: {campaign.contact_tag}")

        created_count = 0
        skipped_count = 0
        error_count = 0

        for contact in contacts:
            try:
                # Check if contact already in target list
                existing = TargetList.objects.filter(
                    contact=contact,
                    contact_type=campaign.contact_type,
                    contact_tag=campaign.contact_tag,
                    status='pending'
                ).exists()

                if existing:
                    logger.info(f"Contact {contact.phone} already in target list")
                    skipped_count += 1
                    continue

                # Check message frequency rules
                if campaign.frequency != "Once":
                    sent_today = MessageLogs.objects.filter(
                        contact=contact,
                        relationship_tag=campaign.contact_tag,
                        sent_at__date=timezone.now().date()
                    ).exists()

                    if sent_today:
                        logger.info(f"Contact {contact.phone} already received message today")
                        skipped_count += 1
                        continue

                # Create target list entry
                TargetList.objects.create(
                    contact=contact,
                    contact_phone=contact.phone,
                    contact_type=campaign.contact_type,
                    contact_tag=campaign.contact_tag,
                    reference_id=str(contact.id),
                    sent_messages_count=0,
                    userphone=userphone,
                    message=message,
                    priority=0,  # Default priority for FIFO
                    status='pending'
                )
                logger.info(f"Created target list entry for contact {contact.phone}")
                created_count += 1

            except Exception as e:
                logger.error(f"Error processing contact {contact.id}: {str(e)}")
                error_count += 1

        logger.info(f"Campaign {campaign.name} processed: {created_count} created, {skipped_count} skipped, {error_count} errors")
        return created_count, skipped_count, error_count

    except Campaign.DoesNotExist:
        logger.error(f"Campaign with id {campaign_id} does not exist")
        raise ValueError(f"Campaign with id {campaign_id} does not exist")
    except Exception as e:
        logger.error(f"Error creating target list: {str(e)}")
        raise Exception(f"Error creating target list: {str(e)}")

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
