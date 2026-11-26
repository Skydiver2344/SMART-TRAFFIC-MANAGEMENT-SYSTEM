from collections import defaultdict


class AnalyticsCollector:

    def __init__(self, video_fps):

        self.video_fps = max(float(video_fps), 1.0)

        self.vehicle_records = {}

        self.vehicle_counts = {
            "cars": 0,
            "vans": 0,
            "motorcycles": 0,
            "buses": 0,
            "trucks": 0
        }

        self.lane_vehicle_counts = {
            "L1": 0,
            "L2": 0,
            "L3": 0,
            "L4": 0
        }

        self.density_observations = {
            "low": 0,
            "medium": 0,
            "high": 0
        }

        self.total_density_observations = 0

        self.traffic_flow = defaultdict(int)

        self.total_vehicles = 0

    # ==============================================
    # VEHICLE CLASS NORMALIZATION
    # ==============================================

    @staticmethod
    def normalize_class(vehicle_class):

        mapping = {
            "car": "cars",
            "van": "vans",
            "motorcycle": "motorcycles",
            "bus": "buses",
            "truck": "trucks"
        }

        return mapping.get(
            str(vehicle_class).lower(),
            None
        )

    # ==============================================
    # RECORD UNIQUE VEHICLES
    # ==============================================

    def update_vehicles(self, vehicles, frame_count, lane_counts):

        video_seconds = frame_count / self.video_fps

        interval_bucket = int(video_seconds // 5)

        for vehicle in vehicles:

            track_id = vehicle.get("track_id")

            # Ignore detections without tracking IDs.
            if track_id is None:
                continue

            lane = vehicle.get("lane")

            # Only count vehicles inside valid lanes.
            if lane not in self.lane_vehicle_counts:
                continue

            vehicle_class = self.normalize_class(
                vehicle.get("class")
            )

            if vehicle_class is None:
                continue

            confidence = float(
                vehicle.get("confidence", 0)
            )

            if track_id not in self.vehicle_records:

                self.vehicle_records[track_id] = {
                    "class_scores": defaultdict(float),
                    "lane": lane,
                    "interval": interval_bucket
                }

                self.total_vehicles += 1

                self.lane_vehicle_counts[lane] += 1

                self.traffic_flow[interval_bucket] += 1

            record = self.vehicle_records[track_id]

            # Accumulate confidence-weighted class votes.
            record["class_scores"][vehicle_class] += confidence

        # Update density using the latest lane counts.
        self.update_density(lane_counts)

    # ==============================================
    # TRAFFIC DENSITY
    # ==============================================

    def update_density(self, lane_counts):

        for count in lane_counts.values():

            if count <= 3:
                category = "low"

            elif count <= 7:
                category = "medium"

            else:
                category = "high"

            self.density_observations[category] += 1

            self.total_density_observations += 1

    # ==============================================
    # FINAL VEHICLE TYPE COUNTS
    # ==============================================

    def calculate_vehicle_distribution(self):

        counts = self.vehicle_counts.copy()

        for record in self.vehicle_records.values():

            scores = record["class_scores"]

            if not scores:
                continue

            final_class = max(
                scores,
                key=scores.get
            )

            counts[final_class] += 1

        return counts

    # ==============================================
    # DENSITY PERCENTAGES
    # ==============================================

    def calculate_density(self):

        if self.total_density_observations == 0:

            return {
                "low": 0,
                "medium": 0,
                "high": 0
            }

        total = self.total_density_observations

        return {
            category: round(
                count / total * 100,
                2
            )
            for category, count
            in self.density_observations.items()
        }

    # ==============================================
    # TRAFFIC FLOW
    # ==============================================

    def calculate_traffic_flow(self):
        if not self.traffic_flow:
            return []

        last_interval = max(self.traffic_flow)

        return [
            {
                "interval": interval,
                "start_seconds": interval * 5,
                "end_seconds": (interval + 1) * 5,
                "vehicles": self.traffic_flow.get(interval, 0)
            }
            for interval in range(last_interval + 1)
        ]

    # ==============================================
    # BUSIEST MINUTE
    # ==============================================

    def calculate_peak_traffic(self):
        flow = self.calculate_traffic_flow()

        if not flow:
            return {
                "interval": None,
                "start_seconds": None,
                "end_seconds": None,
                "vehicles": 0
            }

        return max(flow, key=lambda item: item["vehicles"])

    # ==============================================
    # COMPLETE ANALYTICS SNAPSHOT
    # ==============================================

    def get_analytics(self):

        return {
            "total_vehicles": self.total_vehicles,

            "vehicle_distribution":
                self.calculate_vehicle_distribution(),

            "lane_vehicle_counts":
                self.lane_vehicle_counts.copy(),

            "density":
                self.calculate_density(),

            "traffic_flow":
                self.calculate_traffic_flow(),

            "peak_traffic":
                self.calculate_peak_traffic()
        }