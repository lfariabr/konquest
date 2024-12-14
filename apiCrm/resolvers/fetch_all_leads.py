# apiCrm/resolvers/fetch_all_leads.py
import asyncio
import logging
from typing import List, Dict
from apiCrm.resolvers.fetch_graphql import fetch_graphql

logger = logging.getLogger(__name__)

async def fetch_all_leads(session, start_date: str, end_date: str, token: str) -> List[Dict]:
    current_page = 1
    all_leads = []
    
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

    while True:
        variables = {
            'filters': {
                'createdAtRange': {
                    'start': start_date,
                    'end': end_date,
                },
            },
            'pagination': {
                'currentPage': current_page,
                'perPage': 1000,
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
        await asyncio.sleep(4)

    return all_leads