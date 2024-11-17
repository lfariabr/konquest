from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apiCrm.models.billcharge import BillCharge
from apiCrm.serializers import BillChargeSerializer
from django.utils import timezone

class BillChargesViewTest(TestCase):
    def setUp(self):
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

    def test_get_all_bill_charges(self):
        """Test retrieving all bill charges"""
        response = self.client.get(self.bill_charges_url)
        bill_charges = BillCharge.objects.all()
        serializer = BillChargeSerializer(bill_charges, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(len(response.data), 2)

    def test_get_bill_charges_check_content(self):
        """Test the content of retrieved bill charges"""
        response = self.client.get(self.bill_charges_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['quote_id'], "123")
        self.assertEqual(response.data[0]['status'], "Paid")
        self.assertEqual(response.data[0]['store_name'], "Test Store 1")
        self.assertEqual(response.data[0]['customer_name'], "Test Customer 1")
        self.assertEqual(response.data[0]['customer_email'], "test1@example.com")
        self.assertEqual(float(response.data[0]['total_amount']), 100.00)

    def test_get_bill_charges_no_charges(self):
        """Test retrieving bill charges when none exist"""
        BillCharge.objects.all().delete()
        response = self.client.get(self.bill_charges_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_bill_charges_url_exists(self):
        """Test that the bill charges URL exists and resolves"""
        response = self.client.get(self.bill_charges_url)
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bill_charges_only_allows_get(self):
        """Test that only GET method is allowed"""
        response_post = self.client.post(self.bill_charges_url, {})
        response_put = self.client.put(self.bill_charges_url, {})
        response_delete = self.client.delete(self.bill_charges_url)
        
        self.assertEqual(response_post.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_delete.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_bill_charges_date_format(self):
        """Test that bill charge dates are properly formatted"""
        response = self.client.get(self.bill_charges_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that dates are in ISO format
        bill_charge = response.data[0]
        self.assertRegex(bill_charge['paid_at'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')
        self.assertRegex(bill_charge['due_at'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')

    def test_bill_charges_value_format(self):
        """Test that bill charge values are properly formatted"""
        response = self.client.get(self.bill_charges_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that values are properly formatted as decimal numbers
        bill_charge = response.data[0]
        self.assertEqual(float(bill_charge['total_amount']), 100.00)
