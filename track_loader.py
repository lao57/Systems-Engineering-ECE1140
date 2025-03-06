import pandas as pd
import logging

logger = logging.getLogger(__name__)


def load_track_layout(path):
    def process_sheet(sheet):
        try:
            df = pd.read_excel(path, sheet_name=sheet)
            valid_blocks = []

            for _, row in df.iterrows():
                # Validate block number
                try:
                    block_num = int(float(row['Block Number']))
                except (ValueError, KeyError):
                    logger.warning(f"Invalid Block Number in row {_ + 2} of {sheet}")
                    continue

                # Validate required numeric fields
                try:
                    block_data = {
                        'line': str(row.get('Line', '')).strip(),
                        'section': str(row.get('Section', '')).strip(),
                        'block_number': block_num,
                        'block_length': float(row['Block Length (m)']),
                        'grade': float(row['Block Grade (%)']),
                        'speed_limit': int(row['Speed Limit (Km/Hr)']),
                        'infrastructure': str(row.get('Infrastructure', '')).strip(),
                        'station_side': str(row.get('Station Side', '')).strip(),
                        'elevation': float(row['ELEVATION (M)']),
                        'cumulative_elevation': float(row['CUMALTIVE ELEVATION (M)'])
                    }
                    valid_blocks.append(block_data)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid row {_ + 2} in {sheet}: {str(e)}")

            return valid_blocks

        except Exception as e:
            logger.error(f"Failed to process {sheet}: {str(e)}")
            return []

    return {
        'Red Line': process_sheet('Red Line'),
        'Green Line': process_sheet('Green Line')
    }