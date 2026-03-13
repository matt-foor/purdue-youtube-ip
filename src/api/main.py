from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.auth import verify_api_key
from src.api.routes.jobs import router as jobs_router
from src.api.routes.status import router as status_router
from src.modeling.model_cache import clear_all_caches


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    clear_all_caches()


app = FastAPI(title="CreatorIQ ML Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
app.include_router(status_router)


@app.post("/admin/reload-artifacts", dependencies=[Depends(verify_api_key)])
def reload_artifacts() -> dict:
    clear_all_caches()
    return {"status": "caches cleared"}