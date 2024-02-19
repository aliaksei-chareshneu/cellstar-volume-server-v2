import dask.array as da
import mrcfile
import numpy as np
import zarr
import nibabel as nib

from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
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
    # TODO: reorder later if necessary according to metadata
    # (metadata['DimOrder'] == 'TZCYX')
    # need to swap axes
    # shape
    if (metadata['DimOrder'] == 'TZCYX'):
        # TODO: check dim length, no time dimension actually
        # so actually ZCYX
        # (119, 3, 281, 268)
        # need to make it CZYX
        # CXYZ order now
        corrected_volume_arr_data = img_array[...].swapaxes(0,1).swapaxes(1,3)
        dask_arr = da.from_array(corrected_volume_arr_data)
        # create volume data group
        volume_data_group: zarr.Group = zarr_structure.create_group(
            VOLUME_DATA_GROUPNAME
        )

        # TODO: account for channels
        # TODO: later get channel names from metadata.csv, now from metadata variable
        # so need to first preprocess csv to get channel 
        # first it should preprocess metadata.csv
        # get channel names
        # pass them 
        # {'crop_raw': ['dna', 'membrane', 'structure'] for crop_raw
        # channel_names = ['dna', 'membrane', 'structure']
        channel_names = zarr_structure.attrs['extra_data']['name_dict']['crop_raw']
        print(f'Channel names: {channel_names}')
        
        for channel in range(dask_arr.shape[0]):
            store_volume_data_in_zarr_stucture(
                data=dask_arr[channel],
                volume_data_group=volume_data_group,
                params_for_storing=internal_volume.params_for_storing,
                force_dtype=internal_volume.volume_force_dtype,
                resolution="1",
                time_frame="0",
                channel=channel_names[channel],
                # quantize_dtype_str=internal_volume.quantize_dtype_str
            )
    else:
        raise Exception('DimOrder is not supported')

    print("Volume processed")
