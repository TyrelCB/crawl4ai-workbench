import argparse
import asyncio
import json

import uvicorn

from .config import settings
from .models import CrawlRequest
from .service import crawl_page


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="crawl4ai-workbench")
    commands = root.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="Start the browser UI and API")
    serve.add_argument("--host", default=settings.host)
    serve.add_argument("--port", type=int, default=settings.port)
    crawl = commands.add_parser("crawl", help="Crawl one URL and save Markdown")
    crawl.add_argument("url")
    crawl.add_argument("--raw", action="store_true", help="Do not prune the Markdown")
    crawl.add_argument("--use-cache", action="store_true")
    crawl.add_argument("--depth", type=int, default=None, help="Crawl link-following depth (default: model default=1)")
    return root


async def _crawl(args: argparse.Namespace) -> None:
    result = await crawl_page(
        CrawlRequest(
            url=args.url,
            fit_markdown=not args.raw,
            bypass_cache=not args.use_cache,
            crawl_depth=args.depth,
        )
    )
    print(json.dumps(result.model_dump(exclude={"markdown"}), indent=2))


def main() -> None:
    args = parser().parse_args()
    if args.command == "serve":
        uvicorn.run("crawl4ai_workbench.app:app", host=args.host, port=args.port)
    else:
        asyncio.run(_crawl(args))


if __name__ == "__main__":
    main()
