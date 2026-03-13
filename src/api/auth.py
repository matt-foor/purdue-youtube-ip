import os
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

_api_key_header = APIKeyHeader(name="X-API-Key")


async def verify_api_key(key: str = Security(_api_key_header)) -> None:
    if key != os.environ.get("ML_BACKEND_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key.")