


import argparse
import asyncio
import atexit
from collections import defaultdict
import gzip
import json
import multiprocessing
import os
import shutil
import subprocess
from pathlib import Path
import urllib.request
import ome_zarr

# from _old.input_data_model import QuantizationDtype
from cellstar_db.models import InputForBuildingDatabase, RawInputFileInfo, RawInputFileResourceInfo, RawInputFilesDownloadParams
from cellstar_preprocessor.flows.common import save_dict_to_json_file
from cellstar_preprocessor.flows.constants import CSV_WITH_ENTRY_IDS_FILE, DB_BUILDING_PARAMETERS_JSON, DEFAULT_DB_PATH, RAW_INPUT_DOWNLOAD_PARAMS_JSON, RAW_INPUT_FILES_DIR, TEMP_ZARR_HIERARCHY_STORAGE_PATH
from cellstar_preprocessor.model.input import InputKind
from cellstar_preprocessor.preprocess import PreprocessorMode, main_preprocessor
from cellstar_preprocessor.tools.deploy_db.deploy_process_helper import clean_up_processes
from cellstar_preprocessor.tools.prepare_input_for_preprocessor.prepare_input_for_preprocessor import csv_to_config_list_of_dicts, json_to_list_of_inputs_for_building, prepare_input_for_preprocessor
import ome_zarr.utils
# from preprocessor_old.main import remove_temp_zarr_hierarchy_storage_folder
# from preprocessor_old.src.preprocessors.implementations.sff.preprocessor.constants import CSV_WITH_ENTRY_IDS_FILE, DB_NAME_FOR_OME_TIFF, DEFAULT_DB_PATH, RAW_INPUT_FILES_DIR, TEMP_ZARR_HIERARCHY_STORAGE_PATH
# from preprocessor_old.src.tools.deploy_db.deploy_process_helper import clean_up_processes, clean_up_raw_input_files_dir, clean_up_temp_zarr_hierarchy_storage

# from preprocessor_old.src.tools.prepare_input_for_preprocessor.prepare_input_for_preprocessor import csv_to_config_list_of_dicts, prepare_input_for_preprocessor

PROCESS_IDS_LIST = []

def parse_script_args():
    parser=argparse.ArgumentParser()
    parser.add_argument('--raw_input_download_params', type=str, default=RAW_INPUT_DOWNLOAD_PARAMS_JSON, help='')
    parser.add_argument('--raw_input_files_dir', type=str, default=RAW_INPUT_FILES_DIR, help='dir with raw input files')
    parser.add_argument('--db_building_params_json', type=str, default=DB_BUILDING_PARAMETERS_JSON, help='')
    # parser.add_argument("--db_path", type=str, default=DEFAULT_DB_PATH, help='path to db folder')
    # parser.add_argument("--temp_zarr_hierarchy_storage_path", type=str, default=TEMP_ZARR_HIERARCHY_STORAGE_PATH, help='path to db working directory')
    # parser.add_argument("--delete_existing_db", action='store_true', default=False, help='remove existing db directory')
    args=parser.parse_args()
    return args

def _parse_raw_input_download_params_file(path: Path):
    with open(path.resolve(), "r", encoding="utf-8") as f:
        # reads into dict
        json_params: list[RawInputFilesDownloadParams] = json.load(f)

    return json_params

def _get_filename_from_uri(uri: str):
    parsed = uri.split('/')
    filename = parsed[-1]
    return filename

def _download(uri: str, final_path: Path, kind: InputKind):
    filename = _get_filename_from_uri(uri)
    # difference is that it should use final_path
    if kind == InputKind.omezarr:
        complete_path = final_path / filename
        if complete_path.exists():
            shutil.rmtree(complete_path)
        
        # NOTE: using final_path here as it requires the directory inside
        # of which another directory will be created (idr-XXXX.zarr)
        ome_zarr.utils.download(uri, str(final_path.resolve()))
        return complete_path
    else:
        # regular download
        # filename construct based on last component of uri
        complete_path = final_path / filename
        if complete_path.exists():
            shutil.rmtree(complete_path)
        final_path.mkdir(parents=True, exist_ok=True)    
        req_output = urllib.request.urlretrieve(uri, str(complete_path.resolve()))
        #  check if returns filename
        return complete_path
    
def _copy_file(uri: str, final_path: Path, kind: InputKind):
    filename = _get_filename_from_uri(uri)
    if final_path.exists():
        shutil.rmtree(final_path)
    final_path.mkdir(parents=True)
    complete_path = final_path / filename
    # if omezarr - copy_tree
    if kind == InputKind.omezarr:
        shutil.copytree(uri, complete_path)
    else:
        shutil.copy2(uri, complete_path)
    
    return complete_path

def _gunzip(gz_path: Path):
    # only maps
    filename = gz_path.name
    gunzipped_filename = gz_path.parent / filename.removesuffix('.gz')
    with gzip.open(str(gz_path.resolve()), 'rb') as f_in:
        # bytes?
        # NOTE: only map gz is supported, therefore bytes
        with open(str(gunzipped_filename.resolve()), 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    gz_path.unlink()
    
    return gunzipped_filename

def _get_file(input_file_info: RawInputFileInfo, final_path: Path) -> Path:
    resource = input_file_info['resource']
    if resource['kind'] == 'external':
        complete_path = _download(input_file_info['resource']['uri'], final_path, input_file_info['kind'])
        return complete_path
    elif resource['kind'] == 'local':
        complete_path = _copy_file(resource['uri'], final_path, input_file_info['kind'])
        # shutil.copy2(resource['uri'], final_path)
        return complete_path

def download(args: argparse.Namespace):
    db_building_params: list[InputForBuildingDatabase] = []
    
    raw_unput_files_dir = Path(args.raw_input_files_dir)
    download_params_file_path = Path(args.raw_input_download_params)
    download_params = _parse_raw_input_download_params_file(download_params_file_path)
    
    # Pathes:
    # raw_input_files_dir / source / entry id / kind / files
    for item in download_params:
        entry_folder_path = raw_unput_files_dir / item['source_db'] / item['entry_id']
        # several files
        raw_inputs = item['inputs']
        # create inputs_list
        # tuple str path, inputKind
        inputs_list: list[tuple[str, InputKind]] = []
        
        for raw_input in raw_inputs:
            kind = raw_input['kind']
            final_path = entry_folder_path / kind
            
            complete_path = _get_file(raw_input, final_path)
            
            # gunzip if needed
            if complete_path.suffix == '.gz':
                complete_path = _gunzip(complete_path)
            
            inputs_list.append(
                # TODO:
                # TODO:
                # TODO:
                # need to make it relative to cellstar dev dir?
                (str(complete_path.resolve()),
                kind)
            )
            
        input_for_building_db: InputForBuildingDatabase = {
            'entry_id': item['entry_id'],
            'source_db': item['source_db'],
            'source_db_id': item['source_db_id'],
            'source_db_name': item['source_db_name'],
            'inputs': inputs_list
        }
        # TODO: compile an object with data for building db
            
        db_building_params.append(input_for_building_db)
        
    return db_building_params
            

def _store_db_building_params_to_json(db_building_params: list[InputForBuildingDatabase], args: argparse.Namespace):
    filename = Path(args.db_building_params_json).name
    folder = Path(args.db_building_params_json).parent
    save_dict_to_json_file(db_building_params, filename, folder)
    

# test-data\preprocessor\download_raw_input_params.json
if __name__ == '__main__':
    # print("DEFAULT PORTS ARE TEMPORARILY SET TO 4000 and 8000, CHANGE THIS AFTERWARDS")
    atexit.register(clean_up_processes, PROCESS_IDS_LIST)
    args = parse_script_args()
    db_building_params = download(args)
    _store_db_building_params_to_json(db_building_params, args)
    # store it to json