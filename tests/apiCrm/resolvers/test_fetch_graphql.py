import pytest
from unittest.mock import patch, AsyncMock
import aiohttp
import json
from apiCrm.resolvers.fetch_graphql import fetch_graphql

# Constants
URL = "https://example.com/graphql"
QUERY = "query { someField }"
VARIABLES = {}
TOKEN = "mytoken"

@pytest.mark.asyncio
@patch('aiohttp.ClientSession.post')
async def test_fetch_graphql(mock_post, mocker):
    mock_response = mocker.AsyncMock()
    mock_response.status = 200
    mock_response.json = mocker.AsyncMock(return_value={'data': 'some data'})
    mock_post.return_value.__aenter__.return_value = mock_response
    
    async with aiohttp.ClientSession() as session:
        data = await fetch_graphql(session, 'http://example.com/graphql', 'query {}', {}, 'token')
    
    # Asserts to verify behavior
    assert data == {'data': 'some data'}
    mock_post.assert_called_once_with(
        'http://example.com/graphql',
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer token'
        },
        data='{"query": "query {}", "variables": {}}'
    )

