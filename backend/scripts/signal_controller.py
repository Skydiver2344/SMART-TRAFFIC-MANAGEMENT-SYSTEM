import time


class SignalController:

    def __init__(self, lanes):

        self.lanes = lanes

        # Initially, all signals are RED
        self.signal_states = {
            lane: "RED" for lane in lanes
        }

        self.current_lane = None

        # Emergency handling
        self.emergency_lane = None
        self.emergency_active = False


    def set_all_red(self):
        """Set all traffic signals to RED."""

        for lane in self.lanes:
            self.signal_states[lane] = "RED"


    def set_green(self, lane):
        """Give GREEN signal to the selected lane."""

        self.set_all_red()

        self.signal_states[lane] = "GREEN"
        self.current_lane = lane


    def initialize_system(self):
        """Initialize traffic signals with L1 GREEN."""

        self.set_all_red()
        self.set_green("L1")

        print("Traffic system initialized.")
        print("Initial GREEN lane: L1")


    def display_signals(self):
        """Display current signal states."""

        for lane, state in self.signal_states.items():
            print(f"{lane}: {state}")


    # ---------------- GREEN SIGNAL ----------------

    def start_green_timer(self, duration):
        """Start a non-blocking GREEN timer."""

        self.green_duration = duration
        self.green_start_time = time.time()

        print(
            f"\n{self.current_lane} GREEN for {duration} seconds."
        )


    def is_green_timer_expired(self):
        """Check whether the GREEN timer has expired."""

        if not hasattr(self, "green_start_time"):
            return False

        elapsed_time = time.time() - self.green_start_time

        return elapsed_time >= self.green_duration


    # ---------------- YELLOW SIGNAL ----------------

    def set_yellow(self):
        """Change the current GREEN lane to YELLOW."""

        if self.current_lane is not None:

            self.signal_states[self.current_lane] = "YELLOW"

            print(
                f"\n{self.current_lane} signal changed to YELLOW."
            )


    def start_yellow_timer(self, duration):
        """Start a non-blocking YELLOW timer."""

        self.yellow_duration = duration
        self.yellow_start_time = time.time()

        print(
            f"\n{self.current_lane} YELLOW for {duration} seconds."
        )


    def is_yellow_timer_expired(self):
        """Check whether the YELLOW timer has expired."""

        if not hasattr(self, "yellow_start_time"):
            return False

        elapsed_time = time.time() - self.yellow_start_time

        return elapsed_time >= self.yellow_duration


    def set_red(self):
        """Change the current lane to RED."""

        if self.current_lane is not None:

            self.signal_states[self.current_lane] = "RED"

            print(
                f"\n{self.current_lane} signal changed to RED."
            )

            self.current_lane = None


    # ---------------- EMERGENCY HANDLING ----------------

    def request_emergency(self, lane, yellow_duration=2):
        """
        Request emergency priority for a particular lane.
        """

        if lane not in self.lanes:
            print("Invalid emergency lane.")
            return

        # Avoid repeated requests for the same emergency
        if self.emergency_active or self.emergency_lane is not None:
            return

        self.emergency_lane = lane

        print(f"\nEMERGENCY VEHICLE DETECTED IN {lane}!")

        # If no lane is currently active
        if self.current_lane is None:

            self.activate_emergency_lane()

        # If emergency vehicle is already in the GREEN lane
        elif self.current_lane == lane:

            if self.signal_states[lane] == "GREEN":

                self.emergency_active = True

                print(
                    f"\n{lane} already GREEN. "
                    "Emergency priority activated."
                )

        # Another lane currently has GREEN
        elif self.signal_states[self.current_lane] == "GREEN":

            self.set_yellow()
            self.start_yellow_timer(yellow_duration)

            print(
                "\nSwitching to emergency lane after YELLOW."
            )


    def activate_emergency_lane(self):
        """Activate GREEN for the emergency lane."""

        if self.emergency_lane is None:
            return

        lane = self.emergency_lane

        self.set_green(lane)

        self.emergency_active = True

        print(
            f"\nEMERGENCY PRIORITY: {lane} GREEN!"
        )


    def release_emergency(self, yellow_duration=2):
        """
        Release emergency priority after the ambulance passes.
        """

        if not self.emergency_active:
            return

        print("\nEmergency vehicle has passed.")

        self.emergency_active = False
        self.emergency_lane = None

        # Safely terminate emergency GREEN
        if self.current_lane is not None:

            self.set_yellow()
            self.start_yellow_timer(yellow_duration)


    # ---------------- SIGNAL MANAGEMENT ----------------

    def update_signal_phase(self, yellow_duration=2):
        """
        Automatically manage GREEN, YELLOW and RED transitions.
        """

        # No active lane
        if self.current_lane is None:

            if self.emergency_lane is not None:
                self.activate_emergency_lane()

            return

        current_state = self.signal_states[self.current_lane]

        # GREEN to YELLOW
        if current_state == "GREEN":

            # Emergency GREEN stays active until released
            if self.emergency_active:
                return

            if self.is_green_timer_expired():

                print("\nGREEN duration expired.")

                self.set_yellow()
                self.start_yellow_timer(yellow_duration)

        # YELLOW to RED
        elif current_state == "YELLOW":

            if self.is_yellow_timer_expired():

                print("\nYELLOW duration expired.")

                self.set_red()

                # Activate emergency lane after current lane becomes RED
                if self.emergency_lane is not None:

                    self.activate_emergency_lane()


    # ---------------- NORMAL TRAFFIC ----------------

    def activate_next_lane(self, next_lane, green_duration):
        """Activate the selected lane and start its GREEN timer."""

        self.set_green(next_lane)

        print(f"\n{next_lane} is now GREEN.")

        self.start_green_timer(green_duration)


    def switch_lane(self, next_lane, yellow_duration=2):
        """
        Legacy lane-switch method.
        """

        self.set_yellow()
        self.start_yellow_timer(yellow_duration)
        self.set_red()

        self.set_green(next_lane)

        print(f"\n{next_lane} is now GREEN.")


    def is_all_red(self):
        """Check whether all signals are RED."""

        return all(
            state == "RED"
            for state in self.signal_states.values()
        )