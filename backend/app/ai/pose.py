import cv2
import mediapipe as mp


class PoseEstimator:

    def __init__(self):

        self.mp_pose = mp.solutions.pose
        self.mp_draw = mp.solutions.drawing_utils

        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,
            smooth_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def process(self, image):

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        return self.pose.process(rgb)

    def draw(self, image, results):

        if not results.pose_landmarks:
            return image

        self.mp_draw.draw_landmarks(
            image,
            results.pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
        )

        return image