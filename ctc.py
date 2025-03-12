class CTC:

    def __init__(self):
        self.block_authority = [0] * 150
        self.maintenance = [False] * 150
        self.block_occupancy = [False] * 150
        self.switch_states = [False] * 6
        self.light_states = [False] * 6
        self.crossing_states = [False] * 2
        self.track_controller = None

    def connect_track_controller(self, track_controller):
        self.track_controller = track_controller

    def update_states(self):
        if self.track_controller:
            self.switch_states = self.track_controller.switch_states
            self.light_states = self.track_controller.light_states
            self.crossing_states = self.track_controller.crossing_states
            self.block_occupancy = self.track_controller.block_occupancy

    def get_switch_state(self):
        return self.switch_states

    def get_light_state(self):
        return self.light_states

    def get_crossing_state(self):
        return self.crossing_states

    def get_maintenance_status(self):
        return self.maintenance

    def get_block_authority(self):
        return self.block_authority
