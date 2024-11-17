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
        
        # Create a test contact
        self.contact = Contact.objects.create(
            name="John Doe",
            phone="(11) 98765-4321",
            user=self.user,
            source="WhatsApp",
            store="Test Store",
            region="Test Region"
        )
        
        # Create test appointments
        self.appointment_same_phone = Appointment.objects.create(
            id_crm="123",
            customer_name="John Different",
            customer_phone="11987654321",  # Same phone, different format
            store_name="Test Store",
            status_label="Agendado",
            appointment_date=timezone.now(),
            createdby_name="Test Creator",
            createdby_created_at=timezone.now(),
            procedure_name="Test Procedure",
            procedure_group="Test Group",
            employee_name="Test Employee",
            customer_id=""
        )
        
        self.appointment_different_phone = Appointment.objects.create(
            id_crm="456",
            customer_name="John Doe",  # Same name
            customer_phone="11999999999",  # Different phone
            store_name="Test Store",
            status_label="Agendado",
            appointment_date=timezone.now(),
            createdby_name="Test Creator",
            createdby_created_at=timezone.now(),
            procedure_name="Test Procedure",
            procedure_group="Test Group",
            employee_name="Test Employee",
            customer_id=""
        )

    def test_check_if_appointment_exists_by_phone(self):
        """Test finding an appointment by phone number with different formats"""
        # Test standard format
        appointment = self.contact.check_if_appointment_exists()
        self.assertEqual(appointment, self.appointment_same_phone)

        # Test with country code
        self.contact.phone = "+55 (11) 98765-4321"
        self.contact.save()
        appointment = self.contact.check_if_appointment_exists()
        self.assertEqual(appointment, self.appointment_same_phone)

    def test_check_if_appointment_exists_no_match(self):
        """Test when no matching appointment exists"""
        self.contact.name = "No Match"
        self.contact.phone = "11777777777"
        self.contact.save()
        appointment = self.contact.check_if_appointment_exists()
        self.assertIsNone(appointment)

    def test_check_if_appointment_exists_with_special_chars(self):
        """Test phone matching with special characters"""
        self.contact.phone = "11.98765.4321"
        self.contact.save()
        appointment = self.contact.check_if_appointment_exists()
        self.assertEqual(appointment, self.appointment_same_phone)

    def test_appointment_status_tracking(self):
        """Test that contact's appointment status fields are updated"""
        # Check initial state
        self.assertFalse(self.contact.is_appointment)
        self.assertIsNone(self.contact.appointment_id)
        self.assertIsNone(self.contact.appointment_status)
        self.assertIsNone(self.contact.appointment_created_at)

        # Find appointment
        appointment = self.contact.check_if_appointment_exists()
        
        # Check updated state
        self.assertTrue(self.contact.is_appointment)
        self.assertEqual(self.contact.appointment_id, "123")
        self.assertEqual(self.contact.appointment_status, "Agendado")
        self.assertEqual(self.contact.appointment_created_at, self.appointment_same_phone.appointment_date)

    def test_appointment_status_cleared_when_not_found(self):
        """Test that contact's appointment status fields are cleared when no appointment is found"""
        # First make it an appointment
        appointment = self.contact.check_if_appointment_exists()
        self.assertTrue(self.contact.is_appointment)

        # Change phone to non-matching
        self.contact.phone = "11777777777"
        self.contact.save()
        appointment = self.contact.check_if_appointment_exists()

        # Check that status is cleared
        self.assertFalse(self.contact.is_appointment)
        self.assertIsNone(self.contact.appointment_id)
        self.assertIsNone(self.contact.appointment_status)
        self.assertIsNone(self.contact.appointment_created_at)

    def test_appointment_store_tracking(self):
        """Test that appointment store is properly tracked"""
        # Initial state
        self.assertIsNone(self.contact.store_appointment)

        # After finding appointment
        appointment = self.contact.check_if_appointment_exists()
        self.assertEqual(self.contact.store_appointment, self.appointment_same_phone.store_name)

        # After clearing
        self.contact.phone = "11777777777"  # Non-matching phone
        self.contact.save()
        self.contact.check_if_appointment_exists()
        self.assertIsNone(self.contact.store_appointment)

        # Test with different store
        self.contact.phone = self.appointment_different_phone.customer_phone
        self.contact.save()
        appointment = self.contact.check_if_appointment_exists()
        self.assertEqual(self.contact.store_appointment, self.appointment_different_phone.store_name)

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

    def test_get_appointment_check_stats(self):
        """Test the get_appointment_check_stats method"""
        # Initial stats
        stats = self.contact.get_appointment_check_stats()
        self.assertEqual(stats['total_checks'], 0)
        self.assertIsNone(stats['last_checked'])
        self.assertFalse(stats['is_appointment'])
        self.assertIsNone(stats['appointment_status'])
        self.assertIsNone(stats['appointment_age'])

        # Stats after finding appointment
        self.contact.check_if_appointment_exists()
        stats = self.contact.get_appointment_check_stats()
        self.assertEqual(stats['total_checks'], 1)
        self.assertIsNotNone(stats['last_checked'])
        self.assertTrue(stats['is_appointment'])
        self.assertEqual(stats['appointment_status'], "Agendado")
        self.assertIsNotNone(stats['appointment_age'])
