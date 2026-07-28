from ultralytics import YOLO


class PersonDetector:

    def __init__(self):
        self.model = YOLO("models/yolo11s.pt")

    def detect(self, frame):
        return self.model(frame)