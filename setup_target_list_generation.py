import os
import django
import logging
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'konquist.settings')
django.setup()

from messageShooter.models import Campaign
from messageShooter.resolvers.target_list_resolver import create_target_list

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Get Botox campaign
    try:
        campaign_botox = Campaign.objects.get(name="Botox Campaign")
        logger.info(f"\n=== Found Botox Campaign (ID: {campaign_botox.id}) ===")
        
        # Set up campaign to run now
        now = timezone.now()
        campaign_botox.campaign_status = "Active"
        campaign_botox.start_time = now  # For FREQUENCY_ONCE campaigns
        campaign_botox.next_run = now    # For recurring campaigns
        campaign_botox.active_days = [now.weekday()]  # Add today as an active day
        try:
            campaign_botox.full_clean()  # Validate before save
            campaign_botox.save()
            logger.info("Successfully updated Botox campaign")
        except ValidationError as e:
            logger.error(f"Validation error for Botox campaign: {e}")
        
        # Create target list
        logger.info("Creating target list for Botox...")
        result = create_target_list(campaign_botox.id)
        logger.info(f"Result: {result}")
        
    except Campaign.DoesNotExist:
        logger.error("Botox Campaign not found!")
    
    # Get Preenchimento campaign
    try:
        campaign_preench = Campaign.objects.get(name="Preenchimento Campaign")
        logger.info(f"\n=== Found Preenchimento Campaign (ID: {campaign_preench.id}) ===")
        
        # Set up campaign to run now
        now = timezone.now()
        campaign_preench.campaign_status = "Active"
        campaign_preench.start_time = now  # For FREQUENCY_ONCE campaigns
        campaign_preench.next_run = now    # For recurring campaigns
        campaign_preench.active_days = [now.weekday()]  # Add today as an active day
        try:
            campaign_preench.full_clean()  # Validate before save
            campaign_preench.save()
            logger.info("Successfully updated Preenchimento campaign")
        except ValidationError as e:
            logger.error(f"Validation error for Preenchimento campaign: {e}")
        
        # Create target list
        logger.info("Creating target list for Preenchimento...")
        result = create_target_list(campaign_preench.id)
        logger.info(f"Result: {result}")
        
    except Campaign.DoesNotExist:
        logger.error("Preenchimento Campaign not found!")

if __name__ == "__main__":
    main()
