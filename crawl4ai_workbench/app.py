from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .models import CrawlRequest, CrawlResponse
from .security import UnsafeUrlError
from .service import crawl_page

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="Crawl4AI Workbench",
    description="Local browser UI and API for Crawl4AI",
    version=__version__,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.post("/api/crawl", response_model=CrawlResponse)
async def crawl(request: CrawlRequest) -> CrawlResponse:
    try:
        return await crawl_page(request)
    except UnsafeUrlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Crawl failed: {exc}") from exc
