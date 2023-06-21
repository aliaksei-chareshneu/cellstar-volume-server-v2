import numpy as np
from preprocessor_v2.preprocessor.flows.common import open_zarr_structure_from_path
from preprocessor_v2.preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from preprocessor_v2.preprocessor.flows.volume.helper_methods import normalize_axis_order_mrcfile, store_volume_data_in_zarr_stucture
from preprocessor_v2.preprocessor.model.volume import InternalVolume
import zarr
import mrcfile
import dask.array as da

def map_preprocessing(internal_volume: InternalVolume):
    '''1. normalize axis order
    2. add volume data to intermediate zarr structure
    '''
    zarr_structure: zarr.hierarchy.group = open_zarr_structure_from_path(
    internal_volume.intermediate_zarr_structure_path)
    
    with mrcfile.mmap(str(internal_volume.volume_input_path.resolve())) as mrc_original:
        data: np.memmap = mrc_original.data
        if internal_volume.volume_force_dtype is not None:
            data = data.astype(internal_volume.volume_force_dtype)
        else:
            internal_volume.volume_force_dtype = data.dtype

        header = mrc_original.header

    print(f"Processing volume file {internal_volume.volume_input_path}")
    dask_arr = da.from_array(data)
    dask_arr = normalize_axis_order_mrcfile(dask_arr=dask_arr, mrc_header=header)

    # create volume data group
    volume_data_group: zarr.hierarchy.group = zarr_structure.create_group(VOLUME_DATA_GROUPNAME)

    # TODO: check with empiar-10070 map
    if internal_volume.quantize_dtype_str and \
        (
            (internal_volume.volume_force_dtype in (np.uint8, np.int8)) or \
            ((internal_volume.volume_force_dtype in (np.uint16, np.int16)) and (internal_volume.quantize_dtype_str.value in ['u2', '|u2', '>u2', '<u2'] ))
        ):
        print(f'Quantization is skipped because input volume dtype is {internal_volume.volume_force_dtype} and requested quantization dtype is {internal_volume.quantize_dtype_str.value}')
        internal_volume.quantize_dtype_str = None


    store_volume_data_in_zarr_stucture(
        data=dask_arr,
        volume_data_group=volume_data_group,
        params_for_storing=internal_volume.params_for_storing,
        force_dtype=internal_volume.volume_force_dtype,
        resolution='1',
        time_frame='0',
        channel='0',
        quantize_dtype_str=internal_volume.quantize_dtype_str
    )

    internal_volume.map_header = header

    print('Volume processed')
    # TODO: extract metadata