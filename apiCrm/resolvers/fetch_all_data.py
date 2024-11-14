# apiCrm/resolvers/fetch_all_data
import aiohttp
import asyncio
from decouple import config
from apiCrm.resolvers.fetch_all_leads import fetch_all_leads
from apiCrm.resolvers.fetch_all_appointments import fetch_all_appointments
from apiCrm.resolvers.fetch_bill_charges import fetch_bill_charges
token = config('TOKEN')

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
