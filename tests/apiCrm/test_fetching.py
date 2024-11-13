import pytest
from apiCrm.resolvers import fetch_all_appointments, fetch_all_leads, fetch_bill_charges, fetch_all_data
import aiohttp
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_fetch_all_appointments(mocker):
    # Mock response to simulate a successful API call
    mock_response = {
        'data': {
            'fetchAppointments': {
                'data': [
                    {
                        'id': '2732057',
                        'status': {'label': 'Agendado'},
                        'createdBy': {'name': 'Test User', 'createdAt': '2024-01-02T11:05:30'},
                        'store': {'name': 'MOEMA'},
                        'customer': {'id': 12345, 'name': 'Customer Name'},
                        'procedure': {'name': 'Procedure', 'groupLabel': 'Label'},
                        'employee': {'name': 'Employee Name'},
                        'startDate': '2024-12-24T19:00:00'
                    }
                ],
                'meta': {
                    'currentPage': 1,
                    'lastPage': 1
                }
            }
        }
    }
    # Mock fetch_graphql directly to return the expected data structure
    mocker.patch('apiCrm.resolvers.fetch_graphql', return_value=mock_response)

    # Call the function and assert the results
    appointments = await fetch_all_appointments('session','2024-01-01', '2024-01-02', 'dummy_token')
    assert len(appointments) > 0 
    assert appointments[0]['id'] == '2732057'
    #TODO: match exact lenght of mock response
    #TODO: [0] structure is ok


@pytest.mark.asyncio
async def test_fetch_all_leads(mocker):
    # Mock response to simulate a successful API call
    mock_response = {
        'data': {
            'fetchLeads': {
                'data': [
                    {
                        'createdAt': '2024-01-01T10:00:00',
                        'id': '123',
                        'source': {'title': 'Google Ads'},
                        'store': {'name': 'Downtown Store'},
                        'status': {'label': 'New'},
                        'customer': {'id': 456, 'name': 'John Doe'},
                        'name': 'Lead Name',
                        'telephone': '123-456-7890',
                        'email': 'lead@example.com',
                        'message': 'Interested in product',
                        'utmMedium': 'cpc',
                        'utmContent': 'ad_content',
                        'utmCampaign': 'ad_campaign',
                        'utmSearch': 'search_term',
                        'utmTerm': 'keyword',
                    }
                ],
                'meta': {
                    'currentPage': 1,
                    'lastPage': 1
                }
            }
        }
    }
    mocker.patch('apiCrm.resolvers.fetch_graphql', return_value=mock_response)

    # Call the function and assert the results
    leads = await fetch_all_leads('session', '2024-01-01', '2024-01-02', 'dummy_token')
    assert len(leads) > 0
    assert leads[0]['id'] == '123'
    assert leads[0]['source']['title'] == 'Google Ads'

@pytest.mark.asyncio
async def test_fetch_bill_charges(mocker):
    # Mock session and response data for the test
    session = aiohttp.ClientSession()
    start_date = '2024-11-01'
    end_date = '2024-11-10'
    token = 'test_token'

    # Mock response structure for the GraphQL query
    mock_response_data = {
        'data': {
            'fetchBillCharges': {
                'data': [
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
                                    {'amount': 50.0, 'description': 'Service A', 'quantity': 1},
                                    {'amount': 50.0, 'description': 'Service B', 'quantity': 1}
                                ]
                            }
                        },
                        'store': {'name': 'Main Store'},
                        'amount': 100.0,
                        'paidAt': '2024-11-01T00:00:00Z',
                        'dueAt': '2024-11-10T00:00:00Z',
                        'isPaid': True,
                        'paymentMethod': {'name': 'Credit Card'}
                    }
                ],
                'meta': {
                    'currentPage': 1,
                    'lastPage': 1
                }
            }
        }
    }

    # Patch fetch_graphql to return the mock response data
    mocker.patch('apiCrm.resolvers.fetch_graphql', return_value=mock_response_data)

    # Run the function and check the results
    result = await fetch_bill_charges(session, start_date, end_date, token)
    await session.close()  # Close the session

    # Assertions to verify the results
    assert len(result) == 1
    assert result[0]['quote']['id'] == 'quote1'
    assert result[0]['amount'] == 100.0
    assert result[0]['isPaid'] is True
    assert result[0]['paymentMethod']['name'] == 'Credit Card'
    assert result[0]['quote']['bill']['items'][0]['description'] == 'Service A'
    assert result[0]['quote']['customer']['email'] == 'customer1@example.com'


@pytest.mark.asyncio
async def test_fetch_all_data(mocker):
    # Define the mock data for leads, appointments, and bill charges
    mock_leads_data = [{'id': '1', 'name': 'John Doe'}]
    mock_appointments_data = [{'id': '2', 'name': 'Jane Smith'}]
    mock_bill_charges_data = [{'id': '3', 'amount': 100}]

    # Mock fetch_all_leads, fetch_all_appointments, and fetch_bill_charges
    mocker.patch('apiCrm.resolvers.fetch_all_leads', new_callable=AsyncMock, return_value=mock_leads_data)
    mocker.patch('apiCrm.resolvers.fetch_all_appointments', new_callable=AsyncMock, return_value=mock_appointments_data)
    mocker.patch('apiCrm.resolvers.fetch_bill_charges', new_callable=AsyncMock, return_value=mock_bill_charges_data)

    # Call the main fetching function
    start_date = '2024-01-01'
    end_date = '2024-01-02'
    extended_end_date = '2024-01-03'
    token = 'test_token'
    leads, appointments, bill_charges = await fetch_all_data(start_date, end_date, extended_end_date, token)

    # Assertions to verify that the returned data is as expected
    assert leads == mock_leads_data
    assert appointments == mock_appointments_data
    assert bill_charges == mock_bill_charges_data
    assert len(leads) == 1
    assert len(appointments) == 1
    assert len(bill_charges) == 1