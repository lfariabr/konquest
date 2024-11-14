# tests/apiCrm/schemas/test_resolve_all_data.py
import pytest
from unittest.mock import patch
from graphene.test import Client
from apiCrm.schemas.resolve_all_data import schema
from apiCrm.models.appointment import Appointment
from apiCrm.models.billcharge import BillCharge
from apiCrm.models.lead import Lead
from datetime import datetime

@pytest.mark.django_db
def test_resolve_all_data():
    # Mock run_fetch_all to avoid real HTTP requests
    with patch('apiCrm.schemas.resolve_all_data.run_fetch_all') as mock_run_fetch_all:
        mock_run_fetch_all.return_value = (
            [{'id': 'lead1'}],          # Mock leads data
            [{'id': 'appointment1'}],   # Mock appointments data
            [{'id': 'bill1'}]           # Mock bill charges data
        )

        # Mock processing functions to prevent actual processing
        with patch('apiCrm.schemas.resolve_all_data.process_leads') as mock_process_leads, \
             patch('apiCrm.schemas.resolve_all_data.process_appointments') as mock_process_appointments, \
             patch('apiCrm.schemas.resolve_all_data.process_bill_charges') as mock_process_bill_charges:

            # Create actual model instances in the test database
            lead_instance = Lead.objects.create(
                id_crm='lead1',
                name='Test Lead',
                email='test@example.com',   # Provide required fields
                phone='1234567890',
                source='Test Source',
                store='Test Store',
                status='Test Status',
                customer_id='cust123',
                created_at='2024-01-01T00:00:00Z',
                # Include other required fields as necessary
            )
            appointment_instance = Appointment.objects.create(
                id_crm='appointment1',
                status_label='Test Status',
                appointment_date='2024-01-01T00:00:00Z',
                createdby_created_at='2024-01-01T00:00:00Z',
                # Include other required fields as necessary
            )
            bill_charge_instance = BillCharge.objects.create(
                quote_id='bill1',
                total_amount=100.0,
                is_paid=True,
                # Include other required fields as necessary
            )

            # Set the mock return values
            mock_process_leads.return_value = [lead_instance]
            mock_process_appointments.return_value = [appointment_instance]
            mock_process_bill_charges.return_value = [bill_charge_instance]

            client = Client(schema)

            query = '''
            query($startDate: String!, $endDate: String!, $extendedEndDate: String!) {
                allData(startDate: $startDate, endDate: $endDate, extendedEndDate: $extendedEndDate) {
                    leads {
                        idCrm
                        name
                    }
                    appointments {
                        idCrm
                        statusLabel
                    }
                    billCharges {
                        quoteId
                        totalAmount
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

            # Assertions
            assert 'errors' not in result, f"Errors occurred: {result.get('errors')}"
            assert result['data']['allData']['leads'] == [{'idCrm': 'lead1', 'name': 'Test Lead'}]
            assert result['data']['allData']['appointments'] == [{'idCrm': 'appointment1', 'statusLabel': 'Test Status'}]
            assert result['data']['allData']['billCharges'] == [{'quoteId': 'bill1', 'totalAmount': 100.0}]