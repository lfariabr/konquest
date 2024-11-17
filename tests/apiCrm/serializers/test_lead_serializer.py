from django.test import TestCase
from django.utils import timezone
from apiCrm.models.lead import Lead
from apiCrm.serializers import LeadSerializer

class LeadSerializerTest(TestCase):
    def setUp(self):
        self.lead_attributes = {
            'id_crm': '123',
            'name': 'Test Lead',
            'phone': '11987654321',
            'store': 'Test Store',
            'status': 'Active',
            'created_at': timezone.now()
        }
        
        self.lead = Lead.objects.create(**self.lead_attributes)
        self.serializer = LeadSerializer(instance=self.lead)

    def test_contains_expected_fields(self):
        """Test that serializer contains all expected fields"""
        data = self.serializer.data
        self.assertEqual(set(data.keys()), {
            'id',
            'id_crm',
            'name',
            'email',
            'phone',
            'source',
            'store',
            'status',
            'customer_id',
            'created_at',
            'utm_medium',
            'utm_campaign',
            'utm_content',
            'utm_search',
            'utm_term',
            'message'
        })

    def test_field_content(self):
        """Test that serializer data matches model instance"""
        data = self.serializer.data
        self.assertEqual(data['id_crm'], self.lead_attributes['id_crm'])
        self.assertEqual(data['name'], self.lead_attributes['name'])
        self.assertEqual(data['phone'], self.lead_attributes['phone'])
        self.assertEqual(data['store'], self.lead_attributes['store'])
        self.assertEqual(data['status'], self.lead_attributes['status'])

    def test_serializer_validation(self):
        """Test serializer validation"""
        # Test valid data
        valid_data = {
            'id_crm': '456',
            'name': 'New Lead',
            'email': 'test@example.com',
            'phone': '11987654322',
            'source': 'Test Source',
            'store': 'Another Store',
            'status': 'Inactive',
            'created_at': timezone.now()
        }
        serializer = LeadSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

        # Test invalid data (missing required fields)
        invalid_data = {
            'name': 'Invalid Lead'
        }
        serializer = LeadSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('id_crm', serializer.errors)

    def test_create_lead_with_serializer(self):
        """Test creating a lead using serializer"""
        new_lead_data = {
            'id_crm': '789',
            'name': 'Created Lead',
            'email': 'created@example.com',
            'phone': '11987654323',
            'source': 'Test Source',
            'store': 'New Store',
            'status': 'Active',
            'created_at': timezone.now()
        }
        
        serializer = LeadSerializer(data=new_lead_data)
        self.assertTrue(serializer.is_valid())
        lead = serializer.save()
        
        self.assertEqual(lead.id_crm, new_lead_data['id_crm'])
        self.assertEqual(lead.name, new_lead_data['name'])
        self.assertEqual(lead.phone, new_lead_data['phone'])
        self.assertEqual(lead.store, new_lead_data['store'])
        self.assertEqual(lead.status, new_lead_data['status'])

    def test_update_lead_with_serializer(self):
        """Test updating a lead using serializer"""
        updated_data = {
            'id_crm': '123',
            'name': 'Updated Lead',
            'phone': '11987654324',
            'store': 'Updated Store',
            'status': 'Inactive'
        }
        
        serializer = LeadSerializer(instance=self.lead, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_lead = serializer.save()
        
        self.assertEqual(updated_lead.name, updated_data['name'])
        self.assertEqual(updated_lead.phone, updated_data['phone'])
        self.assertEqual(updated_lead.store, updated_data['store'])
        self.assertEqual(updated_lead.status, updated_data['status'])
