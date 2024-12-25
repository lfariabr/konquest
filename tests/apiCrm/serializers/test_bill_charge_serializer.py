from django.test import TestCase
from django.utils import timezone
from apiCrm.models.billcharge import BillCharge
from apiCrm.serializers import BillChargeSerializer

class BillChargeSerializerTest(TestCase):
    def setUp(self):
        self.bill_charge_attributes = {
            'quote_id': '123',
            'customer_id': '',
            'customer_name': 'Test Customer',
            'customer_taxvat': '123.456.789-00',
            'customer_email': 'test@example.com',
            'store_name': 'Test Store',
            'total_amount': 100.00,
            'installments': 1,
            'paid_at': timezone.now(),
            'due_at': timezone.now(),
            'is_paid': True,
            'payment_method': 'Credit Card',
            'status': 'Paid',
            'quote_items': 'Item 1;Item 2'
        }
        
        self.bill_charge = BillCharge.objects.create(**self.bill_charge_attributes)
        self.serializer = BillChargeSerializer(instance=self.bill_charge)

    def test_contains_expected_fields(self):
        """Test that serializer contains all expected fields"""
        data = self.serializer.data
        self.assertEqual(set(data.keys()), {
            'id',
            'quote_id',
            'customer_id',
            'customer_name',
            'customer_taxvat',
            'customer_email',
            'store_name',
            'total_amount',
            'installments',
            'paid_at',
            'due_at',
            'is_paid',
            'payment_method',
            'status',
            'quote_items',
            'customer_phone'
        })

    def test_field_content(self):
        """Test that serializer data matches model instance"""
        data = self.serializer.data
        self.assertEqual(data['quote_id'], self.bill_charge_attributes['quote_id'])
        self.assertEqual(data['customer_name'], self.bill_charge_attributes['customer_name'])
        self.assertEqual(data['store_name'], self.bill_charge_attributes['store_name'])
        self.assertEqual(float(data['total_amount']), self.bill_charge_attributes['total_amount'])
        self.assertEqual(data['status'], self.bill_charge_attributes['status'])

    def test_serializer_validation(self):
        """Test serializer validation"""
        # Test valid data
        valid_data = {
            'quote_id': '456',
            'customer_id': '',
            'customer_name': 'New Customer',
            'customer_taxvat': '987.654.321-00',
            'customer_email': 'new@example.com',
            'store_name': 'Another Store',
            'total_amount': 200.00,
            'installments': 2,
            'paid_at': timezone.now(),
            'due_at': timezone.now(),
            'is_paid': True,
            'payment_method': 'Credit Card',
            'status': 'Paid',
            'quote_items': 'Item 3;Item 4'
        }
        serializer = BillChargeSerializer(data=valid_data)
        if not serializer.is_valid():
            print("Validation errors:", serializer.errors)  
        self.assertTrue(serializer.is_valid())

        # Test invalid data (missing required fields)
        invalid_data = {
            'customer_name': 'Invalid Bill Charge'
        }
        serializer = BillChargeSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('quote_id', serializer.errors)

    def test_create_bill_charge_with_serializer(self):
        """Test creating a bill charge using serializer"""
        new_bill_charge_data = {
            'quote_id': '789',
            'customer_id': '',
            'customer_name': 'Created Customer',
            'customer_taxvat': '111.222.333-44',
            'customer_email': 'created@example.com',
            'store_name': 'New Store',
            'total_amount': 300.00,
            'installments': 3,
            'paid_at': timezone.now(),
            'due_at': timezone.now(),
            'is_paid': True,
            'payment_method': 'Credit Card',
            'status': 'Paid',
            'quote_items': 'Item 5;Item 6'
        }
        
        serializer = BillChargeSerializer(data=new_bill_charge_data)
        self.assertTrue(serializer.is_valid())
        bill_charge = serializer.save()
        
        self.assertEqual(bill_charge.quote_id, new_bill_charge_data['quote_id'])
        self.assertEqual(bill_charge.customer_name, new_bill_charge_data['customer_name'])
        self.assertEqual(bill_charge.store_name, new_bill_charge_data['store_name'])
        self.assertEqual(float(bill_charge.total_amount), new_bill_charge_data['total_amount'])
        self.assertEqual(bill_charge.status, new_bill_charge_data['status'])

    def test_update_bill_charge_with_serializer(self):
        """Test updating a bill charge using serializer"""
        updated_data = {
            'quote_id': '123',
            'customer_name': 'Updated Customer',
            'store_name': 'Updated Store',
            'total_amount': 150.00,
            'status': 'Cancelled'
        }
        
        serializer = BillChargeSerializer(instance=self.bill_charge, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_bill_charge = serializer.save()
        
        self.assertEqual(updated_bill_charge.customer_name, updated_data['customer_name'])
        self.assertEqual(updated_bill_charge.store_name, updated_data['store_name'])
        self.assertEqual(float(updated_bill_charge.total_amount), updated_data['total_amount'])
        self.assertEqual(updated_bill_charge.status, updated_data['status'])

    def test_value_field_format(self):
        """Test that value field is properly serialized"""
        data = self.serializer.data
        
        # Check that value is a valid decimal
        self.assertIsInstance(float(data['total_amount']), float)
        self.assertEqual(float(data['total_amount']), 100.00)

    def test_date_field_formats(self):
        """Test that date fields are properly serialized"""
        data = self.serializer.data
        
        # Check that dates are in ISO format
        self.assertRegex(data['paid_at'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')
        self.assertRegex(data['due_at'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')
