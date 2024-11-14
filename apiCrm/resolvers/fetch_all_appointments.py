import asyncio
from decouple import config
from apiCrm.resolvers.fetch_graphql import fetch_graphql
token = config('TOKEN')

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

        if data is None: #TODO add test of this case on tests
            print(f"Failed to fetch appointments on page {current_page}. Retrying...")
            continue
        
        # Simply add the raw appointment data to the list
        appointments_data = data['data']['fetchAppointments']['data']
        all_appointments.extend(appointments_data)

        meta = data['data']['fetchAppointments']['meta']
        last_page = meta['lastPage']

        print(f"Querying Appointments - Page: {current_page}/{last_page} - startDate: {start_date} - endDate: {end_date}")

        if current_page >= last_page: #TODO all pages are being loaded on tests
            break #TODO if only one pag on tests

        current_page += 1
        await asyncio.sleep(5)

    return all_appointments