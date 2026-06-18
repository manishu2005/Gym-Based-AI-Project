import os
import cv2
import numpy as np
import mediapipe as mp
import av
import threading
from streamlit_webrtc import VideoProcessorBase
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from detectors.squats import SquatsDetector
from detectors.pushup import PushUpDetector
from detectors.biceps_curls import BicepCurlDetector
from detectors.shoulder_press import ShoulderPressDetector
from detectors.lunges import LungesDetector
from services.config.workout_config import POSE_CONNECTIONS
class VideoProcessorClass(VideoProcessorBase):
    def __init__(self):
        self._lock = threading.Lock()
        self._latest_metrics = None
        self._excercise_type = "Squats"

        model_path = os.path.join(os.getcwd(), "ml_models","pose_landmarker_full.task")
        print("Current Working Dir:", os.getcwd())
        print("Model Path:", model_path)
        print("Model Exists:", os.path.exists(model_path))

        base_option = python.BaseOptions(model_asset_path=model_path)
        
        options = vision.PoseLandmarkerOptions(
            base_options = base_option,
            running_mode = vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.7,
            min_pose_presence_confidence=0.7,
            min_tracking_confidence=0.7,
            output_segmentation_masks=False
        )

        # self._landmarker = vision.PoseLandmarker.create_from_options(options)
        self._landmarker = None
        self._detectors = {
            "Squats":SquatsDetector(),
            "Push-ups":PushUpDetector(),
            "Biceps Curls(Dumbbell)":BicepCurlDetector(),
            "Shoulder Press":ShoulderPressDetector(),
            "Lunges":LungesDetector(),
        }

        self._frame_timestamps_ms = 0

    def set_latest_metrics(self, metrics):
        with self._lock:
            self._latest_metrics=metrics.copy()

    def get_latest_metrics(self):
        with self._lock:
            return None if self._latest_metrics is None else self._latest_metrics.copy()
        
    def set_excercise(self, excercise_type):
        with self._lock:
            self._excercise_type = excercise_type
    
    def get_excercise(self):
        with self._lock:
            return self._excercise_type

    def _draw_skeleton(self, img, landmarks):
        h, w= img.shape[:2]

        for start_idx, end_idx in POSE_CONNECTIONS:
            p1 = landmarks[start_idx]
            p2 = landmarks[end_idx]

            if p1.visibility > 0.7 and p2.visibility > 0.7:
                cv2.line(
                    img,
                    (int(p1.x * w), int(p1.y * h)),
                    (int(p2.x * w), int(p2.y * h)),
                    (0,255,0),
                    8
                )
        for lm in landmarks:
            if lm.visibility > 0.7:
                cv2.circle(
                    img,
                    (int(lm.x * w), int(lm.y * h)),
                    8,
                    (255,0,0),
                    -1
                )
    def _draw_no_pose_warnings(self, img):
        cv2.putText(
            img,
            "No Pose Detected",
            (30,50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0,255,0),
            2,
            cv2.LINE_AA,
        )

        cv2.putText(
                img,
                "Please Face The Camera",
                (30,100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,0),
                2,
                cv2.LINE_AA,
            )

    def _draw_overlays(self, img, metrics, ex_type):
        if ex_type == "Squats":
            self._draw_squats_overlays(img, metrics)
        elif ex_type == "Push-ups":
            self._draw_pushup_overlays(img, metrics)
        elif ex_type == "Biceps Curls(Dumbbell)":
            self._draw_curl_overlays(img, metrics)
        elif ex_type == "Shoulder Press":
            self._draw_press_overlays(img, metrics)
        elif ex_type == "Lunges":
            self._draw_lunges_overlays(img, metrics)
        
    def _draw_squats_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
                img,
                f"Depth: {metrics['depth_status']}",
                (30,100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,0),
                2,
            )
    
    def _draw_pushup_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
                img,
                f"Body: {metrics['body_alignment']} | HIP:{metrics['hip_status']}",
                (30,100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,0),
                2,
            )
    
    def _draw_curl_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
                img,
                f"Swing: {metrics['swing_status']}",
                (30,100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,0),
                2,
            )
        
    def _draw_press_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
                img,
                f"Exit: {metrics['extension_status']} | Back:{metrics['back_arch_status']}",
                (30,100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,0),
                2,
            )
        
    def _draw_lunges_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
                img,
                f"Balance:{metrics['balance_status']}",
                (30,100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,0),
                2,
            )
        
    def recv(self, frame):
        image = np.asarray(
            cv2.flip(frame.to_ndarray(format="bgr24"),1),
            dtype=np.uint8
        )
        
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(
            image_format = mp.ImageFormat.SRGB,
            data = rgb_image
        )

        self._frame_timestamps_ms += 30
        result = self._landmarker.detect_for_video(mp_image, self._frame_timestamps_ms)

        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]

            self._draw_skeleton(image, landmarks)

            ex_type = self.get_excercise()
            detector = self._detectors.get(ex_type)

            if detector:
                metrics = detector.process(landmarks)
                metrics["pose_detected"]=True

                self._draw_overlays(image, metrics, ex_type)

                self.set_latest_metrics(metrics)
        else:
            self._draw_no_pose_warnings(image)

            with self._lock:
                if self._latest_metrics is not None:
                    self._latest_metrics["pose_detected"]=False
                else:
                    self._latest_metrics={"pose_detected":False}

        return av.VideoFrame.from_ndarray(image, format='bgr24')
