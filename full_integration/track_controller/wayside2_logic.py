def update_wayside(block_occupancy, prev_switch_states, block_authorities, maintainence):
    """
    Update the wayside logic for a specific section of the railway system.
    
    Parameters:
    - block_occupancy (list of bool): List indicating whether each block is currently occupied by a train.
    - prev_switch_states (list of bool): Previous state of each switch.
    - block_authorities (unused): Placeholder for block movement authority input.
    - maintainence (unused): Placeholder for future maintenance-based logic.
    
    Returns:
    - switch_states (list of bool): New switch positions (True for one direction, False for the other).
    - light_states (list of bool): Signal light states (True for green, False for red).
    - crossing_states (list of bool): Indicates whether the crossing should be active.
    - stop_signals (list of bool): Signals indicating trains must stop.
    - dont_spawn (bool): Indicates whether spawning a new train is prohibited due to occupancy.
    """

    # --- Initialize output states ---
    switch_states = [True] * 2        # Default: switch 1 True, switch 2 False (manual override)
    light_states = [True] * 2         # Default: both lights green
    crossing_states = [True] * 1      # Default: crossing active
    stop_signals = [False] * 3        # Default: no stop signals triggered
    dont_spawn = [False] * 1          # Default: train can be spawned

    offset = 29     # Offset to align block numbers for first segment
    offset2 = 59    # Offset to align block numbers for second segment
    # Note: Crossing is on block 108

    # --- Prevent spawning if any yard blocks (58–62) are occupied ---
    dont_spawn[0] = (
        block_occupancy[58 - offset] or block_occupancy[59 - offset] or
        block_occupancy[60 - offset] or block_occupancy[61 - offset] or
        block_occupancy[62 - offset]
    )

    # --- Activate crossing if any approach blocks (107–109) are occupied ---
    crossing_states[0] = (
        block_occupancy[109 - offset2] or 
        block_occupancy[108 - offset2] or 
        block_occupancy[107 - offset2]
    )

    # --- Switch Control ---
    # These are hardcoded until further instruction from Dillon
    switch_states[0] = True
    switch_states[1] = False

    # --- Signal Light and Stop Signal Control ---
    # Current light behavior is placeholder and may be updated
    light_states[0] = False
    stop_signals[0] = False
    stop_signals[1] = False
    stop_signals[2] = False

    light_states[1] = True  # Allow trains to proceed in this direction (placeholder)
    # Note: Yard stopping logic is currently unknown / not implemented

    return switch_states, light_states, crossing_states, stop_signals, dont_spawn
