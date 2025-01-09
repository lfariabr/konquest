import os
import logging
from django.utils import timezone
from django.db import transaction
from messageShooter.models.campaign import Campaign
from messageShooter.models.target_list import TargetList
from messageShooter.models.queue import Queue
from messageShooter.resolvers.target_list_resolver import generate_target_lists
from messageShooter.resolvers.get_userphone import get_userphone
from messageShooter.resolvers.get_message import get_message
from messageShooter.resolvers.get_counter import get_counter_whatsapp
from itertools import groupby
from operator import attrgetter

logger = logging.getLogger(__name__)

# Try Docker path first, fallback to local development path
if os.path.exists('/app'):
    log_dir = '/app/logs'
else:
    # Use local development path
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')

# Create logs directory if it doesn't exist
os.makedirs(log_dir, exist_ok=True)

# Setup file handler
file_handler = logging.FileHandler(os.path.join(log_dir, 'scheduler.log'))

# Add the file handler to the logger
logger.addHandler(file_handler)

class CampaignScheduler:
    def process_campaigns(self):
        """Process all campaigns that are ready to run"""
        logger.info("Starting campaign processing")
        
        try:
            # Generate target lists for campaigns that are ready to run
            created_lists = generate_target_lists()
            
            if not created_lists:
                logger.info("No target lists were created")
                return 0

            logger.info(f"Processing {len(created_lists)} target lists for queue creation")

            # Move target lists to Queue
            queued_count = 0
            error_count = 0
            
            with transaction.atomic():
                # Group target lists by campaign and contact_tag
                sorted_targets = sorted(created_lists, key=lambda x: (x.campaign_id, x.contact_tag))
                for (campaign_id, contact_tag), group_targets in groupby(sorted_targets, key=lambda x: (x.campaign_id, x.contact_tag)):
                    try:
                        group_targets = list(group_targets)
                        if not group_targets:
                            continue
                        
                        first_target = group_targets[0]
                        logger.info(f"Processing target lists for campaign {first_target.campaign.name} with tag {contact_tag}")
                        
                        # Check if queue already exists for this campaign and tag
                        existing_queue = Queue.objects.filter(
                            campaign=first_target.campaign,
                            target_list__contact_tag=contact_tag,
                            status__in=['pending', 'processing']
                        ).first()
                        
                        if existing_queue:
                            logger.info(f"Queue already exists for campaign {first_target.campaign.id} and tag {contact_tag}")
                            continue

                        # Get userphone for this tag
                        userphone, phone_token = get_userphone(contact_tag)
                        if not userphone:
                            logger.warning(f"No userphone found for tag {contact_tag}")
                            error_count += 1
                            continue
                        
                        # Get first contact's counter and message
                        counter = get_counter_whatsapp(first_target.contact_phone, contact_tag)
                        initial_message = get_message(
                            contact_type=first_target.contact_type,
                            relationship_tag=contact_tag,
                            counter=counter
                        )
                        
                        if not initial_message:
                            logger.warning(f"No message found for counter {counter} and tag {contact_tag}")
                            error_count += 1
                            continue

                        logger.info(f"Creating queue for campaign {first_target.campaign.name} with tag {contact_tag}")
                        logger.info(f"- Message ID: {initial_message.id}")
                        logger.info(f"- Userphone: {userphone.phone_number}")
                        logger.info(f"- Target Lists Count: {len(group_targets)}")

                        # Create one queue for all target lists in this campaign
                        queue = Queue.objects.create(
                            target_list=first_target,
                            campaign=first_target.campaign,
                            message=initial_message,
                            userphone=userphone,
                            phone_token=phone_token,
                            priority=getattr(first_target, 'priority', 0),
                            scheduled_time=timezone.now(),
                            total_contacts=len(group_targets),
                            processed_contacts={},
                            processed_count=0,
                            status='pending'
                        )
                        queued_count += 1
                        
                        # Update all target lists' status
                        TargetList.objects.filter(id__in=[t.id for t in group_targets]).update(status='processing')
                        
                        # Update campaign status if it's a one-time campaign
                        campaign = first_target.campaign
                        if campaign.frequency == 'Once':
                            campaign.campaign_status = 'Completed'
                            campaign.save()
                        
                        logger.info(f"Successfully created queue {queue.id} for campaign {campaign.name}")
                        
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error processing campaign {campaign_id} with tag {contact_tag}: {str(e)}")
                        continue
            
            logger.info(f"Successfully queued {queued_count} campaigns")
            if error_count > 0:
                logger.warning(f"Failed to process {error_count} campaigns")
            
            return queued_count
            
        except Exception as e:
            logger.error(f"Error in process_campaigns: {str(e)}")
            return 0