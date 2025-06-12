from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from apiCrm.models.appointment import Appointment
from apiCrm.serializers import AppointmentSerializer
from core.models import contact, userphone, user
from django.utils import timezone
import logging
from django.test.utils import override_settings
from django.core.cache import cache

logger = logging.getLogger(__name__)
User = get_user_model()

@override_settings(USE_TZ=False)  # Disable timezone support for tests
class AppointmentsViewTest(APITestCase):
    def setUp(self):
        """Set up test data"""
        # Clear the cache
        cache.clear()
        
        # Clean up any existing data
        Appointment.objects.all().delete()
        contact.Contact.objects.all().delete()
        userphone.UserPhone.objects.all().delete()
        user.kUser.objects.all().delete()

        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=True
        )
        
        # Generate JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # Set up the client with the token
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        self.appointments_url = reverse('appointments')
        
        # Create test appointments
        now = timezone.now()
        self.appointment1 = Appointment.objects.create(
            id_crm="789",
            status_label="Scheduled",
            store_name="Test Store",
            customer_id="cust123",
            customer_name="Test Customer 1",
            customer_phone="11987654321",
            procedure_name="Test Procedure 1",
            procedure_group="Test Group",
            employee_name="Test Employee",
            createdby_name="Test Creator",
            createdby_created_at=now,
            appointment_date=now
        )
        self.appointment2 = Appointment.objects.create(
            id_crm="101112",
            status_label="Completed",
            store_name="Test Store 2",
            customer_id="cust456",
            customer_name="Test Customer 2",
            customer_phone="11987654322",
            procedure_name="Test Procedure 2",
            procedure_group="Test Group 2",
            employee_name="Test Employee 2",
            createdby_name="Test Creator 2",
            createdby_created_at=now,
            appointment_date=now + timezone.timedelta(days=1)
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
        self.assertEqual(len(response.data), 2)
        
        # Compare all fields except timestamps
        response_data = response.data[0]
        serializer_data = serializer.data[0]
        
        for key in response_data:
            if key not in ['createdby_created_at', 'appointment_date']:
                self.assertEqual(response_data[key], serializer_data[key])

    def test_get_appointments_check_content(self):
        """Test the content of retrieved appointments"""
        response = self.client.get(self.appointments_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['id_crm'], "789")
        self.assertEqual(response.data[0]['customer_name'], "Test Customer 1")
        self.assertEqual(response.data[0]['status_label'], "Scheduled")

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

    def test_appointments_date_format(self):
        """Test that appointment dates are properly formatted"""
        response = self.client.get(self.appointments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the date fields exist and are in the correct format
        for appointment in response.data:
            self.assertIn('createdby_created_at', appointment)
            self.assertIn('appointment_date', appointment)
            # Add more specific date format checks if needed
