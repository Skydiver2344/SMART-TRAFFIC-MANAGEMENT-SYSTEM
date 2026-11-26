from ultralytics import YOLO
from pathlib import Path

# ==================================================
# 1. MODEL CONFIGURATION
# ==================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    PROJECT_DIR
    / "runs"
    / "visdrone_yolov8n-2"
    / "weights"
    / "best.pt"
)

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Vehicle detection model not found: {MODEL_PATH}"
    )

model = YOLO(str(MODEL_PATH))


# ==================================================
# 2. VEHICLE CLASSES
# ==================================================

VEHICLE_CLASSES = {
    0: "Car",
    1: "Van",
    2: "Truck",
    3: "Bus",
    4: "Motorcycle"
}


# ==================================================
# 3. RESET TRACKER BETWEEN SESSIONS
# ==================================================

def reset_vehicle_tracker():

    predictor = getattr(model, "predictor", None)

    if predictor is None:
        return

    trackers = getattr(predictor, "trackers", None)

    if trackers is None:
        return

    for tracker in trackers:
        tracker.reset()


# ==================================================
# 4. VEHICLE DETECTION AND TRACKING
# ==================================================

def detect_vehicles(frame):

    results = model.track(
        source=frame,
        conf=0.25,
        persist=True,
        tracker="bytetrack.yaml",
        verbose=False
    )

    detections = []

    for result in results:

        if result.boxes is None:
            continue

        boxes = result.boxes

        track_ids = boxes.id

        for index, box in enumerate(boxes):

            class_id = int(box.cls[0])

            if class_id not in VEHICLE_CLASSES:
                continue

            confidence = float(box.conf[0])

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Tracking ID may be unavailable
            # during initial tracker association.

            track_id = None

            if track_ids is not None:
                track_id = int(track_ids[index])

            vehicle = {
                "class": VEHICLE_CLASSES[class_id],
                "confidence": confidence,
                "bbox": (x1, y1, x2, y2),
                "center": (center_x, center_y),
                "track_id": track_id
            }

            detections.append(vehicle)

    return detections


# ==================================================
# 5. STANDALONE TEST
# ==================================================

if __name__ == "__main__":

    import cv2

    VIDEO_PATH = PROJECT_DIR / "demo_video.mp4"

    cap = cv2.VideoCapture(str(VIDEO_PATH))

    cap.set(cv2.CAP_PROP_POS_MSEC, 10000)

    ret, frame = cap.read()

    if ret:

        vehicles = detect_vehicles(frame)

        for vehicle in vehicles:

            x1, y1, x2, y2 = vehicle["bbox"]

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            label = (
                f'{vehicle["class"]} '
                f'ID:{vehicle["track_id"]}'
            )

            cv2.putText(
                frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )

        cv2.imwrite(
            str(PROJECT_DIR / "vehicle_tracking_test.jpg"),
            frame
        )

        print("Saved vehicle_tracking_test.jpg")

        print("\nDetected vehicles:")

        for vehicle in vehicles:
            print(
                vehicle["class"],
                "| ID:",
                vehicle["track_id"]
            )

    cap.release()