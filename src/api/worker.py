import uuid
from concurrent.futures import ThreadPoolExecutor

from src.api.schemas import ErrorCode, ErrorEnvelope, JobStatus
from src.jobs.job_store import set_job_running, set_job_done, set_job_failed, write_cache
from src.modeling.inference import run_channel_inference, InferenceError

_executor = ThreadPoolExecutor(max_workers=4)


def _run(job_id: str, channel_data: dict) -> None:
    set_job_running(job_id)
    try:
        result = run_channel_inference(channel_data)
        write_cache(channel_data, result)
        set_job_done(job_id, result)
    except InferenceError as e:
        set_job_failed(job_id, ErrorEnvelope(
            error_code=ErrorCode(e.error_code),
            message=e.message,
            retryable=e.retryable,
        ))
    except Exception as e:
        set_job_failed(job_id, ErrorEnvelope(
            error_code=ErrorCode.INTERNAL_ERROR,
            message=str(e),
            retryable=False,
        ))


def enqueue(job_id: str, channel_data: dict) -> None:
    _executor.submit(_run, job_id, channel_data)


def queue_depth() -> int:
    return _executor._work_queue.qsize()