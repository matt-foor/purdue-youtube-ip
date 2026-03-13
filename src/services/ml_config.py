import os

try:
    import src.services.ml_backend_client as _ml_client
    from src.services.channel_payload_builder import build_channel_payload
    _ML_AVAILABLE = True
except Exception:
    _ml_client = None  # type: ignore[assignment]
    build_channel_payload = None  # type: ignore[assignment]
    _ML_AVAILABLE = False

ENABLE_ML_BACKEND: bool = (
    os.environ.get("ENABLE_ML_BACKEND", "").lower() == "true" and _ML_AVAILABLE
)