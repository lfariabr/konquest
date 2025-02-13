# Resolver that converts an Appointment instance to a Contact instance
# This is important because we grab users from apiCrm and plug it in konquista's core mechanism

import logging
from socket import AF_AAL5
from django.conf import settings
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone
from core.models.contact import Contact
from apiCrm.models.appointment import Appointment
from django.db import transaction

logger = logging.getLogger(__name__)

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
            # Update the contact if:
            # 1. New appointment is more recent than the existing one
            # 2. Contact tag priority needs to be considered
            should_update = False
            
            # Check if new appointment is more recent
            if (not existing_contact.appointment_created_at or 
                appointment.appointment_date > existing_contact.appointment_created_at):
                should_update = True
                logger.info(f"Updating contact due to more recent appointment date: {appointment.appointment_date}")
            
            # Consider contact tag priority if defined
            tag_priority = getattr(settings, 'CONTACT_TAG_PRIORITY', {})
            if tag_priority:
                existing_priority = tag_priority.get(existing_contact.relationship_tag, 0)
                new_priority = tag_priority.get(contact_tag, 0)
                if new_priority > existing_priority:
                    should_update = True
                    logger.info(f"Updating contact due to higher priority tag: {contact_tag}")
            
            if should_update:
                existing_contact.name = appointment.customer_name
                existing_contact.appointment_status = appointment.status_label
                existing_contact.appointment_id = appointment.id_crm
                existing_contact.relationship_tag = contact_tag # ?
                existing_contact.is_appointment = True
                existing_contact.appointment_created_at = appointment.appointment_date
                existing_contact.store = appointment.store_name
                existing_contact.save()
                logger.info(f"Updated existing contact {existing_contact.id} with new appointment data")
            else:
                logger.info(f"Kept existing contact data as it was more relevant: {existing_contact.id}")
            
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

def convert_appointments_to_contacts_bulk(appointments, contact_tag, user=None):
    """Bulk convert appointments to contacts"""
    if not user or not appointments:
        return []
        
    # Get all phone numbers from appointments
    phone_numbers = [apt.customer_phone for apt in appointments]
    
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
    
    for appointment in appointments:
        if appointment.customer_phone in existing_contacts:
            # Update existing contact
            contact = existing_contacts[appointment.customer_phone]
            contact.appointment_status = appointment.status_label
            contact.appointment_id = appointment.id_crm
            contact.is_appointment = True
            contacts_to_update.append(contact)
        else:
            # Create new contact
            contacts_to_create.append(Contact(
                name=appointment.customer_name,
                phone=appointment.customer_phone,
                source='Appointment',
                relationship_tag=contact_tag,
                status='active',
                is_appointment=True,
                appointment_id=appointment.id_crm,
                store=appointment.store_name,
                appointment_status=appointment.status_label,
                appointment_created_at=appointment.appointment_date,
                user=user
            ))
    
    # Perform bulk operations
    with transaction.atomic():
        if contacts_to_create:
            Contact.objects.bulk_create(contacts_to_create)
        if contacts_to_update:
            Contact.objects.bulk_update(
                contacts_to_update,
                ['appointment_status', 'appointment_id', 'is_appointment']
            )
    
    logger.info(f"Processed {len(appointments)} appointments: "
                f"Created {len(contacts_to_create)}, "
                f"Updated {len(contacts_to_update)}")
    
    return contacts_to_create + contacts_to_update

def convert_appointment_to_contact(appointment, contact_tag, user=None):
    """
    Convert a single appointment to contact.
    For backward compatibility, wraps the bulk operation.
    """
    if not appointment:
        return None
        
    results = convert_appointments_to_contacts_bulk([appointment], contact_tag, user)
    return results[0] if results else None