from ultralytics import YOLO

# This will automatically download the weights if they aren't present
model = YOLO("yolo11s.pt")

print("Model downloaded successfully!")