from django.core.management.base import BaseCommand
from core.models.messagelog import MessageLogs
from core.models.contact import Contact

class Command(BaseCommand):
    help = 'Show message logs for a specific phone number'

    def add_arguments(self, parser):
        parser.add_argument('phone', type=str, help='Phone number to check')

    def handle(self, *args, **options):
        phone = options['phone']
        
        # Find all contacts with this phone number
        contacts = Contact.objects.filter(phone=phone)
        self.stdout.write(f"Found {contacts.count()} contacts with phone {phone}:")
        
        for contact in contacts:
            self.stdout.write(f"\nContact: {contact.id} - {contact.phone} - {contact.relationship_tag}")
            
            # Get all message logs for this contact
            logs = MessageLogs.objects.filter(contact=contact)
            self.stdout.write(f"Found {logs.count()} message logs:")
            for log in logs:
                self.stdout.write(f"- ID: {log.id}")
                self.stdout.write(f"  Status: {log.status}")
                self.stdout.write(f"  Sent at: {log.sent_at}")
                self.stdout.write(f"  Tag: {log.relationship_tag}")
                self.stdout.write(f"  Message: {log.message.text[:50]}...")
                self.stdout.write("")
