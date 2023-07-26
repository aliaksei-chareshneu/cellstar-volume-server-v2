from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.flows.segmentation.helper_methods import store_segmentation_data_in_zarr_structure
from cellstar_preprocessor.model.segmentation import InternalSegmentation
import nibabel as nib
import numpy as np

def nii_segmentation_preprocessing(internal_segmentation: InternalSegmentation):
    our_zarr_structure = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )

    segmentation_data_gr = our_zarr_structure.create_group(SEGMENTATION_DATA_GROUPNAME)
    internal_segmentation.value_to_segment_id_dict = {}
    lattice_gr = segmentation_data_gr.create_group('0')
        
    # index = 'lattice_id'
    global_data = None
    for index, segm_input_path in enumerate(internal_segmentation.segmentation_input_path):
        img = nib.load(str(segm_input_path.resolve()))
        data = img.get_fdata()
        # temp fix: convert float64 to int
        data = data.astype(np.int32)

        if index == 0:
            global_data = data
        else:
            overlap = np.where((data==global_data) & (data == 1) & (global_data == 1))
            if len(overlap[0]) == 0:
                # get indices of non zero values (basically 1s)
                non_zero_indices = np.nonzero(data)
                # insert 'index+1' (basically 2s) at those indices in global_data
                global_data[non_zero_indices] = index + 1
            else:
                raise Exception(f'Segments in {segm_input_path} overlap with segments in other nii segmentations') 
    

    internal_segmentation.value_to_segment_id_dict[0] = {}
    for value in np.unique(global_data):
        internal_segmentation.value_to_segment_id_dict[0][int(value)] = int(value)
    
    params_for_storing = internal_segmentation.params_for_storing

    store_segmentation_data_in_zarr_structure(
        original_data=global_data,
        lattice_data_group=lattice_gr,
        value_to_segment_id_dict_for_specific_lattice_id=internal_segmentation.value_to_segment_id_dict[
            0
        ],
        params_for_storing=params_for_storing,
    )