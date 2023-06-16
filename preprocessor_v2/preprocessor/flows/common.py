from pathlib import Path
import zarr
import numpy as np
from preprocessor_v2.preprocessor.model.segmentation import InternalSegmentation

from preprocessor_v2.preprocessor.model.volume import InternalVolume

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

def extract_metadata_from_map_and_sff(internal_volume: InternalVolume, internal_segmentation: InternalSegmentation):
    '''Extracts metadata'''
    pass

def decide_np_dtype(mode: str, endianness: str):
    '''decides np dtype based on mode (e.g. float32) and endianness (e.g. little) provided in SFF
    '''
    dt = np.dtype(mode)
    dt = dt.newbyteorder(endianness)
    return dt