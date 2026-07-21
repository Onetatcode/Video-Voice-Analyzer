from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class ProcessingRequest(BaseModel):
    report_id: str
    video_url: Optional[str] = None
    user_id: Optional[str] = None

    class Config:
        extra = "allow"


class ProcessingResponse(BaseModel):
    report_id: str
    status: ReportStatus
    message: str
    result: Optional[Dict[str, Any]] = None


class VoiceFeatures(BaseModel):
    speech_pace: float = Field(..., description="Words per minute")
    pitch_variation: float = Field(..., description="Standard deviation of pitch")
    filler_word_count: int = Field(..., description="Number of filler words (um, uh, like, etc.)")
    pause_frequency: float = Field(..., description="Pauses per minute")
    avg_pause_duration: float = Field(..., description="Average pause duration in seconds")
    total_duration: float = Field(..., description="Total speech duration in seconds")
    transcript: Optional[str] = Field(default=None, description="Full speech transcript from Gemini STT")


class BodyFeatures(BaseModel):
    posture_stability: float = Field(..., description="Posture stability score 0-1")
    eye_contact_ratio: float = Field(..., description="Percentage of time facing camera")
    gesture_frequency: float = Field(..., description="Gestures per minute")
    movement_frequency: float = Field(..., description="Body movements per minute")
    head_nod_count: int = Field(..., description="Number of head nods")
    shoulder_movement_score: float = Field(..., description="Shoulder movement stability 0-1")


class Scores(BaseModel):
    confidence_score: int = Field(..., ge=0, le=100, description="Overall confidence score 0-100")
    voice_score: int = Field(..., ge=0, le=100, description="Voice analysis score 0-100")
    body_score: int = Field(..., ge=0, le=100, description="Body language score 0-100")


class AnalysisReport(BaseModel):
    strengths: List[str] = Field(default_factory=list, description="Identified strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Identified weaknesses")
    tips: List[str] = Field(default_factory=list, description="Actionable improvement tips (2-3)")


class ProcessingResult(BaseModel):
    report_id: str
    status: ReportStatus
    voice_features: Optional[VoiceFeatures] = None
    body_features: Optional[BodyFeatures] = None
    scores: Optional[Scores] = None
    analysis_report: Optional[AnalysisReport] = None
    error_message: Optional[str] = None
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_seconds: Optional[float] = None


class ReportUpdate(BaseModel):
    status: ReportStatus
    voice_score: Optional[int] = None
    body_score: Optional[int] = None
    confidence_score: Optional[int] = None
    voice_features: Optional[Dict[str, Any]] = None
    body_features: Optional[Dict[str, Any]] = None
    report_json: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None