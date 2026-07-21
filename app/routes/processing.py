from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from datetime import datetime
import os
import logging
import threading

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
):
    if request.report_id in processing_jobs:
        existing = processing_jobs[request.report_id]
        if existing["status"] in ["pending", "processing"]:
            return ProcessingResponse(
                report_id=request.report_id,
                status=existing["status"],
                message="Job already in progress",
            )

    processing_jobs[request.report_id] = {
        "status": "pending",
        "request": request.model_dump(),
        "result": None,
        "started_at": None,
    }

    thread = threading.Thread(target=run_processing_task, args=(request.report_id,), daemon=True)
    thread.start()

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


def _save_result_to_db(supabase, report_id, result):
    """Save processing result to Supabase."""
    if not supabase:
        return
    if result.status == ReportStatus.COMPLETE:
        report_json = result.analysis_report.model_dump() if result.analysis_report else {}
        if result.voice_features and result.voice_features.transcript:
            report_json["transcript"] = result.voice_features.transcript
        update_data = {
            "status": result.status.value,
            "voice_score": result.scores.voice_score if result.scores else None,
            "body_score": result.scores.body_score if result.scores else None,
            "confidence_score": result.scores.confidence_score if result.scores else None,
            "report_json": report_json,
        }
        supabase.table("reports").update(update_data).eq("id", report_id).execute()
        logger.info(f"Saved result for report {report_id}")
    else:
        supabase.table("reports").update({"status": result.status.value}).eq("id", report_id).execute()


def _set_report_status(supabase, report_id, status):
    """Set report status in Supabase."""
    if supabase:
        try:
            supabase.table("reports").update({"status": status}).eq("id", report_id).execute()
        except Exception as e:
            logger.error(f"Failed to update status for {report_id}: {e}")


@router.post("/process/sync", response_model=ProcessingResult)
async def process_sync(request: ProcessingRequest):
    try:
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
            _save_result_to_db(supabase, request.report_id, result)
            return result
        finally:
            pipeline.close()
    except ImportError as e:
        supabase = _get_supabase_client()
        error_msg = f"Pipeline dependencies not available (cv2/mediapipe): {e}"
        _set_report_status(supabase, request.report_id, "failed")
        return ProcessingResult(
            report_id=request.report_id,
            status=ReportStatus.FAILED,
            error_message=error_msg,
            processed_at=datetime.utcnow(),
        )


def run_processing_task(report_id: str):
    """Run processing in background daemon thread."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    logger.info(f"Background task started for report {report_id}")

    job = processing_jobs.get(report_id)
    if not job:
        processing_jobs[report_id] = {"status": "processing", "request": {}, "result": None, "started_at": datetime.utcnow().isoformat()}
        job = processing_jobs[report_id]
    else:
        job["status"] = "processing"
        job["started_at"] = datetime.utcnow().isoformat()

    supabase = _get_supabase_client()

    try:
        from ..services.processing_pipeline import ProcessingPipeline

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
        _save_result_to_db(supabase, report_id, result)

        job["status"] = "complete"
        job["result"] = {
            "message": "Processing complete",
            "result": result.model_dump() if hasattr(result, 'model_dump') else str(result),
        }

    except ImportError as e:
        error_message = f"Pipeline dependencies not available (cv2/mediapipe): {e}"
        logger.error(error_message)
        _set_report_status(supabase, report_id, "failed")
        job["status"] = "failed"
        job["result"] = {"message": error_message, "result": None}
    except Exception as e:
        error_message = str(e)
        logger.error(f"Background processing failed for {report_id}: {e}")
        _set_report_status(supabase, report_id, "failed")
        job["status"] = "failed"
        job["result"] = {"message": f"Processing failed: {error_message}", "result": None}
