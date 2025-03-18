class CTC:
    def __init__(self):

        self.block_occupancy = [False] * 150  # 150 blocks on green
        self.switch_states = [False] * 6      # 6 switches
        self.light_states = [False] * 6       # 6 light
        self.crossing_states = [False] * 2    # 2 crossings
        self.block_authority = [False] * 150  # Authority values for each block
        self.maintenance = [False] * 150      # Maintenance status per block.
        self.track_controller = None          # To be set

    def connect_track_controller(self, track_controller):

        self.track_controller = track_controller

        if self.track_controller:
            self.block_occupancy = self.track_controller.get_block_occupancy().copy()
            self.switch_states = self.track_controller.get_switch_state().copy()
            self.light_states = self.track_controller.get_light_state().copy()
            self.crossing_states = self.track_controller.get_crossing_state().copy()

    def send_to_track_controller(self):

        if self.track_controller:
            self.track_controller.receive_authority(self.block_authority.copy())
            self.track_controller.receive_maintenance(self.maintenance.copy())

    def get_authority(self):
        #return copy of current block authority data
        return self.block_authority.copy()

    def get_maintenance(self):
        #return copy of current maintenance status
        return self.maintenance.copy()

    def get_occupancy(self):
        #return a copy of current block occupancy
        return self.block_occupancy.copy()
