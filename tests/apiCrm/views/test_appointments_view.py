from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apiCrm.models.appointment import Appointment
from apiCrm.models.lead import Lead
from apiCrm.models.billcharge import BillCharge
from apiCrm.serializers import AppointmentSerializer
from core.models import contact, userphone, user
from django.utils import timezone
import logging
from django.test.utils import override_settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

@override_settings(USE_TZ=False)  # Disable timezone support for tests
class AppointmentsViewTest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Clear the cache
        cache.clear()
        
        # Clean up any existing data
        Appointment.objects.all().delete()
        Lead.objects.all().delete()
        BillCharge.objects.all().delete()
        contact.Contact.objects.all().delete()
        userphone.UserPhone.objects.all().delete()
        user.kUser.objects.all().delete()

        # Create test data
        self.client = APIClient()
        self.appointments_url = reverse('appointments')
        
        # Create test appointments
        self.appointment1 = Appointment.objects.create(
            id_crm="123",
            status_label="Agendado",
            store_name="Test Store 1",
            customer_id="",
            customer_name="Test Customer 1",
            customer_phone="11987654321",
            procedure_name="Test Procedure 1",
            procedure_group="Test Group 1",
            employee_name="Test Employee 1",
            createdby_name="Test Creator 1",
            createdby_created_at=timezone.now(),
            appointment_date=timezone.now()
        )
        self.appointment2 = Appointment.objects.create(
            id_crm="456",
            status_label="Cancelado",
            store_name="Test Store 2",
            customer_id="",
            customer_name="Test Customer 2",
            customer_phone="11987654322",
            procedure_name="Test Procedure 2",
            procedure_group="Test Group 2",
            employee_name="Test Employee 2",
            createdby_name="Test Creator 2",
            createdby_created_at=timezone.now(),
            appointment_date=timezone.now()
        )
        
        # Verify appointments were created
        logger.info(f"Created appointments: {Appointment.objects.count()}")
        for appointment in Appointment.objects.all():
            logger.info(f"Appointment: {appointment.id_crm} - {appointment.customer_name}")

    def test_get_all_appointments(self):
        """Test retrieving all appointments"""
        # Verify appointments exist before making request
        self.assertEqual(Appointment.objects.count(), 2)
        
        response = self.client.get(self.appointments_url)
        appointments = Appointment.objects.all()
        serializer = AppointmentSerializer(appointments, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Compare all fields except timestamps
        response_data = response.data[0]
        serializer_data = serializer.data[0]
        
        for key in response_data:
            if key not in ['appointment_date', 'createdby_created_at']:
                self.assertEqual(response_data[key], serializer_data[key])
        
        self.assertEqual(len(response.data), 2)

    def test_get_appointments_check_content(self):
        """Test the content of retrieved appointments"""
        response = self.client.get(self.appointments_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['id_crm'], "123")
        self.assertEqual(response.data[0]['status_label'], "Agendado")
        self.assertEqual(response.data[0]['customer_name'], "Test Customer 1")
        self.assertEqual(response.data[0]['customer_phone'], "11987654321")
        self.assertEqual(response.data[0]['store_name'], "Test Store 1")

    def test_get_appointments_no_appointments(self):
        """Test retrieving appointments when there are none"""
        Appointment.objects.all().delete()
        response = self.client.get(self.appointments_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_appointments_only_allows_get(self):
        """Test that only GET requests are allowed"""
        response = self.client.post(self.appointments_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        response = self.client.put(self.appointments_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        response = self.client.delete(self.appointments_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_appointments_url_exists(self):
        """Test that the appointments URL exists"""
        response = self.client.get(self.appointments_url)
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_appointments_date_format(self):
        """Test that appointment dates are properly formatted"""
        response = self.client.get(self.appointments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that dates are in ISO format
        appointment = response.data[0]
        self.assertIn('appointment_date', appointment)
        self.assertIn('createdby_created_at', appointment)
        
        # Verify date format (should be ISO format)
        self.assertRegex(appointment['appointment_date'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')
        self.assertRegex(appointment['createdby_created_at'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')
