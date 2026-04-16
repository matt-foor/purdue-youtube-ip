from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from dashboard.components.visualizations import graph_insight_expander, section_header
from src.llm_integration.thumbnail_generator import ThumbnailGenerator, get_api_key
from src.services.thumbnail_hub_service import PreparedThumbnailArtifact, ThumbnailPreview, prepare_thumbnail_download, preview_thumbnail_target
from src.utils.api_keys import get_provider_key_count
from src.utils.file_utils import cleanup_temp_dirs


THUMBNAILS_STATE_KEYS = (
    "thumbnails_preview",
    "thumbnails_download_artifact",
    "thumbnails_error",
    "thumbnails_temp_paths",
)

PROVIDER_LABELS = {
    "gemini": "Gemini",
    "openai": "OpenAI / ChatGPT",
}

IMAGE_MODEL_CATALOG = {
    "gemini": [
        {
            "id": "gemini-2.5-flash-image",
            "label": "Gemini 2.5 Flash Image",
            "summary": "Fastest option for thumbnail ideation with strong prompt adherence.",
            "per_image": 0.039,
            "size_options": ["1024x1024"],
            "quality_options": ["standard"],
        },
    ],
    "openai": [
        {
            "id": "gpt-image-1.5",
            "label": "GPT Image 1.5",
            "summary": "Highest-quality thumbnail rendering with flexible formats and background control.",
            "pricing": {
                "low": {"1024x1024": 0.009, "1024x1536": 0.013, "1536x1024": 0.013},
                "medium": {"1024x1024": 0.034, "1024x1536": 0.050, "1536x1024": 0.050},
                "high": {"1024x1024": 0.133, "1024x1536": 0.200, "1536x1024": 0.200},
            },
            "size_options": ["1024x1024", "1024x1536", "1536x1024"],
            "quality_options": ["low", "medium", "high"],
            "background_options": ["opaque", "transparent"],
            "format_options": ["png", "webp", "jpeg"],
        },
        {
            "id": "gpt-image-1-mini",
            "label": "GPT Image 1 Mini",
            "summary": "Lower-cost thumbnail iteration when you want a few fast visual angles.",
            "pricing": {
                "low": {"1024x1024": 0.005, "1024x1536": 0.006, "1536x1024": 0.006},
                "medium": {"1024x1024": 0.011, "1024x1536": 0.015, "1536x1024": 0.015},
                "high": {"1024x1024": 0.036, "1024x1536": 0.052, "1536x1024": 0.052},
            },
            "size_options": ["1024x1024", "1024x1536", "1536x1024"],
            "quality_options": ["low", "medium", "high"],
            "background_options": ["opaque", "transparent"],
            "format_options": ["png", "webp", "jpeg"],
        },
    ],
}


def _inject_page_css() -> None:
    st.markdown(
        """
        <style>
        .thumb-page {
            max-width: var(--app-page-width);
            margin: 0 auto;
        }
        .thumb-hero {
            max-width: 920px;
            margin: 0 auto 1.4rem;
            text-align: center;
        }
        .thumb-kicker {
            display:inline-flex;
            align-items:center;
            gap:0.5rem;
            padding:0.45rem 0.78rem;
            border-radius:999px;
            background:rgba(255,255,255,0.05);
            border:1px solid rgba(255,255,255,0.08);
            color:#F7F8FC;
            font-size:12px;
            letter-spacing:0.1em;
            text-transform:uppercase;
            margin-bottom:0.95rem;
        }
        .thumb-kicker-dot {
            width:8px;
            height:8px;
            border-radius:999px;
            background:linear-gradient(180deg,#FF0000,#00D4FF);
            box-shadow:0 0 16px rgba(255,0,0,0.45);
        }
        .thumb-title {
            font-family:"Inter",system-ui,sans-serif;
            font-size:clamp(34px,3.8vw,50px);
            line-height:1.02;
            font-weight:700;
            color:#F7F8FC;
            letter-spacing:-0.04em;
            margin-bottom:0.8rem;
        }
        .thumb-subtitle {
            color:#B8C1DA;
            font-size:16px;
            line-height:1.62;
            max-width:640px;
            margin:0 auto;
            text-align:center;
            text-wrap:balance;
        }
        .thumb-card {
            border-radius:24px;
            border:1px solid rgba(255,255,255,0.08);
            background:
                radial-gradient(circle at top left, rgba(255, 0, 0, 0.12) 0%, transparent 32%),
                radial-gradient(circle at top right, rgba(0, 212, 255, 0.08) 0%, transparent 28%),
                linear-gradient(180deg, rgba(22, 33, 62, 0.95) 0%, rgba(15, 15, 35, 0.98) 100%);
            box-shadow:0 20px 46px rgba(3, 6, 20, 0.40);
            padding:1.1rem 1.2rem;
            margin-bottom:1rem;
        }
        .thumb-card-title {
            font-family:"Inter",system-ui,sans-serif;
            color:#F7F8FC;
            font-size:20px;
            font-weight:700;
            margin-bottom:0.25rem;
        }
        .thumb-card-copy {
            color:#B8C1DA;
            font-size:13px;
            line-height:1.58;
        }
        .thumb-metric {
            padding:0.85rem 0.95rem;
            border-radius:18px;
            background:rgba(255,255,255,0.03);
            border:1px solid rgba(255,255,255,0.06);
            margin-bottom:0.8rem;
        }
        .thumb-metric-label {
            color:#8993B2;
            font-size:11px;
            text-transform:uppercase;
            letter-spacing:0.08em;
            margin-bottom:0.22rem;
        }
        .thumb-metric-value {
            color:#F7F8FC;
            font-size:22px;
            font-weight:700;
        }
        .thumb-gallery-card {
            padding:0.8rem;
            border-radius:18px;
            border:1px solid rgba(255,255,255,0.06);
            background:rgba(255,255,255,0.03);
            margin-bottom:0.85rem;
        }
        .thumb-empty {
            padding:1rem 1.1rem;
            border-radius:20px;
            border:1px dashed rgba(255,255,255,0.12);
            background:rgba(255,255,255,0.02);
            color:#B8C1DA;
            font-size:13px;
            line-height:1.6;
        }
        /* Light glass */
        .thumb-card {
            background: rgba(255, 255, 255, 0.92) !important;
            border: 1px solid rgba(0, 0, 0, 0.1) !important;
            box-shadow: 0 16px 44px rgba(0, 0, 0, 0.1) !important;
        }
        .thumb-card-title { color: #1d1d1f !important; }
        .thumb-card-copy { color: #424245 !important; }
        .thumb-metric {
            background: rgba(255, 255, 255, 0.95) !important;
            border: 1px solid rgba(0, 0, 0, 0.08) !important;
        }
        .thumb-metric-label { color: #6e6e73 !important; }
        .thumb-metric-value { color: #1d1d1f !important; }
        .thumb-empty {
            border: 1px dashed rgba(0, 0, 0, 0.15) !important;
            background: rgba(255, 255, 255, 0.85) !important;
            color: #6e6e73 !important;
        }
        /* Thumbnails page controls: force light glass fields (no dark fallbacks) */
        .thumb-page [data-testid="stWidgetLabel"] p,
        .thumb-page [data-testid="stWidgetLabel"] label,
        .thumb-page [data-testid="stWidgetLabel"] span {
            color: #1d1d1f !important;
            opacity: 1 !important;
            font-weight: 600 !important;
        }
        .thumb-page .stTextInput > div > div > input,
        .thumb-page .stTextArea textarea,
        .thumb-page [data-baseweb="input"] > div,
        .thumb-page [data-baseweb="textarea"] > div,
        .thumb-page [data-baseweb="select"] > div,
        .thumb-page .stSelectbox > div > div {
            background: linear-gradient(165deg, rgba(255, 255, 255, 1), rgba(240, 244, 250, 0.98)) !important;
            color: #1d1d1f !important;
            border: 1px solid rgba(0, 0, 0, 0.16) !important;
            border-radius: 14px !important;
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 1),
                0 6px 16px rgba(0, 0, 0, 0.08) !important;
        }
        .thumb-page [data-baseweb="input"] input,
        .thumb-page [data-baseweb="textarea"] textarea,
        .thumb-page .stTextInput input,
        .thumb-page .stTextArea textarea {
            color: #1d1d1f !important;
            caret-color: #1d1d1f !important;
            background: transparent !important;
        }
        .thumb-page .stTextInput input::placeholder,
        .thumb-page .stTextArea textarea::placeholder {
            color: #6e6e73 !important;
            opacity: 1 !important;
        }
        .thumb-page [data-baseweb="input"] input:focus,
        .thumb-page [data-baseweb="textarea"] textarea:focus,
        .thumb-page .stTextInput input:focus,
        .thumb-page .stTextArea textarea:focus {
            border-color: rgba(230, 0, 18, 0.35) !important;
            box-shadow: 0 0 0 2px rgba(0, 113, 227, 0.14) !important;
            outline: none !important;
        }
        /* Fallback (no .thumb-page wrapper in DOM): force light text areas/inputs */
        .stTextArea textarea,
        [data-baseweb="textarea"] textarea,
        [data-baseweb="textarea"] > div,
        .stTextInput input,
        [data-baseweb="input"] input,
        [data-baseweb="input"] > div,
        .stSelectbox > div > div,
        [data-baseweb="select"] > div {
            background: linear-gradient(165deg, rgba(255, 255, 255, 1), rgba(240, 244, 250, 0.98)) !important;
            color: #1d1d1f !important;
            border: 1px solid rgba(0, 0, 0, 0.16) !important;
            border-radius: 14px !important;
            -webkit-text-fill-color: #1d1d1f !important;
        }
        .stTextArea textarea::placeholder,
        .stTextInput input::placeholder,
        [data-baseweb="textarea"] textarea::placeholder,
        [data-baseweb="input"] input::placeholder {
            color: #6e6e73 !important;
            -webkit-text-fill-color: #6e6e73 !important;
            opacity: 1 !important;
        }
        /* Thumbnails page help icon: remove dark dot artifact and show a clean bulb */
        [data-testid="stWidgetLabel"] [data-testid*="stTooltipHoverTarget"] button,
        [data-testid="stWidgetLabel"] [data-testid*="stTooltipIcon"],
        [data-testid="stWidgetLabel"] [data-testid*="stHelpIcon"] {
            width: 24px !important;
            height: 24px !important;
            min-width: 24px !important;
            min-height: 24px !important;
            border-radius: 999px !important;
            background: linear-gradient(165deg, #fffaf0, #fff3d9) !important;
            border: 1px solid rgba(230, 0, 18, 0.42) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
            color: transparent !important;
            position: relative !important;
            overflow: hidden !important;
        }
        [data-testid="stWidgetLabel"] [data-testid*="stTooltipHoverTarget"] button *,
        [data-testid="stWidgetLabel"] [data-testid*="stTooltipIcon"] *,
        [data-testid="stWidgetLabel"] [data-testid*="stHelpIcon"] * {
            opacity: 0 !important;
            color: transparent !important;
            background: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
        }
        [data-testid="stWidgetLabel"] [data-testid*="stTooltipHoverTarget"] button::before,
        [data-testid="stWidgetLabel"] [data-testid*="stTooltipIcon"]::before,
        [data-testid="stWidgetLabel"] [data-testid*="stHelpIcon"]::before {
            content: "💡";
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -54%);
            font-size: 13px;
            line-height: 1;
            opacity: 1 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _catalog_map(provider: str) -> dict[str, dict]:
    return {item["id"]: item for item in IMAGE_MODEL_CATALOG[provider]}


def _format_model_option(provider: str, model_id: str) -> str:
    item = _catalog_map(provider)[model_id]
    return f"{item['label']}  •  {item['summary']}"


def _estimate_image_cost(provider: str, model_id: str, count: int, size: str, quality: str) -> float:
    item = _catalog_map(provider)[model_id]
    if provider == "gemini":
        return float(item["per_image"]) * count
    return float(item["pricing"][quality][size]) * count


def _clear_thumbnail_state() -> None:
    cleanup_temp_dirs(st.session_state.get("thumbnails_temp_paths", []))
    for key in THUMBNAILS_STATE_KEYS:
        st.session_state.pop(key, None)
    st.session_state["thumbnails_temp_paths"] = []


def _register_thumbnail_artifact(artifact: PreparedThumbnailArtifact) -> None:
    temp_dir = str(Path(artifact.file_path).parent)
    paths = set(st.session_state.get("thumbnails_temp_paths", []))
    paths.add(temp_dir)
    st.session_state["thumbnails_temp_paths"] = sorted(paths)


def _render_generate_tab() -> None:
    section_header("Thumbnail Generation", icon="🖼️")

    provider = st.selectbox(
        "Provider",
        ["gemini", "openai"],
        index=0,
        format_func=lambda value: PROVIDER_LABELS.get(value, value.title()),
    )
    model_options = [item["id"] for item in IMAGE_MODEL_CATALOG[provider]]
    model = st.selectbox(
        "Model",
        model_options,
        format_func=lambda value: _format_model_option(provider, value),
    )
    model_meta = _catalog_map(provider)[model]

    default_api_key = get_api_key(provider) or ""
    api_key = st.text_input(
        "API Key",
        value=default_api_key,
        type="password",
        help="Leave this as-is if your provider key is already configured in Streamlit secrets.",
    )

    title = st.text_input("Video Title", value="The Physics of Black Holes in 10 Minutes")
    context = st.text_area(
        "Creative Context",
        value=(
            "Audience: curious students and lifelong learners. "
            "Goal: make the main concept instantly legible, dramatic, and high-contrast."
        ),
        height=120,
    )
    style = st.text_area(
        "Style Direction",
        value="Bold contrast, one clear subject, cinematic lighting, 16:9 composition, no clutter.",
        height=90,
    )
    negative_prompt = st.text_input(
        "Avoid",
        value="tiny text, low contrast, too many subjects, busy background",
    )

    config_cols = st.columns(4)
    with config_cols[0]:
        count = st.slider("Options", min_value=1, max_value=6, value=3)
    with config_cols[1]:
        size = st.selectbox("Image Size", model_meta["size_options"])
    with config_cols[2]:
        quality = st.selectbox("Image Quality", model_meta["quality_options"])
    with config_cols[3]:
        key_status = "Configured" if default_api_key else "Manual"
        st.markdown(
            f"""
            <div class="thumb-metric">
                <div class="thumb-metric-label">Provider Keys</div>
                <div class="thumb-metric-value">{get_provider_key_count(provider)}</div>
                <div style="font-size:12px;color:#B8C1DA;margin-top:0.25rem;">Default source: {key_status}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    background = "opaque"
    output_format = "png"
    if provider == "openai":
        advanced_cols = st.columns(2)
        with advanced_cols[0]:
            background = st.selectbox("Background", model_meta.get("background_options", ["opaque"]))
        with advanced_cols[1]:
            output_format = st.selectbox("Output Format", model_meta.get("format_options", ["png"]))

    estimated_cost = _estimate_image_cost(provider, model, count, size, quality)
    st.markdown(
        f"""
        <div class="thumb-card">
            <div class="thumb-card-title">Estimated Spend</div>
            <div class="thumb-card-copy">
                This run is estimated at about <strong>${estimated_cost:.4f}</strong> for {count} generated concept(s) using {model_meta['label']}.
                The thumbnail hub stays intentionally focused on image generation only.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Generate Thumbnails", type="primary", use_container_width=True):
        if not api_key:
            st.error("Add a provider API key in the field above or via Streamlit secrets.")
            return
        if not title.strip() or not context.strip():
            st.error("Video title and creative context are both required.")
            return

        with st.spinner("Generating thumbnail concepts..."):
            try:
                generator = ThumbnailGenerator(provider=provider, api_key=api_key, model=model)
                images = generator.generate(
                    title=title,
                    context=context,
                    style=style,
                    negative_prompt=negative_prompt,
                    count=count,
                    size=size,
                    quality=quality,
                    output_format=output_format if provider == "openai" else None,
                    background=background if provider == "openai" else None,
                )
            except Exception as exc:
                st.error(f"Thumbnail generation failed: {exc}")
                return

        output_dir = Path("outputs") / "thumbnails"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        gallery_cols = st.columns(min(len(images), 3) or 1)
        for index, image in enumerate(images, start=1):
            extension = "png" if "png" in image.mime_type else "jpg"
            file_name = f"thumbnail_{timestamp}_{index}.{extension}"
            (output_dir / file_name).write_bytes(image.image_bytes)
            with gallery_cols[(index - 1) % len(gallery_cols)]:
                st.markdown("<div class='thumb-gallery-card'>", unsafe_allow_html=True)
                st.image(image.image_bytes, use_container_width=True)
                st.download_button(
                    "Download",
                    data=image.image_bytes,
                    file_name=file_name,
                    mime=image.mime_type,
                    use_container_width=True,
                    key=f"thumb_generate_{timestamp}_{index}",
                )
                st.markdown("</div>", unsafe_allow_html=True)


def _render_download_tab() -> None:
    section_header("Download Public Thumbnail", icon="🔎")

    left, right = st.columns([1.1, 0.9], gap="large")
    with left:
        st.markdown(
            """
            <div class="thumb-card">
                <div class="thumb-card-title">Preview A Video Thumbnail</div>
                <div class="thumb-card-copy">
                    Paste a public watch URL, Short URL, youtu.be URL, or direct video ID to inspect the available thumbnail variants
                    and download the one you want.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("thumbnail_lookup_form", clear_on_submit=False):
            lookup_value = st.text_input(
                "YouTube Video URL Or ID",
                key="thumbnails_lookup_value",
                placeholder="https://www.youtube.com/watch?v=... or https://youtu.be/...",
            )
            lookup_clicked = st.form_submit_button("Preview Thumbnail", type="primary", use_container_width=True)

        if lookup_clicked:
            try:
                cleanup_temp_dirs(st.session_state.get("thumbnails_temp_paths", []))
                st.session_state["thumbnails_temp_paths"] = []
                preview = preview_thumbnail_target(lookup_value)
            except Exception as exc:
                st.session_state["thumbnails_error"] = str(exc)
                st.session_state.pop("thumbnails_preview", None)
                st.session_state.pop("thumbnails_download_artifact", None)
            else:
                st.session_state["thumbnails_preview"] = preview
                st.session_state["thumbnails_download_artifact"] = None
                st.session_state.pop("thumbnails_error", None)

        if st.session_state.get("thumbnails_error"):
            st.error(st.session_state["thumbnails_error"])

    with right:
        preview: ThumbnailPreview | None = st.session_state.get("thumbnails_preview")
        if not preview:
            st.markdown(
                "<div class='thumb-empty'>Load a public video first to inspect the thumbnail and export one of the available variants.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="thumb-card">
                    <div class="thumb-card-title">{preview.title}</div>
                    <div class="thumb-card-copy">
                        Channel: {preview.channel or 'Unknown'}<br/>
                        Video ID: {preview.video_id}<br/>
                        Available Variants: {len(preview.thumbnail_variants)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    preview = st.session_state.get("thumbnails_preview")
    if not preview:
        return

    variant_options = list(preview.thumbnail_variants.keys())
    selected_variant = st.selectbox(
        "Thumbnail Variant",
        variant_options,
        index=variant_options.index(preview.default_variant) if preview.default_variant in variant_options else 0,
        key="thumbnails_variant",
    )

    preview_url = preview.thumbnail_variants[selected_variant]
    preview_cols = st.columns([1.15, 0.85], gap="large")
    with preview_cols[0]:
        st.image(preview_url, use_container_width=True)
    with preview_cols[1]:
        st.markdown(
            """
            <div class="thumb-card">
                <div class="thumb-card-title">Variant Details</div>
                <div class="thumb-card-copy">
                    Use this flow when you want the exact public thumbnail from an existing YouTube video.
                    It stays intentionally narrow: no transcript, audio, video, batch, or playlist tooling lives here anymore.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Prepare Thumbnail Download", type="primary", use_container_width=True):
            try:
                artifact = prepare_thumbnail_download(preview.canonical_url, selected_variant)
            except Exception as exc:
                st.error(f"Thumbnail download failed: {exc}")
            else:
                _register_thumbnail_artifact(artifact)
                st.session_state["thumbnails_download_artifact"] = artifact

        artifact: PreparedThumbnailArtifact | None = st.session_state.get("thumbnails_download_artifact")
        if artifact:
            artifact_path = Path(artifact.file_path)
            if artifact_path.exists():
                st.download_button(
                    "Download Thumbnail",
                    data=artifact_path.read_bytes(),
                    file_name=artifact.file_name,
                    mime=artifact.mime_type,
                    use_container_width=True,
                    key=f"thumbnail_download_{artifact.file_name}",
                )


def render_thumbnail_workspace() -> None:
    """Thumbnail generate + public thumbnail export (used by Download Hub)."""
    _inject_page_css()
    st.markdown('<div class="thumb-page">', unsafe_allow_html=True)

    graph_insight_expander(
        "Thumbnails",
        """
**Generate (AI)**  
1. Choose **Provider** (Gemini or OpenAI) and **Model**.  
2. Add an **API key** if one is not already in Streamlit secrets.  
3. Fill **Video title**, **Creative context**, **Style**, and **Avoid** so the model matches your channel.  
4. Set **Options** (count), **Size**, and **Quality**, then click **Generate Thumbnails**.  
5. Use each **Download** button to save images to your computer.

**Download from URL (public thumbnail)**  
1. Paste a watch, Short, `youtu.be`, or **video ID** and click **Preview Thumbnail**.  
2. Pick a **Thumbnail variant** in the list.  
3. Click **Prepare Thumbnail Download**, then **Download Thumbnail**.

Public thumbnails come from YouTube’s published assets only; AI generation uses your provider’s API and may incur cost.
        """,
        for_instructions=True,
    )

    tabs = st.tabs(["Generate", "Download From URL"])
    with tabs[0]:
        _render_generate_tab()
    with tabs[1]:
        _render_download_tab()

    st.markdown("</div>", unsafe_allow_html=True)


def render() -> None:
    render_thumbnail_workspace()

