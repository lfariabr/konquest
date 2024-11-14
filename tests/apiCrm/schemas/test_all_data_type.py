import pytest
import graphene
from apiCrm.schemas.all_data_type import AllDataType
from apiCrm.schemas.lead_type import LeadType
from apiCrm.schemas.appointment_type import AppointmentType
from apiCrm.schemas.bill_charges_type import BillChargeType
from apiCrm.schemas.resolve_all_data import Query, schema
from graphene.test import Client


def test_all_data_type_schema():
    assert issubclass(LeadType, graphene.ObjectType), "LeadType should be a graphene.ObjectType"
    assert issubclass(AppointmentType, graphene.ObjectType), "AppointmentType should be a graphene.ObjectType"
    assert issubclass(BillChargeType, graphene.ObjectType), "BillChargeType should be a graphene.ObjectType"

    schema = graphene.Schema(query=Query)
    introspection_query = '''
    {
        __schema {
            types {
                name
                kind
                fields {
                    name
                    type {
                        name
                        ofType {
                            name
                        }
                    }
                }
            }
        }
    }
    '''
    # Test execution and checking output
    result = schema.execute(introspection_query)
    if result.errors:
        print(result.errors)  # Log errors to understand if the schema has issues
    types = {type['name']: type for type in result.data['__schema']['types'] if type['name'] == 'AllDataType'}
    print(types)  # Log the output to understand what is being registered

    all_data_type = next((t for t in result.data['__schema']['types'] if t['name'] == 'AllDataType'), None)
    assert all_data_type, "AllDataType should be defined in the schema"
    fields = {field['name']: field['type']['name'] or field['type']['ofType']['name'] for field in all_data_type['fields']}
    
    assert 'leads' in fields and fields['leads'] == 'LeadType', "Leads field must be of type LeadType"
    assert 'appointments' in fields and fields['appointments'] == 'AppointmentType', "Appointments field must be of type AppointmentType"
    assert 'billCharges' in fields and fields['billCharges'] == 'BillChargeType', "BillCharges field must be of type BillChargeType"

def test_all_data_type_error_handling():
    schema = graphene.Schema(query=Query)
    erroneous_query = '''
    {
        allData {
            leads {
                id
                name
                unknownField
            }
        }
    }
    '''
    result = schema.execute(erroneous_query)
    assert result.errors, "Query with erroneous fields should return errors"
    assert 'unknownField' in str(result.errors[0]), "Error message should mention the erroneous field"