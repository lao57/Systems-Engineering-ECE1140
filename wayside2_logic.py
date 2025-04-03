def update_wayside(block_occupancy, prev_switch_states, block_authorities, maintainence):

    switch_states = [True] * 2
    light_states = [True] * 2
    crossing_states = [True] * 1
    stop_signals = [False] * 3

    offset = 29
    offset2 = 59
    #crossing on 108
    crossing_states[0] = block_occupancy[109 - offset2] or block_occupancy[108 - offset2] or block_occupancy[107 - offset2]

    switch_states[0] = True
    switch_states[1] = False

    light_states[0] = False
    stop_signals[0] = False
    stop_signals[1] = False
    stop_signals[2] = False

    light_states[1] = True

    return switch_states, light_states, crossing_states, stop_signals