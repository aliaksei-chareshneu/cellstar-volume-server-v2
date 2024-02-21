import dask.array as da
import mrcfile
import numpy as np
import zarr
import nibabel as nib

from cellstar_preprocessor.flows.common import _get_ome_tiff_channel_ids, open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume.helper_methods import (
    normalize_axis_order_mrcfile,
    store_volume_data_in_zarr_stucture,
)
from cellstar_preprocessor.model.volume import InternalVolume

from pyometiff import OMETIFFReader

def ometiff_image_processing(internal_volume: InternalVolume):
    # NOTE: supports only 3D images

    zarr_structure: zarr.Group = open_zarr_structure_from_path(
        internal_volume.intermediate_zarr_structure_path
    )

    reader = OMETIFFReader(fpath=internal_volume.volume_input_path)
    img_array, metadata, xml_metadata = reader.read()
    # set map header to metadata to use it in metadata extraction
    internal_volume.custom_data = {}
    internal_volume.custom_data['ometiff_metadata'] = metadata

    print(f"Processing volume file {internal_volume.volume_input_path}")
    # TODO: this assumes array is 4D
    # could try to use metadata['SizeC'] for example
    # need to hardcode this such that it accepts only 'SizeT' == 1
    if metadata['SizeT'] > 1:
        raise Exception('SizeT > 1 is not supported')
    if (metadata['DimOrder'] == 'TZCYX'):
        # need to make it CZYX
        # CXYZ order now
        corrected_volume_arr_data = img_array[...].swapaxes(0,1).swapaxes(1,3)
    elif (metadata['DimOrder'] == 'CTZYX' or metadata['DimOrder'] == 'TCZYX'):
        # TODO: check dimensionality of array
        # metadata does not tells us dimensionality of array
        # TODO: need to do the same for segmentation?
        corrected_volume_arr_data = img_array[...].swapaxes(0,2)
        # corrected_volume_arr_data = img_array[...].swapaxes(0,1).swapaxes(1,3)
    else:
        raise Exception('DimOrder is not supported')
    
    dask_arr = da.from_array(corrected_volume_arr_data)
    # create volume data group
    volume_data_group: zarr.Group = zarr_structure.create_group(
        VOLUME_DATA_GROUPNAME
    )

    channel_ids = _get_ome_tiff_channel_ids(zarr_structure, metadata)
    # channel_names = zarr_structure.attrs['extra_data']['name_dict']['crop_raw']
    # print(f'Channel names: {channel_names}')
    
    # TODO: use metadata['SizeC']
    for channel in range(metadata['SizeC']):
        store_volume_data_in_zarr_stucture(
            data=dask_arr[channel],
            volume_data_group=volume_data_group,
            params_for_storing=internal_volume.params_for_storing,
            force_dtype=internal_volume.volume_force_dtype,
            resolution="1",
            time_frame="0",
            channel=channel_ids[channel],
            # quantize_dtype_str=internal_volume.quantize_dtype_str
        )

    print("Volume processed")
