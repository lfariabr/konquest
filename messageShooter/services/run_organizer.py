import logging
from django.utils import timezone
from core.models.contact import Contact
from messageShooter.services.organizer import ContactOrganizer

# Usage
# python manage.py shell
# from messageShooter.services.run_organizer import test_contact_phone
# test_contact_phone("9999774836")

logger = logging.getLogger(__name__)

def organize_contact(contact):
    """
    Organize a single contact's priority and availability.
    This function should be called after creating or updating a contact
    in contactConversor_apt.py and contactConversor_lead.py.
    
    Args:
        contact: Contact instance to organize
    Returns:
        bool: True if contact was organized successfully
    """
    try:
        logger.info(f"Organizing contact: {contact.name} ({contact.phone})")
        logger.info(f"Current state: priority={contact.priority}, tag={contact.relationship_tag}")
        
        updated = ContactOrganizer.update_contact_priority(contact)
        
        if updated:
            logger.info(
                f"Contact organized: priority={contact.priority}, "
                f"available={contact.available_to_queue}"
            )
        else:
            logger.warning(f"Contact organization unchanged for {contact.phone}")
            
        return updated
        
    except Exception as e:
        logger.error(f"Error organizing contact {contact.phone}: {str(e)}")
        return False

def organize_contacts_bulk(contacts):
    """
    Organize multiple contacts in bulk.
    This function should be called after bulk creating/updating contacts
    in contactConversor_apt.py and contactConversor_lead.py.
    
    Args:
        contacts: List of Contact instances to organize
    Returns:
        int: Number of contacts organized
    """
    try:
        logger.info(f"Bulk organizing {len(contacts)} contacts")
        organized = ContactOrganizer.bulk_update_priorities(contacts)
        logger.info(f"Organized {organized} contacts")
        return organized
        
    except Exception as e:
        logger.error(f"Error in bulk organization: {str(e)}")
        return 0

def test_contact_phone(phone):
    """
    Test priority organization for all contacts with the given phone number.
    Shows the before and after state of each contact.
    
    Args:
        phone: Phone number to test
    """
    try:
        # Find all contacts with this phone
        contacts = Contact.objects.filter(phone=phone)
        
        if not contacts.exists():
            logger.error(f"No contacts found with phone {phone}")
            return
            
        # Show initial state
        logger.info(f"\nFound {contacts.count()} contacts with phone {phone}:")
        for contact in contacts:
            logger.info(
                f"Before - Contact {contact.id}: "
                f"tag={contact.relationship_tag}, "
                f"priority={contact.priority}, "
                f"available={contact.available_to_queue}"
            )
        
        # Update priorities
        organize_contacts_bulk(contacts)
        
        # Refresh from database and show final state
        contacts = Contact.objects.filter(phone=phone)
        logger.info(f"\nAfter organization:")
        for contact in contacts:
            logger.info(
                f"After - Contact {contact.id}: "
                f"tag={contact.relationship_tag}, "
                f"priority={contact.priority}, "
                f"available={contact.available_to_queue}"
            )
            
    except Exception as e:
        logger.error(f"Error testing phone {phone}: {str(e)}")

# Example usage in contactConversor_apt.py:
"""
from messageShooter.services.run_organizer import organize_contact, organize_contacts_bulk

def convert_appointment_to_contact(appointment, contact_tag, user=None):
    # Create contact...
    contact.save()
    
    # Organize the contact's priority
    organize_contact(contact)
    return contact

def convert_appointments_to_contacts_bulk(appointments, contact_tag, user=None):
    # Create contacts...
    contacts = []
    for appointment in appointments:
        contact = Contact(...)
        contacts.append(contact)
    
    Contact.objects.bulk_create(contacts)
    
    # Organize all contacts
    organize_contacts_bulk(contacts)
    return contacts
"""