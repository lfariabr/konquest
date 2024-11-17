from django.test import TestCase, RequestFactory
from django.contrib import admin, messages
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from core.admin import ContactAdmin
from core.models.contact import Contact
from core.models.user import kUser
from apiCrm.models.appointment import Appointment
from django.utils import timezone

class MockSuperUser:
    def has_perm(self, perm):
        return True

class ContactAdminAppointmentTest(TestCase):
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
        self.contact1 = Contact.objects.create(
            name="Test Contact 1",
            phone="11987654321",
            user=self.user
        )
        self.contact2 = Contact.objects.create(
            name="Test Contact 2",
            phone="11987654322",
            user=self.user
        )

        # Create test appointment
        self.appointment = Appointment.objects.create(
            id_crm="123",
            customer_name="Test Contact 1",
            customer_phone="11987654321",
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

    def test_admin_list_display(self):
        """Test that appointment fields are included in list_display"""
        self.assertIn('is_appointment', self.admin.list_display)
        self.assertIn('appointment_id', self.admin.list_display)
        self.assertIn('appointment_status', self.admin.list_display)
        self.assertIn('appointment_created_at', self.admin.list_display)
        self.assertIn('appointment_last_checked', self.admin.list_display)
        self.assertIn('appointment_check_count', self.admin.list_display)

    def test_check_appointments_action(self):
        """Test the check_appointments admin action"""
        request = self.factory.get('/')
        request.user = MockSuperUser()

        # Add message storage to request
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # Execute action
        queryset = Contact.objects.all()
        self.admin.check_appointments(request, queryset)

        # Verify results
        self.contact1.refresh_from_db()
        self.contact2.refresh_from_db()

        # Contact1 should have appointment
        self.assertTrue(self.contact1.is_appointment)
        self.assertEqual(self.contact1.appointment_id, "123")
        self.assertEqual(self.contact1.appointment_status, "Agendado")

        # Contact2 should not have appointment
        self.assertFalse(self.contact2.is_appointment)
        self.assertIsNone(self.contact2.appointment_id)
        self.assertIsNone(self.contact2.appointment_status)

    def test_check_appointments_with_subset(self):
        """Test checking appointments with a subset of contacts"""
        request = self.factory.get('/')
        request.user = MockSuperUser()

        # Add message storage to request
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # Execute action on subset
        queryset = Contact.objects.filter(id=self.contact1.id)
        self.admin.check_appointments(request, queryset)

        # Verify results
        self.contact1.refresh_from_db()
        self.contact2.refresh_from_db()

        # Contact1 should have appointment
        self.assertTrue(self.contact1.is_appointment)
        self.assertEqual(self.contact1.appointment_id, "123")
        self.assertEqual(self.contact1.appointment_status, "Agendado")

        # Contact2 should not be checked
        self.assertEqual(self.contact2.appointment_check_count, 0)
        self.assertIsNone(self.contact2.appointment_last_checked)
