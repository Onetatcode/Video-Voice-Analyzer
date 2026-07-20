from typing import Dict, Any
from datetime import datetime

from .voice_analyzer import VoiceAnalyzer
from .body_analyzer import BodyAnalyzer
from .report_generator import ReportGenerator


class ScoreCalculator:
    """Calculates confidence scores from voice and body features."""

    def __init__(self):
        self.voice_analyzer = VoiceAnalyzer()
        self.body_analyzer = BodyAnalyzer()
        self.report_generator = ReportGenerator()

    def calculate_scores(
        self,
        voice_features: Dict[str, Any],
        body_features: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate overall confidence score and sub-scores.
        Returns dict with confidence_score, voice_score, body_score, and breakdowns.
        """
        # Voice sub-scores
        voice_breakdown = self._compute_voice_breakdown(voice_features)
        voice_score = round(
            voice_breakdown["clarity"] * 0.4 +
            voice_breakdown["consistency"] * 0.3 +
            voice_breakdown["engagement"] * 0.3
        )

        # Body sub-scores
        body_breakdown = self._compute_body_breakdown(body_features)
        body_score = round(
            body_breakdown["posture"] * 0.35 +
            body_breakdown["stability"] * 0.35 +
            body_breakdown["expressiveness"] * 0.3
        )

        # Overall confidence (weighted: 55% voice, 45% body)
        confidence_score = round(voice_score * 0.55 + body_score * 0.45)

        # Clamp scores
        confidence_score = max(0, min(100, confidence_score))
        voice_score = max(0, min(100, voice_score))
        body_score = max(0, min(100, body_score))

        return {
            "confidence_score": confidence_score,
            "voice_score": voice_score,
            "body_score": body_score,
            "voice_breakdown": voice_breakdown,
            "body_breakdown": body_breakdown,
        }

    def _compute_voice_breakdown(self, features: Dict[str, Any]) -> Dict[str, int]:
        """Compute voice sub-scores from features."""
        clarity = max(0, min(100, int(features.get("clarity_score", 50))))
        consistency = max(0, min(100, int(features.get("consistency_score", 50))))
        engagement = max(0, min(100, int(features.get("engagement_score", 50))))

        return {
            "clarity": clarity,
            "consistency": consistency,
            "engagement": engagement,
        }

    def _compute_body_breakdown(self, features: Dict[str, Any]) -> Dict[str, int]:
        """Compute body sub-scores from features."""
        posture_raw = features.get("posture_stability", 0.5)
        posture = max(0, min(100, int(posture_raw * 100) if posture_raw <= 1 else int(posture_raw)))
        stability = max(0, min(100, int(features.get("stability_score", 50))))
        expressiveness = max(0, min(100, int(features.get("expressiveness_score", 50))))

        return {
            "posture": posture,
            "stability": stability,
            "expressiveness": expressiveness,
        }

    def generate_full_report(
        self,
        voice_features: Dict[str, Any],
        body_features: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate complete analysis report with scores and recommendations."""
        scores = self.calculate_scores(voice_features, body_features)

        report = self.report_generator.generate_report(
            scores=scores,
            voice_features=voice_features,
            body_features=body_features,
            voice_breakdown=scores["voice_breakdown"],
            body_breakdown=scores["body_breakdown"],
        )

        # Merge scores into report
        report.update(scores)
        return report