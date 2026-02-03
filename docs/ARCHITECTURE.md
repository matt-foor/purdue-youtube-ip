# System Architecture

This document captures the high-level architecture, core components, and data flow.

## End-to-End Flow
```mermaid
flowchart LR
    A[YouTube Data API v3] --> B[Raw Data Store]
    C[Public Captions] --> B
    D[Google Trends (Optional)] --> B
    B --> E[Data Cleaning & Feature Engineering]
    E --> F[Topic Modeling - BERTopic]
    E --> G[Engagement Analytics]
    F --> H[Semantic Themes & Clusters]
    G --> I[High-Engagement Patterns]
    H --> J[LLM Strategy Generator]
    I --> J
    J --> K[Streamlit Dashboard]
    K --> L[Recommendations & Insights]
```

## Component Responsibilities
```mermaid
flowchart TB
    subgraph Data_Collection
        A1[channel_fetcher.py]
        A2[youtube_api_client.py]
        A3[youtube_scraper.py]
    end
    subgraph Processing
        B1[text_cleaner.py]
        B2[feature_engineering.py]
    end
    subgraph Modeling
        C1[bertopic_trainer.py]
        C2[topic_model.py]
    end
    subgraph LLM
        D1[gpt4_client.py]
        D2[content_generator.py]
    end
    subgraph Delivery
        E1[Streamlit App]
        E2[Visualizations]
    end

    Data_Collection --> Processing --> Modeling --> LLM --> Delivery
```

## Data Artifacts
- **Raw Data:** `data/raw/`
- **Processed Data:** `data/processed/`
- **Models:** `outputs/models/`
- **Visuals and Reports:** `outputs/figures/`, `outputs/reports/`
