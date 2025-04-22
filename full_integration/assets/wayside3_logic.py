def update_wayside(block_occupancy, prev_switch_states, block_authorities, maintenance):
    switch_states = [False] * 2  # 2 switches
    light_states = [False] * 2  # 2 lights: M and O
    crossing_states = [False] * 0  # 0 crossings (not used)
    stop_signals = [False] * 6
    dont_spawn = [False] * 0

    offset = 74  # Offset for block numbering

    # Define occupied conditions
    Q_occupied = (
        block_occupancy[95 - offset] or block_occupancy[96 - offset] or block_occupancy[97 - offset] or 
        block_occupancy[98 - offset] or block_occupancy[99 - offset] or block_occupancy[100 - offset]
    )
    
    N_occupied = (
        block_occupancy[77 - offset] or block_occupancy[78 - offset] or block_occupancy[79 - offset] or 
        block_occupancy[80 - offset] or block_occupancy[81 - offset] or block_occupancy[82 - offset] or 
        block_occupancy[83 - offset] or block_occupancy[84 - offset] or block_occupancy[85 - offset]
    )
    
    M_occupied = (
        block_occupancy[74 - offset] or block_occupancy[75 - offset] or block_occupancy[76 - offset]
    )

    # Prevent switching while a train is on top of the switch
    Switch_MN_R_occupied = block_occupancy[77 - offset]  # Train on switch MN
    Switch_QO_N_occupied = block_occupancy[85 - offset]  # Train on switch QO

    # Define readiness conditions for M and Q
    M_ready = M_occupied
    Q_ready = Q_occupied

    # M has priority if both M and Q are ready
    M_has_priority = M_ready and (not Q_ready or N_occupied)

    # Allow movement logic
    allow_M = (not N_occupied) and M_has_priority
    allow_Q = (not N_occupied) and (not M_has_priority)

    # Switch controls: Do not switch if occupied, and use previous state if necessary
    switch_states[0] = (
        (not Switch_MN_R_occupied and not allow_M)  # Allow switch if block 85 is empty and M has priority
        or (Switch_MN_R_occupied and  prev_switch_states[0])  # Keep previous state if block 85 is occupied
    )

    switch_states[1] = (
        (not Switch_QO_N_occupied) and allow_Q  # Allow switch if block 100 is empty and Q has priority
        or (Switch_QO_N_occupied and prev_switch_states[1])  # Keep previous state if block 100 is occupied
    )

    # Light control: Stop signals for M and Q
    light_states[0] = allow_M  # Stop M if it's not allowed to move
    stop_signals[0] = not allow_M
    stop_signals[1] = not allow_M
    stop_signals[2] = not allow_M


    light_states[1] = allow_Q  # Stop Q if it's not allowed to move
    stop_signals[3] = not allow_Q
    stop_signals[4] = not allow_Q
    stop_signals[5] = not allow_Q

    return switch_states, light_states, crossing_states, stop_signals, dont_spawn