import numpy as np
import pandas as pd

# === CONFIG ===
EXCEL_FILE = "assets/green_line_map.xlsx"     # file name
SHEET_NAME = 0
TID = input("Enter TID for this beacon (e.g. 0001): ")

# === Lookup table configs ===
speed_bin_map = {
    0: "000", 15: "001", 20: "010", 25: "011",
    30: "100", 40: "101", 55: "110", 70: "111"
}

station_map = {
    "STATION; PIONEER": "0001",
    "STATION; EDGEBROOK": "0010",
    "STATION": "0011",
    "STATION; WHITED": "0100",
    "STATION; SOUTH BANK": "0101",
    "STATION; CENTRAL": "0110",
    "STATION; INGLEWOOD": "0111",
    "STATION; OVERBROOK": "1000",
    "STATION; GLENBURY": "1001",
    "STATION; DORMONT": "1010",
    "STATION; MT LEBANON": "1011",
    "STATION; POPLAR": "1100",
    "STATION; CASTLE SHANNON": "1101"
}

def get_closest_speed_bin(speed):
    valid = np.array(list(speed_bin_map.keys()))
    closest = valid[np.abs(valid - speed).argmin()]
    return speed_bin_map[closest]

def encode_distance(meters):
    decimal_flag = 1 if meters % 1 != 0 else 0
    binary = format(int(meters) % 512, "09b")
    return binary + str(decimal_flag)

def generate_beacon_vector(row, tid):
    distance = encode_distance(row["Block Length (m)"])
    speed = get_closest_speed_bin(int(row["Speed Limit (Km/Hr)"]))
    infra = str(row["Infrastructure"]).upper()
    grade = float(row["Block Grade (%)"])

    underground = "1" if "UNDERGROUND" in infra or grade < 0 else "0"
    at_station = "1" if "STATION" in infra else "0"

    # Extract station name if present
    station = "0000"
    if "STATION" in infra:
        station_name = infra.split(";")[-1].strip()  # Extract the name after "STATION;"
        station = station_map.get(f"STATION; {station_name}", "0000")  # Look up in station_map
    
    # Determine station side bits
    station_side = str(row["Station Side"]).strip().upper() if "Station Side" in row else ""
    if station_side == "LEFT/RIGHT" or station_side == "BOTH":
        station_side_bits = "11"
        print("both sides found")
    elif station_side == "RIGHT":
        station_side_bits = "01"
        print("right side found")
    elif station_side == "LEFT":
        station_side_bits = "10"
        print("left side found")
    else:
        station_side_bits = "00"
        print("no side found")

    return f"{tid}{distance}{speed}{underground}{at_station}{station}{station_side_bits}"

# === LOAD DATA ===
df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

# Ask user for block numbers
block_numbers_input = input("Enter block numbers separated by commas: ")
block_numbers = [int(x.strip()) for x in block_numbers_input.split(",")]

# Filter and sort
selected = df[df["Block Number"].isin(block_numbers)].copy()
selected = selected.set_index("Block Number").loc[block_numbers].reset_index()

# Generate vectors
selected["Beacon Vector"] = selected.apply(lambda r: generate_beacon_vector(r, TID), axis=1)

# Build long beacon vector
beacon_vector = (
    TID +
    "".join(selected["Beacon Vector"].str[4:14]) +  # Distance
    "".join(selected["Beacon Vector"].str[14:17]) +  # Speed
    "".join(selected["Beacon Vector"].str[17]) +  # Underground
    "".join(selected["Beacon Vector"].str[18]) +  # At Station
    "".join(selected["Beacon Vector"].str[19:23]) +  # Station Name
    "".join(selected["Beacon Vector"].str[23:])  # Station Side Bits
)

# Output
print("\n✅ Beacon Vector:")
print(f'beacon_vector = "{beacon_vector}"\n')
print("grades =", selected["Block Grade (%)"].tolist())
print("block_numbers =", selected["Block Number"].tolist())
