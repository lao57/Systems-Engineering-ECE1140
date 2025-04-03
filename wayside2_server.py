"""
Raspberry Pi-side wayside2 hardware program:
1. Act as a TCP server to receive data (in JSON format) from the PC side,
   Extract the block data of wayside2 and call wayside2_logic.update_wayside() to calculate the status;
2. Use Sense HAT LED matrix to display the state of two selected blocks (one upper, one lower):
   - Upper part (rows 0–3): display block number (binary, green) and its switch (red), light (yellow), crossing (blue) states;
   - Lower part (rows 4–7): same as above;
3. Use Joystick left/right to switch between displayed block pairs (e.g., from block0/block1 to block2/block3);
4. Send calculated results back to the PC in JSON format.
"""

import socket
import json
import threading
import time
from sense_hat import SenseHat
import wayside2_logic

latest_switch_states = []
latest_light_states = []
latest_crossing_states = []
latest_stop_states = []

# Initialize block occupancy
prev_switch_states = [False] * 87
lock = threading.Lock()

# Define the list of wayside2 blocks (consistent with PC side)
wayside2_blocks = list(range(29, 74)) + list(range(104, 146))  # About 87 blocks in total
total_blocks = len(wayside2_blocks)  # 应为87

current_display_index = 0
# If the total number is odd, only the upper part is shown at the end
max_display_index = (total_blocks + 1) // 2 - 1

# Start a TCP server to continuously listen to data from the PC
def socket_server():
    # Listen on all network interfaces
    host = ''
    port = 12345
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print("Socket Server started, listening on port", port)
    conn, addr = server_socket.accept()
    print("Connection from", addr)
    buffer = ""
    while True:
        try:
            data = conn.recv(1024).decode()
            if not data:
                break
            buffer += data
            # Each JSON message is delimited by newline
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.strip():
                    process_message(line.strip(), conn)
        except Exception as e:
            print("Socket error:", e)
            break
    conn.close()

def process_message(message, conn):
    """
    Process received JSON message:
    Receive global block_occupancy, block_authority, and maintenance data from PC,
    compute the states of various variables,
    finally send back the calculated results (whole list).
    """
    global latest_switch_states, latest_light_states, latest_crossing_states, prev_switch_states
    try:
        msg = json.loads(message)
        full_block_occupancy = msg.get("block_occupancy", [])
        full_block_authority = msg.get("block_authority", [])
        full_maintenance = msg.get("maintenance", [])
        # Extract wayside2-related block data (from PC, 1-indexed)
        wayside2_block_occupancy = [full_block_occupancy[blk - 1] for blk in wayside2_blocks]
        wayside2_block_authority = [full_block_authority[blk - 1] for blk in wayside2_blocks]
        wayside2_maintenance = [full_maintenance[blk - 1] for blk in wayside2_blocks]
        # Call wayside2_logic to compute states (simple logic: return states based on occupancy)
        switch_states, light_states, crossing_states, stop_states = wayside2_logic.update_wayside(
            wayside2_block_occupancy,
            prev_switch_states,
            wayside2_block_authority,
            wayside2_maintenance
        )
        with lock:
            latest_switch_states = switch_states  # 列表长度为87
            latest_light_states = light_states
            latest_crossing_states = crossing_states
            latest_stop_states = stop_states
            prev_switch_states = switch_states
        # Send response back to PC (whole list)
        response = {
            "switch_states": switch_states,
            "light_states": light_states,
            "crossing_states": crossing_states,
            "stop_states": stop_states
        }
        conn.sendall((json.dumps(response) + "\n").encode())
    except Exception as e:
        print("Error processing message:", e)

# Define LED display mapping:
def update_led_display(sense):
    global current_display_index, total_blocks
    sense.clear()
    index_upper = current_display_index * 2
    index_lower = current_display_index * 2 + 1

    def renumber(block_id):
        if block_id in wayside2_blocks:
            return wayside2_blocks.index(block_id)
        else:
            return 0

    # Upper block status
    if index_upper < total_blocks:
        block_id_upper = wayside2_blocks[index_upper]
        block_number_upper = renumber(block_id_upper)

        # Assign values only to some specific blocks
        if block_id_upper == 57:
            state_switch_upper = latest_switch_states[0]
        elif block_id_upper == 61:
            state_switch_upper = latest_switch_states[1]
        else:
            state_switch_upper = False

        if block_id_upper == 60:
            state_light_upper = latest_light_states[0]
        elif block_id_upper == 59:
            state_light_upper = latest_light_states[1]
        else:
            state_light_upper = False

        if block_id_upper == 107:
            state_crossing_upper = latest_crossing_states[0]
        else:
            state_crossing_upper = False
    else:
        block_number_upper = 0
        state_switch_upper = state_light_upper = state_crossing_upper = False

    # The lower block state
    if index_lower < total_blocks:
        block_id_lower = wayside2_blocks[index_lower]
        block_number_lower = renumber(block_id_lower)

        if block_id_lower == 57:
            state_switch_lower = latest_switch_states[0]
        elif block_id_lower == 61:
            state_switch_lower = latest_switch_states[1]
        else:
            state_switch_lower = False

        if block_id_lower == 60:
            state_light_lower = latest_light_states[0]
        elif block_id_lower == 59:
            state_light_lower = latest_light_states[1]
        else:
            state_light_lower = False

        if block_id_lower == 107:
            state_crossing_lower = latest_crossing_states[0]
        else:
            state_crossing_lower = False
    else:
        block_number_lower = 0
        state_switch_lower = state_light_lower = state_crossing_lower = False

    # LED display
    binary_str = format(block_number_upper, '08b')
    for col, bit in enumerate(binary_str):
        color = (0, 255, 0) if bit == '1' else (0, 0, 0)
        sense.set_pixel(col, 0, color)
    color = (255, 0, 0) if state_switch_upper else (0, 0, 0)
    for col in range(8):
        sense.set_pixel(col, 1, color)
    color = (255, 255, 0) if state_light_upper else (0, 0, 0)
    for col in range(8):
        sense.set_pixel(col, 2, color)
    color = (0, 0, 255) if state_crossing_upper else (0, 0, 0)
    for col in range(8):
        sense.set_pixel(col, 3, color)

    binary_str = format(block_number_lower, '08b')
    for col, bit in enumerate(binary_str):
        color = (0, 255, 0) if bit == '1' else (0, 0, 0)
        sense.set_pixel(col, 4, color)
    color = (255, 0, 0) if state_switch_lower else (0, 0, 0)
    for col in range(8):
        sense.set_pixel(col, 5, color)
    color = (255, 255, 0) if state_light_lower else (0, 0, 0)
    for col in range(8):
        sense.set_pixel(col, 6, color)
    color = (0, 0, 255) if state_crossing_lower else (0, 0, 0)
    for col in range(8):
        (sense.
         set_pixel(col, 7, color))

def joystick_moved(event):
    # Define Joystick behavior: use left/right to change displayed block pair
    global current_display_index, max_display_index
    if event.action == "pressed":
        if event.direction == "left":
            current_display_index = max(current_display_index - 1, 0)
        elif event.direction == "right":
            current_display_index = min(current_display_index + 1, max_display_index)
        print("Current displayed block pair index:", current_display_index)

def main():
    # Main program: initialize Sense HAT, start socket server thread, and loop to update LED
    sense = SenseHat()
    sense.clear()
    sense.stick.direction_any = joystick_moved

    # Start socket server thread (connect to PC to get wayside2 state data)
    server_thread = threading.Thread(target=socket_server, daemon=True)
    server_thread.start()

    # Main loop: refresh LED display periodically
    while True:
        update_led_display(sense)
        time.sleep(0.3)

if __name__ == "__main__":
    main()
