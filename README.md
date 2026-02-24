# What's New in Gemini CLI

This project is an automated pipeline that generates rich, detailed "What's New" reports for the [Gemini CLI](https://geminicli.com) releases. It scrapes the official changelog, fetches detailed context from linked GitHub Pull Requests and Issues, and uses the Gemini LLM (`gemini-3-pro-preview`) to write comprehensive, journalist-style feature updates.

## Features

*   **Changelog Monitoring**: Automatically scrapes the latest features from `geminicli.com/docs/changelogs`.
*   **Context Gathering**: Dives into `github.com/google-gemini/gemini-cli` to extract PR descriptions and linked issues for deeper context.
*   **AI-Powered Writing**: Utilizes the Google Gen AI SDK to generate well-structured, third-person reports including Feature Summaries, Context, How-Tos, and Demo Walkthroughs.
*   **REST API**: Includes a FastAPI backend to serve the generated reports and trigger synchronization.

## Prerequisites

*   Python 3.10+
*   [`uv`](https://github.com/astral-sh/uv) (Preferred for package and dependency management)
*   A Google AI Studio API key (`GOOGLE_API_KEY`)

## Setup

1.  **Clone the repository** (if you haven't already).
2.  **Set your API Key**:
    ```bash
    export GOOGLE_API_KEY="your_actual_api_key_here"
    ```
3.  **Install Dependencies using `uv`**:
    ```bash
    # This project uses uv for dependency management. See pyproject.toml / uv.lock
    uv sync
    ```

## Cloud Deployment (Automated)

The project includes an automated deployment script `scripts/deploy_gcp.sh` that provisions the necessary Google Cloud Platform (GCP) resources in correct dependency order.

To deploy the **Backend API** and the **Nightly Worker Job**, ensure you have the `gcloud` CLI installed and authenticated to your project, then run:

```bash
chmod +x scripts/deploy_gcp.sh
./scripts/deploy_gcp.sh YOUR_GCP_PROJECT_ID
```

**The script will automatically:**
1. Enable `run`, `secretmanager`, `firestore`, and `cloudscheduler` APIs.
2. Provision a Cloud Storage bucket for reports and a Firestore database for metadata.
3. Prompt you for an `ADMIN_API_KEY` and save it to GCP Secret Manager.
4. Deploy the FastAPI backend to Cloud Run (Allowing unauthenticated requests, injecting the secret).
5. Deploy the Orchestrator to Cloud Run Jobs.
6. Create a Cloud Scheduler trigger to run the job nightly at 2:00 AM.
7. Print out the final deployed URL of your API.

*Note: You will need to take the `API_URL` returned by the script and use it to configure where your independent Frontend web applications make their `fetch()` requests.*

## Usage

### 1. Running the Orchestrator (CLI Check)

The orchestrator script (`main.py`) checks for updates, coordinates the scraping, gathers the context, generates new reports, and saves them to the local `reports/` directory.

```bash
python main.py --check
```

### 2. Running the API Server

The FastAPI server (`api.py`) serves the generated reports over JSON and offers an endpoint to trigger new synchronization manually.

```bash
uv run uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```
*The server will start on `http://0.0.0.0:8000`.*

**Available Endpoints:**
*   `GET /api/reports`: Lists all generated reports and their status.
*   `GET /api/reports/{id}`: Retrieves the content of the report. **Security**: Requires an `Authorization: Bearer` header with the `ADMIN_API_KEY` to retrieve private admin notes; otherwise strips them.
*   `POST /api/reports/{id}/done`: Marks a given report as processed. **Security**: Requires `ADMIN_API_KEY`.
*   `POST /api/sync`: Manually triggers the update process. **Security**: Requires `ADMIN_API_KEY`.

## Project Structure

*   `main.py`: The CLI application entrypoint for syncing updates.
*   `api.py`: The FastAPI server entrypoint for serving reports.
*   `agents/`: Contains the logic for the different AI/Scraper components (`writer_agent.py`, `changelog_agent.py`, `github_agent.py`).
*   `utils/`: Helper modules (`scraper.py`, `storage.py`).
*   `reports/`: The local directory where generated unified reports and metadata are stored.
*   `static/`: Contains the pre-built `public` and `admin` static web frontends.

## Documentation

*   [System Design & Architecture](./architecture.md)

## Disclaimer

This is not an officially supported Google product.

## License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for details.
