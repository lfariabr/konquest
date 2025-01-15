# if contact_type = whatsapp > get Contacts order FIFO
# if contact_type = whatsapp + contact_tag[Botox] > get Contact Botox order FIFO

# if contact_type > get Appointment
# if contact_type = Appointment + contact_tag[Reschedule] > get Appointment Reschedule

import logging
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Min
from django.db.models.query import QuerySet

from typing import List
from datetime import timedelta
from core.models.contact import Contact
from datetime import datetime, timedelta

from konquist.settings import CONTACTS_TO_LOAD_WPP

logger = logging.getLogger(__name__)

def get_contact_whatsapp(contact_type: str, contact_tag: str) -> QuerySet:
    """
    Get WhatsApp contacts based on tag, ordered by creation date (FIFO).
    If a contact exists with a different tag, it will be included and its tag
    will be updated when creating the target list.
    
    Args:
        contact_type (str): Type of contact (must be "Whatsapp")
        contact_tag (str): Tag to filter contacts
        
    Returns:
        QuerySet: Unique contacts by phone number from the last 30 days, 
                 taking the earliest created contact
    """
    logger.info(f"Fetching WhatsApp contacts with tag '{contact_tag}'")
    
    if contact_type != "Whatsapp":
        logger.warning(f"Invalid contact type: {contact_type}. Expected 'Whatsapp'")
        return []
    
    # Calculate date 30 days ago with timezone awareness
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Get base queryset with all filters
    contacts = Contact.objects.filter(
        source__iexact="Whatsapp",
        relationship_tag=contact_tag,
        is_lead=False,
        is_appointment=False,
        created_at__gte=thirty_days_ago
    )

    logger.info(
        f"Found {contacts.count()} total contacts from the last 30 days "
        f"with tag '{contact_tag}'"
    )
    
    # Remove duplicates by keeping earliest contact per phone number
    unique_contacts = contacts.values('phone').annotate(
        min_created_at=Min('created_at')
    ).order_by('-min_created_at')
    
    # Get the actual Contact objects with proper limit
    unique_contact_ids = contacts.filter(
        created_at__in=[item['min_created_at'] for item in unique_contacts]
    ).values_list('id', flat=True)
    
    final_contacts = contacts.filter(
        id__in=unique_contact_ids
    ).order_by('-created_at')[:CONTACTS_TO_LOAD_WPP]
    
    logger.info(
        f"Found {len(unique_contacts)} unique contacts from the last 30 days "
        f"with tag '{contact_tag}'"
    )
    
    return final_contacts