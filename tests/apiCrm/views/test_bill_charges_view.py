from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apiCrm.models.billcharge import BillCharge
from apiCrm.models.lead import Lead
from apiCrm.models.appointment import Appointment
from core.models import contact, userphone, user
from django.utils import timezone
import logging
from django.test.utils import override_settings
from apiCrm.serializers import BillChargeSerializer
from django.core.cache import cache

logger = logging.getLogger(__name__)

@override_settings(USE_TZ=False)  # Disable timezone support for tests
class BillChargesViewTest(TestCase):
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
        self.bill_charges_url = reverse('bill-charges')
        
        # Create test bill charges
        self.bill_charge1 = BillCharge.objects.create(
            quote_id="123",
            customer_id="",
            customer_name="Test Customer 1",
            customer_taxvat="111.222.333-44",
            customer_email="test1@example.com",
            store_name="Test Store 1",
            total_amount=100.00,
            installments=1,
            paid_at=timezone.now(),
            due_at=timezone.now(),
            is_paid=True,
            payment_method="Credit Card",
            status="Paid",
            quote_items="Item 1;Item 2"
        )
        self.bill_charge2 = BillCharge.objects.create(
            quote_id="456",
            customer_id="",
            customer_name="Test Customer 2",
            customer_taxvat="555.666.777-88",
            customer_email="test2@example.com",
            store_name="Test Store 2",
            total_amount=200.00,
            installments=2,
            paid_at=timezone.now(),
            due_at=timezone.now(),
            is_paid=False,
            payment_method="Credit Card",
            status="Pending",
            quote_items="Item 3;Item 4"
        )
        
        # Verify bill charges were created
        logger.info(f"Created bill charges: {BillCharge.objects.count()}")
        for bill_charge in BillCharge.objects.all():
            logger.info(f"Bill Charge: {bill_charge.quote_id} - {bill_charge.customer_name}")

    def test_get_all_bill_charges(self):
        """Test retrieving all bill charges"""
        # Verify bill charges exist before making request
        self.assertEqual(BillCharge.objects.count(), 2)
        
        response = self.client.get(self.bill_charges_url)
        bill_charges = BillCharge.objects.all()
        serializer = BillChargeSerializer(bill_charges, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Compare all fields except timestamps
        response_data = response.data[0]
        serializer_data = serializer.data[0]
        
        for key in response_data:
            if key not in ['paid_at', 'due_at']:
                self.assertEqual(response_data[key], serializer_data[key])
        
        self.assertEqual(len(response.data), 2)

    def test_get_bill_charges_check_content(self):
        """Test the content of retrieved bill charges"""
        response = self.client.get(self.bill_charges_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['quote_id'], "123")
        self.assertEqual(response.data[0]['customer_name'], "Test Customer 1")
        self.assertEqual(response.data[0]['store_name'], "Test Store 1")
        self.assertEqual(response.data[0]['total_amount'], "100.00")
        self.assertEqual(response.data[0]['is_paid'], True)

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
        
        response = self.client.put(self.bill_charges_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        response = self.client.delete(self.bill_charges_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_bill_charges_url_exists(self):
        """Test that the bill charges URL exists"""
        response = self.client.get(self.bill_charges_url)
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bill_charges_date_format(self):
        """Test that bill charge dates are properly formatted"""
        response = self.client.get(self.bill_charges_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that dates are in ISO format
        bill_charge = response.data[0]
        self.assertIn('paid_at', bill_charge)
        self.assertIn('due_at', bill_charge)
        
        # Verify date format (should be ISO format)
        self.assertRegex(bill_charge['paid_at'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')
        self.assertRegex(bill_charge['due_at'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')

    def test_bill_charges_value_format(self):
        """Test that bill charge values are properly formatted"""
        response = self.client.get(self.bill_charges_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that values are properly formatted as decimal numbers
        bill_charge = response.data[0]
        self.assertEqual(bill_charge['total_amount'], "100.00")
