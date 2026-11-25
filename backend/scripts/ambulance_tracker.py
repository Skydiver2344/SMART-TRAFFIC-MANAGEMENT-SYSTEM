from lane_detection import identify_lane


class AmbulanceTracker:

    def __init__(self, exit_confirmation_frames=3):

        self.tracked_ambulances = {}

        self.exit_confirmation_frames = exit_confirmation_frames

    def update(self, ambulances):

        completed_ids = []

        for ambulance in ambulances:

            track_id = ambulance.get("track_id")

            if track_id is None:
                continue

            current_lane = identify_lane(ambulance["center"])

            # Initialise a new ambulance
            if track_id not in self.tracked_ambulances:

                # Only register an ambulance when first seen in an approach lane
                if current_lane == "JUNCTION / OUTSIDE":
                    continue

                self.tracked_ambulances[track_id] = {
                    "entry_lane": current_lane,
                    "entered_junction": False,
                    "exit_lane": None,
                    "exit_frames": 0,
                    "passed": False
                }

                print(
                    f"Ambulance {track_id} detected in {current_lane}."
                )

                continue

            track = self.tracked_ambulances[track_id]

            if track["passed"]:
                continue

            # Ambulance enters the junction
            if current_lane == "JUNCTION / OUTSIDE":

                track["entered_junction"] = True
                track["exit_lane"] = None
                track["exit_frames"] = 0

            # Ambulance appears in another lane
            elif (
                track["entered_junction"]
                and current_lane != track["entry_lane"]
            ):

                if track["exit_lane"] == current_lane:
                    track["exit_frames"] += 1

                else:
                    track["exit_lane"] = current_lane
                    track["exit_frames"] = 1

                # Confirm exit only after consecutive detections
                if (
                    track["exit_frames"]
                    >= self.exit_confirmation_frames
                ):

                    track["passed"] = True

                    completed_ids.append(track_id)

                    print(
                        f"Ambulance {track_id} passed "
                        f"from {track['entry_lane']} "
                        f"to {current_lane}."
                    )

            # Ambulance returns to its entry lane
            elif current_lane == track["entry_lane"]:

                track["exit_lane"] = None
                track["exit_frames"] = 0

        return completed_ids

    def all_ambulances_passed(self):

        if not self.tracked_ambulances:
            return False

        return all(
            track["passed"]
            for track in self.tracked_ambulances.values()
        )

    def get_active_ambulances(self):

        return [
            track_id
            for track_id, track in self.tracked_ambulances.items()
            if not track["passed"]
        ]

    def reset(self):

        self.tracked_ambulances.clear()