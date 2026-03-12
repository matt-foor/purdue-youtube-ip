# YouTube IP V3

YouTube IP V3 is a Streamlit application for YouTube research, benchmarking, live channel analysis, outlier discovery, and AI-assisted planning. It combines bundled CSV datasets with live YouTube Data API requests and optional Gemini/OpenAI generation so one app can cover historical benchmarking, channel diagnostics, idea research, and creative asset prototyping.

Live app:

- https://youtube-ip-v3.streamlit.app/

This README documents the current deployed app as it exists in this repository, including:

- what the product does
- which files power each feature
- how the app is wired together
- what data sources and API keys it uses
- how to run it locally
- how to deploy it on Streamlit Community Cloud
- what parts of the repo are active versus legacy scaffolding

## Product Overview

The app currently exposes five sidebar destinations:

| Page | Purpose | Main File |
| --- | --- | --- |
| `Channel Analysis` | Portfolio-level analytics across the bundled datasets | `dashboard/views/channel_analysis.py` |
| `Recommendations` | Dataset-backed publishing guidance and thumbnail generation | `dashboard/views/recommendations.py` |
| `Ytuber` | Live creator workspace for one channel at a time | `dashboard/views/ytuber.py` |
| `Outlier Finder` | Standalone niche research and outlier-video discovery | `dashboard/views/outlier_finder.py` |
| `Deployment` | Run/deploy notes shown inside the app | `dashboard/app.py` |

At a high level, the app is designed for three use cases:

1. Analyze existing cross-channel datasets to understand benchmark patterns.
2. Pull live stats for a public channel and turn them into creator-focused diagnostics.
3. Generate strategy and creative suggestions with Gemini or OpenAI using the same public data.

## What The App Includes

### 1. Channel Analysis

`Channel Analysis` is the dataset-backed analytics view.

It can:

- load one category dataset or all committed datasets together
- filter by channel and published-date range
- show KPI summaries for videos, channels, views, average views, and median engagement
- surface top channels by total views
- chart monthly upload trends
- list best-performing videos
- compare publishing-day performance
- visualize views versus engagement

Code:

- `dashboard/views/channel_analysis.py`
- `dashboard/components/visualizations.py`

Data source:

- committed CSV files in `data/youtube api data/`

### 2. Recommendations

`Recommendations` turns the same bundled datasets into lightweight strategy guidance.

It can:

- benchmark a selected category or all categories
- compute a high-performing sample from the top quartile of videos
- suggest publish timing and title length targets
- extract keyword angles from strong titles
- show reference videos to model
- generate thumbnail concepts with Gemini or OpenAI

Code:

- `dashboard/views/recommendations.py`
- `src/llm_integration/thumbnail_generator.py`

### 3. Ytuber

`Ytuber` is the live creator workspace for one public channel.

It can:

- resolve a handle, channel name, or channel ID
- pull fresh channel and recent-video metadata from the YouTube Data API
- cache channel fetches in the local CSV-backed dataset
- compute a channel overview and audit
- generate keyword intelligence from recent uploads
- score titles and descriptions in `Title And SEO Lab`
- benchmark competitors and generate comparative recommendations
- plan content around day/hour performance patterns
- run `AI Studio` for titles, ideas, scripts, clips, and thumbnail generation
- hand off into the standalone `Outlier Finder`

Key modules inside the page:

- `AI Studio`
- `Overview`
- `Channel Audit`
- `Keyword Intel`
- `Outliers Finder` shortcut
- `Title And SEO Lab`
- `Competitor Benchmark`
- `Content Planner`

Code:

- `dashboard/views/ytuber.py`
- `src/utils/api_keys.py`
- `src/llm_integration/thumbnail_generator.py`

### 4. Outlier Finder

`Outlier Finder` is a standalone niche-research page in the sidebar. It is designed to find videos that are overperforming relative to channel size, age, peers, or channel baseline within the scanned cohort returned by the official YouTube API.

It supports:

- niche / keyword search
- timeframe filters
- region and language filters
- language strictness
- duration preference
- minimum views
- subscriber bucket and explicit min/max subscriber filters
- include/exclude hidden subscriber counts
- exact-phrase versus broad matching
- exclude keywords
- bounded search depth and baseline-enrichment settings

Its results-first workflow is:

1. `Top Outliers In This Scan`
2. `Breakout Snapshot`
3. `AI Research`
4. `How This Works`

The page also includes:

- sortable outlier results
- explanation strings for why each video is an outlier
- score and scan summary cards
- breakout charts for age, duration, title pattern, and language quality
- structured AI report cards via Gemini/OpenAI
- an inline methodology section explaining metrics and caveats

Code:

- `dashboard/views/outlier_finder.py`
- `src/services/outliers_finder.py`
- `src/services/outlier_ai.py`

## Current Runtime Architecture

### App Entrypoints

There are two Streamlit entrypoints:

- `streamlit_app.py`
  - root deployment entrypoint used by Streamlit Cloud
  - simply imports `dashboard.app`
- `dashboard/app.py`
  - real application shell
  - configures Streamlit page settings
  - injects the shared theme
  - renders the sidebar
  - routes to each page

### Shared UI Layer

- `dashboard/components/sidebar.py`
  - branded sidebar navigation using `streamlit-option-menu`
- `dashboard/components/theme.py`
  - shared app theme, CSS tokens, page widths, button styling, and general chrome
- `dashboard/components/visualizations.py`
  - reusable Plotly chart helpers, dataframe styling, keyword chips, KPI rows, and section headers

### Active Service Layer

The current active backend logic is concentrated in a small number of files:

- `src/utils/api_keys.py`
  - reads API keys from environment variables and Streamlit secrets
  - supports single-key and pooled-key modes
  - rotates keys per provider in session state
  - retries operations across configured keys

- `src/services/outliers_finder.py`
  - core outlier-search request and scoring engine
  - YouTube API orchestration for search, videos, channels, and baseline fetches
  - language confidence heuristics
  - duration and age bucketing
  - peer percentile and baseline-based scoring
  - cache wrappers for niche scans and channel baselines

- `src/services/outlier_ai.py`
  - converts outlier results into structured AI research cards
  - calls Gemini or OpenAI
  - expects JSON output and falls back gracefully if parsing fails

- `src/llm_integration/thumbnail_generator.py`
  - Gemini and OpenAI image-generation wrapper
  - used by the Recommendations page and `Ytuber -> AI Studio`

### Data Flow

There are two main data flows in the app:

#### A. Dataset-backed analytics

```text
Bundled CSV datasets
-> pandas loading/cleaning in page views
-> dashboard/components/visualizations.py
-> Channel Analysis / Recommendations UI
```

#### B. Live API-backed creator workflows

```text
Streamlit secrets / env vars
-> src/utils/api_keys.py
-> YouTube API or Gemini/OpenAI calls
-> page-specific transformations in Ytuber / Outlier Finder
-> charts, result cards, and AI panels in the Streamlit UI
```

## Repository Map

This is the practical repository layout, not just the nominal one:

```text
.
├── dashboard/
│   ├── app.py                       # Main Streamlit router
│   ├── components/
│   │   ├── sidebar.py               # Sidebar navigation
│   │   ├── theme.py                 # Shared dark/purple theme
│   │   └── visualizations.py        # Plotly + dataframe helpers
│   └── views/
│       ├── channel_analysis.py      # Dataset analytics page
│       ├── recommendations.py       # Recommendations + thumbnail studio
│       ├── ytuber.py                # Live creator workspace
│       └── outlier_finder.py        # Standalone niche research page
├── data/
│   └── youtube api data/            # Bundled CSV datasets used by the app
├── docs/
│   ├── ARCHITECTURE.md              # Original architecture note
│   └── PROJECT_BRIEF.md             # Original project brief
├── outputs/
│   └── thumbnails/                  # Generated image outputs
├── scripts/
│   ├── yt_api_smoketest.py          # Rich YouTube API smoke test
│   ├── build_*_dataset.py           # Dataset builder scripts
│   └── available_data_constraints.md
├── src/
│   ├── services/                    # Active outlier + AI service layer
│   ├── utils/                       # API-key management and helpers
│   ├── llm_integration/             # Thumbnail generation wrapper
│   ├── data_collection/             # Mostly legacy / empty scaffolding
│   ├── data_processing/             # Partial older scaffolding
│   └── modeling/                    # Partial older scaffolding
├── tests/
│   ├── integration/                 # Integration tests
│   └── unit/                        # Unit tests
├── streamlit_app.py                 # Root Streamlit Cloud entrypoint
├── requirements.txt                 # Python dependencies
└── .streamlit/config.toml           # Theme config
```

## What Is Active Versus Historical Scaffolding

This repo has evolved over time. The currently deployed app does **not** use every folder equally.

### Actively used by the app today

- `dashboard/`
- `src/services/`
- `src/utils/api_keys.py`
- `src/llm_integration/thumbnail_generator.py`
- `data/youtube api data/`
- `tests/unit/test_outliers_finder.py`
- `tests/unit/test_outlier_ai.py`
- `tests/integration/test_pipeline.py`

### Present in the repo but only partially used or currently inactive

- `src/data_collection/`
- `src/modeling/`
- `src/llm_integration/content_generator.py`
- `src/llm_integration/gpt4_client.py`
- parts of `src/data_processing/`

Several of these files are empty or legacy placeholders from the original research-project structure. The README reflects the code that powers the live app today, not every historical idea in the repo.

## Bundled Data Assets

The repository currently ships with four CSV datasets under `data/youtube api data/`.

| Dataset | Rows | Columns |
| --- | ---: | ---: |
| `entertainment_channels_videos.csv` | 101,554 | 54 |
| `gaming_channels_videos.csv` | 95,534 | 54 |
| `research_science_channels_videos.csv` | 221,325 | 54 |
| `tech_channels_videos.csv` | 125,693 | 54 |

Total bundled rows: **544,106**

These datasets power:

- `Channel Analysis`
- the dataset-backed parts of `Recommendations`
- parts of the `Ytuber` page when appending live fetches into the working CSV-backed flow

## Secrets, Environment Variables, And API-Key Pools

The app supports both single keys and pooled keys.

Supported provider groups:

- `youtube`
- `gemini`
- `openai`

### Preferred pooled-key format

Environment variables:

```bash
YOUTUBE_API_KEYS=key_1,key_2
GEMINI_API_KEYS=key_1,key_2
OPENAI_API_KEYS=key_1,key_2
```

Streamlit secrets:

```toml
YOUTUBE_API_KEYS = ["key_1", "key_2"]
GEMINI_API_KEYS = ["key_1", "key_2"]
OPENAI_API_KEYS = ["key_1", "key_2"]
```

### Supported single-key fallbacks

- `YOUTUBE_API_KEY`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`

### How key rotation works

`src/utils/api_keys.py` does the following:

- reads values from Streamlit secrets first, then environment variables
- accepts JSON-style lists, comma-separated strings, line-delimited strings, or indexed secret names
- deduplicates the final list
- stores a session-level cursor for each provider
- retries operations across all configured keys when failures are retryable

This matters most for:

- live YouTube fetches in `Ytuber`
- outlier scans in `Outlier Finder`
- Gemini/OpenAI generation in `AI Studio`, `Recommendations`, and Outlier AI reports

## Local Development

### Prerequisites

- Python 3.10 or newer
- valid YouTube Data API credentials for live features
- Gemini and/or OpenAI credentials for AI features

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure local secrets

Copy:

```bash
cp .env.example .env
```

Then populate:

- `YOUTUBE_API_KEYS`
- `GEMINI_API_KEYS`
- `OPENAI_API_KEYS`

Example:

```bash
YOUTUBE_API_KEYS=your_youtube_key_1,your_youtube_key_2
GEMINI_API_KEYS=your_gemini_key_1,your_gemini_key_2
OPENAI_API_KEYS=your_openai_key_1,your_openai_key_2
```

Local Streamlit-style secrets are also supported via `.streamlit/secrets.toml`.

Reference file:

- `.streamlit/secrets.toml.example`

### Run the app

Preferred:

```bash
streamlit run streamlit_app.py
```

Alternate:

```bash
streamlit run dashboard/app.py
```

## Streamlit Community Cloud Deployment

This repo is structured to deploy directly from GitHub to Streamlit Community Cloud.

Current deployed app:

- https://youtube-ip-v3.streamlit.app/

### Streamlit app settings

- Repo: `royayushkr/Youtube-IP-V3`
- Branch: `main`
- Main file path: `streamlit_app.py`

### Required secrets

```toml
YOUTUBE_API_KEYS = ["your_youtube_key_1", "your_youtube_key_2"]
GEMINI_API_KEYS = ["your_gemini_key_1", "your_gemini_key_2"]
OPENAI_API_KEYS = ["your_openai_key_1", "your_openai_key_2"]
```

Single-key fallbacks still work if needed.

### Theme

The live app theme is defined in `.streamlit/config.toml`:

- `primaryColor = "#8B5CF6"`
- `backgroundColor = "#090B14"`
- `secondaryBackgroundColor = "#141A31"`
- `textColor = "#F7F8FC"`

## Outlier Finder Methodology Summary

Outlier Finder is one of the most custom parts of the app, so it deserves a direct summary here.

### What it measures

The outlier score is a weighted mix of:

- channel-baseline lift
- peer percentile
- engagement percentile
- recency boost

### Key derived metrics

- `Views Per Day`
  - views divided by video age in days
- `Views Per Subscriber`
  - views normalized by channel subscriber count when public
- `Peer Percentile`
  - performance relative to the scanned cohort
- `Baseline Component`
  - how far the video is running above the channel's recent baseline
- `Language Confidence`
  - heuristic score based on metadata and title script

### Practical constraints

- results come from the scanned cohort returned by YouTube search, not the entire platform
- YouTube search is ranked and sampled
- subscriber counts may be hidden or rounded
- language filtering is heuristic, not guaranteed
- there is no access to impressions, CTR, watch time, or retention from the public API

### Current cache behavior

- niche query cache: 1 hour
- channel baseline cache: 6 hours

## AI Integrations

### Outlier AI Research

`src/services/outlier_ai.py` converts outlier results into structured research cards with:

- executive headline
- key takeaway
- confidence label and notes
- breakout themes
- title patterns
- repeatable angles
- notable anomalies
- next steps
- warnings

Provider support:

- Gemini
- OpenAI

### Thumbnail Generation

`src/llm_integration/thumbnail_generator.py` supports:

- Gemini image generation
- OpenAI image generation via the Images API

It exposes controls for:

- model
- count
- size
- quality
- background
- output format

Generated files are saved under `outputs/thumbnails/`.

## Scripts

The `scripts/` directory includes the repo's operational utilities.

### `scripts/yt_api_smoketest.py`

A richer smoke test for the public YouTube Data API. It checks:

- channel discovery
- channel details
- uploads playlist traversal
- video details
- video categories
- sample comments

Use it when validating that a YouTube API key is working and returning the expected response shapes.

### `scripts/build_*_dataset.py`

These scripts build the CSV datasets for different categories:

- `build_category_dataset.py`
- `build_fitness_dataset.py`
- `build_research_dataset.py`

They are useful if you want to refresh or regenerate the bundled datasets outside the Streamlit app.

### `scripts/available_data_constraints.md`

Documents what the public YouTube API can and cannot provide, and how those limitations should influence product design and interpretation.

## Tests

The current test suite includes:

- `tests/unit/test_outliers_finder.py`
  - verifies scoring behavior, ordering, scan quality summaries, and presentational helpers
- `tests/unit/test_outlier_ai.py`
  - verifies JSON extraction, report mapping, and fallback behavior
- `tests/integration/test_pipeline.py`
  - verifies outlier search flow with mocked API responses and advanced filters
- `tests/unit/test_text_processing.py`
- `tests/unit/test_data_collection.py`

Run:

```bash
python3 -m pytest
```

## Known Limitations

This app is intentionally pragmatic, not a full YouTube intelligence platform with first-party creator analytics.

Important limitations:

- all live research is limited to public YouTube metadata
- YouTube API search quota is expensive, especially `search.list`
- Outlier Finder is not an exhaustive rank tracker
- language, geography, and subscriber-based filters are best-effort
- some legacy folders in `src/` are still placeholders and do not reflect the live dashboard architecture

## Supporting Documentation

- `docs/ARCHITECTURE.md`
  - original high-level architecture note
- `docs/PROJECT_BRIEF.md`
  - original academic project brief
- `CONTRIBUTING.md`
  - contribution guidelines
- `SECURITY.md`
  - private reporting guidance for vulnerabilities
- `LICENSE`
  - MIT license

## Contribution And Maintenance Notes

If you change behavior or configuration:

- update the relevant view/service code
- update tests if the behavior is observable
- update this README if setup, deployment, or feature scope changed

For UI changes, include screenshots in pull requests as noted in `CONTRIBUTING.md`.

## License

MIT License. See `LICENSE`.
