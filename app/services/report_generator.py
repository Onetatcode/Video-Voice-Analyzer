import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates final analysis reports from scores and features."""

    # Template strings for report generation
    STRENGTH_TEMPLATES = {
        "voice_clarity": [
            "Your speech was clear and well-articulated throughout the presentation.",
            "Excellent diction and pronunciation made your message easy to follow.",
            "You spoke with good clarity, making your points accessible to the audience.",
        ],
        "voice_consistency": [
            "Your speaking pace was steady and consistent, showing good control.",
            "You maintained a reliable rhythm without rushing or dragging.",
            "Consistent vocal delivery helped maintain audience engagement.",
        ],
        "voice_engagement": [
            "Good vocal variety kept the audience interested and engaged.",
            "Effective use of pitch and tone emphasized key points well.",
            "Your voice conveyed enthusiasm and conviction about the topic.",
        ],
        "body_posture": [
            "Strong, upright posture projected confidence and authority.",
            "Good alignment of head, shoulders, and hips conveyed professionalism.",
            "Stable posture throughout showed composure and preparation.",
        ],
        "body_stability": [
            "Minimal fidgeting demonstrated calmness and self-assurance.",
            "Steady presence helped maintain audience focus on your message.",
            "Controlled movements reflected confidence in your material.",
        ],
        "body_expressiveness": [
            "Natural gestures enhanced your verbal communication effectively.",
            "Appropriate hand movements emphasized key points well.",
            "Dynamic body language kept the presentation visually engaging.",
        ],
        "eye_contact": [
            "Excellent eye contact created strong connection with the audience.",
            "Consistent facing of the camera showed engagement and confidence.",
            "Good eye contact helped establish trust and credibility.",
        ],
    }

    WEAKNESS_TEMPLATES = {
        "voice_clarity": [
            "Work on enunciating words more clearly, especially technical terms.",
            "Practice slowing down slightly to improve articulation.",
            "Consider voice exercises to strengthen diction and projection.",
        ],
        "voice_consistency": [
            "Your speaking pace varied - try to maintain a steadier rhythm.",
            "Practice with a metronome to develop more consistent timing.",
            "Record yourself to identify sections where pace changes unexpectedly.",
        ],
        "voice_engagement": [
            "Add more vocal variety - vary pitch and emphasis for key points.",
            "Practice emphasizing important words to avoid monotone delivery.",
            "Work on conveying more enthusiasm through vocal tone.",
        ],
        "body_posture": [
            "Focus on keeping shoulders back and head aligned over shoulders.",
            "Practice standing with weight evenly distributed on both feet.",
            "Consider posture exercises to strengthen core alignment.",
        ],
        "body_stability": [
            "Reduce fidgeting by practicing with hands clasped or at sides.",
            "Plant feet firmly to create a stable base for upper body.",
            "Practice mindfulness techniques to reduce nervous movements.",
        ],
        "body_expressiveness": [
            "Incorporate more purposeful gestures to emphasize key points.",
            "Practice using hands to illustrate concepts and transitions.",
            "Work on making movements feel more natural and less stiff.",
        ],
        "eye_contact": [
            "Practice looking directly at the camera more consistently.",
            "Position notes/screen to maintain camera-facing posture.",
            "Work on sustaining eye contact through entire sentences.",
        ],
    }

    TIP_TEMPLATES = [
        "Record yourself practicing and review for 3 specific improvements.",
        "Try the 'power pose' for 2 minutes before your next presentation.",
        "Practice your opening and closing 5 times - they matter most.",
        "Use the 3-second pause rule after important points for emphasis.",
        "Place a sticky note at camera level as an eye contact reminder.",
        "Time your presentation to ensure you stay within limits.",
        "Practice with a friend and ask for specific feedback on body language.",
        "Use hand gestures deliberately - one per main point is a good rule.",
    ]

    def generate_report(
        self,
        scores: Dict[str, int],
        voice_features: Dict[str, Any],
        body_features: Dict[str, Any],
        voice_breakdown: Optional[Dict[str, Any]] = None,
        body_breakdown: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate complete analysis report with strengths, weaknesses, and tips.
        """
        confidence_score = scores.get("confidence_score", 0)
        voice_score = scores.get("voice_score", 0)
        body_score = scores.get("body_score", 0)

        # Determine overall performance level
        if confidence_score >= 80:
            level = "Excellent"
        elif confidence_score >= 65:
            level = "Good"
        elif confidence_score >= 50:
            level = "Fair"
        else:
            level = "Needs Improvement"

        # Generate strengths, weaknesses, tips
        strengths = self._generate_strengths(voice_features, body_features, voice_score, body_score)
        weaknesses = self._generate_weaknesses(voice_features, body_features, voice_score, body_score)
        tips = self._generate_tips(weaknesses, confidence_score)

        # Limit to 2-3 each
        strengths = strengths[:3]
        weaknesses = weaknesses[:3]
        tips = tips[:3]

        return {
            "level": level,
            "confidence_score": confidence_score,
            "voice_score": voice_score,
            "body_score": body_score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "tips": tips,
            "voice_breakdown": voice_breakdown,
            "body_breakdown": body_breakdown,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": self._generate_summary(level, confidence_score, strengths[:1], weaknesses[:1]),
        }

    def _generate_strengths(
        self,
        voice_features: Dict[str, Any],
        body_features: Dict[str, Any],
        voice_score: int,
        body_score: int,
    ) -> List[str]:
        """Identify strengths based on scores and features."""
        strengths = []

        # Voice strengths
        if voice_score >= 70:
            if voice_features.get("clarity_score", 50) >= 70:
                strengths.append(self.STRENGTH_TEMPLATES["voice_clarity"][0])
            if voice_features.get("consistency_score", 50) >= 70:
                strengths.append(self.STRENGTH_TEMPLATES["voice_consistency"][0])
            if voice_features.get("engagement_score", 50) >= 70:
                strengths.append(self.STRENGTH_TEMPLATES["voice_engagement"][0])

        # Body strengths
        if body_score >= 70:
            if body_features.get("posture_score", 50) >= 70:
                strengths.append(self.STRENGTH_TEMPLATES["body_posture"][0])
            if body_features.get("stability_score", 50) >= 70:
                strengths.append(self.STRENGTH_TEMPLATES["body_stability"][0])
            if body_features.get("expressiveness_score", 50) >= 70:
                strengths.append(self.STRENGTH_TEMPLATES["body_expressiveness"][0])
            if body_features.get("eye_contact_ratio", 0.5) >= 0.7:
                strengths.append(self.STRENGTH_TEMPLATES["eye_contact"][0])

        return strengths

    def _generate_weaknesses(
        self,
        voice_features: Dict[str, Any],
        body_features: Dict[str, Any],
        voice_score: int,
        body_score: int,
    ) -> List[str]:
        """Identify areas for improvement."""
        weaknesses = []

        # Voice weaknesses
        if voice_score < 70:
            if voice_features.get("clarity_score", 50) < 60:
                weaknesses.append(self.WEAKNESS_TEMPLATES["voice_clarity"][0])
            if voice_features.get("consistency_score", 50) < 60:
                weaknesses.append(self.WEAKNESS_TEMPLATES["voice_consistency"][0])
            if voice_features.get("engagement_score", 50) < 60:
                weaknesses.append(self.WEAKNESS_TEMPLATES["voice_engagement"][0])

        # Body weaknesses
        if body_score < 70:
            if body_features.get("posture_score", 50) < 60:
                weaknesses.append(self.WEAKNESS_TEMPLATES["body_posture"][0])
            if body_features.get("stability_score", 50) < 60:
                weaknesses.append(self.WEAKNESS_TEMPLATES["body_stability"][0])
            if body_features.get("expressiveness_score", 50) < 60:
                weaknesses.append(self.WEAKNESS_TEMPLATES["body_expressiveness"][0])
            if body_features.get("eye_contact_ratio", 0.5) < 0.6:
                weaknesses.append(self.WEAKNESS_TEMPLATES["eye_contact"][0])

        return weaknesses

    def _generate_tips(self, weaknesses: List[str], confidence_score: int) -> List[str]:
        """Generate actionable tips based on weaknesses."""
        tips = list(self.TIP_TEMPLATES)

        # Add specific tips based on weaknesses
        if any("posture" in w.lower() for w in weaknesses):
            tips.insert(0, "Practice wall-standing: back against wall, heels 6 inches out, touch head/shoulders/hips to wall for 1 minute daily.")

        if any("eye contact" in w.lower() for w in weaknesses):
            tips.insert(0, "Place a small colored dot or photo near your camera lens - glance at it every 5 seconds.")

        if any("pace" in w.lower() or "consistency" in w.lower() for w in weaknesses):
            tips.insert(0, "Use a metronome app at 130 BPM while practicing to build steady rhythm.")

        if any("gesture" in w.lower() or "express" in w.lower() for w in weaknesses):
            tips.insert(0, "Map one purposeful gesture to each of your 3 main points.")

        if confidence_score < 50:
            tips.insert(0, "Start with 2-minute daily power poses - research shows this boosts confidence hormones.")

        return tips[:5]  # Return top 5 tips

    def _generate_summary(
        self,
        level: str,
        confidence_score: int,
        top_strength: Optional[List[str]],
        top_weakness: Optional[List[str]],
    ) -> str:
        """Generate a brief summary paragraph."""
        strength_text = top_strength[0] if top_strength else "consistent effort"
        weakness_text = top_weakness[0] if top_weakness else "areas for growth"

        return (
            f"Your presentation scored {confidence_score}/100 ({level}). "
            f"Strength: {strength_text.lower()}. "
            f"Focus area: {weakness_text.lower()}. "
            f"With targeted practice on the suggested tips, you can significantly improve your confidence and delivery."
        )