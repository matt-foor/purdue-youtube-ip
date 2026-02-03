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