from types import SimpleNamespace

import pytest

from crawl4ai_workbench.models import CrawlRequest
from crawl4ai_workbench import service


class FakeResultContainer:
    """Mimics crawl4ai's CrawlResultContainer: delegates to first item and is iterable."""

    def __init__(self, results):
        if not isinstance(results, list):
            results = [results]
        self._results = results

    def __iter__(self):
        return iter(self._results)

    def __len__(self):
        return len(self._results)

    def __getattr__(self, attr):
        if self._results:
            return getattr(self._results[0], attr)
        raise AttributeError(attr)


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
            return FakeResultContainer(
                SimpleNamespace(
                    success=False,
                    error_message=(
                        "Blocked by anti-bot protection: Structural: minimal_text, "
                        "no_content_elements, script_heavy_shell"
                    ),
                )
            )
        return FakeResultContainer(
            SimpleNamespace(
                success=True,
                error_message=None,
                markdown="# Recovered page\n\nReadable content.",
                links={"internal": [], "external": []},
                media={"images": []},
                metadata={"title": "Recovered"},
                url=url,
            )
        )


def test_overlay_removal_is_opt_in():
    assert CrawlRequest(url="https://example.com").remove_overlays is False


def test_crawl_depth_default_is_one():
    assert CrawlRequest(url="https://example.com").crawl_depth == 1


@pytest.mark.asyncio
async def test_deep_crawl_uses_bfs_strategy_with_requested_depth(monkeypatch, tmp_path):
    captured = {}

    class SpyStrategy:
        def __init__(self, max_depth, **kwargs):
            captured["max_depth"] = max_depth
            captured["kwargs"] = kwargs

    monkeypatch.setattr(service, "BFSDeepCrawlStrategy", SpyStrategy)
    monkeypatch.setattr(service, "AsyncWebCrawler", FakeCrawler)
    monkeypatch.setattr(service.settings, "output_dir", tmp_path)

    result = await service.crawl_page(
        CrawlRequest(url="https://example.com", crawl_depth=3)
    )

    assert captured["max_depth"] == 3
    assert result.pages_crawled == 1
    assert result.success is True


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
