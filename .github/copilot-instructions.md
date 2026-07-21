Purpose

This file gives Copilot sessions focused, repository-specific instructions: how to build/run/test/lint, important architecture/flow, and conventions worth knowing when making changes or answering questions.

Build / Run / Test / Lint (concrete commands)

- Run the web UI + API (two options):
  - Using uvicorn directly:
    uvicorn crawl4ai_workbench.app:app --host 0.0.0.0 --port 8088
  - Using the package CLI after installing the project (editable install):
    python -m pip install -e .
    crawl4ai-workbench serve --host 0.0.0.0 --port 8088
  - README shows shorthand using the project's task runner: uv run crawl4ai-workbench serve

- CLI single-crawl:
  - python -m crawl4ai_workbench.cli crawl https://example.com --raw
  - or after install: crawl4ai-workbench crawl https://example.com
  - Control crawl link-following depth with --depth (int, 0..5). Default is 1: 0 = only the provided URL, 1 = follow top-level links.

- Tests
  - Full test suite: pytest -q
  - Run a single test file: pytest tests/test_service.py -q
  - Run a single test case: pytest tests/test_service.py::test_retries_structural_false_positive_without_overlay_removal -q
  - Notes: tests use pytest-asyncio for async tests. There is an optional Playwright e2e script at tests/e2e_smoke.py that requires Playwright and a running server.

- Linting
  - Run ruff over repo: ruff check .
  - Run ruff against a single file: ruff check crawl4ai_workbench/service.py

- Developer deps (pyproject.dev): pytest, pytest-asyncio, ruff. The project uses hatchling as build backend (pyproject.toml).

High-level architecture (big picture)

- crawl4ai_workbench (package)
  - crawl4ai_workbench.app: FastAPI application; mounts static UI under /static and exposes /api/crawl and /api/health.
  - crawl4ai_workbench.cli: thin CLI wrapper providing `serve` (runs the API/UI) and `crawl` (single-site crawl + JSON output).
  - crawl4ai_workbench.service: core logic that orchestrates crawl4ai.AsyncWebCrawler, configures BrowserConfig and CrawlerRunConfig, applies markdown generator when requested, writes timestamped outputs under outputs/ and produces a CrawlResponse.
  - crawl4ai_workbench.config: runtime settings via pydantic-settings, env prefix C4AI_. (.env.example provided)
  - crawl4ai_workbench.security: URL validation/SSRF mitigation (resolves host, blocks non-global addresses unless allow_private enabled).
  - crawl4ai_workbench.models: Pydantic request/response models used across API/CLI/service.
  - static/: front-end assets (index.html, app.js, style.css) served by FastAPI for interactive use.

Key repository conventions and patterns

- Env vars use prefix C4AI_ and are consumed by pydantic-settings (see Settings in config.py). Examples in .env.example.
- Default outputs folder is outputs/; service writes a timestamped stem: YYYYMMDDTHHMMSSZ-<slug>.md and matching .json metadata.
- Overlay removal is opt-in (remove_overlays flag). If overlay removal triggers a structural false positive, the service retries once without overlay removal.
- Error handling: UnsafeUrlError is raised for disallowed URLs; API converts it to HTTP 400. Other crawl errors surface as 502.
- Tests commonly monkeypatch AsyncWebCrawler in service to avoid real browser runs; follow that pattern when writing unit tests.
- The project exposes a console script (project.scripts) named crawl4ai-workbench; after installation the CLI can be run directly.
- E2E tests (tests/e2e_smoke.py) are present but optional — they require Playwright and a running local server and will write artifacts/workbench-e2e.png when run.

Files and AI-config to consider

- No existing .github/copilot-instructions.md was present (this file created).
- No CLAUDE.md, AGENTS.md, .cursorrules, .windsurfrules, .clinerules or similar AI assistant config files were found.

Quick tips for Copilot sessions (short)

- Use pyproject.toml to discover runtime and dev deps (hatchling + dev group).
- Prefer testing by monkeypatching AsyncWebCrawler for unit tests; run Playwright only for explicit integration/e2e runs.
- Environment toggles that matter to reasoning: C4AI_ALLOW_PRIVATE_NETWORKS, C4AI_OUTPUT_DIR, C4AI_PAGE_TIMEOUT_MS.

MCP servers

This repo includes an e2e script that uses Playwright. If desired, configure an MCP Playwright server (or other browser/runner) to run e2e flows from Copilot agents.

If changes are desired (expand sections, add CI workflow notes, or include example pytest invocations for common edits), say which area to expand.