from preprocessor_v2.preprocessor.flows.common import open_zarr_structure_from_path
from preprocessor_v2.preprocessor.flows.constants import SEGMENTATION_DATA_GROUPNAME
from preprocessor_v2.preprocessor.flows.segmentation.helper_methods import hdf5_to_zarr, lattice_data_to_np_arr, map_value_to_segment_id, store_segmentation_data_in_zarr_structure
from preprocessor_v2.preprocessor.model.segmentation import InternalSegmentation
import zarr

def sff_preprocessing(internal_segmentation: InternalSegmentation):
    hdf5_to_zarr(intermediate_zarr_structure_path=internal_segmentation.intermediate_zarr_structure_path,
                file_path=internal_segmentation.sff_input_path)

    zarr_structure: zarr.hierarchy.group = open_zarr_structure_from_path(internal_segmentation.intermediate_zarr_structure_path)
    segm_data_gr: zarr.hierarchy.group = zarr_structure.create_group(SEGMENTATION_DATA_GROUPNAME)
    
    internal_segmentation.value_to_segment_id_dict = map_value_to_segment_id(zarr_structure)

    # PLAN:
    # 1. Convert hff to intermediate zarr structure
    # 2. Process it with one of 2 methods (3d volume segmentation, mesh segmentation)
    if zarr_structure.primary_descriptor[0] == b'three_d_volume':
        _process_three_d_volume_segmentation_data(segm_data_gr, zarr_structure, params_for_storing=internal_segmentation.params_for_storing, value_to_segment_id_dict=internal_segmentation.value_to_segment_id_dict)
    elif zarr_structure.primary_descriptor[0] == b'mesh_list':
        pass
        # process_mesh_segmentation_data(segm_data_gr, zarr_structure, mesh_simplification_curve, params_for_storing=params_for_storing)
    
    print('Segmentation processed')

def _process_three_d_volume_segmentation_data(segm_data_gr: zarr.hierarchy.group, zarr_structure: zarr.hierarchy.group, params_for_storing, value_to_segment_id_dict):
    for gr_name, gr in zarr_structure.lattice_list.groups():
        # gr is a 'lattice' obj in lattice list
        lattice_id = int(gr.id[...])
        segm_arr = lattice_data_to_np_arr(
            data=gr.data[0],
            mode=gr.mode[0],
            endianness=gr.endianness[0],
            arr_shape=(gr.size.cols[...], gr.size.rows[...], gr.size.sections[...])
        )

        lattice_gr = segm_data_gr.create_group(gr_name)
        
        store_segmentation_data_in_zarr_structure(
            original_data=segm_arr,
            lattice_data_group=lattice_gr,
            value_to_segment_id_dict_for_specific_lattice_id=value_to_segment_id_dict[lattice_id],
            params_for_storing=params_for_storing
        )
        