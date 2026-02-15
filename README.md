# Purdue YouTube Intelligence Platform

An end-to-end analytics and recommendation system that leverages public YouTube metadata and LLMs to help creators plan high-impact content strategies.

## Overview
Small-to-mid-tier creators often lack cross-channel intelligence and actionable insights. This project fills that gap by combining scalable public data collection with modern NLP and LLM-assisted recommendations to deliver channel-specific strategy guidance.

## Project Brief
The full business context, goals, scope, deliverables, and schedule live in `docs/PROJECT_BRIEF.md`.

## Solution Summary
- **Collect** public channel/video metadata and captions
- **Process** and clean data for analysis
- **Model** topics and patterns that correlate with engagement
- **Recommend** titles, topics, thumbnails, and posting strategy
- **Deliver** results via an interactive Streamlit dashboard

## Tech Stack
- **Python 3.10+** for data collection, processing, and modeling
- **YouTube Data API v3** for public metadata
- **BERTopic** for topic modeling and semantic patterns
- **GPT-4 API** for content ideation and strategic recommendations
- **Streamlit** for interactive insights delivery

## System Architecture
See `docs/ARCHITECTURE.md` for the component map and data flow.

## Data Sources
- **YouTube Data API v3:** titles, tags, views, likes, comments, channel data
- **Public captions:** NLP inputs for semantic modeling
- **Google Trends (optional):** external signal for topic validation

## Repository Structure
```
.
├── config/                 # Project configuration
├── dashboard/              # Streamlit app and UI components
├── data/                   # Raw and processed data (gitignored)
├── docs/                   # Architecture and project brief
├── notebooks/              # Exploration, modeling, and reporting notebooks
├── outputs/                # Figures, reports, and models (gitignored)
├── src/                    # Core Python package
│   ├── data_collection/    # API clients and scrapers
│   ├── data_processing/    # Cleaning and feature engineering
│   ├── llm_integration/    # GPT-4 integration
│   ├── modeling/           # BERTopic and modeling logic
│   └── utils/              # Helpers and logging
└── tests/                  # Unit and integration tests
```

## Getting Started
### Prerequisites
- Python 3.10+
- YouTube Data API key
- OpenAI API key

### Setup
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables
Copy and edit:
```bash
cp .env.example .env
```
Then populate with your credentials (do not commit `.env`).

### Run the Dashboard
```bash
streamlit run dashboard/app.py
```

### Run Tests
```bash
pytest
```

## Configuration
Project-level configuration lives in `config/config.yaml`. Logging is configured in `config/logging_config.yaml`.

## Visual Analytics
Place generated visuals in `outputs/figures/` and link them here. Recommended artifacts:
- **Channel Performance Summary:** engagement vs. frequency
- **Topic Clusters:** BERTopic 2D embeddings and top keywords
- **Recommendation Impact:** before/after mock strategy uplift

## Ethics and Compliance
- Respect YouTube API Terms of Service
- Do not store or share personally identifiable information (PII)
- Publish only aggregated or anonymized insights

## Contributing
See `CONTRIBUTING.md` for standards and workflow.

## License
MIT License. See `LICENSE`.
## Thumbnail Dashboard (Deployable)
A Streamlit dashboard is available at `dashboard/app.py` with:
- **Thumbnail Generator** page (Gemini + OpenAI providers)
- **Dataset Overview** page for `data/youtube api data/research_science_channels_videos.csv`

### Required Env Vars
- `GEMINI_API_KEY` for Gemini image generation
- `OPENAI_API_KEY` for OpenAI image generation (optional fallback)

Use `.env.example` as a template.

### Run Dashboard
```bash
source .venv/bin/activate
streamlit run dashboard/app.py
```

### Deploy on Streamlit Cloud
1. Push repo to GitHub.
2. Create app with entrypoint: `dashboard/app.py`.
3. Add secrets in Streamlit: `GEMINI_API_KEY`, `OPENAI_API_KEY`.

## Creator Suite V2 (Current App)
The app now includes a full creator operating system experience with modular tools, API-backed analytics, and AI generation workflows.

### Core V2 Features
- **Website-style App Shell:** custom theme, polished home page, and modular navigation.
- **Extension Framework:** enable/disable modules from the in-app Extension Center (`config/extensions.json`).
- **Ytuber (Advanced Suite):**
  - Cache-aware channel loading (dataset-first, API fallback)
  - Last-1-year channel intelligence and KPI dashboards
  - Channel audit (consistency, growth, outlier rate, shorts mix)
  - Keyword intelligence and opportunity scoring
  - Title/description SEO scoring
  - Title A/B lab with automated scoring
  - Competitor benchmarking and content gap finder
  - Trend radar + Google Trends + optional News signals
  - Comment intelligence and sentiment signals
  - Transcript lab and AI retention/script improvement
  - Content planner (best day/hour + 4-week calendar)
  - Thumbnail critic (image diagnostics + Gemini visual critique)
  - Brand kit memory (tone, audience, visual style, banned words)
  - AI Studio for titles, descriptions, scripts, hooks, and thumbnails
- **Recommendations Page:** data-driven content guidance + thumbnail generation workflows.
- **Channel Analysis Page:** filtered analytics, top videos/channels, and publishing performance insights.

### Updated Environment Variables
Use `.env.example` and include what you need:
- `YOUTUBE_API_KEY` (required for live YouTube sync in Ytuber)
- `GEMINI_API_KEY` (required for Gemini generation workflows)
- `OPENAI_API_KEY` (optional fallback for image generation)
- `NEWSAPI_KEY` (optional for News signal feed in Trend APIs)

### How To Use (Suggested Workflow)
1. Open **Home** for suite overview.
2. Go to **Ytuber** and load a channel using `YOUTUBE_API_KEY`.
3. In **Keyword Intel** and **Title & SEO Lab**, identify target terms and optimize metadata.
4. Use **Content Gap Finder** + **Competitor Benchmark** to identify growth opportunities.
5. In **AI Studio**, generate titles/descriptions/scripts/thumbnails aligned to your Brand Kit.
6. Use **Content Planner** to schedule your next 4 weeks.
7. Use **Extension Center** to toggle tools based on your workflow.

### Local Run (Recommended)
```bash
cd "/Users/ayushkumar/Desktop/Youtube-IP"
source .venv/bin/activate
python3 -m streamlit run dashboard/app.py
```

### Streamlit Cloud Deploy (Private Repo Supported)
1. Create/select app in Streamlit Cloud.
2. Repo: your private GitHub repository.
3. Branch: `main`.
4. Main file path: `dashboard/app.py`.
5. Add required secrets (`YOUTUBE_API_KEY`, `GEMINI_API_KEY`, etc.).
6. Deploy or Reboot app.

### Troubleshooting
- **`ModuleNotFoundError`**: confirm dependencies in `requirements.txt` and reboot deployment.
- **Repository not found on Streamlit**: reconnect GitHub access and grant repo permissions.
- **No live data**: verify `YOUTUBE_API_KEY` and quota in Google Cloud.
- **AI generation fails**: verify Gemini/OpenAI key and selected model name.
