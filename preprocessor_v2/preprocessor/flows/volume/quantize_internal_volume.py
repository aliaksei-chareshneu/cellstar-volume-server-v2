import numpy as np
from preprocessor_v2.preprocessor.flows.common import open_zarr_structure_from_path
from preprocessor_v2.preprocessor.flows.constants import QUANTIZATION_DATA_DICT_ATTR_NAME, VOLUME_DATA_GROUPNAME
from preprocessor_v2.preprocessor.model.volume import InternalVolume
import zarr
import dask.array as da

from preprocessor_v2.preprocessor.tools.quantize_data.quantize_data import quantize_data

# TODO: quantization for each level separately
def quantize_internal_volume(internal_volume: InternalVolume):
    if internal_volume.quantize_dtype_str and \
        (
            (internal_volume.volume_force_dtype in (np.uint8, np.int8)) or \
            ((internal_volume.volume_force_dtype in (np.uint16, np.int16)) and (internal_volume.quantize_dtype_str.value in ['u2', '|u2', '>u2', '<u2'] ))
        ):
        print(f'Quantization is skipped because input volume dtype is {internal_volume.volume_force_dtype} and requested quantization dtype is {internal_volume.quantize_dtype_str.value}')
        internal_volume.quantize_dtype_str = None
    
    if not internal_volume.quantize_dtype_str:
        raise Exception('No quantize dtype is provided')
    else:
        quantize_dtype_str = internal_volume.quantize_dtype_str

    zarr_structure: zarr.hierarchy.group = open_zarr_structure_from_path(
        internal_volume.intermediate_zarr_structure_path)
    
    # iterate over all arrays
    # create dask array
    for resolution, res_gr in zarr_structure[VOLUME_DATA_GROUPNAME].groups():
        for time, time_gr in res_gr.groups():
            for channel_arr_name, channel_arr in time_gr.arrays():
                data = da.from_array(channel_arr)


                quantized_data_dict = quantize_data(
                    data=data,
                    output_dtype=quantize_dtype_str.value)
                
                data = quantized_data_dict["data"]
                
                quantized_data_dict_without_data = quantized_data_dict.copy()
                quantized_data_dict_without_data.pop('data')

                # save this dict as attr of zarr arr
                channel_arr.attrs[QUANTIZATION_DATA_DICT_ATTR_NAME] = quantized_data_dict_without_data

                # TODO: fix arr dtype
                da.to_zarr(arr=data, url=channel_arr, overwrite=True, compute=True)

    print('Volume quantized')
