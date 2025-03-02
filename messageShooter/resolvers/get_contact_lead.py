# Previous version:
#  python manage.py shell -c "from messageShooter.resolvers.get_contact_lead import get_contact_lead; print(get_contact_lead('Lead', 'Não Conseguiu Entrar Em Contato'))"
# New test to be done:
# python manage.py shell -c "from django.contrib.auth import get_user_model; from messageShooter.resolvers.get_contact_lead import get_contact_lead; user = get_user_model().objects.first(); print(get_contact_lead('Lead', 'Não Conseguiu Entrar Em Contato', user=user))"

# New fixing the 'user' call:
# python manage.py shell -c "from core.models.user import kUser; from messageShooter.resolvers.get_contact_lead import get_contact_lead; user = kUser.objects.first(); print(get_contact_lead('Lead', 'Não Conseguiu Entrar Em Contato', user=user))"

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
    logger.info(f"Processing contacts wiceth tag {contact_tag}")

    if contact_type != "Lead" or not user:
        logger.error("Invalid contact type")
        return []

    now = timezone.now()
    ten_days_ago = now - timedelta (days=10)

    logger.info(f'Total leads: {Lead.objects.count()}')
    # Check leads by store
    store_leads = Lead.objects.filter(store__in=lead_stores_ncc)
    logger.info(f'Leads in {lead_stores_ncc} store: {store_leads.count()}')
    # Check leads by status
    status_leads = store_leads.filter(status__in=lead_status_ncc)
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
            ten_days_ago = now - timedelta(days=10)

            # Get total eligible leads first
            total_leads = base_query.filter(
                created_at__lte=ten_days_ago,
                store__in=lead_stores_ncc,
                status__in=lead_status_ncc,
            ).order_by('-created_at')

            # Defining time slots:
            morning_start = 1
            afternoon_start = 15

            if morning_start <= now.hour < afternoon_start:
                # Morning batch (first 50 contacts)
                leads = total_leads[:CONTACTS_TO_LOAD_LEAD]
                logger.info(f"Processing morning batch: leads 1-{CONTACTS_TO_LOAD_LEAD}")

            elif now.hour >= afternoon_start:
                # Afternoon batch (last 50 contacts)
                leads = total_leads[CONTACTS_TO_LOAD_LEAD:CONTACTS_TO_LOAD_LEAD*2]
                logger.info(f"Processing afternoon batch: leads {CONTACTS_TO_LOAD_LEAD+1}-{CONTACTS_TO_LOAD_LEAD*2}")
            
            else:
                logger.info("Outside of the defined time slots")
                return []

            leads = list(leads)
            total_count = total_leads.count()
            logger.info(f"Found {len(leads)} leads for {contact_tag} out of {total_count} total leads")
        
        else:
            logger.warning(f"Unknown contact tag: {contact_tag}")
            return []
        
        # Convert all leads to contacts using bulk operation
        contacts = convert_lead_to_contact_bulk(leads, contact_tag, user)

        # Caching results
        cache_timeout = 300 if contact_tag == "NCC" else 3600
        cache.set(cache_key, contacts, timeout=cache_timeout)

        return contacts

    except Exception as e:
        logger.error(f"Error getting leads for {contact_tag}: {str(e)}")
        return []
