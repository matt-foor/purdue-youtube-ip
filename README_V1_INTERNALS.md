# YouTube IP Dashboard - V1 Internal Working (Teammate Handoff)

This document explains how V1 works internally so teammates can maintain, debug, and extend it safely.

## Scope (What this document refers to)
V1 in this project means the pre-V2 app state used in the original deployment repo:
- Repo: `royayushkr/Youtube-IP-private`
- Stable commit used for V1 rollback: `135e2f6`
- Streamlit entrypoint: `dashboard/app.py`

This doc maps to the code at that V1 commit, not the newer V2 modular suite.

## V1 Architecture (High-Level)
V1 is a Streamlit app with a simple manual router and three functional pages:
- `Channel Analysis`
- `Recommendations`
- `Ytuber`

Core design choice:
- Use a **local CSV dataset** as the default analytics source.
- Use **YouTube Data API** only when needed for live channel pulls (inside `Ytuber`).
- Use **Gemini/OpenAI APIs** for creative generation (thumbnails + AI content).

## Request/Render Flow (V1)
1. User opens Streamlit app (`dashboard/app.py`).
2. Sidebar returns selected page string.
3. App routes to `channel_analysis.render()`, `recommendations.render()`, or `ytuber.render()`.
4. Each page reads local CSV and/or calls APIs depending on user action.
5. `Ytuber` stores loaded channel data in `st.session_state` so tabs can reuse it without re-fetching.

## Key Files and Responsibilities (V1)
### App Shell
- `/Users/ayushkumar/Desktop/Youtube-IP/dashboard/app.py`
  - Streamlit entrypoint
  - Adds project root to `sys.path` (import path fix)
  - Routes sidebar choice to page render functions
- `/Users/ayushkumar/Desktop/Youtube-IP/dashboard/components/sidebar.py`
  - Renders left sidebar navigation and API-key setup hints

### Analytics / UI Pages
- `/Users/ayushkumar/Desktop/Youtube-IP/dashboard/views/channel_analysis.py`
  - Dataset analytics (filters, KPIs, trends, top videos, publish-day performance)
- `/Users/ayushkumar/Desktop/Youtube-IP/dashboard/views/recommendations.py`
  - Data-driven recommendations from dataset
  - Thumbnail generation UI (Gemini/OpenAI)
- `/Users/ayushkumar/Desktop/Youtube-IP/dashboard/views/ytuber.py`
  - Cache-aware channel loading via YouTube API + dataset
  - 1-year channel analytics
  - SEO/title scoring, competitor benchmarking, trend radar, content planner, AI Studio

### AI Integration
- `/Users/ayushkumar/Desktop/Youtube-IP/src/llm_integration/thumbnail_generator.py`
  - Provider abstraction for `gemini` and `openai`
  - Builds image prompt and returns decoded image bytes
  - Used by `Recommendations` and `Ytuber`

### Data Storage
- `/Users/ayushkumar/Desktop/Youtube-IP/data/youtube api data/research_science_channels_videos.csv`
  - Main local analytics/cache dataset
  - Used by all V1 pages
  - Also appended by `Ytuber` when new channel data is fetched

## V1 Data Model (Important Columns)
V1 relies on a unified channel+video row schema in the CSV. Commonly used fields:
- Channel fields:
  - `channel_id`, `channel_title`, `channel_subscriberCount`, `channel_viewCount`, `channel_videoCount`
- Video fields:
  - `video_id`, `video_title`, `video_description`, `video_publishedAt`, `views`, `likes`, `comments`, `duration`
- Thumbnails:
  - `thumb_*` columns (URL/width/height variants)
- Metadata:
  - `video_tags`, `video_topicCategories`, `video_topicIds`

Derived metrics computed at runtime (not stored initially in raw form):
- `engagement_rate`
- `publish_month`
- `publish_day`
- `publish_hour` (in `Ytuber`)
- `duration_seconds` and `is_short` (in `Ytuber`)

## Page-by-Page Internal Working
### 1) Channel Analysis (`dashboard/views/channel_analysis.py`)
Purpose:
- Provide a fast dataset-only analytics view for multiple channels.

How it works:
- Loads CSV from `DATASET_PATH`.
- Converts `views/likes/comments` to numeric.
- Parses `video_publishedAt` into UTC datetime.
- Computes:
  - `engagement_rate = (likes + comments) / max(views, 1)`
  - `publish_month`
  - `publish_day`
- Applies user filters:
  - channel multiselect
  - published date range
- Renders:
  - KPI metrics
  - top channels table
  - monthly trend line chart
  - top videos table
  - publish-day performance table

What teammates can safely change:
- Add new KPIs/tables/charts using derived fields.
- Change defaults for selected channels/date range.

Risk points:
- Empty/invalid CSV values causing dtype issues.
- Date parsing assumptions if schema changes.

### 2) Recommendations (`dashboard/views/recommendations.py`)
Purpose:
- Combine data-driven strategy hints with thumbnail generation.

How it works (analytics side):
- Loads same CSV dataset.
- Derives:
  - `engagement_rate`
  - `title_length`
  - `publish_day`
- Selects a benchmark channel (or all channels).
- Picks high-performing subset (top quartile by views).
- Extracts keyword angles from high-performing titles via regex + stopword filter.
- Computes quick heuristics:
  - best publish day
  - target title length
  - reference videos table

How it works (thumbnail generation side):
- User picks provider (`gemini` or `openai`).
- `ThumbnailGenerator` builds a prompt from title/context/style/negative prompt.
- Calls API and decodes image bytes.
- Saves generated images to `outputs/thumbnails/`.
- Provides `st.download_button` for each image.

Import/path behavior:
- Adds project root to `sys.path` to avoid `ModuleNotFoundError`.
- `dotenv` is optional (guarded import) so app does not crash if package is missing.

### 3) Ytuber (`dashboard/views/ytuber.py`) - V1 Internal Core
Purpose:
- Main “power user” page for channel intelligence + AI planning.
- This is the most important V1 component.

#### 3.1 Cache-first channel loading strategy
Key function:
- `_fetch_or_get_cached_channel(channel_query, youtube_api_key, force_refresh)`

Behavior:
1. Load local CSV dataset.
2. Normalize dtypes and derived fields (`_ensure_numeric_and_dates`).
3. Resolve `channel_query` -> `channel_id` using YouTube API search (`_resolve_channel_id`).
4. Compute 1-year cutoff (`now - 365 days`).
5. Check local dataset for rows with same `channel_id`.
6. If cached rows exist and `force_refresh=False`, return cached recent rows.
7. Otherwise call YouTube API to fetch channel + uploads playlist + recent videos.
8. Build rows in dataset schema and dedupe by `video_id` against existing dataset.
9. Append new rows to CSV.
10. Reload dataset and return channel rows (recent 1 year preferred).

Why this matters:
- Reduces YouTube API quota usage.
- Makes repeated analysis fast.
- Keeps local dataset improving over time.

#### 3.2 YouTube API fetch pipeline (inside Ytuber)
Main helper functions:
- `_yt_client()` -> build YouTube API client
- `_resolve_channel_id()` -> channel lookup by handle/name/ID
- `_fetch_channel_details()` -> channel metadata + related playlists
- `_fetch_recent_video_ids()` -> scan uploads playlist until 1-year cutoff
- `_fetch_videos_details()` -> batch `videos().list` calls in chunks of 50

Retry strategy:
- `_api_call_with_backoff()` handles transient API failures (`403/429/500/503`) with exponential backoff.

Data shaping helpers:
- `_channel_fields()` for channel columns
- `_video_row()` for video-level row construction
- `_extract_thumbnails()` for standardized thumbnail columns

#### 3.3 Ytuber derived analytics (V1)
Once channel data is loaded, V1 computes runtime features:
- `engagement_rate`
- `publish_month`, `publish_day`, `publish_hour`
- `duration_seconds`
- `is_short` (duration <= 60s)

These feed the analytics tabs below.

#### 3.4 Ytuber tabs in V1 (what each does)
V1 tabs (in order):
1. `Overview`
   - KPI metrics, monthly trend, top videos table
2. `Channel Audit`
   - upload consistency score, gap days, 90d growth, outlier rate
3. `Keyword Intel`
   - keyword scoring based on views, engagement, recency momentum, competition proxy
4. `Title & SEO Lab`
   - heuristic scoring for title and description quality
5. `Competitor Benchmark`
   - compare multiple channels (cache/API loaded per handle)
6. `Trend Radar`
   - recent keyword momentum (last 60 days vs previous 60 days)
7. `Content Planner`
   - best day/hour and a generated 4-week publishing calendar
8. `AI Studio`
   - Gemini text generation + Gemini thumbnail generation

#### 3.5 Ytuber session state keys (important for debugging)
`Ytuber` stores channel state in `st.session_state` after a successful load:
- `ytuber_channel_df`
- `ytuber_channel_title`
- `ytuber_channel_id`
- `ytuber_source` (`dataset_cache` or `youtube_api`)
- `ytuber_keyword_hints` (set after Keyword Intel tab runs)

If teammates see weird tab behavior, check whether these keys exist and whether `channel_df` is empty.

## AI / LLM Integration (V1)
### Thumbnail generation (`ThumbnailGenerator`)
File:
- `/Users/ayushkumar/Desktop/Youtube-IP/src/llm_integration/thumbnail_generator.py`

How it works:
- Builds a reusable thumbnail prompt from:
  - title
  - context
  - style
  - negative prompt
- Supports two providers:
  - `gemini` image generation endpoint (`generateContent` with image modality)
  - `openai` image generation endpoint (`/v1/images/generations`)
- Returns decoded image bytes (`GeneratedImage` dataclass)
- Callers save outputs to `outputs/thumbnails/` and surface downloads in UI

### Gemini text generation in V1 (`Ytuber` AI Studio)
Key function:
- `_gemini_generate_text(gemini_key, model, prompt)`

What it returns:
- Plain text output joined across Gemini response parts/candidates

Used for:
- titles/descriptions/scripts/hooks/CTA generation
- channel-strategy outputs based on current channel metrics + keyword hints

## API and Quota Behavior (V1)
### YouTube Data API usage
High-cost operations in V1:
- resolving channels (`search.list`)
- reading uploads playlist pages (`playlistItems.list`)
- fetching video details (`videos.list`)
- competitor benchmark (multiple channels)

Quota mitigation built into V1:
- cache-first reads from CSV
- dedupe on `video_id`
- one-year cutoff for video fetches
- exponential backoff retries for transient failures

### Gemini / OpenAI usage
- Triggered only by user button clicks in UI
- No automatic background generation
- API keys are read from `.env` or input boxes

## Dependency/Runtime Notes (V1)
Common dependencies used by V1 pages:
- `streamlit`
- `pandas`
- `requests`
- `google-api-python-client`
- `python-dotenv` (optional but recommended)

Common runtime failures and fixes:
- `ModuleNotFoundError: dashboard` or `src`
  - solved in V1 by adding project root to `sys.path`
- `ModuleNotFoundError: dotenv`
  - V1 recommendations page guards import and still works without it
- `googleapiclient` missing
  - Ytuber page shows friendly error and exits
- Streamlit Cloud dependency mismatch
  - fixed by pinning `streamlit` + `altair`

## Safe Update Guidelines for Teammates (V1)
### Safe changes
- Add charts/metrics in `channel_analysis.py`
- Tune scoring heuristics in `ytuber.py` (`_title_score`, `_description_score`)
- Improve prompt templates in `recommendations.py` and `ytuber.py`
- Add columns to UI tables (if present in CSV schema)

### Changes requiring care
- Editing dataset schema (risk: breaks pages expecting columns)
- Changing `DATASET_PATH`
- Modifying `_fetch_or_get_cached_channel()` (affects cache + API + CSV append behavior)
- Changing `st.session_state` keys (breaks Ytuber tab flow)

### Team handoff checklist before pushing changes
1. Run locally with `.venv`:
   - `python3 -m streamlit run dashboard/app.py`
2. Open `Channel Analysis`, `Recommendations`, and `Ytuber`
3. Load one test channel in `Ytuber`
4. Verify cache/API path (`dataset_cache` vs `youtube_api`) loads successfully
5. If changing dependencies, update `requirements.txt` and test deployment

## Where to Look First When Debugging V1
- Routing issue / wrong page loads:
  - `/Users/ayushkumar/Desktop/Youtube-IP/dashboard/app.py`
- Sidebar/nav issue:
  - `/Users/ayushkumar/Desktop/Youtube-IP/dashboard/components/sidebar.py`
- Dataset analytics issue:
  - `/Users/ayushkumar/Desktop/Youtube-IP/dashboard/views/channel_analysis.py`
- Thumbnail generation issue:
  - `/Users/ayushkumar/Desktop/Youtube-IP/src/llm_integration/thumbnail_generator.py`
- Channel API loading / cache issue:
  - `/Users/ayushkumar/Desktop/Youtube-IP/dashboard/views/ytuber.py`

## V1 vs V2 (Quick Note for Teammates)
- V1 = simpler shell, fewer modules, focused creator suite tabs.
- V2 = modular extension framework, themed home page, expanded creator tools.
- Keep teammate debugging aligned to the correct repo and branch:
  - V1 app repo: `Youtube-IP-private`
  - V2 app repo: `Youtube-IP-v2-private`
