import pytest
from graphene.test import Client
from apiCrm.schema import schema
from apiCrm.schema import LeadType, AppointmentType, BillChargeType
from datetime import datetime

@pytest.mark.django_db
def test_query_leads(mocker):
    # Define mock data with `createdAt` as a `datetime` object
    mock_leads_data = [
        {
            'id': 'test123',
            'name': 'Test Lead',
            'email': 'lead@example.com',
            'telephone': '1234567890',
            'source': {'title': 'Google'},
            'store': {'name': 'Online'},
            'status': {'label': 'new'},
            'createdAt': datetime(2024, 11, 9, 0, 17, 6),  # Mocked as a datetime object
            'customer': {'id': 'cust001'},
            'utmMedium': 'social',
            'utmCampaign': 'campaign1',
            'utmContent': 'content1',
            'utmSearch': 'search1',
            'utmTerm': 'term1',
            'message': 'Test message'
        }
    ]

    # Mock fetch_all_leads to return the mock_leads_data
    mocker.patch("apiCrm.schema.fetch_all_leads", return_value=mock_leads_data)

    # Expected formatted data for the LeadType response
    expected_leads_data = [
        LeadType(
            id_crm="test123",
            name="Test Lead",
            email="lead@example.com",
            phone="1234567890",
            source="Google",
            store="Online",
            status="new",
            created_at=datetime(2024, 11, 9, 0, 17, 6),  # Match the datetime format
            customer_id="cust001",
            utm_medium="social",
            utm_campaign="campaign1",
            utm_content="content1",
            utm_search="search1",
            utm_term="term1",
            message="Test message"
        )
    ]

    # Patch resolve_leads to use the formatted mock data without saving to the database
    mocker.patch("apiCrm.schema.Query.resolve_leads", return_value=expected_leads_data)

    client = Client(schema)
    response = client.execute(
        """
        query($startDate: String!, $endDate: String!) {
            leads(startDate: $startDate, endDate: $endDate) {
                idCrm
                name
                email
                phone
                source
                store
                status
                createdAt
                customerId
                utmMedium
                utmCampaign
                utmContent
                utmSearch
                utmTerm
                message
            }
        }
        """,
        variables={"startDate": "2024-11-09", "endDate": "2024-11-09"}
    )

    print("Response:", response)  # To verify the response format
    assert "errors" not in response  # Ensure no errors in the response
    assert response["data"]["leads"]  # Ensure data exists
    assert response["data"]["leads"][0]["idCrm"] == "test123"  # Validate a specific field

@pytest.mark.django_db
def test_query_appointments(mocker):
    # Define mock data with Django model field names and add an `id` to match GraphQL's requirement
    mock_appointments_data = [
        {
            'id_crm': 'apt123',
            'id': 'apt123',  # Explicitly include `id` as `id_crm`
            'status_label': 'Confirmed',
            'store_name': 'Main Branch',
            'customer_id': 'cust001',
            'customer_name': 'Customer Name',
            'customer_phone': '1234567890',
            'procedure_name': 'Massage',
            'procedure_group': 'Wellness',
            'employee_name': 'Therapist Name',
            'createdby_name': 'Staff Member',
            'createdby_created_at': datetime(2024, 1, 1, 0, 0, 0).isoformat(),
            'appointment_date': datetime(2024, 11, 9, 10, 0, 0).isoformat()
        }
    ]
    
    # Mock fetch_all_appointments to return the mock data
    mocker.patch("apiCrm.schema.fetch_all_appointments", return_value=mock_appointments_data)
    
    # Expected data for AppointmentType with `id` to satisfy GraphQL's default expectations
    mock_appointment_instances = [
        AppointmentType(
            id="apt123",  # Explicit `id` to satisfy GraphQL
            id_crm="apt123",
            status_label="Confirmed",
            store_name="Main Branch",
            customer_id="cust001",
            customer_name="Customer Name",
            customer_phone="1234567890",
            procedure_name="Massage",
            procedure_group="Wellness",
            employee_name="Therapist Name",
            createdby_name="Staff Member",
            createdby_created_at="2024-01-01T00:00:00",
            appointment_date="2024-11-09T10:00:00"
        )
    ]
    
    # Patch resolve_appointments to use the formatted mock data
    mocker.patch("apiCrm.schema.Query.resolve_appointments", return_value=mock_appointment_instances)
    
    # Test GraphQL query
    client = Client(schema)
    response = client.execute(
        """
        query($startDate: String!, $endDate: String!) {
            appointments(startDate: $startDate, endDate: $endDate) {
                id  # Ensure `id` is included here
                idCrm
                statusLabel
                storeName
                customerId
                customerName
                customerPhone
                procedureName
                procedureGroup
                employeeName
                createdbyName
                createdbyCreatedAt
                appointmentDate
            }
        }
        """,
        variables={"startDate": "2024-11-09", "endDate": "2024-11-09"}
    )

    print("Response:", response)  # To verify the response format
    assert "errors" not in response, f"Unexpected errors in response: {response['errors']}"
    assert response["data"]["appointments"] is not None
    assert response["data"]["appointments"][0]["idCrm"] == "apt123"

@pytest.mark.django_db
def test_query_bill_charges(mocker):
    # Define mock data
    mock_bill_charges_data = [
        {
            'quote': {
                'id': 'quote1',
                'customer': {
                    'id': 'cust1',
                    'name': 'Customer One',
                    'taxvat': '123456789',
                    'email': 'customer1@example.com'
                },
                'status': 'Completed',
                'bill': {
                    'total': 100.0,
                    'installmentsQuantity': 2,
                    'items': [
                        {'description': 'Service A', 'quantity': 1, 'amount': 50.0},
                        {'description': 'Service B', 'quantity': 1, 'amount': 50.0}
                    ]
                }
            },
            'store': {'name': 'Main Store'},
            'amount': 100.0,
            'paidAt': '2024-11-01T00:00:00',
            'dueAt': '2024-11-10T00:00:00',
            'isPaid': True,
            'paymentMethod': {'name': 'Credit Card'}
        }
    ]

    # Patch fetch_bill_charges where it's imported in schema.py
    mocker.patch('apiCrm.schema.fetch_bill_charges', return_value=mock_bill_charges_data)

    client = Client(schema)
    response = client.execute(
        """
        query($startDate: String!, $endDate: String!) {
            billCharges(startDate: $startDate, endDate: $endDate) {
                id
                quoteId
                customerId
                customerName
                customerTaxvat
                customerEmail
                storeName
                totalAmount
                installments
                paidAt
                dueAt
                isPaid
                paymentMethod
                status
                quoteItems
            }
        }
        """,
        variables={"startDate": "2024-11-08", "endDate": "2024-11-08"}
    )

    # Verify that response matches the mock data
    assert "errors" not in response, f"Unexpected errors in response: {response['errors']}"
    assert response["data"]["billCharges"][0]["quoteId"] == "quote1"
    assert response["data"]["billCharges"][0]["customerEmail"] == "customer1@example.com"
    assert response["data"]["billCharges"][0]["id"] == "quote1"