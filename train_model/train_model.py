import time
import numpy as np
from train_controller.train_controller import TrainController

service_brake_deceleration = 1.2  # m/s^2
emergency_brake_deceleration = 2.73  # m/s^2
cabinLen = 32.2  # m
cabinHeight = 3.42  # m
cabinWidth = 2.65  # m
g = 9.8  # m/s^2
static_rolling_ressistance = 0.1 #m/s^2

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
        
        #SPEED CALCULATION VARIABLES
        self.velocity = 0
        self.previous_velocity = 0
        self.acceleration = 0
        self.previous_acceleration = 0
        self.distance_travelled = 0
        self.power = 0
        self.ebrake = False
        self.sbrake_decel = 0.0

        # failure modes
        self.failure_modes = [False, False, False]  # [train engine failure, signal pickup failure, brake failure]


        #TRAIN STATUS
        self.doors_status = [False, False]  # left door open, right door open
        self.lights_status = [False, False]  # interior light on, exterior light on
        self.cabin_temp = 70
        self.announcement = False
        self.announcement_text = ""

        #TRAIN PHYSICAL VARIABLES
        self.numberOfCars = 5  # according to profetta this is constant
        self.numberOfPassengers = numberOfPassengers  # starts at 2 for the driver and the conductor
        self.train_number = train_number
        self.mass = self.numberOfCars * 40900 + numberOfPassengers * 70  # 40 tons per cart plus 70 kg per person
        self.mass_imperial = self.mass * 2.20462
        self.length = 32.3 * self.numberOfCars
        self.length_imperial = self.length * 3.2808399
        self.capacity = 75  # SET AS MAX VALUE



        #BEACON VARIABLES
        self.last_beacon = 0000
        self.authority = 0
        self.distance_vector = []
        self.imperial_distance_vector = []
        self.speeds_vector = []  # holds initial speed until beacon where then those are pushed to the back of the vector
        self.underground_vector = []
        self.at_station_vector = []
        self.Next_station_names = []
        self.grade_vector = [] 
        self.blocknumbervector = [] #hold the next bunch of blocks given by the beacon stars on block one

        #TRAIN CONTROLLER VARIABLES (SAMARTH ADDED VARIABLES)
        self.k_p = k_p
        self.k_i = k_i
        self.dt = 1  # sampling time
        self.max_engine_power = 1000
        self.sample_period = 1
        self.comfortable_temp = 70
        #POTENTIALLY UNESSARY VARIABLES
        self.cmd_velocity = 0

        # GUI
        self.train_controller_gui = train_controller_gui
        self.train_controller_testbench = train_controller_testbench

        #OTHER MODULES
        self.Track_model = None #holds the actual track information
        self.train_controller = TrainController(self.k_p, self.k_i, self.max_engine_power, self.sample_period,
                                                self.comfortable_temp, train_controller_gui,
                                                train_controller_testbench)


    def display_train(self):
        print("--------------------------TRAIN STATUS--------------------------")
        print("Authority: ", self.authority)
        print("velocity: ", self.velocity)
        print("Acceleration: ", self.acceleration)
        print("SL: ", self.speeds_vector[0]," Dis: ", self.distance_vector[0], " UG: ",self.underground_vector[0], " AS: ", self.at_station_vector[0]," SN: ", self.Next_station_names[0])
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


    def beacon_parse(self, beaconvector, gradevector_REALSIM, blocknumbervector_REALSIM):
        n = len(beaconvector)
        self.last_beacon = beaconvector[0:4]
        if beaconvector[0] != None:
            number_of_blocks = (n - 4) / 19
            num_blocks = int(number_of_blocks)
            self.grade_vector.extend(gradevector_REALSIM)  # adds the grade to the grade vector
            self.blocknumbervector.extend(blocknumbervector_REALSIM)  # adds the block number to the block number vector
            for i in range(0, num_blocks):  # adds all block distances to the distance vector
                number_str = beaconvector[4 + 10 * i:14 + 10 * i]
                number = number_str[0:(len(number_str) - 1)]  # equals the first 9
                distance_value = int(number, 2) + 0.6 * float(number_str[len(number_str) - 1])  # adds the first 9 bits to 0.6 times the last bit to account for one block that is 86.6 meters
                self.distance_vector.append(distance_value)
                self.imperial_distance_vector.append(distance_value * 3.2808399)  # converts meters to feet

                speed_str = beaconvector[4 + num_blocks * 10 + 3 * i:7 + num_blocks * 10 + 3 * i]
                speed_limit = binary_to_value[speed_str]
                self.speeds_vector.append(speed_limit)

                self.underground_vector.append(beaconvector[4 + num_blocks * 13 + i])
                self.at_station_vector.append(beaconvector[4 + num_blocks * 14 + i])
                self.Next_station_names.append(beaconvector[4 + num_blocks * 15 + 4 * i:4 + num_blocks * 15 + 4 * (i + 1)])


    def baud_read(self):
        """ Print the values to debug
        print(f"baud_signal[0:4]: '{baud_signal[0:4]}' (type: {type(baud_signal[0:4])})")
        print(f"self.Baud_ID: '{self.Baud_ID}' (type: {type(self.Baud_ID)})")"""
        if self.blocknumbervector:
            baud_signal = self.Track_model.get_baud_sig(self.blocknumbervector[0])
        else:
            baud_signal = self.Track_model.get_baud_sig(1)
        #baud_signal.append(0)  | Potentail add if we are not getting enough range
        if baud_signal is not None:
            self.authority = int(baud_signal,2)
    

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


    def update_train(self, world_time):
        
        #read from the track model
        self.pickup_beacon_signal()
        if not self.failure_modes[1]:
            self.baud_read()

        #Should be replaced by iterate() in train model
        
        #calling Train Controller function (also will need to be able to send at_station_vector[0] so that you can check if you are at a station if you are stopping)
        self.train_controller.iterate(self.speeds_vector[0], self.authority, self.velocity, self.failure_modes, self.underground_vector[0], self.cabin_temp, self.doors_status, self.lights_status, self.Next_station_names[0],world_time)
        #AFTER TRAIN CONTROLLER ITERATE -update the power, ebrake, sbrake_decel, and cabin_temp, etc
        self.power = self.train_controller.cmd_power
        self.ebrake = self.train_controller.e_brake_on
        self.sbrake_decel = self.train_controller.service_brake_decel
        self.cabin_temp = self.train_controller.set_cabin_temp
        self.doors_status = self.train_controller.doors_status
        self.lights_status = self.train_controller.lights_status
        self.announcement = self.train_controller.announce_station

        #handling announcments
        if self.announcement:
            self.announcement_text = "Arriving at: " + self.Next_station_names[0]
        else:
            self.announcement_text = "The Next station is: " + self.Next_station_names[0]

        #Acceleration Calculation
        self.previous_acceleration = self.acceleration
        gravitational_acceleration = (g * np.sin(np.arctan(self.grade_vector[0]/100))) #negative when going down hill | positive when going up hill

        """
        Three cases for acceleration calculation
        1. If the ebrake is on (cuts off engine power and applies emergency brake with normal rolling ressistance)
        2. If the train is at a stop and the ebrake is off (static rolling resistance plus work derived equation for power based acceleration to avoid divide by zero error)
        3. If the train is moving (non-static rolling resistance plus normal acceleration calculation)
        """
        if self.ebrake:
            self.acceleration = (0 - self.sbrake_decel*service_brake_deceleration - self.ebrake*emergency_brake_deceleration - gravitational_acceleration - static_rolling_ressistance)
        else:
            if(self.velocity <= 0):#see Ipad for notes on this derivation but avoids divide by zero error
                self.acceleration =((not(self.failure_modes[0]))*np.sqrt((2*self.power)/(self.mass))-self.sbrake_decel*(not(self.failure_modes[2]))*service_brake_deceleration - self.ebrake*emergency_brake_deceleration - gravitational_acceleration)
            else:#normal acceleration calculation
                self.acceleration = ((not(self.failure_modes[0]))*self.power/(self.mass*self.velocity) - self.sbrake_decel*(not(self.failure_modes[2]))*service_brake_deceleration - self.ebrake*emergency_brake_deceleration - gravitational_acceleration)
        
        velocity_holder = self.velocity
        self.velocity = self.previous_velocity + (1/2)*(self.acceleration + self.previous_acceleration)
        if(self.velocity < 0):
            self.velocity = 0
        self.previous_velocity = velocity_holder
        distance_over_interval = (1/2)*(self.velocity + self.previous_velocity)#one second times the average velocity
        self.distance_travelled += distance_over_interval
        self.distance_vector[0] -= distance_over_interval
        self.imperial_distance_vector[0] -= distance_over_interval * 3.2808399
        self.authority -= distance_over_interval
        while self.distance_vector[0] < 0:
            self.distance_vector[1] += self.distance_vector[0] #applying extra distance into the next block
            self.distance_vector.pop(0)
            self.imperial_distance_vector.pop(0)
            self.imperial_distance_vector[0] = self.distance_vector[0] * 3.2808399
            self.speeds_vector.pop(0)
            self.underground_vector.pop(0)
            self.at_station_vector.pop(0)
            self.Next_station_names.pop(0)
            self.grade_vector.pop(0)
            self.blocknumbervector.pop(0)
        #update time flag to move to the next second

        # update gui
        self.update_gui(world_time)

        """ Original Integration Train model code
        #update time flag to move to the next second
        # Failure modes: [train engine failure, signal pickup failure, brake failure]
        # TODO: Add gravitational accel back
        # gravitational_acceleration = (g * np.sin(np.arctan(self.grade_vector[0] / 100)))
        gravitational_acceleration = 0
        rolling_resistance = 1000 * 4  # Constant rolling resistance (N)
        # Calculate force: F = P / v (if v > 0 to avoid divide by zero)
        if self.velocity > 0:
            # works unless train engine failure
            force = self.power / self.velocity * (not self.failure_modes[0])
        else:
            force = self.power / 1
        # Apply rolling resistance
        force = force - rolling_resistance
        # Calculate acceleration: a = F / m - (brake decel)
        acceleration = force / self.mass - (emergency_brake_deceleration * self.ebrake + self.sbrake_decel +
                                            gravitational_acceleration)
        # Update speed: v = u + at
        self.velocity += acceleration * self.dt

        if not self.failure_modes[1]:
            self.pickup_beacon_signal()
            self.baud_read()

        return max(self.velocity, 0)
    """

    def pickup_beacon_signal(self):
        if self.blocknumbervector:
            beacon_signal = self.Track_model.get_beacon_from_block(self.blocknumbervector[0])
        else:
            beacon_signal = self.Track_model.get_beacon_from_block(1)
        if beacon_signal[0:4] != self.last_beacon and beacon_signal[0:4] != 0000:
            if self.blocknumbervector:
                grade_vector_holder = self.Track_model.get_grade_from_block(self.blocknumbervector[0])
                blocknumbervector_holder = self.Track_model.get_block_vector_from_block(self.blocknumbervector[0])#there will be some function from the track
            else:
                grade_vector_holder = self.Track_model.get_grade_from_block(1)
                blocknumbervector_holder = self.Track_model.get_block_vector_from_block(1)
            self.beacon_parse(beacon_signal, grade_vector_holder, blocknumbervector_holder)
            """
            the idea here is that I will be pinging the block that I am currently on
            then I make sure that I have not already read this beacon if I have not
            then I parse it plus the grade and block number vector
            """
        

        
        # TODO: Add beacon signal pickup back
        # while self.distance_vector[0] < 0:
        #     self.distance_vector[1] += self.distance_vector[0]  # applying extra distance into the next block
        #     self.distance_vector.pop(0)
        #     self.imperial_distance_vector.pop(0)
        #     self.imperial_distance_vector[0] = self.distance_vector[0] * 3.2808399
        #     self.speeds_vector.pop(0)
        #     self.underground_vector.pop(0)
        #     self.at_station_vector.pop(0)
        #     self.extra_bit_vector.pop(0)
        #     self.grade_vector.pop(0)
        #     self.blocknumbervector.pop(0)
        """change name of baud stuff
        udate baud pickup
        add gravitational acceleration
        """
        pass


    def get_user_inputs(self):
        """
        Get user inputs from UI
        """
        # Train controller testbench
        self.train_controller.get_user_inputs()

        # Train model testbench


    def update_gui(self, world_time):
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
