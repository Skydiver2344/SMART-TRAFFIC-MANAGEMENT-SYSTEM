import sys
import cv2
import threading
import time
import copy

from pathlib import Path


# ==================================================
# 1. PATH CONFIGURATION
# ==================================================
BACKEND_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BACKEND_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# ==================================================
# 2. TRAFFIC MANAGER
# ==================================================

class TrafficManager:

    def __init__(self):

        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)

        self.stop_event = None
        self.worker_thread = None

        self.latest_frame = None
        self.frame_number = 0
        

        self.traffic_state = {
            "signal_states": {
                "L1": "RED",
                "L2": "RED",
                "L3": "RED",
                "L4": "RED"
            },
            "lane_counts": {
                "L1": 0,
                "L2": 0,
                "L3": 0,
                "L4": 0
            },
            "waiting_times": {
                "L1": 0,
                "L2": 0,
                "L3": 0,
                "L4": 0
            },
            "current_lane": None,
            "emergency_active": False,
            "emergency_lane": None,
            "frame_count": 0
        }

        self.analytics_data = self._empty_analytics()
        self.status = "stopped"
        self.error = None


    @staticmethod
    def _empty_analytics():

        return {
            "total_vehicles": 0,
            "vehicle_distribution": {
                "cars": 0,
                "vans": 0,
                "motorcycles": 0,
                "buses": 0,
                "trucks": 0
            },
            "lane_vehicle_counts": {
                "L1": 0,
                "L2": 0,
                "L3": 0,
                "L4": 0
            },
            "density": {
                "low": 0,
                "medium": 0,
                "high": 0
            },
            "traffic_flow": [],
            "peak_traffic": {
                "interval": None,
                "start_seconds": None,
                "end_seconds": None,
                "vehicles": 0
            }
        }
    # ==================================================
    # 3. START MONITORING
    # ==================================================

    def start(self):

        with self.condition:

            if (
                self.worker_thread is not None
                and self.worker_thread.is_alive()
            ):
                raise RuntimeError(
                    "Traffic monitoring is already running."
                )

            self.stop_event = threading.Event()

            self.latest_frame = None
            self.frame_number = 0
            self.error = None
            self.analytics_data = self._empty_analytics()


            self.traffic_state = {
                "signal_states": {
                    lane: "RED"
                    for lane in ["L1", "L2", "L3", "L4"]
                },
                "lane_counts": {
                    lane: 0
                    for lane in ["L1", "L2", "L3", "L4"]
                },
                "waiting_times": {
                    lane: 0
                    for lane in ["L1", "L2", "L3", "L4"]
                },
                "current_lane": None,
                "emergency_active": False,
                "emergency_lane": None,
                "frame_count": 0
            }

            self.status = "starting"

            self.worker_thread = threading.Thread(
                target=self._run_worker,
                name="TrafficProcessingThread",
                daemon=True
            )

            self.worker_thread.start()

            self.condition.notify_all()

            return self.get_status()

    # ==================================================
    # 4. BACKGROUND PROCESSING
    # ==================================================

    def _run_worker(self):

        try:

            # Import here so API startup does not wait
            # for YOLO model initialization.

            from main import run_traffic

            with self.condition:

                if self.stop_event.is_set():
                    self.status = "stopped"
                    self.condition.notify_all()
                    return

                self.status = "running"
                self.condition.notify_all()

            result = run_traffic(
                stop_event=self.stop_event,
                frame_callback=self._update_frame,
                state_callback=self._update_state,
                analytics_callback=self._update_analytics,
                preview=False
            )

            with self.condition:

                if self.stop_event.is_set():
                    self.status = "stopped"

                elif result == "completed":
                    self.status = "completed"

                else:
                    self.status = "stopped"

                self.condition.notify_all()

        except Exception as error:

            with self.condition:

                self.status = "error"
                self.error = str(error)

                self.condition.notify_all()

            print("\nTRAFFIC MANAGER ERROR:")
            print(error)

    # ==================================================
    # 5. UPDATE VIDEO FRAME
    # ==================================================

    def _update_frame(self, frame):

        success, encoded_frame = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 80]
        )

        if not success:
            raise RuntimeError(
                "Unable to encode processed video frame."
            )

        frame_bytes = encoded_frame.tobytes()

        with self.condition:

            self.latest_frame = frame_bytes
            self.frame_number += 1

            self.condition.notify_all()

    # ==================================================
    # 6. UPDATE TRAFFIC STATE
    # ==================================================

    def _update_state(self, state):

        with self.condition:

            self.traffic_state = state.copy()

            self.condition.notify_all()

    def _update_analytics(self, analytics):
        with self.condition:
            self.analytics_data = copy.deepcopy(analytics)
            self.condition.notify_all()

    def get_analytics(self):
        with self.lock:
            return copy.deepcopy(self.analytics_data)
    # ==================================================
    # 7. STOP MONITORING
    # ==================================================

    def stop(self, timeout=10):

        with self.condition:

            if (
                self.worker_thread is None
                or not self.worker_thread.is_alive()
            ):

                if self.status not in ["completed", "error"]:
                    self.status = "stopped"

                self.condition.notify_all()

                return True

            self.status = "stopping"

            self.stop_event.set()

            self.condition.notify_all()

            worker = self.worker_thread

        # Never join while holding the manager lock.
        worker.join(timeout=timeout)

        with self.condition:

            if worker.is_alive():

                self.condition.notify_all()
                return False

            self.status = "stopped"

            self.condition.notify_all()

            return True

    # ==================================================
    # 8. GET CURRENT STATUS
    # ==================================================

    def get_status(self):

        with self.lock:

            return {
                "status": self.status,
                "error": self.error,
                "is_running": (
                    self.worker_thread is not None
                    and self.worker_thread.is_alive()
                ),
                "traffic": self.traffic_state.copy()
            }

    # ==================================================
    # 9. MJPEG VIDEO STREAM
    # ==================================================

    def generate_frames(self):

        last_frame_number = 0

        while True:

            with self.condition:

                # Wait for a new frame or session termination.
                self.condition.wait_for(
                    lambda: (
                        self.frame_number > last_frame_number
                        or self.status in [
                            "stopped",
                            "completed",
                            "error"
                        ]
                    ),
                    timeout=2
                )

                if (
                    self.frame_number > last_frame_number
                    and self.latest_frame is not None
                ):

                    frame = self.latest_frame
                    last_frame_number = self.frame_number

                else:

                    if self.status in [
                        "stopped",
                        "completed",
                        "error"
                    ]:
                        return

                    continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + frame
                + b"\r\n"
            )