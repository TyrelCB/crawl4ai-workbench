import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 1100})
        await page.goto("http://127.0.0.1:8088", wait_until="networkidle")
        assert await page.title() == "Crawl4AI Workbench"
        await page.locator("#health.ok").wait_for()
        await page.locator("#url").fill("https://example.com")
        await page.locator("#submit").click()
        await page.locator("#result:not(.hidden)").wait_for(timeout=120_000)
        assert await page.locator("#title").inner_text() == "Example Domain"
        assert "Example Domain" in await page.locator("#markdown").inner_text()
        screenshot = Path("artifacts/workbench-e2e.png").resolve()
        screenshot.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=screenshot, full_page=True)
        print(
            f"E2E PASS: {await page.locator('#metric-words').inner_text()} words; screenshot={screenshot}"
        )
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
