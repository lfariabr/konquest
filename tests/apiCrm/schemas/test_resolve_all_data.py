# tests/apiCrm/schemas/test_resolve_all_data.py
import pytest
from unittest.mock import patch, MagicMock
from graphene.test import Client
from apiCrm.schemas.resolve_all_data import schema
from apiCrm.models.appointment import Appointment
from apiCrm.models.billcharge import BillCharge
from apiCrm.models.lead import Lead
from datetime import datetime

@pytest.fixture
def mock_data():
    return {
        'leads': [
            {
                'id_crm': 'lead1',
                'name': 'Test Lead',
                'email': 'test@example.com',
                'phone': '1234567890',
                'source': 'Test Source',
                'store': 'Test Store',
                'status': 'Active',
                'created_at': '2024-01-01T00:00:00Z'
            }
        ],
        'appointments': [
            {
                'id_crm': 'appointment1',
                'status_label': 'Scheduled',
                'store_name': 'Test Store',
                'customer_id': '',
                'customer_name': 'Test Customer',
                'customer_phone': '1234567890',
                'procedure_name': 'Test Procedure',
                'procedure_group': 'Test Group',
                'employee_name': 'Test Employee',
                'createdby_name': 'Test Creator',
                'createdby_created_at': '2024-01-01T00:00:00Z',
                'appointment_date': '2024-01-01T00:00:00Z'
            }
        ],
        'bill_charges': [
            {
                'quote_id': 'bill1',
                'customer_id': '',
                'customer_name': 'Test Customer',
                'customer_taxvat': '123.456.789-00',
                'customer_email': 'test@example.com',
                'store_name': 'Test Store',
                'total_amount': 100.00,
                'installments': 1,
                'paid_at': '2024-01-01T00:00:00Z',
                'due_at': '2024-01-01T00:00:00Z',
                'is_paid': True,
                'payment_method': 'Credit Card',
                'status': 'Paid',
                'quote_items': 'Item 1;Item 2'
            }
        ]
    }

@pytest.mark.django_db
def test_resolve_all_data_success(mock_data):
    """Test successful resolution of all data types with mocked data"""
    with patch('apiCrm.schemas.resolve_all_data.fetch_data') as mock_fetch_data, \
         patch('apiCrm.schemas.resolve_all_data.process_leads') as mock_process_leads, \
         patch('apiCrm.schemas.resolve_all_data.process_appointments') as mock_process_appointments, \
         patch('apiCrm.schemas.resolve_all_data.process_bill_charges') as mock_process_bill_charges:

        # Mock fetch_data to return our test data
        mock_fetch_data.return_value = (
            mock_data['leads'],
            mock_data['appointments'],
            mock_data['bill_charges']
        )

        # Create model instances from mock data
        lead = Lead.objects.create(**mock_data['leads'][0])
        appointment = Appointment.objects.create(**mock_data['appointments'][0])
        bill_charge = BillCharge.objects.create(**mock_data['bill_charges'][0])

        # Mock process functions to return our model instances
        mock_process_leads.return_value = [lead]
        mock_process_appointments.return_value = [appointment]
        mock_process_bill_charges.return_value = [bill_charge]

        client = Client(schema)
        query = '''
        query($startDate: String!, $endDate: String!, $extendedEndDate: String!) {
            allData(startDate: $startDate, endDate: $endDate, extendedEndDate: $extendedEndDate) {
                leads {
                    idCrm
                    name
                    email
                    phone
                    source
                    store
                    status
                }
                appointments {
                    idCrm
                    statusLabel
                    storeName
                    customerName
                    customerPhone
                    procedureName
                    procedureGroup
                    employeeName
                }
                billCharges {
                    quoteId
                    customerName
                    customerEmail
                    storeName
                    totalAmount
                    installments
                    isPaid
                    paymentMethod
                    status
                }
            }
        }
        '''

        variables = {
            'startDate': '2024-01-01',
            'endDate': '2024-01-02',
            'extendedEndDate': '2024-01-03'
        }

        result = client.execute(query, variables=variables)

        assert 'errors' not in result
        assert result['data']['allData']['leads'][0]['idCrm'] == 'lead1'
        assert result['data']['allData']['appointments'][0]['idCrm'] == 'appointment1'
        assert result['data']['allData']['billCharges'][0]['quoteId'] == 'bill1'

@pytest.mark.django_db
def test_resolve_all_data_empty_response():
    """Test handling of empty data with mocked responses"""
    with patch('apiCrm.schemas.resolve_all_data.fetch_data') as mock_fetch_data, \
         patch('apiCrm.schemas.resolve_all_data.process_leads') as mock_process_leads, \
         patch('apiCrm.schemas.resolve_all_data.process_appointments') as mock_process_appointments, \
         patch('apiCrm.schemas.resolve_all_data.process_bill_charges') as mock_process_bill_charges:

        # Mock all functions to return empty lists
        mock_fetch_data.return_value = ([], [], [])
        mock_process_leads.return_value = []
        mock_process_appointments.return_value = []
        mock_process_bill_charges.return_value = []

        client = Client(schema)
        query = '''
        query($startDate: String!, $endDate: String!, $extendedEndDate: String!) {
            allData(startDate: $startDate, endDate: $endDate, extendedEndDate: $extendedEndDate) {
                leads {
                    idCrm
                }
                appointments {
                    idCrm
                }
                billCharges {
                    quoteId
                }
            }
        }
        '''

        variables = {
            'startDate': '2024-01-01',
            'endDate': '2024-01-02',
            'extendedEndDate': '2024-01-03'
        }

        result = client.execute(query, variables=variables)

        assert 'errors' not in result
        assert len(result['data']['allData']['leads']) == 0
        assert len(result['data']['allData']['appointments']) == 0
        assert len(result['data']['allData']['billCharges']) == 0

@pytest.mark.django_db
def test_resolve_all_data_invalid_dates():
    """Test handling of invalid date inputs with mocked responses"""
    with patch('apiCrm.schemas.resolve_all_data.fetch_data') as mock_fetch_data:
        mock_fetch_data.side_effect = ValueError("Invalid date format")

        client = Client(schema)
        query = '''
        query($startDate: String!, $endDate: String!, $extendedEndDate: String!) {
            allData(startDate: $startDate, endDate: $endDate, extendedEndDate: $extendedEndDate) {
                leads {
                    idCrm
                }
            }
        }
        '''

        variables = {
            'startDate': 'invalid-date',
            'endDate': '2024-01-02',
            'extendedEndDate': '2024-01-03'
        }

        result = client.execute(query, variables=variables)
        assert 'errors' in result

@pytest.mark.django_db
def test_resolve_all_data_processing_error():
    """Test handling of data processing errors with mocked responses"""
    with patch('apiCrm.schemas.resolve_all_data.fetch_data') as mock_fetch_data, \
         patch('apiCrm.schemas.resolve_all_data.process_leads') as mock_process_leads:

        mock_fetch_data.return_value = ([{'invalid': 'data'}], [], [])
        mock_process_leads.side_effect = ValueError("Invalid data format")

        client = Client(schema)
        query = '''
        query($startDate: String!, $endDate: String!, $extendedEndDate: String!) {
            allData(startDate: $startDate, endDate: $endDate, extendedEndDate: $extendedEndDate) {
                leads {
                    idCrm
                }
            }
        }
        '''

        variables = {
            'startDate': '2024-01-01',
            'endDate': '2024-01-02',
            'extendedEndDate': '2024-01-03'
        }

        result = client.execute(query, variables=variables)
        assert 'errors' in result