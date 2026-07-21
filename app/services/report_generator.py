import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

GROQ_TEXT_MODEL = "llama-3.1-8b-instant"


class ReportGenerator:
    """Generates analysis reports with AI-powered feedback via Hugging Face Inference API."""

    # Template fallback when Gemini is unavailable or fails
    STRENGTH_TEMPLATES = {
        "voice_clarity": ["Your speech was clear and well-articulated throughout the presentation."],
        "voice_consistency": ["Your speaking pace was steady and consistent, showing good control."],
        "voice_engagement": ["Good vocal variety kept the audience interested and engaged."],
        "body_posture": ["Strong, upright posture projected confidence and authority."],
        "body_stability": ["Minimal fidgeting demonstrated calmness and self-assurance."],
        "body_expressiveness": ["Natural gestures enhanced your verbal communication effectively."],
        "eye_contact": ["Excellent eye contact created strong connection with the audience."],
    }

    WEAKNESS_TEMPLATES = {
        "voice_clarity": ["Work on enunciating words more clearly, especially technical terms."],
        "voice_consistency": ["Your speaking pace varied - try to maintain a steadier rhythm."],
        "voice_engagement": ["Add more vocal variety - vary pitch and emphasis for key points."],
        "body_posture": ["Focus on keeping shoulders back and head aligned over shoulders."],
        "body_stability": ["Reduce fidgeting by practicing with hands clasped or at sides."],
        "body_expressiveness": ["Incorporate more purposeful gestures to emphasize key points."],
        "eye_contact": ["Practice looking directly at the camera more consistently."],
    }

    TIP_TEMPLATES = [
        "Map one purposeful gesture to each of your 3 main points.",
        "Record yourself practicing and review for 3 specific improvements.",
        "Try the 'power pose' for 2 minutes before your next presentation.",
        "Practice your opening and closing 5 times - they matter most.",
        "Use the 3-second pause rule after important points for emphasis.",
        "Place a sticky note at camera level as an eye contact reminder.",
        "Practice with a friend and ask for specific feedback on body language.",
    ]

    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY", "")

    def generate_report(
        self,
        scores: Dict[str, int],
        voice_features: Dict[str, Any],
        body_features: Dict[str, Any],
        voice_breakdown: Optional[Dict[str, Any]] = None,
        body_breakdown: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate report with AI-powered or template-based feedback.
        Tries Gemini first, falls back to templates on any failure.
        """
        confidence_score = scores.get("confidence_score", 0)
        voice_score = scores.get("voice_score", 0)
        body_score = scores.get("body_score", 0)

        if confidence_score >= 80:
            level = "Excellent"
        elif confidence_score >= 65:
            level = "Good"
        elif confidence_score >= 50:
            level = "Fair"
        else:
            level = "Needs Improvement"

        strengths, weaknesses, tips = self._generate_with_hf(
            scores, voice_features, body_features
        )
        if not strengths:
            strengths = self._template_strengths(voice_features, body_features, voice_score, body_score)
            weaknesses = self._template_weaknesses(voice_features, body_features, voice_score, body_score)
            tips = self._template_tips(weaknesses, confidence_score)

        return {
            "level": level,
            "confidence_score": confidence_score,
            "voice_score": voice_score,
            "body_score": body_score,
            "strengths": strengths[:3],
            "weaknesses": weaknesses[:3],
            "tips": tips[:3],
            "voice_breakdown": scores.get("voice_breakdown"),
            "body_breakdown": scores.get("body_breakdown"),
            "generated_at": datetime.utcnow().isoformat(),
            "summary": self._generate_summary(level, confidence_score, strengths[:1], weaknesses[:1]),
        }

    def _build_prompt(
        self,
        scores: Dict[str, Any],
        voice_features: Dict[str, Any],
        body_features: Dict[str, Any],
    ) -> str:
        """Build structured prompt for Gemini with actual analysis data."""
        vf = voice_features
        bf = body_features
        transcript = vf.get("transcript", "")

        prompt_parts = [f"""You are an expert public speaking coach. Analyze these metrics from a user's video and generate concise, personalized feedback.

SPEECH METRICS:
- Speaking pace: {vf.get('speech_pace', 0):.1f} words per minute (ideal: 110-160)
- Word count: {vf.get('word_count', 0)}
- Pitch variation: {vf.get('pitch_variation', 0):.1f} Hz std dev (higher = more vocal variety)
- Filler word count: {vf.get('filler_word_count', 0)} (lower is better)
- Pause frequency: {vf.get('pause_frequency', 0):.1f} pauses per minute
- Average pause duration: {vf.get('avg_pause_duration', 0):.2f}s
- Speech duration: {vf.get('total_duration', 0):.1f}s

VOICE SUB-SCORES (0-100):
- Clarity: {vf.get('clarity_score', 50)}
- Consistency: {vf.get('consistency_score', 50)}
- Engagement: {vf.get('engagement_score', 50)}

BODY LANGUAGE METRICS:
- Posture stability: {bf.get('posture_stability', 0.5):.2f} (0-1, higher = better)
- Eye contact ratio: {bf.get('eye_contact_ratio', 0.5):.2f} (0-1, % time facing camera)
- Gesture frequency: {bf.get('gesture_frequency', 0):.1f} gestures per minute
- Movement frequency: {bf.get('movement_frequency', 0):.1f} movements per minute
- Head nod count: {bf.get('head_nod_count', 0)}
- Shoulder movement score: {bf.get('shoulder_movement_score', 0.5):.2f} (0-1, lower = more stable)

OVERALL SCORES (0-100):
- Voice score: {scores.get('voice_score', 0)}
- Body language score: {scores.get('body_score', 0)}
- Overall confidence: {scores.get('confidence_score', 0)}"""]

        if transcript:
            prompt_parts.append(f"""
SPEECH TRANSCRIPT (delimited by --- markers):
---{transcript}---

Analyze the transcript for content quality, clarity of expression, sentence structure, use of jargon, and overall coherence. Reference specific words or phrases from the transcript in your feedback.""")

        prompt_parts.append("""
Generate a JSON response with exactly three arrays:
1. "strengths" - 3 specific strengths based on their best metrics AND transcript content
2. "weaknesses" - 3 specific areas to improve based on their weakest metrics AND transcript content
3. "tips" - 3 actionable, concrete tips addressing their specific weaknesses

Rules:
- Be SPECIFIC. Reference actual numbers from their data (e.g., "Your speech pace of 92 WPM is slightly below the ideal 110-160 range")
- If transcript is available, reference specific words or phrases they used
- Make tips actionable (something they can practice today)
- Keep each item to 1-2 sentences
- Do NOT use generic platitudes
- Return ONLY valid JSON, no markdown formatting""")

        return "\n".join(prompt_parts)

    def _generate_with_hf(
        self,
        scores: Dict[str, Any],
        voice_features: Dict[str, Any],
        body_features: Dict[str, Any],
    ) -> tuple:
        """Generate feedback via Groq API (Llama-3.1-8B). Returns ([], [], []) on failure."""
        if not self.groq_key:
            return [], [], []

        try:
            prompt = self._build_prompt(scores, voice_features, body_features)
            import requests
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.groq_key}"},
                json={
                    "model": GROQ_TEXT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1024,
                },
                timeout=60,
            )
            if resp.status_code != 200:
                logger.warning(f"Groq API returned {resp.status_code}: {resp.text[:200]}")
                return [], [], []

            text = resp.json()["choices"][0]["message"]["content"]
            start = text.find('{')
            end = text.rfind('}')
            if start == -1 or end == -1:
                logger.warning("Groq response contains no JSON")
                return [], [], []
            text = text[start:end+1]
            # Fix common JSON issues from LLM output
            text = text.replace("'", '"')  # single quotes → double
            import re
            text = re.sub(r',\s*([}\]])', r'\1', text)  # trailing commas
            data = json.loads(text)
            def _text(item):
                if isinstance(item, dict):
                    return item.get("tip") or item.get("detail") or item.get("text") or item.get("strength") or item.get("weakness") or str(item)
                return str(item)
            strengths = [_text(s) for s in data.get("strengths", [])]
            weaknesses = [_text(w) for w in data.get("weaknesses", [])]
            tips = [_text(t) for t in data.get("tips", [])]
            if not (strengths and weaknesses and tips):
                logger.warning("Groq returned incomplete response")
                return [], [], []

            logger.info("Groq report generated successfully")
            return strengths, weaknesses, tips

        except Exception as e:
            logger.error(f"Groq report generation failed: {e}")
            return [], [], []

    def _template_strengths(self, voice_features, body_features, voice_score, body_score) -> List[str]:
        strengths = []
        if voice_score >= 70:
            if voice_features.get("clarity_score", 50) >= 70:
                strengths.append(self.STRENGTH_TEMPLATES["voice_clarity"][0])
            if voice_features.get("consistency_score", 50) >= 70:
                strengths.append(self.STRENGTH_TEMPLATES["voice_consistency"][0])
            if voice_features.get("engagement_score", 50) >= 70:
                strengths.append(self.STRENGTH_TEMPLATES["voice_engagement"][0])
        if body_score >= 70:
            if body_features.get("posture_score", 50) >= 70:
                strengths.append(self.STRENGTH_TEMPLATES["body_posture"][0])
            if body_features.get("stability_score", 50) >= 70:
                strengths.append(self.STRENGTH_TEMPLATES["body_stability"][0])
            if body_features.get("expressiveness_score", 50) >= 70:
                strengths.append(self.STRENGTH_TEMPLATES["body_expressiveness"][0])
            if body_features.get("eye_contact_ratio", 0.5) >= 0.7:
                strengths.append(self.STRENGTH_TEMPLATES["eye_contact"][0])
        if not strengths:
            strengths.append("Consistent effort shows commitment to improving your presentation skills.")
        return strengths

    def _template_weaknesses(self, voice_features, body_features, voice_score, body_score) -> List[str]:
        weaknesses = []
        if voice_score < 70:
            if voice_features.get("clarity_score", 50) < 60:
                weaknesses.append(self.WEAKNESS_TEMPLATES["voice_clarity"][0])
            if voice_features.get("consistency_score", 50) < 60:
                weaknesses.append(self.WEAKNESS_TEMPLATES["voice_consistency"][0])
            if voice_features.get("engagement_score", 50) < 60:
                weaknesses.append(self.WEAKNESS_TEMPLATES["voice_engagement"][0])
        if body_score < 70:
            if body_features.get("posture_score", 50) < 60:
                weaknesses.append(self.WEAKNESS_TEMPLATES["body_posture"][0])
            if body_features.get("stability_score", 50) < 60:
                weaknesses.append(self.WEAKNESS_TEMPLATES["body_stability"][0])
            if body_features.get("expressiveness_score", 50) < 60:
                weaknesses.append(self.WEAKNESS_TEMPLATES["body_expressiveness"][0])
            if body_features.get("eye_contact_ratio", 0.5) < 0.6:
                weaknesses.append(self.WEAKNESS_TEMPLATES["eye_contact"][0])
        if not weaknesses:
            weaknesses.append("Continue refining your delivery to reach the next level.")
        return weaknesses

    def _template_tips(self, weaknesses: List, confidence_score: int) -> List[str]:
        def _text(item):
            if isinstance(item, dict):
                return item.get("text", item.get("weakness", str(item)))
            return str(item)
        tips = list(self.TIP_TEMPLATES)
        w_texts = [_text(w) for w in weaknesses]
        if any("posture" in w.lower() for w in w_texts):
            tips.insert(0, "Practice wall-standing: back against wall, heels 6 inches out for 1 minute daily.")
        if any("eye contact" in w.lower() for w in w_texts):
            tips.insert(0, "Place a small dot near your camera lens - glance at it every 5 seconds.")
        if any("pace" in w.lower() or "consistency" in w.lower() for w in w_texts):
            tips.insert(0, "Use a metronome app at 130 BPM to build steady rhythm.")
        if any("gesture" in w.lower() or "express" in w.lower() for w in w_texts):
            tips.insert(0, "Map one purposeful gesture to each of your 3 main points.")
        if confidence_score < 50:
            tips.insert(0, "Start with 2-minute daily power poses to boost confidence.")
        return tips[:5]

    def _generate_summary(self, level, confidence_score, top_strength, top_weakness) -> str:
        def _text(item):
            if isinstance(item, dict):
                return item.get("text", item.get("strength", item.get("weakness", str(item))))
            return str(item)
        st = _text(top_strength[0]) if top_strength else "consistent effort"
        wt = _text(top_weakness[0]) if top_weakness else "areas for growth"
        return (
            f"Your presentation scored {confidence_score}/100 ({level}). "
            f"Strength: {st.lower()}. "
            f"Focus area: {wt.lower()}."
        )
