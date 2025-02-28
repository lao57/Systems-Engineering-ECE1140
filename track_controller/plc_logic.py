def update_plc_logic(block_occupancy, num_switches, num_lights, num_crossings):
    """
    Logic for wayside1 (blocks 0-3).
    """
    switch_states = [False] * num_switches 
    light_states = [False] * num_lights  
    crossing_states = [False] * num_crossings  

    # Crossing is active if any of blocks 0, 1, or 2 are occupied
    crossing_states[0] = block_occupancy[0] or block_occupancy[1] or block_occupancy[2]
    
    return switch_states, light_states, crossing_states

def update_plc_logic2(block_occupancy, num_switches, num_lights, num_crossings):
    """
    Logic for wayside2 (blocks 4-14).
    """
    switch_states = [False] * num_switches 
    light_states = [False] * num_lights  
    crossing_states = [False] * num_crossings  

    # Block A: Blocks 4-5
    block_a_occupied = block_occupancy[0] or block_occupancy[1]
    # Block B: Blocks 6-10
    block_b_occupied = block_occupancy[2] or block_occupancy[3] or block_occupancy[4] or block_occupancy[5] or block_occupancy[6]
    # Block C: Blocks 11-14
    block_c_occupied = block_occupancy[7] or block_occupancy[8] or block_occupancy[9] or block_occupancy[10]

    # Light and switch logic
    light_states[0] = not ((block_a_occupied and block_b_occupied) or (block_a_occupied and block_b_occupied and block_c_occupied))
    light_states[1] = not ((block_a_occupied and block_c_occupied) or (block_a_occupied and block_b_occupied and block_c_occupied))
    switch_states[0] = block_a_occupied and block_b_occupied

    return switch_states, light_states, crossing_states