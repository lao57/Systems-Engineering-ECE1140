import pandas as pd

def load_track_layout(file_path):

    def process_row(row):

        # Skip rows with missing block number
        if pd.isna(row['Block Number']):
            return None

        return {
            'line': str(row['Line']),
            'section': str(row['Section']),
            'block_number': int(row['Block Number']),
            'length': float(row['Block Length (m)']),
            'grade': float(row['Block Grade (%)']),
            'speed_limit': int(row['Speed Limit (Km/Hr)']),
            'infrastructure': str(row['Infrastructure']) if pd.notna(row['Infrastructure']) else None,
            'station_side': str(row['Station Side']) if pd.notna(row['Station Side']) else None,
            'elevation': float(row['ELEVATION (M)']),
            'cumulative_elevation': float(row['CUMALTIVE ELEVATION (M)']),
        }

    # Read and process Red Line
    red_df = pd.read_excel(file_path, sheet_name='Red Line')
    red_blocks = [block for block in red_df.apply(process_row, axis=1) if block is not None]

    # Read and process Green Line
    green_df = pd.read_excel(file_path, sheet_name='Green Line')
    green_blocks = [block for block in green_df.apply(process_row, axis=1) if block is not None]

    # Add traversal time for Green Line
    if 'seconds to traverse block' in green_df.columns:
        for i, row in green_df.iterrows():
            if i < len(green_blocks) and green_blocks[i]:
                green_blocks[i]['traversal_time'] = float(row['seconds to traverse block']) if pd.notna(
                    row['seconds to traverse block']) else None

    return {
        'Red Line': red_blocks,
        'Green Line': green_blocks,
    }