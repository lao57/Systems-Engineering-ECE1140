import pandas as pd
from typing import Dict, List

def load_track_layout(path: str) -> Dict[str, List[dict]]:
    COLUMN_MAP = {
        'block number': 'block_number',
        'block length (m)': 'block_length',
        'speed limit (km/hr)': 'speed_limit',
        'infrastructure': 'infrastructure'
    }

    def process_sheet(sheet: str) -> List[dict]:
        try:
            df = pd.read_excel(
                path,
                sheet_name=sheet,
                engine='openpyxl'
            ).rename(columns=str.lower).rename(columns=COLUMN_MAP)

            # Clean and validate data
            df = df.dropna(subset=['block_number'])
            df['block_number'] = pd.to_numeric(df['block_number'], errors='coerce').dropna().astype(int)

            valid_blocks = []
            for _, row in df.iterrows():
                try:
                    block_data = {
                        'line': sheet.strip(),
                        'block_number': int(row['block_number']),
                        'block_length': float(row['block_length']),
                        'speed_limit': int(row['speed_limit']),
                        'infrastructure': str(row.get('infrastructure', '')).strip().upper()
                    }
                    if 1 <= block_data['block_number'] <= 150:
                        valid_blocks.append(block_data)
                except Exception as e:

                    pass

            return valid_blocks

        except Exception as e:

            return []

    return {
        'Red Line': process_sheet('Red Line'),
        'Green Line': process_sheet('Green Line')
    }
