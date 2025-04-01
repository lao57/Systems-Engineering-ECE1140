def update_wayside(block_occupancy, prev_switch_states, block_authorities, maintainence):
    # Initialize outputs
    switch_states = [False] * 2  # 2 switches: one on 12, one on 28
    light_states = [False] * 2  # 2 lights: stopping A and stopping Z
    crossing_states = [False] * 1  # 1 crossings
    stop_signals = [False] * 150

    offset = 1  # Offset for blocks 1-28
    offset2 = 118  # Offset for blocks 146-150

    # Define occupied conditions
    curve_occupied = (
            block_occupancy[1 - offset] or block_occupancy[2 - offset] or block_occupancy[3 - offset] or
            block_occupancy[4 - offset] or block_occupancy[5 - offset] or block_occupancy[6 - offset]
    )

    two_way_occupied = (
            block_occupancy[12 - offset] or block_occupancy[13 - offset] or block_occupancy[14 - offset] or
            block_occupancy[15 - offset] or block_occupancy[16 - offset] or block_occupancy[17 - offset] or
            block_occupancy[18 - offset] or block_occupancy[19 - offset] or block_occupancy[20 - offset] or
            block_occupancy[21 - offset] or block_occupancy[22 - offset] or block_occupancy[23 - offset] or
            block_occupancy[24 - offset] or block_occupancy[25 - offset] or block_occupancy[26 - offset] or
            block_occupancy[27 - offset] or block_occupancy[28 - offset]
    )

    YZ_occupied = (
            block_occupancy[146 - offset2] or block_occupancy[147 - offset2] or
            block_occupancy[148 - offset2] or block_occupancy[149 - offset2] or
            block_occupancy[150 - offset2]
    )

    crossing_occupied = (
            block_occupancy[18 - offset] or block_occupancy[19 - offset] or block_occupancy[20 - offset]
    )

    # Define readiness conditions for A and Z
    A_ready = curve_occupied
    Z_ready = YZ_occupied

    # A has priority if both are ready or two_way is occupied by a train from Z
    A_has_priority = A_ready and (not Z_ready or two_way_occupied)

    # Allow movement logic
    allow_A = not two_way_occupied and A_has_priority
    allow_Z = not two_way_occupied and not A_has_priority

    # Switch 1 (Block 12): Check occupancy
    block_12_idx = 12 - offset

    switch_states[0] = (
            (not block_occupancy[
                block_12_idx] and not two_way_occupied and A_has_priority)  # Allow switch if block 12 is empty and no train is in two_way
            or (block_occupancy[block_12_idx] and prev_switch_states[0])  # Keep previous state if block 12 is occupied
    )

    # Switch 2 (Block 28): Check occupancy
    block_28_idx = 28 - offset
    switch_states[1] = (
            (not block_occupancy[
                block_28_idx] and not two_way_occupied and not A_has_priority)  # Allow switch if block 28 is empty and no train is in two_way
            or (block_occupancy[block_28_idx] and prev_switch_states[1])  # Keep previous state if block 28 is occupied
    )

    # Light control
    light_states[0] = allow_A  # Green light for A if allowed

    stop_signals[0] = allow_Z
    stop_signals[1] = allow_Z
    stop_signals[2] = allow_Z

    light_states[1] = allow_Z  # Green light for Z if allowed

    stop_signals[3] = allow_A
    stop_signals[4] = allow_A

    # Crossing control
    crossing_states[0] = crossing_occupied

    return switch_states, light_states, crossing_states, stop_signals