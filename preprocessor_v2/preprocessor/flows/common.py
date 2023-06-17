import math
from pathlib import Path
from typing import Union
import zarr
import numpy as np
from preprocessor_v2.preprocessor.model.segmentation import InternalSegmentation

from preprocessor_v2.preprocessor.model.volume import InternalVolume

def compute_downsamplings_to_be_stored(*, int_vol_or_seg: Union[InternalVolume, InternalSegmentation], number_of_downsampling_steps: int,
                                       input_grid_size: int, dtype: np.dtype, factor: int):
    # if min_downsampling_level and max_downsampling_level are provided,
    # list between those two numbers
    lst = [2**i for i in range(1, number_of_downsampling_steps + 1)]
    if int_vol_or_seg.downsampling_parameters.max_downsampling_level:
        lst = [x for x in lst if x <= int_vol_or_seg.downsampling_parameters.max_downsampling_level]
    if int_vol_or_seg.downsampling_parameters.min_downsampling_level:
        lst = [x for x in lst if x >= int_vol_or_seg.downsampling_parameters.min_downsampling_level]
    if int_vol_or_seg.downsampling_parameters.max_size_per_channel_mb:
        x1_filesize_bytes: int = input_grid_size * dtype.itemsize
        # num_of_downsampling_step_to_start_saving_from
        n = math.ceil(math.log(
            x1_filesize_bytes / (int_vol_or_seg.downsampling_parameters.max_size_per_channel_mb * 1024**2),
            factor)
        )
        lst = [x for x in lst if x >= 2**n]
        if len(lst) == 0:
            raise Exception(f'No downsamplings will be saved: max size per channel {int_vol_or_seg.downsampling_parameters.max_size_per_channel_mb} is too high')


    return lst

def compute_number_of_downsampling_steps(*, int_vol_or_seg: Union[InternalVolume, InternalSegmentation],
                                        min_grid_size: int, input_grid_size: int, force_dtype: np.dtype, factor: int) -> int:
    num_of_downsampling_steps = 1
    if int_vol_or_seg.downsampling_parameters.max_downsampling_level:
        num_of_downsampling_steps = int(math.log2(int_vol_or_seg.downsampling_parameters.max_downsampling_level))
    else:
        if input_grid_size <= min_grid_size:
            return 1
   
        x1_filesize_bytes: int = input_grid_size * force_dtype.itemsize
        num_of_downsampling_steps = int(math.log(
            x1_filesize_bytes / (int_vol_or_seg.downsampling_parameters.min_size_per_channel_mb * 10**6),
            factor
        ))
        if num_of_downsampling_steps <= 1:
            return 1

    return num_of_downsampling_steps

def _compute_chunk_size_based_on_data(arr: np.ndarray) -> tuple[int, int, int]:
    shape: tuple = arr.shape
    chunks = tuple([int(i/4) if i > 4 else i for i in shape])
    return chunks

def open_zarr_structure_from_path(path: Path) -> zarr.hierarchy.Group:
    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(path))
    # Re-create zarr hierarchy from opened store
    root: zarr.hierarchy.group = zarr.group(store=store)
    return root

def create_dataset_wrapper(
        zarr_group: zarr.hierarchy.group,
        data,
        name,
        shape,
        dtype,
        params_for_storing: dict,
        is_empty=False
    ) -> zarr.core.Array:

    compressor = params_for_storing.compressor
    chunking_mode = params_for_storing.chunking_mode

    if chunking_mode == 'auto':
        chunks = True
    elif chunking_mode == 'custom_function':
        chunks = _compute_chunk_size_based_on_data(data)
    elif chunking_mode == 'false':
        chunks = False
    else:
        raise ValueError(f'Chunking approach arg value is invalid: {chunking_mode}')
    if not is_empty:
        zarr_arr = zarr_group.create_dataset(
            data=data,
            name=name,
            shape=shape,
            dtype=dtype,
            compressor=compressor,
            chunks=chunks
        )
    else:
        zarr_arr = zarr_group.create_dataset(
            name=name,
            shape=shape,
            dtype=dtype,
            compressor=compressor,
            chunks=chunks
        )

    return zarr_arr

def extract_metadata_from_map_and_sff(int_vol_or_seg: InternalVolume, internal_segmentation: InternalSegmentation):
    '''Extracts metadata'''
    pass

def decide_np_dtype(mode: str, endianness: str):
    '''decides np dtype based on mode (e.g. float32) and endianness (e.g. little) provided in SFF
    '''
    dt = np.dtype(mode)
    dt = dt.newbyteorder(endianness)
    return dt