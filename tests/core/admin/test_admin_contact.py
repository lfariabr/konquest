from django.test import TestCase, RequestFactory
from django.contrib import admin, messages
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from core.admin import ContactAdmin
from core.models.contact import Contact
from core.models.user import kUser
from apiCrm.models.lead import Lead
from django.utils import timezone

class MockSuperUser:
    def has_perm(self, perm):
        return True

class ContactAdminTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.admin = ContactAdmin(Contact, self.site)
        
        # Create test user
        self.user = kUser.objects.create(
            name="Test Admin",
            email="admin@test.com",
            password="testpass123"
        )
        
        # Create test contacts
        self.contacts = []
        for i in range(3):
            contact = Contact.objects.create(
                name=f"Contact {i}",
                phone=f"1198765432{i}",
                user=self.user
            )
            self.contacts.append(contact)
        
        # Create test leads
        self.leads = []
        for i in range(2):  # Only create 2 leads (to test both match and no-match cases)
            lead = Lead.objects.create(
                id_crm=f"123{i}",
                name=f"Contact {i}",  # Match first two contact names
                email=f"lead{i}@test.com",
                phone=f"1198765432{i}",  # Match first two contact phones
                source="Test",
                store="Test Store",
                status="Active",
                created_at=timezone.now()
            )
            self.leads.append(lead)

    def test_check_leads_action(self):
        """Test the admin action to check leads"""
        request = self.factory.get('/')
        request.user = MockSuperUser()
        
        # Add message storage to request
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        # Test checking all contacts
        queryset = Contact.objects.all()
        self.admin.check_leads(request, queryset)
        
        # Verify results
        contacts = Contact.objects.all()
        found_leads = sum(1 for c in contacts if c.is_lead)
        self.assertEqual(found_leads, 2)  # Should find 2 matching leads
        
        # Check specific contact statuses
        self.assertTrue(contacts[0].is_lead)
        self.assertTrue(contacts[1].is_lead)
        self.assertFalse(contacts[2].is_lead)
        
        # Check lead information is properly stored
        for i in range(2):
            contact = contacts[i]
            self.assertEqual(contact.lead_id, self.leads[i].id_crm)
            self.assertEqual(contact.lead_status, self.leads[i].status)
            self.assertIsNotNone(contact.lead_last_checked)
            self.assertEqual(contact.lead_check_count, 1)

    def test_check_leads_with_subset(self):
        """Test checking only selected contacts"""
        request = self.factory.get('/')
        request.user = MockSuperUser()
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))
        
        # Test checking only first contact
        queryset = Contact.objects.filter(id=self.contacts[0].id)
        self.admin.check_leads(request, queryset)
        
        # Verify only first contact was checked
        contact1 = Contact.objects.get(id=self.contacts[0].id)
        contact2 = Contact.objects.get(id=self.contacts[1].id)
        
        self.assertTrue(contact1.is_lead)
        self.assertEqual(contact1.lead_check_count, 1)
        
        self.assertFalse(contact2.is_lead)
        self.assertEqual(contact2.lead_check_count, 0)

    def test_admin_list_display(self):
        """Test that lead-related fields are in list_display"""
        self.assertIn('is_lead', self.admin.list_display)
        self.assertIn('lead_status', self.admin.list_display)
        self.assertIn('lead_last_checked', self.admin.list_display)
        self.assertIn('lead_check_count', self.admin.list_display)
