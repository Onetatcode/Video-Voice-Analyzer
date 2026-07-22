from fastapi import APIRouter
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

from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["processing"])

supabase_url = os.getenv("SUPABASE_URL", "")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
_supabase_client = None
if supabase_url and supabase_key:
    from supabase import create_client
    _supabase_client = create_client(supabase_url, supabase_key)
else:
    logger.warning("Supabase credentials not found in environment")


def _get_supabase_client():
    return _supabase_client


@router.post("/process", response_model=ProcessingResponse)
async def start_processing(
    request: ProcessingRequest,
):
    supabase = _get_supabase_client()
    if supabase:
        try:
            existing = supabase.table("reports").select("status").eq("id", request.report_id).single().execute()
            if existing.data and existing.data.get("status") in ["pending", "processing"]:
                return ProcessingResponse(
                    report_id=request.report_id,
                    status=existing.data["status"],
                    message="Job already in progress",
                )
        except Exception:
            pass

    thread = threading.Thread(target=run_processing_task, args=(request.report_id,), daemon=True)
    thread.start()

    return ProcessingResponse(
        report_id=request.report_id,
        status="pending",
        message="Processing started",
    )


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
        pipeline = ProcessingPipeline(supabase_client=_supabase_client)
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
    except ImportError:
        supabase = _get_supabase_client()
        _set_report_status(supabase, request.report_id, "failed")
        return ProcessingResult(
            report_id=request.report_id,
            status=ReportStatus.FAILED,
            error_message="Pipeline dependencies not available",
            processed_at=datetime.utcnow(),
        )


def run_processing_task(report_id: str):
    """Run processing in background daemon thread."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    logger.info(f"Background task started for report {report_id}")

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
            raise Exception("Supabase client not available - cannot fetch report data")

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

    except ImportError as e:
        error_message = f"Pipeline dependencies not available: {e}"
        logger.error(error_message)
        _set_report_status(supabase, report_id, "failed")
    except Exception as e:
        error_message = str(e)
        logger.error(f"Background processing failed for {report_id}: {e}")
        _set_report_status(supabase, report_id, "failed")
