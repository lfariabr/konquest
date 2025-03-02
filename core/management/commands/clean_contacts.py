# Easy usage @ terminal
"""
python manage.py clean_contacts
"""

from django.core.management.base import BaseCommand
from core.models.contact import Contact
from apiCrm.models.appointment import Appointment
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Clean contacts"

    def handle(self, *args, **options):
        contacts = Contact.objects.filter(available_to_queue=True, priority__lte=5)
        
        logger.info(f"Found {len(contacts)} contacts to clean")
        
        for contact in contacts:
            # Delete all contacts
            contact.delete()
                        
        logger.info("Cleaned contacts")