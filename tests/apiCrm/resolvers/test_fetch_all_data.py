# tests/apiCrm/resolvers/test_fetch_all_data.py
import pytest
from unittest.mock import AsyncMock, patch
from apiCrm.resolvers.fetch_all_data import fetch_all_data

@pytest.mark.asyncio
async def test_fetch_all_data():
    # Mock aiohttp.ClientSession and its context manager
    with patch('aiohttp.ClientSession') as mock_client_session:
        # Create a mock session instance
        mock_session_instance = AsyncMock()
        mock_client_session.return_value.__aenter__.return_value = mock_session_instance

        # Mock the fetch functions to return predefined data
        with patch('apiCrm.resolvers.fetch_all_data.fetch_all_leads', new_callable=AsyncMock) as mock_fetch_all_leads, \
             patch('apiCrm.resolvers.fetch_all_data.fetch_all_appointments', new_callable=AsyncMock) as mock_fetch_all_appointments, \
             patch('apiCrm.resolvers.fetch_all_data.fetch_bill_charges', new_callable=AsyncMock) as mock_fetch_bill_charges:

            # Set the mock return values
            mock_fetch_all_leads.return_value = [{'id': 'lead1'}]
            mock_fetch_all_appointments.return_value = [{'id': 'appointment1'}]
            mock_fetch_bill_charges.return_value = [{'id': 'bill1'}]

            # Define test parameters
            start_date = '2024-01-01'
            end_date = '2024-01-02'
            extended_end_date = '2024-01-03'
            token = 'test-token'

            # Call the function under test
            leads_data, appointments_data, bill_charges_data = await fetch_all_data(
                start_date, end_date, extended_end_date, token
            )

            # Assertions
            assert leads_data == [{'id': 'lead1'}]
            assert appointments_data == [{'id': 'appointment1'}]
            assert bill_charges_data == [{'id': 'bill1'}]

            # Verify that fetch functions were called with the correct arguments
            mock_fetch_all_leads.assert_called_once_with(
                mock_session_instance, start_date, end_date, token
            )
            mock_fetch_all_appointments.assert_called_once_with(
                mock_session_instance, start_date, extended_end_date, token
            )
            mock_fetch_bill_charges.assert_called_once_with(
                mock_session_instance, start_date, end_date, token
            )