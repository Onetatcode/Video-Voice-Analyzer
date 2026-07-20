from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, Dict, Any
from datetime import datetime
import os
import logging

from ..models.processing import (
    ProcessingRequest,
    ProcessingResult,
    ProcessingResponse,
    ReportStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["processing"])

# In-memory job storage (replace with Redis/DB in production)
processing_jobs: Dict[str, Dict[str, Any]] = {}


def _get_supabase_client():
    """Create Supabase client with explicit .env path."""
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(dotenv_path=env_path)

    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if supabase_url and supabase_key:
        from supabase import create_client
        return create_client(supabase_url, supabase_key)
    logger.warning("Supabase credentials not found in environment")
    return None


@router.post("/process", response_model=ProcessingResponse)
async def start_processing(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks,
):
    if request.report_id in processing_jobs:
        existing = processing_jobs[request.report_id]
        if existing["status"] in ["pending", "processing"]:
            return ProcessingResponse(
                job_id=request.report_id,
                status=existing["status"],
                message="Job already in progress",
            )

    processing_jobs[request.report_id] = {
        "status": "pending",
        "request": request.model_dump(),
        "result": None,
        "started_at": None,
    }

    background_tasks.add_task(run_processing_task, request.report_id)

    return ProcessingResponse(
        report_id=request.report_id,
        status="pending",
        message="Processing started",
    )


@router.get("/process/{report_id}/status")
async def get_processing_status(report_id: str):
    if report_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = processing_jobs[report_id]
    result = job.get("result")

    return {
        "report_id": report_id,
        "status": job.get("status", "unknown"),
        "message": result.get("message") if result else None,
        "result": result,
    }


@router.post("/process/sync", response_model=ProcessingResult)
async def process_sync(request: ProcessingRequest):
    from ..services.processing_pipeline import ProcessingPipeline

    pipeline = ProcessingPipeline()
    try:
        supabase = _get_supabase_client()
        if supabase and (not request.video_url or not request.user_id):
            report_data = supabase.table("reports").select("*").eq("id", request.report_id).single().execute()
            if report_data.data:
                if not request.video_url:
                    request.video_url = report_data.data.get("video_url")
                if not request.user_id:
                    request.user_id = report_data.data.get("user_id")

        result = pipeline.process(request)
        return result
    finally:
        pipeline.close()


def run_processing_task(report_id: str):
    """Run processing in background thread pool."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from ..services.processing_pipeline import ProcessingPipeline

    logger.info(f"Background task started for report {report_id}")

    if report_id not in processing_jobs:
        processing_jobs[report_id] = {
            "status": "pending",
            "result": None,
            "started_at": None,
        }

    job = processing_jobs[report_id]
    job["status"] = "processing"
    job["started_at"] = datetime.utcnow().isoformat()

    supabase = _get_supabase_client()

    try:
        video_url = None
        user_id = None

        if supabase:
            report_data = supabase.table("reports").select("*").eq("id", report_id).single().execute()
            if report_data.data:
                video_url = report_data.data.get("video_url")
                user_id = report_data.data.get("user_id")
                supabase.table("reports").update({"status": "processing"}).eq("id", report_id).execute()
                logger.info(f"Fetched report {report_id} from DB: video_url={video_url}")
            else:
                raise Exception(f"Report {report_id} not found in database")
        else:
            request_dict = job.get("request", {})
            video_url = request_dict.get("video_url")
            user_id = request_dict.get("user_id")

        if not video_url:
            raise Exception("No video_url available for processing")

        request = ProcessingRequest(
            report_id=report_id,
            video_url=video_url,
            user_id=user_id,
        )

        pipeline = ProcessingPipeline(supabase_client=supabase)
        result = pipeline.process(request)
        pipeline.close()

        logger.info(f"Pipeline returned status: {result.status}")

        if supabase and result.status == ReportStatus.COMPLETE:
            update_data = {
                "status": result.status.value,
                "voice_score": result.scores.voice_score if result.scores else None,
                "body_score": result.scores.body_score if result.scores else None,
                "confidence_score": result.scores.confidence_score if result.scores else None,
                "report_json": result.analysis_report.model_dump() if result.analysis_report else None,
            }
            supabase.table("reports").update(update_data).eq("id", report_id).execute()
            logger.info(f"Updated report {report_id} with scores: {update_data}")

        job["status"] = "complete"
        job["result"] = {
            "message": "Processing complete",
            "result": result.model_dump() if hasattr(result, 'model_dump') else str(result),
        }

    except Exception as e:
        logger.error(f"Background processing failed for {report_id}: {e}")
        if supabase:
            try:
                supabase.table("reports").update({
                    "status": "failed",
                }).eq("id", report_id).execute()
            except Exception as update_err:
                logger.error(f"Failed to update report status to failed: {update_err}")
            try:
                supabase.table("reports").update({
                    "error_message": str(e),
                }).eq("id", report_id).execute()
            except Exception as update_err:
                logger.error(f"Failed to update error_message: {update_err}")

        job["status"] = "failed"
        job["result"] = {
            "message": f"Processing failed: {str(e)}",
            "result": None,
        }
