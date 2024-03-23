from typing import TypedDict
from cellstar_db.models import OMETIFFSpecificExtraData, VolumeExtraData
from cellstar_preprocessor.model.segmentation import InternalSegmentation
import dask.array as da
import mrcfile
import numpy as np
import zarr
import nibabel as nib

from cellstar_preprocessor.flows.common import _get_ome_tiff_channel_ids_dict, _is_channels_correct, open_zarr_structure_from_path, set_ometiff_source_metadata, set_volume_custom_data
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume.helper_methods import (
    normalize_axis_order_mrcfile,
    store_volume_data_in_zarr_stucture,
)
from cellstar_preprocessor.model.volume import InternalVolume

from pyometiff import OMETIFFReader

class PreparedOMETIFFData(TypedDict):
    time: int
    # channel would be int
    # TODO: get its name later on
    channel_number: int
    data: np.ndarray

def _create_reorder_tuple(d: dict, correct_order: str):
    reorder_tuple = tuple([d[l] for l in correct_order])
    return reorder_tuple

def _get_missing_dims(sizesBF: list[int]):
    sizesBFcorrected = sizesBF[1:]
    missing = []
    order = 'TZCYX'
    for idx, dim in enumerate(sizesBFcorrected):
        if dim == 1:
            missing.append(order[idx])
    print(f'Missing dims: {missing}')
    return missing 

def prepare_ometiff_for_writing(img_array: np.ndarray, metadata, int_vol_or_seg: InternalVolume | InternalSegmentation):
    prepared_data: list[PreparedOMETIFFData] = []

    d = {}
    order = metadata['DimOrder BF Array']
    for letter in order:
        d[str(letter)] = order.index(str(letter))


    missing_dims = []

    if len(img_array.shape) != 5:
        local_d = {
            'T': 0,
            'Z': 1,
            'C': 2,
            'Y': 3,
            'X': 4
        }
        missing_dims = _get_missing_dims(metadata['Sizes BF'])
        for missing_dim in missing_dims:
            img_array = np.expand_dims(img_array, axis=local_d[missing_dim])

        d = local_d

    CORRECT_ORDER = 'TCXYZ'
    reorder_tuple = _create_reorder_tuple(d, CORRECT_ORDER)
    # NOTE: assumes correct order is TCXYZ
    
    custom_data = int_vol_or_seg.custom_data

    # if 'dataset_specific_data' in custom_data:
    #     if 'ometiff' in custom_data['dataset_specific_data']:
    #         if 'missing_dimensions' in custom_data['dataset_specific_data']['ometiff']:
                # may not exist if no missing dimension
                # ometiff_custom_data: OMETIFFSpecificExtraData = custom_data['dataset_specific_data']['ometiff']
                # missing_dims: list[str] = ometiff_custom_data['missing_dimensions']

    # if 'extra_data' in zarr_structure.attrs:
    #     if 'missing_dimensions' in zarr_structure.attrs['extra_data']:
    #         missing_dim: str = zarr_structure.attrs['extra_data']['missing_dimensions']
                # TODO: problem here
                # for missing_dim in missing_dims:
                #     img_array = np.expand_dims(img_array, axis=d[missing_dim])

    # TODO: fix for mitocheck
    # need to provide missing dimensions (Z, C)
    rearranged_arr = img_array.transpose(*reorder_tuple)        
    

    artificial_channel_ids = list(range(rearranged_arr.shape[1]))
    artificial_channel_ids = [str(x) for x in artificial_channel_ids]
    # TODO: prepare list of of PreparedOMETIFFData
    # for each time and channel
    for time in range(rearranged_arr.shape[0]):
        time_arr = rearranged_arr[time]
        for channel_number in range(time_arr.shape[0]):
            three_d_arr = time_arr[channel_number]
            p: PreparedOMETIFFData = {
                'channel_number': channel_number,
                'time': time,
                'data': three_d_arr
            }
            prepared_data.append(p)


    artificial_channel_ids_dict = dict(zip(artificial_channel_ids, artificial_channel_ids))
    return prepared_data, artificial_channel_ids_dict


def ometiff_image_processing(internal_volume: InternalVolume):
    # NOTE: supports only 3D images

    zarr_structure: zarr.Group = open_zarr_structure_from_path(
        internal_volume.intermediate_zarr_structure_path
    )
    set_volume_custom_data(internal_volume, zarr_structure)
    
    print(f"Processing volume file {internal_volume.volume_input_path}")
    
    reader = OMETIFFReader(fpath=internal_volume.volume_input_path)
    img_array, metadata, xml_metadata = reader.read()

    prepared_data, artificial_channel_ids = prepare_ometiff_for_writing(img_array, metadata, internal_volume)

    volume_data_group: zarr.Group = zarr_structure.create_group(
        VOLUME_DATA_GROUPNAME
    )

    set_ometiff_source_metadata(internal_volume, metadata)
    
    # NOTE: at that point internal_volume.custom_data should exist
    # as it is filled by one of three ways
    
    # TODO: set internal_volume.custom_data['channel_ids_mapping'] to artificial
    # if it does not exist
    if 'channel_ids_mapping' not in internal_volume.custom_data:
        internal_volume.custom_data['channel_ids_mapping'] = artificial_channel_ids

    channel_ids_mapping: dict[str, str] = internal_volume.custom_data['channel_ids_mapping']
    for data_item in prepared_data:
        dask_arr = da.from_array(data_item['data'])
        channel_number = data_item['channel_number']
        channel_id = channel_ids_mapping[str(channel_number)]
        store_volume_data_in_zarr_stucture(
                data=dask_arr,
                volume_data_group=volume_data_group,
                params_for_storing=internal_volume.params_for_storing,
                force_dtype=internal_volume.volume_force_dtype,
                resolution="1",
                time_frame=str(data_item['time']),
                channel=channel_id,
                # quantize_dtype_str=internal_volume.quantize_dtype_str
            )
    print("Volume processed")

