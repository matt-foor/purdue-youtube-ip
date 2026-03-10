# YouTube IP V1

Public repo: `royayushkr/Youtube-IP-V1`  
Deployed app: `https://youtube-stats-ip.streamlit.app/`

This `README.md` is the only maintained documentation file for V1. Architecture notes, project briefs, and internal handoff notes that previously lived in other markdown files are intentionally consolidated here so the deployed V1 state and its internals are described in one place.

## What V1 Is

V1 is the stable, simpler Streamlit version of YouTube IP. It is centered around one primary dataset of research-oriented YouTube channels and exposes three main product surfaces:

- `Channel Analysis` for dataset-level analytics
- `Recommendations` for heuristic content guidance plus thumbnail generation
- `Ytuber` for cache-aware live channel analysis using the YouTube Data API

V1 does not use the extension framework, themed home page, brand kit, transcript analysis, or comment intelligence that exist in V2.

## Live App And Repo Entry Points

- Streamlit entrypoint: `dashboard/app.py`
- Sidebar navigation: `dashboard/components/sidebar.py`
- Main dataset used by the app: `data/youtube api data/research_science_channels_videos.csv`
- Local thumbnail output directory: `outputs/thumbnails/`

If you open the deployed V1 app, it is running the code path described in this file.

## Runtime Flow

V1 follows a small, direct request flow:

1. Streamlit starts at `dashboard/app.py`.
2. The app inserts the project root into `sys.path` so `dashboard` and `src` imports work in local runs and Streamlit Cloud.
3. `dashboard/components/sidebar.py` renders a radio selector with `Channel Analysis`, `Recommendations`, `Ytuber`, and `Deploy Notes`.
4. The selected page dispatches to one of the render functions under `dashboard/views/`.
5. `Channel Analysis` and `Recommendations` read from the local CSV dataset only.
6. `Ytuber` first checks the local dataset for the requested channel and only calls the YouTube API if cache data is missing or `Force API refresh` is enabled.
7. AI features call Gemini or OpenAI only when the user explicitly presses a button.

## User-Facing Pages

### `Channel Analysis`

File: `dashboard/views/channel_analysis.py`

This page is dataset-only. It loads `research_science_channels_videos.csv`, converts `views`, `likes`, and `comments` to numeric, parses `video_publishedAt`, and computes these derived fields in memory:

- `engagement_rate = (likes + comments) / max(views, 1)`
- `publish_month`
- `publish_day`

It then exposes:

- channel filters
- date range filter
- KPI cards for videos, channels, views, average views, and median engagement
- top channels table
- monthly video and view trend
- top videos table
- publish-day performance table

No writes happen on this page. It is read-only analytics over the local CSV.

### `Recommendations`

File: `dashboard/views/recommendations.py`

This page has two separate functions.

The first half is a data recommendation engine built entirely on the local CSV. It:

- computes `engagement_rate`, `title_length`, and `publish_day`
- selects a benchmark channel or all channels
- takes the top quartile by views as the "high-performing" sample
- extracts recurring title keywords after a simple stopword pass
- recommends a best publishing day and approximate title length
- shows reference videos to model

The second half is the thumbnail generator UI. It:

- lets the user choose `gemini` or `openai`
- reads API keys from `.env` if available, or from the password field in the UI
- builds a structured thumbnail prompt from title, context, style, and negative prompt
- requests images through `src/llm_integration/thumbnail_generator.py`
- saves generated images to `outputs/thumbnails/`
- exposes `Download` buttons for the generated files

### `Ytuber`

File: `dashboard/views/ytuber.py`

This is the most important runtime module in V1. It combines local cache usage, live YouTube API fetches, metric derivation, and AI generation in one page.

The page flow is:

1. Read `YOUTUBE_API_KEY` from the environment or input box.
2. Accept a channel handle, channel name, or channel ID.
3. Resolve the input to a canonical YouTube `channel_id` with `search.list`.
4. Check the local dataset for rows that already belong to that channel.
5. If recent cached rows exist and refresh is not forced, use them.
6. Otherwise fetch the channel record, uploads playlist, and up to 1 year of recent videos from the YouTube API.
7. Transform API responses into the dataset row schema.
8. Deduplicate against existing `video_id` values.
9. Append only new rows to `data/youtube api data/research_science_channels_videos.csv`.
10. Store the loaded channel dataframe and metadata in `st.session_state`.

#### `Ytuber` Session State Keys

After a successful load, V1 stores:

- `ytuber_channel_df`
- `ytuber_channel_title`
- `ytuber_channel_id`
- `ytuber_source`
- `ytuber_keyword_hints`

These keys allow tabs to reuse the same loaded channel without re-fetching.

#### `Ytuber` Runtime-Derived Metrics

After a channel is loaded, V1 computes:

- `engagement_rate`
- `publish_month`
- `publish_day`
- `publish_hour`
- `duration_seconds`
- `is_short`

#### `Ytuber` Tabs In V1

- `Overview`
  Shows one-year KPIs, a monthly trend chart, and the top-performing videos table.
- `Channel Audit`
  Computes consistency score, average upload gap, 90-day view growth, outlier rate, and shorts ratio.
- `Keyword Intel`
  Tokenizes titles and calculates a heuristic keyword opportunity table based on views, engagement, and frequency.
- `Title & SEO Lab`
  Scores a draft title and description using heuristics such as keyword presence, length, and structure.
- `Competitor Benchmark`
  Loads competitor channels through the same cache/API path and compares one-year metrics.
- `Trend Radar`
  Compares keyword mentions in the last 60 days versus the previous 60 days.
- `Content Planner`
  Recommends best publish day and hour and generates a 4-week schedule.
- `AI Studio`
  Uses Gemini text generation for planning outputs and Gemini image generation for thumbnails.

## Data Model Used By The App

The app expects a flat per-video CSV schema with both channel-level and video-level fields in each row. The most important columns are:

- channel identity: `channel_id`, `channel_title`, `channel_handle_used`
- channel stats: `channel_subscriberCount`, `channel_viewCount`, `channel_videoCount`
- video identity: `video_id`, `video_title`, `video_description`
- publish and engagement fields: `video_publishedAt`, `views`, `likes`, `comments`, `duration`
- taxonomy and metadata: `video_tags`, `video_topicCategories`, `video_topicIds`
- thumbnails: `thumb_default_*`, `thumb_medium_*`, `thumb_high_*`, `thumb_standard_*`, `thumb_maxres_*`

V1 does not maintain a normalized relational store. The CSV is both the analytics source and the cache layer for live channel fetches.

## AI And API Integrations

### YouTube Data API

Used by:

- `dashboard/views/ytuber.py`
- dataset build scripts in `scripts/`
- `scripts/yt_api_smoketest.py`

The page and scripts both use the same basic API shape:

- resolve channel
- fetch channel details
- read uploads playlist
- fetch video details in batches of 50
- retry transient failures with exponential backoff

### Gemini And OpenAI

File: `src/llm_integration/thumbnail_generator.py`

This is the active image-generation integration in V1. It exposes:

- `ThumbnailGenerator`
- `GeneratedImage`
- `get_api_key(provider)`

Supported providers:

- `gemini` via `generateContent`
- `openai` via `images/generations`

`Ytuber` also sends direct Gemini text requests for titles, scripts, hooks, and strategy outputs. Those text calls happen inside `dashboard/views/ytuber.py`, not through a separate client abstraction.

## Repository Map

### Files Actively Used By The Deployed V1 App

- `dashboard/app.py`
  Manual router for the Streamlit app.
- `dashboard/components/sidebar.py`
  Sidebar UI and key reminders.
- `dashboard/views/channel_analysis.py`
  Dataset KPI and trend page.
- `dashboard/views/recommendations.py`
  Recommendation engine plus thumbnail generation UI.
- `dashboard/views/ytuber.py`
  Cache-aware live channel intelligence page.
- `src/llm_integration/thumbnail_generator.py`
  Shared image generation provider wrapper.
- `data/youtube api data/research_science_channels_videos.csv`
  Primary dataset and channel cache used by the UI.

### Shared Pipeline Files Present In The Repo

- `scripts/build_category_dataset.py`
  YouTube API extractor for category datasets.
- `scripts/build_fitness_dataset.py`
  Fitness-focused extractor.
- `scripts/build_research_dataset.py`
  Research/science extractor used for the main shipped dataset.
- `scripts/yt_api_smoketest.py`
  Quick smoke test against the YouTube API.
- `src/data_collection/*.py`
  Earlier collection helpers from the original project scaffold.
- `src/data_processing/*.py`
  Text cleaning and feature engineering helpers.
- `src/modeling/*.py`
  BERTopic and topic-modeling scaffolding.
- `src/llm_integration/content_generator.py`
  Legacy content-generation scaffold, not the primary V1 UI path.
- `src/llm_integration/gpt4_client.py`
  Legacy OpenAI text helper, not the main deployed V1 runtime path.
- `dashboard/components/visualizations.py`
  Present but currently empty and not wired into the deployed app.
- `config/config.yaml`
  Present from the original scaffold and currently empty.
- `config/logging_config.yaml`
  Present from the original scaffold and currently empty.

## Environment Variables

V1 can run entirely from local `.env` values or from Streamlit secret values.

Required for full functionality:

- `YOUTUBE_API_KEY`
- `GEMINI_API_KEY`

Optional:

- `OPENAI_API_KEY`

Template:

```bash
cp .env.example .env
```

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m streamlit run dashboard/app.py
```

## Deployment

The currently intended V1 deployment target is:

- `https://youtube-stats-ip.streamlit.app/`

Recommended Streamlit settings:

- Repository: `royayushkr/Youtube-IP-V1`
- Branch: `main`
- Main file path: `dashboard/app.py`

Required Streamlit secrets:

- `YOUTUBE_API_KEY`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY` if you want OpenAI image generation available

## Outputs And Files Written At Runtime

V1 writes to disk in a few specific places:

- `data/youtube api data/research_science_channels_videos.csv`
  Appended to when `Ytuber` fetches new channel rows from the YouTube API.
- `outputs/thumbnails/`
  Receives generated thumbnail images from `Recommendations` and `Ytuber`.

V1 does not create a database. Persistence is file-based.

## Troubleshooting

- If Streamlit says `No module named dashboard` or `No module named src`, confirm you are launching from the project root and using `dashboard/app.py`.
- If `dotenv` is missing, `Recommendations` still runs because the import is guarded.
- If `googleapiclient` is missing, `Ytuber` exits early with an install message.
- If the YouTube API quota is exhausted, `Ytuber` falls back to cached rows when available.
- If Gemini or OpenAI calls fail, confirm the key, model name, and provider selection.

## Documentation Policy

This repository intentionally keeps runtime and internal documentation in this file only. If architecture, deployment, or maintenance notes need to change, update `README.md` instead of creating parallel markdown documents.
