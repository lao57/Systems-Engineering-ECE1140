def update_wayside(block_occupancy, prev_switch_states, block_authorities, maintenance):
    """
    Update the wayside controller state based on current track conditions.
    
    This function implements the PLC logic for the Red Line wayside controller (wayside4).
    It determines switch positions, signal lights, crossing gates, and stop signals
    based on block occupancy and maintenance status.
    
    Args:
        block_occupancy: List of booleans indicating occupancy status for each block (1-76)
        prev_switch_states: List of current switch positions
        block_authorities: List of authority values for each block
        maintenance: List of maintenance status for each block
        
    Returns:
        tuple: (switch_states, light_states, crossing_states, stop_signals, dont_spawn)
            - switch_states: List of new switch positions (7 switches)
            - light_states: List of signal light states (4 lights)
            - crossing_states: List of crossing gate states (2 crossings)
            - stop_signals: List of stop signal states (75 blocks)
            - dont_spawn: List of spawn prevention flags (unused in this implementation)
    """
    # Initialize all outputs to default states
    switch_states = [False] * 7  # 7 switches on Red Line
    light_states = [False] * 4    # 4 signal lights on Red Line
    crossing_states = [False] * 2 # 2 crossing gates on Red Line
    stop_signals = [False] * 75   # Stop signals for 75 blocks
    dont_spawn = [False] * 1      # Spawn prevention flag (unused)

    offset = 1  # Convert from 1-based to 0-based indexing

    # Define block occupancy conditions for different track segments
    # These boolean expressions represent occupancy in key track areas
    
    # Yard and approach blocks (A-B-C)
    abc_occupied = (
        block_occupancy[1 - offset] or block_occupancy[2 - offset] or block_occupancy[3 - offset] or 
        block_occupancy[4 - offset] or block_occupancy[5 - offset] or block_occupancy[6 - offset] or
        block_occupancy[7 - offset] or block_occupancy[8 - offset] or block_occupancy[9 - offset]
    )
    
    # F-G straight section
    fg_occupied = (
        block_occupancy[16 - offset] or block_occupancy[17 - offset] or block_occupancy[18 - offset] or
        block_occupancy[19 - offset] or block_occupancy[20 - offset] or block_occupancy[21 - offset] or
        block_occupancy[22 - offset] or block_occupancy[23 - offset]
    )
    
    # Top loop return (T-S-R)
    tsr_occupied = (
        block_occupancy[72 - offset] or block_occupancy[73 - offset] or block_occupancy[74 - offset] or
        block_occupancy[75 - offset] or block_occupancy[76 - offset]
    )
    
    # Bottom loop approach (Q-P-O)
    qpo_occupied = (
        block_occupancy[71 - offset] or block_occupancy[70 - offset] or block_occupancy[69 - offset] or
        block_occupancy[68 - offset] or block_occupancy[67 - offset]
    )
    
    # Top of H section
    h_top_occupied = (
        block_occupancy[24 - offset] or block_occupancy[25 - offset] or block_occupancy[26 - offset] or
        block_occupancy[27 - offset] or block_occupancy[28 - offset] or block_occupancy[29 - offset] or
        block_occupancy[30 - offset] or block_occupancy[31 - offset] or block_occupancy[32 - offset]
    )
    
    # Middle of H section
    h_mid_occupied = (
        block_occupancy[33 - offset] or block_occupancy[34 - offset] or block_occupancy[35 - offset] or
        block_occupancy[36 - offset] or block_occupancy[37 - offset] or block_occupancy[38 - offset]
    )
    
    # Bottom of H section
    h_bot_occupied = (
        block_occupancy[38 - offset] or block_occupancy[39 - offset] or block_occupancy[40 - offset] or
        block_occupancy[41 - offset] or block_occupancy[42 - offset] or block_occupancy[43 - offset]
    )
    
    # Full main line path (through all blocks)
    long_path_occupied = (
        block_occupancy[16 - offset] or block_occupancy[17 - offset] or block_occupancy[18 - offset] or
        block_occupancy[19 - offset] or block_occupancy[20 - offset] or block_occupancy[21 - offset] or
        block_occupancy[22 - offset] or block_occupancy[23 - offset] or block_occupancy[24 - offset] or
        block_occupancy[25 - offset] or block_occupancy[26 - offset] or block_occupancy[27 - offset] or
        block_occupancy[28 - offset] or block_occupancy[29 - offset] or block_occupancy[30 - offset] or
        block_occupancy[31 - offset] or block_occupancy[32 - offset] or block_occupancy[33 - offset] or
        block_occupancy[34 - offset] or block_occupancy[35 - offset] or block_occupancy[36 - offset] or
        block_occupancy[37 - offset] or block_occupancy[38 - offset] or block_occupancy[39 - offset] or
        block_occupancy[40 - offset] or block_occupancy[41 - offset] or block_occupancy[42 - offset] or
        block_occupancy[43 - offset] or block_occupancy[44 - offset] or block_occupancy[45 - offset] or
        block_occupancy[46 - offset] or block_occupancy[47 - offset] or block_occupancy[48 - offset] or
        block_occupancy[49 - offset] or block_occupancy[50 - offset] or block_occupancy[51 - offset] or
        block_occupancy[52 - offset] or block_occupancy[67 - offset] or block_occupancy[68 - offset] or 
        block_occupancy[69 - offset] or block_occupancy[70 - offset] or block_occupancy[71 - offset] or
        block_occupancy[72 - offset] or block_occupancy[73 - offset] or block_occupancy[74 - offset] or
        block_occupancy[75 - offset] or block_occupancy[76 - offset]
    )
    
    # Main line path excluding top loop
    long_path_no_top_loop_occupied = (
        block_occupancy[16 - offset] or block_occupancy[17 - offset] or block_occupancy[18 - offset] or
        block_occupancy[19 - offset] or block_occupancy[20 - offset] or block_occupancy[21 - offset] or
        block_occupancy[22 - offset] or block_occupancy[23 - offset] or block_occupancy[24 - offset] or
        block_occupancy[25 - offset] or block_occupancy[26 - offset] or block_occupancy[27 - offset] or
        block_occupancy[28 - offset] or block_occupancy[29 - offset] or block_occupancy[30 - offset] or
        block_occupancy[31 - offset] or block_occupancy[32 - offset] or block_occupancy[33 - offset] or
        block_occupancy[34 - offset] or block_occupancy[35 - offset] or block_occupancy[36 - offset] or
        block_occupancy[37 - offset] or block_occupancy[38 - offset] or block_occupancy[39 - offset] or
        block_occupancy[40 - offset] or block_occupancy[41 - offset] or block_occupancy[42 - offset] or
        block_occupancy[43 - offset] or block_occupancy[44 - offset] or block_occupancy[45 - offset] or
        block_occupancy[46 - offset] or block_occupancy[47 - offset] or block_occupancy[48 - offset] or
        block_occupancy[49 - offset] or block_occupancy[50 - offset] or block_occupancy[51 - offset] or
        block_occupancy[52 - offset] or block_occupancy[67 - offset] or block_occupancy[68 - offset] or 
        block_occupancy[69 - offset] or block_occupancy[70 - offset] or block_occupancy[71 - offset]
    )
    
    # Main line path excluding bottom loop
    long_path_no_bot_loop_occupied = (
        block_occupancy[16 - offset] or block_occupancy[17 - offset] or block_occupancy[18 - offset] or
        block_occupancy[19 - offset] or block_occupancy[20 - offset] or block_occupancy[21 - offset] or
        block_occupancy[22 - offset] or block_occupancy[23 - offset] or block_occupancy[24 - offset] or
        block_occupancy[25 - offset] or block_occupancy[26 - offset] or block_occupancy[27 - offset] or
        block_occupancy[28 - offset] or block_occupancy[29 - offset] or block_occupancy[30 - offset] or
        block_occupancy[31 - offset] or block_occupancy[32 - offset] or block_occupancy[33 - offset] or
        block_occupancy[34 - offset] or block_occupancy[35 - offset] or block_occupancy[36 - offset] or
        block_occupancy[37 - offset] or block_occupancy[38 - offset] or block_occupancy[39 - offset] or
        block_occupancy[40 - offset] or block_occupancy[41 - offset] or block_occupancy[42 - offset] or
        block_occupancy[43 - offset] or block_occupancy[44 - offset] or block_occupancy[45 - offset] or
        block_occupancy[46 - offset] or block_occupancy[47 - offset] or block_occupancy[48 - offset] or
        block_occupancy[49 - offset] or block_occupancy[50 - offset] or block_occupancy[51 - offset] or
        block_occupancy[52 - offset] or
        block_occupancy[72 - offset] or block_occupancy[73 - offset] or block_occupancy[74 - offset] or
        block_occupancy[75 - offset] or block_occupancy[76 - offset]
    )
    
    # Bottom curve section
    bottom_curve_occupied = (
        block_occupancy[57 - offset] or block_occupancy[58 - offset] or block_occupancy[59 - offset] or
        block_occupancy[60 - offset] or block_occupancy[61 - offset] or block_occupancy[62 - offset] or
        block_occupancy[63 - offset] or block_occupancy[64 - offset] or block_occupancy[65 - offset] or 
        block_occupancy[66 - offset]
    )
    
    # Approach to bottom loop
    into_bottom_loop_occupied = (
        block_occupancy[48 - offset] or block_occupancy[47 - offset] or block_occupancy[46 - offset] or
        block_occupancy[45 - offset] or block_occupancy[44 - offset]
    )

    # Switch 1: Fixed position (always False in current implementation)
    switch_states[1 - offset] = False
    
    # Switch 2: Controls entry from yard to main line
    # Allows entry if yard is ready and main line is clear, or if train is already approaching
    switch_states[2 - offset] = (
        (abc_occupied and (not long_path_occupied)) or 
        (block_occupancy[16 - offset] and prev_switch_states[2 - offset])
    )
    
    # Light 1: Controls yard entry signal
    # Red if anything is on the main line path
    light_states[1 - offset] = not long_path_occupied
    
    # Stop signals for yard approach blocks
    stop_signals[1 - offset] = not light_states[1 - offset] 
    stop_signals[2 - offset] = not light_states[1 - offset] 
    stop_signals[3 - offset] = not light_states[1 - offset] 

    # Switch 7: Controls entry to top loop
    # Allows entry if top loop return is ready and main line (excluding top loop) is clear
    switch_states[7 - offset] = (
        (tsr_occupied and (not long_path_no_top_loop_occupied)) or 
        (block_occupancy[27 - offset] and prev_switch_states[7 - offset])
    )
    
    # Light 2: Top loop entry signal
    light_states[2 - offset] = not long_path_no_top_loop_occupied
    
    # Stop signals for top loop approach
    stop_signals[4 - offset] = not light_states[2 - offset] 
    stop_signals[5 - offset] = not light_states[2 - offset] 
    stop_signals[6 - offset] = not light_states[2 - offset] 

    # Switch 5: Controls entry to bottom loop
    # Allows entry if bottom approach is ready and main line (excluding bottom loop) is clear
    switch_states[5 - offset] = (
        (qpo_occupied and (not long_path_no_bot_loop_occupied)) or 
        (block_occupancy[38 - offset] and prev_switch_states[5 - offset])
    )
    
    # Light 3: Bottom loop entry signal
    light_states[3 - offset] = not long_path_no_bot_loop_occupied
    
    # Stop signals for bottom loop approach
    stop_signals[7 - offset] = not light_states[3 - offset] 
    stop_signals[8 - offset] = not light_states[3 - offset] 
    stop_signals[9 - offset] = not light_states[3 - offset]   

    # Switch 3: Controls bottom curve entry
    switch_states[3 - offset] = (
        (bottom_curve_occupied and (not long_path_occupied)) or 
        (block_occupancy[51 - offset] and prev_switch_states[3 - offset])
    )
    
    # Light 4: Bottom curve signal
    light_states[4 - offset] = (
        not long_path_occupied or 
        block_occupancy[1 - offset] or 
        block_occupancy[2 - offset] or 
        block_occupancy[3 - offset]
    )
    
    # Stop signals for bottom curve
    stop_signals[10 - offset] = not light_states[4 - offset] 
    stop_signals[11 - offset] = not light_states[4 - offset] 
    stop_signals[12 - offset] = not light_states[4 - offset]   

    # Switch 4: Controls entry to bottom loop from H section
    switch_states[4 - offset] = (
        (into_bottom_loop_occupied and not h_bot_occupied) or 
        (block_occupancy[44 - offset] and prev_switch_states[4 - offset])
    )

    # Switch 6: Controls middle H section routing
    switch_states[6 - offset] = (
        (h_mid_occupied and (not h_top_occupied)) or 
        (block_occupancy[33 - offset] and prev_switch_states[6 - offset])
    )

    # Crossing 1: Activated by blocks 10-12
    crossing_states[1 - offset] = (
        block_occupancy[10 - offset] or 
        block_occupancy[11 - offset] or  
        block_occupancy[12 - offset]
    )
    
    # Crossing 2: Activated by blocks 46-48
    crossing_states[2 - offset] = (
        block_occupancy[46 - offset] or 
        block_occupancy[47 - offset] or  
        block_occupancy[48 - offset]
    )

    return switch_states, light_states, crossing_states, stop_signals, dont_spawn