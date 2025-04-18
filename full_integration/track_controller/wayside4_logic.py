def update_wayside(block_occupancy, prev_switch_states, block_authorities, maintainence):
    # Initialize outputs
    switch_states = [False] * 7  # 2 switches: one on 12, one on 28
    light_states = [False] * 4  # 2 lights: stopping A and stopping Z
    crossing_states = [False] * 2  # 1 crossings
    stop_signals = [False] * 75
    dont_spawn = [False] * 1

    offset = 1  
    # Define occupied conditions
     # Define occupied conditions
    abc = (
        block_occupancy[1 - offset] or block_occupancy[2 - offset] or block_occupancy[3 - offset] or 
        block_occupancy[4 - offset] or block_occupancy[5 - offset] or block_occupancy[6 - offset] or
        block_occupancy[7 - offset] or block_occupancy[8 - offset] or block_occupancy[9 - offset]
    )
    fg = (
        block_occupancy[16 - offset] or block_occupancy[17 - offset] or block_occupancy[18 - offset] or
        block_occupancy[19 - offset] or block_occupancy[20 - offset] or block_occupancy[21 - offset] or
        block_occupancy[22 - offset] or block_occupancy[23 - offset]
    )
    tsr = (
        block_occupancy[72 - offset] or block_occupancy[73 - offset] or block_occupancy[74 - offset] or
        block_occupancy[75 - offset] or block_occupancy[76 - offset]
    )
    qpo = (
        block_occupancy[71 - offset] or block_occupancy[70 - offset] or block_occupancy[69 - offset] or
        block_occupancy[68 - offset] or block_occupancy[67 - offset]
    )
    H_top = (
        block_occupancy[24 - offset] or block_occupancy[25 - offset] or block_occupancy[26 - offset] or
        block_occupancy[27 - offset] or block_occupancy[28 - offset] or block_occupancy[29 - offset] or
        block_occupancy[30 - offset] or block_occupancy[31 - offset] or block_occupancy[32 - offset]
    )
    H_mid = (
        block_occupancy[33 - offset] or block_occupancy[34 - offset] or block_occupancy[35 - offset] or
        block_occupancy[36 - offset] or block_occupancy[37 - offset] or block_occupancy[38 - offset]
    )
    H_bot = (
        block_occupancy[38 - offset] or block_occupancy[39 - offset] or block_occupancy[40 - offset] or
        block_occupancy[41 - offset] or block_occupancy[42 - offset] or block_occupancy[43 - offset]
    )
    
    long_path = (
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
        
    long_path_no_top_loop = (
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
        
    long_path_no_bot_loop = (
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
    bottom_curve = (
        block_occupancy[57 - offset] or block_occupancy[58 - offset] or block_occupancy[59 - offset] or
        block_occupancy[60 - offset] or block_occupancy[61 - offset] or block_occupancy[62 - offset] or
        block_occupancy[63 - offset] or block_occupancy[64 - offset] or block_occupancy[65 - offset] or block_occupancy[66 - offset]
    )

    into_bottom_loop = (
        block_occupancy[48 - offset] or block_occupancy[47 - offset] or block_occupancy[46 - offset] or
        block_occupancy[45 - offset] or block_occupancy[44 - offset]
    )

    # Define readiness conditions for M and Q
    ABC_ready = abc
    FG_ready = fg
    tsr_ready = tsr
    #top part of the map
    switch_states[1 - offset] = False #always off since we are doing one loop
    switch_states[2 - offset] = (ABC_ready and (not long_path)) or block_occupancy[16 - offset] and prev_switch_states[2 - offset] #if A is ready and nothing is in the long path
    light_states[1 - offset] = not long_path #if anything is on the long path stop the train on A
    #top part of the map


    switch_states[7 - offset] = tsr_ready and (not long_path_no_top_loop) or block_occupancy[27 - offset] and prev_switch_states[7 - offset] #switch allowing train to enter into the long path on the top loop
    light_states[2 - offset] = not (long_path_no_top_loop)

    switch_states[5 - offset] = qpo and (not long_path_no_bot_loop) or block_occupancy[38 - offset] and prev_switch_states[5 - offset] #switch allowing train to enter into the long path on the bottom loop
    light_states[3 -offset] = not (long_path_no_bot_loop)
   
    switch_states[3 - offset] = (bottom_curve and (not long_path)) or (block_occupancy[51] and prev_switch_states[3 - offset])
    light_states[4 - offset] = not (long_path) or block_occupancy[1-offset] or block_occupancy[2-offset] or block_occupancy[3-offset]

    switch_states[4 - offset] = into_bottom_loop and not H_bot or (block_occupancy[44-offset] and prev_switch_states[4 - offset])#if a train is heading into O from I then allow it 

    switch_states[6 - offset] =  H_mid and (not H_top) or (block_occupancy[33-offset] and prev_switch_states[6 - offset])#if a train is heading into R from Hmid then allow it 


    return switch_states, light_states, crossing_states, stop_signals, dont_spawn