import time
import numpy as np
from train_controller.train_controller import TrainController

service_brake_deceleration = 1.2  # m/s^2
emergency_brake_deceleration = 2.73  # m/s^2
cabinLen = 32.2  # m
cabinHeight = 3.42  # m
cabinWidth = 2.65  # m
g = 9.8  # m/s^2

# Static dictionary to convert three-bit binary numbers to specific values
binary_to_value = {
    '000': 0,
    '001': 15,
    '010': 20,
    '011': 25,
    '100': 30,
    '101': 40,
    '110': 55,
    '111': 70
}

# static dictionary for authority
authority_decoder = {
    '0000': 0,
    '0001': 65,
    '0010': 130,
    '0011': 195,
    '0100': 260,
    '0101': 325,
    '0110': 390,
    '0111': 455,
    '1000': 520,
    '1001': 585,
    '1010': 650,
    '1011': 715,
    '1100': 780,
    '1101': 845,
    '1110': 910,
    '1111': 3000  # big number
}


class TrainModel:
    def __init__(self, k_p, k_i, train_controller_gui, train_controller_testbench, train_number=1,
                 numberOfPassengers=2):
        self.Baud_ID = 0
        self.train_number = train_number

        self.cmd_velocity = 0
        self.velocity = 0
        self.previous_velocity = 0
        self.acceleration = 0
        self.previous_acceleration = 0
        self.distance_travelled = 0
        self.authority = 0

        self.power = 0
        self.ebrake_signal = 0
        self.brake_signal = 0

        # failure modes
        self.signal_pickup = True
        self.brake_status = True
        self.engine_status = True
        self.failure_modes = [False, False, False]  # [train engine failure, signal pickup failure, brake failure]

        self.capacity = 75  # SET AS MAX VALUE
        self.numberOfCarts = 5  # according to profetta this is constant
        self.numberOfPassengers = numberOfPassengers  # starts at 2 for the driver and the conductor

        self.doors_status = [False, False]  # left door open, right door open
        self.lights_status = [False, False]  # interior light on, exterior light on
        self.cabin_temp = 70
        self.weight = self.numberOfCarts * 40000 + numberOfPassengers * 70  # 40 tons per cart plus 70 kg per person
        self.weight_imperial = self.weight * 2.20462
        self.length = 32.3 * self.numberOfCarts
        self.length_imperial = self.length * 3.2808399

        self.distance_vector = []
        self.imperial_distance_vector = []
        self.speeds_vector = []  # holds initial speed until beacon where then those are pushed to the back of the vector
        self.underground_vector = []
        self.at_station_vector = []
        self.extra_bit_vector = []
        self.grade_vector = []
        self.blocknumbervector = []

        self.k_p = k_p
        self.k_i = k_i
        self.max_engine_power = 1000
        self.sample_period = 1
        self.comfortable_temp = 70

        # GUI
        self.train_controller_gui = train_controller_gui
        self.train_controller_testbench = train_controller_testbench

        self.train_controller = TrainController(self.k_p, self.k_i, self.max_engine_power, self.sample_period,
                                                self.comfortable_temp, train_controller_gui,
                                                train_controller_testbench)

    def display_train(self):
        print("Distance Vector:", self.distance_vector)
        print("Speeds Vector:", self.speeds_vector)
        print("Underground Vector:", self.underground_vector)
        print("At Station Vector:", self.at_station_vector)
        print("Extra Bit Vector:", self.extra_bit_vector)

    def beacon_parse(self, beaconvector, gradevector_REALSIM, blocknumbervector_REALSIM):
        n = len(beaconvector)
        self.Baud_ID = beaconvector[0:4]  # takes the first for values and sets to ID
        number_of_blocks = (n - 4) / 19
        num_blocks = int(number_of_blocks)
        self.grade_vector.extend(gradevector_REALSIM)  # adds the grade to the grade vector
        self.blocknumbervector.extend(blocknumbervector_REALSIM)  # adds the block number to the block number vector
        for i in range(0, num_blocks):  # adds all block distances to the distance vector
            number_str = beaconvector[4 + 10 * i:14 + 10 * i]
            number = number_str[0:(len(number_str) - 1)]  # equals the first 9
            distance_value = int(number, 2) + 0.6 * float(number_str[
                                                              len(number_str) - 1])  # adds the first 9 bits to 0.6 times the last bit to account for one block that is 86.6 meters
            self.distance_vector.append(distance_value)
            self.imperial_distance_vector.append(distance_value * 3.2808399)  # converts meters to feet

            speed_str = beaconvector[4 + num_blocks * 10 + 3 * i:7 + num_blocks * 10 + 3 * i]
            speed_limit = binary_to_value[speed_str]
            self.speeds_vector.append(speed_limit)

            self.underground_vector.append(beaconvector[4 + num_blocks * 13 + i])
            self.at_station_vector.append(beaconvector[4 + num_blocks * 14 + i])
            self.extra_bit_vector.append(beaconvector[4 + num_blocks * 15 + 4 * i:4 + num_blocks * 15 + 4 * (i + 1)])

    def baud_read(self, baud_signal):
        """ Print the values to debug
        print(f"baud_signal[0:4]: '{baud_signal[0:4]}' (type: {type(baud_signal[0:4])})")
        print(f"self.Baud_ID: '{self.Baud_ID}' (type: {type(self.Baud_ID)})")"""

        if baud_signal[0:4] == self.Baud_ID:
            self.authority = authority_decoder[baud_signal[-4:]]

    def iterate(self, world_time):
        """
        :param world_time: world time dict: {'day', 'hour', 'min'}
        :return:
        """
        failure_modes = [not self.engine_status, not self.signal_pickup, not self.ebrake_signal]
        print("about to enter train controller iter")
        # TODO: parse underground_vector, at_station_vector
        ebrake, sbrake_decel, cmd_power, modified_cabin_temp, open_doors, open_lights, announcement = \
            self.train_controller.iterate(self.cmd_velocity, self.authority, self.velocity, failure_modes,
                                          self.underground_vector, self.cabin_temp, self.doors_status,
                                          self.lights_status, self.at_station_vector, world_time)
        print("fin train controller iter")

        print("entering update train model")
        self.update_train(cmd_power)
        print("fin update train model")

        # update gui

    # this function is used to update the speed acceleration and distance travelled of the train over a one second interval
    def update_train(self, power):  # power in watts, grade in percentage
        power = power * 1000  # converts kW to Watts
        gravitational_acceleration = (g * np.sin(np.arctan(self.grade_vector[0] / 100)))
        self.previous_acceleration = self.acceleration
        if self.ebrake_signal:
            self.acceleration = (
                    0 - self.brake_signal * service_brake_deceleration - self.ebrake_signal * emergency_brake_deceleration - gravitational_acceleration)
        else:
            # if self.velocity <= 0:  # see Ipad for notes on this derivation but avoids divide by zero error
            #     self.acceleration = (self.engine_status * np.sqrt((2 * power) / (
            #         self.weight)) - self.brake_status * self.brake_signal * service_brake_deceleration - self.ebrake_signal * emergency_brake_deceleration - gravitational_acceleration)
            # else:  # normal acceleration calculation
            self.acceleration = (self.engine_status * power / (self.weight * self.velocity + 1e-12) -
                                 self.brake_status * self.brake_signal *
                                 service_brake_deceleration - self.ebrake_signal *
                                 emergency_brake_deceleration - gravitational_acceleration)

        # calculate authority
        velocity_holder = self.velocity
        self.velocity = self.previous_velocity + (1 / 2) * (self.acceleration + self.previous_acceleration)
        if self.velocity < 0:
            self.velocity = 0
        self.previous_velocity = velocity_holder
        distance_over_interval = (1 / 2) * (
                self.velocity + self.previous_velocity)  # one second times the average velocity
        self.distance_travelled += distance_over_interval
        self.distance_vector[0] -= distance_over_interval
        self.imperial_distance_vector[0] -= distance_over_interval * 3.2808399
        self.authority -= distance_over_interval

        print("computing dist vec")
        while self.distance_vector[0] < 0:
            self.distance_vector[1] += self.distance_vector[0]  # applying extra distance into the next block
            self.distance_vector.pop(0)
            self.imperial_distance_vector.pop(0)
            self.imperial_distance_vector[0] = self.distance_vector[0] * 3.2808399
            self.speeds_vector.pop(0)
            self.underground_vector.pop(0)
            self.at_station_vector.pop(0)
            self.extra_bit_vector.pop(0)
            self.grade_vector.pop(0)
            self.blocknumbervector.pop(0)
        # update time flag to move to the next second

    def get_user_inputs(self):
        """
        Get user inputs from UI
        """
        # Train controller testbench
        self.train_controller.get_user_inputs()

        # Train model testbench

