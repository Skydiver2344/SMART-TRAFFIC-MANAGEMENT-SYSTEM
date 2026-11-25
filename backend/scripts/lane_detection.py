# Lane coordinates (1920 x 1080 resolution)

LANE_ROIS = {
    "L1": (795, 0, 1032, 160),
    "L2": (1339, 313, 1918, 573),
    "L3": (914, 885, 1192, 1079),
    "L4": (12, 483, 616, 756)
}


def identify_lane(center):

    x, y = center

    for lane, (x1, y1, x2, y2) in LANE_ROIS.items():

        if x1 <= x <= x2 and y1 <= y <= y2:
            return lane

    return "JUNCTION / OUTSIDE"

def count_vehicles_per_lane(vehicles):
    """
    Count detected vehicles belonging to each lane.
    Vehicles outside the four ROIs are ignored.
    """

    lane_counts = {
        "L1": 0,
        "L2": 0,
        "L3": 0,
        "L4": 0
    }

    for vehicle in vehicles:
        lane = identify_lane(vehicle["center"])

        if lane in lane_counts:
            lane_counts[lane] += 1

    return lane_counts