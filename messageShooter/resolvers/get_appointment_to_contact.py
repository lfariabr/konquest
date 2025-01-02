# Resolver that converts an Appointment instance to a Contact instance
# This is important because we grab users from apiCrm and plug it in konquista's core mechanism

import logging
from django.conf import settings
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone
from core.models.contact import Contact
from apiCrm.models.appointment import Appointment

def convert_appointment_to_contact(appointment, contact_tag, user=None):
    """
    Convert an Appointment instance to a Contact instance.
    This allows us to maintain the existing flow while handling appointments.
    
    Args:
        appointment: Appointment instance to convert
        contact_tag: Tag to assign to the contact (e.g., 'Reminder', 'Reschedule')
        user: User instance to associate with created contacts
    Returns:
        Contact instance (saved to DB)
    """
    from core.models.contact import Contact
    import logging
    logger = logging.getLogger(__name__)
    
    if not user:
        logger.error(f"No user provided for appointment {appointment.id_crm}")
        return None
    
    try:
        # Check if contact already exists with this phone
        existing_contact = Contact.objects.filter(
            phone=appointment.customer_phone,
            relationship_tag=contact_tag,
            # is_appointment=True
        ).first()
        
        
        if existing_contact:
            # logger.info(f"Found existing contact for phone {appointment.customer_phone}: {existing_contact}. \n This means we are updating an existing contact, not creating neither duplication.")
            existing_contact.appointment_status = appointment.status_label
            existing_contact.appointment_id = appointment.id_crm  # Update to latest appointment
            existing_contact.is_appointment = True
            existing_contact.save()
            return existing_contact

            
        contact = Contact(
            name=appointment.customer_name,
            phone=appointment.customer_phone,
            source='Appointment',  # Mark the source as Appointment
            relationship_tag=contact_tag,
            status='active', 
            is_appointment=True,  # Mark as appointment-derived
            appointment_id=appointment.id_crm,  # Store the original appointment ID
            store=appointment.store_name,  # Store additional appointment data
            appointment_status=appointment.status_label,
            appointment_created_at=appointment.appointment_date,
            user=user  # Set the user
        )
    
        # Save to database
        contact.save()
        
        logger.info(f"Created and saved contact from appointment: {appointment.id_crm} -> Contact(id={contact.id}, phone={contact.phone})")
        return contact
        
    except Exception as e:
        logger.error(f"Error converting appointment {appointment.id_crm} to contact: {str(e)}")
        return None