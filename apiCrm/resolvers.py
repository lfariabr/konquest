# apiCrm/resolvers.py
import aiohttp
import asyncio
from datetime import datetime, timedelta


async def fetch_graphql(session, url, query, variables, token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    async with session.post(url, json={'query': query, 'variables': variables}, headers=headers) as response:
        if response.status == 200:
            return await response.json()
        else:
            print(f"GraphQL request failed with status {response.status}")
            return None

# Session? for "fetch_all_data"
async def fetch_all_leads(start_date, end_date, token): 
    current_page = 1
    all_leads = []

    async with aiohttp.ClientSession() as session:
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
                    'perPage': 200,
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

async def fetch_all_appointments(start_date, end_date, token):
    current_page = 1
    all_appointments = []

    async with aiohttp.ClientSession() as session:
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

            print(f"Fetched data: {data}")

            # Simply add the raw appointment data to the list
            appointments_data = data['data']['fetchAppointments']['data']
            print(f"Appointments data: {appointments_data}")
            all_appointments.extend(appointments_data)

            meta = data['data']['fetchAppointments']['meta']
            last_page = meta['lastPage']

            print(f"Querying Appointments - Page: {current_page}/{last_page} - startDate: {start_date} - endDate: {end_date}")

            if current_page >= last_page:
                break

            current_page += 1
            await asyncio.sleep(5)

    return all_appointments

