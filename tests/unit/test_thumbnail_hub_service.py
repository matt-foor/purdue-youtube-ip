from __future__ import annotations

from pathlib import Path

import src.services.thumbnail_hub_service as thumbnail_hub_service


class _FakeResponse:
    def __init__(self, *, status_code: int = 200, json_payload=None, content: bytes = b"", headers=None) -> None:
        self.status_code = status_code
        self._json_payload = json_payload
        self.content = content
        self.headers = headers or {"content-type": "image/jpeg"}

    def json(self):
        if self._json_payload is None:
            raise ValueError("No JSON configured")
        return self._json_payload

    def close(self) -> None:
        return None


def test_resolve_video_target_supports_watch_short_youtu_be_and_id() -> None:
    video_id, canonical = thumbnail_hub_service.resolve_video_target("https://www.youtube.com/watch?v=abc123xyz90")
    short_id, short_canonical = thumbnail_hub_service.resolve_video_target("https://www.youtube.com/shorts/xyz789abc12")
    share_id, share_canonical = thumbnail_hub_service.resolve_video_target("https://youtu.be/hij456klm34")
    raw_id, raw_canonical = thumbnail_hub_service.resolve_video_target("zxy987wvu65")

    assert video_id == "abc123xyz90"
    assert canonical.endswith("abc123xyz90")
    assert short_id == "xyz789abc12"
    assert short_canonical.endswith("xyz789abc12")
    assert share_id == "hij456klm34"
    assert share_canonical.endswith("hij456klm34")
    assert raw_id == "zxy987wvu65"
    assert raw_canonical.endswith("zxy987wvu65")


def test_preview_thumbnail_target_shapes_metadata_and_variants(monkeypatch) -> None:
    def fake_get(url: str, **kwargs):
        if "oembed" in url:
            return _FakeResponse(
                json_payload={
                    "title": "How To Improve Packaging",
                    "author_name": "Demo Channel",
                },
                headers={"content-type": "application/json"},
            )
        return _FakeResponse(headers={"content-type": "image/jpeg"})

    monkeypatch.setattr(thumbnail_hub_service.requests, "get", fake_get)

    preview = thumbnail_hub_service.preview_thumbnail_target("https://www.youtube.com/watch?v=abc123xyz90")

    assert preview.video_id == "abc123xyz90"
    assert preview.title == "How To Improve Packaging"
    assert preview.channel == "Demo Channel"
    assert "High" in preview.thumbnail_variants
    assert preview.default_variant in preview.thumbnail_variants


def test_prepare_thumbnail_download_writes_file(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(thumbnail_hub_service, "safe_temp_dir", lambda prefix: tmp_path)

    def fake_get(url: str, **kwargs):
        if "oembed" in url:
            return _FakeResponse(
                json_payload={
                    "title": "Thumbnail Hooks",
                    "author_name": "Demo Channel",
                },
                headers={"content-type": "application/json"},
            )
        return _FakeResponse(content=b"image-bytes", headers={"content-type": "image/jpeg"})

    monkeypatch.setattr(thumbnail_hub_service.requests, "get", fake_get)

    artifact = thumbnail_hub_service.prepare_thumbnail_download(
        "https://www.youtube.com/watch?v=abc123xyz90",
        "High",
    )

    assert artifact.file_name.endswith(".jpg")
    assert artifact.variant_label == "High"
    assert Path(artifact.file_path).exists()
    assert Path(artifact.file_path).read_bytes() == b"image-bytes"
