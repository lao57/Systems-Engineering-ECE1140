class CTC:
    def __init__(self):
        self.block_authority = [0] * 150  # Authority for blocks 1-150 (meters)
        self.maintenance = [False] * 150  # Maintenance status for each block
        self.actual_occupancy = [False] * 150  # Occupancy from track
        self.block_occupancy = [False] * 150  # Combined occupancy (actual + maintenance)
        self.switch_states = [False] * 6  # Current state of switches
        self.light_states = [False] * 6  # Current state of traffic lights
        self.crossing_states = [False] * 2  # Current state of crossing gates
        self.track_controller = None  # Reference to track controller UI

    def receive_maintenance_requests(self, maintenance_requests):
        try:
            if len(maintenance_requests) != 150:
                raise ValueError
            self.maintenance = [bool(req) for req in maintenance_requests]
        except TypeError:
            raise ValueError("Maintenance requests must be iterable")
        except ValueError:
            raise ValueError("Maintenance requests must have exactly 150 elements")
        self._update_block_occupancy()

    def update_occupancy(self, occupancy):
        self.actual_occupancy = occupancy[:150]
        self._update_block_occupancy()

    def _update_block_occupancy(self):
        self.block_occupancy = [
            actual or maint
            for actual, maint in zip(self.actual_occupancy, self.maintenance)
        ]

    def set_authorities(self, authorities):
        if any(a < 0 for a in authorities):
            raise ValueError("Authority values cannot be negative")
        self.block_authority = authorities[:150]

    def update_track_devices(self, switches, lights, crossings):
        self.switch_states = switches[:6]
        self.light_states = lights[:6]
        self.crossing_states = crossings[:2]

    def set_track_controller(self, track_controller):
        self.track_controller = track_controller