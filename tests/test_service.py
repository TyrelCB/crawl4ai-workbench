from types import SimpleNamespace

import pytest

from crawl4ai_workbench.models import CrawlRequest
from crawl4ai_workbench import service


class FakeCrawler:
    calls: list[bool] = []

    def __init__(self, config):
        self.config = config

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return None

    async def arun(self, url, config):
        self.calls.append(config.remove_overlay_elements)
        if config.remove_overlay_elements:
            return SimpleNamespace(
                success=False,
                error_message=(
                    "Blocked by anti-bot protection: Structural: minimal_text, "
                    "no_content_elements, script_heavy_shell"
                ),
            )
        return SimpleNamespace(
            success=True,
            error_message=None,
            markdown="# Recovered page\n\nReadable content.",
            links={"internal": [], "external": []},
            media={"images": []},
            metadata={"title": "Recovered"},
            url=url,
        )


def test_overlay_removal_is_opt_in():
    assert CrawlRequest(url="https://example.com").remove_overlays is False


@pytest.mark.asyncio
async def test_retries_structural_false_positive_without_overlay_removal(
    monkeypatch, tmp_path
):
    FakeCrawler.calls = []
    monkeypatch.setattr(service, "AsyncWebCrawler", FakeCrawler)
    monkeypatch.setattr(service.settings, "output_dir", tmp_path)

    result = await service.crawl_page(
        CrawlRequest(
            url="https://example.com",
            fit_markdown=False,
            remove_overlays=True,
        )
    )

    assert FakeCrawler.calls == [True, False]
    assert result.success is True
    assert result.title == "Recovered"
