import math
import time
import mediapipe as mp


class FallDetector:

    def __init__(self):
        self.mp_pose = mp.solutions.pose

        self.fall_start_time = None
        self.fall_confirmed = False

        self.prev_hip_y = None
        self.prev_time = None
        self.last_high_speed_time = None
        self.last_seen_time = None
        self.lying_start_time = None
        self.not_lying_start_time = None

        self.ANGLE_THRESHOLD = 55.0  # degrees from horizontal (standing ~90, lying ~0-40)
        self.Y_DIFF_THRESHOLD = 0.25  # vertical distance threshold
        self.FALL_TIME = 0.8         # seconds lying to confirm fall
        self.SPEED_THRESHOLD = 0.20   # downward speed threshold
        self.GRACE_PERIOD = 0.5      # grace period before clearing fall state when upright/missing

    def _angle(self, p1, p2, image_shape=None):
        if image_shape and len(image_shape) >= 2:
            h, w = image_shape[0], image_shape[1]
            dx = abs(p2.x - p1.x) * w
            dy = abs(p2.y - p1.y) * h
        else:
            dx = abs(p2.x - p1.x)
            dy = abs(p2.y - p1.y)

        if dx == 0 and dy == 0:
            return 90.0

        # atan2(dy, dx) gives acute angle with horizontal plane (0° = horizontal, 90° = vertical)
        return math.degrees(math.atan2(dy, dx))

    def detect(self, pose_results, image_shape=None):
        current_time = time.time()

        if not pose_results or not pose_results.pose_landmarks:
            if self.last_seen_time and (current_time - self.last_seen_time < self.GRACE_PERIOD):
                duration = round(current_time - (self.lying_start_time or current_time), 2)
                return self.fall_confirmed, {
                    "body_angle": 0.0,
                    "vertical_distance": 0.0,
                    "hip_speed": 0.0,
                    "lying": True,
                    "duration": duration,
                }
            self.lying_start_time = None
            self.fall_confirmed = False
            self.prev_hip_y = None
            self.prev_time = None
            return False, {}

        self.last_seen_time = current_time
        landmarks = pose_results.pose_landmarks.landmark

        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP]

        shoulder_x = (left_shoulder.x + right_shoulder.x) / 2
        shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        hip_x = (left_hip.x + right_hip.x) / 2
        hip_y = (left_hip.y + right_hip.y) / 2

        hip_speed = 0.0
        if self.prev_hip_y is not None and self.prev_time is not None:
            dt = current_time - self.prev_time
            if dt > 0:
                hip_speed = (hip_y - self.prev_hip_y) / dt

        self.prev_hip_y = hip_y
        self.prev_time = current_time

        if hip_speed > self.SPEED_THRESHOLD:
            self.last_high_speed_time = current_time

        class Point:
            pass

        shoulder = Point()
        shoulder.x, shoulder.y = shoulder_x, shoulder_y
        hip = Point()
        hip.x, hip.y = hip_x, hip_y

        body_angle = self._angle(shoulder, hip, image_shape=image_shape)
        vertical_distance = abs(shoulder_y - hip_y)

        # Check if crop bounding box is horizontal (width >= height)
        is_wide_crop = False
        if image_shape and len(image_shape) >= 2:
            h, w = image_shape[0], image_shape[1]
            if w > 0 and h > 0 and (w / h) >= 1.0:
                is_wide_crop = True

        lying = (
            body_angle < self.ANGLE_THRESHOLD
            and (vertical_distance < self.Y_DIFF_THRESHOLD or is_wide_crop)
        )

        recent_speed_spike = (
            self.last_high_speed_time is not None
            and (current_time - self.last_high_speed_time) <= 3.0
        )

        duration = 0.0

        if lying:
            self.not_lying_start_time = None
            if self.lying_start_time is None:
                self.lying_start_time = current_time

            duration = current_time - self.lying_start_time

            if recent_speed_spike or duration >= self.FALL_TIME:
                self.fall_confirmed = True
        else:
            if self.not_lying_start_time is None:
                self.not_lying_start_time = current_time

            if current_time - self.not_lying_start_time > self.GRACE_PERIOD:
                self.lying_start_time = None
                self.fall_confirmed = False
                duration = 0.0
            elif self.lying_start_time is not None:
                duration = current_time - self.lying_start_time

        print(
            f"Angle={body_angle:.1f}, "
            f"YDiff={vertical_distance:.2f}, "
            f"HipSpeed={hip_speed:.2f}, "
            f"Lying={lying}, "
            f"Duration={duration:.1f}"
        )

        return self.fall_confirmed, {
            "body_angle": round(body_angle, 2),
            "vertical_distance": round(vertical_distance, 2),
            "hip_speed": round(hip_speed, 2),
            "lying": lying,
            "duration": round(duration, 2),
        }