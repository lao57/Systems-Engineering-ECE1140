class DiscreteTimeSystem:
    def __init__(self, number_of_systems):
        self.system_vector = [False] * number_of_systems
        self.shared_state = 0

    def update_time(self):
        if all(self.system_vector):
            self.shared_state += 1
            self.system_vector = [False] * len(self.system_vector)

    def update_system(self, system_number, system_state):
        self.system_vector[system_number] = system_state

    