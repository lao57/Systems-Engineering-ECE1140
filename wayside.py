class WAYSIDE:
    def __init__(self, switches, lights, crossings, stop_blocks ,logic_function, prev_switch_states, block_authorities):
        """
        Initialize the PLC for a specific section of the track.
        :param switches: List of switch indices controlled by this wayside.
        :param lights: List of light indices controlled by this wayside.
        :param crossings: List of crossing indices controlled by this wayside.
        :param logic_function: The logic function for this wayside controller.
        :param prev_switch_states: The previous states of the switches.
        :param block_authorities: The block authorities for the blocks controlled by this wayside.
        """
        self.switches = switches
        self.lights = lights
        self.crossings = crossings
        self.stop_blocks = stop_blocks
        self.logic_function = logic_function
        self.prev_switch_states = prev_switch_states
        self.block_authorities = block_authorities

    def update_wayside(self, block_occupancy, maintenance):
        """
        Execute the PLC logic to generate outputs.
        """
        return self.logic_function(
            block_occupancy,
            self.prev_switch_states,
            self.block_authorities,
            maintenance
        )
