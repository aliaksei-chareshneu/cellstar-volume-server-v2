# TODO: figure out how to use these internal volume attributes
# params_for_storing=self.preprocessor_input.storing_params,
# volume_force_dtype=preprocessor_input.volume.force_volume_dtype,
# quantize_dtype_str=preprocessor_input.volume.quantize_dtype_str,
# downsampling_parameters=preprocessor_input.downsampling,

# TODO: if quantization should be supported, modify store_volume_data_in_zarr_stucture
# so that it creates time and resolution groups only when they don't exist
# otherwise it references the existing group
# and use this modified function to store ome zarr volume data

from preprocessor_v2.preprocessor.flows.common import open_zarr_structure_from_path
from preprocessor_v2.preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from preprocessor_v2.preprocessor.model.volume import InternalVolume
import zarr

def ome_zarr_image_preprocessing(internal_volume: InternalVolume):
    ome_zarr_root = zarr.open_group(internal_volume.volume_input_path)
    
    our_zarr_structure = open_zarr_structure_from_path(
        internal_volume.intermediate_zarr_structure_path)

    # PROCESSING VOLUME
    volume_data_gr = our_zarr_structure.create_group(VOLUME_DATA_GROUPNAME)
    root_zattrs = ome_zarr_root.attrs
    multiscales = root_zattrs["multiscales"]
    # NOTE: can be multiple multiscales, here picking just 1st
    axes = multiscales[0]['axes']
    for volume_arr_resolution, volume_arr in ome_zarr_root.arrays():
        # if time is first and there are 5 axes = read as it is, create groups accordingly
        # if there are 4 axes - add time group
        # if there are 3 axes - check if 1st is time
        # if yes, create 1st layer groups from it, 2nd layer group = 1, in 3rd layer
        # create array with added Z dimension = 1
        # if not time - create 1st and 2nd layer groups == 1

        resolution_group = volume_data_gr.create_group(volume_arr_resolution)
        if len(axes) == 5 and axes[0]['name'] == 't':
            for i in range(volume_arr.shape[0]):
                time_group = resolution_group.create_group(str(i))
                for j in range(volume_arr.shape[1]):
                    corrected_volume_arr_data = volume_arr[...][i][j].swapaxes(0,2)
                    our_channel_arr = time_group.create_dataset(
                        name=j,
                        shape=corrected_volume_arr_data.shape,
                        data=corrected_volume_arr_data
                    )
        elif len(axes) == 4 and axes[0]['name'] == 'c':
            time_group = resolution_group.create_group('0')
            for j in range(volume_arr.shape[0]):
                corrected_volume_arr_data = volume_arr[...][j].swapaxes(0,2)
                our_channel_arr = time_group.create_dataset(
                    name=j,
                    shape=corrected_volume_arr_data.shape,
                    data=corrected_volume_arr_data
                )
        # TODO: later
        # elif len(axes) == 3:
        #     if axes[0] == 't':
        #         pass
        #     else:
        #         pass
        else:
            raise Exception('Axes number/order is not supported')
        

        print('Volume processed')