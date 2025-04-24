def update_wayside(block_occupancy, prev_switch_states, block_authorities, maintainence):
    """
    Update the state of switches, lights, crossings, and stop signals for a train control system.

    Parameters:
    - block_occupancy (list of bool): True if the block is currently occupied by a train.
    - prev_switch_states (list of bool): The previous states of the switches.
    - block_authorities (unused): Reserved for future logic regarding authority through blocks.
    - maintainence (unused): Reserved for future logic to handle maintenance mode on blocks.

    Returns:
    - switch_states (list of bool): Current state of the switches.
    - light_states (list of bool): Current state of the lights (green if train may proceed).
    - crossing_states (list of bool): Current state of the crossing (True if active).
    - stop_signals (list of bool): Stop signals to prevent train movement.
    - dont_spawn (list of bool): Placeholder for future train spawning logic.
    """
    
    # Initialize outputs
    switch_states = [False] * 2       # 2 switches: located at block 12 and block 28
    light_states = [False] * 2        # 2 lights: facing A and Z directions
    crossing_states = [False] * 1     # 1 crossing
    stop_signals = [False] * 150      # Stop signal array (150 entries)
    dont_spawn = [False] * 0          # Placeholder for future spawning logic

    offset = 1        # Offset for addressing blocks 1-28
    offset2 = 118     # Offset for addressing blocks 146-150

    # Check if any of the curve blocks (1 to 6) are occupied
    curve_occupied = (
        block_occupancy[1 - offset] or block_occupancy[2 - offset] or
        block_occupancy[3 - offset] or block_occupancy[4 - offset] or
        block_occupancy[5 - offset] or block_occupancy[6 - offset]
    )

    # Check if any of the two-way blocks (12 to 28) are occupied
    two_way_occupied = any(
        block_occupancy[i - offset] for i in range(12, 29)
    )

    # Check if any of the Y-Z blocks (146 to 150) are occupied
    YZ_occupied = any(
        block_occupancy[i - offset2] for i in range(146, 151)
    )

    # Determine if the crossing area (blocks 18 to 20) is occupied
    crossing_occupied = (
        block_occupancy[18 - offset] or block_occupancy[19 - offset] or 
        block_occupancy[20 - offset]
    )

    # Define train readiness from direction A or Z
    A_ready = curve_occupied
    Z_ready = YZ_occupied

    # Priority logic: Z has priority if it's ready and either A isn't or two-way is occupied
    Z_has_priority = Z_ready and (not A_ready or two_way_occupied)

    # Determine if movement is allowed from A or Z
    allow_Z = not two_way_occupied and Z_has_priority
    allow_A = not two_way_occupied and not Z_has_priority

    # --- Switch Logic ---

    # Switch 1 at Block 12: Only change if block is empty and conditions allow, otherwise hold
    block_12_idx = 12 - offset
    switch_states[0] = (
        (not block_occupancy[block_12_idx] and not two_way_occupied and Z_has_priority)
        or (block_occupancy[block_12_idx] and prev_switch_states[0])
    )

    # Switch 2 at Block 28: Same logic applied
    block_28_idx = 28 - offset
    switch_states[1] = (
        (not block_occupancy[block_28_idx] and not two_way_occupied and not Z_has_priority)
        or (block_occupancy[block_28_idx] and prev_switch_states[1])
    )

    # --- Light and Stop Signal Logic ---

    # Light for direction A
    light_states[0] = allow_A
    stop_signals[0] = not allow_A
    stop_signals[1] = not allow_A
    stop_signals[2] = not allow_A

    # Light for direction Z
    light_states[1] = allow_Z
    stop_signals[3] = not allow_Z
    stop_signals[4] = not allow_Z

    # --- Crossing Logic ---
    crossing_states[0] = crossing_occupied

    return switch_states, light_states, crossing_states, stop_signals, dont_spawn
