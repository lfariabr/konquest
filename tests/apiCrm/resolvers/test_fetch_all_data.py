# tests/apiCrm/resolvers/test_fetch_all_data.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp
from datetime import datetime

@pytest.fixture(autouse=True)
def mock_env_config():
    """Mock environment config to prevent real token loading"""
    with patch('decouple.config', return_value='test-token'), \
         patch('apiCrm.resolvers.fetch_graphql.config', return_value='test-token'), \
         patch('apiCrm.resolvers.fetch_all_leads.config', return_value='test-token'), \
         patch('apiCrm.resolvers.fetch_all_appointments.config', return_value='test-token'), \
         patch('apiCrm.resolvers.fetch_bill_charges.config', return_value='test-token'):
        yield

@pytest.fixture
def mock_response():
    mock = AsyncMock()
    mock.status = 200
    mock.json.return_value = {'data': {'fetchData': {'data': [], 'meta': {'currentPage': 1, 'lastPage': 1}}}}
    return mock

@pytest.fixture
def mock_client_session(mock_response):
    mock_session = AsyncMock()
    mock_session.post = AsyncMock()
    mock_session.post.return_value.__aenter__.return_value = mock_response
    mock_session.post.return_value.__aexit__.return_value = None
    return mock_session

@pytest.fixture
def mock_graphql_response():
    return {
        'leads': {
            'data': {
                'fetchLeads': {
                    'data': [{
                        'id': 'lead1',
                        'name': 'Test Lead',
                        'email': 'test@example.com',
                        'telephone': '1234567890',
                        'source': {'title': 'Test Source'},
                        'store': {'name': 'Test Store'},
                        'status': {'label': 'Active'},
                        'createdAt': '2024-01-01T00:00:00Z'
                    }],
                    'meta': {'currentPage': 1, 'lastPage': 1}
                }
            }
        },
        'appointments': {
            'data': {
                'fetchAppointments': {
                    'data': [{
                        'id': 'appointment1',
                        'status': {'label': 'Scheduled'},
                        'store': {'name': 'Test Store'},
                        'customer': {
                            'id': '',
                            'name': 'Test Customer',
                            'telephone': '1234567890'
                        },
                        'procedure': {
                            'name': 'Test Procedure',
                            'group': {'name': 'Test Group'}
                        },
                        'employee': {'name': 'Test Employee'},
                        'createdBy': {
                            'name': 'Test Creator',
                            'createdAt': '2024-01-01T00:00:00Z'
                        },
                        'date': '2024-01-01T00:00:00Z'
                    }],
                    'meta': {'currentPage': 1, 'lastPage': 1}
                }
            }
        },
        'bill_charges': {
            'data': {
                'fetchBillCharges': {
                    'data': [{
                        'id': 'bill1',
                        'amount': 100.00,
                        'status': 'Paid',
                        'store': {'name': 'Test Store'},
                        'customer': {
                            'id': '',
                            'name': 'Test Customer',
                            'email': 'test@example.com'
                        }
                    }],
                    'meta': {'currentPage': 1, 'lastPage': 1}
                }
            }
        }
    }

@pytest.fixture
def mock_processed_data():
    return {
        'leads': [{
            'id': 'lead1',
            'name': 'Test Lead',
            'email': 'test@example.com',
            'phone': '1234567890',
            'source': 'Test Source',
            'store': 'Test Store',
            'status': 'Active'
        }],
        'appointments': [{
            'id': 'appointment1',
            'status_label': 'Scheduled',
            'store_name': 'Test Store',
            'customer_name': 'Test Customer',
            'customer_phone': '1234567890',
            'procedure_name': 'Test Procedure',
            'procedure_group': 'Test Group',
            'employee_name': 'Test Employee'
        }],
        'bill_charges': [{
            'id': 'bill1',
            'amount': 100.00,
            'status': 'Paid',
            'store_name': 'Test Store',
            'customer_name': 'Test Customer',
            'customer_email': 'test@example.com'
        }]
    }

@pytest.fixture
def mock_session():
    """Create a mock aiohttp ClientSession"""
    mock = AsyncMock()
    mock.__aenter__.return_value = mock
    mock.__aexit__.return_value = None
    
    # Mock the post method
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {'data': {'fetchData': {'data': [], 'meta': {'currentPage': 1, 'lastPage': 1}}}}
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None
    mock.post.return_value = mock_response
    
    return mock

@pytest.mark.asyncio
async def test_fetch_all_data_success(mock_processed_data, mock_session):
    """Test successful data fetching from all endpoints with fully mocked data"""
    with patch('aiohttp.ClientSession', return_value=mock_session), \
         patch('apiCrm.resolvers.fetch_all_leads.fetch_graphql', new_callable=AsyncMock) as mock_fetch_leads_graphql, \
         patch('apiCrm.resolvers.fetch_all_appointments.fetch_graphql', new_callable=AsyncMock) as mock_appointments_graphql, \
         patch('apiCrm.resolvers.fetch_bill_charges.fetch_graphql', new_callable=AsyncMock) as mock_bill_charges_graphql:

        # Mock successful GraphQL responses
        mock_fetch_leads_graphql.return_value = {
            'data': {
                'fetchLeads': {
                    'data': mock_processed_data['leads'],
                    'meta': {'currentPage': 1, 'lastPage': 1}
                }
            }
        }
        mock_appointments_graphql.return_value = {
            'data': {
                'fetchAppointments': {
                    'data': mock_processed_data['appointments'],
                    'meta': {'currentPage': 1, 'lastPage': 1}
                }
            }
        }
        mock_bill_charges_graphql.return_value = {
            'data': {
                'fetchBillCharges': {
                    'data': mock_processed_data['bill_charges'],
                    'meta': {'currentPage': 1, 'lastPage': 1}
                }
            }
        }

        # Call the function
        from apiCrm.resolvers.fetch_all_data import fetch_all_data
        leads_data, appointments_data, bill_charges_data = await fetch_all_data(
            '2024-01-01', '2024-01-02', '2024-01-03', 'test-token'
        )

        # Verify results
        assert leads_data == mock_processed_data['leads']
        assert appointments_data == mock_processed_data['appointments']
        assert bill_charges_data == mock_processed_data['bill_charges']

@pytest.mark.asyncio
async def test_fetch_all_data_empty_response(mock_session):
    """Test handling of empty responses with fully mocked data"""
    with patch('aiohttp.ClientSession', return_value=mock_session), \
         patch('apiCrm.resolvers.fetch_all_leads.fetch_graphql', new_callable=AsyncMock) as mock_fetch_leads_graphql, \
         patch('apiCrm.resolvers.fetch_all_appointments.fetch_graphql', new_callable=AsyncMock) as mock_appointments_graphql, \
         patch('apiCrm.resolvers.fetch_bill_charges.fetch_graphql', new_callable=AsyncMock) as mock_bill_charges_graphql:

        # Mock empty GraphQL responses
        mock_fetch_leads_graphql.return_value = {
            'data': {
                'fetchLeads': {
                    'data': [],
                    'meta': {'currentPage': 1, 'lastPage': 1}
                }
            }
        }
        mock_appointments_graphql.return_value = {
            'data': {
                'fetchAppointments': {
                    'data': [],
                    'meta': {'currentPage': 1, 'lastPage': 1}
                }
            }
        }
        mock_bill_charges_graphql.return_value = {
            'data': {
                'fetchBillCharges': {
                    'data': [],
                    'meta': {'currentPage': 1, 'lastPage': 1}
                }
            }
        }

        # Call the function
        from apiCrm.resolvers.fetch_all_data import fetch_all_data
        leads_data, appointments_data, bill_charges_data = await fetch_all_data(
            '2024-01-01', '2024-01-02', '2024-01-03', 'test-token'
        )

        # Verify results
        assert leads_data == []
        assert appointments_data == []
        assert bill_charges_data == []

@pytest.mark.asyncio
async def test_fetch_all_data_network_error(mock_session):
    """Test handling of network errors with fully mocked data"""
    with patch('aiohttp.ClientSession', return_value=mock_session), \
         patch('apiCrm.resolvers.fetch_all_leads.fetch_graphql', new_callable=AsyncMock) as mock_fetch_leads_graphql, \
         patch('apiCrm.resolvers.fetch_all_appointments.fetch_graphql', new_callable=AsyncMock) as mock_appointments_graphql, \
         patch('apiCrm.resolvers.fetch_bill_charges.fetch_graphql', new_callable=AsyncMock) as mock_bill_charges_graphql:

        # Simulate network error
        mock_fetch_leads_graphql.side_effect = aiohttp.ClientError("Network error")
        mock_appointments_graphql.side_effect = aiohttp.ClientError("Network error")
        mock_bill_charges_graphql.side_effect = aiohttp.ClientError("Network error")

        # Call the function and expect error
        from apiCrm.resolvers.fetch_all_data import fetch_all_data
        with pytest.raises(aiohttp.ClientError) as exc_info:
            await fetch_all_data('2024-01-01', '2024-01-02', '2024-01-03', 'test-token')
        
        assert str(exc_info.value) == "Network error"

@pytest.mark.asyncio
async def test_fetch_all_data_invalid_dates(mock_session):
    """Test handling of invalid date formats with fully mocked data"""
    with patch('aiohttp.ClientSession', return_value=mock_session), \
         patch('apiCrm.resolvers.fetch_all_leads.fetch_graphql', new_callable=AsyncMock) as mock_fetch_leads_graphql, \
         patch('apiCrm.resolvers.fetch_all_appointments.fetch_graphql', new_callable=AsyncMock) as mock_appointments_graphql, \
         patch('apiCrm.resolvers.fetch_bill_charges.fetch_graphql', new_callable=AsyncMock) as mock_bill_charges_graphql:

        # Simulate date validation error
        mock_fetch_leads_graphql.side_effect = ValueError("Invalid date format")
        mock_appointments_graphql.side_effect = ValueError("Invalid date format")
        mock_bill_charges_graphql.side_effect = ValueError("Invalid date format")

        # Call the function and expect error
        from apiCrm.resolvers.fetch_all_data import fetch_all_data
        with pytest.raises(ValueError) as exc_info:
            await fetch_all_data('invalid-date', '2024-01-02', '2024-01-03', 'test-token')

# @pytest.mark.asyncio
# async def test_fetch_all_data_missing_token(mock_session):
#     """Test handling of missing authentication token"""
#     with patch('aiohttp.ClientSession', return_value=mock_session), \
#          patch('apiCrm.resolvers.fetch_all_leads.fetch_graphql', new_callable=AsyncMock) as mock_fetch_leads_graphql, \
#          patch('apiCrm.resolvers.fetch_all_appointments.fetch_graphql', new_callable=AsyncMock) as mock_appointments_graphql, \
#          patch('apiCrm.resolvers.fetch_bill_charges.fetch_graphql', new_callable=AsyncMock) as mock_bill_charges_graphql:

#         # Simulate authentication error by returning None
#         mock_fetch_leads_graphql.return_value = None
#         mock_appointments_graphql.return_value = None
#         mock_bill_charges_graphql.return_value = None

#         # Call the function and expect error
#         from apiCrm.resolvers.fetch_all_data import fetch_all_data
#         with pytest.raises(ValueError) as exc_info:
#             await fetch_all_data('2024-01-01', '2024-01-02', '2024-01-03', '')

#         assert str(exc_info.value) == "Missing or invalid token"

# @pytest.mark.asyncio
# async def test_fetch_all_data_partial_failure(mock_session):
#     """Test handling of partial endpoint failures with fully mocked data"""
#     with patch('aiohttp.ClientSession', return_value=mock_session), \
#          patch('apiCrm.resolvers.fetch_all_leads.fetch_graphql', new_callable=AsyncMock) as mock_fetch_leads_graphql, \
#          patch('apiCrm.resolvers.fetch_all_appointments.fetch_graphql', new_callable=AsyncMock) as mock_appointments_graphql, \
#          patch('apiCrm.resolvers.fetch_bill_charges.fetch_graphql', new_callable=AsyncMock) as mock_bill_charges_graphql:

#         # First request succeeds, second fails
#         mock_fetch_leads_graphql.return_value = {
#             'data': {
#                 'fetchLeads': {
#                     'data': [{'id': 'lead1'}],
#                     'meta': {'currentPage': 1, 'lastPage': 1}
#                 }
#             }
#         }
#         mock_appointments_graphql.side_effect = aiohttp.ClientError("Network error")
#         mock_bill_charges_graphql.side_effect = aiohttp.ClientError("Network error")

#         # Call the function and expect error
#         from apiCrm.resolvers.fetch_all_data import fetch_all_data
#         with pytest.raises(aiohttp.ClientError) as exc_info:
#             await fetch_all_data('2024-01-01', '2024-01-02', '2024-01-03', 'test-token')
        
#         assert str(exc_info.value) == "Network error"