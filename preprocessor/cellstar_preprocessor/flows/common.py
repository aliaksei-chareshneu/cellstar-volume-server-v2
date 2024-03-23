import json
import math
from pathlib import Path
import re
from typing import Union

from cellstar_db.models import ExtraData, OMETIFFSpecificExtraData
import numpy as np
import zarr

from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.model.volume import InternalVolume

import collections.abc

def _is_channels_correct(source_ometiff_metadata):
    ch = list(source_ometiff_metadata['Channels'].keys())
    number_of_channels = source_ometiff_metadata['SizeC']
    if len(ch) != number_of_channels:
        return False
    else:
        return True


def _get_ome_tiff_channel_ids_dict(root: zarr.Group, internal_volume: InternalVolume):
    # TODO: fix this part
    # if 'extra_data' in root.attrs:
    #     return root.attrs['extra_data']['name_dict']['crop_raw']
    # if internal_volume.custom_data:
        # Need to check if there is mapping provided
        # if not return artificial channel ids
        # if 'channel_ids_mapping' in internal_volume.custom_data:
    return internal_volume.custom_data['channel_ids_mapping']

    # elif 'ometiff' in internal_volume.custom_data:
    #     ometiff_custom_data: OMETIFFExtraData = internal_volume.custom_data['ometiff']
    #     ome_tiff_metadata = ometiff_custom_data['ometiff_source_metadata']
        
        
    # #     # TODO: fix this part later
    # #     if _is_channels_correct(ome_tiff_metadata):
    # #         # TODO: check if this works 
    # #         print('"Channels" in ometiff metadata are correct')
    # #         # channels is a dict
    # #         channels = ome_tiff_metadata['Channels']
    # #         # for now just return 0
    # #         # return [0]
    # #         channel_ids = []
    # #         for key in channels:
    # #             channel = channels[key]
    # #             # NOTE: assumes the order is the same?
    # #             # or parse
    # #             channel_id = channel['Name']
    # #             # channel_id = _parse_ome_tiff_channel_id(channel['ID'])
    # #             # TODO: do something like 
    # #             # 
    # #             channel_ids.append(channel_id)

    # #         return channel_ids
    # #     # get artificial ones
    #     # else:
    #     keys: list[int] = ometiff_custom_data['artificial_channel_ids']
    #     return dict(zip(str(keys), str(keys)))
        # return ometiff_custom_data['artificial_channel_ids']

def _parse_ome_tiff_channel_id(ometiff_channel_id: str):
    channel_id = re.sub(r'\W+', '', ometiff_channel_id)
    return channel_id

def set_ometiff_source_metadata(int_vol_or_seg: InternalVolume | InternalSegmentation, metadata):
    if 'dataset_specific_data' in int_vol_or_seg.custom_data:
        if 'ometiff' in int_vol_or_seg.custom_data['dataset_specific_data']:
                c: OMETIFFSpecificExtraData = int_vol_or_seg.custom_data['dataset_specific_data']['ometiff']
                c['ometiff_source_metadata'] = metadata
                int_vol_or_seg.custom_data['dataset_specific_data']['ometiff'] = c
    else:
        c: OMETIFFSpecificExtraData = {
            'ometiff_source_metadata': metadata
        }
        # if 'dataset_specific_data' in int_vol_or_seg.custom_data               
        try:
            int_vol_or_seg.custom_data['dataset_specific_data']['ometiff'] = c
        except KeyError:
            int_vol_or_seg.custom_data['dataset_specific_data'] = {
                "ometiff": c
            }

def get_ometiff_source_metadata(int_vol_or_seg: InternalVolume | InternalSegmentation):
    return int_vol_or_seg.custom_data['dataset_specific_data']['ometiff']['ometiff_source_metadata']

def set_volume_custom_data(internal_volume: InternalVolume, zarr_structure: zarr.Group):
    if 'extra_data' in zarr_structure.attrs:
        if 'volume' in zarr_structure.attrs['extra_data']:
            internal_volume.custom_data = zarr_structure.attrs['extra_data']['volume']
    else:
        internal_volume.custom_data = {}

def set_segmentation_custom_data(internal_segmentation: InternalSegmentation, zarr_structure: zarr.Group):
    if 'extra_data' in zarr_structure.attrs:
        if 'segmentation' in zarr_structure.attrs['extra_data']:
            internal_segmentation.custom_data = zarr_structure.attrs['extra_data']['segmentation']
    else:
        internal_segmentation.custom_data = {}

def process_extra_data(path: Path, intermediate_zarr_structure: Path):
    data: ExtraData = open_json_file(path)
    zarr_structure: zarr.Group = open_zarr_structure_from_path(
        intermediate_zarr_structure
    )
    zarr_structure.attrs['extra_data'] = data

def update_dict(orig_dict, new_dict: dict):
    for key, val in new_dict.items():
        if isinstance(val, collections.abc.Mapping):
            tmp = update_dict(orig_dict.get(key, { }), val)
            orig_dict[key] = tmp
        # elif isinstance(val, list):
        #     orig_dict[key] = (orig_dict.get(key, []) + val)
        else:
            orig_dict[key] = new_dict[key]
    return orig_dict


def get_downsamplings(data_group: zarr.Group) -> list[int]:
    downsamplings = []
    for gr_name, gr in data_group.groups():
        downsamplings.append(gr_name)
        downsamplings = sorted(downsamplings)

    # convert to ints
    downsamplings = sorted([int(x) for x in downsamplings])
    return downsamplings


def save_dict_to_json_file(
    d: dict | list, filename: str, path: Path
) -> None:
    with (path / filename).open("w") as fp:
        json.dump(d, fp, indent=4)

def open_json_file(path: Path):
    with open(path.resolve(), "r", encoding="utf-8") as f:
        # reads into dict
        read_file: dict | list = json.load(f)
    return read_file

def compute_downsamplings_to_be_stored(
    *,
    int_vol_or_seg: Union[InternalVolume, InternalSegmentation],
    number_of_downsampling_steps: int,
    input_grid_size: int,
    dtype: np.dtype,
    factor: int,
):
    # if min_downsampling_level and max_downsampling_level are provided,
    # list between those two numbers
    lst = [2**i for i in range(1, number_of_downsampling_steps + 1)]
    if int_vol_or_seg.downsampling_parameters.max_downsampling_level:
        lst = [
            x
            for x in lst
            if x <= int_vol_or_seg.downsampling_parameters.max_downsampling_level
        ]
    if int_vol_or_seg.downsampling_parameters.min_downsampling_level:
        lst = [
            x
            for x in lst
            if x >= int_vol_or_seg.downsampling_parameters.min_downsampling_level
        ]
    if int_vol_or_seg.downsampling_parameters.max_size_per_downsampling_lvl_mb:
        x1_filesize_bytes: int = input_grid_size * dtype.itemsize
        # num_of_downsampling_step_to_start_saving_from
        n = math.ceil(
            math.log(
                x1_filesize_bytes
                / (
                    int_vol_or_seg.downsampling_parameters.max_size_per_downsampling_lvl_mb
                    * 1024**2
                ),
                factor,
            )
        )
        lst = [x for x in lst if x >= 2**n]
        if len(lst) == 0:
            raise Exception(
                f"No downsamplings will be saved: max size per channel {int_vol_or_seg.downsampling_parameters.max_size_per_downsampling_lvl_mb} is too low"
            )

    return lst


def compute_number_of_downsampling_steps(
    *,
    int_vol_or_seg: Union[InternalVolume, InternalSegmentation],
    min_grid_size: int,
    input_grid_size: int,
    force_dtype: np.dtype,
    factor: int,
) -> int:
    num_of_downsampling_steps = 1
    if int_vol_or_seg.downsampling_parameters.max_downsampling_level:
        num_of_downsampling_steps = int(
            math.log2(int_vol_or_seg.downsampling_parameters.max_downsampling_level)
        )
    else:
        if input_grid_size <= min_grid_size:
            return 1

        x1_filesize_bytes: int = input_grid_size * force_dtype.itemsize
        num_of_downsampling_steps = int(
            math.log(
                x1_filesize_bytes
                / (
                    int_vol_or_seg.downsampling_parameters.min_size_per_downsampling_lvl_mb
                    * 10**6
                ),
                factor,
            )
        )
        if num_of_downsampling_steps <= 1:
            return 1

    return num_of_downsampling_steps


def _compute_chunk_size_based_on_data(arr: np.ndarray) -> tuple[int, int, int]:
    shape: tuple = arr.shape
    chunks = tuple([int(i / 4) if i > 4 else i for i in shape])
    return chunks


def open_zarr_zip(path: Path) -> zarr.Group:
    store = zarr.ZipStore(
        path=path,
        compression=0,
        allowZip64=True,
        mode='r'
    )
    # Re-create zarr hierarchy from opened store
    root: zarr.Group = zarr.group(store=store)
    return root

def open_zarr_structure_from_path(path: Path) -> zarr.Group:
    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(path))
    # Re-create zarr hierarchy from opened store
    root: zarr.Group = zarr.group(store=store)
    return root


def create_dataset_wrapper(
    zarr_group: zarr.Group,
    data,
    name,
    shape,
    dtype,
    params_for_storing: dict,
    is_empty=False,
) -> zarr.core.Array:
    compressor = params_for_storing.compressor
    chunking_mode = params_for_storing.chunking_mode

    if chunking_mode == "auto":
        chunks = True
    elif chunking_mode == "custom_function":
        chunks = _compute_chunk_size_based_on_data(data)
    elif chunking_mode == "false":
        chunks = False
    else:
        raise ValueError(f"Chunking approach arg value is invalid: {chunking_mode}")
    if not is_empty:
        zarr_arr = zarr_group.create_dataset(
            data=data,
            name=name,
            shape=shape,
            dtype=dtype,
            compressor=compressor,
            chunks=chunks,
        )
    else:
        zarr_arr = zarr_group.create_dataset(
            name=name, shape=shape, dtype=dtype, compressor=compressor, chunks=chunks
        )

    return zarr_arr


def decide_np_dtype(mode: str, endianness: str):
    """decides np dtype based on mode (e.g. float32) and endianness (e.g. little) provided in SFF"""
    dt = np.dtype(mode)
    dt = dt.newbyteorder(endianness)
    return dt


def chunk_numpy_arr(arr, chunk_size):
    lst = np.split(arr, np.arange(chunk_size, len(arr), chunk_size))
    return np.stack(lst, axis=0)
