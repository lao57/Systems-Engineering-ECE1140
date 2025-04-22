def update_wayside(block_occupancy, prev_switch_states, block_authorities, maintainence):

    switch_states = [True] * 2  
    light_states = [True] * 2 
    crossing_states = [True] * 1 
    stop_signals = [False] * 3
    dont_spawn = [False] * 1

    offset = 29
    offset2 = 59
    #crossing on 108

    dont_spawn = block_occupancy[58-offset] or block_occupancy[59-offset] or block_occupancy[60-offset] or block_occupancy[61-offset] or block_occupancy[62-offset]
    crossing_states[0] = block_occupancy[109-offset2] or block_occupancy[108-offset2] or block_occupancy[107-offset2]

    switch_states[0] = True #until dillion tells me otherwise 
    switch_states[1] = False #until dillion tells me otherwise

    light_states[0] = False #until dillion tells me otherwise
    stop_signals[0] = False
    stop_signals[1] = False
    stop_signals[2] = False

    light_states[1] = True #until dillion tells me otherwise 
    #dont know how to stop yard/if we can

    return switch_states, light_states, crossing_states, stop_signals, dont_spawn