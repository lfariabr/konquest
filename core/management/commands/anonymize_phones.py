# Easy usage @ terminal
"""
python manage.py anonymize_phones
"""

from django.core.management.base import BaseCommand
from apiCrm.models.appointment import Appointment
from apiCrm.models.lead import Lead
from core.models.contact import Contact
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Anonymize phone numbers in Appointment and Lead tables'

    def generate_fake_phone(self, counter):
        """Generate a fake phone number starting from 9999999999"""
        base = 9999999999 - counter
        return str(base)
        # 9999999999
        # 0000000000

    @transaction.atomic
    def handle(self, *args, **kwargs):
        try:
            # Counter for generating unique phone numbers
            counter = 0
            
            # Anonymize Appointments
            appointments = Appointment.objects.all()
            self.stdout.write(f"Found {appointments.count()} appointments to anonymize")
            
            for appointment in appointments:
                fake_phone = self.generate_fake_phone(counter)
                appointment.customer_phone = fake_phone
                appointment.save()
                counter += 1
                
            self.stdout.write(self.style.SUCCESS(f"Successfully anonymized {counter} appointment phone numbers"))
            
            # Anonymize Leads
            leads = Lead.objects.all()
            self.stdout.write(f"Found {leads.count()} leads to anonymize")
            
            lead_counter = 0
            for lead in leads:
                fake_phone = self.generate_fake_phone(counter)
                lead.phone = fake_phone
                lead.save()
                counter += 1
                lead_counter += 1
            
            self.stdout.write(self.style.SUCCESS(f"Successfully anonymized {lead_counter} lead phone numbers"))

            # anonymize contacts
            contacts = Contact.objects.all()
            self.stdout.write(f"Found {contacts.count()} contacts to anonymize")
            
            for contact in contacts:
                fake_phone = self.generate_fake_phone(counter)
                contact.phone = fake_phone
                contact.save()
                counter += 1
            
            self.stdout.write(self.style.SUCCESS(f"Successfully anonymized {counter} contact phone numbers"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during anonymization: {str(e)}"))
            raise

