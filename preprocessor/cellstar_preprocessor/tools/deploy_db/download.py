


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

# from _old.input_data_model import QuantizationDtype
from cellstar_db.models import InputForBuildingDatabase, RawInputFileInfo, RawInputFileResourceInfo, RawInputFilesDownloadParams
from cellstar_preprocessor.flows.common import save_dict_to_json_file
from cellstar_preprocessor.flows.constants import CSV_WITH_ENTRY_IDS_FILE, DB_BUILDING_PARAMETERS_JSON, DEFAULT_DB_PATH, RAW_INPUT_DOWNLOAD_PARAMS_JSON, RAW_INPUT_FILES_DIR, TEMP_ZARR_HIERARCHY_STORAGE_PATH
from cellstar_preprocessor.model.input import InputKind
from cellstar_preprocessor.preprocess import PreprocessorMode, main_preprocessor
from cellstar_preprocessor.tools.deploy_db.deploy_process_helper import clean_up_processes
from cellstar_preprocessor.tools.prepare_input_for_preprocessor.prepare_input_for_preprocessor import csv_to_config_list_of_dicts, json_to_list_of_inputs_for_building, prepare_input_for_preprocessor
# from preprocessor_old.main import remove_temp_zarr_hierarchy_storage_folder
# from preprocessor_old.src.preprocessors.implementations.sff.preprocessor.constants import CSV_WITH_ENTRY_IDS_FILE, DB_NAME_FOR_OME_TIFF, DEFAULT_DB_PATH, RAW_INPUT_FILES_DIR, TEMP_ZARR_HIERARCHY_STORAGE_PATH
# from preprocessor_old.src.tools.deploy_db.deploy_process_helper import clean_up_processes, clean_up_raw_input_files_dir, clean_up_temp_zarr_hierarchy_storage

# from preprocessor_old.src.tools.prepare_input_for_preprocessor.prepare_input_for_preprocessor import csv_to_config_list_of_dicts, prepare_input_for_preprocessor

PROCESS_IDS_LIST = []

def parse_script_args():
    parser=argparse.ArgumentParser()
    parser.add_argument('--raw_input_download_params', type=str, default=RAW_INPUT_DOWNLOAD_PARAMS_JSON, help='')
    parser.add_argument('--raw_input_files_dir', type=str, default=RAW_INPUT_FILES_DIR, help='dir with raw input files')
    parser.add_argument('--db_building_params_json', type=str, help='')
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
    if kind == InputKind.omezarr:
        # TODO: ome-zarr-py 
        return Path()
    else:
        # regular download
        # filename construct based on last component of uri
        filename = _get_filename_from_uri(uri)
        complete_path = final_path / filename
        final_path.mkdir(parents=True, exist_ok=True)
        req_output = urllib.request.urlretrieve(uri, complete_path.resolve())
        #  check if returns filename
        return complete_path
    
def _copy_file(uri: str, final_path: Path, kind: InputKind):
    filename = _get_filename_from_uri(uri)
    final_path.mkdir(parents=True, exist_ok=True)
    complete_path = final_path / filename
    # if omezarr - copy_tree
    if kind == InputKind.omezarr:
        shutil.copytree(uri, complete_path)
    else:
        shutil.copy2(uri, complete_path)
    
    return complete_path

def _gunzip(gz_path: Path):
    filename = gz_path.name
    gunzipped_filename = gz_path.parent / filename.split('.')[0]
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
                (complete_path.resolve(),
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
            

             
            

# # common arguments
# def _preprocessor_internal_wrapper(input_for_building: InputForBuildingDatabase, db_path: str, working_folder: str):
#     # TODO: run as function
#     # main_preprocessor
#     # before that convert some arguments types used in main_preprocessor
#     # input_for_building = defaultdict(str, input_for_building_raw)
#     quantize_downsampling_levels = None
#     if 'quantize_downsampling_levels' in input_for_building:
#         quantize_downsampling_levels = []
#         quantize_downsampling_levels = " ".join(str(item) for item in input_for_building['quantize_downsampling_levels'])
    
    
#     # TODO: replace all absent values with None
#     # if not 'quantize_dtype_str' in input_for_building:
#     #     input_for_building['quantize_dtype_str'] = None
#         # if input_for_building['quantize_dtype_str'] == 'u1':
#         #     input_for_building['quantize_dtype_str'] = QuantizationDtype.u1
#         # if input_for_building['quantize_dtype_str'] == 'u2':
#         #     input_for_building['quantize_dtype_str'] = QuantizationDtype.u2
            
#     # there is a list
#     # each item is tuple
#     # need to get two lists
#     inputs = input_for_building['inputs']
#     input_pathes_list = [Path(i[0]) for i in inputs]
#     input_kinds_list = [i[1] for i in inputs]
#     # TODO: use starmap?
#     asyncio.run(
#         main_preprocessor(
#             mode=PreprocessorMode.add,
#             quantize_dtype_str=input_for_building.get('quantize_dtype_str'),
#             quantize_downsampling_levels=quantize_downsampling_levels,
#             force_volume_dtype=input_for_building.get('force_volume_dtype'),
#             max_size_per_downsampling_lvl_mb=input_for_building.get('max_size_per_downsampling_lvl_mb'),
#             min_size_per_downsampling_lvl_mb=input_for_building.get('min_size_per_downsampling_lvl_mb'),
#             max_downsampling_level=input_for_building.get('max_downsampling_level'),
#             min_downsampling_level=input_for_building.get('min_downsampling_level'),
#             remove_original_resolution=input_for_building.get('remove_original_resolution'),
#             entry_id=input_for_building.get('entry_id'),
#             source_db=input_for_building.get('source_db'),
#             source_db_id=input_for_building.get('source_db_id'),
#             source_db_name=input_for_building.get('source_db_name'),
#             working_folder=Path(working_folder),
#             db_path=Path(db_path),
#             input_paths=input_pathes_list,
#             input_kinds=input_kinds_list,
#         )
#     )
    
    
#     # lst = [
#     #     "python", "preprocessor/main.py",
#     #     "--db_path", input,    
#     #     # "--single_entry", entry['single_entry'],
#     #     "--entry_id", entry['entry_id'],
#     #     "--source_db", entry['source_db'],
#     #     "--source_db_id", entry['source_db_id'],
#     #     "--source_db_name", entry['source_db_name']
#     # ]

#     # if entry['force_volume_dtype']:
#     #     lst.extend(['--force_volume_dtype', entry['force_volume_dtype']])
    
#     # if entry['quantization_dtype']:
#     #     lst.extend(['--quantize_volume_data_dtype_str', entry['quantization_dtype']])

#     # if entry['temp_zarr_hierarchy_storage_path']:
#     #     lst.extend(['--temp_zarr_hierarchy_storage_path', entry['temp_zarr_hierarchy_storage_path']])

#     # if entry['source_db'] == 'idr':
#     #     lst.extend(['--ome_zarr_path', entry['ome_zarr_path']])

#     # if entry['source_db'] == DB_NAME_FOR_OME_TIFF:
#     #     lst.extend(['--ome_tiff_path', entry['ome_tiff_path']])


#     # TODO: can run as function instead?
#     # process = subprocess.Popen(lst)
#     # global PROCESS_IDS_LIST
#     # PROCESS_IDS_LIST.append(process.pid)

#     # return process.communicate()

# def _preprocessor_external_wrapper(arguments_list: list[tuple[InputForBuildingDatabase, str, str]]):
#     # need to provide that input:
#     # input: InputForBuildingDatabase, db_path: str, working_folder: str
#     # as list to starmap
#     # arguments_list: list[tuple[InputForBuildingDatabase, str, str]] = []
#     with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
#         # TODO: use starmap?
#         result_iterator = p.starmap(_preprocessor_internal_wrapper, arguments_list)
#         # print(123)
    
#     p.join()

# def build(args):
#     if args.delete_existing_db and Path(args.db_path).exists():
#         shutil.rmtree(args.db_path)
        
#     if not args.temp_zarr_hierarchy_storage_path:
        
#         temp_zarr_hierarchy_storage_path = Path(TEMP_ZARR_HIERARCHY_STORAGE_PATH) / args.db_path
#     else:
#         temp_zarr_hierarchy_storage_path = Path(args.temp_zarr_hierarchy_storage_path)

#     # atexit.register(clean_up_temp_zarr_hierarchy_storage, temp_zarr_hierarchy_storage_path)

#     # here it is removed
#     if temp_zarr_hierarchy_storage_path.exists():
#         # remove_temp_zarr_hierarchy_storage_folder(temp_zarr_hierarchy_storage_path)
#         shutil.rmtree(temp_zarr_hierarchy_storage_path, ignore_errors=True)
    
#     # clean_up_raw_input_files_dir(args.raw_input_files_dir)

#     # NOTE: this function should parse JSON to list[tuple[InputForBuildingDatabase]
#     config = json_to_list_of_inputs_for_building(args.db_building_parameters_json)
#     print('JSON was parsed')
    
#     # this function should create arguments list
#     # arguments_list: list[tuple[InputForBuildingDatabase, str, str]]
#     # from parsed list of InputForBuildingDatabase
#     # and args.db_path and args temp_zarr_hierarchy_storage_path
#     arguments_list = prepare_input_for_preprocessor(config=config,
#         db_path=args.db_path,
#         temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path)
    
    
#     # print('Input files have been downloaded')
#     _preprocessor_external_wrapper(arguments_list)

#     # TODO: this should be done only after everything is build
#     shutil.rmtree(temp_zarr_hierarchy_storage_path, ignore_errors=True)

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