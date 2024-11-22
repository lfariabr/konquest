from django.utils import timezone
from messageShooter.models.target_list import TargetList
from messageShooter.models.campaign import Campaign
from messageShooter.resolvers.get_contacts import get_contact_whatsapp, get_contact_appointment
from messageShooter.resolvers.get_counter import get_counter_whatsapp, get_counter_appointment
from messageShooter.resolvers.get_message import get_message
from messageShooter.resolvers.get_userphone import get_userphone
from core.models.messagelog import MessageLogs

def create_target_list(campaign_id):
    """
    Create target list entries for a campaign
    Returns (created_count, skipped_count, error_count)
    """
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        if campaign.campaign_status != "Active":
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

        # Get message and userphone
        message = get_message(campaign.contact_type, campaign.contact_tag, counter)
        if not message:
            raise ValueError(f"No message found for {campaign.contact_type}/{campaign.contact_tag}")

        userphone, token = get_userphone(campaign.contact_tag)
        if not userphone or not token:
            raise ValueError(f"No userphone/token found for tag: {campaign.contact_tag}")

        created_count = 0
        skipped_count = 0
        error_count = 0

        for contact in contacts:
            try:
                # Check if contact already in target list
                existing = TargetList.objects.filter(
                    contact_phone=contact.phone,
                    contact_tag=campaign.contact_tag,
                    reference_id=str(contact.id)
                ).exists()

                if existing:
                    skipped_count += 1
                    continue

                # Check message frequency rules
                if campaign.frequency != "Once":
                    sent_today = MessageLogs.objects.filter(
                        phone_number=contact.phone,
                        contact_tag=campaign.contact_tag,
                        sent_at__date=timezone.now().date()
                    ).exists()

                    if sent_today:
                        skipped_count += 1
                        continue

                # Create target list entry
                TargetList.objects.create(
                    contact_phone=contact.phone,
                    contact_type=campaign.contact_type,
                    contact_tag=campaign.contact_tag,
                    reference_id=str(contact.id),
                    sent_messages_count=0,
                    userphone=userphone,
                    message=message,
                    priority=0  # Default priority for FIFO
                )
                created_count += 1

            except Exception as e:
                print(f"Error processing contact {contact.id}: {str(e)}")
                error_count += 1

        return created_count, skipped_count, error_count

    except Campaign.DoesNotExist:
        raise ValueError(f"Campaign with id {campaign_id} does not exist")
    except Exception as e:
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
