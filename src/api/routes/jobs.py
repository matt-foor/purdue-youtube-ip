import uuid
from fastapi import APIRouter, Depends, HTTPException

from src.api.auth import verify_api_key
from src.api.schemas import ChannelPayload, CreateJobResponse, JobResponse, JobStatus
from src.jobs.job_store import check_cache, create_job, create_job_done, get_job
from src.api.worker import enqueue

router = APIRouter()


@router.post("/jobs/channel-inference", response_model=CreateJobResponse, status_code=202, dependencies=[Depends(verify_api_key)])
async def create_inference_job(payload: ChannelPayload) -> CreateJobResponse:
    channel_data = payload.model_dump()
    cached = check_cache(channel_data)
    job_id = str(uuid.uuid4())

    if cached:
        create_job_done(job_id, channel_data["channel"]["channel_id"], cached)
        return CreateJobResponse(job_id=job_id)

    create_job(job_id, channel_data["channel"]["channel_id"])
    enqueue(job_id, channel_data)
    return CreateJobResponse(job_id=job_id)


@router.get("/jobs/{job_id}", response_model=JobResponse, dependencies=[Depends(verify_api_key)])
async def get_inference_job(job_id: str) -> JobResponse:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobResponse(
        job_id=job_id,
        status=JobStatus(job["status"]),
        result=job.get("result"),
        error=job.get("error"),
    )