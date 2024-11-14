import pytest
from graphene.test import Client
from apiCrm.schemas.resolve_all_data import schema  # Assuming the schema is defined and includes AppointmentType

def test_lead_type_fields():
    client = Client(schema)
    executed = client.execute('''
    {
      __type(name: "LeadType") {
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
    
    expected_fields = {
    'id': 'ID',
    'idCrm': 'String',
    'name': 'String',
    'email': 'String',
    'phone': 'String',
    'source': 'String',
    'store': 'String',
    'status': 'String',
    'customerId': 'String',  # Adjusted from 'customer_id' to 'customerId'
    'createdAt': 'DateTime',
    
    # Optional fields
    'utmMedium': 'String',
    'utmCampaign': 'String',
    'utmContent': 'String',
    'utmSearch': 'String',
    'utmTerm': 'String',
    'message': 'String'
}

    for field_name, field_type in expected_fields.items():
        assert field_name in fields, f"Field {field_name} missing in LeadType"
        
        assert fields[field_name]['name'] == field_type or (fields[field_name]['ofType'] and fields[field_name]['ofType']['name'] == field_type), f"Field {field_name} does not match expected type {field_type}"