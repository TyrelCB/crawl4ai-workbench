# Crawl4AI Workbench

A local browser UI, JSON API, and CLI built on [Crawl4AI](https://github.com/unclecode/crawl4ai) 0.9.2. It turns JavaScript-rendered web pages into clean Markdown and saves each result under `outputs/`.

## Run

```bash
cd ~/projects/crawl4ai-workbench
uv sync
uv run crawl4ai-setup
uv run crawl4ai-workbench serve
```

Open `http://localhost:8088`. The service binds `0.0.0.0` by default, but private/local crawl targets are blocked to reduce SSRF risk.

Overlay removal is opt-in because aggressive DOM cleanup can remove an entire page on some themes. If that produces Crawl4AI's structural anti-bot false positive, the workbench automatically retries once without overlay removal.

## CLI

```bash
uv run crawl4ai-workbench crawl https://example.com
uv run crawl4ai-workbench crawl https://example.com --raw
```

## API

```bash
curl -X POST http://localhost:8088/api/crawl \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","fit_markdown":true}'
```

Interactive OpenAPI docs: `http://localhost:8088/docs`.

## Service

The installer has enabled `crawl4ai-workbench.service` as a user service:

```bash
systemctl --user status crawl4ai-workbench
systemctl --user restart crawl4ai-workbench
journalctl --user -u crawl4ai-workbench -f
```

## Configuration

Copy `.env.example` to `.env` and edit values. Set `C4AI_ALLOW_PRIVATE_NETWORKS=true` only if you intentionally need to crawl LAN or localhost services.

## Development

```bash
uv run ruff check .
uv run pytest -q
```
