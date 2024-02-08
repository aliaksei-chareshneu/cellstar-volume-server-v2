from cellstar_preprocessor.model.segmentation import InternalSegmentation
import dask.array as da
import mrcfile
import numpy as np
import zarr
import nibabel as nib
import gc
import numcodecs


from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME, VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume.helper_methods import (
    normalize_axis_order_mrcfile,
    store_volume_data_in_zarr_stucture,
)
from cellstar_preprocessor.model.volume import InternalVolume

from pyometiff import OMETIFFReader

def ometiff_segmentation_processing(internal_segmentation: InternalSegmentation):
    # NOTE: supports only 3D images

    zarr_structure: zarr.Group = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )

    reader = OMETIFFReader(fpath=internal_segmentation.segmentation_input_path)
    img_array, metadata, xml_metadata = reader.read()
    # set map header to metadata to use it in metadata extraction
    internal_segmentation.custom_data = metadata

    print(f"Processing segmentation file {internal_segmentation.segmentation_input_path}")
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
        corrected_arr_data_with_channel = img_array[...].swapaxes(0,1).swapaxes(1,3)
        # dask_arr = da.from_array(corrected_arr_data)
        # create volume data group
        segmentation_data_gr = zarr_structure.create_group(LATTICE_SEGMENTATION_DATA_GROUPNAME)

        # NOTE: several lattices, as channels
        # NOTE: artificially create set table and grid
        # similar to omezarr labels processing


        # TODO: account for channels
        # TODO: later get channel names from metadata.csv, now from metadata variable
        # so need to first preprocess csv to get channel 
        # first it should preprocess metadata.csv
        # get channel names
        # pass them 
        # {'crop_raw': ['dna', 'membrane', 'structure'] for crop_raw
        # channel_names = ['dna', 'membrane', 'structure']
        channel_names = zarr_structure.attrs['allencell_metadata_csv']['name_dict']['crop_seg']
        print(f'Channel names: {channel_names}')
        
        for channel in range(corrected_arr_data_with_channel.shape[0]):
            corrected_arr_data = corrected_arr_data_with_channel[channel]
            lattice_id_gr = segmentation_data_gr.create_group(channel_names[channel])

            # NOTE: single resolution
            resolution_gr = lattice_id_gr.create_group('1')

            # NOTE: single timeframe
            time_group = resolution_gr.create_group('0')

            our_arr = time_group.create_dataset(
                name="grid",
                shape=corrected_arr_data.shape,
                data=corrected_arr_data,
            )

            our_set_table = time_group.create_dataset(
                name="set_table",
                dtype=object,
                object_codec=numcodecs.JSON(),
                shape=1,
            )

            d = {}
            for value in np.unique(our_arr[...]):
                d[str(value)] = [int(value)]

            our_set_table[...] = [d]

            del corrected_arr_data
            gc.collect()
    else:
        raise Exception('DimOrder is not supported')

    print("Segmentation processed")
