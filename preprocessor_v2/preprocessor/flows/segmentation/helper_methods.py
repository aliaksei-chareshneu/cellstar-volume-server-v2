import logging
from pathlib import Path
import shutil

import h5py
import numcodecs
import zarr

import base64
import zlib

import numpy as np

from preprocessor_v2.preprocessor.flows.common import decide_np_dtype
from preprocessor_v2.preprocessor.flows.segmentation.category_set_downsampling_methods import store_downsampling_levels_in_zarr
from preprocessor_v2.preprocessor.flows.segmentation.downsampling_level_dict import DownsamplingLevelDict
from preprocessor_v2.preprocessor.flows.segmentation.segmentation_set_table import SegmentationSetTable


temp_zarr_structure_path = None


def hdf5_to_zarr(intermediate_zarr_structure_path: Path, file_path: Path):
    '''
    Creates temp zarr structure mirroring that of hdf5
    '''
    global temp_zarr_structure_path
    temp_zarr_structure_path = intermediate_zarr_structure_path
    try:
        # assert temp_zarr_structure_path.exists() == False, \
        #     f'temp_zarr_structure_path: {temp_zarr_structure_path} already exists'
        # store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(temp_zarr_structure_path))
        # # directory store does not need to be closed, zip does
        hdf5_file: h5py.File = h5py.File(file_path, mode='r')
        hdf5_file.visititems(__visitor_function)
        hdf5_file.close()
    except Exception as e:
        logging.error(e, stack_info=True, exc_info=True)
        raise e


def __visitor_function(name: str, node: h5py.Dataset) -> None:
    '''
    Helper function used to create zarr hierarchy based on hdf5 hierarchy from sff file
    Takes nodes one by one and depending of their nature (group/object dataset/non-object dataset)
    creates the corresponding zarr hierarchy element (group/array)
    '''
    global temp_zarr_structure_path
    # input hdf5 file may be too large for memory, so we save it in temp storage
    node_name = node.name[1:]
    if isinstance(node, h5py.Dataset):
        # for text-based fields, including lattice data (as it is b64 encoded zlib-zipped sequence)
        if node.dtype == 'object':
            data = [node[()]]
            arr = zarr.array(data, dtype=node.dtype, object_codec=numcodecs.MsgPack())
            zarr.save_array(temp_zarr_structure_path / node_name, arr, object_codec=numcodecs.MsgPack())
        else:
            arr = zarr.open_array(temp_zarr_structure_path / node_name, mode='w', shape=node.shape,
                                  dtype=node.dtype)
            arr[...] = node[()]
    elif isinstance(node, h5py.Group):
        zarr.open_group(temp_zarr_structure_path / node_name, mode='w')
    else:
        raise Exception('h5py node is neither dataset nor group')


def lattice_data_to_np_arr(data: str, mode: str, endianness: str, arr_shape: tuple[int, int, int]) -> np.ndarray:
    '''
    Converts lattice data to np array.
    Under the hood, decodes lattice data into zlib-zipped data, decompress it to bytes,
    and converts to np arr based on dtype (sff mode), endianness and shape (sff size)
    '''
    try:
        decoded_data = base64.b64decode(data)
        byteseq = zlib.decompress(decoded_data)
        np_dtype = decide_np_dtype(mode=mode, endianness=endianness)
        arr = np.frombuffer(byteseq, dtype=np_dtype).reshape(arr_shape, order='F')
    except Exception as e:
        logging.error(e, stack_info=True, exc_info=True)
        raise e
    return arr

def decode_base64_data(data: str, mode: str, endianness: str):
    try:
        # TODO: decode any data, take into account endiannes
        decoded_data = base64.b64decode(data)
        np_dtype = decide_np_dtype(mode=mode, endianness=endianness)
        arr = np.frombuffer(decoded_data, dtype=np_dtype)
    except Exception as e:
        logging.error(e, stack_info=True, exc_info=True)
        raise e
    return arr

def map_value_to_segment_id(zarr_structure):
    '''
    Iterates over zarr structure and returns dict with
    keys=lattice_id, and for each lattice id => keys=grid values, values=segm ids
    '''
    root = zarr_structure
    d = {}
    for segment_name, segment in root.segment_list.groups():
        lat_id = int(segment.three_d_volume.lattice_id[...])
        value = int(segment.three_d_volume.value[...])
        segment_id = int(segment.id[...])
        if lat_id not in d:
            d[lat_id] = {}
        d[lat_id][value] = segment_id
    # print(d)
    return d

def store_segmentation_data_in_zarr_structure(
        original_data: np.ndarray,
        lattice_data_group: zarr.hierarchy.Group,
        value_to_segment_id_dict_for_specific_lattice_id: dict,
        params_for_storing: dict
    ):
# TODO: params
# TODO: procedure from create_category_set_downsamplings
    # table with just singletons, e.g. "104": {104}, "94" :{94}
    initial_set_table = SegmentationSetTable(original_data, value_to_segment_id_dict_for_specific_lattice_id)

    # just x1 downsampling lvl dict
    levels = [
        DownsamplingLevelDict({'ratio': 1, 'grid': original_data, 'set_table': initial_set_table})
    ]
    
    # store levels list in zarr structure (can be separate function)
    store_downsampling_levels_in_zarr(levels, lattice_data_group, params_for_storing=params_for_storing,
                                      time_frame='0',
                                      channel='0')
