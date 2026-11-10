# What's New in Gemini CLI (Archived)

> [!CAUTION]
> **ARCHIVED & UNSUPPORTED PROJECT**: This repository is **archived** for historical reference only and is **no longer actively maintained or supported**. No new features, bug fixes, dependency updates, or pull requests will be accepted.

> [!IMPORTANT]
> **DISCLAIMER & LIABILITY NOTICE**: This is a **personal, individual project** created by the author (Prashanth Subrahmanyam). It is **not** an official Google product, it is **not** affiliated with or supported by Google Cloud or Google LLC, and it does **not** come with any official support or warranty. By using this software, you acknowledge that you are solely liable for its use.

---

This project is an automated prototype pipeline that generated "What's New" reports for [Gemini CLI](https://geminicli.com) releases. It scraped the official changelog, fetched context from linked GitHub Pull Requests and Issues, and used the Google Gen AI SDK (`google-genai`) to draft feature summaries.

## Features

* **Changelog Monitoring**: Scraped release entries from `geminicli.com/docs/changelogs`.
* **Context Gathering**: Pulled PR descriptions and linked issues from `github.com/google-gemini/gemini-cli`.
* **AI-Powered Summaries**: Used the Google Gen AI SDK to draft structured third-person release notes (Feature Summaries, Context, How-Tos, and Walkthroughs).
* **REST API**: Included a FastAPI backend to serve generated reports and trigger synchronization.

## Prerequisites

* Python 3.10+
* [`uv`](https://github.com/astral-sh/uv)
* A Google AI Studio API key (`GOOGLE_API_KEY`)

## Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ksprashu/whats-new-in-gemini-cli.git
   cd whats-new-in-gemini-cli
   ```
2. **Set your API Key**:
   ```bash
   export GOOGLE_API_KEY="your_actual_api_key_here"
   ```
3. **Install dependencies using `uv`**:
   ```bash
   uv sync
   ```

## Usage

### 1. Running the Orchestrator (CLI Check)

The orchestrator script (`main.py`) checks for updates, coordinates scraping, gathers context, generates reports, and saves them to the local `reports/` directory:

```bash
uv run python main.py --check
```

### 2. Running the API Server

The FastAPI server (`api.py`) serves generated reports over JSON:

```bash
uv run uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

**Endpoints:**
* `GET /api/reports`: Lists generated reports and their status.
* `GET /api/reports/{id}`: Retrieves a report (requires `Authorization: Bearer <ADMIN_API_KEY>` to include private admin notes).
* `POST /api/reports/{id}/done`: Marks a report as processed (requires `ADMIN_API_KEY`).
* `POST /api/sync`: Triggers synchronization in the background (requires `ADMIN_API_KEY`).

## Project Structure

* `main.py`: CLI entrypoint for syncing updates.
* `api.py`: FastAPI server entrypoint.
* `agents/`: Scraper and writer components (`writer_agent.py`, `changelog_agent.py`, `github_agent.py`).
* `utils/`: Scraper and storage helpers (`scraper.py`, `storage.py`).
* `reports/`: Local directory where generated reports and metadata are stored.
* `static/`: Static web frontends (`public` and `admin`).
* `scripts/deploy_gcp.sh`: Example Cloud Run / Cloud Scheduler deployment script.
* [`architecture.md`](./architecture.md): System design and architecture notes.

## Project Status & Disclaimer

* **Status**: Archived / Unsupported. Maintained in read-only state for reference only.
* **Disclaimer**: This is a personal project and is **not** an officially supported Google product.

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
