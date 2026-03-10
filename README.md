# YouTube IP V2

Public repo: `royayushkr/Youtube-IP-V2`  
Deployed app: `https://youtube-stats-ip-v2.streamlit.app/`

This `README.md` is the only maintained documentation file for V2. Earlier architecture notes, project briefs, and auxiliary markdown docs have been intentionally folded into this file so the current deployed V2 behavior is documented in one place.

## What V2 Is

V2 is the expanded creator-suite version of YouTube IP. It keeps the research-oriented YouTube dataset and the V1 analytics base, then layers on:

- a themed home page
- extension-based navigation
- a larger `Ytuber` tool suite
- brand kit persistence
- trend APIs
- comment analysis
- transcript analysis
- thumbnail critique

The deployed V2 app is the public Streamlit app at `https://youtube-stats-ip-v2.streamlit.app/`.

## Live App And Repo Entry Points

- Streamlit entrypoint: `dashboard/app.py`
- Theme injection: `dashboard/components/theme.py`
- Sidebar navigation: `dashboard/components/sidebar.py`
- Extension registry: `dashboard/extensions/registry.py`
- Main dataset used by the UI: `data/youtube api data/research_science_channels_videos.csv`
- Additional dataset currently present but not wired into the main app flow: `data/youtube api data/entertainment_channels_videos.csv`
- Extension config persisted in repo: `config/extensions.json`
- Brand kit persisted at runtime: `config/brand_kit.json`

## Runtime Flow

V2 adds a proper app shell around the same core Streamlit model:

1. Streamlit starts at `dashboard/app.py`.
2. The app inserts the project root into `sys.path`.
3. `dashboard/components/theme.py` injects the visual system used across the dashboard.
4. `dashboard/extensions/registry.py` reads `config/extensions.json` and returns the enabled navigation items.
5. `dashboard/components/sidebar.py` renders only the enabled modules.
6. The selected page dispatches to the matching render function in `dashboard/views/`.
7. Dataset pages read from the local CSV files.
8. `Ytuber` uses the dataset as a cache and calls the YouTube API only when the requested channel is not already available for the last year or the user forces refresh.
9. AI features call Gemini, News API, Google Trends, or transcript/comment workflows only on explicit user actions.

## Current Navigation Model

The page registry in `dashboard/app.py` supports:

- `Home`
- `Channel Analysis`
- `Recommendations`
- `Ytuber`
- `Extension Center`
- `Deploy Notes`

However, the visible navigation is controlled by `config/extensions.json`. In the current V2 repo state:

- `Home` is enabled
- `Channel Analysis` is disabled by default
- `Recommendations` is enabled
- `Ytuber` is enabled
- `Extension Center` is enabled
- `Deploy Notes` is enabled

This means the code for `Channel Analysis` exists and works, but the sidebar hides it unless the extension config is changed.

## User-Facing Pages

### `Home`

File: `dashboard/views/home.py`

The home page is V2-only. It:

- reads the research dataset
- shows top-level dataset metrics
- presents the suite as product modules
- gives a quick-start workflow into `Ytuber`

It does not write any files. It is an orientation surface for the suite.

### `Channel Analysis`

File: `dashboard/views/channel_analysis.py`

This page is still dataset-only and is functionally the same analytics layer from V1. It:

- loads `research_science_channels_videos.csv`
- parses numeric engagement fields
- computes `engagement_rate`, `publish_month`, and `publish_day`
- renders KPI cards, top channels, monthly trends, top videos, and day-level performance

The file remains in V2 even if it is disabled in the default extension config.

### `Recommendations`

File: `dashboard/views/recommendations.py`

This page remains largely the same as V1:

- local-data recommendation heuristics based on high-performing titles and videos
- benchmark channel selection
- keyword extraction from winning titles
- thumbnail generation using Gemini or OpenAI through `src/llm_integration/thumbnail_generator.py`
- output persistence to `outputs/thumbnails/`

### `Extension Center`

File: `dashboard/views/extension_center.py`

This page is V2-only. It exposes toggles for all registered modules and persists the result to `config/extensions.json`.

Supporting file:

- `dashboard/extensions/registry.py`

That registry module:

- defines default modules
- loads the persisted config
- merges persisted values over defaults
- saves updated values
- returns the ordered list of enabled nav items

### `Ytuber`

File: `dashboard/views/ytuber.py`

This is the core of V2 and the largest functional difference from V1.

#### Cache And API Flow

The initial channel-loading path is still cache-first:

1. Read `YOUTUBE_API_KEY` and user channel input.
2. Resolve the query to a `channel_id`.
3. Check `research_science_channels_videos.csv` for existing rows for that channel.
4. Reuse cached rows from the last year if available and refresh is not forced.
5. Otherwise fetch the channel record, uploads playlist, and recent videos through the YouTube Data API.
6. Convert the API payload into the flat dataset schema.
7. Deduplicate by `video_id`.
8. Append only unseen rows into the dataset CSV.
9. Save the loaded dataframe and channel metadata to `st.session_state`.

#### Session State Used By V2

`Ytuber` stores and reuses:

- `ytuber_channel_df`
- `ytuber_channel_title`
- `ytuber_channel_id`
- `ytuber_source`
- `ytuber_keyword_hints`
- `ytuber_brand_kit`

#### Runtime-Derived Metrics

After loading the channel, V2 computes the same base derived fields as V1 plus uses them in more places:

- `engagement_rate`
- `publish_month`
- `publish_day`
- `publish_hour`
- `duration_seconds`
- `is_short`

#### V2 `Ytuber` tabs

- `Overview`
  One-year KPIs, trend line, and top videos.
- `Channel Audit`
  Cadence, growth, outlier rate, and shorts mix.
- `Keyword Intel`
  Heuristic keyword opportunity scoring.
- `Title & SEO Lab`
  Heuristic evaluation of candidate titles and descriptions.
- `Title A/B Lab`
  Generates title variants with Gemini when available, otherwise heuristic suffix variants, then scores them.
- `Competitor Benchmark`
  Loads competitor channels through the same cache/API path and compares one-year metrics.
- `Content Gap Finder`
  Compares your channel keywords against competitor keyword surfaces to find uncovered opportunities.
- `Trend Radar`
  Measures keyword momentum based on recent versus previous windows.
- `Trend APIs`
  Pulls Google Trends data through `pytrends` and optional news signals through News API.
- `Comment Intelligence`
  Pulls top-level comments from top videos and computes simple token and sentiment-style counts.
- `Transcript Lab`
  Pulls transcripts with `youtube-transcript-api`, previews them, and optionally sends them to Gemini for retention/script improvement ideas.
- `Content Planner`
  Recommends best publishing day/hour and builds a 4-week calendar.
- `Thumbnail Critic`
  Computes brightness, contrast, and aspect ratio locally, then can send the image to Gemini for a visual critique.
- `Brand Kit`
  Saves tone, audience, visual style, banned words, and CTA guidance to `config/brand_kit.json`.
- `AI Studio`
  Uses Gemini text generation and Gemini image generation, conditioned by channel metrics, keyword hints, and the saved brand kit.

## Data Model Used By The App

The deployed V2 app still runs on a flat per-video dataset schema. The most important stored columns remain:

- channel identity: `channel_id`, `channel_title`, `channel_handle_used`
- channel stats: `channel_subscriberCount`, `channel_viewCount`, `channel_videoCount`
- video identity: `video_id`, `video_title`, `video_description`
- publish and engagement fields: `video_publishedAt`, `views`, `likes`, `comments`, `duration`
- taxonomy and metadata: `video_tags`, `video_topicCategories`, `video_topicIds`
- thumbnails: `thumb_default_*`, `thumb_medium_*`, `thumb_high_*`, `thumb_standard_*`, `thumb_maxres_*`

The main UI path uses the research/science dataset. The entertainment dataset exists in the V2 repo but is not yet the primary source for the current page logic.

## Visual Shell And Theming

### Theme

File: `dashboard/components/theme.py`

V2 injects a custom visual theme instead of using default Streamlit styling. The theme layer provides:

- `Space Grotesk` typography
- custom background gradients
- sidebar styling
- hero card styling
- tool-card styling
- metric-card styling

### Sidebar

File: `dashboard/components/sidebar.py`

The sidebar accepts a dynamic `nav_items` list from the extension registry. Unlike V1, it does not hardcode the available pages.

## AI And API Integrations

### YouTube Data API

Used by:

- `dashboard/views/ytuber.py`
- dataset build scripts under `scripts/`
- `scripts/yt_api_smoketest.py`

Main API operations:

- resolve channel by search
- fetch channel details
- read uploads playlist
- fetch videos in batches
- fetch comments for comment intelligence
- retry transient failures with exponential backoff

### Gemini

Used by:

- `src/llm_integration/thumbnail_generator.py` for image generation
- direct text generation in `dashboard/views/ytuber.py`
- direct visual review in `dashboard/views/ytuber.py`
- direct prompt-based title variant generation when enabled
- transcript improvement prompts

### OpenAI

Still supported by `src/llm_integration/thumbnail_generator.py` as an optional thumbnail-generation fallback on the `Recommendations` page.

### Google Trends

Used in `Ytuber` through `pytrends`. This is on-demand only and only runs if the user presses the relevant button.

### News API

Optional. Used in the `Trend APIs` tab if `NEWSAPI_KEY` is supplied.

### Transcript API

The `Transcript Lab` tab depends on `youtube-transcript-api`, which is why V2 adds that package to `requirements.txt`.

## Repository Map

### Files Actively Used By The Deployed V2 App

- `dashboard/app.py`
  Main router, page registry, theme injection, and extension-aware navigation.
- `dashboard/components/sidebar.py`
  Sidebar renderer for enabled pages.
- `dashboard/components/theme.py`
  App theme injection.
- `dashboard/views/home.py`
  Product-style landing page for the suite.
- `dashboard/views/channel_analysis.py`
  Dataset analytics page, currently present but disabled by default in navigation.
- `dashboard/views/recommendations.py`
  Recommendation engine plus thumbnail generation UI.
- `dashboard/views/ytuber.py`
  Main creator intelligence suite.
- `dashboard/views/extension_center.py`
  Extension toggle and persistence UI.
- `dashboard/extensions/registry.py`
  Extension config load/save/order logic.
- `src/llm_integration/thumbnail_generator.py`
  Shared provider wrapper for Gemini/OpenAI image generation.
- `config/extensions.json`
  Persisted enabled/disabled page state.
- `data/youtube api data/research_science_channels_videos.csv`
  Primary dataset and cache used by the UI.

### Supporting Files Present In The Repo

- `data/youtube api data/entertainment_channels_videos.csv`
  Secondary dataset present in V2 but not the current default input for page logic.
- `scripts/build_category_dataset.py`
  Generic category dataset build script.
- `scripts/build_fitness_dataset.py`
  Fitness dataset builder.
- `scripts/build_research_dataset.py`
  Research/science dataset builder.
- `scripts/yt_api_smoketest.py`
  API connectivity and response inspection script.
- `src/data_collection/*.py`
  Legacy collection scaffold from the original project.
- `src/data_processing/*.py`
  Legacy processing scaffold.
- `src/modeling/*.py`
  Legacy topic-modeling scaffold.
- `src/llm_integration/content_generator.py`
  Earlier content-generation scaffold, not the main V2 app path.
- `src/llm_integration/gpt4_client.py`
  Earlier text-generation helper, not the main deployed V2 runtime path.
- `dashboard/components/visualizations.py`
  Present but currently empty and not wired into the deployed app.
- `config/config.yaml`
  Present from the original scaffold and currently empty.
- `config/logging_config.yaml`
  Present from the original scaffold and currently empty.

## Environment Variables

Required for the full V2 experience:

- `YOUTUBE_API_KEY`
- `GEMINI_API_KEY`

Optional:

- `OPENAI_API_KEY`
- `NEWSAPI_KEY`

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

The intended V2 deployment target is:

- `https://youtube-stats-ip-v2.streamlit.app/`

Recommended Streamlit settings:

- Repository: `royayushkr/Youtube-IP-V2`
- Branch: `main`
- Main file path: `dashboard/app.py`

Recommended Streamlit secrets:

- `YOUTUBE_API_KEY`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY` if OpenAI image generation should stay available
- `NEWSAPI_KEY` if the `Trend APIs` news workflow should be active

## Outputs And Files Written At Runtime

V2 writes to disk in these locations:

- `data/youtube api data/research_science_channels_videos.csv`
  Appended to when `Ytuber` loads a new channel from the YouTube API.
- `config/extensions.json`
  Updated by `Extension Center`.
- `config/brand_kit.json`
  Created or updated by the `Brand Kit` tab.
- `outputs/thumbnails/`
  Receives generated thumbnail files.

V2 still uses file-based persistence rather than a database.

## Troubleshooting

- If Streamlit says `No module named dashboard` or `No module named src`, launch from the project root using `dashboard/app.py`.
- If `googleapiclient` is missing, `Ytuber` exits early with an install message.
- If `pytrends` is unavailable, the `Trend APIs` tab shows an explicit error.
- If `youtube-transcript-api` is unavailable, the `Transcript Lab` tab shows a warning and disables transcript analysis.
- If YouTube API quota is exhausted, `Ytuber` reuses cached rows when available.
- If Gemini text or image generation fails, confirm key validity, selected model names, and outbound API access.
- If a page is missing from the sidebar, check `config/extensions.json` or use `Extension Center`.

## Documentation Policy

This repository intentionally keeps runtime and internal documentation in this file only. If deployment, architecture, or maintenance notes change, update `README.md` instead of creating parallel markdown documents.
