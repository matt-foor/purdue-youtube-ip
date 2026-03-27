# YouTube IP V4 Architecture

## Sidebar Navigation

1. `Channel Analysis`
2. `Channel Insights`
3. `Recommendations`
4. `Outlier Finder`
5. `Ytuber`
6. `Tools`
7. `Deployment`

V4 also includes a global sidebar `Assistant`.

## Full Runtime And Data Pipeline

```mermaid
flowchart TD
    A["GitHub committed CSVs<br/>data/youtube api data/*.csv"] --> B["streamlit_app.py"]
    U["User actions"] --> B
    B --> C["dashboard/app.py"]
    C --> D["dashboard/components/sidebar.py"]
    D --> E["Page views"]

    S["Streamlit secrets / env"] --> F["src/utils/api_keys.py"]
    F --> G["YouTube Data API v3"]
    F --> H["Gemini / OpenAI"]
    O["Google OAuth + YouTube Analytics"] --> I["youtube_owner_analytics_service.py"]

    A --> J["Channel Analysis / Recommendations"]
    G --> K["Ytuber / Channel Insights / Outlier Finder / Tools"]
    H --> L["Recommendations / Ytuber / Outlier Finder / Assistant"]
    I --> M["Channel Insights owner overlays"]

    J --> N["pandas transforms + service payloads"]
    K --> N
    L --> N
    M --> N

    N --> P["dashboard/components/visualizations.py"]
    P --> Q["Charts, cards, tables, downloads, AI outputs"]
```

## Page Problem Map

| Page | Problem Solved | Main Services / Inputs | Main UI Outputs | Interlinks |
| --- | --- | --- | --- | --- |
| `Channel Analysis` | benchmark bundled datasets | CSVs, pandas, visualization helpers | KPI cards, trend charts, ranked tables | shares benchmark context with `Recommendations` |
| `Channel Insights` | analyze one tracked channel over time | `public_channel_service`, `channel_snapshot_store`, `channel_insights_service`, optional owner analytics | topic trends, format analysis, outliers, next-topic ideas | can inform `Outlier Finder` themes |
| `Recommendations` | convert benchmark patterns into guidance and thumbnail concepts | bundled datasets, `thumbnail_generator.py` | sample videos, heuristic guidance, thumbnail outputs | overlaps with thumbnail generation used in `Ytuber` |
| `Outlier Finder` | find niche winners | `outliers_finder.py`, `outlier_ai.py`, YouTube API | scored outlier tables, breakout snapshot, AI research | receives handoff from `Ytuber` and `Channel Insights` |
| `Ytuber` | run a live creator AI workspace | YouTube API, pooled API keys, thumbnail generator | AI Studio, audit views, keyword and planner outputs | can hand off into `Outlier Finder` |
| `Tools` | export public YouTube assets | `youtube_tools.py`, `transcript_service.py`, `yt-dlp`, `ffmpeg` | metadata previews, transcript/audio/video/thumbnail downloads | standalone utility surface |
| `Deployment` | explain setup and deployment | static instructions in app shell | repo, branch, secrets, deploy notes | operational reference only |
| `Assistant` | answer help/troubleshooting/product questions | retrieval services, knowledge base, Gemini/OpenAI fallback | answer cards, related questions, feedback controls | available across all pages |

## Live API Extraction Flow

```mermaid
flowchart LR
    A["User enters channel, keyword, or URL"] --> B["Page view"]
    B --> C["src/utils/api_keys.py"]
    C --> D["Selected provider key"]
    D --> E["YouTube Data API request"]
    E --> F["Service-layer normalization"]
    F --> G["pandas dataframes / scored payloads"]
    G --> H["dashboard/components/visualizations.py"]
    H --> I["Rendered Streamlit UI"]

    J["Optional Google OAuth session"] --> K["YouTube Analytics request"]
    K --> F
```

In V4, `Channel Insights` may merge owner-only metrics only when Google OAuth is configured and the signed-in Google account owns the tracked channel.

## Model-Backed Topic Flow

```mermaid
flowchart LR
    A["Streamlit secrets"] --> B["MODEL_ARTIFACTS_ENABLED"]
    A --> C["MODEL_ARTIFACTS_MANIFEST_URL"]
    C --> D["src/services/model_artifact_service.py"]
    D --> E["Manifest JSON"]
    E --> F["artifact_url + sha256 + bundle_version"]
    F --> G["Download on explicit beta refresh only"]
    G --> H["outputs/models/runtime/<bundle_version>/"]
    H --> I["src/services/topic_model_runtime.py"]
    I --> J["src/services/channel_insights_service.py"]
    J --> K["dashboard/views/channel_insights.py"]
    D --> L["Fallback to heuristic topics"]
    L --> J
```

Topic modes:

- `Heuristic Topics` uses built-in keyword and rule grouping
- `Model-Backed Topics` uses optional BERTopic semantic grouping

## Branch Notes

- V4 keeps the global `Assistant`
- V4 keeps Google OAuth and owner-only analytics overlays in `Channel Insights`
- V4 keeps the page label `Recommendations`
- BERTopic is optional and never required at app boot
