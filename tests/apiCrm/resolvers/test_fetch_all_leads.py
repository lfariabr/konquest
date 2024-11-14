import pytest
from unittest.mock import patch, AsyncMock
from apiCrm.resolvers.fetch_all_leads import fetch_all_leads

# Constants
URL = "https://open-api.eprocorpo.com.br/graphql"
TOKEN = "yourtoken"
START_DATE = "2024-01-01"
END_DATE = "2024-01-02"

@pytest.mark.asyncio
@patch('apiCrm.resolvers.fetch_all_leads.fetch_graphql', new_callable=AsyncMock)
async def test_fetch_all_leads(mock_fetch_graphql):
    # Setup mock response data
    mock_response_data = {
        'data': {
            'fetchLeads': {
                'data': [
                    {
                        'createdAt': '2024-01-02T14:00:00Z',
                        'id': '1',
                        'source': {'title': 'Facebook Leads'},
                        'store': {'name': 'Main Branch'},
                        'status': {'label': 'Confirmed'},
                        'customer': {'id': 'C1', 'name': 'John Doe'},
                        'name': 'John Doe',
                        'telephone': '1234567890',
                        'email': 'johndoe@example',
                        'message': 'Test message',
                        'utmMedium': 'Social',
                        'utmContent': 'Facebook',
                        'utmCampaign': '2024-01-01',
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
    leads = await fetch_all_leads(mock_session, START_DATE, END_DATE, TOKEN)

    # Assertions to check if the leads list is correct
    assert len(leads) == 1
    lead = leads[0]
    assert lead['id'] == '1'
    assert lead['createdAt'] == '2024-01-02T14:00:00Z'
    assert lead['source']['title'] == 'Facebook Leads'
    assert lead['store']['name'] == 'Main Branch'
    assert lead['status']['label'] == 'Confirmed'
    assert lead['customer']['name'] == 'John Doe'
    assert lead['name'] == 'John Doe'
    assert lead['telephone'] == '1234567890'
    assert lead['email'] == 'johndoe@example'
    assert lead['message'] == 'Test message'
    assert lead['utmMedium'] == 'Social'
    assert lead['utmContent'] == 'Facebook'
    assert lead['utmCampaign'] == '2024-01-01'

    # Verify that fetch_graphql was called correctly
    mock_fetch_graphql.assert_called_once_with(
        mock_session,
        URL,
        '''query ($filters: LeadFiltersInput, $pagination: PaginationInput) {
                    fetchLeads(filters: $filters, pagination: $pagination) {
                        data {
                            createdAt
                            id
                            source {
                                title
                            }
                            store {
                                name
                            }
                            status {
                                label
                            }
                            customer {
                                id
                                name
                            }
                            name
                            telephone
                            email
                            message
                            utmMedium
                            utmContent
                            utmCampaign
                            utmSearch
                            utmTerm
                        }
                        meta {
                            currentPage
                            lastPage
                        }
                    }
                }''',
        {
            'filters': {
                'createdAtRange': {
                    'start': START_DATE,
                    'end': END_DATE,
                },
            },
            'pagination': {
                'currentPage': 1,
                'perPage': 100,
            },
        },
        TOKEN
    )