import pytest
from graphene.test import Client
from apiCrm.schemas.resolve_all_data import schema  # Assuming the schema is defined and includes AppointmentType

def test_bill_charges_type_fields():
    client = Client(schema)
    executed = client.execute('''
    {
      __type(name: "BillChargeType") {
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
        'id': 'String',
        'quoteId': 'String',
        'customerId': 'String',
        'customerName': 'String',
        'customerTaxvat': 'String',
        'customerEmail': 'String',
        'storeName': 'String',
        'totalAmount': 'Float',
        'installments': 'Int',
        'paidAt': 'String',
        'dueAt': 'String',
        'isPaid': 'Boolean',
        'paymentMethod': 'String',
        'status': 'String',
        'quoteItems': 'String',
    }
    
    for field_name, field_type in expected_fields.items():
        assert field_name in fields, f"Field '{field_name}' not found in BillChargeType"
        assert fields[field_name]['name'] == field_type

def test_security_restrictions():
    client = Client(schema, context_value={'user_role': 'guest'})
    executed = client.execute('''
    query GetSensitiveData {
      billCharges {
        customerTaxvat
      }
    }
    ''')
    assert 'errors' in executed, "Unauthorized access to sensitive fields should result in an error"
    assert 'customerTaxvat' not in executed.get('data', {}), "Sensitive data should not be exposed to unauthorized roles"

def test_bill_charge_type_nested_fields():
    client = Client(schema)
    executed = client.execute('''
    {
      __type(name: "BillChargeType") {
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
    
    # Check if the query was successful and the data is present
    if 'data' not in executed or '__type' not in executed['data'] or 'fields' not in executed['data']['__type']:
        print("Query failed or returned unexpected data structure:", executed)
        assert False, "Failed to fetch data or incorrect data structure returned"
    
    fields = {field['name']: field['type'] for field in executed['data']['__type']['fields']}

    # Checking for both direct fields from the model and the additional fields in BillChargeType
    expected_fields = {
        'id': 'String',  # Make sure this and other expected types align with what is actually defined in your schema
        'quoteId': 'String',
        'customerId': 'String',
        'customerName': 'String',
        'customerTaxvat': 'String',
        'customerEmail': 'String',
        'storeName': 'String',
        'totalAmount': 'Float',
        'installments': 'Int',
        'paidAt': 'String',
        'dueAt': 'String',
        'isPaid': 'Boolean',
        'paymentMethod': 'String',
        'status': 'String',
        'quoteItems': 'String',
    }
    
    for field_name, field_type in expected_fields.items():
        assert field_name in fields, f"Field '{field_name}' not found in BillChargeType"
        assert fields[field_name]['name'] == field_type, f"Field {field_name} does not match expected type {field_type}"