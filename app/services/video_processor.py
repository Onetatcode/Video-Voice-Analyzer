import os
import tempfile
import subprocess
import logging
from typing import Tuple, Optional
from pathlib import Path

import cv2
import numpy as np
import librosa
from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)


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
        """
        Extract sampled frames from video for body language analysis.
        Returns list of frames as numpy arrays.
        """
        frames = []
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Could not open video: {video_path}")
            return frames

        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            # Calculate frame indices to sample
            if total_frames <= max_frames:
                frame_indices = list(range(total_frames))
            else:
                frame_indices = list(range(0, total_frames, total_frames // max_frames))[:max_frames]

            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
                else:
                    break
        finally:
            cap.release()

        logger.info(f"Extracted {len(frames)} frames from {video_path}")
        return frames

    def extract_frames_at_intervals(self, video_path: str, interval_seconds: float = 1.0) -> list:
        """Extract frames at regular time intervals."""
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


class AudioProcessor:
    """Handles audio feature extraction for voice analysis."""

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate

    def load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """Load audio file and return waveform and sample rate."""
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            return y, sr
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
            # 1. Speech pace (words per minute) - estimate from speech segments
            speech_pace = self._estimate_speech_pace(y, sr)

            # 2. Pitch variation
            pitch_variation = self._compute_pitch_variation(y, sr)

            # 3. Filler word count (basic heuristic)
            filler_count = self._estimate_filler_words(y, sr)

            # 4. Pause frequency and duration
            pause_freq, avg_pause_dur = self._analyze_pauses(y, sr)

            # 5. Total duration
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
        """Estimate words per minute from speech segments."""
        # Use spectral centroid and energy to detect speech segments
        # This is a simplified heuristic
        duration = len(y) / sr
        # Rough estimate: average speaking rate is ~130-150 wpm
        # We'll use a heuristic based on speech activity
        energy = librosa.feature.rms(y=y)[0]
        speech_frames = np.sum(energy > np.mean(energy) * 0.5)
        speech_ratio = speech_frames / len(energy) if len(energy) > 0 else 0
        # Estimate WPM based on speech activity
        estimated_wpm = 130 * speech_ratio + 20 * (1 - speech_ratio)
        return round(estimated_wpm, 1)

    def _compute_pitch_variation(self, y: np.ndarray, sr: int) -> float:
        """Compute pitch variation (standard deviation of fundamental frequency)."""
        try:
            f0, voiced_flag, _ = librosa.pyin(
                y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr
            )
            voiced_f0 = f0[voiced_flag]
            if len(voiced_f0) > 0:
                return round(float(np.std(voiced_f0)), 2)
        except Exception:
            pass
        return 0.0

    def _estimate_filler_words(self, y: np.ndarray, sr: int) -> int:
        """Estimate filler word count using spectral features."""
        # This is a very rough heuristic - in production would use ASR
        # For now, return a reasonable estimate based on pause patterns
        try:
            # Count short pauses that might indicate filler words
            energy = librosa.feature.rms(y=y)[0]
            low_energy = energy < np.percentile(energy, 25)
            # Count transitions from low to high energy (potential filler starts)
            transitions = np.sum(np.diff(low_energy.astype(int)) > 0)
            return max(0, int(transitions * 0.3))  # Rough scaling
        except Exception:
            return 0

    def _analyze_pauses(self, y: np.ndarray, sr: int) -> Tuple[float, float]:
        """Analyze pause frequency and average duration."""
        try:
            energy = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
            threshold = np.mean(energy) * 0.3
            is_speech = energy > threshold

            # Find pause segments (continuous non-speech)
            pauses = []
            in_pause = False
            pause_start = 0

            for i, speech in enumerate(is_speech):
                if not speech and not in_pause:
                    in_pause = True
                    pause_start = i
                elif speech and in_pause:
                    in_pause = False
                    pause_duration = (i - pause_start) * 512 / sr  # hop_length=512
                    if pause_duration > 0.2:  # Ignore very short pauses
                        pauses.append(pause_duration)

            if pauses:
                pause_frequency = len(pauses) / (len(y) / sr) * 60  # pauses per minute
                avg_pause_duration = np.mean(pauses)
                return round(pause_frequency, 1), round(avg_pause_duration, 2)
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