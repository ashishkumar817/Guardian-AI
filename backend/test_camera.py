import cv2

from app.ai.camera import Camera
from app.ai.detector import PersonDetector
from app.ai.pose import PoseEstimator

camera = Camera()
detector = PersonDetector()
pose = PoseEstimator()

while True:
    ret, frame = camera.read()

    if not ret:
        break

    # YOLO Detection
    results = detector.detect(frame)
    annotated = results[0].plot()

    # Pose Estimation
    pose_results = pose.process(annotated)
    annotated = pose.draw(annotated, pose_results)

    cv2.imshow("GuardianAI", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()