from django.test import TestCase
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from core.models.contact import Contact
from core.models.user import kUser
from apiCrm.models.lead import Lead
import time

class ContactLeadEdgeCasesTest(TestCase):
    def setUp(self):
        self.user = kUser.objects.create(
            name="Test User",
            email="test@example.com",
            password="testpass123"
        )
        
        # Create contacts with edge case scenarios
        self.contacts = {
            'empty_phone': Contact.objects.create(
                name="Empty Phone",
                phone="",
                user=self.user
            ),
            'null_like_phone': Contact.objects.create(
                name="Null Phone",
                phone="",
                user=self.user
            ),
            'special_chars': Contact.objects.create(
                name="Special Chars",
                phone="!@#11$%^98&*()765_+-4321",
                user=self.user
            ),
            'very_long_phone': Contact.objects.create(
                name="Long Phone",
                phone="+1234567890123456789011987654321",
                user=self.user
            ),
            'whitespace_phone': Contact.objects.create(
                name="Whitespace Phone",
                phone="   11   98765   4321   ",
                user=self.user
            ),
            'duplicate_name': Contact.objects.create(
                name="Duplicate Name",
                phone="11999999999",
                user=self.user
            ),
            'duplicate_name_2': Contact.objects.create(
                name="Duplicate Name",
                phone="11888888888",
                user=self.user
            )
        }
        
        # Create leads for edge cases
        self.leads = {
            'standard': Lead.objects.create(
                id_crm="123",
                name="Standard Lead",
                email="lead@test.com",
                phone="11987654321",
                source="Test",
                store="Test Store",
                status="Active",
                created_at=timezone.now()
            ),
            'duplicate_name': Lead.objects.create(
                id_crm="456",
                name="Duplicate Name",
                email="duplicate@test.com",
                phone="11999999999",
                source="Test",
                store="Test Store",
                status="Active",
                created_at=timezone.now()
            )
        }

    def test_empty_phone_handling(self):
        """Test handling of empty phone numbers"""
        # Empty string phone
        lead = self.contacts['empty_phone'].check_if_lead_exists()
        self.assertIsNone(lead)
        self.assertFalse(self.contacts['empty_phone'].is_lead)
        
        # Null-like phone
        lead = self.contacts['null_like_phone'].check_if_lead_exists()
        self.assertIsNone(lead)
        self.assertFalse(self.contacts['null_like_phone'].is_lead)

    def test_special_chars_phone(self):
        """Test handling of phones with special characters"""
        contact = self.contacts['special_chars']
        # Should extract "11987654321" from special chars
        lead = contact.check_if_lead_exists()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.phone, "11987654321")

    def test_very_long_phone(self):
        """Test handling of very long phone numbers"""
        contact = self.contacts['very_long_phone']
        # Should use last 11 digits
        self.assertEqual(
            ''.join(filter(str.isdigit, contact.phone))[-11:],
            "11987654321"
        )
        lead = contact.check_if_lead_exists()
        self.assertIsNotNone(lead)

    def test_whitespace_phone(self):
        """Test handling of phones with excessive whitespace"""
        contact = self.contacts['whitespace_phone']
        cleaned_phone = ''.join(filter(str.isdigit, contact.phone))
        self.assertEqual(cleaned_phone, "11987654321")
        lead = contact.check_if_lead_exists()
        self.assertIsNotNone(lead)

    def test_duplicate_name_handling(self):
        """Test handling of duplicate contact names"""
        # First duplicate should match by phone
        contact1 = self.contacts['duplicate_name']
        lead1 = contact1.check_if_lead_exists()
        self.assertIsNotNone(lead1)
        self.assertEqual(lead1.phone, "11999999999")
        
        # Second duplicate should not match
        contact2 = self.contacts['duplicate_name_2']
        lead2 = contact2.check_if_lead_exists()
        self.assertIsNone(lead2)

    def test_concurrent_checks(self):
        """Test handling multiple concurrent lead checks"""
        contact1 = self.contacts['special_chars']
        contact2 = self.contacts['whitespace_phone']
        
        with transaction.atomic():
            lead1 = contact1.check_if_lead_exists()
            lead2 = contact2.check_if_lead_exists()
        
        self.assertIsNotNone(lead1)
        self.assertIsNotNone(lead2)
        self.assertEqual(contact1.lead_check_count, 1)
        self.assertEqual(contact2.lead_check_count, 1)

    def test_rapid_consecutive_checks(self):
        """Test handling rapid consecutive checks"""
        contact = self.contacts['special_chars']
        
        # Perform 5 rapid checks
        for _ in range(5):
            contact.check_if_lead_exists()
            time.sleep(0.1)  # Small delay to ensure distinct timestamps
        
        self.assertEqual(contact.lead_check_count, 5)
        self.assertTrue(contact.is_lead)

    def test_status_transitions(self):
        """Test lead status transitions"""
        contact = self.contacts['special_chars']
        
        # Initial check - should be a lead
        lead = contact.check_if_lead_exists()
        self.assertTrue(contact.is_lead)
        initial_status = contact.lead_status
        
        # Update lead status
        lead.status = "Inactive"
        lead.save()
        
        # Check again - should update status
        contact.check_if_lead_exists()
        self.assertEqual(contact.lead_status, "Inactive")
        
        # Delete lead
        lead.delete()
        
        # Check again - should no longer be a lead
        contact.check_if_lead_exists()
        self.assertFalse(contact.is_lead)
        self.assertIsNone(contact.lead_status)

    def test_performance_with_many_leads(self):
        """Test performance with a large number of leads"""
        # Create 100 leads
        start_time = time.time()
        leads = []
        for i in range(100):
            lead = Lead.objects.create(
                id_crm=f"test{i}",
                name=f"Test Lead {i}",
                email=f"test{i}@test.com",
                phone=f"1199999{i:04d}",
                source="Test",
                store="Test Store",
                status="Active",
                created_at=timezone.now()
            )
            leads.append(lead)
        
        # Test checking a contact
        contact = self.contacts['special_chars']
        lead = contact.check_if_lead_exists()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Check should complete in reasonable time (adjust threshold as needed)
        self.assertLess(execution_time, 2.0)  # Should take less than 2 seconds
        self.assertIsNotNone(lead)  # Should still find the correct lead
