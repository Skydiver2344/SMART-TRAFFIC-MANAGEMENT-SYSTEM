from ultralytics import YOLO
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    PROJECT_DIR
    / "runs"
    / "ambulance_merged-2"
    / "weights"
    / "best.pt"
)

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Ambulance model not found: {MODEL_PATH}")

model = YOLO(str(MODEL_PATH))


def detect_ambulance(frame):

    results = model.track(
        source=frame,
        conf=0.47,
        persist=True,
        tracker="bytetrack.yaml",
        verbose=False
    )

    ambulances = []

    for result in results:

        if result.boxes is None:
            continue

        for box in result.boxes:

            confidence = float(box.conf[0])

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            track_id = None

            if box.id is not None:
                track_id = int(box.id[0])

            ambulance = {
                "class": "Ambulance",
                "confidence": confidence,
                "bbox": (x1, y1, x2, y2),
                "center": (center_x, center_y),
                "track_id": track_id
            }

            ambulances.append(ambulance)

    return ambulances