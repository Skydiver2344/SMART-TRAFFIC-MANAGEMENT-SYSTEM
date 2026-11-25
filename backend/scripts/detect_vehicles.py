from ultralytics import YOLO
from pathlib import Path

# Project directory
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Load trained model
MODEL_PATH = (
    PROJECT_DIR / "runs" /
    "visdrone_yolov8n-2" / "weights" / "best.pt"
)

model = YOLO(str(MODEL_PATH))

# Vehicle classes
VEHICLE_CLASSES = {
    0: "Car",
    1: "Van",
    2: "Truck",
    3: "Bus",
    4: "Motorcycle"
}

def detect_vehicles(frame):

    results = model(frame, conf=0.25, verbose=False)

    detections = []

    for result in results:

        for box in result.boxes:

            # Get class ID
            class_id = int(box.cls[0])

            # Get confidence
            confidence = float(box.conf[0])

            # Get bounding box coordinates
            x1, y1, x2, y2 = map(
                int, box.xyxy[0]
            )
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            vehicle = {
                "class": VEHICLE_CLASSES[class_id],
                "confidence": confidence,
                "bbox": (x1, y1, x2, y2),
                "center": (center_x, center_y)
            }

            detections.append(vehicle)

    return detections

if __name__ == "__main__":

    import cv2

    PROJECT_DIR = Path(__file__).resolve().parent.parent
    VIDEO_PATH = PROJECT_DIR / "demo_video.mp4"
    cap = cv2.VideoCapture(str(VIDEO_PATH))

    cap.set(cv2.CAP_PROP_POS_MSEC, 10000)
    ret, frame = cap.read()

    if ret:

        vehicles = detect_vehicles(frame)

        for vehicle in vehicles:
            x1, y1, x2, y2 = vehicle["bbox"]
            center_x, center_y = vehicle["center"]

            # Draw bounding box
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            # Draw centre point
            cv2.circle(
                frame,
                (center_x, center_y),
                5,
                (0, 0, 255),
                -1
            )

            # Display vehicle class
            cv2.putText(
                frame,
                vehicle["class"],
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )

        cv2.imwrite(
        "runs/vehicle_centres.jpg",
        frame
        )

        print("Saved vehicle_centres.jpg")

    cap.release()
        