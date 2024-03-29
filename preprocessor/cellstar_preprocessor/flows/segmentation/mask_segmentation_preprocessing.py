from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.flows.segmentation.helper_methods import store_segmentation_data_in_zarr_structure
from cellstar_preprocessor.model.input import SegmentationPrimaryDescriptor
from cellstar_preprocessor.model.segmentation import InternalSegmentation
import numpy as np
import mrcfile

def _normalize_axis_order_mrcfile_numpy(arr: np.memmap, mrc_header: object) -> np.memmap:
    """
    Normalizes axis order to X, Y, Z (1, 2, 3)
    """
    h = mrc_header
    current_order = int(h.mapc) - 1, int(h.mapr) - 1, int(h.maps) - 1

    if current_order != (0, 1, 2):
        print(f"Reordering axes from {current_order}...")
        ao = {v: i for i, v in enumerate(current_order)}
        # TODO: optimize this to a single transpose
        arr = arr.transpose().transpose(ao[2], ao[1], ao[0]).transpose()
    else:
        arr = arr.transpose()

    return arr

def mask_segmentation_preprocessing(internal_segmentation: InternalSegmentation):
    our_zarr_structure = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )

    internal_segmentation.primary_descriptor = (
            SegmentationPrimaryDescriptor.three_d_volume
        )

    segmentation_data_gr = our_zarr_structure.create_group(LATTICE_SEGMENTATION_DATA_GROUPNAME)

    # TODO: process masks as multiple lattices
    # PLAN: iterate over masks

    # artificially create value_to_segment_id_dict
    internal_segmentation.value_to_segment_id_dict = {}
    
    for lattice_id, mask in enumerate(internal_segmentation.segmentation_input_path):
        with mrcfile.open(str(mask.resolve())) as mrc_original:
            data = mrc_original.data
            header = mrc_original.header

            data = _normalize_axis_order_mrcfile_numpy(arr=data, mrc_header=header)
            internal_segmentation.value_to_segment_id_dict[lattice_id] = {}
    
    
            # TODO: edit this part

            unique_values = np.unique(data)
            unique_values_without_zero = unique_values[unique_values > 0]
            if unique_values_without_zero.dtype.kind == 'f':
                data.setflags(write=1)
                # start from highest value found in the array + 1
                start = int(unique_values_without_zero.max() + 1)
                for index, value in enumerate(unique_values_without_zero, start=start):
                    data[data == value] = index
            
                data = data.astype('i4')


            for value in np.unique(data):
                internal_segmentation.value_to_segment_id_dict[lattice_id][int(value)] = int(value)

            lattice_gr = segmentation_data_gr.create_group(lattice_id)
            params_for_storing = internal_segmentation.params_for_storing

            store_segmentation_data_in_zarr_structure(
                original_data=data,
                lattice_data_group=lattice_gr,
                value_to_segment_id_dict_for_specific_lattice_id=internal_segmentation.value_to_segment_id_dict[
                    lattice_id
                ],
                params_for_storing=params_for_storing,
            )
    
    













# OLD part
    # global_data = None
    # for index, mask in enumerate(internal_segmentation.segmentation_input_path):
    #     with mrcfile.open(str(mask.resolve())) as mrc_original:
    #         data = mrc_original.data
    #         # non_zero_indices[index] = data.nonzero()
    #         header = mrc_original.header
        
    #     if index == 0:
    #         global_data = data
    #         global_data.setflags(write=1)
    #     else:
    #         overlap = np.where((data==global_data) & (data == 1) & (global_data == 1))
    #         if len(overlap[0]) == 0:
    #             # get indices of non zero values (basically 1s)
    #             non_zero_indices = np.nonzero(data)
    #             # insert 'index+1' (basically 2s) at those indices in global_data
    #             global_data[non_zero_indices] = index + 1
    #         else:
    #             raise Exception(f'Segments in {mask} overlap with segments in other mask')

    # # TODO: get data from map
    # # with mrcfile.mmap(str(internal_segmentation.segmentation_input_path.resolve())) as mrc_original:
    # #     data: np.memmap = mrc_original.data
    # #     header = mrc_original.header

    # global_data = _normalize_axis_order_mrcfile_numpy(arr=global_data, mrc_header=header)

    # # artificially create value_to_segment_id_dict
    # internal_segmentation.value_to_segment_id_dict = {}
    # internal_segmentation.value_to_segment_id_dict[0] = {}

    # # Temp hack to preprocess masks with float values:
    # # get unique values as array
    # # loop over that array
    # # on each iteration replace that value by index of loop iteration
    # unique_values = np.unique(global_data)
    # unique_values_without_zero = unique_values[unique_values > 0]
    # if unique_values_without_zero.dtype.kind == 'f':
    #     # start from highest value found in the array + 1
    #     start = int(unique_values_without_zero.max() + 1)
    #     for index, value in enumerate(unique_values_without_zero, start=start):
    #         global_data[global_data == value] = index
    
    #     global_data = global_data.astype('i4')


    # for value in np.unique(global_data):
    #     internal_segmentation.value_to_segment_id_dict[0][int(value)] = int(value)

    # lattice_gr = segmentation_data_gr.create_group(str(0))
    # params_for_storing = internal_segmentation.params_for_storing

    # store_segmentation_data_in_zarr_structure(
    #     original_data=global_data,
    #     lattice_data_group=lattice_gr,
    #     value_to_segment_id_dict_for_specific_lattice_id=internal_segmentation.value_to_segment_id_dict[
    #         0
    #     ],
    #     params_for_storing=params_for_storing,
    # )
