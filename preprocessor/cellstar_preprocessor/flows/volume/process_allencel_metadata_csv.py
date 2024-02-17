import ast
from pathlib import Path
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
import pandas as pd
import zarr
# PLAN:

# open CSV file
# find raw with that cellId
# get channel names
# all necessary info
# put to .attrs ['allencell_metadata_csv']
# access those attrs in extract_ometiff_metadata

# pandas.read_csv

def process_allencell_metadata_csv(path: Path, cell_id: int, intermediate_zarr_structure_path: Path):
    zarr_structure: zarr.Group = open_zarr_structure_from_path(
        intermediate_zarr_structure_path
    )
    
    df = pd.read_csv(str(path.resolve()))
    target_row = df[df['CellId'] == cell_id]
    name_dict_str = target_row['name_dict'][0]
    name_dict = ast.literal_eval(name_dict_str)
    # size of voxel in micrometers
    # taken not from ometiff, but from csv
    scale_micron_str = target_row['scale_micron'][0]
    scale_micron = ast.literal_eval(scale_micron_str)

    zarr_structure.attrs['allencell_metadata_csv'] = {
        'name_dict': name_dict,
        # list with 3 float numbers in micrometers
        'scale_micron': scale_micron
    }
    print('Allencell metadata processed')