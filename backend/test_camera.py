import cv2
import time
import os
from datetime import datetime
from app.ai.camera import Camera
from app.ai.detector import PersonDetector
from app.ai.pose import PoseEstimator
from app.ai.fall_detector import FallDetector

from app.ai.api_client import GuardianAPI

camera = Camera()
detector = PersonDetector()
pose = PoseEstimator()
fall_detector = FallDetector()
api = GuardianAPI()

api.login(
    "ashish@gmail.com",
    "NewPassword@123"
)
frame_count = 0
last_results = None

prev_time = time.time()
os.makedirs("captures", exist_ok=True)

last_capture_time = 0
CAPTURE_INTERVAL = 10  # seconds
while True:

    ret, frame = camera.read()

    if not ret:
        break

    frame = cv2.resize(frame, (640, 480))

    frame_count += 1

    # Run YOLO every 5 frames on resized 320x240 frame for max FPS & 0 lag
    if frame_count % 5 == 0 or last_results is None:
        small_frame = cv2.resize(frame, (320, 240))
        last_results = detector.detect(small_frame)

    results = last_results

    annotated = frame.copy()
    confidence = 0.9

    if results is not None and len(results[0].boxes) > 0:
        box = results[0].boxes[0]
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        # Scale coordinates from 320x240 to 640x480
        x1, y1, x2, y2 = x1 * 2, y1 * 2, x2 * 2, y2 * 2

        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(frame.shape[1], x2)
        y2 = min(frame.shape[0], y2)

        # Draw YOLO box
        cv2.rectangle(
            annotated,
            (x1, y1),
            (x2, y2),
            (255, 0, 0),
            2,
        )

    # Run MediaPipe on full frame for zero-latency posture tracking
    pose_results = pose.process(frame)
    annotated = pose.draw(annotated, pose_results)

    # Fall Detection
    if pose_results is not None:
        fall_detected, info = fall_detector.detect(pose_results, image_shape=frame.shape[:2])
    else:
        fall_detected = False
        info = None

    if info:

        angle = info.get("body_angle")
        ydiff = info.get("vertical_distance")
        lying = info.get("lying")
        duration = info.get("duration")

        if angle is not None:
            cv2.putText(
                annotated,
                f"Angle: {angle:.1f} deg",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

        if ydiff is not None:
            cv2.putText(
                annotated,
                f"YDiff: {ydiff:.2f}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

        if lying is not None:
            color = (0, 0, 255) if lying else (0, 255, 0)
            cv2.putText(
                annotated,
                f"Lying: {lying}",
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2,
            )

        if duration is not None:
            cv2.putText(
                annotated,
                f"Duration: {duration:.1f}s",
                (10, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )

    if fall_detected:

        cv2.putText(
            annotated,
            "FALL DETECTED!",
            (140, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 0, 255),
            3,
        )

        current_time = time.time()

        if current_time - last_capture_time > CAPTURE_INTERVAL:

            filename = datetime.now().strftime("%Y%m%d_%H%M%S.jpg")

            image_path = os.path.join("captures", filename)

            cv2.imwrite(image_path, annotated)

            print(f"[INFO] Snapshot saved: {image_path}")

            try:
                api.create_incident(
                    confidence=confidence,
                    image_path=image_path
                )
            except Exception as e:
                print(f"[WARNING] API incident creation failed: {e}")

            last_capture_time = current_time

    # FPS Counter - top right corner
    current_time = time.time()
    fps = 1 / max(1e-5, current_time - prev_time)
    prev_time = current_time

    cv2.putText(
        annotated,
        f"FPS: {fps:.1f}",
        (500, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2,
    )

    cv2.imshow("GuardianAI", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()