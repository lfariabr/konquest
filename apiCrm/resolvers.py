# apiCrm/resolvers.py
import aiohttp
import asyncio
import json
import pandas as pd
from datetime import datetime, timedelta
from decouple import config
token = config('TOKEN')

async def fetch_graphql(session, url, query, variables, token):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    payload = {
        'query': query,
        'variables': variables,
    }

    attempt = 0
    while True:  # Infinite retry loop
        try:
            async with session.post(url, headers=headers, data=json.dumps(payload)) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'errors' in data:
                        print(f"GraphQL errors: {data['errors']}")
                        return None
                    return data
                else:
                    print(f"Request failed with status {response.status}")
        except aiohttp.ClientError as e:
            print(f"Request exception: {e}")

        # Exponential backoff and retry
        attempt += 1
        wait_time = min(5 * 2 ** attempt, 30)  # Exponential backoff with max wait time of 30 seconds
        print(f"Retrying in {wait_time} seconds (attempt {attempt})...")
        await asyncio.sleep(wait_time)

# Main async function to fetch all data concurrently
async def fetch_all_data(start_date, end_date, extended_end_date, token):
    async with aiohttp.ClientSession() as session:
        leads_task = fetch_all_leads(session, start_date, end_date, token)
        appointments_task = fetch_all_appointments(session, start_date, extended_end_date, token)
        bill_charges_task = fetch_bill_charges(session, start_date, end_date, token)

        leads_data, appointments_data, bill_charges_data = await asyncio.gather(
            leads_task, appointments_task, bill_charges_task
        )

        return leads_data, appointments_data, bill_charges_data

# Wrapper function to run async functions with coroutines
def run_fetch_all(start_date, end_date, extended_end_date, token):
    return asyncio.run(fetch_all_data(start_date, end_date, extended_end_date, token))


# Session? for "fetch_all_data"
async def fetch_all_leads(session, start_date, end_date, token): 
    current_page = 1
    all_leads = []
    
    # async with aiohttp.ClientSession() as session:
    while True:
        query = '''query ($filters: LeadFiltersInput, $pagination: PaginationInput) {
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
                }'''

        variables = {
            'filters': {
                'createdAtRange': {
                    'start': start_date,
                    'end': end_date,
                },
            },
            'pagination': {
                'currentPage': current_page,
                'perPage': 100,
            },
        }

        data = await fetch_graphql(session, 'https://open-api.eprocorpo.com.br/graphql', query, variables, token)

        if data is None:
            print(f"Failed to fetch leads on page {current_page}. Retrying...")
            continue

        leads_data = data['data']['fetchLeads']['data']
        all_leads.extend(leads_data)

        meta = data['data']['fetchLeads']['meta']
        last_page = meta['lastPage']

        print(f"Querying Leads - Page: {current_page}/{last_page} - startDate: {start_date} - endDate: {end_date}")

        if current_page >= last_page:
            break

        current_page += 1
        await asyncio.sleep(10)

    return all_leads

async def fetch_all_appointments(session, start_date, end_date, token):
    current_page = 1
    all_appointments = []

    while True:
        query = '''query ($filters: AppointmentFiltersInput, $pagination: PaginationInput) {
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
                }'''

        variables = {
            'filters': {
                'startDateRange': {
                    'start': start_date,
                    'end': end_date,
                },
            },
            'pagination': {
                'currentPage': current_page,
                'perPage': 200,
            },
        }

        data = await fetch_graphql(session, 'https://open-api.eprocorpo.com.br/graphql', query, variables, token)

        if data is None:
            print(f"Failed to fetch appointments on page {current_page}. Retrying...")
            continue
        
        # Simply add the raw appointment data to the list
        appointments_data = data['data']['fetchAppointments']['data']
        all_appointments.extend(appointments_data)

        meta = data['data']['fetchAppointments']['meta']
        last_page = meta['lastPage']

        print(f"Querying Appointments - Page: {current_page}/{last_page} - startDate: {start_date} - endDate: {end_date}")

        if current_page >= last_page:
            break

        current_page += 1
        await asyncio.sleep(5)

    return all_appointments

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
                'perPage': 200,
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
