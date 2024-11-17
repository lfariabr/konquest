from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from core.models.contact import Contact
from core.models.user import kUser
from apiCrm.models.lead import Lead

class ContactLeadCheckTest(TestCase):
    def setUp(self):
        # Create test user
        self.user = kUser.objects.create(
            name="Test User",
            email="test@example.com",
            password="testpass123"
        )
        
        # Create test contacts with various phone formats
        self.contacts = {
            'standard': Contact.objects.create(
                name="John Standard",
                phone="11987654321",
                user=self.user
            ),
            'formatted': Contact.objects.create(
                name="John Formatted",
                phone="(11) 98765-4322",
                user=self.user
            ),
            'with_country': Contact.objects.create(
                name="John International",
                phone="+55 11 98765-4323",
                user=self.user
            ),
            'special_chars': Contact.objects.create(
                name="John Special",
                phone="11.98765.4324",
                user=self.user
            ),
            'name_match': Contact.objects.create(
                name="John Special",  # Same name as lead
                phone="123",  # Invalid phone number
                user=self.user
            )
        }
        
        # Create matching leads
        self.leads = {
            'standard': Lead.objects.create(
                id_crm="123",
                name="Different Name",  # Test phone-only match
                email="lead1@test.com",
                phone="11987654321",
                source="Test",
                store="Test Store",
                status="Active",
                created_at=timezone.now()
            ),
            'by_name': Lead.objects.create(
                id_crm="456",
                name="John Special",  # Match by name
                email="lead2@test.com",
                phone="99999999999",  # Different phone
                source="Test",
                store="Test Store",
                status="Pending",
                created_at=timezone.now()
            )
        }

    def test_phone_format_matching(self):
        """Test matching leads with different phone formats"""
        # Standard format should match
        lead = self.contacts['standard'].check_if_lead_exists()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.phone, "11987654321")
        
        # Formatted phone should match after cleaning
        lead = self.contacts['formatted'].check_if_lead_exists()
        self.assertIsNone(lead)  # No matching lead for this phone
        
        # International format should match after cleaning
        lead = self.contacts['with_country'].check_if_lead_exists()
        self.assertIsNone(lead)  # No matching lead for this phone
        
        # Special characters should be handled
        lead = self.contacts['special_chars'].check_if_lead_exists()
        self.assertIsNone(lead)  # No matching lead for this phone

    def test_name_matching_fallback(self):
        """Test that name-only matching is no longer supported"""
        # This contact has a valid name match but invalid phone
        lead = self.contacts['name_match'].check_if_lead_exists()
        self.assertIsNone(lead)  # Should return None as we don't match by name anymore
        
        # Verify status remains unchanged
        self.assertFalse(self.contacts['name_match'].is_lead)
        self.assertIsNone(self.contacts['name_match'].lead_id)
        self.assertIsNone(self.contacts['name_match'].lead_status)

    def test_lead_status_tracking(self):
        """Test that lead status fields are properly updated"""
        contact = self.contacts['standard']
        
        # Initial state
        self.assertFalse(contact.is_lead)
        self.assertIsNone(contact.lead_status)
        
        # After finding lead
        lead = contact.check_if_lead_exists()
        self.assertTrue(contact.is_lead)
        self.assertEqual(contact.lead_status, "Active")
        self.assertEqual(contact.lead_id, "123")
        self.assertIsNotNone(contact.lead_created_at)

    def test_lead_store_tracking(self):
        """Test that lead store is properly tracked"""
        contact = self.contacts['standard']
        
        # Initial state
        self.assertIsNone(contact.store_lead)

        # After finding lead
        lead = contact.check_if_lead_exists()
        self.assertEqual(contact.store_lead, lead.store)

        # After clearing
        contact.phone = "11777777777"  # Non-matching phone
        contact.save()
        contact.check_if_lead_exists()
        self.assertIsNone(contact.store_lead)

    def test_lead_check_tracking(self):
        """Test tracking of lead checks"""
        contact = self.contacts['standard']
        
        # Initial state
        self.assertEqual(contact.lead_check_count, 0)
        self.assertIsNone(contact.lead_last_checked)
        
        # After first check
        contact.check_if_lead_exists()
        self.assertEqual(contact.lead_check_count, 1)
        self.assertIsNotNone(contact.lead_last_checked)
        first_check = contact.lead_last_checked
        
        # After second check
        contact.check_if_lead_exists()
        self.assertEqual(contact.lead_check_count, 2)
        self.assertGreater(contact.lead_last_checked, first_check)

    def test_needs_lead_check(self):
        """Test the needs_lead_check method"""
        contact = self.contacts['standard']
        
        # Never checked before
        self.assertTrue(contact.needs_lead_check())
        
        # Just checked
        contact.check_if_lead_exists()
        self.assertFalse(contact.needs_lead_check())
        
        # Simulate time passing
        contact.lead_last_checked = timezone.now() - timedelta(hours=25)
        contact.save()
        self.assertTrue(contact.needs_lead_check())  # Should need check after 24h
        self.assertFalse(contact.needs_lead_check(hours=48))  # But not after 48h

    def test_lead_check_stats(self):
        """Test the get_lead_check_stats method"""
        contact = self.contacts['standard']
        
        # Initial stats
        stats = contact.get_lead_check_stats()
        self.assertEqual(stats['total_checks'], 0)
        self.assertIsNone(stats['last_checked'])
        self.assertFalse(stats['is_lead'])
        
        # After checking
        contact.check_if_lead_exists()
        stats = contact.get_lead_check_stats()
        self.assertEqual(stats['total_checks'], 1)
        self.assertIsNotNone(stats['last_checked'])
        self.assertTrue(stats['is_lead'])
        self.assertEqual(stats['lead_status'], 'Active')
        self.assertIsNotNone(stats['lead_age'])
