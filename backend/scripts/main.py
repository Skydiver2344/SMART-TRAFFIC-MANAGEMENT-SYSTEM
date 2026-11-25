
import cv2
import os
from pathlib import Path

from detect_vehicles import detect_vehicles

from lane_detection import (
    count_vehicles_per_lane,
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

# ==================================================
# 1. CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Video path can be configured through an environment variable.
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

def get_green_duration(vehicle_count):

    if vehicle_count < 5:
        return 5

    elif vehicle_count <= 7:
        return 7

    else:
        return 10


# ==================================================
# 2. INITIALIZE SYSTEM
# ==================================================

def main():

    print("=" * 55)
    print(" AI BASED SMART TRAFFIC MANAGEMENT SYSTEM")
    print("=" * 55)

    # Check video path
    if not VIDEO_PATH.exists():
        print("\nERROR: Video file not found:")
        print(VIDEO_PATH)
        return

    # Open video
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    VIDEO_FPS = cap.get(cv2.CAP_PROP_FPS)

    if VIDEO_FPS <= 0:
        VIDEO_FPS = 30

    FRAME_DELAY = max(1, int(1000 / VIDEO_FPS))

    print(f"Video FPS: {VIDEO_FPS}")
    print(f"Frame delay: {FRAME_DELAY} ms")

    if not cap.isOpened():
        print("\nERROR: Unable to open video.")
        return

    # Initialize signal controller
    controller = SignalController(LANES)
        # Initialize ambulance tracking
    ambulance_tracker = AmbulanceTracker(
        exit_confirmation_frames=3
    )

    # Initialize emergency manager
    emergency_manager = EmergencyManager(
        ambulance_tracker,
        controller,
        yellow_duration=YELLOW_DURATION
    )

    # Reset waiting-time tracking
    reset_waiting_times()

    # Initialize all signals RED and L1 GREEN
    controller.initialize_system()

    controller.start_green_timer(GREEN_DURATION)

    # Initialize lane counts
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
    print("Press Q to stop.\n")


    # ==================================================
    # 3. MAIN TRAFFIC MANAGEMENT LOOP
    # ==================================================

    try:

        while True:

            ret, frame = cap.read()

            if not ret:
                print("\nVideo ended.")
                break

            frame_count += 1

            # ------------------------------------------
            # 3.1 EMERGENCY VEHICLE DETECTION
            # ------------------------------------------

            ambulances = detect_ambulance(frame)

            emergency_manager.update(ambulances)

            # ------------------------------------------
            # 3.1 VEHICLE DETECTION
            # ------------------------------------------

            if frame_count % DETECTION_INTERVAL == 0:

                vehicles = detect_vehicles(frame)

                lane_counts = count_vehicles_per_lane(
                    vehicles
                )


            # ------------------------------------------
            # 3.2 UPDATE WAITING TIMES
            # ------------------------------------------

            if controller.current_lane is not None:

                waiting_times = update_waiting_times(
                    controller.current_lane
                )


            # ------------------------------------------
            # 3.3 UPDATE SIGNAL PHASE
            # ------------------------------------------

            previous_lane = controller.current_lane

            controller.update_signal_phase(
                YELLOW_DURATION
            )


            # ------------------------------------------
            # 3.4 CHECK SIGNAL TRANSITION
            # ------------------------------------------

            if (
                previous_lane is not None
                and controller.current_lane is None
                and not emergency_manager.is_emergency_active()
            ):

                print("\n" + "-" * 45)
                print("Current GREEN phase completed.")
                print("All signals are RED.")

                # Update waiting times
                waiting_times = update_waiting_times(
                    previous_lane
                )


                # --------------------------------------
                # DISPLAY CURRENT TRAFFIC INFORMATION
                # --------------------------------------

                print("\nCurrent vehicle counts:")

                for lane, count in lane_counts.items():

                    print(f"{lane}: {count}")

                print("\nCurrent waiting times:")

                for lane, wait_time in waiting_times.items():

                    print(
                        f"{lane}: {wait_time:.2f} seconds"
                    )


                # --------------------------------------
                # 3.5 SELECT NEXT LANE
                # --------------------------------------

                next_lane = select_next_lane(
                    lane_counts,
                    waiting_times,
                    MAX_WAIT_TIME,
                    current_lane=previous_lane
                )

                print("\nScheduler selected:", next_lane)


                # --------------------------------------
                # 3.6 ACTIVATE NEXT LANE
                # --------------------------------------

                if next_lane is not None:

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

                else:

                    print("ERROR: No eligible lane found.")
                    break


            # ==================================================
            # 4. VISUALIZATION
            # ==================================================

            display_frame = frame.copy()


            # ------------------------------------------
            # 4.1 DRAW VEHICLE BOUNDING BOXES
            # ------------------------------------------

            for vehicle in vehicles:

                x1, y1, x2, y2 = vehicle["bbox"]

                cx, cy = vehicle["center"]

                x1, y1 = int(x1), int(y1)
                x2, y2 = int(x2), int(y2)

                cx, cy = int(cx), int(cy)

                # Bounding box
                cv2.rectangle(
                    display_frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    1
                )

                # Vehicle centre
                cv2.circle(
                    display_frame,
                    (cx, cy),
                    3,
                    (0, 0, 255),
                    -1
                )

                # Vehicle label
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


            
            # ------------------------------------------
            # 4.2 DRAW LANE ROIs AND WAITING TIMES
            # ------------------------------------------

            for lane, (x1, y1, x2, y2) in LANE_ROIS.items():

                # Draw ROI rectangle
                cv2.rectangle(
                    display_frame,
                    (x1, y1),
                    (x2, y2),
                    (255, 0, 0),
                    1
                )

                # Display lane name
                cv2.putText(
                    display_frame,
                    lane,
                    (x1 + 5, y1 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 0, 0),
                    2
                )

                # Get lane waiting time
                wait_time = waiting_times.get(lane, 0)

                # Display waiting time near ROI
                wait_text = f"Wait: {wait_time:.1f}s"

                # Green text for currently active lane,
                # red text for waiting lanes
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


            # ------------------------------------------
            # 4.3 DISPLAY LANE COUNTS
            # ------------------------------------------

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


            # ------------------------------------------
            # 4.4 DISPLAY SIGNAL STATES
            # ------------------------------------------

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


            # ------------------------------------------
            # 4.5 DISPLAY VIDEO
            # ------------------------------------------

            resized_frame = cv2.resize(
                display_frame,
                (DISPLAY_WIDTH, DISPLAY_HEIGHT)
            )

            cv2.imshow(
                "AI Based Smart Traffic Management System",
                resized_frame
            )


            # ------------------------------------------
            # 4.6 STOP CONDITION
            # ------------------------------------------

            if cv2.waitKey(FRAME_DELAY) & 0xFF == ord("q"):

                print("\nSystem stopped by user.")
                break


    # ==================================================
    # 5. CLEANUP
    # ==================================================

    finally:

        cap.release()
        cv2.destroyAllWindows()

        print("\n" + "=" * 55)
        print("TRAFFIC MANAGEMENT SYSTEM STOPPED")
        print("=" * 55)


# ==================================================
# 6. PROGRAM ENTRY POINT
# ==================================================

if __name__ == "__main__":
    main()
