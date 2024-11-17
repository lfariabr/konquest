import pytest
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth.models import User as DjangoUser
from core.models.user import kUser
from core.models.contact import Contact
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import datetime
from django.utils import timezone
import pandas as pd
import io

class TestContactUpload(TestCase):
    def setUp(self):
        # Create Django admin user
        self.admin_user = DjangoUser.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        
        # Create corresponding kUser
        self.k_user = kUser.objects.create(
            name='Admin User',
            email='admin@test.com',
            password='admin123'
        )
        
        # Create test client and login
        self.client = Client()
        self.client.login(username='admin', password='admin123')
        
        # Create test CSV content
        self.botox_data = pd.DataFrame({
            'Nome': ['Test Botox 1', 'Test Botox 2'],
            'Whatsapp': ['5511999999999', '5511888888888'],
            'Tags': ['CAMPINAS', 'TATUAPÉ']
        })
        
        self.preench_data = pd.DataFrame({
            'Nome': ['Test Preench 1', 'Test Preench 2'],
            'Whatsapp': ['5511777777777', '5511666666666'],
            'Tags': ['SANTOS', 'MOEMA']
        })

    def create_csv_file(self, data, filename):
        csv_buffer = io.StringIO()
        data.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue().encode('utf-8')
        return SimpleUploadedFile(filename, csv_content, content_type='text/csv')

    def test_upload_leads_botox(self):
        # Create CSV file
        csv_file = self.create_csv_file(self.botox_data, 'botox.csv')
        
        # Upload the file
        response = self.client.post(reverse('admin:core_contact_changelist'), {
            'csv_upload': True,
            'botox_file': csv_file
        })
        
        # Check response
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check created contacts
        contacts = Contact.objects.all()
        self.assertEqual(contacts.count(), 2)
        
        # Check first contact details
        contact = contacts.first()
        self.assertEqual(contact.name, 'Test Botox 1')
        self.assertEqual(contact.phone, '11999999999')
        self.assertEqual(contact.store, 'CAMPINAS')
        self.assertEqual(contact.region, 'Campinas')
        self.assertEqual(contact.relationship_tag, 'Botox')

    def test_upload_leads_preenchimento(self):
        # Create CSV file
        csv_file = self.create_csv_file(self.preench_data, 'preenchimento.csv')
        
        # Upload the file
        response = self.client.post(reverse('admin:core_contact_changelist'), {
            'csv_upload': True,
            'preenchimento_file': csv_file
        })
        
        # Check response
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check created contacts
        contacts = Contact.objects.all()
        self.assertEqual(contacts.count(), 2)
        
        # Check first contact details
        contact = contacts.first()
        self.assertEqual(contact.name, 'Test Preench 1')
        self.assertEqual(contact.phone, '11777777777')
        self.assertEqual(contact.store, 'SANTOS')
        self.assertEqual(contact.region, 'Santos')
        self.assertEqual(contact.relationship_tag, 'Preenchimento')

    def test_date_empty_is_equal_today(self):
        # Create CSV file
        csv_file = self.create_csv_file(self.botox_data, 'botox.csv')
        
        # Get current time for comparison
        before_upload = timezone.now()
        
        # Upload the file without date
        response = self.client.post(reverse('admin:core_contact_changelist'), {
            'csv_upload': True,
            'botox_file': csv_file
        })
        
        after_upload = timezone.now()
        
        # Check created contacts
        contact = Contact.objects.first()
        
        # Contact created_at should be between before_upload and after_upload
        self.assertTrue(before_upload <= contact.created_at <= after_upload)

    def test_date_filled_is_filled_data(self):
        # Create CSV file
        csv_file = self.create_csv_file(self.botox_data, 'botox.csv')
        
        # Set specific date
        test_date = '2024-01-01'
        
        # Upload the file with date
        response = self.client.post(reverse('admin:core_contact_changelist'), {
            'csv_upload': True,
            'botox_file': csv_file,
            'date': test_date
        })
        
        # Check created contacts
        contact = Contact.objects.first()
        
        # Convert test_date to datetime for comparison
        expected_date = timezone.make_aware(datetime.strptime(test_date, '%Y-%m-%d'))
        
        # Contact created_at should be the specified date
        self.assertEqual(contact.created_at.date(), expected_date.date())
