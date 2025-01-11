import logging
from django.conf import settings
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone
from core.models.contact import Contact
from apiCrm.models.lead import Lead
from django.db import transaction

logger = logging.getLogger(__name__)

def convert_lead_to_contact_bulk(leads, contact_tag, user=None):
    """
    Bulk convert lead to konquista contact
    """
    if not user or not leads:
        return []
        
    # Get all phone numbers from leads
    phone_numbers = [lead.phone for lead in leads]
    
    # Fetch all existing contacts in one query
    existing_contacts = {
        contact.phone: contact 
        for contact in Contact.objects.filter(
            phone__in=phone_numbers,
            relationship_tag=contact_tag
        )
    }
    
    # Prepare bulk operations
    contacts_to_update = []
    contacts_to_create = []

    for lead in leads:
        if lead.phone in existing_contacts:
            # Update existing contact
            contact = existing_contacts[lead.phone]
            contact.lead_status = lead.status
            contact.lead_id = lead.id_crm
            contact.is_lead = True
            contacts_to_update.append(contact)
        else:
            # Create new contact
            contacts_to_create.append(Contact(
                user=user,
                lead_id=lead.id_crm,
                name=lead.name,
                phone=lead.phone,
                store=lead.store,
                lead_status=lead.status,
                relationship_tag=contact_tag,
                is_lead=True,
                lead_last_checked=timezone.now(),
                lead_check_count=0,
                lead_created_at=lead.created_at
            ))

    # Perform bulk operations
    with transaction.atomic():
        if contacts_to_create:
            Contact.objects.bulk_create(contacts_to_create)

        if contacts_to_update:
            Contact.objects.bulk_update(contacts_to_update, fields=['lead_status', 'lead_id', 'is_lead'])

    logger.info(f"Processed {len(leads)} leads and created {len(contacts_to_create)} contacts.")
    
    return contacts_to_create + contacts_to_update

def convert_lead_to_contact(lead, contact_tag, user=None):
    """
    Convert lead to konquista contact
    """
    if not lead:
        return None

    results = convert_lead_to_contact_bulk([lead], contact_tag, user)
    return results[0] if results else None