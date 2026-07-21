import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from .config import settings
from .models import CrawlRequest, CrawlResponse
from .security import validate_public_url


def _safe_slug(url: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", url).strip("-").lower()
    return slug[:80] or "crawl"


def _markdown_text(markdown: object, fit: bool) -> str:
    if isinstance(markdown, str):
        return markdown
    field = "fit_markdown" if fit else "raw_markdown"
    value = getattr(markdown, field, None)
    if value is not None:
        return str(value)
    return str(markdown or "")


def _overlay_false_positive(error: str | None) -> bool:
    message = (error or "").lower()
    return "structural:" in message and "no_content_elements" in message


def _build_run_config(request: CrawlRequest) -> CrawlerRunConfig:
    markdown_generator = None
    if request.fit_markdown:
        markdown_generator = DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.45, threshold_type="fixed")
        )

    deep_crawl_strategy = None
    if request.crawl_depth > 0:
        # Cap pages to keep local runs bounded; depth still controls breadth.
        deep_crawl_strategy = BFSDeepCrawlStrategy(
            max_depth=request.crawl_depth,
            max_pages=50,
            include_external=False,
        )

    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS if request.bypass_cache else CacheMode.ENABLED,
        page_timeout=settings.page_timeout_ms,
        remove_overlay_elements=request.remove_overlays,
        word_count_threshold=request.word_count_threshold,
        markdown_generator=markdown_generator,
        deep_crawl_strategy=deep_crawl_strategy,
    )


def _result_to_response(
    result: object,
    request: CrawlRequest,
    output_dir: Path,
    timestamp: str,
    elapsed_seconds: float,
) -> CrawlResponse:
    """Serialize one crawl result to markdown/json and return a CrawlResponse."""
    url = str(result.url) if result.url else request.url
    markdown = _markdown_text(result.markdown, request.fit_markdown)
    links = result.links or {}
    media = result.media or {}
    metadata = result.metadata or {}
    stem = f"{timestamp}-{_safe_slug(url)}"
    markdown_path = output_dir / f"{stem}.md"
    metadata_path = output_dir / f"{stem}.json"
    markdown_path.write_text(markdown, encoding="utf-8")

    response = CrawlResponse(
        success=True,
        url=url,
        title=metadata.get("title"),
        markdown=markdown,
        output_file=str(markdown_path),
        elapsed_seconds=round(elapsed_seconds, 3),
        word_count=len(markdown.split()),
        markdown_chars=len(markdown),
        internal_links=len(links.get("internal", [])),
        external_links=len(links.get("external", [])),
        images=len(media.get("images", [])),
    )
    metadata_path.write_text(
        json.dumps(response.model_dump(exclude={"markdown"}), indent=2),
        encoding="utf-8",
    )
    return response


async def crawl_page(request: CrawlRequest) -> CrawlResponse:
    url = await validate_public_url(request.url, settings.allow_private_networks)
    run_config = _build_run_config(request)
    browser_config = BrowserConfig(headless=True, verbose=False)

    started = time.perf_counter()
    async with AsyncWebCrawler(config=browser_config) as crawler:
        container = await crawler.arun(url=url, config=run_config)

        # If the root page fails due to an overlay-removal false positive, retry
        # once without overlay removal before giving up.
        if (
            not container.success
            and request.remove_overlays
            and _overlay_false_positive(container.error_message)
        ):
            container = await crawler.arun(
                url=url,
                config=run_config.clone(remove_overlay_elements=False),
            )
    elapsed = time.perf_counter() - started

    if not container.success:
        raise RuntimeError(container.error_message or "Crawl failed")

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_dir = settings.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    results = list(container)
    if not results:
        raise RuntimeError("Crawl produced no results")

    responses = [
        _result_to_response(result, request, output_dir, timestamp, elapsed / len(results))
        for result in results
    ]

    root = responses[0]
    root.pages_crawled = len(responses)
    root.child_output_files = [r.output_file for r in responses[1:]]
    return root
