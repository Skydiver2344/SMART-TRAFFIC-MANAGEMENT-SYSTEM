import cv2
import os
import threading

from pathlib import Path

from detect_vehicles import (
    detect_vehicles,
    reset_vehicle_tracker
)
from lane_detection import (
    count_vehicles_per_lane,
    identify_lane,
    LANE_ROIS
)

from lane_scheduler import (
    update_waiting_times,
    reset_waiting_times,
    select_next_lane
)

from signal_controller import SignalController

from detect_ambulance import detect_ambulance
from ambulance_tracker import AmbulanceTracker
from emergency_manager import EmergencyManager


from analytics_collector import AnalyticsCollector

# ==================================================
# 1. CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

VIDEO_ENV = os.getenv("TRAFFIC_VIDEO_PATH")

if VIDEO_ENV:
    VIDEO_PATH = Path(VIDEO_ENV).expanduser()

    if not VIDEO_PATH.is_absolute():
        VIDEO_PATH = BASE_DIR / VIDEO_PATH
else:
    VIDEO_PATH = BASE_DIR / "demo_video.mp4"


LANES = ["L1", "L2", "L3", "L4"]

GREEN_DURATION = 5
YELLOW_DURATION = 2

MAX_WAIT_TIME = 30

DETECTION_INTERVAL = 5

DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720


# ==================================================
# 2. GREEN SIGNAL DURATION
# ==================================================

def get_green_duration(vehicle_count):

    if vehicle_count < 5:
        return 5

    elif vehicle_count <= 7:
        return 7

    else:
        return 10


# ==================================================
# 3. TRAFFIC STATE SNAPSHOT
# ==================================================

def get_traffic_state(
    controller,
    lane_counts,
    waiting_times,
    emergency_manager,
    frame_count
):

    return {
        "signal_states": controller.signal_states.copy(),

        "lane_counts": {
            lane: int(count)
            for lane, count in lane_counts.items()
        },

        "waiting_times": {
            lane: round(float(wait), 2)
            for lane, wait in waiting_times.items()
        },

        "current_lane": controller.current_lane,

        "emergency_active": (
            emergency_manager.is_emergency_active()
        ),

        "emergency_lane": controller.emergency_lane,

        "frame_count": frame_count
    }


# ==================================================
# 4. MAIN TRAFFIC PROCESSING FUNCTION
# ==================================================

def run_traffic(
    stop_event=None,
    frame_callback=None,
    state_callback=None,
    analytics_callback=None,
    preview=False
):
    """
    Run the traffic management system.

    Parameters
    ----------
    stop_event:
        threading.Event used to stop processing.

    frame_callback:
        Receives the resized processed video frame.

    state_callback:
        Receives the latest traffic state dictionary.

    preview:
        True enables the standalone OpenCV window.
        False disables GUI for FastAPI execution.

    Returns
    -------
    str:
        "completed" or "stopped"
    """

    if stop_event is None:
        stop_event = threading.Event()

    print("=" * 55)
    print(" AI BASED SMART TRAFFIC MANAGEMENT SYSTEM")
    print("=" * 55)

    # ----------------------------------------------
    # CHECK VIDEO
    # ----------------------------------------------

    if not VIDEO_PATH.exists():
        raise FileNotFoundError(
            f"Video file not found: {VIDEO_PATH}"
        )

    cap = cv2.VideoCapture(str(VIDEO_PATH))

    try:

        if not cap.isOpened():
            raise RuntimeError(
                f"Unable to open video: {VIDEO_PATH}"
            )

        video_fps = cap.get(cv2.CAP_PROP_FPS)

        if video_fps <= 0:
            video_fps = 30

        frame_delay = max(
            1,
            int(1000 / video_fps)
        )

        print(f"Video FPS: {video_fps}")
        print(f"Frame delay: {frame_delay} ms")
        analytics = AnalyticsCollector(video_fps)


        # ------------------------------------------
        # INITIALIZE TRAFFIC SYSTEM
        # ------------------------------------------

        controller = SignalController(LANES)

        ambulance_tracker = AmbulanceTracker(
            exit_confirmation_frames=3
        )

        emergency_manager = EmergencyManager(
            ambulance_tracker,
            controller,
            yellow_duration=YELLOW_DURATION
        )

        reset_waiting_times()
        reset_vehicle_tracker()

        controller.initialize_system()

        controller.start_green_timer(
            GREEN_DURATION
        )

        lane_counts = {
            lane: 0 for lane in LANES
        }

        waiting_times = {
            lane: 0 for lane in LANES
        }

        vehicles = []

        frame_count = 0

        print("\nTraffic management system started.")
        print("Initial GREEN lane: L1")

        if preview:
            print("Press Q to stop.\n")

        # ------------------------------------------
        # MAIN TRAFFIC MANAGEMENT LOOP
        # ------------------------------------------

        while not stop_event.is_set():

            ret, frame = cap.read()

            if not ret:
                print("\nVideo ended.")
                return "completed"

            frame_count += 1

            # ======================================
            # 4.1 EMERGENCY VEHICLE DETECTION
            # ======================================

            ambulances = detect_ambulance(frame)

            emergency_manager.update(ambulances)

            # ======================================
            # 4.2 NORMAL VEHICLE DETECTION
            # ======================================

            if frame_count % DETECTION_INTERVAL == 0:

                vehicles = detect_vehicles(frame)

                lane_counts = count_vehicles_per_lane(
                    vehicles
                )

                analytics_vehicles = []

                for vehicle in vehicles:

                    analytics_vehicle = vehicle.copy()

                    analytics_vehicle["lane"] = identify_lane(
                        vehicle["center"]
                    )

                    analytics_vehicles.append(analytics_vehicle)

                analytics.update_vehicles(
                    analytics_vehicles,
                    frame_count,
                    lane_counts
                )

                if analytics_callback is not None:
                    analytics_callback(
                        analytics.get_analytics()
                    )

            # ======================================
            # 4.3 UPDATE WAITING TIMES
            # ======================================

            if controller.current_lane is not None:

                waiting_times = update_waiting_times(
                    controller.current_lane
                )

            # ======================================
            # 4.4 UPDATE SIGNAL PHASE
            # ======================================

            previous_lane = controller.current_lane

            controller.update_signal_phase(
                YELLOW_DURATION
            )

            # ======================================
            # 4.5 CHECK SIGNAL TRANSITION
            # ======================================

            if (
                previous_lane is not None
                and controller.current_lane is None
                and not emergency_manager.is_emergency_active()
            ):

                print("\n" + "-" * 45)
                print("Current GREEN phase completed.")
                print("All signals are RED.")

                waiting_times = update_waiting_times(
                    previous_lane
                )

                print("\nCurrent vehicle counts:")

                for lane, count in lane_counts.items():
                    print(f"{lane}: {count}")

                print("\nCurrent waiting times:")

                for lane, wait_time in waiting_times.items():
                    print(
                        f"{lane}: {wait_time:.2f} seconds"
                    )

                # ----------------------------------
                # SELECT NEXT LANE
                # ----------------------------------

                next_lane = select_next_lane(
                    lane_counts,
                    waiting_times,
                    MAX_WAIT_TIME,
                    current_lane=previous_lane
                )

                print("\nScheduler selected:", next_lane)

                # ----------------------------------
                # ACTIVATE NEXT LANE
                # ----------------------------------

                if next_lane is None:
                    raise RuntimeError(
                        "Scheduler could not select a lane."
                    )

                green_duration = get_green_duration(
                    lane_counts[next_lane]
                )

                print(
                    f"Green time allocated to {next_lane}: "
                    f"{green_duration} seconds"
                )

                controller.activate_next_lane(
                    next_lane,
                    green_duration
                )

            # ======================================
            # 4.6 CREATE DISPLAY FRAME
            # ======================================

            display_frame = frame.copy()

            # --------------------------------------
            # DRAW VEHICLE BOUNDING BOXES
            # --------------------------------------

            for vehicle in vehicles:

                x1, y1, x2, y2 = vehicle["bbox"]

                cx, cy = vehicle["center"]

                x1, y1 = int(x1), int(y1)
                x2, y2 = int(x2), int(y2)

                cx, cy = int(cx), int(cy)

                cv2.rectangle(
                    display_frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    1
                )

                cv2.circle(
                    display_frame,
                    (cx, cy),
                    3,
                    (0, 0, 255),
                    -1
                )

                label = (
                    f'{vehicle["class"]} '
                    f'{vehicle["confidence"]:.2f}'
                )

                cv2.putText(
                    display_frame,
                    label,
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (0, 255, 0),
                    1
                )

            # --------------------------------------
            # DRAW LANE ROIs AND WAITING TIMES
            # --------------------------------------

            for lane, (x1, y1, x2, y2) in LANE_ROIS.items():

                cv2.rectangle(
                    display_frame,
                    (x1, y1),
                    (x2, y2),
                    (255, 0, 0),
                    1
                )

                cv2.putText(
                    display_frame,
                    lane,
                    (x1 + 5, y1 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 0, 0),
                    2
                )

                wait_time = waiting_times.get(lane, 0)

                wait_text = f"Wait: {wait_time:.1f}s"

                if lane == controller.current_lane:
                    wait_color = (0, 255, 0)
                else:
                    wait_color = (0, 0, 255)

                cv2.putText(
                    display_frame,
                    wait_text,
                    (x1 + 5, y1 + 45),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    wait_color,
                    2
                )

            # --------------------------------------
            # DISPLAY LANE COUNTS
            # --------------------------------------

            y_position = 40

            for lane, count in lane_counts.items():

                cv2.putText(
                    display_frame,
                    f"{lane}: {count}",
                    (1640, y_position),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 30, 255),
                    2
                )

                y_position += 35

            # --------------------------------------
            # DISPLAY SIGNAL STATES
            # --------------------------------------

            y_position = 40

            for lane, state in controller.signal_states.items():

                if state == "GREEN":
                    color = (0, 255, 0)

                elif state == "YELLOW":
                    color = (0, 255, 255)

                else:
                    color = (0, 0, 255)

                cv2.putText(
                    display_frame,
                    f"{lane}: {state}",
                    (200, y_position),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )

                y_position += 35

            # ======================================
            # 4.7 RESIZE FRAME
            # ======================================

            resized_frame = cv2.resize(
                display_frame,
                (DISPLAY_WIDTH, DISPLAY_HEIGHT)
            )

            # ======================================
            # 4.8 SEND FRAME TO CALLBACK
            # ======================================

            if frame_callback is not None:
                frame_callback(resized_frame)

            # ======================================
            # 4.9 SEND TRAFFIC STATE TO CALLBACK
            # ======================================

            if state_callback is not None:

                traffic_state = get_traffic_state(
                    controller,
                    lane_counts,
                    waiting_times,
                    emergency_manager,
                    frame_count
                )

                state_callback(traffic_state)

            # ======================================
            # 4.10 STANDALONE PREVIEW
            # ======================================

            if preview:

                cv2.imshow(
                    "AI Based Smart Traffic Management System",
                    resized_frame
                )

                if cv2.waitKey(frame_delay) & 0xFF == ord("q"):

                    print("\nSystem stopped by user.")

                    stop_event.set()
                    return "stopped"

            else:

                # Interruptible frame pacing for API execution
                if stop_event.wait(frame_delay / 1000):
                    break

        print("\nSystem stopped.")

        return "stopped"

    finally:

        cap.release()

        if preview:
            cv2.destroyAllWindows()

        print("\n" + "=" * 55)
        print("TRAFFIC MANAGEMENT SYSTEM STOPPED")
        print("=" * 55)




# ==================================================
# 5. STANDALONE PROGRAM ENTRY POINT
# ==================================================

def main():

    stop_event = threading.Event()

    try:

        run_traffic(
            stop_event=stop_event,
            preview=True
        )

    except Exception as error:

        print("\nTRAFFIC SYSTEM ERROR:")
        print(error)

        raise


if __name__ == "__main__":
    main()
