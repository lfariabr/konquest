# apiCrm/resolvers.py
import asyncio
from decouple import config
from apiCrm.resolvers.fetch_graphql import fetch_graphql
token = config('TOKEN')

async def fetch_bill_charges(session, start_date, end_date, token):
    current_page = 1
    all_bill_charges = []

    while True:
        query = '''query ($filters: BillChargeFiltersInput, $pagination: PaginationInput) {
                fetchBillCharges(filters: $filters, pagination: $pagination) {
                    data {
                        quote {
                            id
                            customer {
                                id
                                name
                                taxvat
                                email
                                telephones {
                                    number
                                }
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
            }'''
        variables = {
            'filters': {
                'paidAtRange': {
                    'start': start_date,
                    'end': end_date,
                }
            },
            'pagination': {
                'currentPage': current_page,
                'perPage': 1000,
            }
        }

        data = await fetch_graphql(session, 'https://open-api.eprocorpo.com.br/graphql', query, variables, token)

        if data is None:
            print(f"Failed to fetch bill charges on page {current_page}. Retrying...")
            continue  # Retry the loop on failure

        bill_charges_data = data['data']['fetchBillCharges']['data']
        all_bill_charges.extend(bill_charges_data)

        meta = data['data']['fetchBillCharges']['meta']
        print(f"Querying Bill Charges - Page: {current_page}/{meta['lastPage']} - startDate: {start_date} - endDate: {end_date}")

        if current_page >= meta['lastPage']:
            break

        current_page += 1
        await asyncio.sleep(5)  # Small delay

    return all_bill_charges
