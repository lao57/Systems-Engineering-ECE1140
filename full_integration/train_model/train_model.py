import time
import numpy as np
from train_controller.train_controller import TrainController
from train_controller.train_controller_gui import TrainControllerGUI
from train_controller.testbench_gui import TestbenchGUI
from train_model.train_gui import Train_GUI
from train_controller.train_controller_gui_v2 import TrainControllerGUIv2

service_brake_deceleration = 1.2  # m/s^2
emergency_brake_deceleration = 2.73  # m/s^2
cabinLen = 32.2  # m
cabinHeight = 3.42  # m
cabinWidth = 2.65  # m
g = 9.8  # m/s^2
static_rolling_ressistance = 0.1  # m/s^2
max_speed = 19.444  # m/s
max_num_passengers = 73  # max number of people in the train - 1 driver and 1 conductor

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

# static dictionary for authority (NOT REALLY NEEDED ANYMORE)

"""
station_map = {
    "STATION; PIONEER": "0001",
    "STATION; EDGEBROOK": "0010",
    "STATION": "0011",
    "STATION; WHITED": "0100",
    "STATION; SOUTH BANK": "0101",
    "STATION; CENTRAL": "0110",
    "STATION; INGLEWOOD": "0111",
    "STATION; OVERBROOK": "1000",
    "STATION; GLENBURY": "1001",
    "STATION; DORMONT": "1010",
    "STATION; MT LEBANON": "1011",
    "STATION; POPLAR": "1100",
    "STATION; CASTLE SHANNON": "1101"
}


"""

station_naming = {
    '0001': "PIONEER",
    '0010': "EDGEBROOK",
    '0100': "WHITED",
    '0101': "SOUTH BANK",
    '0110': "CENTRAL",
    '0111': "INGLEWOOD",
    '1000': "OVERBROOK",
    '1001': "GLENBURY",
    '1010': "DORMONT",
    '1011': "MT LEBANON",
    '1100': "POPLAR",
    '1101': "CASTLE SHANNON",
    '0011': "STATION",
    '0000': "To be Announced",
    '1110': "EXTRA",
    '1111': "EXTRA" 
}


class TrainModel:
    """INITIALIZATION"""

    def __init__(self, k_p=1.5e5, k_i=1.5e4, train_number=1, numberOfPeople=3, start_block=64):

        # SPEED CALCULATION VARIABLES
        self.velocity = 0
        self.previous_velocity = 0
        self.acceleration = 0
        self.previous_acceleration = 0
        self.distance_travelled = 0
        self.distance_travelled_middle = -16.1
        self.distance_travelled_end = -32.2
        self.power = 0
        self.ebrake = False
        self.sbrake_decel = 0.0

        # failure modes
        self.failure_modes = [False, False, False]  # [train engine failure, signal pickup failure, brake failure]

        # TRAIN STATUS
        self.doors_status = [False, False]  # left door open, right door open
        self.lights_status = [False, False]  # interior light on, exterior light on
        self.cabin_temp = 70
        self.announcement = False
        self.stop_flag = False #flag to make sure at a given stop passenger transaction only happens once

        # TRAIN PHYSICAL VARIABLES
        self.numberOfCars = 5  # according to profetta this is constant
        self.numberOfPeople = numberOfPeople # starts at 2 for the driver and the conductor
        self.train_number = train_number
        self.mass = self.numberOfCars * 40900 + numberOfPeople * 70  # 40 tons per cart plus 70 kg per person
        self.weight_imperial = self.mass * 2.20462
        self.length = 32.3 * self.numberOfCars
        self.length_imperial = self.length * 3.2808399
        self.capacity = 75  # SET AS MAX VALUE

        # BEACON VARIABLES
        self.last_beacon = 0000
        self.authority = 0
        self.authority_wait = 0
        self.cmd_velocity = 14
        self.distance_vector = []  # holds the start of the trains current spot
        self.distance_vector_middle = [16.1]  # holds the middle of the trains current spot
        self.distance_vector_end = [32.2]  # holds the end of the trains current spot
        self.imperial_distance_vector = []
        self.speeds_vector = []  # holds initial speed until beacon where then those are pushed to the back of the vector
        self.underground_vector = []
        self.at_station_vector = []
        self.Next_station_names = []
        self.grade_vector = []
        self.blocknumbervector = []  # hold the next bunch of blocks given by the beacon stars on block one
        self.blocknumbervector_middle = [None]
        self.blocknumbervector_end = [None]
        self.START_BLOCK = start_block  # starting block number

        # TRAIN CONTROLLER VARIABLES (SAMARTH ADDED VARIABLES)
        self.k_p = k_p
        self.k_i = k_i
        self.dt = 1  # sampling time
        self.max_engine_power = 120e3  # 4 motors; each can supply up to max 120 kW
        self.sample_period = 1
        self.comfortable_temp = 70

        # GUI
        # self.train_controller_gui = TrainControllerGUI(self.k_p, self.k_i)
        self.train_controller_gui = TrainControllerGUIv2(self.k_p, self.k_i)
        self.train_controller_testbench = None  # TestbenchGUI()
        self.train_gui = Train_GUI(self)
        self.ebrake_gui_signal = False

        # OTHER MODULES
        self.Track_model = None  # holds the actual track information
        self.train_controller = TrainController(self.k_p, self.k_i, self.max_engine_power, self.sample_period,
                                                self.comfortable_temp, self.train_controller_gui,
                                                self.train_controller_testbench)
        self.train_controller_gui.show()
        self.train_gui.show()
        # self.train_controller_testbench.show()

    def __del__(self):
        print("Train Model Deleted")
        self.train_controller_gui.close()
        self.train_gui.close()
        # self.train_controller_testbench.close()

    def display_train(self):
        print("--------------------------TRAIN STATUS--------------------------")
        print("Authority: ", self.authority)
        print("velocity: ", self.velocity)
        print("Acceleration: ", self.acceleration)
        print("Previous Acceleration: ", self.previous_acceleration)
        print("Begining block: ", self.blocknumbervector[0])
        print("Middle block: ", self.blocknumbervector_middle[0])
        print("End block: ", self.blocknumbervector_end[0])
        print("SL: ", self.speeds_vector[0], " Dis: ", self.distance_vector[0], " UG: ", self.underground_vector[0],
              " AS: ", self.at_station_vector[0], " SN: ", self.Next_station_names[0])
        print("Distance Vector:", self.distance_vector)
        print("Speeds Vector:", self.speeds_vector)
        print("Underground Vector:", self.underground_vector)
        print("At Station Vector:", self.at_station_vector)
        print("Next station vames:", self.Next_station_names)
        print("Grade Vector:", self.grade_vector)
        print("Block Number Vector:", self.blocknumbervector)
        print("Power: ", self.power)

    def add_classes(self, Track_model):
        self.Track_model = Track_model

    """SIGNAL FUNCTIONS"""

    def pickup_beacon_signal(self):
        #print("block number than beacon signal")

        if self.blocknumbervector:
            beacon_signal = self.Track_model.get_beacon_from_block(self.blocknumbervector[0])
        else:
            beacon_signal = self.Track_model.get_beacon_from_block(64)
        if beacon_signal[0:4] != self.last_beacon and beacon_signal[0:4] != 0000 and beacon_signal[0:4] != None:
            if self.blocknumbervector:
                grade_vector_holder = self.Track_model.get_grade_from_block(self.blocknumbervector[0])
                if grade_vector_holder and isinstance(grade_vector_holder, (list, str)):
                    try:
                        # Join the elements if it's a list, split by spaces, and convert to integers
                        # grade_vector_holder_parsed = [int(num) for num in ''.join(grade_vector_holder).split()]
                        grade_vector_holder_parsed = [float(num) for num in grade_vector_holder.split()]
                        parse_blocknumbervector = self.Track_model.get_block_vector_from_block(self.blocknumbervector[0])
                        blocknumbervector_holder = [int(num) for num in ''.join(parse_blocknumbervector).split()]
                        self.beacon_parse(beacon_signal, grade_vector_holder_parsed, blocknumbervector_holder)
                    except ValueError as e:
                        #print(f"Error parsing grade_vector_holder: {grade_vector_holder}. Error: {e}")
                        grade_vector_holder_parsed = []  # Default to an empty list if parsing fails
                else:
                    #print(f"Invalid grade_vector_holder: {grade_vector_holder}")
                    grade_vector_holder_parsed = []  # Default to an empty list if input is invalid
                """
                if grade_vector_holder != "nan":
                    print(f"grade vector holder: {grade_vector_holder}")
                    grade_vector_holder_parsed = [int(num) for num in ''.join(grade_vector_holder).split()]
                    parse_blocknumbervector = self.Track_model.get_block_vector_from_block(
                        self.blocknumbervector[0])  # there will be some function from the track
                    blocknumbervector_holder = [int(num) for num in ''.join(parse_blocknumbervector).split()]
                    self.beacon_parse(beacon_signal, grade_vector_holder_parsed, blocknumbervector_holder)
                    """
            else:
                # grade_vector_holder = self.Track_model.get_grade_from_block(62)
                grade_vector_holder = self.Track_model.get_grade_from_block(64)
                if grade_vector_holder != "nan":
                    #print(f"grade vector holder: {grade_vector_holder}")
                    # grade_vector_holder_parsed = [int(num) for num in ''.join(grade_vector_holder).split()]
                    grade_vector_holder_parsed = [float(num) for num in grade_vector_holder.split()]
                    # grade_vector_holder_parsed = [float(num) for num in grade_vector_holder.split()]
                    # grade_vector_holder_parsed = [int(float(num)) for num in grade_vector_holder.split(', ')]
                    # parse_blocknumbervector = self.Track_model.get_block_vector_from_block(62)
                    parse_blocknumbervector = self.Track_model.get_block_vector_from_block(64)
                    blocknumbervector_holder = [int(num) for num in ''.join(parse_blocknumbervector).split()]
                    self.beacon_parse(beacon_signal, grade_vector_holder_parsed, blocknumbervector_holder)
            """
            the idea here is that I will be pinging the block that I am currently on
            then I make sure that I have not already read this beacon if I have not
            then I parse it plus the grade and block number vector
            """
        pass

    def beacon_parse(self, beaconvector, gradevector_REALSIM, blocknumbervector_REALSIM):
        n = len(beaconvector)
        self.last_beacon = beaconvector[0:4]
        if beaconvector[0] != None:
            number_of_blocks = (n - 4) / 19
            num_blocks = int(number_of_blocks)
            self.grade_vector.extend(gradevector_REALSIM)  # adds the grade to the grade vector
            self.blocknumbervector.extend(blocknumbervector_REALSIM)  # adds the block number to the block number vector
            self.blocknumbervector_middle.extend(blocknumbervector_REALSIM)
            self.blocknumbervector_end.extend(blocknumbervector_REALSIM)
            for i in range(0, num_blocks):  # adds all block distances to the distance vector
                number_str = beaconvector[4 + 10 * i:14 + 10 * i]
                number = number_str[0:(len(number_str) - 1)]  # equals the first 9
                distance_value = int(number, 2) + 0.6 * float(number_str[
                                                                  len(number_str) - 1])  # adds the first 9 bits to 0.6 times the last bit to account for one block that is 86.6 meters
                self.distance_vector.append(distance_value)
                self.distance_vector_middle.append(distance_value)
                self.distance_vector_end.append(distance_value)
                self.imperial_distance_vector.append(distance_value * 3.2808399)  # converts meters to feet

                speed_str = beaconvector[4 + num_blocks * 10 + 3 * i:7 + num_blocks * 10 + 3 * i]
                speed_limit = binary_to_value[speed_str]
                self.speeds_vector.append(speed_limit)

                self.underground_vector.append(beaconvector[4 + num_blocks * 13 + i])
                self.at_station_vector.append(beaconvector[4 + num_blocks * 14 + i])
                self.Next_station_names.append(
                    beaconvector[4 + num_blocks * 15 + 4 * i:4 + num_blocks * 15 + 4 * (i + 1)])
                
            self.display_train()

    def baud_read(self):
        """ Print the values to debug
        print(f"baud_signal[0:4]: '{baud_signal[0:4]}' (type: {type(baud_signal[0:4])})")
        print(f"self.Baud_ID: '{self.Baud_ID}' (type: {type(self.Baud_ID)})")"""
        #print(self.blocknumbervector[0])
        if self.blocknumbervector:
            self.authority = self.Track_model.get_block_authority(int(self.blocknumbervector[0]))
            """ USED TO CHEAT FOR SINGLE STOPS ON ITERATION 3
            if self.authority == 0:
                self.authority_wait += 1
                if self.authority_wait > 300:
                    self.authority = 100
                    self.next_station_names[0] = "Yard"
            
            """
        else:
            self.authority = self.Track_model.get_block_authority(self.START_BLOCK)#starting block
        # baud_signal.append(0)  | Potentail add if we are not getting enough range

    """UPDATING FUNCTIONS"""

    def iterate(self, world_time):
        """
        :param world_time: world time dict: {'day', 'hour', 'min'}
        """
        # TODO: parse underground_vector, at_station_vector
        ebrake, sbrake_decel, cmd_power, modified_cabin_temp, open_doors, open_lights, announcement = \
            self.train_controller.iterate(self.speeds_vector[0], self.authority, self.velocity, self.failure_modes,
                                          self.underground_vector, self.cabin_temp, self.doors_status,
                                          self.lights_status, self.at_station_vector, world_time)

        self.power = cmd_power
        self.ebrake = ebrake
        self.sbrake_decel = sbrake_decel
        self.cabin_temp = self.cabin_temp
        self.doors_status = open_doors
        self.lights_status = open_lights
        self.announcement = announcement  # TODO: Change bool to string val

        self.update_train()

        # update gui
        self.update_gui(world_time)

    def update_train(self, world_time, delta_t=1):
        if self.Track_model.ready == False:
            return
        # read from the track model
        self.pickup_beacon_signal()
        if not self.failure_modes[1]:
            self.baud_read()

        # Update train controller mode (interaction from train driver)
        self.train_controller.train_controller_mode = self.train_controller_gui.train_controller_mode

        if self.train_controller.train_controller_mode == 'Manual':
            self.cmd_velocity = self.train_controller_gui.driver_speed
            self.train_controller.train_controller_mode = 'manual'
            # self.driver_inputs = {'ebrake': self.train_controller_gui.e_brake_on,
            #                       'sbrake': self.train_controller_gui.service_brake_decel}
            self.train_controller.e_brake_on = self.train_controller_gui.e_brake_on
            self.train_controller.service_brake_decel = self.train_controller_gui.service_brake_decel
            self.cabin_temp = self.train_controller_gui.cur_cabin_temp
            self.lights_status[0] = self.train_controller_gui.lights_status[0]
        else:
            self.train_controller.train_controller_mode = 'auto'

        # calling Train Controller function (also will need to be able to send at_station_vector[0] so that you can check if you are at a station if you are stopping)
        self.train_controller.iterate(self.acceleration, self.previous_acceleration,
                                      min(float(self.speeds_vector[0])*0.75, max_speed),
                                      self.authority, self.velocity, self.failure_modes, self.underground_vector[0],
                                      self.cabin_temp, self.doors_status, self.lights_status,
                                      self.Next_station_names[0], world_time, )
        # AFTER TRAIN CONTROLLER ITERATE -update the power, ebrake, sbrake_decel, and cabin_temp, etc
        self.power = self.train_controller.cmd_power
        self.ebrake = self.train_controller.e_brake_on
        self.sbrake_decel = self.train_controller.service_brake_decel
        self.cabin_temp = self.train_controller.set_cabin_temp
        self.doors_status = self.train_controller.doors_status
        self.lights_status = self.train_controller.lights_status
        self.announcement = self.train_controller.announce_station
        if self.ebrake == False:
            if self.ebrake_gui_signal == True:
                self.ebrake = True

        # handling announcments / stops
        if self.announcement:
            self.announcement_text = "Arriving at: " + self.Next_station_names[0]
            if self.stop_flag == False:
                self.numberOfPeople = self.Track_model.station_stop(self.blocknumbervector[0], self.numberOfPeople-2, max_num_passengers)
                self.numberOfPeople += 2  # add the driver and conductor back
                self.stop_flag = True
        else:
            self.announcement_text = "The Next station is: " + self.Next_station_names[0]
            self.stop_flag = False


        # Ensure self.grade_vector[0] is a valid number
        if self.grade_vector[0] is not None:
            try:
                grade_value = float(self.grade_vector[0])  # Convert to float
            except ValueError:
                print(f"Invalid grade value: {self.grade_vector[0]}")
        else:
            print(f"no grade vector 1")  # Default to 0 if grade_vector is empty or None

        # Calculate gravitational acceleration
        gravitational_acceleration = g * np.sin(np.arctan(grade_value / 100))

        """
        # Acceleration Calculation
        self.previous_acceleration = self.acceleration
        gravitational_acceleration = (g * np.sin(
            np.arctan(self.grade_vector[0] / 100)))  # negative when going down hill | positive when going up hill
        """

        """
        Three cases for acceleration calculation
        1. If the ebrake is on (cuts off engine power and applies emergency brake with normal rolling ressistance)
        2. If the train is at a stop and the ebrake is off (static rolling resistance plus work derived equation for power based acceleration to avoid divide by zero error)
        3. If the train is moving (non-static rolling resistance plus normal acceleration calculation)
        """
        if self.ebrake:
            self.acceleration = (
                        0 - self.sbrake_decel * service_brake_deceleration - self.ebrake * emergency_brake_deceleration - gravitational_acceleration - static_rolling_ressistance)
        else:
            if (self.velocity <= 0):  # see Ipad for notes on this derivation but avoids divide by zero error
                self.acceleration = ((not (self.failure_modes[0])) * np.sqrt(
                    (2 * self.power) / (self.mass)) - self.sbrake_decel * (not (self.failure_modes[
                    2])) * service_brake_deceleration - self.ebrake * emergency_brake_deceleration - gravitational_acceleration)
            else:  # normal acceleration calculation
                self.acceleration = ((not (self.failure_modes[0])) * self.power / (
                            self.mass * self.velocity) - self.sbrake_decel * (not (self.failure_modes[
                    2])) * service_brake_deceleration - self.ebrake * emergency_brake_deceleration - gravitational_acceleration)

        self.previous_velocity = self.velocity
        self.velocity += (1 / 2) * (self.acceleration + self.previous_acceleration) * delta_t
        if (self.velocity < 0):
            self.velocity = 0

        # distance handling
        distance_over_interval = (1 / 2) * (self.velocity + self.previous_velocity) * delta_t
        self.distance_travelled += distance_over_interval
        self.distance_travelled_middle += distance_over_interval
        self.distance_travelled_end += distance_over_interval
        self.distance_vector[0] -= distance_over_interval
        self.distance_vector_middle[0] -= distance_over_interval
        self.distance_vector_end[0] -= distance_over_interval
        self.imperial_distance_vector[0] -= distance_over_interval * 3.2808399
        self.authority -= distance_over_interval
        while self.distance_vector_end[0] < 0:
            if len(self.distance_vector) < 2:
                print("Train ID: ", self.train_number, " has reached the end of the line")
                return
            self.distance_vector_end[1] += self.distance_vector_end[0]
            self.distance_vector_end.pop(0)
            self.blocknumbervector_end.pop(0)
        while self.distance_vector_middle[0] < 0:
            self.distance_vector_middle[1] += self.distance_vector_middle[0]
            self.distance_vector_middle.pop(0)
            self.blocknumbervector_middle.pop(0)
        while self.distance_vector[0] < 0:
            self.distance_vector[1] += self.distance_vector[0]  # applying extra distance into the next block
            self.distance_vector.pop(0)
            self.imperial_distance_vector.pop(0)
            self.imperial_distance_vector[0] = self.distance_vector[0] * 3.2808399
            self.speeds_vector.pop(0)
            self.underground_vector.pop(0)
            self.at_station_vector.pop(0)
            self.Next_station_names.pop(0)
            self.grade_vector.pop(0)
            self.blocknumbervector.pop(0)
        # update time flag to move to the next second
        # update occupancy
        #self.Track_model.update_block_occupancy(self.blocknumbervector[0], self.blocknumbervector_middle[0], self.blocknumbervector_end[0])
        if self.blocknumbervector[0]:
            self.Track_model.occupancy_status[int(self.blocknumbervector[0]) - 1] = True
        if self.blocknumbervector_middle[0]:
            self.Track_model.occupancy_status[int(self.blocknumbervector_middle[0]) - 1] = True
        if self.blocknumbervector_end[0]:
            self.Track_model.occupancy_status[int(self.blocknumbervector_end[0]) - 1] = True
        #print(f"Train Model: Block occupancy updated blocks: {self.blocknumbervector[0]}, {self.blocknumbervector_middle[0]}, {self.blocknumbervector_end[0]}")
        # update gui
        self.update_gui(world_time)
        self.train_gui.update_train_model_GUI(delta_t)

    def update_train_no_signal_pickup(self, world_time, delta_t=1):
        if self.Track_model.ready == False:
            return
        # read from the track model
        self.pickup_beacon_signal()

        # Update train controller mode (interaction from train driver)
        self.train_controller.train_controller_mode = self.train_controller_gui.train_controller_mode

        if self.train_controller.train_controller_mode == 'Manual':
            self.cmd_velocity = self.train_controller_gui.driver_speed
            self.train_controller.train_controller_mode = 'manual'
            # self.driver_inputs = {'ebrake': self.train_controller_gui.e_brake_on,
            #                       'sbrake': self.train_controller_gui.service_brake_decel}
            self.train_controller.e_brake_on = self.train_controller_gui.e_brake_on
            self.train_controller.service_brake_decel = self.train_controller_gui.service_brake_decel
            self.cabin_temp = self.train_controller_gui.cur_cabin_temp
            self.lights_status[0] = self.train_controller_gui.lights_status[0]
        else:
            self.train_controller.train_controller_mode = 'auto'

        # calling Train Controller function (also will need to be able to send at_station_vector[0] so that you can check if you are at a station if you are stopping)
        self.train_controller.iterate(self.acceleration, self.previous_acceleration,
                                      min(float(self.speeds_vector[0])*0.75, max_speed),
                                      self.authority, self.velocity, self.failure_modes, self.underground_vector[0],
                                      self.cabin_temp, self.doors_status, self.lights_status,
                                      self.Next_station_names[0], world_time, )
        # AFTER TRAIN CONTROLLER ITERATE -update the power, ebrake, sbrake_decel, and cabin_temp, etc
        self.power = self.train_controller.cmd_power
        self.ebrake = self.train_controller.e_brake_on
        self.sbrake_decel = self.train_controller.service_brake_decel
        self.cabin_temp = self.train_controller.set_cabin_temp
        self.doors_status = self.train_controller.doors_status
        self.lights_status = self.train_controller.lights_status
        self.announcement = self.train_controller.announce_station
        if self.ebrake == False:
            if self.ebrake_gui_signal == True:
                self.ebrake = True

        # handling announcments / stops
        if self.announcement:
            self.announcement_text = "Arriving at: " + self.Next_station_names[0]
            if self.stop_flag == False:
                self.numberOfPeople = self.Track_model.station_stop(self.blocknumbervector[0], self.numberOfPeople-2, max_num_passengers)
                self.numberOfPeople += 2  # add the driver and conductor back
                self.stop_flag = True
        else:
            self.announcement_text = "The Next station is: " + self.Next_station_names[0]
            self.stop_flag = False


        # Ensure self.grade_vector[0] is a valid number
        if self.grade_vector[0] is not None:
            try:
                grade_value = float(self.grade_vector[0])  # Convert to float
            except ValueError:
                print(f"Invalid grade value: {self.grade_vector[0]}")
        else:
            print(f"no grade vector 1")  # Default to 0 if grade_vector is empty or None

        # Calculate gravitational acceleration
        gravitational_acceleration = g * np.sin(np.arctan(grade_value / 100))

        """
        # Acceleration Calculation
        self.previous_acceleration = self.acceleration
        gravitational_acceleration = (g * np.sin(
            np.arctan(self.grade_vector[0] / 100)))  # negative when going down hill | positive when going up hill
        """

        """
        Three cases for acceleration calculation
        1. If the ebrake is on (cuts off engine power and applies emergency brake with normal rolling ressistance)
        2. If the train is at a stop and the ebrake is off (static rolling resistance plus work derived equation for power based acceleration to avoid divide by zero error)
        3. If the train is moving (non-static rolling resistance plus normal acceleration calculation)
        """
        if self.ebrake:
            self.acceleration = (
                        0 - self.sbrake_decel * service_brake_deceleration - self.ebrake * emergency_brake_deceleration - gravitational_acceleration - static_rolling_ressistance)
        else:
            if (self.velocity <= 0):  # see Ipad for notes on this derivation but avoids divide by zero error
                self.acceleration = ((not (self.failure_modes[0])) * np.sqrt(
                    (2 * self.power) / (self.mass)) - self.sbrake_decel * (not (self.failure_modes[
                    2])) * service_brake_deceleration - self.ebrake * emergency_brake_deceleration - gravitational_acceleration)
            else:  # normal acceleration calculation
                self.acceleration = ((not (self.failure_modes[0])) * self.power / (
                            self.mass * self.velocity) - self.sbrake_decel * (not (self.failure_modes[
                    2])) * service_brake_deceleration - self.ebrake * emergency_brake_deceleration - gravitational_acceleration)

        self.previous_velocity = self.velocity
        self.velocity += (1 / 2) * (self.acceleration + self.previous_acceleration) * delta_t
        if (self.velocity < 0):
            self.velocity = 0

        # distance handling
        distance_over_interval = (1 / 2) * (self.velocity + self.previous_velocity) * delta_t
        self.distance_travelled += distance_over_interval
        self.distance_travelled_middle += distance_over_interval
        self.distance_travelled_end += distance_over_interval
        self.distance_vector[0] -= distance_over_interval
        self.distance_vector_middle[0] -= distance_over_interval
        self.distance_vector_end[0] -= distance_over_interval
        self.imperial_distance_vector[0] -= distance_over_interval * 3.2808399
        self.authority -= distance_over_interval
        while self.distance_vector_end[0] < 0:
            if len(self.distance_vector) < 2:
                print("Train ID: ", self.train_number, " has reached the end of the line")
                return
            self.distance_vector_end[1] += self.distance_vector_end[0]
            self.distance_vector_end.pop(0)
            self.blocknumbervector_end.pop(0)
        while self.distance_vector_middle[0] < 0:
            self.distance_vector_middle[1] += self.distance_vector_middle[0]
            self.distance_vector_middle.pop(0)
            self.blocknumbervector_middle.pop(0)
        while self.distance_vector[0] < 0:
            self.distance_vector[1] += self.distance_vector[0]  # applying extra distance into the next block
            self.distance_vector.pop(0)
            self.imperial_distance_vector.pop(0)
            self.imperial_distance_vector[0] = self.distance_vector[0] * 3.2808399
            self.speeds_vector.pop(0)
            self.underground_vector.pop(0)
            self.at_station_vector.pop(0)
            self.Next_station_names.pop(0)
            self.grade_vector.pop(0)
            self.blocknumbervector.pop(0)
        # update time flag to move to the next second
        # update occupancy
        #self.Track_model.update_block_occupancy(self.blocknumbervector[0], self.blocknumbervector_middle[0], self.blocknumbervector_end[0])
        if self.blocknumbervector[0]:
            self.Track_model.occupancy_status[int(self.blocknumbervector[0]) - 1] = True
        if self.blocknumbervector_middle[0]:
            self.Track_model.occupancy_status[int(self.blocknumbervector_middle[0]) - 1] = True
        if self.blocknumbervector_end[0]:
            self.Track_model.occupancy_status[int(self.blocknumbervector_end[0]) - 1] = True
        #print(f"Train Model: Block occupancy updated blocks: {self.blocknumbervector[0]}, {self.blocknumbervector_middle[0]}, {self.blocknumbervector_end[0]}")
        # update gui
        self.update_gui(world_time)
        self.train_gui.update_train_model_GUI(delta_t)

    """UI FUNCTIONS"""

    def get_user_inputs(self):
        """
        Get user inputs from UI
        """
        # Train controller testbench
        self.train_controller.get_user_inputs()

        # Train model testbench

    def update_gui(self, world_time):

        # Update train GUI

        # Update train controller GUI
        self.train_controller_gui.update_world_time(world_time)
        self.train_controller_gui.update_power_cmd(self.power)
        self.train_controller_gui.update_cur_speed(self.velocity)
        self.train_controller_gui.update_cmd_speed(self.cmd_velocity)
        self.train_controller_gui.update_sbrake_decel(self.sbrake_decel)
        self.train_controller_gui.update_ebrake(self.ebrake)
        self.train_controller_gui.update_cabin_temp(self.cabin_temp)
        self.train_controller_gui.update_doors_status(self.doors_status)
        self.train_controller_gui.update_lights_status(self.lights_status)
        # self.train_controller_gui.update_most_recent_station(self.station_to_be_reached)
        self.train_controller_gui.update_speed_limit(self.train_controller.speed_limit)
        self.train_controller_gui.update_authority(self.authority)
        self.train_controller_gui.update_failure_modes(self.failure_modes)
        # self.train_controller_gui.update_underground(self.underground)
