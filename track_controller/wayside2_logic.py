def update_wayside(block_occupancy, prev_switch_states, block_authorities, maintainence):

    switch_states = [True] * 2  
    light_states = [True] * 2 
    crossing_states = [True] * 1 
    stop_signals = [False] * 150


    offset = 29
    offset2 = 59
    #crossing on 108

    switch_states[0] = True #until dillion tells me otherwise 
    switch_states[1] = False #until dillion tells me otherwise

    light_states[0] = False #until dillion tells me otherwise 
    light_states[1] = True #until dillion tells me otherwise 


    return switch_states, light_states, crossing_states, stop_signals