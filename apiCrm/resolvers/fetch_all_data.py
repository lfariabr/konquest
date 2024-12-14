# apiCrm/resolvers/fetch_all_data
import aiohttp
import asyncio
import logging
from typing import Dict, List, Tuple, Optional
from decouple import config
from apiCrm.resolvers.fetch_all_leads import fetch_all_leads
from apiCrm.resolvers.fetch_all_appointments import fetch_all_appointments
from apiCrm.resolvers.fetch_bill_charges import fetch_bill_charges

logger = logging.getLogger(__name__)

class FetchStats:
    def __init__(self):
        self.total_pages = 0
        self.current_page = 0
        self.total_records = 0
        self.fetched_records = 0
        self.failed_pages = []
        self.start_time = None
        self.end_time = None

    @property
    def progress(self) -> float:
        return (self.current_page / self.total_pages * 100) if self.total_pages > 0 else 0

    def log_progress(self, data_type: str):
        if self.total_pages > 0:  # Only log if we have pages to process
            logger.info(
                f"{data_type} Progress: {self.progress:.1f}% | "
                f"Page {self.current_page}/{self.total_pages} | "
                f"Records: {self.fetched_records}/{self.total_records or 1}"  # Avoid division by zero
            )

async def fetch_with_stats(
    session: aiohttp.ClientSession,
    fetch_func,
    data_type: str,
    start_date: str,
    end_date: str,
    token: str,
    stats: Optional[FetchStats] = None
) -> Tuple[List[Dict], List[str]]:
    try:
        # Call the fetch function with only the required arguments
        data = await fetch_func(session, start_date, end_date, token)
        
        if stats:
            if stats.failed_pages:
                logger.warning(
                    f"{data_type}: Failed to fetch {len(stats.failed_pages)} pages: {stats.failed_pages}"
                )
            if stats.total_records > 0:  # Only log if we have records
                logger.info(
                    f"{data_type} Complete | "
                    f"Total Records: {stats.fetched_records} | "
                    f"Failed Pages: {len(stats.failed_pages)}"
                )
        return data, stats.failed_pages if stats else []
    except Exception as e:
        logger.error(f"Error fetching {data_type}: {str(e)}")
        return [], []

# Main async function to fetch all data concurrently
async def fetch_all_data(start_date, end_date, extended_end_date, token):
    logger.info(f"Fetching data for dates: {start_date} to {end_date}")
    async with aiohttp.ClientSession() as session:
        leads_task = fetch_all_leads(session, start_date, end_date, token)
        appointments_task = fetch_all_appointments(session, start_date, extended_end_date, token)
        bill_charges_task = fetch_bill_charges(session, start_date, end_date, token)

        leads_data, appointments_data, bill_charges_data = await asyncio.gather(
            leads_task, appointments_task, bill_charges_task
        )

        logger.info(f"Fetched: {len(leads_data)} leads, {len(appointments_data)} appointments, {len(bill_charges_data)} bill charges")
        return leads_data, appointments_data, bill_charges_data

# Wrapper function to run async functions with coroutines
def run_fetch_all(start_date, end_date, extended_end_date, token):
    return asyncio.run(fetch_all_data(start_date, end_date, extended_end_date, token))
