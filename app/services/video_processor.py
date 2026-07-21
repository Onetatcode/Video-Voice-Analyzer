import os
import tempfile
import subprocess
import logging
from typing import Tuple, Optional
from pathlib import Path

import numpy as np
from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)

# Lazy cv2 import — gracefully degrade when DLL blocked by WDAC/AppLocker
def _import_cv2():
    """Import cv2, returning None if unavailable or partially loaded."""
    import sys
    if 'cv2' in sys.modules:
        cv2 = sys.modules['cv2']
        if hasattr(cv2, 'VideoCapture'):
            return cv2
        del sys.modules['cv2']

    try:
        import cv2
        if hasattr(cv2, 'VideoCapture'):
            return cv2
        logger.warning("cv2 imported but not fully functional")
        return None
    except ImportError:
        logger.warning("cv2 (OpenCV) not available — skipping video/body analysis")
        return None


class VideoProcessor:
    """Handles video/audio extraction and frame sampling from video files."""

    def __init__(self, frame_sample_rate: int = 5):
        """
        Args:
            frame_sample_rate: Sample 1 frame every N frames (default 5)
        """
        self.frame_sample_rate = frame_sample_rate

    def download_video(self, video_url: str, output_path: str, supabase_client=None) -> bool:
        """
        Download video from URL to local path.
        For Supabase Storage, we can use the Supabase client to download directly.
        """
        try:
            # If we have a Supabase client and the URL is from Supabase storage, use the client to download
            if supabase_client and "supabase.co/storage" in video_url:
                # Extract the file path from the URL
                # URL format: https://<project>.supabase.co/storage/v1/object/public/<bucket>/<path>
                import urllib.parse
                parsed = urllib.parse.urlparse(video_url)
                path_parts = parsed.path.split('/')
                # Find the bucket name and file path
                try:
                    bucket_idx = path_parts.index('videos')
                    bucket_name = 'videos'
                    file_path = '/'.join(path_parts[bucket_idx + 1:])
                    
                    # Download using Supabase client
                    file_data = supabase_client.storage.from_(bucket_name).download(file_path)
                    with open(output_path, 'wb') as f:
                        f.write(file_data)
                    logger.info(f"Downloaded video via Supabase client: {output_path}")
                    return True
                except (ValueError, IndexError) as e:
                    logger.warning(f"Could not parse Supabase URL, falling back to direct download: {e}")
            
            # Fallback to direct HTTP download
            import requests
            response = requests.get(video_url, stream=True, timeout=60)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            logger.error(f"Failed to download video from {video_url}: {e}")
            return False

    def extract_audio(self, video_path: str, output_audio_path: str) -> bool:
        """Extract audio track from video file."""
        try:
            video = VideoFileClip(video_path)
            if video.audio is None:
                logger.warning(f"No audio track in video: {video_path}")
                return False
            video.audio.write_audiofile(output_audio_path, logger=None)
            video.close()
            return True
        except Exception as e:
            logger.error(f"Failed to extract audio from {video_path}: {e}")
            return False

    def get_video_info(self, video_path: str) -> dict:
        """Get basic video metadata."""
        cv2 = _import_cv2()
        if cv2 is None:
            return {"fps": 0, "frame_count": 0, "width": 0, "height": 0, "duration": 0}

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {}
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            return {
                "fps": fps,
                "frame_count": frame_count,
                "width": width,
                "height": height,
                "duration": duration,
            }
        finally:
            cap.release()

    def extract_frames(self, video_path: str, max_frames: int = 100) -> list:
        """Extract sampled frames for body language analysis. Falls back to moviepy if cv2 unavailable."""
        cv2 = _import_cv2()
        if cv2 is not None:
            frames = []
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Could not open video: {video_path}")
                return frames
            try:
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if total_frames <= max_frames:
                    frame_indices = list(range(total_frames))
                else:
                    frame_indices = list(range(0, total_frames, total_frames // max_frames))[:max_frames]
                for idx in frame_indices:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                    ret, frame = cap.read()
                    if ret:
                        frames.append(frame)
            finally:
                cap.release()
            logger.info(f"Extracted {len(frames)} frames from {video_path}")
            return frames

        # Fallback: moviepy-based frame extraction (no cv2 needed)
        logger.info("cv2 unavailable — extracting frames with moviepy")
        try:
            from moviepy.editor import VideoFileClip
            import numpy as np
            clip = VideoFileClip(video_path)
            duration = clip.duration
            num_frames = min(max_frames, max(1, int(duration)))
            times = np.linspace(0, duration, num_frames)
            frames = [clip.get_frame(t) for t in times]
            clip.close()
            logger.info(f"Extracted {len(frames)} frames via moviepy from {video_path}")
            return frames
        except Exception as e:
            logger.warning(f"Moviepy frame extraction failed: {e}")
            return []

    def extract_frames_at_intervals(self, video_path: str, interval_seconds: float = 1.0) -> list:
        """Extract frames at regular time intervals."""
        cv2 = _import_cv2()
        if cv2 is not None:
            frames = []
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return frames
            try:
                fps = cap.get(cv2.CAP_PROP_FPS)
                if fps <= 0:
                    return frames
                frame_interval = int(fps * interval_seconds)
                frame_idx = 0
                while True:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frames.append(frame)
                    frame_idx += frame_interval
            finally:
                cap.release()
            return frames

        # Fallback: moviepy
        try:
            from moviepy.editor import VideoFileClip
            import numpy as np
            clip = VideoFileClip(video_path)
            duration = clip.duration
            times = np.arange(0, duration, interval_seconds)
            frames = [clip.get_frame(t) for t in times]
            clip.close()
            return frames
        except Exception:
            return []


class AudioProcessor:
    """Handles audio feature extraction for voice analysis using pydub+numpy (no librosa native DLLs)."""

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate

    def _load_pydub(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """Load audio via pydub (ffmpeg subprocess, no native Python DLLs)."""
        from pydub import AudioSegment
        audio = AudioSegment.from_file(audio_path)
        audio = audio.set_frame_rate(self.sample_rate).set_channels(1)
        y = np.array(audio.get_array_of_samples()).astype(np.float32) / 32768.0
        return y, self.sample_rate

    def _rms_energy(self, y: np.ndarray, frame_length: int = 2048, hop_length: int = 512) -> np.ndarray:
        """Compute RMS energy per frame (numpy equivalent of librosa.feature.rms)."""
        frames = []
        for i in range(0, len(y) - frame_length + 1, hop_length):
            frame = y[i:i + frame_length]
            frames.append(np.sqrt(np.mean(frame ** 2)))
        return np.array(frames) if frames else np.array([0.0])

    def transcribe(self, audio_path: str) -> str:
        """Transcribe audio via Groq API (whisper-large-v3). Returns transcript or empty."""
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            logger.warning("GROQ_API_KEY not set — STT unavailable")
            return ""
        try:
            import requests
            with open(audio_path, "rb") as f:
                files = {"file": ("audio.wav", f, "audio/wav")}
                resp = requests.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    files=files,
                    data={"model": "whisper-large-v3", "language": "en"},
                    timeout=120,
                )
            if resp.status_code == 200:
                text = resp.json().get("text", "")
                logger.info(f"Groq STT: {len(text.split())} words")
                return text.strip()
            else:
                logger.warning(f"Groq STT returned {resp.status_code}: {resp.text[:200]}")
                return ""
        except Exception as e:
            logger.warning(f"Groq STT failed: {e}")
            return ""

    def load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """Load audio file and return waveform and sample rate."""
        try:
            return self._load_pydub(audio_path)
        except Exception as e:
            logger.error(f"Failed to load audio {audio_path}: {e}")
            return np.array([]), self.sample_rate

    def extract_voice_features(self, audio_path: str) -> dict:
        """
        Extract voice features for confidence analysis.
        Returns dict with speech pace, pitch variation, filler words, pauses, etc.
        """
        y, sr = self.load_audio(audio_path)
        if len(y) == 0:
            return self._empty_features()

        try:
            speech_pace = self._estimate_speech_pace(y, sr)
            pitch_variation = self._compute_pitch_variation(y, sr)
            filler_count = self._estimate_filler_words(y, sr)
            pause_freq, avg_pause_dur = self._analyze_pauses(y, sr)
            total_duration = len(y) / sr

            return {
                "speech_pace": speech_pace,
                "pitch_variation": pitch_variation,
                "filler_word_count": filler_count,
                "pause_frequency": pause_freq,
                "avg_pause_duration": avg_pause_dur,
                "total_duration": total_duration,
            }
        except Exception as e:
            logger.error(f"Error extracting voice features: {e}")
            return self._empty_features()

    def _estimate_speech_pace(self, y: np.ndarray, sr: int) -> float:
        """Estimate words per minute using RMS energy threshold."""
        energy = self._rms_energy(y)
        if len(energy) == 0:
            return 0.0
        speech_frames = float(np.sum(energy > np.mean(energy) * 0.5))
        speech_ratio = speech_frames / len(energy)
        estimated_wpm = 130 * speech_ratio + 20 * (1 - speech_ratio)
        return round(estimated_wpm, 1)

    def _compute_pitch_variation(self, y: np.ndarray, sr: int) -> float:
        """Compute pitch variation via numpy autocorrelation."""
        try:
            frame_length = 2048
            hop_length = 512
            min_freq = 65.0   # C2
            max_freq = 2093.0  # C7
            min_period = int(sr / max_freq)
            max_period = int(sr / min_freq)
            f0s = []
            for start in range(0, len(y) - frame_length, hop_length):
                frame = y[start:start + frame_length]
                frame = frame - np.mean(frame)
                corr = np.correlate(frame, frame, mode="same")
                mid = len(corr) // 2
                lo = mid + min_period
                hi = min(mid + max_period, len(corr))
                if lo >= hi:
                    continue
                segment = corr[lo:hi]
                if len(segment) == 0:
                    continue
                peak = np.argmax(segment)
                conf = corr[lo + peak] / (corr[mid] + 1e-10)
                if conf > 0.3:
                    f0s.append(sr / (lo - mid + peak))
            if len(f0s) >= 2:
                return round(float(np.std(f0s)), 2)
        except Exception:
            pass
        return 0.0

    def _estimate_filler_words(self, y: np.ndarray, sr: int) -> int:
        """Estimate filler word count from energy transitions."""
        try:
            energy = self._rms_energy(y)
            low_energy = energy < np.percentile(energy, 25)
            transitions = np.sum(np.diff(low_energy.astype(int)) > 0)
            return max(0, int(transitions * 0.3))
        except Exception:
            return 0

    def _analyze_pauses(self, y: np.ndarray, sr: int) -> Tuple[float, float]:
        """Analyze pause frequency and average duration."""
        try:
            hop_length = 512
            energy = self._rms_energy(y, hop_length=hop_length)
            if len(energy) == 0:
                return 0.0, 0.0
            threshold = np.mean(energy) * 0.3
            is_speech = energy > threshold

            pauses = []
            in_pause = False
            pause_start = 0
            for i, speech in enumerate(is_speech):
                if not speech and not in_pause:
                    in_pause = True
                    pause_start = i
                elif speech and in_pause:
                    in_pause = False
                    pause_dur = (i - pause_start) * hop_length / sr
                    if pause_dur > 0.2:
                        pauses.append(pause_dur)
            if pauses:
                freq = len(pauses) / (len(y) / sr) * 60
                avg = float(np.mean(pauses))
                return round(freq, 1), round(avg, 2)
        except Exception:
            pass
        return 0.0, 0.0

    def _empty_features(self) -> dict:
        return {
            "speech_pace": 0.0,
            "pitch_variation": 0.0,
            "filler_word_count": 0,
            "pause_frequency": 0.0,
            "avg_pause_duration": 0.0,
            "total_duration": 0.0,
        }