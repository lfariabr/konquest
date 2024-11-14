import pytest
from graphene.test import Client
from apiCrm.schemas.resolve_all_data import schema  # Assuming the schema is defined and includes AppointmentType

def test_appointment_type_fields():
    client = Client(schema)
    executed = client.execute('''
    {
      __type(name: "AppointmentType") {
        name
        fields {
          name
          type {
            name
            kind
            ofType {
              name
              kind
            }
          }
        }
      }
    }
    ''')
    fields = {field['name']: field['type'] for field in executed['data']['__type']['fields']}
    
    # Checking for both direct fields from the model and the additional fields in AppointmentType
    expected_fields = {
        'id': 'ID',
        'idCrm': 'String',
        'statusLabel': 'String',
        'storeName': 'String',
        'customerId': 'String',
        'customerName': 'String',
        'customerPhone': 'String',
        'procedureName': 'String',
        'procedureGroup': 'String',
        'employeeName': 'String',
        'createdbyName': 'String',
        'createdbyCreatedAt': 'DateTime',
        'appointmentDate': 'DateTime',
    }
    
    for field_name, field_type in expected_fields.items():
        assert field_name in fields, f"Field {field_name} missing in AppointmentType"
        assert fields[field_name]['name'] == field_type or (fields[field_name]['ofType'] and fields[field_name]['ofType']['name'] == field_type), f"Field {field_name} does not match expected type {field_type}"