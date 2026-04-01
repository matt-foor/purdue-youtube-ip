import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired
from hdbscan import HDBSCAN
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, CountVectorizer
from umap import UMAP

warnings.filterwarnings("ignore")

RAW_CSV      = Path("data/processed/combined_videos_raw.csv")
CLEAN_CSV    = Path("data/processed/combined_videos_clean.csv")
CORPUS_TXT   = Path("data/processed/bertopic_corpus.txt")
META_CSV     = Path("data/processed/bertopic_metadata.csv")
STATS_CSV    = Path("data/processed/topic_stats.csv")
MODEL_DIR    = Path("outputs/models")

RANDOM_STATE   = 42
MIN_TOPIC_SIZE = 30
N_GRAM_RANGE   = (1, 2)
TOP_N_WORDS    = 10
SPARSE_THRESHOLD = 5

_BOILERPLATE_RE = re.compile(
    r"""
    \bsubscribe\b | \bhit\s+the\s+bell\b | \bturn\s+on\s+notifications?\b
    | \bsmash\s+(that\s+)?like\b | \blike\s+and\s+subscribe\b | \blike\s+(and|&)\s+share\b
    | \bbecome\s+a\s+channel\s+member\b
    | \bpatreon\b | \bko-?fi\b | \bbuy\s+me\s+a\s+coffee\b | \bbecome\s+a\s+patron\b
    | \bsupport\s+(the|this|my)\s+(channel|show|podcast)\b | \bmerch\b | \bmerchandise\b
    | \bjoin\s+(my|our|the)\s+discord\b | \bdiscord\s+(server|community|link)\b | \bdiscord\.gg\b
    | \bsponsored\s+by\b | \bthis\s+(episode|video)\s+(was\s+|is\s+)?sponsored\b
    | \bbrought\s+to\s+you\s+by\b | \buse\s+(code|promo\s+code|discount\s+code)\b
    | \baffiliate\s+(link|code|partner)\b | \bpromo\s+code\b | \bdiscount\s+code\b
    | \bfollow\s+(me|us)\s+on\b | \bfind\s+(me|us)\s+on\b | \bcheck\s+(me|us)\s+out\s+on\b
    | \bmy\s+(instagram|twitter|tiktok|facebook|twitch)\s*[:@]
    | \b(instagram|twitter|tiktok|facebook)\s*:\s*[@]?\w+
    | \blinks?\s+(below|in\s+(the\s+)?description|in\s+bio)\b
    | \bmore\s+info\s+(below|in\s+the\s+description)\b | \ball\s+links?\s+in\b
    | \bbusiness\s+(inquir|email|contact)\b
    | \bfor\s+(sponsorship|collaboration|collab|business)\s+(inquir|email|contact|opportunit)
    | \b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b
    | \ball\s+rights\s+reserved\b | \bcopyright\s+\xa9?\s*\d{4}\b
    | \bthank\s*(s|\s+you)\s+for\s+watching\b | \bsee\s+you\s+(in\s+the\s+next|next\s+time)\b
    | ^(chapters?|timestamps?)\s*:?\s*$
    | \btwitch\.tv\b | \blive\s+stream\b | \bgoing\s+live\b | \bwatch\s+live\b
    | \bsubscribe\s+for\s+more\b | \bnotification\s+squad\b
    | \bdonat(e|ions?)\b | \btip\s+(jar|link)\b | \bstreamlabs\b
    | \bnord\s*vpn\b | \bexpressvpn\b | \bsurfshark\b | \bvpn\s+(deal|sponsor|code|link)\b
    | \buse\s+code\b | \bget\s+\d+%\s+off\b | \bfirst\s+\d+\s+people\b
    | \bnebula\b | \bepidemic\s+sound\b | \bartlist\b
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)

URL_RE     = re.compile(r"http\S+|www\.\S+")
HASHTAG_RE = re.compile(r"#\w+")
MENTION_RE = re.compile(r"@\w+")
EMOJI_RE   = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F9FF"
    "\U00002700-\U000027BF"
    "\U0001FA00-\U0001FA6F"
    "]+",
    flags=re.UNICODE,
)
PUNCT_RE = re.compile(r"[^\w\s]")
SPACE_RE = re.compile(r"\s+")

_CHANNEL_STOPWORDS = [
    "smarter", "smartereveryday", "vsauce", "veritasium", "kurzgesagt",
    "mrbeast", "markiplier", "pewdiepie", "linus", "linustechtips",
    "technicalguruji", "mkbhd", "unboxtherapy", "jerryrigeverything",
    "jacksepticeye", "affiliate",
]


def _parse_duration(val):
    if pd.isna(val):
        return np.nan
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", str(val).strip())
    if not m:
        return np.nan
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return float(h * 3600 + mi * 60 + s)


def _strip_boilerplate(text) -> str:
    if pd.isna(text) or not str(text).strip():
        return ""
    lines = str(text).splitlines()
    kept = [ln.strip() for ln in lines if ln.strip() and not _BOILERPLATE_RE.search(ln)]
    return " ".join(kept)


def _clean_text(text) -> str:
    if pd.isna(text) or not str(text).strip():
        return ""
    text = URL_RE.sub(" ", text)
    text = HASHTAG_RE.sub(" ", text)
    text = MENTION_RE.sub(" ", text)
    text = EMOJI_RE.sub(" ", text)
    text = PUNCT_RE.sub(" ", text)
    text = SPACE_RE.sub(" ", text)
    return text.strip()


def _dominant_share(d):
    vals = list(d.values())
    return max(vals) / sum(vals)


def build_clean_csv() -> pd.DataFrame:
    df = pd.read_csv(RAW_CSV, low_memory=False)
    df["video_publishedAt"] = pd.to_datetime(df["video_publishedAt"], utc=True, errors="coerce")
    df["snapshot_utc"]      = pd.to_datetime(df["snapshot_utc"],      utc=True, errors="coerce")
    df["duration_sec"] = df["duration"].apply(_parse_duration)
    df["is_short"]     = df["duration_sec"] <= 60
    for col in ["views", "likes", "comments"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.loc[df["video_description"].str.strip().eq(""), "video_description"] = np.nan
    drop_mask = df["views"].isna() | df["duration_sec"].isna()
    df = df[~drop_mask].reset_index(drop=True)
    df["like_rate"]     = df["likes"]    / df["views"].replace(0, np.nan)
    df["comment_rate"]  = df["comments"] / df["views"].replace(0, np.nan)
    df["views_per_day"] = df["views"] / (
        (df["snapshot_utc"] - df["video_publishedAt"]).dt.total_seconds() / 86_400
    ).replace(0, np.nan)
    df["publish_year"]  = df["video_publishedAt"].dt.year
    df["publish_month"] = df["video_publishedAt"].dt.to_period("M").dt.to_timestamp()
    df["title_clean"] = df["video_title"].apply(_clean_text)
    df["desc_clean"]  = df["video_description"].apply(_strip_boilerplate).apply(_clean_text)
    df["tags_clean"]  = (
        df["video_tags"].fillna("")
        .apply(lambda x: " ".join(_clean_text(tag) for tag in x.split("|") if tag.strip()))
    )
    df["bertopic_text"] = (
        df["title_clean"] + " " + df["title_clean"] + " " + df["desc_clean"] + " " + df["tags_clean"]
    ).str.strip()
    df["bertopic_text"] = (
        df["bertopic_text"]
        .str.replace(r"\b\d+\b", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    df["bertopic_token_count"] = df["bertopic_text"].str.split().str.len()
    df["is_sparse_text"] = df["bertopic_token_count"] < SPARSE_THRESHOLD
    drop_cols = [
        "thumb_default_url", "thumb_default_width", "thumb_default_height",
        "thumb_medium_url",  "thumb_medium_width",  "thumb_medium_height",
        "thumb_high_url",    "thumb_high_width",     "thumb_high_height",
        "thumb_standard_url","thumb_standard_width", "thumb_standard_height",
        "thumb_maxres_url",  "thumb_maxres_width",   "thumb_maxres_height",
        "video_description", "video_tags",
        "video_channelId", "uploads_playlist_id", "channel_topicIds", "video_topicIds",
        "channel_isLinked", "channel_madeForKids", "projection", "embeddable",
    ]
    df_clean = df.drop(columns=[c for c in drop_cols if c in df.columns])
    df_clean.to_csv(CLEAN_CSV, index=False)
    df_clean["bertopic_text"].to_csv(CORPUS_TXT, index=False, header=False)
    meta_cols = [
        "video_id", "video_title", "channel_title", "category_name",
        "publish_year", "views", "like_rate", "comment_rate",
        "duration_sec", "is_short", "is_sparse_text", "bertopic_token_count",
    ]
    df_clean[meta_cols].to_csv(META_CSV, index=False)
    print(f"Clean CSV saved -> {CLEAN_CSV} ({len(df_clean):,} rows)")
    return df_clean


def train(df_clean: pd.DataFrame | None = None) -> None:
    if df_clean is None:
        df_clean = pd.read_csv(CLEAN_CSV)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    embedding_model    = SentenceTransformer("all-MiniLM-L6-v2")
    umap_model         = UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine",
                              random_state=RANDOM_STATE, low_memory=False)
    hdbscan_model      = HDBSCAN(min_cluster_size=MIN_TOPIC_SIZE, metric="euclidean",
                                 cluster_selection_method="eom", prediction_data=True)
    vectorizer_model   = CountVectorizer(ngram_range=N_GRAM_RANGE,
                                         stop_words=list(ENGLISH_STOP_WORDS) + _CHANNEL_STOPWORDS,
                                         min_df=10, max_df=0.85)
    representation_model = KeyBERTInspired()

    topic_model = BERTopic(
        embedding_model=embedding_model,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        representation_model=representation_model,
        top_n_words=TOP_N_WORDS,
        nr_topics=90,
        calculate_probabilities=False,
        verbose=True,
    )

    corpus = df_clean["bertopic_text"].tolist()
    topics, _ = topic_model.fit_transform(corpus)
    print(f"Topics found (excl. -1): {len(set(topics)) - 1}")
    print(f"Outlier docs (topic -1): {topics.count(-1):,} ({topics.count(-1)/len(topics)*100:.1f}%)")

    new_topics = topic_model.reduce_outliers(corpus, topics, strategy="embeddings", threshold=0.3)
    topic_model.update_topics(corpus, topics=new_topics,
                               vectorizer_model=vectorizer_model,
                               representation_model=representation_model)
    topics = new_topics
    print(f"Outliers after reduction: {list(topics).count(-1):,} ({list(topics).count(-1)/len(topics)*100:.1f}%)")

    df_clean = df_clean.copy()
    df_clean["topic_id"] = topics

    topic_info   = topic_model.get_topic_info()
    topic_labels = (
        topic_info[topic_info["Topic"] != -1][["Topic", "Name"]]
        .rename(columns={"Topic": "topic_id", "Name": "topic_label"})
    )

    topic_stats = (
        df_clean[df_clean["topic_id"] != -1]
        .groupby("topic_id")
        .agg(
            video_count=("video_id", "count"),
            median_views=("views", "median"),
            median_like_rate=("like_rate", "median"),
            top_category=("category_name", lambda x: x.value_counts().index[0]),
            category_mix=("category_name", lambda x: x.value_counts().to_dict()),
        )
        .reset_index()
        .merge(topic_labels, on="topic_id")
    )
    topic_stats["dominant_category_share"] = topic_stats["category_mix"].apply(_dominant_share)
    topic_stats = topic_stats.sort_values("median_views", ascending=False).reset_index(drop=True)

    topic_model.save(str(MODEL_DIR / "bertopic_model"), serialization="pickle", save_ctfidf=True)
    topic_stats.to_csv(STATS_CSV, index=False)

    meta_out = (
        df_clean[[
            "video_id", "video_title", "channel_title", "category_name",
            "publish_year", "views", "like_rate", "comment_rate",
            "duration_sec", "is_short", "is_sparse_text", "bertopic_token_count", "topic_id",
        ]]
        .copy()
        .merge(topic_labels, on="topic_id", how="left")
    )
    meta_out["topic_label"] = meta_out["topic_label"].fillna("outlier")
    meta_out.to_csv(META_CSV, index=False)

    print(f"Topics found: {len(set(topics)) - 1}")
    print(f"Outlier rate: {list(topics).count(-1)/len(topics)*100:.1f}%")
    print(f"Median topic size: {topic_stats['video_count'].median():.0f} videos")
    print(f"Model saved -> {MODEL_DIR / 'bertopic_model'}")
    print(f"Stats saved -> {STATS_CSV}")
    print(f"Metadata saved -> {META_CSV}")


if __name__ == "__main__":
    df_clean = build_clean_csv()
    train(df_clean)