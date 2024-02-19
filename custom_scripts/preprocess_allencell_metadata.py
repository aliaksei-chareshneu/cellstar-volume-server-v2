import ast
import json
from pathlib import Path
import pandas as pd
import zarr

# PLAN:

# open CSV file
# find raw with that cellId
# get channel names
# all necessary info
# put to .attrs ['extra_data']
# access those attrs in extract_ometiff_metadata

# pandas.read_csv

# need to know cell_id
# can be still provided to script, no problem
def process_allencell_metadata_csv(csv_path: Path, custom_data_json_path: Path, cell_id: int):
    
    df = pd.read_csv(str(csv_path.resolve()))
    target_row = df[df['CellId'] == cell_id]
    name_dict_str = target_row['name_dict'][0]
    name_dict = ast.literal_eval(name_dict_str)
    # size of voxel in micrometers
    # taken not from ometiff, but from csv
    scale_micron_str = target_row['scale_micron'][0]
    scale_micron = ast.literal_eval(scale_micron_str)

    cell_stage = target_row['cell_stage'][0]

    d = {
        'name_dict': name_dict,
        # list with 3 float numbers in micrometers
        'scale_micron': scale_micron,
        'cell_stage': cell_stage
    }

    with custom_data_json_path.open("w") as fp:
        json.dump(d, fp, indent=4)

    print('Allencell metadata processed')

if __name__ == '__main__':
    process_allencell_metadata_csv(Path('preprocessor/temp/allencel_datasets/metadata/metadata.csv'), Path('preprocessor/temp/custom_data.json'), 230741)