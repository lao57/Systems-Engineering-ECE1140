class WAYSIDE:
    def __init__(self, start_block, end_block, num_switches, num_lights, num_crossings, logic_function):
        """
        Initialize the PLC for a specific section of the track.
        :param start_block: First block in the section.
        :param end_block: Last block in the section.
        :param num_switches: Number of switches in the section.
        :param num_lights: Number of lights in the section.
        :param num_crossings: Number of crossings in the section.
        :param logic_function: The logic function for this wayside controller.
        """
        self.start_block = start_block
        self.end_block = end_block
        self.num_switches = num_switches
        self.num_lights = num_lights
        self.num_crossings = num_crossings
        self.logic_function = logic_function

    def update_plc_logic(self, block_occupancy, errors, maintenance):
        """
        Execute the PLC logic to generate outputs.
        """
        return self.logic_function(
            block_occupancy,
            self.num_switches,
            self.num_lights,
            self.num_crossings
        )

    def update_plc_logic2(self, block_occupancy, errors, maintenance):
        """
        Execute the PLC logic to generate outputs.
        """
        return self.logic_function(
            block_occupancy,
            self.num_switches,
            self.num_lights,
            self.num_crossings
        )