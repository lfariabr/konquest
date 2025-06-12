from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from apiCrm.models.billcharge import BillCharge
from apiCrm.serializers import BillChargeSerializer
from core.models import contact, userphone, user
from django.utils import timezone
import logging
from django.test.utils import override_settings
from django.core.cache import cache

logger = logging.getLogger(__name__)
User = get_user_model()

@override_settings(USE_TZ=False)  # Disable timezone support for tests
class BillChargesViewTest(APITestCase):
    def setUp(self):
        """Set up test data"""
        # Clear the cache
        cache.clear()
        
        # Clean up any existing data
        BillCharge.objects.all().delete()
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
        
        self.bill_charges_url = reverse('bill-charges')
        
        # Create test bill charges
        self.bill_charge1 = BillCharge.objects.create(
            quote_id="123",
            status="paid",
            store_name="Test Store 1",
            customer_id="cust123",
            customer_name="Test Customer 1",
            customer_phone="11987654321",
            customer_taxvat="12345678901",
            customer_email="test1@example.com",
            total_amount=100.50,
            due_at=timezone.now(),
            is_paid=True,
            payment_method="credit_card",
            quote_items="Item 1;Item 2"
        )
        self.bill_charge2 = BillCharge.objects.create(
            quote_id="456",
            status="pending",
            store_name="Test Store 2",
            customer_id="cust456",
            customer_name="Test Customer 2",
            customer_phone="11987654322",
            customer_taxvat="98765432109",
            customer_email="test2@example.com",
            total_amount=200.75,
            due_at=timezone.now() + timezone.timedelta(days=30),
            is_paid=False,
            payment_method="pix",
            quote_items="Item 3;Item 4"
        )
        
        # Verify bill charges were created
        logger.info(f"Created bill charges: {BillCharge.objects.count()}")
        for charge in BillCharge.objects.all():
            logger.info(f"Bill Charge: {charge.quote_id} - {charge.customer_name} - {charge.total_amount}")

    def test_get_all_bill_charges(self):
        """Test retrieving all bill charges"""
        # Verify bill charges exist before making request
        self.assertEqual(BillCharge.objects.count(), 2)
        
        response = self.client.get(self.bill_charges_url)
        bill_charges = BillCharge.objects.all()
        serializer = BillChargeSerializer(bill_charges, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Compare all fields except timestamps
        response_data = response.data[0]
        serializer_data = serializer.data[0]
        
        for key in response_data:
            if key not in ['created_at', 'due_at']:
                self.assertEqual(response_data[key], serializer_data[key])

    def test_get_bill_charges_check_content(self):
        """Test the content of retrieved bill charges"""
        response = self.client.get(self.bill_charges_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['quote_id'], "123")
        self.assertEqual(response.data[0]['customer_name'], "Test Customer 1")
        self.assertEqual(response.data[0]['status'], "paid")
        self.assertEqual(float(response.data[0]['total_amount']), 100.50)

    def test_get_bill_charges_no_charges(self):
        """Test retrieving bill charges when there are none"""
        BillCharge.objects.all().delete()
        response = self.client.get(self.bill_charges_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_bill_charges_only_allows_get(self):
        """Test that only GET requests are allowed"""
        response = self.client.post(self.bill_charges_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_bill_charges_date_format(self):
        """Test that bill charge dates are properly formatted"""
        response = self.client.get(self.bill_charges_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
        # Check that the date fields exist and are in the correct format
        for charge in response.data:
            self.assertIn('due_at', charge)
            # Verify the date format by trying to parse it
            if charge['due_at'] is not None:
                from datetime import datetime
                try:
                    datetime.fromisoformat(charge['due_at'].replace('Z', '+00:00'))
                except ValueError:
                    self.fail(f"Invalid date format for due_at: {charge['due_at']}")

    def test_bill_charges_value_format(self):
        """Test that bill charge values are properly formatted"""
        response = self.client.get(self.bill_charges_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that values are properly formatted as strings that can be converted to float
        for charge in response.data:
            self.assertIn('total_amount', charge)
            try:
                float(charge['total_amount'])
            except (TypeError, ValueError):
                self.fail(f"Value {charge['total_amount']} is not a valid number")
