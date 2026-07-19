import pytest

from crawl4ai_workbench.security import UnsafeUrlError, validate_public_url


@pytest.mark.asyncio
async def test_rejects_non_http_scheme():
    with pytest.raises(UnsafeUrlError, match="Only http"):
        await validate_public_url("file:///etc/passwd")


@pytest.mark.asyncio
async def test_rejects_localhost():
    with pytest.raises(UnsafeUrlError, match="private"):
        await validate_public_url("http://localhost:9090")


@pytest.mark.asyncio
async def test_allows_private_when_explicitly_enabled():
    assert (
        await validate_public_url("http://127.0.0.1:8000", allow_private=True)
        == "http://127.0.0.1:8000"
    )
