# TODO: figure out how to use these internal volume attributes
# volume_force_dtype=preprocessor_input.volume.force_volume_dtype,
# downsampling_parameters=preprocessor_input.downsampling,

import gc
import numpy as np
import zarr

from cellstar_preprocessor.flows.common import (
    create_dataset_wrapper,
    open_zarr_structure_from_path,
)
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.model.volume import InternalVolume

# TODO: support 3 axes case?

def ome_zarr_image_preprocessing(internal_volume: InternalVolume):
    ome_zarr_root = zarr.open_group(internal_volume.volume_input_path)

    our_zarr_structure = open_zarr_structure_from_path(
        internal_volume.intermediate_zarr_structure_path
    )

    # PROCESSING VOLUME
    volume_data_gr: zarr.Group = our_zarr_structure.create_group(VOLUME_DATA_GROUPNAME)
    root_zattrs = ome_zarr_root.attrs
    multiscales = root_zattrs["multiscales"]
    # NOTE: can be multiple multiscales, here picking just 1st
    axes = multiscales[0]["axes"]
    for volume_arr_resolution, volume_arr in ome_zarr_root.arrays():
        # if time is first and there are 5 axes = read as it is, create groups accordingly
        # if there are 4 axes - add time group
        # if there are 3 axes - check if 1st is time
        # if yes, create 1st layer groups from it, 2nd layer group = 1, in 3rd layer
        # create array with added Z dimension = 1
        # if not time - create 1st and 2nd layer groups == 1

        # # TODO: later: add support for volume force dtype
        # # setting volume_force_dtype attribute - required to skip quantization if dtype is e.g. u2
        # # NOTE: currently sets it based on the first array
        # if internal_volume.volume_force_dtype is None:
        #     internal_volume.volume_force_dtype = volume_arr.dtype

        size_of_data_for_lvl = 0
        resolution_group = volume_data_gr.create_group(volume_arr_resolution)
        if len(axes) == 5 and axes[0]["name"] == "t":
            for i in range(volume_arr.shape[0]):
                time_group = resolution_group.create_group(str(i))
                for j in range(volume_arr.shape[1]):
                    corrected_volume_arr_data = volume_arr[...][i][j].swapaxes(0, 2)
                    # our_channel_arr = time_group.create_dataset(
                    #     name=j,
                    #     shape=corrected_volume_arr_data.shape,
                    #     data=corrected_volume_arr_data
                    # )
                    our_channel_arr = create_dataset_wrapper(
                        zarr_group=time_group,
                        name=j,
                        shape=corrected_volume_arr_data.shape,
                        data=corrected_volume_arr_data,
                        dtype=corrected_volume_arr_data.dtype,
                        params_for_storing=internal_volume.params_for_storing,
                    )

                    size_of_data_for_lvl = size_of_data_for_lvl + our_zarr_structure.store.getsize(our_channel_arr.path)
                    del corrected_volume_arr_data
                    gc.collect()
                    

        elif len(axes) == 4 and axes[0]["name"] == "c":
            time_group = resolution_group.create_group("0")
            for j in range(volume_arr.shape[0]):
                corrected_volume_arr_data = volume_arr[...][j].swapaxes(0, 2)
                our_channel_arr = create_dataset_wrapper(
                    zarr_group=time_group,
                    name=j,
                    shape=corrected_volume_arr_data.shape,
                    data=corrected_volume_arr_data,
                    dtype=corrected_volume_arr_data.dtype,
                    params_for_storing=internal_volume.params_for_storing,
                )
                size_of_data_for_lvl = size_of_data_for_lvl + our_zarr_structure.store.getsize(our_channel_arr.path)
                del corrected_volume_arr_data
                gc.collect()
        # TODO: later
        # elif len(axes) == 3:
        #     # NOTE: assumes CYX order
        #     if axes[0]["name"] == 'c':
        #         # PLAN:
        #         # create time group
        #         # add z dimension to volume_arr
        #         # NOTE: be careful with axes order
        #         # NOTE: modify also ome_zarr_labels_preprocessing.py
        #         time_group = resolution_group.create_group("0")
        #         for j in range(volume_arr.shape[0]):
        #             # swap Y and X
        #             corrected_volume_arr_data = volume_arr[...][j].swapaxes(0, 1)
        #             # add Z dimension = 1
        #             corrected_volume_arr_data = np.expand_dims(corrected_volume_arr_data, axis=2)
        #             assert corrected_volume_arr_data.shape[2] == 1
        #             our_channel_arr = create_dataset_wrapper(
        #                 zarr_group=time_group,
        #                 name=j,
        #                 shape=corrected_volume_arr_data.shape,
        #                 data=corrected_volume_arr_data,
        #                 dtype=corrected_volume_arr_data.dtype,
        #                 params_for_storing=internal_volume.params_for_storing,
        #             )
        #     else:
        #         pass
        else:
            raise Exception("Axes number/order is not supported")
        
        size_of_data_for_lvl_mb = size_of_data_for_lvl / 1024 ** 2
        print(f'size of data for lvl in mb: {size_of_data_for_lvl_mb}')
        if internal_volume.downsampling_parameters.max_size_per_downsampling_lvl_mb and size_of_data_for_lvl_mb > internal_volume.downsampling_parameters.max_size_per_downsampling_lvl_mb:
            print(f'Data for resolution {volume_arr_resolution} removed for volume')
            del volume_data_gr[volume_arr_resolution]

    print("Volume processed")

    if internal_volume.downsampling_parameters.remove_original_resolution:
        all_resolutions = sorted(ome_zarr_root.array_keys())
        original_resolution = all_resolutions[0]
        if original_resolution in volume_data_gr:
            del volume_data_gr[original_resolution]
            print('Original resolution data removed for volume')
    