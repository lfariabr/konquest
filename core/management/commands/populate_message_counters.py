from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
from core.models.contact import Contact
from core.models.messagelog import MessageLogs

class Command(BaseCommand):
    help = 'Populate message counters for all contacts based on MessageLogs'

    def handle(self, *args, **options):
        self.stdout.write('Starting to populate message counters...')
        
        try:
            with connection.cursor() as cursor:
                # Update Botox counters
                cursor.execute("""
                    UPDATE core_contact c
                    SET botox_messages_sent = subquery.msg_count
                    FROM (
                        SELECT contact_id, COUNT(*) as msg_count
                        FROM core_messagelogs
                        WHERE LOWER(relationship_tag) = 'botox'
                        AND status = 'sent'
                        GROUP BY contact_id
                    ) as subquery
                    WHERE c.id = subquery.contact_id
                """)
                
                # Update Preenchimento counters
                cursor.execute("""
                    UPDATE core_contact c
                    SET preenchimento_messages_sent = subquery.msg_count
                    FROM (
                        SELECT contact_id, COUNT(*) as msg_count
                        FROM core_messagelogs
                        WHERE LOWER(relationship_tag) = 'preenchimento'
                        AND status = 'sent'
                        GROUP BY contact_id
                    ) as subquery
                    WHERE c.id = subquery.contact_id
                """)
                
                # Update last message sent timestamp
                cursor.execute("""
                    UPDATE core_contact c
                    SET last_message_sent_at = subquery.last_sent
                    FROM (
                        SELECT contact_id, MAX(sent_at) as last_sent
                        FROM core_messagelogs
                        WHERE status = 'sent'
                        GROUP BY contact_id
                    ) as subquery
                    WHERE c.id = subquery.contact_id
                """)

            # Verify the updates
            total_contacts = Contact.objects.count()
            contacts_with_botox = Contact.objects.filter(botox_messages_sent__gt=0).count()
            contacts_with_preench = Contact.objects.filter(preenchimento_messages_sent__gt=0).count()
            
            self.stdout.write(self.style.SUCCESS(f'''
            Successfully populated message counters!
            Total contacts: {total_contacts}
            Contacts with Botox messages: {contacts_with_botox}
            Contacts with Preenchimento messages: {contacts_with_preench}
            '''))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error populating counters: {str(e)}'))