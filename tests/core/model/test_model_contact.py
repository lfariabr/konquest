from django.test import TestCase
from django.utils import timezone
from core.models.contact import Contact
from core.models.user import kUser
from apiCrm.models.lead import Lead

class ContactModelTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = kUser.objects.create(
            name="Test User",
            email="test@example.com",
            password="testpass123"
        )
        
        # Create a test contact
        self.contact = Contact.objects.create(
            name="John Doe",
            phone="(11) 98765-4321",
            user=self.user,
            source="WhatsApp",
            store="Test Store",
            region="Test Region",
            relationship_tag="Preenchimento",  # Use relationship_tag here
        )
        
        # Create test leads
        self.lead_same_phone = Lead.objects.create(
            id_crm="123",
            name="John Different",
            email="john@example.com",
            phone="11987654321",  # Same phone, different format
            source="CRM",
            store="Test Store",
            status="Active",
            created_at=timezone.now()
        )
        
        self.lead_same_name = Lead.objects.create(
            id_crm="456",
            name="John Doe",  # Same name
            email="different@example.com",
            phone="11999999999",  # Different phone
            source="CRM",
            store="Test Store",
            status="Active",
            created_at=timezone.now()
        )
        
        self.lead_different = Lead.objects.create(
            id_crm="789",
            name="Different Person",
            email="diff@example.com",
            phone="11888888888",
            source="CRM",
            store="Test Store",
            status="Active",
            created_at=timezone.now()
        )

    def test_check_if_lead_exists_by_phone(self):
        """Test finding a lead by phone number with different formats"""
        lead = self.contact.check_if_lead_exists()
        self.assertEqual(lead, self.lead_same_phone)
        
        # Test with different phone formats
        self.contact.phone = "11987654321"  # No formatting
        self.contact.save()
        lead = self.contact.check_if_lead_exists()
        self.assertEqual(lead, self.lead_same_phone)
        
        self.contact.phone = "+55 (11) 98765-4321"  # With country code
        self.contact.save()
        lead = self.contact.check_if_lead_exists()
        self.assertEqual(lead, self.lead_same_phone)

    def test_check_if_lead_exists_by_name(self):
        """Test that name-only matching is not supported"""
        self.contact.phone = "123"  # Invalid/short phone number
        self.contact.save()
        lead = self.contact.check_if_lead_exists()
        self.assertIsNone(lead)  # Should return None as we no longer support name-only matching

    def test_check_if_lead_exists_no_match(self):
        """Test when no matching lead exists"""
        self.contact.name = "No Match"
        self.contact.phone = "11000000000"
        self.contact.save()
        lead = self.contact.check_if_lead_exists()
        self.assertIsNone(lead)

    def test_check_if_lead_exists_with_special_chars(self):
        """Test phone matching with various special characters"""
        test_phones = [
            "(11)987654321",
            "11.98765.4321",
            "11_98765_4321",
            " 11 98765 4321 ",
        ]
        
        for phone in test_phones:
            self.contact.phone = phone
            self.contact.save()
            lead = self.contact.check_if_lead_exists()
            self.assertEqual(lead, self.lead_same_phone)

    def test_lead_status_tracking_by_phone(self):
        """Test that contact's lead status fields are updated when lead is found by phone"""
        lead = self.contact.check_if_lead_exists()
        self.assertTrue(self.contact.is_lead)
        self.assertEqual(self.contact.lead_id, self.lead_same_phone.id_crm)
        self.assertEqual(self.contact.lead_status, self.lead_same_phone.status)
        self.assertEqual(self.contact.lead_created_at, self.lead_same_phone.created_at)

    def test_lead_status_tracking_by_name(self):
        """Test that name-only matching is not supported and status remains unchanged"""
        self.contact.phone = "123"  # Invalid/short phone number
        self.contact.save()
        lead = self.contact.check_if_lead_exists()
        self.assertFalse(self.contact.is_lead)  # Should remain False as we don't match by name
        self.assertIsNone(self.contact.lead_id)
        self.assertIsNone(self.contact.lead_status)

    def test_lead_status_cleared_when_not_found(self):
        """Test that contact's lead status fields are cleared when no lead is found"""
        # First make it a lead
        lead = self.contact.check_if_lead_exists()
        self.assertTrue(self.contact.is_lead)
        
        # Then change details so no lead matches
        self.contact.name = "No Match"
        self.contact.phone = "11000000000"
        self.contact.save()
        lead = self.contact.check_if_lead_exists()
        
        self.assertFalse(self.contact.is_lead)
        self.assertIsNone(self.contact.lead_id)
        self.assertIsNone(self.contact.lead_status)
        self.assertIsNone(self.contact.lead_created_at)

    def test_str_representation(self):
        """Test the string representation of Contact with and without lead status"""
        # When not a lead
        self.assertEqual(str(self.contact), "John Doe - (11) 98765-4321")
        
        # When is a lead
        lead = self.contact.check_if_lead_exists()
        self.assertEqual(str(self.contact), f"John Doe - (11) 98765-4321 (Lead: {self.lead_same_phone.status})")

    def test_lead_check_tracking(self):
        """Test that lead check tracking is updated correctly"""
        # Initial state
        self.assertIsNone(self.contact.lead_last_checked)
        self.assertEqual(self.contact.lead_check_count, 0)
        
        # First check
        lead = self.contact.check_if_lead_exists()
        self.assertIsNotNone(self.contact.lead_last_checked)
        self.assertEqual(self.contact.lead_check_count, 1)
        
        # Second check
        lead = self.contact.check_if_lead_exists()
        self.assertEqual(self.contact.lead_check_count, 2)

    def test_needs_lead_check(self):
        """Test the needs_lead_check method"""
        # Never checked before
        self.assertTrue(self.contact.needs_lead_check())
        
        # Just checked
        self.contact.check_if_lead_exists()
        self.assertFalse(self.contact.needs_lead_check())
        
        # Check with different hour thresholds
        self.assertTrue(self.contact.needs_lead_check(hours=0))  # Always needs check
        self.assertFalse(self.contact.needs_lead_check(hours=24))  # Doesn't need check within 24h
        
        # Simulate time passing
        self.contact.lead_last_checked = timezone.now() - timezone.timedelta(hours=25)
        self.contact.save()
        self.assertTrue(self.contact.needs_lead_check(hours=24))  # Needs check after 24h

    def test_get_lead_check_stats(self):
        """Test the get_lead_check_stats method"""
        # Initial stats
        stats = self.contact.get_lead_check_stats()
        self.assertEqual(stats['total_checks'], 0)
        self.assertIsNone(stats['last_checked'])
        self.assertFalse(stats['is_lead'])
        self.assertIsNone(stats['lead_status'])
        self.assertIsNone(stats['lead_age'])
        
        # Stats after becoming a lead
        self.contact.check_if_lead_exists()
        stats = self.contact.get_lead_check_stats()
        self.assertEqual(stats['total_checks'], 1)
        self.assertIsNotNone(stats['last_checked'])
        self.assertTrue(stats['is_lead'])
        self.assertEqual(stats['lead_status'], self.lead_same_phone.status)
        self.assertIsNotNone(stats['lead_age'])
