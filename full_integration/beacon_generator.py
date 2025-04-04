import numpy as np
import pandas as pd

# === CONFIG ===
EXCEL_FILE = "green_line.xlsx"     # file name
SHEET_NAME = 0
TID = input("Enter TID for this beacon (e.g. 0001): ")

# === Lookup table configs ===
speed_bin_map = {
    0: "000", 15: "001", 20: "010", 25: "011",
    30: "100", 40: "101", 55: "110", 70: "111"
}

station_map = {
    "PIONEER": "0001",
    "EDGEBROOK": "0010",
    "STATION": "0011",
    "WHITED": "0100",
    "SOUTH BANK": "0101",
    "CENTRAL; UNDERDROUND": "0110",
    "INGLEWOOD; UNDERGROUND": "0111",
    "OVERBROOK; UNDERGROUND": "1000",
    "GLENBURY": "1001",
    "DORMONT": "1010",
    "MT LEBANON": "1011",
    "POPLAR": "1100",
    "CASTLE SHANNON": "1101"
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

    station = "0000"
    for name in station_map:
        if name in infra:
            station = station_map[name]
            break

    return f"{tid}{distance}{speed}{underground}{at_station}{station}"

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
    "".join(selected["Beacon Vector"].str[4:14]) +
    "".join(selected["Beacon Vector"].str[14:17]) +
    "".join(selected["Beacon Vector"].str[17]) +
    "".join(selected["Beacon Vector"].str[18]) +
    "".join(selected["Beacon Vector"].str[19:])
)

# Output
print("\n✅ Beacon Vector:")
print(f'beacon_vector = "{beacon_vector}"\n')
print("grades =", selected["Block Grade (%)"].tolist())
print("block_numbers =", selected["Block Number"].tolist())
