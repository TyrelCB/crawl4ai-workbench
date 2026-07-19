from pydantic import BaseModel, Field


class CrawlRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2048)
    fit_markdown: bool = True
    bypass_cache: bool = True
    remove_overlays: bool = False
    word_count_threshold: int = Field(default=10, ge=0, le=1000)


class CrawlResponse(BaseModel):
    success: bool
    url: str
    title: str | None = None
    markdown: str
    output_file: str
    elapsed_seconds: float
    word_count: int
    markdown_chars: int
    internal_links: int
    external_links: int
    images: int
    error: str | None = None
