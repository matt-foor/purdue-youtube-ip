from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict
from urllib.parse import parse_qs, quote_plus, urlparse

import requests

from src.utils.file_utils import guess_mime_type, safe_temp_dir, sanitize_filename


THUMBNAIL_VARIANTS = (
    ("Max Resolution", "maxresdefault.jpg"),
    ("Standard", "sddefault.jpg"),
    ("High", "hqdefault.jpg"),
    ("Medium", "mqdefault.jpg"),
    ("Default", "default.jpg"),
)

_VIDEO_ID_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")


@dataclass(frozen=True)
class ThumbnailPreview:
    video_id: str
    canonical_url: str
    title: str
    channel: str
    thumbnail_variants: Dict[str, str]
    default_variant: str


@dataclass(frozen=True)
class PreparedThumbnailArtifact:
    file_path: str
    file_name: str
    mime_type: str
    size_bytes: int
    variant_label: str


def _looks_like_video_id(value: str) -> bool:
    return len(value) == 11 and all(char in _VIDEO_ID_CHARS for char in value)


def resolve_video_target(value: str) -> tuple[str, str]:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("Enter a public YouTube video or Short URL first.")

    if _looks_like_video_id(raw):
        return raw, f"https://www.youtube.com/watch?v={raw}"

    parsed = urlparse(raw)
    host = parsed.netloc.lower()
    path_parts = [part for part in parsed.path.split("/") if part]

    if "youtu.be" in host and path_parts:
        video_id = path_parts[0]
    elif "youtube.com" in host:
        if path_parts and path_parts[0] == "watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif len(path_parts) >= 2 and path_parts[0] in {"shorts", "embed", "live"}:
            video_id = path_parts[1]
        else:
            video_id = ""
    else:
        raise ValueError("Use a public YouTube watch URL, Short URL, youtu.be URL, or a direct video ID.")

    if not _looks_like_video_id(video_id):
        raise ValueError("This input does not contain a valid public YouTube video ID.")
    return video_id, f"https://www.youtube.com/watch?v={video_id}"


def _oembed_metadata(canonical_url: str) -> tuple[str, str]:
    endpoint = "https://www.youtube.com/oembed"
    try:
        response = requests.get(
            endpoint,
            params={"url": canonical_url, "format": "json"},
            timeout=20,
        )
    except Exception:
        return "", ""
    if response.status_code >= 400:
        return "", ""
    try:
        payload = response.json()
    except Exception:
        return "", ""
    return str(payload.get("title", "") or ""), str(payload.get("author_name", "") or "")


def _variant_url(video_id: str, filename: str) -> str:
    return f"https://img.youtube.com/vi/{quote_plus(video_id)}/{filename}"


def _variant_available(url: str) -> bool:
    response = None
    try:
        response = requests.get(url, stream=True, timeout=20)
        content_type = str(response.headers.get("content-type", "")).lower()
        return response.status_code < 400 and content_type.startswith("image/")
    except Exception:
        return False
    finally:
        if response is not None:
            response.close()


def preview_thumbnail_target(value: str) -> ThumbnailPreview:
    video_id, canonical_url = resolve_video_target(value)
    title, channel = _oembed_metadata(canonical_url)

    variants: Dict[str, str] = {}
    for label, filename in THUMBNAIL_VARIANTS:
        candidate = _variant_url(video_id, filename)
        if _variant_available(candidate):
            variants[label] = candidate

    if not variants:
        fallback_url = _variant_url(video_id, "hqdefault.jpg")
        variants["High"] = fallback_url

    default_variant = next(iter(variants.keys()))
    return ThumbnailPreview(
        video_id=video_id,
        canonical_url=canonical_url,
        title=title or f"YouTube Video {video_id}",
        channel=channel,
        thumbnail_variants=variants,
        default_variant=default_variant,
    )


def prepare_thumbnail_download(value: str, variant_label: str | None = None) -> PreparedThumbnailArtifact:
    preview = preview_thumbnail_target(value)
    chosen_label = variant_label or preview.default_variant
    thumbnail_url = preview.thumbnail_variants.get(chosen_label)
    if not thumbnail_url:
        raise ValueError("The selected thumbnail variant is not available for this video.")

    response = requests.get(thumbnail_url, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"Failed to download the thumbnail ({response.status_code}).")

    suffix = Path(urlparse(thumbnail_url).path).suffix or ".jpg"
    temp_dir = safe_temp_dir("thumbnail-hub-")
    file_name = f"{sanitize_filename(preview.title, preview.video_id)}-{preview.video_id}-{chosen_label.lower().replace(' ', '-')}{suffix}"
    file_path = temp_dir / file_name
    file_path.write_bytes(response.content)
    return PreparedThumbnailArtifact(
        file_path=str(file_path),
        file_name=file_name,
        mime_type=guess_mime_type(file_path),
        size_bytes=file_path.stat().st_size,
        variant_label=chosen_label,
    )


__all__ = [
    "PreparedThumbnailArtifact",
    "ThumbnailPreview",
    "prepare_thumbnail_download",
    "preview_thumbnail_target",
    "resolve_video_target",
]
