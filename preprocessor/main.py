import zarr
import argparse
import asyncio
import logging
from pprint import pprint
import shutil
from asgiref.sync import async_to_sync
import numpy as np
import numcodecs
from PIL import ImageColor
from pyometiff import OMETIFFReader

from pathlib import Path
from numcodecs import Blosc
from typing import Dict, Optional, Union
from db.file_system.db import FileSystemVolumeServerDB
from db.file_system.constants import ANNOTATION_METADATA_FILENAME, GRID_METADATA_FILENAME, SEGMENTATION_DATA_GROUPNAME, VOLUME_DATA_GROUPNAME
from db.models import Metadata
from preprocessor.params_for_storing_db import CHUNKING_MODES, COMPRESSORS
from preprocessor.src.service.implementations.preprocessor_service import PreprocessorService
from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import \
    APPLICATION_SPECIFIC_SEGMENTATION_EXTENSIONS, DEFAULT_DB_PATH, OUTPUT_FILEPATH as FAKE_SEGMENTATION_FILEPATH, PARAMETRIZED_DBS_INPUT_PARAMS_FILEPATH, RAW_INPUT_FILES_DIR, TEMP_ZARR_HIERARCHY_STORAGE_PATH

from db.protocol import VolumeServerDB
from preprocessor.src.preprocessors.implementations.sff.preprocessor.sff_preprocessor import SFFPreprocessor
from preprocessor.src.tools.convert_app_specific_segm_to_sff.convert_app_specific_segm_to_sff import convert_app_specific_segm_to_sff
from preprocessor.src.tools.remove_files_or_folders_by_pattern.remove_files_or_folders_by_pattern import remove_files_or_folders_by_pattern
from preprocessor.src.tools.write_dict_to_file.write_dict_to_json import write_dict_to_json
from preprocessor.src.tools.write_dict_to_file.write_dict_to_txt import write_dict_to_txt

OME_ZARR_DEFAULT_PATH = Path('sample_ome_zarr_from_ome_zarr_py_docs/6001240.zarr')
SPACE_UNITS_CONVERSION_DICT = {
    'micrometer': 10000,
    'angstrom': 1
}

def obtain_paths_to_single_entry_files(input_files_dir: Path) -> Dict:
    d = {}
    segmentation_file_path: Path = None
    volume_file_path: Optional[Path] = None

    if input_files_dir.is_dir():
        content = sorted(input_files_dir.glob('*'))
        for item in content:
            if item.is_file():
                if item.suffix in APPLICATION_SPECIFIC_SEGMENTATION_EXTENSIONS:
                    sff_segmentation_hff_file = convert_app_specific_segm_to_sff(input_file=item)
                    segmentation_file_path = sff_segmentation_hff_file
                elif item.suffix == '.hff':
                    segmentation_file_path = item
                elif item.suffix == '.map' or item.suffix == '.ccp4' or item.suffix == '.mrc':
                    volume_file_path = item
        if volume_file_path == None:
            raise Exception('Volume file not found')
            
        d = {
                'id': (input_files_dir.stem).lower(),
                'volume_file_path': volume_file_path,
                'segmentation_file_path': segmentation_file_path,
            }

        return d
    else:
        raise Exception('input files dir path is not directory')


def obtain_paths_to_all_files(raw_input_files_dir: Path, hardcoded=True) -> Dict:
    '''
    Returns dict where keys = source names (e.g. EMDB), values = Lists of Dicts.
    In each (sub)Dict, Path objects to volume and segmentation files are provided along with entry name.
    Both files are located in one dir (name = entry name)
    ----
    Example:
    {'emdb': [
        {
            'id': emd-1832,
            'volume_file_path': Path(...),
            'segmentation_file_path': Path(...),
        },
        {
            ...
        },
    ]}
    '''
    d = {}
    # temp implementation
    if hardcoded:
        dummy_dict = {
            'emdb': [
                {
                    'id': 'emd-1832',
                    'volume_file_path': Path(__file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'emd-1832' / 'EMD-1832.map',
                    'segmentation_file_path': Path(
                        __file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'emd-1832' / 'emd_1832.hff',
                },
                {
                    'id': 'fake-emd-1832',
                    'volume_file_path': Path(__file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'emd-1832' / 'EMD-1832.map',
                    'segmentation_file_path': FAKE_SEGMENTATION_FILEPATH,
                }
                # {
                #     'id': 'empiar_10087_c2_tomo02',
                #     'volume_file_path': Path(__file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'empiar_10087_c2_tomo02' / 'C2_tomo02.mrc',
                #     'segmentation_file_path': Path(__file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'empiar_10087_c2_tomo02' / 'empiar_10087_c2_tomo02.hff',
                # },
                # {
                #     'id': 'empiar_10087_e64_tomo03',
                #     'volume_file_path': Path(__file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'empiar_10087_e64_tomo03' / 'E64_tomo03.mrc',
                #     'segmentation_file_path': Path(__file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'emd-empiar_10087_e64_tomo03' / 'empiar_10087_e64_tomo03.hff',
                # }
            ]
        }
        d = dummy_dict
    else:
        # all ids should be lowercase!
        # TODO: later this dict can be compiled during batch raw file download, it should be easier than doing it like this
        for dir_path in raw_input_files_dir.iterdir():
            if dir_path.is_dir():
                source_db = (dir_path.stem).lower()
                d[source_db] = []
                for subdir_path in dir_path.iterdir():
                    single_entry_dict = obtain_paths_to_single_entry_files(input_files_dir=subdir_path)        
                    d[source_db].append(single_entry_dict)
    return d


async def preprocess_everything(db: VolumeServerDB, raw_input_files_dir: Path, params_for_storing: dict, temp_zarr_hierarchy_storage_path: Path) -> None:
    preprocessor_service = PreprocessorService([SFFPreprocessor(temp_zarr_hierarchy_storage_path)])
    files_dict = obtain_paths_to_all_files(raw_input_files_dir, hardcoded=False)
    for source_name, source_entries in files_dict.items():
        for entry in source_entries:
            # check if entry exists
            if await db.contains(namespace=source_name, key=entry['id']):
                await db.delete(namespace=source_name, key=entry['id'])

            segm_file_type = preprocessor_service.get_raw_file_type(entry['segmentation_file_path'])
            file_preprocessor = preprocessor_service.get_preprocessor(segm_file_type)
            # for now np.float32 by default, after mrcfile guys will confirm that map is read according to mode - could be None
            processed_data_temp_path = file_preprocessor.preprocess(
                segm_file_path=entry['segmentation_file_path'],
                volume_file_path=entry['volume_file_path'],
                volume_force_dtype=None,
                params_for_storing=params_for_storing,
                entry_id=entry['id'],
                source_db_id=entry['id'],
                source_db_name=source_name
            )
            await db.store(namespace=source_name, key=entry['id'], temp_store_path=processed_data_temp_path)

async def preprocess_single_entry(db: VolumeServerDB, input_files_dir: Path, params_for_storing: dict, entry_id: str, source_db: str, force_volume_dtype: Union[str, None],
        temp_zarr_hierarchy_storage_path: Path,
        source_db_id: str,
        source_db_name: str) -> None:
    preprocessor_service = PreprocessorService([SFFPreprocessor(temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path)])
    if await db.contains(namespace=source_db, key=entry_id):
        await db.delete(namespace=source_db, key=entry_id)

    files_dict = obtain_paths_to_single_entry_files(input_files_dir)

    segm_file_type = preprocessor_service.get_raw_file_type(files_dict['segmentation_file_path'])
    file_preprocessor = preprocessor_service.get_preprocessor(segm_file_type)

    if force_volume_dtype is not None:
        try:
            force_volume_dtype = np.dtype(force_volume_dtype)
        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
            raise e

    processed_data_temp_path = file_preprocessor.preprocess(
        segm_file_path=files_dict['segmentation_file_path'],
        volume_file_path=files_dict['volume_file_path'],
        volume_force_dtype=force_volume_dtype,
        params_for_storing=params_for_storing,
        entry_id=entry_id,
        source_db_id=source_db_id,
        source_db_name=source_db_name
    )
    await db.store(namespace=source_db, key=entry_id, temp_store_path=processed_data_temp_path)
    
async def check_read_slice(db: VolumeServerDB):
    box = ((0, 0, 0), (10, 10, 10), (10, 10, 10))
    
    with db.read(namespace='emdb', key='emd-99999') as reader:
        slice_emd_99999 = await reader.read_slice(
            lattice_id=0,
            down_sampling_ratio=1,
            box=box
        )

    with db.read(namespace='emdb', key='emd-1832') as reader:
        slice_emd_1832 = await reader.read_slice(
            lattice_id=0,
            down_sampling_ratio=1,
            box=box
        )

    emd_1832_volume_slice = slice_emd_1832['volume_slice']
    emd_1832_segm_slice = slice_emd_1832['segmentation_slice']['category_set_ids']

    emd_99999_volume_slice = slice_emd_99999['volume_slice']

    print(f'volume slice_emd_1832 shape: {emd_1832_volume_slice.shape}, dtype: {emd_1832_volume_slice.dtype}')
    print(emd_1832_volume_slice)
    print(f'segmentation slice_emd_1832 shape: {emd_1832_segm_slice.shape}, dtype: {emd_1832_segm_slice.dtype}')
    print(emd_1832_segm_slice)
    print()
    print(f'volume slice_emd_99999 shape: {emd_99999_volume_slice.shape}, dtype: {emd_99999_volume_slice.dtype}')
    print(emd_99999_volume_slice)
    # print(slice)
    return {
        'slice_emd_1832': slice_emd_1832,
        'slice_emd_99999': slice_emd_99999
    }

async def check_read_meshes(db: VolumeServerDB):
    with db.read(namespace='empiar', key='empiar-10070') as reader:
        read_meshes_list = await reader.read_meshes(
            segment_id=15,
            detail_lvl=3
        )

    pprint(read_meshes_list)

    return read_meshes_list

def create_dict_of_input_params_for_storing(chunking_mode: list, compressors: list) -> dict:
    i = 1
    d = {}
    for mode in chunking_mode:
        for compressor in compressors:
            d[i] = {
                'chunking_mode': mode,
                'compressor': compressor,
                'store_type': 'directory'
            }
            i = i + 1
    
    return d

def remove_temp_zarr_hierarchy_storage_folder(path: Path):
    shutil.rmtree(path, ignore_errors=True)

async def create_db(db_path: Path, params_for_storing: dict,
    raw_input_files_dir_path: Path,
    temp_zarr_hierarchy_storage_path: Path):
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    remove_temp_zarr_hierarchy_storage_folder(temp_zarr_hierarchy_storage_path)
    db = FileSystemVolumeServerDB(new_db_path, params_for_storing['store_type'])
    # db.remove_all_entries()
    await preprocess_everything(db, raw_input_files_dir_path, params_for_storing=params_for_storing,
        temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path)

async def add_entry_to_db(
        db_path: Path,
        params_for_storing: dict,
        input_files_dir: Path,
        entry_id: str,
        source_db: str,
        force_volume_dtype: Union[str, None],
        temp_zarr_hierarchy_storage_path: Path,
        source_db_id: str,
        source_db_name: str):
    '''
    By default, initializes db with store_type = "zip"
    '''
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    # NOTE: with this multiprocessing in deployement script may not work, so commented
    # remove_temp_zarr_hierarchy_storage_folder(TEMP_ZARR_HIERARCHY_STORAGE_PATH)
    db = FileSystemVolumeServerDB(new_db_path, store_type='zip')
    await preprocess_single_entry(
        db=db,
        input_files_dir=input_files_dir,
        params_for_storing=params_for_storing,
        entry_id=entry_id,
        source_db=source_db,
        force_volume_dtype=force_volume_dtype,
        temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path,
        source_db_id=source_db_id,
        source_db_name=source_db_name
        )

def _compose_voxel_sizes_in_downsamplings_dict(ome_zarr_root):
    root_zattrs = ome_zarr_root.attrs
    multiscales = root_zattrs["multiscales"]
    datasets_meta = multiscales[0]["datasets"]

    labels_datasets_meta = ome_zarr_root['labels'][0].attrs['multiscales'][0]["datasets"]

    d = {}
    
    for index, level in enumerate(datasets_meta):
        scale_arr = level['coordinateTransformations'][0]['scale']
        # check if multiscales in labels are the same
        assert scale_arr == labels_datasets_meta[index]['coordinateTransformations'][0]['scale']
        # no channel, *micrometers to angstroms
        scale_arr = scale_arr[1:]
        scale_arr = [i*10000 for i in scale_arr]
        # x and z swapped
        d[level['path']] = (
            scale_arr[2],
            scale_arr[1],
            scale_arr[0]
        )

    return d

def get_origins(ome_zarr_attrs, boxes_dict: dict):
    multiscales = ome_zarr_attrs["multiscales"]
    # NOTE: can be multiple multiscales, here picking just 1st
    axes = multiscales[0]['axes']
    datasets_meta = multiscales[0]["datasets"]
    for index, level in enumerate(datasets_meta):
        if len(level['coordinateTransformations']) == 2 and level['coordinateTransformations'][1]['type'] == 'translation':
            translation_arr = level['coordinateTransformations'][1]['translation']

            # instead of swapaxes, -1, -2, -3
            boxes_dict[level['path']]['origin'] = [
                translation_arr[-1],
                translation_arr[-2],
                translation_arr[-3]
            ]
        else:
            boxes_dict[level['path']]['origin'] = [0, 0, 0]

    # apply global

    if 'coordinateTransformations' in multiscales[0]:
        if multiscales[0]['coordinateTransformations'][1]['type'] == 'translation':
            global_translation_arr = multiscales[0]['coordinateTransformations'][1]['translation']
            global_translation_arr = global_translation_arr[-3:]
            global_translation_arr[0], global_translation_arr[2] = global_translation_arr[2], global_translation_arr[0]
            
            for resolution in boxes_dict:
                boxes_dict[resolution]['origin'] = [a+b for a, b in zip(
                    boxes_dict[resolution]['origin'],
                    global_translation_arr
                )]

    # convert to angstroms
    for resolution in boxes_dict:
        boxes_dict[resolution]['origin'][0] = _convert_to_angstroms(
            boxes_dict[resolution]['origin'][0],
            input_unit=axes[-1]['unit'])
        boxes_dict[resolution]['origin'][1] = _convert_to_angstroms(
            boxes_dict[resolution]['origin'][1],
            input_unit=axes[-2]['unit'])
        boxes_dict[resolution]['origin'][2] = _convert_to_angstroms(
            boxes_dict[resolution]['origin'][2],
            input_unit=axes[-3]['unit'])
    

    return boxes_dict

def _convert_hex_to_rgba_fractional(channel_color_hex):
    channel_color_rgba = ImageColor.getcolor(f'#{channel_color_hex}', "RGBA")
    channel_color_rgba_fractional = tuple([i/255 for i in channel_color_rgba])
    return channel_color_rgba_fractional

def get_channel_annotations(ome_zarr_attrs, volume_channel_annotations):
    for channel_id, channel in enumerate(ome_zarr_attrs['omero']['channels']):
        volume_channel_annotations.append(
            {
                'channel_id': channel_id,
                'color': _convert_hex_to_rgba_fractional(channel['color']),
                'label': channel['label']
            }
        )
        # volume_channel_annotations_dict['colors'][str(channel_id)] = _convert_hex_to_rgba_fractional(channel['color'])
        # volume_channel_annotations_dict['labels'][str(channel_id)] = channel['label']

# TODO: add support for time transformations applied to all resolution
def get_time_transformations(ome_zarr_attrs, time_transformations_list: list):
    multiscales = ome_zarr_attrs["multiscales"]
    # NOTE: can be multiple multiscales, here picking just 1st
    axes = multiscales[0]['axes']
    datasets_meta = multiscales[0]["datasets"]
    if axes[0]['name'] == 't':
        for index, level in enumerate(datasets_meta):
            scale_arr = level['coordinateTransformations'][0]['scale']
            if len(scale_arr) == 5:
                factor = scale_arr[0]
                if 'coordinateTransformations' in multiscales[0]:
                    if multiscales[0]['coordinateTransformations'][0]['type'] == 'scale':
                        factor = factor * multiscales[0]['coordinateTransformations'][0]['scale'][0]
                time_transformations_list.append(
                    {
                        'downsampling_level': level['path'],
                        'factor': factor
                    }
                )
            else:
                raise Exception('Length of scale arr is not supported')
        return time_transformations_list
    else:
        return time_transformations_list

def get_voxel_sizes_in_downsamplings(ome_zarr_attrs, boxes_dict):
    multiscales = ome_zarr_attrs["multiscales"]
    datasets_meta = multiscales[0]["datasets"]
    axes = multiscales[0]['axes']
    
    for index, level in enumerate(datasets_meta):
        scale_arr = level['coordinateTransformations'][0]['scale']
        if len(scale_arr) == 5:
            scale_arr = scale_arr[2:]
        elif len(scale_arr) == 4:
            scale_arr = scale_arr[1:]
        else:
            raise Exception('Length of scale arr is not supported')

        # x and z swapped
        boxes_dict[level['path']]['voxel_size'] = [
            _convert_to_angstroms(scale_arr[2], input_unit=axes[-1]['unit']),
            _convert_to_angstroms(scale_arr[1], input_unit=axes[-2]['unit']),
            _convert_to_angstroms(scale_arr[0], input_unit=axes[-3]['unit'])
        ]


        if 'coordinateTransformations' in multiscales[0]:
            if multiscales[0]['coordinateTransformations'][0]['type'] == 'scale':
                global_scale_arr = multiscales[0]['coordinateTransformations'][0]['scale']
                if len(global_scale_arr) == 5:
                    global_scale_arr = global_scale_arr[2:]
                elif len(global_scale_arr) == 4:
                    global_scale_arr = global_scale_arr[1:]
                else:
                    raise Exception('Length of scale arr is not supported')
                boxes_dict[level['path']]['voxel_size'][0] = boxes_dict[level['path']]['voxel_size'][0] * global_scale_arr[2]
                boxes_dict[level['path']]['voxel_size'][1] = boxes_dict[level['path']]['voxel_size'][1] * global_scale_arr[1]
                boxes_dict[level['path']]['voxel_size'][2] = boxes_dict[level['path']]['voxel_size'][2] * global_scale_arr[0]
            else:
                raise Exception('First transformation should be of scale type')



    return boxes_dict

def _convert_to_angstroms(value, input_unit: str):
    # TODO: support other units
    if input_unit in SPACE_UNITS_CONVERSION_DICT:
        return value*SPACE_UNITS_CONVERSION_DICT[input_unit]
    else:
        raise Exception(f'{input_unit} space unit is not supported')


def get_time_units(ome_zarr_attrs):
    # NOTE: default is milliseconds if time axes is not present
    multiscales = ome_zarr_attrs["multiscales"]
    # NOTE: can be multiple multiscales, here picking just 1st
    axes = multiscales[0]['axes']
    if axes[0]['name'] == 't':
        # NOTE: may not have it, then we default to ms
        if 'unit' in axes[0]:
            return axes[0]['unit']
        else:
            return "millisecond"
    else:
        return "millisecond"

def _get_downsamplings(data_group) -> list:
    volume_downsamplings = []
    for gr_name, gr in data_group.groups():
        volume_downsamplings.append(gr_name)
        volume_downsamplings = sorted(volume_downsamplings)

    # convert to ints
    volume_downsamplings = sorted([int(x) for x in volume_downsamplings])
    return volume_downsamplings

def _get_channel_ids(time_data_group, segmentation_data=False) -> list:
    if segmentation_data:
        channel_ids = sorted(time_data_group.group_keys())
    else:
        channel_ids = sorted(time_data_group.array_keys())
    channel_ids = sorted(int(x) for x in channel_ids)

    return channel_ids

def _get_start_end_time(resolution_data_group) -> tuple[int, int]:
    time_intervals = sorted(resolution_data_group.group_keys())
    time_intervals = sorted(int(x) for x in time_intervals)
    start_time = min(time_intervals)
    end_time = max(time_intervals)
    return (start_time, end_time)

def _get_volume_sampling_info(root_data_group, sampling_info_dict):
    for res_gr_name, res_gr in root_data_group.groups():
        # create layers (time gr, channel gr)
        sampling_info_dict['boxes'][res_gr_name] = {
            'origin': None,
            'voxel_size': None,
            'grid_dimensions': None,
            # 'force_dtype': None
        }
        
        sampling_info_dict['descriptive_statistics'][res_gr_name] = {}


        

        for time_gr_name, time_gr in res_gr.groups():
            first_group_key = sorted(time_gr.array_keys())[0]

            sampling_info_dict['boxes'][res_gr_name]['grid_dimensions'] = time_gr[first_group_key].shape
            # sampling_info_dict['boxes'][res_gr_name]['force_dtype'] = time_gr[first_group_key].dtype.str
            
            sampling_info_dict['descriptive_statistics'][res_gr_name][time_gr_name] = {}
            for channel_arr_name, channel_arr in time_gr.arrays():
                assert sampling_info_dict['boxes'][res_gr_name]['grid_dimensions'] == channel_arr.shape
                # assert sampling_info_dict['boxes'][res_gr_name]['force_dtype'] == channel_arr.dtype.str

                arr_view = channel_arr[...]
                # if QUANTIZATION_DATA_DICT_ATTR_NAME in arr.attrs:
                #     data_dict = arr.attrs[QUANTIZATION_DATA_DICT_ATTR_NAME]
                #     data_dict['data'] = arr_view
                #     arr_view = decode_quantized_data(data_dict)
                #     if isinstance(arr_view, da.Array):
                #         arr_view = arr_view.compute()

                mean_val = float(str(np.mean(arr_view)))
                std_val = float(str(np.std(arr_view)))
                max_val = float(str(arr_view.max()))
                min_val = float(str(arr_view.min()))

                sampling_info_dict['descriptive_statistics']\
                    [res_gr_name][time_gr_name][channel_arr_name] = {
                    'mean': mean_val,
                    'std': std_val,
                    'max': max_val,
                    'min': min_val,
                }

def _get_segmentation_sampling_info(root_data_group, sampling_info_dict):
    for res_gr_name, res_gr in root_data_group.groups():
        # create layers (time gr, channel gr)
        sampling_info_dict['boxes'][res_gr_name] = {
            'origin': None,
            'voxel_size': None,
            'grid_dimensions': None,
            # 'force_dtype': None
        }

        for time_gr_name, time_gr in res_gr.groups():
            first_group_key = sorted(time_gr.group_keys())[0]

            sampling_info_dict['boxes'][res_gr_name]['grid_dimensions'] = time_gr[first_group_key].grid.shape
            
            for channel_gr_name, channel_gr in time_gr.groups():
                assert sampling_info_dict['boxes'][res_gr_name]['grid_dimensions'] == channel_gr.grid.shape



def _get_source_axes_units(ome_zarr_root_attrs: zarr.hierarchy.group):
    d = {}
    multiscales = ome_zarr_root_attrs["multiscales"]
    # NOTE: can be multiple multiscales, here picking just 1st
    axes = multiscales[0]['axes']
    for axis in axes:
        if not 'unit' in axis or axis['type'] != 'channel':
            d[axis['name']] = None
        else:
            d[axis['name']] = axis['unit']
    
    return d

def _add_defaults_to_ome_zarr_attrs(ome_zarr_root: zarr.hierarchy.group):
    # TODO: try put/update
    # 1. add units to axes
    # NOTE: can be multiple multiscales, here picking just 1st
    d = ome_zarr_root.attrs.asdict()
    for axis in d["multiscales"][0]['axes']:
        if not 'unit' in axis:
            if axis['type'] == 'space':
                axis['unit'] = 'angstrom'
            if axis['type'] == 'time':
                axis['unit'] = 'millisecond'

    return d

def extract_ome_zarr_metadata(our_zarr_structure: zarr.hierarchy.group,
        source_db_id: str,
        source_db_name: str,
        ome_zarr_root: zarr.hierarchy.group) -> Metadata:
    root = our_zarr_structure


    new_volume_attrs_dict = _add_defaults_to_ome_zarr_attrs(ome_zarr_root=ome_zarr_root)
    ome_zarr_root.attrs.put(new_volume_attrs_dict)

    # ome_zarr_root = _add_defaults_to_ome_zarr_attrs(ome_zarr_root=ome_zarr_root)

    volume_downsamplings = _get_downsamplings(data_group=root[VOLUME_DATA_GROUPNAME])
    channel_ids = _get_channel_ids(time_data_group=root[VOLUME_DATA_GROUPNAME][0][0])
    start_time, end_time = _get_start_end_time(resolution_data_group=root[VOLUME_DATA_GROUPNAME][0])

    # time_scale_factors = get_time_scale_factors(ome_zarr_root)

    # 1. Collect common metadata
    metadata_dict = {
        'entry_id': {
            'source_db_name': source_db_name,
            'source_db_id': source_db_id

        },
        'volumes': {
            'channel_ids': channel_ids,
            # Values of time dimension
            'time_info': {
                'kind': "range",
                'start': start_time,
                'end': end_time,
                'units': get_time_units(ome_zarr_attrs=ome_zarr_root.attrs)
            },
            'volume_sampling_info': {
                # Info about "downsampling dimension"
                'spatial_downsampling_levels': volume_downsamplings,
                # the only thing with changes with SPATIAL downsampling is box!
                'boxes': {},
                # time -> channel_id
                'descriptive_statistics': {},
                'time_transformations': [],
                'source_axes_units': _get_source_axes_units(ome_zarr_root_attrs=ome_zarr_root.attrs)
            }
        },
        'segmentation_lattices': {
            'segmentation_lattice_ids': [],
            'segmentation_sampling_info': {},
            'channel_ids': {},
            'time_info': {}
        },
        'segmentation_meshes': {
            'mesh_component_numbers': {},
            'detail_lvl_to_fraction': {}
        }
    }
    
    get_time_transformations(ome_zarr_attrs=ome_zarr_root.attrs,
        time_transformations_list=metadata_dict['volumes']['volume_sampling_info']['time_transformations'])

    _get_volume_sampling_info(root_data_group=root[VOLUME_DATA_GROUPNAME],
        sampling_info_dict=metadata_dict['volumes']['volume_sampling_info'])

    get_origins(ome_zarr_attrs=ome_zarr_root.attrs,
        boxes_dict=metadata_dict['volumes']['volume_sampling_info']['boxes'])
    get_voxel_sizes_in_downsamplings(ome_zarr_attrs=ome_zarr_root.attrs,
        boxes_dict=metadata_dict['volumes']['volume_sampling_info']['boxes'])


    # lattice_dict = {}
    lattice_ids = []

    if SEGMENTATION_DATA_GROUPNAME in root:
        for label_gr_name, label_gr in root[SEGMENTATION_DATA_GROUPNAME].groups():
            new_segm_attrs_dict = _add_defaults_to_ome_zarr_attrs(ome_zarr_root=ome_zarr_root.labels[label_gr_name])
            ome_zarr_root.labels[label_gr_name].attrs.put(new_segm_attrs_dict)

            # each label group is lattice id
            lattice_id = label_gr_name

            # segm_downsamplings = sorted(label_gr.group_keys())
            # # convert to ints
            # segm_downsamplings = sorted([int(x) for x in segm_downsamplings])
            # lattice_dict[str(lattice_id)] = segm_downsamplings
            
            lattice_ids.append(lattice_id)

            metadata_dict['segmentation_lattices']['segmentation_sampling_info'][str(lattice_id)] = {
                # Info about "downsampling dimension"
                'spatial_downsampling_levels': volume_downsamplings,
                # the only thing with changes with SPATIAL downsampling is box!
                'boxes': {},
                'time_transformations': [],
                'source_axes_units': _get_source_axes_units(ome_zarr_root_attrs=ome_zarr_root.labels[str(label_gr_name)].attrs)
            }
            get_time_transformations(ome_zarr_attrs=ome_zarr_root.labels[str(label_gr_name)].attrs,
                time_transformations_list=metadata_dict['segmentation_lattices']['segmentation_sampling_info'][str(lattice_id)]['time_transformations'])
            _get_segmentation_sampling_info(root_data_group=label_gr,
                sampling_info_dict=metadata_dict['segmentation_lattices']['segmentation_sampling_info'][str(lattice_id)])

            get_origins(ome_zarr_attrs=ome_zarr_root.labels[str(label_gr_name)].attrs,
                boxes_dict=metadata_dict['segmentation_lattices']['segmentation_sampling_info'][str(lattice_id)]['boxes'])
            get_voxel_sizes_in_downsamplings(ome_zarr_attrs=ome_zarr_root.labels[str(label_gr_name)].attrs,
                boxes_dict=metadata_dict['segmentation_lattices']['segmentation_sampling_info'][str(lattice_id)]['boxes'])

            segm_channel_ids = _get_channel_ids(time_data_group=label_gr[0][0], segmentation_data=True)
            metadata_dict['segmentation_lattices']['channel_ids'][label_gr_name] = segm_channel_ids
            
            segm_start_time, segm_end_time = _get_start_end_time(resolution_data_group=label_gr[0])
            metadata_dict['segmentation_lattices']['time_info'][label_gr_name] = {
                'kind': "range",
                'start': segm_start_time,
                'end': segm_end_time,
                'units': get_time_units(ome_zarr_attrs=ome_zarr_root.labels[str(label_gr_name)].attrs)
            }

        metadata_dict['segmentation_lattices']['segmentation_lattice_ids'] = lattice_ids

    return metadata_dict

# NOTE: Lattice IDs = Label groups
def extract_ome_zarr_annotations(ome_zarr_root, source_db_id: str, source_db_name: str):
    d = {
        'entry_id': {
            'source_db_name': source_db_name,
            'source_db_id': source_db_id
        },
        # 'segment_list': [],
        'segmentation_lattices': [],
        'details': None,
        'volume_channels_annotations': []
    }
    # segment_list = d['segment_list']

    get_channel_annotations(ome_zarr_attrs=ome_zarr_root.attrs,
        volume_channel_annotations=d['volume_channels_annotations'])

    if 'labels' in ome_zarr_root:    
        for label_gr_name, label_gr in ome_zarr_root.labels.groups():
            segmentation_lattice_info = {
                "lattice_id": label_gr_name,
                "segment_list": []
            }
            labels_metadata_list = label_gr.attrs['image-label']['colors']
            for ind_label_meta in labels_metadata_list:
                label_value = ind_label_meta['label-value']
                ind_label_color_rgba = ind_label_meta['rgba']
                ind_label_color_fractional = [i/255 for i in ind_label_color_rgba]

                segmentation_lattice_info["segment_list"].append(
                    {
                        "id": int(label_value),
                        "biological_annotation": {
                            "name": f"segment {label_value}",
                            "description": None,
                            "number_of_instances": None,
                            "external_references": [
                            ]
                        },
                        "color": ind_label_color_fractional,
                    }
                )
            # append
            d['segmentation_lattices'].append(segmentation_lattice_info)

            

    return d

def extract_ome_tiff_annotations(ome_tiff_metadata, source_db_id: str, source_db_name: str):
    d = {
        'entry_id': {
            'source_db_name': source_db_name,
            'source_db_id': source_db_id
        },
        # 'segment_list': [],
        'segmentation_lattices': [],
        'details': None,
        'volume_channels_annotations': []
    }

    get_ome_tiff_channel_annotations(ome_tiff_metadata=ome_tiff_metadata,
        volume_channel_annotations=d['volume_channels_annotations'])

    return d

def process_ome_tiff(ome_tiff_path, temp_zarr_hierarchy_storage_path, source_db_id, source_db_name):
    reader = OMETIFFReader(fpath=ome_tiff_path)
    img_array, metadata, xml_metadata = reader.read()

    entry_id = source_db_name + '-' + source_db_id
    our_zarr_structure_path = temp_zarr_hierarchy_storage_path / entry_id
    our_zarr_structure = zarr.open_group(our_zarr_structure_path, mode='w')

    # PROCESSING VOLUME
    volume_data_gr = our_zarr_structure.create_group(VOLUME_DATA_GROUPNAME)
    # NOTE: no pyramids in sample ome tiff, so resolution group = 0
    # NOTE: time and channel = 1
    resolution_group = volume_data_gr.create_group('0')
    time_group = resolution_group.create_group('0')

    # TODO: function to determine how to reorder dimensions in array
    if metadata['DimOrder'] == 'TCZYX' or metadata['DimOrder'] == 'CTZYX':
        corrected_volume_arr_data = img_array[...].swapaxes(0,2)
        our_channel_arr = time_group.create_dataset(
            # channel also 0
            name='0',
            shape=corrected_volume_arr_data.shape,
            data=corrected_volume_arr_data
        )

    # TODO: extract grid_metadata and annotation_metadata
    grid_metadata = extract_ome_tiff_metadata(
        source_db_id=source_db_id,
        source_db_name=source_db_name,
        ome_tiff_metadata=metadata
    )

    annotation_metadata = extract_ome_tiff_annotations(
        ome_tiff_metadata=metadata,
        source_db_id=source_db_id,
        source_db_name=source_db_name,
    )

    SFFPreprocessor.temp_save_metadata(grid_metadata, GRID_METADATA_FILENAME, our_zarr_structure_path)
    SFFPreprocessor.temp_save_metadata(annotation_metadata, ANNOTATION_METADATA_FILENAME, our_zarr_structure_path)

    return our_zarr_structure
    # TODO: channel can contain color, see: https://www.openmicroscopy.org/Schemas/Documentation/Generated/OME-2016-06/ome.html
    # <Channel AcquisitionMode="" Color="-1"
    # but our files does not contain it
    # default #FFFFFFFF

def _get_ome_tiff_channel_ids(ome_tiff_metadata):
    channels = ome_tiff_metadata['Channels']
    # for now just return 0
    return [0]


def extract_ome_tiff_metadata(
        source_db_id: str,
        source_db_name: str,
        ome_tiff_metadata):
    
    channel_ids = _get_ome_tiff_channel_ids(ome_tiff_metadata)
    start_time = 0
    end_time = 0
    # no time units data in metadata
    time_units = 'millisecond'
    volume_downsamplings = [0]
    source_axes_units = {}

    metadata_dict = {
        'entry_id': {
            'source_db_name': source_db_name,
            'source_db_id': source_db_id

        },
        'volumes': {
            'channel_ids': channel_ids,
            # Values of time dimension
            'time_info': {
                'kind': "range",
                'start': start_time,
                'end': end_time,
                'units': time_units
            },
            'volume_sampling_info': {
                # Info about "downsampling dimension"
                'spatial_downsampling_levels': volume_downsamplings,
                # the only thing with changes with SPATIAL downsampling is box!
                'boxes': {},
                # time -> channel_id
                'descriptive_statistics': {},
                'time_transformations': [],
                'source_axes_units': source_axes_units
            }
        },
        'segmentation_lattices': {
            'segmentation_lattice_ids': [],
            'segmentation_sampling_info': {},
            'channel_ids': {},
            'time_info': {}
        },
        'segmentation_meshes': {
            'mesh_component_numbers': {},
            'detail_lvl_to_fraction': {}
        }
    }

    return metadata_dict
    

def get_ome_tiff_channel_annotations(ome_tiff_metadata, volume_channel_annotations):
    for key in ome_tiff_metadata['Channels']:
        channel = ome_tiff_metadata['Channels'][key]
        channel_id = channel['ID']
        # for now FFFFFFF
        color = 'FFFFFF'
        # TODO: check how it is encoded in some sample
        # if channel['Color']:
        #     color = _convert_hex_to_rgba_fractional(channel['Color'])
        label = channel_id
        if 'Name' in channel:
            label = channel['Name']

        volume_channel_annotations.append(
            {
                'channel_id': channel_id,
                'color': color,
                'label': label
            }
        )
        

# returns zarr structure to be stored with db.store
# NOTE: just one channel
def process_ome_zarr(ome_zarr_path, temp_zarr_hierarchy_storage_path, source_db_id, source_db_name):
    ome_zarr_root = zarr.open_group(ome_zarr_path)
    
    entry_id = source_db_name + '-' + source_db_id
    our_zarr_structure_path = temp_zarr_hierarchy_storage_path / entry_id
    our_zarr_structure = zarr.open_group(temp_zarr_hierarchy_storage_path / entry_id, mode='w')

    # PROCESSING VOLUME
    volume_data_gr = our_zarr_structure.create_group(VOLUME_DATA_GROUPNAME)
    root_zattrs = ome_zarr_root.attrs
    multiscales = root_zattrs["multiscales"]
    # NOTE: can be multiple multiscales, here picking just 1st
    axes = multiscales[0]['axes']
    for volume_arr_resolution, volume_arr in ome_zarr_root.arrays():
        # if time is first and there are 5 axes = read as it is, create groups accordingly
        # if there are 4 axes - add time group
        # if there are 3 axes - check if 1st is time
        # if yes, create 1st layer groups from it, 2nd layer group = 1, in 3rd layer
        # create array with added Z dimension = 1
        # if not time - create 1st and 2nd layer groups == 1

        resolution_group = volume_data_gr.create_group(volume_arr_resolution)
        if len(axes) == 5 and axes[0]['name'] == 't':
            for i in range(volume_arr.shape[0]):
                time_group = resolution_group.create_group(str(i))
                for j in range(volume_arr.shape[1]):
                    corrected_volume_arr_data = volume_arr[...][i][j].swapaxes(0,2)
                    our_channel_arr = time_group.create_dataset(
                        name=j,
                        shape=corrected_volume_arr_data.shape,
                        data=corrected_volume_arr_data
                    )
        elif len(axes) == 4 and axes[0]['name'] == 'c':
            time_group = resolution_group.create_group('0')
            for j in range(volume_arr.shape[0]):
                corrected_volume_arr_data = volume_arr[...][j].swapaxes(0,2)
                our_channel_arr = time_group.create_dataset(
                    name=j,
                    shape=corrected_volume_arr_data.shape,
                    data=corrected_volume_arr_data
                )
        # TODO: later
        # elif len(axes) == 3:
        #     if axes[0] == 't':
        #         pass
        #     else:
        #         pass
        else:
            raise Exception('Axes number/order is not recognized')
        
        



    

    
    # PROCESSING SEGMENTATION
    segmentation_data_gr = our_zarr_structure.create_group(SEGMENTATION_DATA_GROUPNAME)
    
    # Lattice IDs = Label groups
    if 'labels' in ome_zarr_root:
        for label_gr_name, label_gr in ome_zarr_root.labels.groups():
            lattice_id_gr = segmentation_data_gr.create_group(label_gr_name)
            # arr_name is resolution
            for arr_name, arr in label_gr.arrays():
                our_resolution_gr = lattice_id_gr.create_group(arr_name)
                if len(axes) == 5 and axes[0]['name'] == 't':
                    for i in range(arr.shape[0]):
                        time_group = our_resolution_gr.create_group(str(i))
                        for j in range(arr.shape[1]):
                            corrected_arr_data = arr[...][i][j].swapaxes(0,2)
                            # i8 is not supported by CIFTools
                            if corrected_arr_data.dtype == 'i8':
                                corrected_arr_data = corrected_arr_data.astype('i4')
                            our_channel_group = time_group.create_group(str(j))
                            our_arr = our_channel_group.create_dataset(
                                name='grid',
                                shape=corrected_arr_data.shape,
                                data=corrected_arr_data
                            )

                            our_set_table = our_channel_group.create_dataset(
                                name='set_table',
                                dtype=object,
                                object_codec=numcodecs.JSON(),
                                shape=1
                            )

                            d = {}
                            for value in np.unique(our_arr[...]):
                                d[str(value)] = [int(value)]

                            our_set_table[...] = [d]

                elif len(axes) == 4 and axes[0]['name'] == 'c':
                    time_group = our_resolution_gr.create_group('0')
                    for j in range(arr.shape[0]):
                        corrected_arr_data = arr[...][j].swapaxes(0,2)
                        if corrected_arr_data.dtype == 'i8':
                            corrected_arr_data = corrected_arr_data.astype('i4')
                        our_channel_group = time_group.create_group(str(j))
                        our_arr = our_channel_group.create_dataset(
                            name='grid',
                            shape=corrected_arr_data.shape,
                            data=corrected_arr_data
                        )

                        our_set_table = our_channel_group.create_dataset(
                            name='set_table',
                            dtype=object,
                            object_codec=numcodecs.JSON(),
                            shape=1
                        )

                        d = {}
                        for value in np.unique(our_arr[...]):
                            d[str(value)] = [int(value)]

                        our_set_table[...] = [d]

        
        
        

    grid_metadata = extract_ome_zarr_metadata(
        our_zarr_structure=our_zarr_structure,
        source_db_id=source_db_id,
        source_db_name=source_db_name,
        ome_zarr_root=ome_zarr_root
    )

    annotation_metadata = extract_ome_zarr_annotations(
        ome_zarr_root=ome_zarr_root,
        source_db_id=source_db_id,
        source_db_name=source_db_name
    )

    SFFPreprocessor.temp_save_metadata(grid_metadata, GRID_METADATA_FILENAME, our_zarr_structure_path)
    SFFPreprocessor.temp_save_metadata(annotation_metadata, ANNOTATION_METADATA_FILENAME, our_zarr_structure_path)

    # need 3D dataset
    return our_zarr_structure

async def store_ome_zarr_structure(db_path, temp_ome_zarr_structure, source_db, entry_id):
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    db = FileSystemVolumeServerDB(new_db_path, store_type='zip')
    await db.store(namespace=source_db, key=entry_id, temp_store_path=Path(temp_ome_zarr_structure.store.path))

async def store_ome_tiff_structure(db_path, temp_ome_tiff_structure, source_db, entry_id):
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    db = FileSystemVolumeServerDB(new_db_path, store_type='zip')
    await db.store(namespace=source_db, key=entry_id, temp_store_path=Path(temp_ome_tiff_structure.store.path))


async def main():
    args = parse_script_args()
    

    if args.raw_input_files_dir_path:
        raw_input_files_dir_path = args.raw_input_files_dir_path
    else:
        raise ValueError('No raw input files dir path is provided as argument')
    
    if args.temp_zarr_hierarchy_storage_path:
        temp_zarr_hierarchy_storage_path = args.temp_zarr_hierarchy_storage_path
    else:
        # raise ValueError('No temp_zarr_hierarchy_storage_path is provided as argument')
        temp_zarr_hierarchy_storage_path = TEMP_ZARR_HIERARCHY_STORAGE_PATH / args.db_path.name
        
    # NOTE: not maintained currently (outdated arg numbers etc.)
    if args.create_parametrized_dbs:
        # TODO: add quantize and raw input files dir path here too
        remove_files_or_folders_by_pattern('db_*/')
        storing_params_dict = create_dict_of_input_params_for_storing(
            chunking_mode=CHUNKING_MODES,
            compressors=COMPRESSORS
        )
        write_dict_to_txt(storing_params_dict, PARAMETRIZED_DBS_INPUT_PARAMS_FILEPATH)
        for db_id, param_set in storing_params_dict.items():
            await create_db(Path(f'db_{db_id}'), params_for_storing=param_set,
                temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path)
    elif args.db_path:
        # print(args.quantize_volume_data_dtype_str)
        params_for_storing={
            'chunking_mode': 'auto',
            'compressor': Blosc(cname='lz4', clevel=5, shuffle=Blosc.SHUFFLE, blocksize=0),
            'store_type': 'zip'
        }
        if args.quantize_volume_data_dtype_str:
            params_for_storing['quantize_dtype_str'] = args.quantize_volume_data_dtype_str

        if args.single_entry:
            if args.entry_id and args.source_db and args.source_db_id and args.source_db_name:
                if args.ome_tiff_path:
                    # do ome tiff thing
                    zarr_structure_to_be_saved = process_ome_tiff(
                        ome_tiff_path=args.ome_tiff_path,
                        temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path,
                        source_db_id=args.source_db_id,
                        source_db_name=args.source_db_name)
                    await store_ome_tiff_structure(args.db_path, zarr_structure_to_be_saved, args.source_db, args.entry_id)
                    print(1)
                elif args.ome_zarr_path:
                    # do ome zarr thing
                    zarr_structure_to_be_saved = process_ome_zarr(
                        ome_zarr_path=args.ome_zarr_path,
                        temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path,
                        source_db_id=args.source_db_id,
                        source_db_name=args.source_db_name)
                    await store_ome_zarr_structure(args.db_path, zarr_structure_to_be_saved, args.source_db, args.entry_id)
                    print(1)
                else:
                    single_entry_folder_path = args.single_entry
                    single_entry_id = args.entry_id
                    single_entry_source_db = args.source_db

                    if args.force_volume_dtype:
                        force_volume_dtype = args.force_volume_dtype
                    else:
                        force_volume_dtype = None

                    await add_entry_to_db(
                        Path(args.db_path),
                        params_for_storing=params_for_storing,
                        input_files_dir=single_entry_folder_path,
                        entry_id=single_entry_id,
                        source_db=single_entry_source_db,
                        force_volume_dtype=force_volume_dtype,
                        temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path,
                        source_db_id=args.source_db_id,
                        source_db_name=args.source_db_name
                        )
            else:
                raise ValueError('args.entry_id and args.source_db and args.source_db_id and args.source_db_name are required for single entry mode')
        else:
            await create_db(Path(args.db_path),
                params_for_storing=params_for_storing,
                raw_input_files_dir_path=raw_input_files_dir_path,
                temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path)
    else:
        raise ValueError('No db path is provided as argument')

def parse_script_args():
    parser=argparse.ArgumentParser()
    parser.add_argument("--db_path", type=Path, default=DEFAULT_DB_PATH, help='path to db folder')
    parser.add_argument("--raw_input_files_dir_path", type=Path, default=RAW_INPUT_FILES_DIR, help='path to directory with input files (maps and sff)')
    parser.add_argument("--create_parametrized_dbs", action='store_true')
    parser.add_argument("--quantize_volume_data_dtype_str", action="store", choices=['u1', 'u2'])
    parser.add_argument('--single_entry', type=Path, help='path to folder with MAP and segmentation files')
    parser.add_argument('--entry_id', type=str, help='entry id to be used as DB folder name')
    parser.add_argument('--source_db', type=str, help='source database name to be used as DB folder name')
    parser.add_argument('--force_volume_dtype', type=str, help='dtype of volume data to be used')
    parser.add_argument("--temp_zarr_hierarchy_storage_path", type=Path, help='path to db working directory')
    parser.add_argument('--source_db_id', type=str, help='actual source db id for metadata')
    parser.add_argument('--source_db_name', type=str, help='actual source db name for metadata')
    parser.add_argument('--ome_zarr_path', type=Path)
    parser.add_argument('--ome_tiff_path', type=Path)
    args=parser.parse_args()
    return args

if __name__ == '__main__':
    asyncio.run(main())


    # uncomment to check read slice method
    # asyncio.run(check_read_slice(db))

    # uncomment to check read_meshes method
    # asyncio.run(check_read_meshes(db))

    # event loop works, while async to sync returns Metadata class
    # https://stackoverflow.com/questions/44048536/python3-get-result-from-async-method
    # metadata = async_to_sync(db.read_metadata)(namespace='emdb', key='emd-1832')
    # print(metadata)

    # lat_ids = metadata.segmentation_lattice_ids()
    # segm_dwnsmplings = metadata.segmentation_downsamplings(lat_ids[0])
    # volume_downsamplings = metadata.volume_downsamplings()
    # origin = metadata.origin()
    # voxel_size = metadata.volume_downsamplings()
    # grid_dimensions = metadata.grid_dimensions()

    # print(lat_ids)
    # print(segm_dwnsmplings)
    # print(volume_downsamplings)
    # print(origin)
    # print(voxel_size)
    # print(grid_dimensions)
