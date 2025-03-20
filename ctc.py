class CTC:
    def __init__(self):
        # Read-only from Track Controller
        self.block_occupancy = [False]*150
        self.switch_states = [False]*6
        self.light_states = [False]*6
        self.crossing_states = [False]*2


        self.block_authority = [[False]*10 for _ in range(150)] #each block represented as 10 bit bool array
        self.maintenance = [False]*150
        self.track_controller = None

    def connect_track_controller(self, track_controller):

        self.track_controller = track_controller #connect track controller
        if self.track_controller:

            #updates CTC with block occ & switch/light/crossing states
            self.block_occupancy = self.track_controller.get_block_occupancy().copy()
            self.switch_states = self.track_controller.get_switch_state().copy()
            self.light_states = self.track_controller.get_light_state().copy()
            self.crossing_states = self.track_controller.get_crossing_state().copy()

    def send_to_track_controller(self):


        if self.track_controller:

            #sends block auth & maintenance to Track Controller
            self.track_controller.receive_authority(self.block_authority.copy())
            self.track_controller.receive_maintenance(self.maintenance.copy())


    #copies of block auth., maint, and block occ. for safe reading
    def get_block_authority(self):
        return self.block_authority.copy()

    def get_maintenance_status(self):
        return self.maintenance.copy()

    def get_block_occupancy(self):
        return self.block_occupancy.copy()