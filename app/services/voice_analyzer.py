import numpy as np
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .video_processor import AudioProcessor

logger = logging.getLogger(__name__)


class VoiceAnalyzer:
    """Analyzes voice features for confidence scoring."""

    def __init__(self):
        self.audio_processor = AudioProcessor()

    def analyze(self, audio_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive voice analysis.
        Returns dict with all voice features needed for scoring.
        """
        try:
            # Extract base features
            features = self.audio_processor.extract_voice_features(audio_path)

            # Additional analysis
            features["clarity_score"] = self._compute_clarity_score(features)
            features["consistency_score"] = self._compute_consistency_score(features)
            features["engagement_score"] = self._compute_engagement_score(features)

            return features
        except Exception as e:
            logger.error(f"Voice analysis failed: {e}")
            return self._empty_analysis()

    def _compute_clarity_score(self, features: Dict) -> float:
        """Compute speech clarity score (0-100)."""
        score = 50.0  # base

        # Speech pace: ideal range 110-160 WPM
        pace = features.get("speech_pace", 0)
        if 110 <= pace <= 160:
            score += 20
        elif 90 <= pace <= 180:
            score += 10
        else:
            score -= 10

        # Pitch variation: moderate variation is good
        pitch_var = features.get("pitch_variation", 0)
        if 20 <= pitch_var <= 80:
            score += 15
        elif pitch_var > 0:
            score += 5

        # Low filler words is good
        filler = features.get("filler_word_count", 0)
        if filler <= 3:
            score += 15
        elif filler <= 6:
            score += 5
        else:
            score -= 10

        return max(0, min(100, score))

    def _compute_consistency_score(self, features: Dict) -> float:
        """Compute speech consistency score (0-100)."""
        score = 50.0

        # Pause frequency: moderate is good
        pause_freq = features.get("pause_frequency", 0)
        if 5 <= pause_freq <= 15:
            score += 20
        elif 3 <= pause_freq <= 20:
            score += 10
        elif pause_freq > 25:
            score -= 15

        # Average pause duration
        avg_pause = features.get("avg_pause_duration", 0)
        if 0.3 <= avg_pause <= 1.5:
            score += 15
        elif avg_pause > 0:
            score += 5

        # Pitch stability
        pitch_var = features.get("pitch_variation", 0)
        if pitch_var > 0 and pitch_var < 100:
            score += 10

        return max(0, min(100, score))

    def _compute_engagement_score(self, features: Dict) -> float:
        """Compute vocal engagement score (0-100)."""
        score = 50.0

        # Speech pace energy
        pace = features.get("speech_pace", 0)
        if 120 <= pace <= 150:
            score += 20
        elif 100 <= pace <= 170:
            score += 10

        # Pitch variation indicates expressiveness
        pitch_var = features.get("pitch_variation", 0)
        if 30 <= pitch_var <= 100:
            score += 15
        elif pitch_var > 10:
            score += 5

        # Low filler words = more engaging
        filler = features.get("filler_word_count", 0)
        if filler <= 2:
            score += 15
        elif filler <= 4:
            score += 10
        else:
            score -= 5

        return max(0, min(100, score))

    def _empty_analysis(self) -> Dict[str, Any]:
        return {
            "speech_pace": 0.0,
            "pitch_variation": 0.0,
            "filler_word_count": 0,
            "pause_frequency": 0.0,
            "avg_pause_duration": 0.0,
            "total_duration": 0.0,
            "clarity_score": 0.0,
            "consistency_score": 0.0,
            "engagement_score": 0.0,
        }