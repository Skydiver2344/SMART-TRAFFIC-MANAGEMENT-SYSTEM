
class EmergencyManager:

    def __init__(
        self,
        ambulance_tracker,
        signal_controller,
        yellow_duration=2
    ):

        self.ambulance_tracker = ambulance_tracker
        self.signal_controller = signal_controller

        self.yellow_duration = yellow_duration

        self.active_ambulance_id = None
        self.emergency_lane = None

        self.emergency_active = False

    # ==============================================
    # 1. UPDATE EMERGENCY STATUS
    # ==============================================

    def update(self, ambulances):
        """
        Update ambulance tracking and manage emergency signals.

        Called once for every video frame.
        """

        # Update ambulance tracking
        completed_ids = self.ambulance_tracker.update(
            ambulances
        )

        # ------------------------------------------
        # CHECK FOR NEW AMBULANCE
        # ------------------------------------------

        if self.active_ambulance_id is None:

            active_ids = (
                self.ambulance_tracker.get_active_ambulances()
            )

            if active_ids:

                # Single ambulance implementation
                track_id = active_ids[0]

                track = (
                    self.ambulance_tracker
                    .tracked_ambulances[track_id]
                )

                lane = track["entry_lane"]

                # Validate emergency lane
                if lane not in self.signal_controller.lanes:
                    return

                self.active_ambulance_id = track_id
                self.emergency_lane = lane

                self.emergency_active = True

                print("\n" + "=" * 45)
                print("EMERGENCY MANAGER ACTIVATED")
                print(f"Ambulance ID: {track_id}")
                print(f"Emergency Lane: {lane}")
                print("=" * 45)

                # Request emergency priority
                self.signal_controller.request_emergency(
                    lane,
                    self.yellow_duration
                )

        # ------------------------------------------
        # CHECK FOR CONFIRMED AMBULANCE EXIT
        # ------------------------------------------

        if self.active_ambulance_id in completed_ids:

            self.release_emergency()

    # ==============================================
    # 2. RELEASE EMERGENCY
    # ==============================================

    def release_emergency(self):
        """
        Release emergency priority after confirmed passage.
        """

        if not self.emergency_active:
            return

        print("\n" + "=" * 45)
        print("AMBULANCE PASSAGE CONFIRMED")
        print(f"Ambulance ID: {self.active_ambulance_id}")
        print(f"Lane: {self.emergency_lane}")
        print("Releasing emergency priority.")
        print("=" * 45)

        # Release emergency signal
        self.signal_controller.release_emergency(
            self.yellow_duration
        )

        # Reset ambulance tracking
        

        # Reset manager state
        self.active_ambulance_id = None
        self.emergency_lane = None

        self.emergency_active = False

    # ==============================================
    # 3. CHECK EMERGENCY STATUS
    # ==============================================

    def is_emergency_active(self):
        """
        Check whether emergency handling is in progress.

        Includes the pending transition to emergency GREEN.
        """

        return self.emergency_active

    # ==============================================
    # 4. RESET MANAGER
    # ==============================================

    def reset(self):
        """
        Reset ambulance tracking and manager state.
        """

        self.ambulance_tracker.reset()

        self.active_ambulance_id = None
        self.emergency_lane = None

        self.emergency_active = False
