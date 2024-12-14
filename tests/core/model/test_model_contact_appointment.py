from django.test import TestCase
from django.utils import timezone
from core.models.contact import Contact
from core.models.user import kUser
from apiCrm.models.appointment import Appointment

class ContactAppointmentTest(TestCase):
    def setUp(self):
        # Create a test user
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
            region="Test Region",
            relationship_tag="Preenchimento",
        )
        
        # Create test appointments with matching clean phone numbers
        self.appointment_same_phone = Appointment.objects.create(
            id_crm="123",
            customer_name="John Different",
            customer_phone="11987654321",  # Exact same format as contact
            store_name="Test Store",
            status_label="Agendado",
            createdby_created_at=timezone.now(),
            appointment_date=timezone.now()
        )
        
        self.appointment_different = Appointment.objects.create(
            id_crm="789",
            customer_name="Different Person",
            customer_phone="11888888888",
            store_name="Test Store",
            status_label="Agendado",
            createdby_created_at=timezone.now(),
            appointment_date=timezone.now()
        )

    def test_check_if_appointment_exists_by_phone(self):
        """Test finding an appointment by exact phone number match"""
        appointment = self.contact.check_if_appointment_exists()
        self.assertEqual(appointment, self.appointment_same_phone)
        
        # Test with exact same format
        self.contact.phone = "11987654321"
        self.contact.save()
        appointment = self.contact.check_if_appointment_exists()
        self.assertEqual(appointment, self.appointment_same_phone)

    def test_check_if_appointment_exists_with_special_chars(self):
        """Test exact phone number matching"""
        self.contact.phone = "11987654321"  # Must match exactly
        self.contact.save()
        appointment = self.contact.check_if_appointment_exists()
        self.assertEqual(appointment, self.appointment_same_phone)

    def test_appointment_status_tracking(self):
        """Test that contact's appointment status fields are updated"""
        appointment = self.contact.check_if_appointment_exists()
        self.assertTrue(self.contact.is_appointment)
        self.assertEqual(self.contact.appointment_id, self.appointment_same_phone.id_crm)
        self.assertEqual(self.contact.appointment_status, self.appointment_same_phone.status_label)
        
        # Compare timestamps with a small tolerance for microsecond differences
        time_difference = abs(self.contact.appointment_created_at - self.appointment_same_phone.createdby_created_at)
        self.assertLess(time_difference.total_seconds(), 1)  # Allow 1 second difference

    def test_appointment_status_cleared_when_not_found(self):
        """Test that contact's appointment status fields are cleared when no appointment is found"""
        # First make it an appointment
        appointment = self.contact.check_if_appointment_exists()
        self.assertTrue(self.contact.is_appointment)
        
        # Then change phone so no appointment matches
        self.contact.phone = "11000000000"
        self.contact.save()
        appointment = self.contact.check_if_appointment_exists()
        
        self.assertFalse(self.contact.is_appointment)
        self.assertIsNone(self.contact.appointment_id)
        self.assertIsNone(self.contact.appointment_status)
        self.assertIsNone(self.contact.appointment_created_at)

    def test_appointment_store_tracking(self):
        """Test that store information is tracked correctly"""
        appointment = self.contact.check_if_appointment_exists()
        self.assertEqual(self.contact.store_appointment, self.appointment_same_phone.store_name)

    def test_get_appointment_check_stats(self):
        """Test the get_appointment_check_stats method"""
        # Initial stats
        stats = self.contact.get_appointment_check_stats()
        self.assertEqual(stats['total_checks'], 0)
        self.assertIsNone(stats['last_checked'])
        self.assertFalse(stats['is_appointment'])
        self.assertIsNone(stats['appointment_status'])
        
        # Stats after finding appointment
        self.contact.check_if_appointment_exists()
        stats = self.contact.get_appointment_check_stats()
        self.assertEqual(stats['total_checks'], 1)
        self.assertIsNotNone(stats['last_checked'])
        self.assertTrue(stats['is_appointment'])
        self.assertEqual(stats['appointment_status'], self.appointment_same_phone.status_label)

    def test_needs_appointment_check(self):
        """Test the needs_appointment_check method"""
        # Should need check initially
        self.assertTrue(self.contact.needs_appointment_check())

        # Shouldn't need check right after checking
        self.contact.check_if_appointment_exists()
        self.assertFalse(self.contact.needs_appointment_check())

        # Should need check after time passes
        self.contact.appointment_last_checked = timezone.now() - timezone.timedelta(hours=25)
        self.contact.save()
        self.assertTrue(self.contact.needs_appointment_check())

    def test_appointment_check_tracking(self):
        """Test that appointment check tracking is updated correctly"""
        # Initial state
        self.assertEqual(self.contact.appointment_check_count, 0)
        self.assertIsNone(self.contact.appointment_last_checked)

        # First check
        first_check_time = timezone.now()
        self.contact.check_if_appointment_exists()
        self.assertEqual(self.contact.appointment_check_count, 1)
        self.assertIsNotNone(self.contact.appointment_last_checked)
        self.assertGreaterEqual(self.contact.appointment_last_checked, first_check_time)

        # Second check
        second_check_time = timezone.now()
        self.contact.check_if_appointment_exists()
        self.assertEqual(self.contact.appointment_check_count, 2)
        self.assertGreaterEqual(self.contact.appointment_last_checked, second_check_time)
