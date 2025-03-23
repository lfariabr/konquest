import logging
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache

from core.models import contact
from apiCrm.models.lead import Lead

from messageShooter.utils.lead_ncc_rules import lead_stores_ncc, lead_status_ncc
from messageShooter.resolvers.contactConversor_lead import convert_lead_to_contact_bulk
from konquist.settings import CONTACTS_TO_LOAD_LEAD

logger = logging.getLogger(__name__)

def get_contact_lead(contact_type, contact_tag, user=None):
    """
    Get lead based on specific relationship tag rules
    - Args: 
        contact_type (str): Type of contact ('Lead')
        contact_tag (str): Tag to filter leads ('NCC') or Não Atendido #FUTURE
        user (User, optional): User associated with the leads/contacts
    - Returns: List[Contact]
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing contacts with tag {contact_tag}")

    if contact_type != "Lead" or not user:
        logger.error("Invalid contact type")
        return []

    now = timezone.now()

    # Checking: leads by store and by status
    store_leads = Lead.objects.filter(store__in=lead_stores_ncc)
    status_leads = store_leads.filter(status__in=lead_status_ncc)

    logger.info(f'Total leads: {Lead.objects.count()}')
    logger.info(f'Leads in {lead_stores_ncc} store: {store_leads.count()}')
    logger.info(f'Leads with status {lead_status_ncc}: {status_leads.count()}')

    # try to get from cache first for all types
    cache_key = f"lead_{contact_tag}_{now.hour}"
    cached_contacts = cache.get(cache_key)
    if cached_contacts is not None:
        logger.info(f"Using cached contacts for {contact_tag} at {now.hour}")
        return cached_contacts

    # Base query with common filters
    base_query = Lead.objects.filter(
        status__in=lead_status_ncc, 
        store__in=lead_stores_ncc
    )
    
    leads = []

    try:
        if contact_tag == "NCC":
            x_days_ago = now - timedelta(days=7)

            # Get total eligible leads
            total_leads = base_query.filter(
                created_at__lte=x_days_ago,
                store__in=lead_stores_ncc,
                status__in=lead_status_ncc,
            ).order_by('-created_at')

            morning_start = 1  # 1 AM
            afternoon_start = 14  # 2 PM
            batch_size = CONTACTS_TO_LOAD_LEAD # Amount of contacts to be processed
            
            # Calculate available batches
            total_eligible_leads = total_leads.count()
            logger.info(f"Total eligible leads: {total_eligible_leads}")
            
            # Batch navigation parameters
            starting_batch = 0  # First batch index (0-indexed)
            batch_increment = 1  # can be changed to 2, 3, etc.
            
            # Determine which batch to process: morning or afternoon
            if morning_start <= now.hour < afternoon_start:
                current_batch = starting_batch
                logger.info(f"Processing morning batch (batch {current_batch+1})")

            elif now.hour >= afternoon_start:
                current_batch = starting_batch + batch_increment
                logger.info(f"Processing afternoon batch (batch {current_batch+1})")

            else:
                logger.info("Outside of the defined time slots")
                return []
            
            # Calculate which slice of leads to process
            start_index = current_batch * batch_size
            end_index = start_index + batch_size
            
            # Make sure we don't exceed available leads
            if start_index >= total_eligible_leads and total_eligible_leads > 0:
                # Wrap around if needed
                start_index = start_index % total_eligible_leads
                end_index = start_index + batch_size
            
            # Get the leads for the current batch
            leads = total_leads[start_index:end_index]
            
            logger.info(f"Processing leads {start_index+1}-{min(end_index, total_eligible_leads)} of {total_eligible_leads}")

            leads = list(leads)
            total_count = total_leads.count()
            logger.info(f"Found {len(leads)} leads for {contact_tag} out of {total_count} total leads")
        
        else:
            logger.warning(f"Unknown contact tag: {contact_tag}")
            return []
        
        contacts = convert_lead_to_contact_bulk(leads, contact_tag, user)

        cache_timeout = 300 if contact_tag == "NCC" else 3600
        cache.set(cache_key, contacts, timeout=cache_timeout)

        return contacts

    except Exception as e:
        logger.error(f"Error getting leads for {contact_tag}: {str(e)}")
        return []
