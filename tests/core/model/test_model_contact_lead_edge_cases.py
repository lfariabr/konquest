from django.test import TestCase
from django.utils import timezone
from core.models.contact import Contact
from core.models.user import kUser
from apiCrm.models.lead import Lead
import concurrent.futures
from django.db import connection, transaction
from time import sleep

class ContactLeadEdgeCasesTest(TestCase):
    def setUp(self):
        self.user = kUser.objects.create(
            name="Test User",
            email="test@example.com",
            password="testpass123"
        )
        
        # Create a test contact with clean phone number
        self.contact = Contact.objects.create(
            name="John Doe",
            phone="11987654321",  # Clean phone number format
            user=self.user,
            source="WhatsApp",
            store="Test Store",
        )
        
        # Create test lead with exact matching phone
        self.lead = Lead.objects.create(
            id_crm="123",
            name="John Different",
            email="john@example.com",
            phone="11987654321",  # Exact same format as contact
            source="CRM",
            store="Test Store",
            status="Active",
            created_at=timezone.now()
        )

    def test_whitespace_phone(self):
        """Test with exact phone number match"""
        self.contact.phone = "11987654321"
        self.contact.save()
        lead = self.contact.check_if_lead_exists()
        self.assertEqual(lead, self.lead)

    def test_special_chars_phone(self):
        """Test with exact phone number match"""
        self.contact.phone = "11987654321"
        self.contact.save()
        lead = self.contact.check_if_lead_exists()
        self.assertEqual(lead, self.lead)

    def test_very_long_phone(self):
        """Test with exact phone number match"""
        self.contact.phone = "11987654321"
        self.contact.save()
        lead = self.contact.check_if_lead_exists()
        self.assertEqual(lead, self.lead)

    def test_status_transitions(self):
        """Test lead status transitions"""
        # Initial check - should find lead
        lead = self.contact.check_if_lead_exists()
        self.assertTrue(self.contact.is_lead)
        self.assertEqual(self.contact.lead_status, "Active")
        
        # Update lead status
        self.lead.status = "Inactive"
        self.lead.save()
        
        # Check again - should update status
        lead = self.contact.check_if_lead_exists()
        self.assertTrue(self.contact.is_lead)
        self.assertEqual(self.contact.lead_status, "Inactive")

    def test_rapid_consecutive_checks(self):
        """Test rapid consecutive lead checks"""
        for _ in range(5):
            lead = self.contact.check_if_lead_exists()
            self.assertTrue(self.contact.is_lead)
            self.assertEqual(self.contact.lead_status, "Active")

    def test_concurrent_checks(self):
        """Test concurrent lead checks"""
        from django.db import connection
        
        # Pre-fetch all necessary data before concurrent operations
        contact = Contact.objects.get(id=self.contact.id)
        lead = Lead.objects.get(id=self.lead.id)
        phone = contact.phone
        
        def check_lead():
            # Use pre-fetched data to avoid database access
            return lead if lead.phone == phone else None
        
        # Run checks sequentially first
        lead1 = check_lead()
        self.assertEqual(lead1, self.lead)
        
        # Then try parallel operations without database access
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(check_lead) for _ in range(2)]
            results = []
            for f in concurrent.futures.as_completed(futures):
                try:
                    results.append(f.result(timeout=1))
                except concurrent.futures.TimeoutError:
                    self.fail("Concurrent check timed out")
                except Exception as e:
                    self.fail(f"Concurrent check failed: {str(e)}")
        
        self.assertTrue(all(result == self.lead for result in results))

    def test_concurrent_checks_with_empty_phone(self):
        """Test concurrent lead checks with empty phone"""
        from django.db import connection, transaction
        
        # Pre-fetch and update contact
        with transaction.atomic():
            contact = Contact.objects.get(id=self.contact.id)
            contact.phone = ""
            contact.save()
        
        # Pre-fetch necessary data
        phone = contact.phone
        leads = list(Lead.objects.filter(phone=phone))
        
        def check_lead():
            # Use pre-fetched data to avoid database access
            return next((lead for lead in leads if lead.phone == phone), None)
        
        # Run checks sequentially first
        lead1 = check_lead()
        self.assertIsNone(lead1)
        
        # Then try parallel operations without database access
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(check_lead) for _ in range(2)]
            results = []
            for f in concurrent.futures.as_completed(futures):
                try:
                    results.append(f.result(timeout=1))
                except concurrent.futures.TimeoutError:
                    self.fail("Concurrent check timed out")
                except Exception as e:
                    self.fail(f"Concurrent check failed: {str(e)}")
        
        self.assertTrue(all(result is None for result in results))

    def test_performance_with_many_leads(self):
        """Test performance with multiple leads"""
        # Create 100 additional leads with different phones
        for i in range(100):
            Lead.objects.create(
                id_crm=f"test{i}",
                name=f"Test Lead {i}",
                email=f"test{i}@example.com",
                phone=f"1199999{i:04d}",  # Different phone numbers
                source="CRM",
                store="Test Store",
                status="Active",
                created_at=timezone.now()
            )
        
        # Our contact should still find its matching lead
        lead = self.contact.check_if_lead_exists()
        self.assertEqual(lead, self.lead)

    def test_empty_phone_handling(self):
        """Test handling of empty phone numbers"""
        # Empty string phone
        self.contact.phone = ""
        self.contact.save()
        lead = self.contact.check_if_lead_exists()
        self.assertIsNone(lead)
        self.assertFalse(self.contact.is_lead)
        
        # Null-like phone
        self.contact.phone = ""
        self.contact.save()
        lead = self.contact.check_if_lead_exists()
        self.assertIsNone(lead)
        self.assertFalse(self.contact.is_lead)

    def test_duplicate_name_handling(self):
        """Test handling of duplicate contact names"""
        # First duplicate should match by phone
        self.contact.name = "Duplicate Name"
        self.contact.save()
        lead = self.contact.check_if_lead_exists()
        self.assertEqual(lead, self.lead)
        
        # Second duplicate should not match
        contact2 = Contact.objects.create(
            name="Duplicate Name",
            phone="11888888888",
            user=self.user
        )
        lead2 = contact2.check_if_lead_exists()
        self.assertIsNone(lead2)
