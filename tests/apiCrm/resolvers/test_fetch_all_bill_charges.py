import pytest
from unittest.mock import patch, AsyncMock
from apiCrm.resolvers.fetch_bill_charges import fetch_bill_charges

# Constants
URL = "https://open-api.eprocorpo.com.br/graphql"
TOKEN = "yourtoken"
START_DATE = "2024-01-01"
END_DATE = "2024-01-02"

@pytest.mark.asyncio
@patch('apiCrm.resolvers.fetch_bill_charges.fetch_graphql', new_callable=AsyncMock)
async def test_fetch_bill_charges(mock_fetch_graphql):
    # Setup mock response data
    mock_response_data = {
        'data': {
            'fetchBillCharges': {
                'data': [
                    {
                        'quote': {
                            'id': '1',
                            'customer': {'name': 'John Doe'},
                            'status': 'Confirmed',
                            'bill': {
                                'total': 100.0,
                                'installmentsQuantity': 1,
                                'items': [
                                    {'amount': 50.0, 'description': 'Item 1', 'quantity': 2},
                                    {'amount': 50.0, 'description': 'Item 2', 'quantity': 2}
                                ]
                            }
                        },
                        'store': {'name': 'Main Branch'},
                        'amount': 100.0,
                        'paidAt': '2024-01-02T14:00:00Z',
                        'dueAt': '2024-01-02T14:00:00Z',
                        'isPaid': True,
                        'paymentMethod': {
                            'label': 'Credit Card',
                        }
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
    bill_charges = await fetch_bill_charges(mock_session, START_DATE, END_DATE, TOKEN)

    # Assertions to check if the bill_charges list is correct
    assert len(bill_charges) == 1
    bill_charge = bill_charges[0]
    assert bill_charge['quote']['id'] == '1'
    assert bill_charge['quote']['customer']['name'] == 'John Doe'
    assert bill_charge['quote']['status'] == 'Confirmed'
    assert bill_charge['store']['name'] == 'Main Branch'
    assert bill_charge['amount'] == 100.0
    assert bill_charge['paidAt'] == '2024-01-02T14:00:00Z'
    assert bill_charge['dueAt'] == '2024-01-02T14:00:00Z'
    assert bill_charge['isPaid'] is True
    assert bill_charge['paymentMethod']['label'] == 'Credit Card'

    # Verify that fetch_graphql was called correctly
    mock_fetch_graphql.assert_called_once_with(
        mock_session,
        URL,
        '''query ($filters: BillChargeFiltersInput, $pagination: PaginationInput) {
                fetchBillCharges(filters: $filters, pagination: $pagination) {
                    data {
                        quote {
                            id
                            customer {
                                id
                                name
                                taxvat
                                email
                            }
                            status
                            bill {
                                total
                                installmentsQuantity
                                items {
                                    amount
                                    description
                                    quantity
                                }
                            }
                        }
                        store {
                            name
                        }
                        amount
                        paidAt
                        dueAt
                        isPaid
                        paymentMethod {
                            name
                        }
                    }
                    meta {
                        currentPage
                        lastPage
                    }
                }
            }''',
        {
            'filters': {
                'paidAtRange': {
                    'start': START_DATE,
                    'end': END_DATE,
                },
            },
            'pagination': {
                'currentPage': 1,
                'perPage': 1000,
            },
        },
        TOKEN
    )