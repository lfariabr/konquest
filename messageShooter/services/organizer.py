import logging
from django.utils import timezone
from django.db import transaction
from core.models.contact import Contact
from messageShooter.models.campaign import Campaign

logger = logging.getLogger(__name__)

class ContactOrganizer:
    """Service class to handle contact organization and priority management"""
    
    PRIORITY_RULES = {
        'Reminder': 1,
        'ReminderPL': 1,          # Highest priority
        'Reschedule': 2,        
        'ReschedulePL': 2,
        'NPS': 3,              
        'NCC': 4,              
        'Botox': 5,            
        'Preenchimento': 5,    
        'Instagram': 5         # Lowest priority
    }
    
    @classmethod
    def update_contact_priority(cls, contact):
        """
        Update contact priority based on relationship_tag.
        If a contact appears with multiple tags, prioritize according to PRIORITY_RULES
        and set available_to_queue=True only for the highest priority contact.
        
        Args:
            contact: Contact instance to update
        Returns:
            bool: True if priority was updated, False otherwise
        """
        try:
            if not contact.relationship_tag:
                logger.warning(f"No tag for contact {contact.id} ({contact.phone})")
                return False
            
            # Find all contacts with the same phone number
            related_contacts = Contact.objects.filter(
                phone=contact.phone,
                available_to_queue=True
            )
            
            if not related_contacts.exists():
                # No other contacts found, use current contact's tag
                new_priority = cls.PRIORITY_RULES.get(contact.relationship_tag, 5)
                contact.priority = new_priority
                contact.save(update_fields=['priority'])
                logger.info(f"Single contact {contact.id} ({contact.phone}) priority set to {new_priority}")
                return True
            
            # Get all unique tags and their priorities
            contact_priorities = {}
            for related in related_contacts:
                if related.relationship_tag:
                    priority = cls.PRIORITY_RULES.get(related.relationship_tag, 5)
                    contact_priorities[related.id] = {
                        'contact': related,
                        'priority': priority,
                        'tag': related.relationship_tag
                    }
            
            # Find the highest priority (lowest number)
            if contact_priorities:
                min_priority = min(info['priority'] for info in contact_priorities.values())
                
                # Update all related contacts
                with transaction.atomic():
                    for contact_info in contact_priorities.values():
                        contact = contact_info['contact']
                        priority = contact_info['priority']
                        
                        # Set priority for all contacts
                        contact.priority = priority
                        
                        # Only the highest priority contact should be available for queue
                        contact.available_to_queue = (priority == min_priority)
                        
                        contact.save(update_fields=['priority', 'available_to_queue'])
                        
                        logger.info(
                            f"Updated contact {contact.id} ({contact.phone}): "
                            f"priority={priority}, available={contact.available_to_queue}, "
                            f"tag={contact.relationship_tag}"
                        )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating priority for contact {contact.id}: {str(e)}")
            return False
    
    @classmethod
    def bulk_update_priorities(cls, contacts=None):
        """
        Bulk update priorities for multiple contacts
        Args:
            contacts: Optional QuerySet of contacts to update. If None, updates all contacts.
        Returns:
            int: Number of contacts updated
        """
        if contacts is None:
            contacts = Contact.objects.filter(available_to_queue=True)
            
        updated_count = 0
        processed_phones = set()
        
        try:
            for contact in contacts:
                # Only process each phone number once to avoid duplicate work
                if contact.phone not in processed_phones:
                    if cls.update_contact_priority(contact):
                        updated_count += 1
                    processed_phones.add(contact.phone)
                        
            logger.info(f"Bulk updated priorities for {updated_count} unique phone numbers")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error in bulk priority update: {str(e)}")
            return 0