
# e.g. emd-1832 or emd_1832
import argparse
import json
from pathlib import Path
import re
import urllib.request
import os
import gzip
import shutil
import csv
from cellstar_db.models import InputForBuildingDatabase
import pandas as pd
import numpy as np

STATIC_INPUT_FILES_DIR = Path('temp/v2_temp_static_entry_files_dir')

TEST_RAW_INPUT_FILES_DIR = Path('temp/test_raw_input_files_dir')

def json_to_list_of_inputs_for_building(json_path: Path):
    with open(json_path.resolve(), "r", encoding="utf-8") as f:
            # reads into list
        read_json: list[InputForBuildingDatabase] = json.load(f)
    return read_json

def csv_to_config_list_of_dicts(csv_file_path: Path) -> list[dict]:
    df = pd.read_csv(
        str(csv_file_path.resolve()),
        converters={
            'static_input_files': lambda x: bool(int(x))
            }
        )

    df = df.replace({np.nan: None})
    df['entry_id'] = df['entry_id'].str.lower()
    list_of_dicts = df.to_dict('records')

    return list_of_dicts

    

def prepare_input_for_preprocessor(config: list[InputForBuildingDatabase], db_path: str,
    temp_zarr_hierarchy_storage_path: str) -> list[dict]:
    arguments_list = []
    for input in config:
        arguments_list.append(
            (input, Path(db_path), Path(temp_zarr_hierarchy_storage_path))
        )
    print('arguments_list')
    print(arguments_list)
    return arguments_list
    # for entry in config:
    #     entry['db_path'] = str(db_path.resolve())
    #     entry['temp_zarr_hierarchy_storage_path'] = str(temp_zarr_hierarchy_storage_path.resolve())

    #     db = re.split('-|_', entry['entry_id'])[0].lower()
    #     id = re.split('-|_', entry['entry_id'])[-1]
        
    #     emdb_folder_name = db.upper() + '-' + id
    #     emdb_map_gz_file_name = db.lower() + '_' + id + '.map.gz'
    #     # https://www.ebi.ac.uk/em_static/emdb_sff/10/1014/emd_1014.hff.gz
    #     volume_browser_gz_file_name = db.lower() + '_' + id + '.hff.gz'
    #     preprocessor_folder_name = db.lower() + '-' + id

    #     # add to json object addtional info required on preprocessing step
    #     if db == 'emd':
    #         entry['source_db'] = 'emdb'
    #     elif db == 'empiar':
    #         entry['source_db'] = 'empiar'
    #     elif db == 'idr':
    #         entry['source_db'] = 'idr'
    #     elif db == DB_NAME_FOR_OME_TIFF:
    #         entry['source_db'] = DB_NAME_FOR_OME_TIFF
    #     else:
    #         raise ValueError(f'Source db is not recognized: {db}')

    #     entry_folder = output_dir / entry['source_db'] / preprocessor_folder_name
    #     entry_folder.mkdir(parents=True, exist_ok=True)
    #     entry['single_entry'] = str(entry_folder.resolve())

    #     if entry['static_input_files'] and entry['source_db'] not in ['idr', DB_NAME_FOR_OME_TIFF]:
    #         static_segmentation_file_path = None
    #         static_folder_content = sorted((STATIC_INPUT_FILES_DIR / entry['source_db'] / preprocessor_folder_name).glob('*'))
    #         for item in static_folder_content:
    #             if item.is_file():
    #                 if item.suffix == '.hff' or item.suffix in APPLICATION_SPECIFIC_SEGMENTATION_EXTENSIONS:
    #                     static_segmentation_file_path = item
    #                     # TODO: add segmentation specific exts
    #                 elif item.suffix == '.map' or item.suffix == '.ccp4' or item.suffix == '.mrc':
    #                     static_volume_file_path: Path = item

    #         static_map_output_path = entry_folder / static_volume_file_path.name
    #         shutil.copy2(static_volume_file_path, static_map_output_path)

    #         if static_segmentation_file_path:
    #             static_sff_output_path = entry_folder / static_segmentation_file_path.name
    #             shutil.copy2(static_segmentation_file_path, static_sff_output_path)

    #     elif entry['static_input_files'] and entry['source_db'] == 'idr':
    #         # NOTE: for ome 
    #         static_ome_zarr_dir_path = None
    #         static_folder_content = sorted((STATIC_INPUT_FILES_DIR / entry['source_db'] / preprocessor_folder_name).glob('*'))
    #         for item in static_folder_content:
    #             if item.is_dir() and item.name.split('.')[1] == 'zarr':
    #                 static_ome_zarr_dir_path = item
    #                 static_ome_zarr_dir_output_path = entry_folder / static_ome_zarr_dir_path.name
    #                 entry['ome_zarr_path'] = static_ome_zarr_dir_output_path
            
    #         if not static_ome_zarr_dir_path:
    #             raise Exception('No ome zarr found')

    #         shutil.copytree(static_ome_zarr_dir_path, static_ome_zarr_dir_output_path)
    #     elif entry['static_input_files'] and entry['source_db'] == DB_NAME_FOR_OME_TIFF:
    #         static_ome_tiff_path = None
    #         static_folder_content = sorted((STATIC_INPUT_FILES_DIR / entry['source_db'] / preprocessor_folder_name).glob('*'))
    #         for item in static_folder_content:
    #             if item.is_file() and item.name.split('.')[-1] in ['tif', 'tiff']:
    #                 static_ome_tiff_path = item
    #                 static_ome_tiff_output_path = entry_folder / static_ome_tiff_path.name
    #                 entry['ome_tiff_path'] = static_ome_tiff_output_path
            
    #         if not static_ome_tiff_path:
    #             raise Exception('No ome tiff found')

    #         shutil.copy2(static_ome_tiff_path, static_ome_tiff_output_path)
    #     else:
    #         if db == 'emd':
    #             # Get map
    #             map_gz_output_path = entry_folder / emdb_map_gz_file_name
    #             map_request_output = urllib.request.urlretrieve(
    #                 f'https://ftp.ebi.ac.uk/pub/databases/emdb/structures/{emdb_folder_name}/map/{emdb_map_gz_file_name}',
    #                 str(map_gz_output_path.resolve())
    #             )

    #             with gzip.open(str(map_gz_output_path.resolve()), 'rb') as f_in:
    #                 with open(str(map_gz_output_path.with_suffix('').resolve()), 'wb') as f_out:
    #                     shutil.copyfileobj(f_in, f_out)
    #             map_gz_output_path.unlink()


    #             # get sff (.hff)
    #             sff_gz_output_path = entry_folder / volume_browser_gz_file_name

    #             # first two digits of emd ID?
    #             if len(id) == 4:
    #                 emdb_sff_prefix_number = id[0:2]
    #                 sff_request_output = urllib.request.urlretrieve(
    #                     f'https://www.ebi.ac.uk/em_static/emdb_sff/{emdb_sff_prefix_number}/{id}/{volume_browser_gz_file_name}',
    #                     str(sff_gz_output_path.resolve())
    #                 )
    #             elif len(id) == 5:
    #                 emdb_sff_prefix_number_1 = id[0:2]
    #                 emdb_sff_prefix_number_2 = id[2]
    #                 sff_request_output = urllib.request.urlretrieve(
    #                     f'https://www.ebi.ac.uk/em_static/emdb_sff/{emdb_sff_prefix_number_1}/{emdb_sff_prefix_number_2}/{id}/{volume_browser_gz_file_name}',
    #                     str(sff_gz_output_path.resolve())
    #                 )

    #             with gzip.open(str(sff_gz_output_path.resolve()), 'rb') as f_in:
    #                 with open(str(sff_gz_output_path.with_suffix('').resolve()), 'wb') as f_out:
    #                     shutil.copyfileobj(f_in, f_out)
    #             sff_gz_output_path.unlink()
        
    #     # NOTE: if one of them is not present, use source_db and entry_id
    #     if not entry['source_db_name'] or not entry['source_db_id']:
    #         entry['source_db_name'] = entry['source_db']
    #         entry['source_db_id'] = entry['entry_id']



            # elif db == 'empiar':
            #     pass
        # for sff:
        # https://www.ebi.ac.uk/em_static/emdb_sff/empiar_10087_c2_tomo02/empiar_10087_c2_tomo02.hff.gz
        # https://www.ebi.ac.uk/em_static/emdb_sff/empiar_10087_e64_tomo03/empiar_10087_e64_tomo03.hff.gz
        # https://www.ebi.ac.uk/em_static/emdb_sff/empiar_10070_b3talongmusc20130301/empiar_10070_b3talongmusc20130301.hff.gz

        # for maps
        # any API?

        # 1. 2 empiar VB entries with same ID

        # updated config list of dicts
    return config
        

if __name__ == '__main__':
    config = csv_to_config_list_of_dicts(CSV_WITH_ENTRY_IDS_FILE)
    updated_config = prepare_input_for_preprocessor(config=config, output_dir=TEST_RAW_INPUT_FILES_DIR, db_path=DEFAULT_DB_PATH, temp_zarr_hierarchy_storage_path=Path(r'dummy_temp_zarr_hierarchy_storage'))