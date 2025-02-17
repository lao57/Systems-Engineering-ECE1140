import time
import numpy as np
service_brake_deceleration = 1.2 #m/s^2
emergency_brake_deceleration = 2.73 #m/s^2
cabinLen = 32.2 #m
cabinHeight = 3.42 #m
cabinWidth = 2.65 #m
g = 9.8 #m/s^2
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

#static dictionary for authority
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
    '1111': 3000 #big number
}

from enum import Enum

class Train:
    def __init__(self, train_number = 1, numberOfPassengers = 2):
        self.Baud_ID = 0
        self.train_number = train_number

        self.velocity = 0
        self.previous_velocity = 0
        self.acceleration = 0
        self.previous_acceleration = 0
        self.distance_travelled = 0
        self.authority = 0

        self.power = 0
        self.ebrake_signal = 0
        self.brake_signal = 0

        self.capacity = 75 #SET AS MAX VALUE
        self.numberOfCarts = 1 #according to profetta this is constant
        self.numberOfPassengers = numberOfPassengers #starts at 2 for the driver and the conductor

        self.left_door = False
        self.right_door = False
        self.exterior_light = False
        self.interior_light = False
        self.weight = self.numberOfCarts * 40000 + numberOfPassengers * 70 #40 tons per cart plus 70 kg per person

        self.distance_vector = []
        self.speeds_vector = [] #holds initial speed until beacon where then those are pushed to the back of the vector
        self.underground_vector = []
        self.at_station_vector = []
        self.extra_bit_vector = []
        
    def display_train(self):
        print("Distance Vector:", self.distance_vector)
        print("Speeds Vector:", self.speeds_vector)
        print("Underground Vector:", self.underground_vector)
        print("At Station Vector:", self.at_station_vector)
        print("Extra Bit Vector:", self.extra_bit_vector)

    def beacon_parse(self, beaconvector):
        n = len(beaconvector)
        self.Baud_ID = beaconvector[0:4] #takes the first for values and sets to ID
        number_of_blocks = (n - 4)/16
        num_blocks = int(number_of_blocks)
        for i in range(0, num_blocks):#adds all block distances to the distance vector
            number_str = beaconvector[4 + 10*i:14 + 10*i]
            number =number_str[0:(len(number_str)-1)] # equals the first 9
            distance_value = int(number,2) + 0.6*float(number_str[len(number_str)-1]) #adds the first 9 bits to 0.6 times the last bit to account for one block that is 86.6 meters
            self.distance_vector.append(distance_value)

            speed_str = beaconvector[4+num_blocks*10 + 3*i:7+num_blocks*10 + 3*i]
            speed_limit = binary_to_value[speed_str]
            self.speeds_vector.append(speed_limit)

            self.underground_vector.append(beaconvector[4+num_blocks*13+i])
            self.at_station_vector.append(beaconvector[4+num_blocks*14+i])
            self.extra_bit_vector.append(beaconvector[4+num_blocks*15+i])

    def baud_read(self,baud_signal):
        # Print the values to debug
        print(f"baud_signal[0:4]: '{baud_signal[0:4]}' (type: {type(baud_signal[0:4])})")
        print(f"self.Baud_ID: '{self.Baud_ID}' (type: {type(self.Baud_ID)})")

        if baud_signal[0:4] == self.Baud_ID:
            self.authority = authority_decoder[baud_signal[-4:]]


    #this function is used to update the speed acceleration and distance travelled of the train over a one second interval
    def update_train(self, power, grade): #power in watts, grade in percentage
        power = power *1000 #converts kW to Watts
        gravitational_acceleration = (g * np.sin(np.arctan(grade/100)))
        self.previous_acceleration = self.acceleration
        if self.ebrake_signal == True:
            self.acceleration = (0 - self.brake_signal*service_brake_deceleration - self.ebrake_signal*emergency_brake_deceleration - gravitational_acceleration)
        else:
            if(self.velocity <= 0):#see Ipad for notes on this derivation but avoids divide by zero error
                self.acceleration = (np.sqrt((2*power)/(self.weight))-self.brake_signal*service_brake_deceleration - self.ebrake_signal*emergency_brake_deceleration - gravitational_acceleration)
            else:#normal acceleration calculation
                self.acceleration = (power/(self.weight*self.velocity) - self.brake_signal*service_brake_deceleration - self.ebrake_signal*emergency_brake_deceleration - gravitational_acceleration)
        velocity_holder = self.velocity
        self.velocity = self.previous_velocity + (1/2)*(self.acceleration + self.previous_acceleration)
        if(self.velocity < 0):
            self.velocity = 0
        self.previous_velocity = velocity_holder
        distance_over_interval = (1/2)*(self.velocity + self.previous_velocity)#one second times the average velocity
        self.distance_travelled += distance_over_interval
        self.distance_vector[0] -= distance_over_interval
        self.authority -= distance_over_interval
        while self.distance_vector[0] < 0:
            self.distance_vector[1] += self.distance_vector[0] #applying extra distance into the next block
            self.distance_vector.pop(0)
            self.speeds_vector.pop(0)
            self.underground_vector.pop(0)
            self.at_station_vector.pop(0)
            self.extra_bit_vector.pop(0)
        #update time flag to move to the next second

"""
TODO: Implement the following functions:
get this test case passed
make GUI



"""


# Example usage
if __name__ == "__main__":
    print("Testing Train Class ----------------------------------------------------------")
    train1 = Train(0)
    #####################0000,1101011101,010,
    train1.beacon_parse("000011010111010100110100101111UVSZE3")
    train1.display_train()
    i = 1
    summer = 0
    while train1.distance_vector[0] > 0:
        train1.update_train(120, 0)
        print("----------------------------------------------------------")
        print(f"Time: {i} seconds")
        print(f"The speed is: {train1.velocity * 3.6} (km/hr)")
        print(f"The acceleration is: {train1.acceleration} (m/s^2), Distance traveled: {train1.distance_travelled} (m)")
        print(f"Distance traveled: {train1.distance_travelled} (m)")
        print(f"The distance remaing in the block is:{train1.distance_vector[0]} (m)")
        summer += train1.acceleration
        avgaccel = summer/i
        print()
        print(f"The average acceleration is: {avgaccel} (m/s^2)")

        i += 1
        time.sleep(1)


