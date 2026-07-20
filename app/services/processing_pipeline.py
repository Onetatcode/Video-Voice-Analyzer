import os
import tempfile
import time
import logging
from typing import Optional
from datetime import datetime

from ..models.processing import (
    ProcessingRequest,
    ProcessingResult,
    ProcessingResponse,
    ReportStatus,
    Scores,
    AnalysisReport,
    VoiceFeatures,
    BodyFeatures,
)
from ..services.video_processor import VideoProcessor, AudioProcessor
from ..services.voice_analyzer import VoiceAnalyzer
from ..services.body_analyzer import BodyAnalyzer
from ..services.score_calculator import ScoreCalculator
from ..services.report_generator import ReportGenerator
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """
    Main pipeline that orchestrates the complete video processing workflow:
    1. Download video
    2. Extract audio
    3. Extract frames
    4. Analyze voice features
    5. Analyze body language
    6. Calculate scores
    7. Generate report
    """

    def __init__(self, supabase_client: Optional[Client] = None):
        self.video_processor = VideoProcessor()
        self.audio_processor = AudioProcessor()
        self.voice_analyzer = VoiceAnalyzer()
        self.body_analyzer = BodyAnalyzer()
        self.score_calculator = ScoreCalculator()
        self.report_generator = ReportGenerator()
        self.supabase_client = supabase_client or self._create_supabase_client()

    def _create_supabase_client(self) -> Optional[Client]:
        """Create Supabase client from environment variables."""
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        load_dotenv(dotenv_path=env_path)
        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if supabase_url and supabase_key:
            return create_client(supabase_url, supabase_key)
        return None

    def _fetch_report_from_db(self, report_id: str) -> Optional[dict]:
        """Fetch report details from Supabase."""
        if not self.supabase_client:
            return None
        try:
            result = self.supabase_client.table("reports").select("*").eq("id", report_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.warning(f"Failed to fetch report {report_id} from DB: {e}")
            return None

    def process(self, request: ProcessingRequest) -> ProcessingResult:
        """
        Process a video through the complete pipeline.
        """
        start_time = time.time()
        temp_dir = tempfile.mkdtemp(prefix=f"processing_{request.report_id}_")

        try:
            # Fetch video_url from DB if not provided in request
            if not request.video_url:
                report = self._fetch_report_from_db(request.report_id)
                if report and report.get("video_url"):
                    request.video_url = report["video_url"]
                    if not request.user_id:
                        request.user_id = report.get("user_id")
                    logger.info(f"Fetched video_url from DB: {request.video_url}")
                else:
                    raise Exception(f"No video_url found for report {request.report_id}")

            logger.info(f"Starting processing for report {request.report_id}")

            # 1. Download video
            video_path = os.path.join(temp_dir, "input_video.mp4")
            logger.info(f"Downloading video from {request.video_url}")
            if not self.video_processor.download_video(request.video_url, video_path, self.supabase_client):
                raise Exception("Failed to download video")

            # 2. Get video info
            video_info = self.video_processor.get_video_info(video_path)
            duration = video_info.get("duration", 0)
            logger.info(f"Video duration: {duration:.1f}s, FPS: {video_info.get('fps', 0):.1f}")

            # 3. Extract audio
            audio_path = os.path.join(temp_dir, "audio.wav")
            logger.info("Extracting audio...")
            if not self.video_processor.extract_audio(video_path, audio_path):
                logger.warning("Could not extract audio, proceeding with empty audio features")
                voice_features = self.voice_analyzer._empty_analysis()
            else:
                # 4. Analyze voice
                logger.info("Analyzing voice features...")
                voice_features = self.voice_analyzer.analyze(audio_path)

            # 5. Extract frames for body analysis
            logger.info("Extracting frames...")
            frames = self.video_processor.extract_frames(video_path, max_frames=150)

            # 6. Analyze body language
            logger.info("Analyzing body language...")
            body_features = self.body_analyzer.analyze_frames(frames)

            # 7. Calculate scores
            logger.info("Calculating scores...")
            scores = self.score_calculator.calculate_scores(voice_features, body_features)

            # 8. Generate report
            logger.info("Generating report...")
            report = self.report_generator.generate_report(
                scores=scores,
                voice_features=voice_features,
                body_features=body_features,
            )

            processing_time = time.time() - start_time

            result = ProcessingResult(
                report_id=request.report_id,
                status=ReportStatus.COMPLETE,
                voice_features=VoiceFeatures(**voice_features),
                body_features=BodyFeatures(**body_features),
                scores=Scores(**scores),
                analysis_report=AnalysisReport(**report),
                processed_at=datetime.utcnow(),
                processing_time_seconds=round(processing_time, 2),
            )

            logger.info(f"Processing complete for {request.report_id} in {processing_time:.1f}s")
            return result

        except Exception as e:
            logger.error(f"Processing failed for {request.report_id}: {e}")
            processing_time = time.time() - start_time
            return ProcessingResult(
                report_id=request.report_id,
                status=ReportStatus.FAILED,
                error_message=str(e),
                processing_time_seconds=round(processing_time, 2),
            )

        finally:
            # Cleanup temp files
            self._cleanup_temp_dir(temp_dir)

    def _cleanup_temp_dir(self, temp_dir: str):
        """Clean up temporary directory."""
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp dir {temp_dir}: {e}")

    def close(self):
        """Clean up resources."""
        self.body_analyzer.close()