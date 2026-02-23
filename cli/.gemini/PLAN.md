# STRATEGY PLAN: "What's New in Gemini CLI" Helper App

## 1. Objective
Automate the extraction, synthesis, and content generation of new Gemini CLI features from changelogs, pull requests, and issues. The goal is to produce comprehensive reports (Walkthroughs, How-to guides, Feature summaries) for the user to try out features and create weekly blog/video content.

## 2. Strategic Analysis
*   **First Principles**: To provide an actionable guide for a new feature, the agent needs the historical context (the Bug/Issue), the technical implementation details (the PR description and code changes), and the release context (the Changelog). An AI agent can synthesize this raw data into structured learning materials.
*   **Trade-offs**: 
    *   *Scheduling*: Local Cron vs. GitHub Actions. GitHub Actions is preferable for a reliable nightly/weekly job that doesn't depend on the user's local machine being awake.
    *   *Scraping vs. API*: The changelog is on a website (`geminicli.com/docs/changelogs/`), requiring HTML parsing. PRs and Issues are on GitHub, requiring API access.
*   **Risks**: 
    *   GitHub API rate limiting (requires an authenticated Personal Access Token).
    *   Changelog HTML structure changes breaking the scraper.
    *   LLM context window limits if PR threads are massively long (mitigated by Gemini's large context windows).

## 3. Design Specification
*   **Tech Stack**: Python, managed by `uv`. 
*   **Libraries**:
    *   `google-genai`: For agentic synthesis and generation.
    *   `PyGithub` or `httpx`: For GitHub API interactions.
    *   `beautifulsoup4` & `httpx`: For scraping the changelog website.
    *   `pydantic`: For structured data extraction and agent response parsing.
*   **Data Flow**:
    1.  **Changelog Monitor Agent**: Fetches `https://geminicli.com/docs/changelogs/`, parses the latest release, and extracts PR numbers (e.g., `#17698`, `#18324`).
    2.  **GitHub Context Agent**: Uses GitHub API to fetch PR descriptions, comments, and linked issue data for each extracted PR number.
    3.  **Synthesis Agent**: Feeds the raw PR/Issue text into Gemini to understand "Before vs. After" and the technical context.
    4.  **Content Creator Agent**: Generates the final markdown assets: Walkthrough guide, How-to guide, Background guide, and Feature summary.
*   **State Management**: A local `state.json` or SQLite DB to track processed PRs/Releases, ensuring the nightly job only processes *new* changelog items.

## 4. Alternatives Considered
*   *Node.js / TypeScript*: Node.js is excellent for scripting and has the `@google/genai` SDK. Python was chosen because its ecosystem for data extraction (BeautifulSoup, Pydantic) and AI agent orchestration is highly mature, and `uv` provides blazing-fast dependency management. Both are valid according to the workspace guidelines.
*   *RSS Feeds*: If the changelog has an RSS feed, we could use that instead of HTML scraping. This should be investigated during implementation.

## 5. Implementation Roadmap
- [x] **Step 1: Project Initialization**: Set up the Python project with `uv init`, configure `.env` for `GITHUB_TOKEN` and `GEMINI_API_KEY`.
- [x] **Step 2: Changelog Scraper**: Implement a module to fetch and parse `https://geminicli.com/docs/changelogs/` to extract recent release notes and associated PR numbers.
- [x] **Step 3: GitHub Extractor**: Implement a module using the GitHub API to fetch PR details, diff summaries, and linked issue conversations for a given PR number.
- [x] **Step 4: AI Agent Orchestration**: Build the `google-genai` prompts and Pydantic output schemas to synthesize the raw GitHub data into structured context.
- [ ] **Step 5: Content Generation**: Create the prompt pipeline to generate the final assets (Walkthrough, How-To, Background, Summary) and save them as Markdown files.
- [ ] **Step 6: State & Scheduling**: Implement local state tracking (e.g., `processed_prs.json`) to prevent duplicate work, and set up a basic runner script for cron/GitHub Actions.

## 6. Review
Please review the proposed architecture, tech stack (Python/uv), and the steps in the roadmap. Let me know if you would like to adjust the scheduling approach or the specific formats of the generated content.
