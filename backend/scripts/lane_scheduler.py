
import time

LANES = ["L1", "L2", "L3", "L4"]

# Stores when each lane started waiting
waiting_start_time = {
    lane: None for lane in LANES
}


def reset_waiting_times():
    """Reset waiting-time tracking."""
    for lane in LANES:
        waiting_start_time[lane] = None


def update_waiting_times(current_lane):
    """
    Update waiting times for all lanes.
    The currently GREEN lane is not considered waiting.
    """

    current_time = time.monotonic()
    waiting_times = {}

    for lane in LANES:

        if lane == current_lane:
            waiting_start_time[lane] = None
            waiting_times[lane] = 0

        else:
            if waiting_start_time[lane] is None:
                waiting_start_time[lane] = current_time

            waiting_times[lane] = (
                current_time - waiting_start_time[lane]
            )

    return waiting_times


def check_max_waiting_lane(waiting_times, max_wait_time):
    """
    Return the lane with the longest waiting time
    if it has reached the maximum waiting threshold.
    """

    if not waiting_times:
        return None

    longest_waiting_lane = max(
        waiting_times,
        key=waiting_times.get
    )

    if waiting_times[longest_waiting_lane] >= max_wait_time:
        return longest_waiting_lane

    return None


def calculate_priority_scores(
    lane_counts,
    waiting_times,
    alpha=0.6,
    beta=0.4
):
    """
    Calculate priority scores.

    alpha = vehicle demand weight
    beta = waiting time weight
    """

    if not lane_counts:
        return {}

    max_demand = max(lane_counts.values())
    max_wait = max(waiting_times.values(), default=0)

    priority_scores = {}

    for lane in lane_counts:

        demand = (
            lane_counts[lane] / max_demand
            if max_demand > 0 else 0
        )

        wait = (
            waiting_times[lane] / max_wait
            if max_wait > 0 else 0
        )

        priority_scores[lane] = (
            alpha * demand + beta * wait
        )

    return priority_scores


def select_next_lane(
    lane_counts,
    waiting_times,
    max_wait_time,
    current_lane
):
    """
    Select the next lane, excluding the current GREEN lane.
    """

    eligible_lanes = [
        lane for lane in lane_counts
        if lane != current_lane
    ]

    if not eligible_lanes:
        return None

    eligible_counts = {
        lane: lane_counts[lane]
        for lane in eligible_lanes
    }

    eligible_waiting = {
        lane: waiting_times[lane]
        for lane in eligible_lanes
    }

    # Maximum waiting-time override
    priority_lane = check_max_waiting_lane(
        eligible_waiting,
        max_wait_time
    )

    if priority_lane is not None:
        return priority_lane

    # Calculate weighted priority scores
    priority_scores = calculate_priority_scores(
        eligible_counts,
        eligible_waiting
    )

    return max(
        priority_scores,
        key=priority_scores.get
    )
