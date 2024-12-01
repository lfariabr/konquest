from django.utils import timezone
from django.db import transaction
from messageShooter.models.campaign import Campaign
from messageShooter.models.target_list import TargetList
from messageShooter.models.queue import Queue
from messageShooter.resolvers.target_list_resolver import generate_target_lists
import logging

logger = logging.getLogger(__name__)

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

            # Move target lists to Queue
            queued_count = 0
            with transaction.atomic():
                for target_list in created_lists:
                    contacts = target_list.get_contacts()
                    Queue.objects.create(
                        target_list=target_list,
                        campaign=target_list.campaign,  # Make sure campaign is set
                        message=target_list.message,
                        userphone=target_list.userphone,
                        phone_token=target_list.token,
                        priority=target_list.priority if hasattr(target_list, 'priority') else 0,
                        scheduled_time=timezone.now(),
                        total_contacts=len(contacts),
                        processed_contacts={},
                        processed_count=0,
                        status='pending'
                    )
                    target_list.status = 'processing'
                    target_list.save()
                    queued_count += 1
                    logger.info(f"Queued target list {target_list.id} for campaign {target_list.campaign.id if target_list.campaign else 'None'}")
            
            logger.info(f"Successfully queued {queued_count} target lists")
            return queued_count
        
        except Exception as e:
            logger.error(f"Error processing campaign: {str(e)}")
            return 0