
---

## 2️⃣ `AVAILABLE_DATA_CONSTRAINTS_AND_USAGE.md`

```md
# YouTube Data API: Available Data, Constraints, and Intended Usage

## Overview
This document summarizes the **public data surfaces** available through the YouTube Data API v3, the **constraints** associated with each, and the **intended analytical or product usage** within this project.

The scope reflects validated outputs from an end-to-end smoke test.

---

## 1. Channel-Level Data

### Core Metadata
**Fields**
- Channel title
- Publish date
- Uploads playlist ID

**Constraints**
- Static metadata only
- No behavioral insight

**Intended Usage**
- Channel identification and labeling
- Channel age normalization
- Scalable entry point for video ingestion

---

### Aggregate Channel Metrics
**Fields**
- Subscriber count (if public)
- Total views
- Total video count

**Constraints**
- Subscriber count may be hidden
- Metrics are cumulative and not time-bounded

**Intended Usage**
- Channel size segmentation
- Performance normalization (e.g., views per subscriber)
- Baseline context for video-level metrics

---

### Branding Settings
**Fields**
- Country
- Channel keywords
- Default language (often missing)

**Constraints**
- Self-declared and inconsistently maintained
- Not guaranteed to be accurate

**Intended Usage**
- Channel fingerprinting
- Weak semantic priors for topic modeling
- Geographic segmentation
- Cold-start context when video history is limited

---

### Channel Status Flags
**Fields**
- Privacy status
- Made-for-kids flag

**Constraints**
- Binary indicators
- Limited explanatory power

**Intended Usage**
- Filtering logic (exclude non-public content)
- Adjust modeling assumptions for kids content
- Policy-safe comparisons

---

### Channel Topic Details
**Fields**
- Topic categories (Wikipedia URLs)
- Topic IDs (often missing)

**Constraints**
- Sparse and coarse-grained
- Frequently generic (e.g., “Knowledge”)

**Intended Usage**
- Weak validation signal for topic clusters
- Interpretability support in dashboards
- Never a primary modeling feature

---

## 2. Video-Level Data

### Identity and Timing
**Fields**
- Video ID
- Publish timestamp
- Channel title

**Constraints**
- None for public videos

**Intended Usage**
- Time-series analysis
- Posting cadence analysis
- Velocity calculations (views per day)

---

### Content Metadata
**Fields**
- Title
- Tags (if present)
- Category ID and name

**Constraints**
- Tags are optional and inconsistent
- Categories are broad

**Intended Usage**
- Primary text input for NLP and topic modeling
- Feature engineering
- High-level content grouping

---

### Engagement Metrics
**Fields**
- View count
- Like count (may be disabled)
- Comment count (may be disabled)

**Constraints**
- No impressions or CTR
- Cumulative counts only
- Availability varies by creator settings

**Intended Usage**
- Proxy measures of audience interest
- Relative performance comparisons
- Outcome variables for correlation analysis
- Ranking and prioritization signals for recommendations

---

### Technical Attributes
**Fields**
- Duration
- Caption availability flag
- Embeddable flag

**Constraints**
- Caption flag does not provide transcript text
- Duration requires parsing

**Intended Usage**
- Format analysis (short vs long-form)
- Length optimization recommendations
- Accessibility and production maturity proxies

---

### Video Status Flags
**Fields**
- Privacy status
- Made-for-kids flag

**Constraints**
- Binary indicators only

**Intended Usage**
- Filtering and validation
- Adjust engagement expectations
- Ensure comparable cohorts

---

### Video Topic Details
**Fields**
- Topic categories
- Topic IDs (largely absent)

**Constraints**
- Sparse and unreliable

**Intended Usage**
- Weak supervision for topic models
- Interpretability support
- Secondary enrichment only

---

## 3. Video Categories

**Fields**
- Category ID to category name mapping

**Constraints**
- Platform-defined and coarse

**Intended Usage**
- Broad segmentation
- Exploratory analysis sanity checks
- Supplemental labeling

---

## 4. Comments

**Fields**
- Comment text
- Publish timestamp
- Like count

**Constraints**
- Partial retrieval only
- Replies not fully captured
- Sentiment can be noisy or adversarial

**Intended Usage**
- Audience language analysis
- Qualitative sentiment and controversy detection
- Supplementary topic modeling input
- Early reaction signals

---

## 5. Data Not Available via Public API

The following are not accessible without creator authorization:
- Watch time and retention
- Impressions and CTR
- Audience demographics
- Revenue and monetization
- Full transcripts at scale

**Design Implication**
All insights must rely on **observable public outcomes** rather than internal performance metrics.

---

## Conclusion
The YouTube Data API v3 provides sufficient public data to support cross-channel analysis, trend detection, and AI-assisted content strategy recommendations. While internal performance metrics are unavailable, careful normalization, enrichment, and proxy-based reasoning allow the construction of defensible, production-grade insights within documented constraints.
