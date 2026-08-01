from ultralytics import YOLO
import torch


class PersonDetector:

    def __init__(self):

        self.device = 0 if torch.cuda.is_available() else "cpu"

        print(f"[INFO] Using device: {'CUDA' if self.device == 0 else 'CPU'}")

        self.model = YOLO("models/yolo11n.pt")
        self.model.to(self.device)

    def detect(self, frame):

        results = self.model(
            frame,
            classes=[0],          # Person only
            conf=0.5,
            verbose=False
        )

        return results