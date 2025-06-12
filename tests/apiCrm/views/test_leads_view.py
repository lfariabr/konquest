from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from apiCrm.models.billcharge import BillCharge
from apiCrm.models.lead import Lead
from apiCrm.models.appointment import Appointment
from core.models import contact, userphone, user
from django.utils import timezone
import logging
from django.test.utils import override_settings
from apiCrm.serializers import LeadSerializer
from django.core.cache import cache

logger = logging.getLogger(__name__)
User = get_user_model()

@override_settings(USE_TZ=False)  # Disable timezone support for tests
class LeadsViewTest(APITestCase):
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

        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=True  # Make sure the user is active
        )
        
        # Generate JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # Set up the client with the token
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        self.leads_url = reverse('leads')
        
        # Create test leads
        self.lead1 = Lead.objects.create(
            id_crm="123",
            name="Test Lead 1",
            phone="11987654321",
            store="Test Store 1",
            status="Active",
            created_at=timezone.now(),
            email=""  # Added missing required field
        )
        self.lead2 = Lead.objects.create(
            id_crm="456",
            name="Test Lead 2",
            phone="11987654322",
            store="Test Store 2",
            status="Inactive",
            created_at=timezone.now(),
            email=""  # Added missing required field
        )
        
        # Verify leads were created
        logger.info(f"Created leads: {Lead.objects.count()}")
        for lead in Lead.objects.all():
            logger.info(f"Lead: {lead.id_crm} - {lead.name}")

    def test_get_all_leads(self):
        """Test retrieving all leads"""
        # Verify leads exist before making request
        self.assertEqual(Lead.objects.count(), 2)
        
        response = self.client.get(self.leads_url)
        leads = Lead.objects.all()
        serializer = LeadSerializer(leads, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Compare all fields except timestamps
        response_data = response.data[0]
        serializer_data = serializer.data[0]
        
        for key in response_data:
            if key not in ['created_at']:
                self.assertEqual(response_data[key], serializer_data[key])
        
        self.assertEqual(len(response.data), 2)

    def test_get_leads_check_content(self):
        """Test the content of retrieved leads"""
        response = self.client.get(self.leads_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['id_crm'], "123")
        self.assertEqual(response.data[0]['name'], "Test Lead 1")
        self.assertEqual(response.data[0]['phone'], "11987654321")
        self.assertEqual(response.data[0]['store'], "Test Store 1")

    def test_get_leads_no_leads(self):
        """Test retrieving leads when there are none"""
        Lead.objects.all().delete()
        response = self.client.get(self.leads_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_leads_only_allows_get(self):
        """Test that only GET requests are allowed"""
        response = self.client.post(self.leads_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_leads_url_exists(self):
        """Test that the leads URL exists"""
        response = self.client.get(self.leads_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
