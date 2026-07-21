import os
import logging
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

COCO_KEYPOINTS = {
    "nose": 0, "left_eye": 1, "right_eye": 2, "left_ear": 3, "right_ear": 4,
    "left_shoulder": 5, "right_shoulder": 6, "left_elbow": 7, "right_elbow": 8,
    "left_wrist": 9, "right_wrist": 10, "left_hip": 11, "right_hip": 12,
    "left_knee": 13, "right_knee": 14, "left_ankle": 15, "right_ankle": 16,
}

KEYPOINT_NAMES = {v: k for k, v in COCO_KEYPOINTS.items()}

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "yolov8n-pose.onnx")


class BodyAnalyzer:
    """Analyzes body language using local YOLOv8-pose ONNX model (no native DLLs)."""

    def __init__(self, api_key: Optional[str] = None, model_id: str = ""):
        self.api_key = api_key or os.getenv("ROBOFLOW_API_KEY", "")
        self.model_id = model_id or ""
        self._session = None
        self._ort_session = None

    def _load_onnx(self):
        if self._ort_session is not None:
            return
        try:
            import onnxruntime
            if os.path.exists(MODEL_PATH):
                self._ort_session = onnxruntime.InferenceSession(
                    MODEL_PATH, providers=["CPUExecutionProvider"]
                )
                logger.info(f"Loaded ONNX model: {MODEL_PATH}")
            else:
                logger.warning(f"ONNX model not found at {MODEL_PATH}")
        except Exception as e:
            logger.warning(f"Failed to load ONNX Runtime: {e}")

    def _onnx_infer(self, frame: np.ndarray) -> Optional[List[np.ndarray]]:
        if self._ort_session is None:
            return None
        try:
            img = Image.fromarray(frame).resize((640, 640), Image.LANCZOS)
            img_np = np.array(img, dtype=np.float32) / 255.0
            input_tensor = img_np.transpose(2, 0, 1)[np.newaxis, :, :, :].astype(np.float32)
            input_name = self._ort_session.get_inputs()[0].name
            outputs = self._ort_session.run(None, {input_name: input_tensor})
            return outputs
        except Exception as e:
            logger.warning(f"ONNX inference failed: {e}")
            return None

    def _parse_onnx_keypoints(self, outputs: List[np.ndarray]) -> Optional[Dict[int, Tuple[float, float, float]]]:
        out = outputs[0]
        if out.shape != (1, 56, 8400):
            logger.warning(f"Unexpected ONNX output shape: {out.shape}")
            return None
        data = out[0]
        raw_scores = data[4, :]
        best_idx = int(np.argmax(raw_scores))
        best_conf = 1.0 / (1.0 + np.exp(-raw_scores[best_idx]))
        if best_conf < 0.3:
            return None
        keypoints = {}
        for kpt_idx in range(17):
            x = float(data[5 + kpt_idx * 3, best_idx]) / 640.0
            y = float(data[5 + kpt_idx * 3 + 1, best_idx]) / 640.0
            conf = float(data[5 + kpt_idx * 3 + 2, best_idx])
            if conf > 0.1:
                keypoints[kpt_idx] = (x, y, conf)
        return keypoints if len(keypoints) >= 3 else None

    def _roboflow_infer(self, frame: np.ndarray) -> Optional[Dict]:
        if not self.api_key or not self.model_id:
            return None
        try:
            import base64
            from io import BytesIO
            import requests as req
            pil_img = Image.fromarray(frame)
            buffer = BytesIO()
            pil_img.save(buffer, format="JPEG")
            img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            if self._session is None:
                self._session = req.Session()
            resp = self._session.post(
                f"https://detect.roboflow.com/{self.model_id}",
                params={"api_key": self.api_key},
                json={"image": f"data:image/jpeg;base64,{img_b64}"},
                timeout=30,
            )
            resp.raise_for_status()
            preds = resp.json().get("predictions", [])
            return preds[0] if preds else None
        except Exception as e:
            logger.warning(f"Roboflow API call failed: {e}")
            return None

    def _parse_roboflow_keypoints(self, prediction: Dict) -> Optional[Dict[int, Tuple[float, float, float]]]:
        raw_kps = prediction.get("keypoints")
        if not raw_kps:
            return None
        keypoints = {}
        for kp in raw_kps:
            idx = COCO_KEYPOINTS.get(kp.get("class_name", ""))
            if idx is not None:
                keypoints[idx] = (kp["x"], kp["y"], kp.get("confidence", 1.0))
        return keypoints if len(keypoints) >= 3 else None

    def _infer_keypoints(self, frame: np.ndarray) -> Optional[Dict[int, Tuple[float, float, float]]]:
        self._load_onnx()
        outputs = self._onnx_infer(frame)
        if outputs is not None:
            kps = self._parse_onnx_keypoints(outputs)
            if kps is not None:
                return kps
        pred = self._roboflow_infer(frame)
        if pred is not None:
            return self._parse_roboflow_keypoints(pred)
        return None

    def analyze_frames(self, frames: List[np.ndarray], fps: float = 30.0) -> Dict[str, Any]:
        if not frames:
            return self._empty_features()

        if not os.path.exists(MODEL_PATH) and not self.api_key:
            logger.warning("No ONNX model or Roboflow API key — returning default body features")
            return self._empty_features()

        try:
            self._load_onnx()
        except Exception:
            pass

        logger.info(f"Analyzing {len(frames)} frames for body language...")
        try:
            landmarks_sequence = []
            face_visible_count = 0
            total_frames_analyzed = 0

            for frame in frames:
                kps = self._infer_keypoints(frame)
                if kps is None:
                    continue
                total_frames_analyzed += 1
                landmarks_sequence.append(kps)
                if self._is_face_visible(kps):
                    face_visible_count += 1

            if not landmarks_sequence:
                logger.warning("No pose detected in any frame — using defaults")
                return self._empty_features()

            logger.info(f"Pose detected in {len(landmarks_sequence)}/{total_frames_analyzed} frames")

            return {
                "posture_stability": self._compute_posture_score(landmarks_sequence),
                "stability_score": self._compute_stability_score(landmarks_sequence),
                "expressiveness_score": self._compute_expressiveness_score(landmarks_sequence),
                "eye_contact_ratio": face_visible_count / max(total_frames_analyzed, 1),
                "gesture_frequency": self._compute_gesture_frequency(landmarks_sequence, fps),
                "movement_frequency": self._compute_movement_frequency(landmarks_sequence, fps),
                "head_nod_count": 0,
                "shoulder_movement_score": 0.5,
            }

        except Exception as e:
            logger.error(f"Body analysis failed: {e}")
            return self._empty_features()

    def _is_face_visible(self, kps: Dict[int, Tuple]) -> bool:
        required = [0, 1, 2]
        for idx in required:
            if idx not in kps or kps[idx][2] < 0.3:
                return False
        nose_x = kps[0][0]
        return 0.15 <= nose_x <= 0.85

    def _compute_posture_score(self, seq: List[Dict[int, Tuple]]) -> float:
        scores = []
        for kps in seq:
            try:
                nose = kps.get(0)
                lsh = kps.get(5)
                rsh = kps.get(6)
                lhip = kps.get(11)
                rhip = kps.get(12)
                if not all([nose, lsh, rsh, lhip, rhip]):
                    continue
                shoulder_diff = abs(lsh[1] - rsh[1])
                shoulder_score = max(0, 1.0 - shoulder_diff * 5.0)
                shoulder_cx = (lsh[0] + rsh[0]) / 2
                head_align = abs(nose[0] - shoulder_cx)
                alignment_score = max(0, 1.0 - head_align * 3.0)
                hip_cx = (lhip[0] + rhip[0]) / 2
                vert_align = abs(nose[0] - hip_cx)
                vertical_score = max(0, 1.0 - vert_align * 3.0)
                scores.append((shoulder_score + alignment_score + vertical_score) / 3)
            except Exception:
                continue
        return round(float(np.mean(scores)) if scores else 0.5, 2)

    def _compute_stability_score(self, seq: List[Dict[int, Tuple]]) -> float:
        if len(seq) < 2:
            return 75.0
        variances = []
        for pt_idx in [0, 5, 6, 11, 12]:
            positions = []
            for kps in seq:
                if pt_idx in kps:
                    positions.append(kps[pt_idx][:2])
            if len(positions) >= 2:
                variances.append(float(np.mean(np.var(np.array(positions), axis=0))))
        if not variances:
            return 50.0
        stability = max(0, 100.0 - float(np.mean(variances)) * 2000.0)
        return round(min(100.0, stability), 1)

    def _compute_expressiveness_score(self, seq: List[Dict[int, Tuple]]) -> float:
        if len(seq) < 3:
            return 50.0
        scores = []
        for pt_idx in [9, 10]:
            positions = []
            for kps in seq:
                if pt_idx in kps:
                    positions.append(kps[pt_idx][:2])
            if len(positions) >= 3:
                arr = np.array(positions)
                diffs = np.diff(arr, axis=0)
                total_movement = float(np.sum(np.linalg.norm(diffs, axis=1)))
                scores.append(min(100.0, total_movement * 100.0))
        return round(float(np.mean(scores)) if scores else 50.0, 1)

    def _compute_gesture_frequency(self, seq: List[Dict[int, Tuple]], fps: float) -> float:
        if len(seq) < 5:
            return 0.0
        wrists = []
        for kps in seq:
            lw = kps.get(9)
            rw = kps.get(10)
            if lw and rw:
                wrists.append(((lw[0] + rw[0]) / 2, (lw[1] + rw[1]) / 2))
        if len(wrists) < 5:
            return 0.0
        gestures = 0
        for i in range(2, len(wrists)):
            v1 = np.array(wrists[i]) - np.array(wrists[i - 1])
            v2 = np.array(wrists[i - 1]) - np.array(wrists[i - 2])
            n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
            if n1 > 0.005 and n2 > 0.005:
                angle = np.arccos(np.clip(np.dot(v1, v2) / (n1 * n2), -1, 1))
                if angle > np.pi / 2:
                    gestures += 1
        duration_min = len(seq) / fps / 60.0
        return round(gestures / max(duration_min, 0.1), 1)

    def _compute_movement_frequency(self, seq: List[Dict[int, Tuple]], fps: float) -> float:
        if len(seq) < 5:
            return 0.0
        coms = []
        for kps in seq:
            pts = [kps[i] for i in [0, 5, 6, 11, 12] if i in kps]
            if pts:
                coms.append(np.mean([p[:2] for p in pts], axis=0))
        if len(coms) < 5:
            return 0.0
        movements = 0
        for i in range(1, len(coms)):
            if np.linalg.norm(np.array(coms[i]) - np.array(coms[i - 1])) > 0.01:
                movements += 1
        duration_min = len(seq) / fps / 60.0
        return round(movements / max(duration_min, 0.1), 1)

    def _empty_features(self) -> Dict[str, Any]:
        return {
            "posture_stability": 0.5,
            "stability_score": 50.0,
            "expressiveness_score": 50.0,
            "eye_contact_ratio": 0.5,
            "gesture_frequency": 0.0,
            "movement_frequency": 0.0,
            "head_nod_count": 0,
            "shoulder_movement_score": 0.5,
        }

    def close(self):
        self._ort_session = None
        if self._session:
            self._session.close()
            self._session = None
