def update_wayside(block_occupancy, prev_switch_states, block_authorities, maintenance):
    """
    Update wayside logic for the section containing blocks M, N, and Q.
    
    Parameters:
    - block_occupancy (list of bool): Indicates whether each track block is currently occupied.
    - prev_switch_states (list of bool): The previous state of each switch.
    - block_authorities (unused): Reserved for authority logic, not used here.
    - maintenance (unused): Placeholder for future use.

    Returns:
    - switch_states (list of bool): Updated switch states.
    - light_states (list of bool): Updated light signals for M and Q.
    - crossing_states (list of bool): No crossings in this section.
    - stop_signals (list of bool): Stop signals for M and Q directions.
    - dont_spawn (list of bool): No spawning logic for this wayside.
    """

    # --- Initialize all outputs ---
    switch_states = [False] * 2           # Two switches (MN-R and QO-N)
    light_states = [False] * 2            # Lights for M and Q
    crossing_states = [False] * 0         # No crossings in this wayside
    stop_signals = [False] * 6            # Stop signals for both directions
    dont_spawn = [False] * 0              # No spawning logic needed

    offset = 74  # Base block number offset for indexing

    # --- Determine occupancy for each relevant block group ---
    Q_occupied = (
        block_occupancy[95 - offset] or block_occupancy[96 - offset] or
        block_occupancy[97 - offset] or block_occupancy[98 - offset] or
        block_occupancy[99 - offset] or block_occupancy[100 - offset]
    )

    N_occupied = (
        block_occupancy[77 - offset] or block_occupancy[78 - offset] or
        block_occupancy[79 - offset] or block_occupancy[80 - offset] or
        block_occupancy[81 - offset] or block_occupancy[82 - offset] or
        block_occupancy[83 - offset] or block_occupancy[84 - offset] or
        block_occupancy[85 - offset]
    )

    M_occupied = (
        block_occupancy[74 - offset] or block_occupancy[75 - offset] or
        block_occupancy[76 - offset]
    )

    # --- Check if a train is on a switch block to prevent unsafe switching ---
    Switch_MN_R_occupied = block_occupancy[77 - offset]
    Switch_QO_N_occupied = block_occupancy[85 - offset]

    # --- Define readiness of trains from M and Q ---
    M_ready = M_occupied
    Q_ready = Q_occupied

    # M has priority if both are ready or if N is occupied and Q is also trying to move
    M_has_priority = M_ready and (not Q_ready or N_occupied)

    # --- Determine if each direction is allowed to move ---
    allow_M = not N_occupied and M_has_priority
    allow_Q = not N_occupied and not M_has_priority

    # --- Switch logic: maintain previous state if a train is on the switch ---
    switch_states[0] = (
        (not Switch_MN_R_occupied and not allow_M) or 
        (Switch_MN_R_occupied and prev_switch_states[0])
    )

    switch_states[1] = (
        (not Switch_QO_N_occupied and allow_Q) or 
        (Switch_QO_N_occupied and prev_switch_states[1])
    )

    # --- Light and stop signal logic ---
    light_states[0] = allow_M
    stop_signals[0] = not allow_M
    stop_signals[1] = not allow_M
    stop_signals[2] = not allow_M

    light_states[1] = allow_Q
    stop_signals[3] = not allow_Q
    stop_signals[4] = not allow_Q
    stop_signals[5] = not allow_Q

    return switch_states, light_states, crossing_states, stop_signals, dont_spawn
