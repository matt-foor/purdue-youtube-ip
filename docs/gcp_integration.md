# GCP Deployment & Streamlit Integration

This document covers the complete GCP infrastructure setup, Cloud Run deployment, and how the ML backend integrates with the Streamlit frontend. It assumes the modeling artifacts have already been trained and the FastAPI backend code is complete.

---

## Architecture Overview

The system is split into two independently deployed services:

```
Streamlit Cloud (frontend)              Cloud Run (ML backend)
-------------------------------         ---------------------------
dashboard/                              src/api/main.py  (FastAPI)
  channel_analysis.py                     POST /jobs
  recommendations.py                      GET  /jobs/{id}
  ytuber.py                               GET  /status
  outlier_finder.py                       POST /admin/reload-artifacts
src/services/
  ml_config.py          -- HTTP -->   src/modeling/
  ml_backend_client.py                  inference.py
  channel_payload_builder.py            model_cache.py (GCS)
```

The Streamlit frontend never imports BERTopic, torch, or any heavy ML dependency. It communicates with the ML backend over HTTP using a shared API key. The ML backend runs on Cloud Run, loads model artifacts from GCS on first use, and persists job state to Firestore.

---

## GCP Infrastructure

### Project

```
Project ID:     purdue-youtube-ip
Project number: 307626651629
Region:         us-east1
```

### APIs enabled

```bash
gcloud services enable run.googleapis.com \
  cloudbuild.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com \
  --project=purdue-youtube-ip
```

### Firestore

Native mode database in `us-east1`. Stores inference job state under `/inference_jobs/{job_id}` and inference result cache.

```bash
gcloud firestore databases create \
  --location=us-east1 \
  --project=purdue-youtube-ip
```

### GCS bucket

Model artifacts bucket. All trained artifacts live under the `models/` prefix.

```bash
gcloud storage buckets create gs://purdue-youtube-ip-models \
  --location=us-east1 \
  --project=purdue-youtube-ip
```

Artifacts at:

```
gs://purdue-youtube-ip-models/models/bertopic_model
gs://purdue-youtube-ip-models/models/xgboost_longform.json
gs://purdue-youtube-ip-models/models/xgboost_shorts.json
gs://purdue-youtube-ip-models/models/xgboost_engagement_shorts.json
gs://purdue-youtube-ip-models/models/niche_blueprints.json
gs://purdue-youtube-ip-models/models/topic_engagement_stats.json
gs://purdue-youtube-ip-models/models/publish_time_stats.json
gs://purdue-youtube-ip-models/models/title_effectiveness_stats.json
gs://purdue-youtube-ip-models/models/topic_trend_baseline.json
gs://purdue-youtube-ip-models/models/topic_stats.csv
```

To re-upload after retraining:

```bash
gcloud storage cp outputs/models/ gs://purdue-youtube-ip-models/ \
  --recursive --project=purdue-youtube-ip
```

### Service account

```bash
gcloud iam service-accounts create youtube-ip-backend \
  --display-name="YouTube IP Backend" \
  --project=purdue-youtube-ip
```

Full identifier: `youtube-ip-backend@purdue-youtube-ip.iam.gserviceaccount.com`

IAM roles granted:

```bash
gcloud projects add-iam-policy-binding purdue-youtube-ip \
  --member="serviceAccount:youtube-ip-backend@purdue-youtube-ip.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding purdue-youtube-ip \
  --member="serviceAccount:youtube-ip-backend@purdue-youtube-ip.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding purdue-youtube-ip \
  --member="serviceAccount:youtube-ip-backend@purdue-youtube-ip.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Secret Manager

Three secrets stored:

| Secret name | Description |
|---|---|
| `ML_BACKEND_API_KEY` | Shared key authenticating Streamlit requests to Cloud Run |
| `YOUTUBE_API_KEYS` | JSON array of YouTube Data API v3 keys |
| `GEMINI_API_KEYS` | JSON array of Gemini API keys |

To create:

```bash
echo -n '["key1","key2"]' | gcloud secrets create YOUTUBE_API_KEYS \
  --data-file=- --project=purdue-youtube-ip

echo -n '["gemini-key"]' | gcloud secrets create GEMINI_API_KEYS \
  --data-file=- --project=purdue-youtube-ip

echo -n "your-random-hex-key" | gcloud secrets create ML_BACKEND_API_KEY \
  --data-file=- --project=purdue-youtube-ip
```

To retrieve a secret value:

```bash
gcloud secrets versions access latest \
  --secret=ML_BACKEND_API_KEY \
  --project=purdue-youtube-ip
```

---

## ML Backend Deployment

### Requirements split

`requirements.txt` is frontend-only (Streamlit Cloud). `requirements-ml.txt` is used exclusively by the Dockerfile for the Cloud Run container. The split prevents Streamlit Cloud from attempting to install torch, BERTopic, and CLIP.

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-ml.txt .
RUN pip install --no-cache-dir -r requirements-ml.txt

COPY src/ ./src/

ENV PYTHONPATH=/app
ENV PORT=8080

EXPOSE 8080

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Model artifacts are not baked into the image. They are loaded from GCS at runtime via `model_cache.py` on first inference request, then held in memory via `@lru_cache`.

### Cloud Build

`cloudbuild.yaml` at repo root. Triggered manually via `gcloud builds submit` or automatically via a Cloud Build trigger on push to `main`.

Steps: build image, push tagged and latest images to Container Registry, deploy to Cloud Run with secrets and env vars injected.

To trigger manually:

```bash
gcloud builds submit --config=cloudbuild.yaml \
  --project=purdue-youtube-ip \
  --substitutions=SHORT_SHA=local
```

### Cloud Run service

```
Service name:   youtube-ip-backend
Region:         us-east1
URL:            https://youtube-ip-backend-307626651629.us-east1.run.app
Memory:         4Gi
CPU:            2
Concurrency:    4
Timeout:        300s
Auth:           no-allow-unauthenticated
```

Environment variables injected at deploy time:

| Variable | Value |
|---|---|
| `MODEL_ROOT` | `gs://purdue-youtube-ip-models/models` |
| `GCS_BUCKET` | `purdue-youtube-ip-models` |
| `FIRESTORE_PROJECT` | `purdue-youtube-ip` |
| `ML_BACKEND_API_KEY` | from Secret Manager |
| `GEMINI_API_KEYS` | from Secret Manager |
| `YOUTUBE_API_KEYS` | from Secret Manager |

`no-allow-unauthenticated` means the service is not publicly accessible. All requests must include the `X-API-Key` header with the `ML_BACKEND_API_KEY` value. The Streamlit frontend injects this header automatically via `ml_backend_client.py`.

### Cold start note

BERTopic and CLIP model loading on first request takes 10-20 seconds. `min-instances=1` in the Cloud Run config keeps one warm instance alive at all times to avoid cold starts for real users. If this is changed to 0 for cost savings, expect the first inference request after idle to take 30-60 seconds.

---

## Model Loading at Runtime

`src/modeling/model_cache.py` resolves artifact paths from the `MODEL_ROOT` environment variable. If `MODEL_ROOT` starts with `gs://`, artifacts are downloaded to a temp file via the GCS client and loaded from there. If `MODEL_ROOT` is a local path (e.g. `./outputs/models/`), files are loaded directly.

This means the same codebase runs in local development (local files) and production (GCS) with only an env var change.

```python
MODEL_ROOT=./outputs/models/       # local dev
MODEL_ROOT=gs://purdue-youtube-ip-models/models  # production
```

---

## Streamlit Frontend Integration

### Feature flag

`ENABLE_ML_BACKEND` controls whether the Streamlit app attempts to contact Cloud Run at all. When `false`, the ML overlay sections are hidden and the app runs entirely on the static CSV datasets.

```python
# src/services/ml_config.py
ENABLE_ML_BACKEND: bool = (
    os.environ.get("ENABLE_ML_BACKEND", "").lower() == "true" and _ML_AVAILABLE
)
```

### Streamlit Cloud secrets

Add the following to your app's secrets at share.streamlit.io under Settings > Secrets:

```toml
ML_BACKEND_URL = "https://youtube-ip-backend-307626651629.us-east1.run.app"
ML_BACKEND_API_KEY = "your-ml-backend-api-key"
ENABLE_ML_BACKEND = "true"
YOUTUBE_API_KEYS = ["your-key-1", "your-key-2", "your-key-3"]
GEMINI_API_KEYS = ["your-gemini-key"]
```

### Request flow

1. User enters a channel handle in Ytuber and clicks "Open Workspace"
2. Ytuber fetches live channel and video data from the YouTube Data API v3
3. `channel_payload_builder.py` assembles the `channel_data` dict from live API data
4. User clicks "Run ML Analysis" in the ML Analysis tab
5. Streamlit calls `_ml_client.post_job(payload)` — HTTP POST to `/jobs` on Cloud Run with the API key header
6. Cloud Run creates a Firestore job record and returns a `job_id`
7. Streamlit polls `_ml_client.get_job(job_id)` every 2 seconds via `st.fragment(run_every=2)`
8. Cloud Run runs the full inference chain (BERTopic, XGBoost, CLIP, PyTrends, Gemini) in a background thread
9. On completion, the result is written to Firestore and the job transitions to `done`
10. Streamlit reads the result and stores it in `st.session_state["ml_inference"]`
11. Recommendations, Channel Analysis, and Ytuber all read from `st.session_state["ml_inference"]` to render ML overlays

### ML result schema

The result stored in `st.session_state["ml_inference"]` has this top-level shape:

```json
{
  "channel_id": "UC...",
  "computed_at": "2026-04-01T02:00:00Z",
  "category": "tech",
  "coverage_summary": { "total_topics": 12, "top_topics": [...], "category": "tech" },
  "gaps": { "topics": [...] },
  "time_windows": { "best_hour_utc": 15, "best_dow": "saturday", "cadence_videos_per_week_recommended": 3 },
  "title_patterns": { "by_topic": { "42": { ... } } },
  "thumbnail_blueprint": { "source": "channel", "axes": [...] },
  "ai_sections": { "growth_angle": "...", "content_gap_brief": "...", "title_framework": "..." }
}
```

---

## Reloading Artifacts Without Redeployment

If model artifacts are updated in GCS but the Cloud Run service is still running with old cached models, call the admin endpoint to clear the in-memory cache:

```bash
curl -X POST \
  https://youtube-ip-backend-307626651629.us-east1.run.app/admin/reload-artifacts \
  -H "X-API-Key: your-ml-backend-api-key"
```

The next inference request will reload all artifacts from GCS.

---

## Local Development

For local development without Cloud Run:

```bash
# .env for the ML backend
MODEL_ROOT=./outputs/models/
FIRESTORE_EMULATOR_HOST=localhost:8080
ML_BACKEND_API_KEY=dev-key-local
GEMINI_API_KEYS=["your-real-gemini-key"]
YOUTUBE_API_KEYS=["your-real-youtube-key"]

# .env for Streamlit
ML_BACKEND_URL=http://localhost:8000
ML_BACKEND_API_KEY=dev-key-local
ENABLE_ML_BACKEND=true
```

```bash
# terminal 1 - firestore emulator
firebase emulators:start --only firestore

# terminal 2 - ml backend
uvicorn src.api.main:app --reload --port 8000

# terminal 3 - streamlit
streamlit run streamlit_app.py
```

Set `ML_DRY_RUN=true` in the Streamlit env to return a fixture result immediately without running inference. Useful for frontend development without Gemini keys or 40-second wait cycles.