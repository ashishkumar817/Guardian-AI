import cv2
import mediapipe as mp


class PoseEstimator:

    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_draw = mp.solutions.drawing_utils

        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def process(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self.pose.process(rgb)

    def draw(self, frame, results):

        if results.pose_landmarks:

            self.mp_draw.draw_landmarks(
                frame,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
            )

            landmarks = results.pose_landmarks.landmark

            h, w, _ = frame.shape

            # Nose
            nose = landmarks[self.mp_pose.PoseLandmark.NOSE]
            cv2.circle(
                frame,
                (int(nose.x * w), int(nose.y * h)),
                6,
                (0, 0, 255),
                -1,
            )

            # Left Hip
            hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]
            cv2.circle(
                frame,
                (int(hip.x * w), int(hip.y * h)),
                6,
                (255, 0, 0),
                -1,
            )

        return frame