import cv2
import numpy as np
import logging
import os
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class BodyAnalyzer:
    """Analyzes body language from video frames using OpenCV DNN for pose estimation."""
    
    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        model_complexity: int = 1,
    ):
        """
        Args:
            min_detection_confidence: Minimum confidence for pose detection
            min_tracking_confidence: Minimum confidence for pose tracking
            model_complexity: 0=lite, 1=full, 2=heavy (not used with OpenCV)
        """
        # Use OpenCV's DNN module with OpenPose model
        # Download OpenPose model if needed
        self.proto_path = self._get_model_path("pose_deploy_linevec.prototxt")
        self.model_path = self._get_model_path("pose_iter_440000.caffemodel")
        
        if not os.path.exists(self.proto_path) or not os.path.exists(self.model_path):
            logger.warning("OpenPose model files not found. Using fallback analysis.")
            self.net = None
        else:
            self.net = cv2.dnn.readNetFromCaffe(self.proto_path, self.model_path)
            self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        
        self.pose_pairs = [
            [1, 2], [1, 5], [2, 3], [3, 4], [5, 6], [6, 7],
            [1, 8], [8, 9], [9, 10], [1, 11], [11, 12], [12, 13],
            [1, 0], [0, 14], [14, 16], [0, 15], [15, 17],
            [2, 17], [5, 18]
        ]
        
        self.pose_points = {
            "nose": 0, "neck": 1, "rshoulder": 2, "relbow": 3, "rwrist": 4,
            "lshoulder": 5, "lelbow": 6, "lwrist": 7, "rhip": 8, "rknee": 9,
            "rankle": 10, "lhip": 11, "lknee": 12, "lankle": 13,
            "reye": 14, "leye": 15, "rear": 17, "lear": 18
        }

    def _get_model_path(self, filename: str) -> str:
        """Get model file path, downloading if necessary."""
        import os
        model_dir = os.path.join(os.path.dirname(__file__), "..", "..", "models")
        os.makedirs(model_dir, exist_ok=True)
        file_path = os.path.join(model_dir, filename)
        
        if not os.path.exists(file_path):
            logger.info(f"Model file {filename} not found. Please download manually.")
        
        return os.path.abspath(file_path)

    def analyze_frames(self, frames: List[np.ndarray], fps: float = 30.0) -> Dict[str, Any]:
        """
        Analyze a list of frames for body language features.
        Returns dict with posture, stability, expressiveness, eye contact metrics.
        """
        if not frames:
            return self._empty_features()

        if self.net is None:
            logger.warning("OpenPose model not available. Using fallback analysis.")
            return self._fallback_analysis(frames, fps)

        try:
            landmarks_sequence = []
            face_visible_sequence = []

            for frame in frames:
                # Run pose detection
                keypoints = self._detect_pose(frame)
                
                if keypoints is not None:
                    landmarks = self._extract_landmarks(keypoints)
                    landmarks_sequence.append(landmarks)
                    
                    # Check if face is visible (for eye contact estimation)
                    face_visible = self._is_face_visible(keypoints)
                    face_visible_sequence.append(face_visible)
                else:
                    face_visible_sequence.append(False)

            if not landmarks_sequence:
                logger.warning("No pose landmarks detected in any frame")
                return self._empty_features()

            # Compute metrics from sequence
            features = {
                "posture_stability": self._compute_posture_score(landmarks_sequence),
                "stability_score": self._compute_stability_score(landmarks_sequence),
                "expressiveness_score": self._compute_expressiveness_score(landmarks_sequence),
                "eye_contact_ratio": sum(face_visible_sequence) / len(face_visible_sequence) if face_visible_sequence else 0,
                "gesture_frequency": self._compute_gesture_frequency(landmarks_sequence),
                "movement_frequency": self._compute_movement_frequency(landmarks_sequence),
            }

            return features

        except Exception as e:
            logger.error(f"Error analyzing body language: {e}")
            return self._empty_features()

    def _detect_pose(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Run pose detection on a single frame."""
        if self.net is None:
            return None
        
        height, width = frame.shape[:2]
        inp_blob = cv2.dnn.blobFromImage(frame, 1.0 / 255, (368, 368), (0, 0, 0), swapRB=True, crop=False)
        self.net.setInput(inp_blob)
        output = self.net.forward()
        
        # Output shape: [1, 19, H, W] for 18 keypoints + background
        return output

    def _extract_keypoints(self, output: np.ndarray, frame_shape: Tuple[int, int]) -> Optional[Dict[int, Tuple[float, float, float]]]:
        """Extract keypoint coordinates from network output."""
        height, width = frame_shape[:2]
        keypoints = {}
        
        for i in range(18):  # 18 keypoints in OpenPose
            prob_map = output[0, i, :, :]
            min_val, prob, _, point = cv2.minMaxLoc(prob_map)
            
            if prob > 0.1:  # Confidence threshold
                x = (point[0] * frame_shape[1]) / output.shape[3]
                y = (point[1] * frame_shape[0]) / output.shape[2]
                keypoints[i] = (x / frame_shape[1], y / frame_shape[0], prob)
        
        return keypoints if keypoints else None

    def _detect_pose(self, frame: np.ndarray) -> Optional[Dict[int, Tuple[float, float, float]]]:
        """Run pose detection and extract keypoints."""
        if self.net is None:
            return None
        
        output = self._detect_pose(frame)
        if output is None:
            return None
        
        return self._extract_keypoints(output, frame.shape)

    def _is_face_visible(self, keypoints: Dict[int, Tuple[float, float, float]]) -> bool:
        """Check if face is visible (nose and eyes detected)."""
        # Nose=0, LEye=14, REye=15, LEar=17, REar=18
        required = [0, 14, 15]
        for idx in required:
            if idx not in keypoints or keypoints[idx][2] < 0.3:
                return False
        
        # Check if face is roughly centered
        nose = keypoints[0]
        left_eye = keypoints[14]
        right_eye = keypoints[15]
        
        face_center_x = (nose[0] + left_eye[0] + right_eye[0]) / 3
        return 0.2 <= face_center_x <= 0.8

    def _compute_posture_score(self, landmarks_sequence: List[Dict]) -> float:
        """Compute posture score based on head-shoulder-hip alignment."""
        scores = []
        for landmarks in landmarks_sequence:
            try:
                nose = landmarks.get(0)
                left_shoulder = landmarks.get(2)
                right_shoulder = landmarks.get(5)
                left_hip = landmarks.get(8)
                right_hip = landmarks.get(11)
                
                if not all([nose, left_shoulder, right_shoulder, left_hip, right_hip]):
                    continue
                
                # Shoulder level
                shoulder_diff = abs(left_shoulder[1] - right_shoulder[1])
                shoulder_score = max(0, 100 - shoulder_diff * 500)
                
                # Head centered over shoulders
                shoulder_center_x = (left_shoulder[0] + right_shoulder[0]) / 2
                head_alignment = abs(nose[0] - shoulder_center_x)
                alignment_score = max(0, 100 - head_alignment * 300)
                
                # Vertical alignment
                hip_center_x = (left_hip[0] + right_hip[0]) / 2
                vertical_alignment = abs(nose[0] - hip_center_x)
                vertical_score = max(0, 100 - vertical_alignment * 300)
                
                frame_score = (shoulder_score + alignment_score + vertical_score) / 3
                scores.append(frame_score)
            except Exception:
                continue
        
        return round(np.mean(scores), 1) if scores else 50.0

    def _compute_stability_score(self, landmarks_sequence: List[Dict]) -> float:
        if len(landmarks_sequence) < 2:
            return 75.0
        
        key_points = [0, 2, 5, 8, 11]  # nose, shoulders, hips
        variances = []
        
        for pt_idx in [0, 2, 5, 8, 11]:
            positions = []
            for landmarks in landmarks_sequence:
                if pt_idx in landmarks:
                    positions.append(landmarks[pt_idx])
            
            if len(positions) >= 2:
                pos_array = np.array(positions)
                var = np.mean(np.var(pos_array, axis=0))
                variances.append(var)
        
        if not variances:
            return 50.0
        
        avg_variance = np.mean(variances)
        stability = max(0, 100 - avg_variance * 2000)
        return round(min(100, stability), 1)

    def _compute_expressiveness_score(self, landmarks_sequence: List[Dict]) -> float:
        if len(landmarks_sequence) < 3:
            return 50.0
        
        gesture_points = [4, 7, 9, 12]  # wrists and hands
        gesture_scores = []
        
        for pt_idx in [4, 7, 9, 12]:
            positions = []
            for landmarks in landmarks_sequence:
                if pt_idx in landmarks:
                    positions.append(landmarks[pt_idx][:2])
            
            if len(positions) >= 3:
                pos_array = np.array(positions)
                diffs = np.diff(pos_array, axis=0)
                distances = np.linalg.norm(diffs, axis=1)
                total_movement = np.sum(distances)
                score = min(100, total_movement * 1000)
                gesture_scores.append(score)
        
        return round(np.mean(gesture_scores), 1) if gesture_scores else 50.0

    def _compute_gesture_frequency(self, landmarks_sequence: List[Dict], fps: float) -> float:
        if len(landmarks_sequence) < 10:
            return 0.0
        
        wrist_positions = []
        for landmarks in landmarks_sequence:
            left = landmarks.get(4)
            right = landmarks.get(7)
            if left and right:
                wrist_positions.append(((left[0] + right[0]) / 2, (left[1] + right[1]) / 2))
        
        if len(wrist_positions) < 5:
            return 0.0
        
        gestures = 0
        for i in range(2, len(wrist_positions)):
            v1 = np.array(wrist_positions[i]) - np.array(wrist_positions[i-1])
            v2 = np.array(wrist_positions[i-1]) - np.array(wrist_positions[i-2])
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            if norm1 > 0.01 and norm2 > 0.01:
                dot = np.dot(v1, v2)
                angle = np.arccos(np.clip(dot / (norm1 * norm2), -1, 1))
                if angle > np.pi / 2:
                    gestures += 1
        
        duration_min = len(landmarks_sequence) / 30.0 / 60
        return round(gestures / max(duration_min, 0.1), 1)

    def _compute_movement_frequency(self, landmarks_sequence: List[Dict], fps: float) -> float:
        if len(landmarks_sequence) < 10:
            return 0.0
        
        com_positions = []
        for landmarks in landmarks_sequence:
            key_pts = [0, 2, 5, 8, 11]
            pts = [landmarks[k] for k in [0, 2, 5, 8, 11] if k in landmarks]
            if pts:
                com = np.mean([p[:2] for p in pts], axis=0)
                com_positions.append(com)
        
        if len(com_positions) < 5:
            return 0.0
        
        movements = 0
        for i in range(1, len(com_positions)):
            dist = np.linalg.norm(np.array(com_positions[i]) - np.array(com_positions[i-1]))
            if dist > 0.02:
                movements += 1
        
        duration_min = len(landmarks_sequence) / 30.0 / 60
        return round(movements / max(duration_min, 0.1), 1)

    def _empty_features(self) -> Dict[str, Any]:
        return {
            "posture_stability": 0.5,
            "eye_contact_ratio": 0.5,
            "gesture_frequency": 0.0,
            "movement_frequency": 0.0,
            "head_nod_count": 0,
            "shoulder_movement_score": 0.5,
        }

    def _fallback_analysis(self, frames: List[np.ndarray], fps: float) -> Dict[str, Any]:
        """Fallback when OpenPose model is not available."""
        logger.info("Using fallback body analysis (no OpenPose model)")
        return self._empty_features()

    def close(self):
        """Clean up resources."""
        pass