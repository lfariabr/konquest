import pytest
from unittest.mock import patch, AsyncMock
from apiCrm.resolvers.fetch_all_appointments import fetch_all_appointments

# Constants
URL = "https://open-api.eprocorpo.com.br/graphql"
TOKEN = "yourtoken"
START_DATE = "2024-01-01"
END_DATE = "2024-01-02"

@pytest.mark.asyncio
@patch('apiCrm.resolvers.fetch_all_appointments.fetch_graphql', new_callable=AsyncMock)
async def test_fetch_all_appointments(mock_fetch_graphql):
    # Setup mock response data
    mock_response_data = {
        'data': {
            'fetchAppointments': {
                'data': [
                    {
                        'id': '1',
                        'status': {'label': 'Confirmed'},
                        'createdBy': {'name': 'Admin', 'createdAt': '2024-01-01T12:00:00Z'},
                        'store': {'name': 'Main Branch'},
                        'customer': {'id': 'C1', 'name': 'John Doe', 'telephones': [{'number': '1234567890'}]},
                        'procedure': {'name': 'Checkup', 'groupLabel': 'General'},
                        'employee': {'name': 'Dr. Smith'},
                        'startDate': '2024-01-02T14:00:00Z'
                    }
                ],
                'meta': {'currentPage': 1, 'lastPage': 1}
            }
        }
    }
    
    # Configure the mock to return the prepared data
    mock_fetch_graphql.return_value = mock_response_data

    # Create a mock session (not used directly since fetch_graphql is mocked)
    mock_session = AsyncMock()

    # Call the function under test
    appointments = await fetch_all_appointments(mock_session, START_DATE, END_DATE, TOKEN)

    # Assertions to check if the appointments list is correct
    assert len(appointments) == 1
    appointment = appointments[0]
    assert appointment['id'] == '1'
    assert appointment['status']['label'] == 'Confirmed'
    assert appointment['createdBy']['name'] == 'Admin'
    assert appointment['store']['name'] == 'Main Branch'
    assert appointment['customer']['id'] == 'C1'
    assert appointment['customer']['name'] == 'John Doe'
    assert appointment['customer']['telephones'][0]['number'] == '1234567890'
    assert appointment['procedure']['name'] == 'Checkup'
    assert appointment['procedure']['groupLabel'] == 'General'
    assert appointment['employee']['name'] == 'Dr. Smith'
    assert appointment['startDate'] == '2024-01-02T14:00:00Z'

    # Verify that fetch_graphql was called correctly
    mock_fetch_graphql.assert_called_once_with(
        mock_session,
        URL,
        '''query ($filters: AppointmentFiltersInput, $pagination: PaginationInput) {
                    fetchAppointments(filters: $filters, pagination: $pagination) {
                        data {
                            id
                            status {
                                label
                            }
                            createdBy {
                                name
                                createdAt
                            }
                            store {
                                name
                            }
                            customer {
                                id
                                name
                                telephones {
                                    number
                                }
                            }
                            procedure {
                                name
                                groupLabel
                            }
                            employee {
                                name
                            }
                            startDate
                        }
                        meta {
                            currentPage
                            lastPage
                        }
                    }
                }''',
        {
            'filters': {
                'startDateRange': {
                    'start': START_DATE,
                    'end': END_DATE,
                },
            },
            'pagination': {
                'currentPage': 1,
                'perPage': 200,
            },
        },
        TOKEN
    )