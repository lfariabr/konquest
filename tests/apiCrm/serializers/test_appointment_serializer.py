from django.test import TestCase
from django.utils import timezone
from apiCrm.models.appointment import Appointment
from apiCrm.serializers import AppointmentSerializer

class AppointmentSerializerTest(TestCase):
    def setUp(self):
        self.appointment_attributes = {
            'id_crm': '123',
            'status_label': 'Agendado',
            'store_name': 'Test Store',
            'customer_id': '',
            'customer_name': 'Test Customer',
            'customer_phone': '11987654321',
            'procedure_name': 'Test Procedure',
            'procedure_group': 'Test Group',
            'employee_name': 'Test Employee',
            'createdby_name': 'Test Creator',
            'createdby_created_at': timezone.now(),
            'appointment_date': timezone.now()
        }
        
        self.appointment = Appointment.objects.create(**self.appointment_attributes)
        self.serializer = AppointmentSerializer(instance=self.appointment)

    def test_contains_expected_fields(self):
        """Test that serializer contains all expected fields"""
        data = self.serializer.data
        self.assertEqual(set(data.keys()), {
            'id',
            'id_crm',
            'status_label',
            'store_name',
            'customer_id',
            'customer_name',
            'customer_phone',
            'procedure_name',
            'procedure_group',
            'employee_name',
            'createdby_name',
            'createdby_created_at',
            'appointment_date'
        })

    def test_field_content(self):
        """Test that serializer data matches model instance"""
        data = self.serializer.data
        self.assertEqual(data['id_crm'], self.appointment_attributes['id_crm'])
        self.assertEqual(data['status_label'], self.appointment_attributes['status_label'])
        self.assertEqual(data['store_name'], self.appointment_attributes['store_name'])
        self.assertEqual(data['customer_name'], self.appointment_attributes['customer_name'])
        self.assertEqual(data['customer_phone'], self.appointment_attributes['customer_phone'])
        self.assertEqual(data['procedure_name'], self.appointment_attributes['procedure_name'])
        self.assertEqual(data['employee_name'], self.appointment_attributes['employee_name'])

    def test_serializer_validation(self):
        """Test serializer validation"""
        # Test valid data
        valid_data = {
            'id_crm': '456',
            'status_label': 'Confirmado',
            'store_name': 'Another Store',
            'customer_id': '',
            'customer_name': 'New Customer',
            'customer_phone': '11987654322',
            'procedure_name': 'New Procedure',
            'procedure_group': 'New Group',
            'employee_name': 'New Employee',
            'createdby_name': 'New Creator',
            'createdby_created_at': timezone.now(),
            'appointment_date': timezone.now()
        }
        serializer = AppointmentSerializer(data=valid_data)
        if not serializer.is_valid():
            print("Validation errors:", serializer.errors)
        self.assertTrue(serializer.is_valid())

        # Test invalid data (missing required fields)
        invalid_data = {
            'customer_name': 'Invalid Appointment'
        }
        serializer = AppointmentSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('id_crm', serializer.errors)

    def test_create_appointment_with_serializer(self):
        """Test creating an appointment using serializer"""
        new_appointment_data = {
            'id_crm': '789',
            'status_label': 'Pendente',
            'store_name': 'New Store',
            'customer_id': '',
            'customer_name': 'Created Customer',
            'customer_phone': '11987654323',
            'procedure_name': 'Created Procedure',
            'procedure_group': 'Created Group',
            'employee_name': 'Created Employee',
            'createdby_name': 'Created Creator',
            'createdby_created_at': timezone.now(),
            'appointment_date': timezone.now()
        }
        
        serializer = AppointmentSerializer(data=new_appointment_data)
        self.assertTrue(serializer.is_valid())
        appointment = serializer.save()
        
        self.assertEqual(appointment.id_crm, new_appointment_data['id_crm'])
        self.assertEqual(appointment.status_label, new_appointment_data['status_label'])
        self.assertEqual(appointment.store_name, new_appointment_data['store_name'])
        self.assertEqual(appointment.customer_name, new_appointment_data['customer_name'])
        self.assertEqual(appointment.customer_phone, new_appointment_data['customer_phone'])

    def test_update_appointment_with_serializer(self):
        """Test updating an appointment using serializer"""
        updated_data = {
            'id_crm': '123',
            'status_label': 'Cancelado',
            'store_name': 'Updated Store',
            'customer_name': 'Updated Customer',
            'customer_phone': '11987654324',
            'procedure_name': 'Updated Procedure'
        }
        
        serializer = AppointmentSerializer(instance=self.appointment, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_appointment = serializer.save()
        
        self.assertEqual(updated_appointment.status_label, updated_data['status_label'])
        self.assertEqual(updated_appointment.store_name, updated_data['store_name'])
        self.assertEqual(updated_appointment.customer_name, updated_data['customer_name'])
        self.assertEqual(updated_appointment.customer_phone, updated_data['customer_phone'])
        self.assertEqual(updated_appointment.procedure_name, updated_data['procedure_name'])

    def test_date_field_formats(self):
        """Test that date fields are properly serialized"""
        data = self.serializer.data
        
        # Check that dates are in ISO format
        self.assertRegex(data['createdby_created_at'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')
        self.assertRegex(data['appointment_date'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')
