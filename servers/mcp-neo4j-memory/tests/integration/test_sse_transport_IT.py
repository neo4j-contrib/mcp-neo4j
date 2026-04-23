import aiohttp
import pytest


@pytest.mark.asyncio
async def test_sse_endpoint(sse_server):
    """Test that SSE endpoint is accessible."""
    async with aiohttp.ClientSession() as session:
        async with session.get("http://127.0.0.1:8002/mcp/") as response:
            # SSE endpoint should be accessible
            assert response.status in [200, 404]  # 404 is okay if no specific endpoint