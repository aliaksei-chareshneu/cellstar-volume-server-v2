from preprocessor_v2.preprocessor.flows.common import open_zarr_structure_from_path
from preprocessor_v2.preprocessor.flows.constants import MESH_SIMPLIFICATION_LEVELS_PER_ORDER, MESH_SIMPLIFICATION_N_LEVELS, MESH_VERTEX_DENSITY_THRESHOLD, SEGMENTATION_DATA_GROUPNAME
from preprocessor_v2.preprocessor.flows.segmentation.helper_methods import hdf5_to_zarr, lattice_data_to_np_arr, make_simplification_curve, map_value_to_segment_id, store_segmentation_data_in_zarr_structure, write_mesh_component_data_to_zarr_arr
from preprocessor_v2.preprocessor.model.input import SegmentationPrimaryDescriptor
from preprocessor_v2.preprocessor.model.segmentation import InternalSegmentation
import zarr
from vedo import Mesh

def sff_preprocessing(internal_segmentation: InternalSegmentation):
    hdf5_to_zarr(internal_segmentation=internal_segmentation)

    zarr_structure: zarr.hierarchy.group = open_zarr_structure_from_path(internal_segmentation.intermediate_zarr_structure_path)
    segm_data_gr: zarr.hierarchy.group = zarr_structure.create_group(SEGMENTATION_DATA_GROUPNAME)
    
    
    # PLAN:
    # 1. Convert hff to intermediate zarr structure
    # 2. Process it with one of 2 methods (3d volume segmentation, mesh segmentation)
    if zarr_structure.primary_descriptor[0] == b'three_d_volume':
        internal_segmentation.primary_descriptor = SegmentationPrimaryDescriptor.three_d_volume
        internal_segmentation.value_to_segment_id_dict = map_value_to_segment_id(zarr_structure)
        _process_three_d_volume_segmentation_data(segm_data_gr, zarr_structure, internal_segmentation=internal_segmentation)
    elif zarr_structure.primary_descriptor[0] == b'mesh_list':
        internal_segmentation.primary_descriptor = SegmentationPrimaryDescriptor.mesh_list
        internal_segmentation.simplification_curve = make_simplification_curve(MESH_SIMPLIFICATION_N_LEVELS, MESH_SIMPLIFICATION_LEVELS_PER_ORDER)
        _process_mesh_segmentation_data(segm_data_gr, zarr_structure, internal_segmentation=internal_segmentation)
    
    print('Segmentation processed')

def _process_three_d_volume_segmentation_data(segm_data_gr: zarr.hierarchy.group, zarr_structure: zarr.hierarchy.group, internal_segmentation: InternalSegmentation):
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
        value_to_segment_id_dict = internal_segmentation.value_to_segment_id_dict
        params_for_storing = internal_segmentation.params_for_storing

        store_segmentation_data_in_zarr_structure(
            original_data=segm_arr,
            lattice_data_group=lattice_gr,
            value_to_segment_id_dict_for_specific_lattice_id=value_to_segment_id_dict[lattice_id],
            params_for_storing=params_for_storing
        )

def _process_mesh_segmentation_data(segm_data_gr: zarr.hierarchy.group, zarr_structure: zarr.hierarchy.group, internal_segmentation: InternalSegmentation):
    # TODO: add time and channel to server\app\api\requests.py
    # and to async def get_meshes AND get_meshes_bcif in server\app\api\v2.py
    
    params_for_storing = internal_segmentation.params_for_storing

    for segment_name, segment in zarr_structure.segment_list.groups():
        segment_id = str(int(segment.id[...]))
        single_segment_group = segm_data_gr.create_group(segment_id)
        single_detail_lvl_group = single_segment_group.create_group('1')
        if 'mesh_list' in segment:
            for mesh_name, mesh in segment.mesh_list.groups():
                mesh_id = str(int(mesh.id[...]))
                time_group = single_detail_lvl_group.create_group('0')
                channel_group = time_group.create_group('0')
                single_mesh_group = channel_group.create_group(mesh_id)

                for mesh_component_name, mesh_component in mesh.groups():
                    if mesh_component_name != 'id':
                        write_mesh_component_data_to_zarr_arr(
                            target_group=single_mesh_group,
                            mesh=mesh,
                            mesh_component_name=mesh_component_name,
                            params_for_storing=params_for_storing
                        )
                # TODO: check in which units is area and volume
                vertices = single_mesh_group['vertices'][...]
                triangles = single_mesh_group['triangles'][...]
                vedo_mesh_obj = Mesh([vertices, triangles])
                single_mesh_group.attrs['num_vertices'] = single_mesh_group.vertices.attrs['num_vertices']
                single_mesh_group.attrs['area'] = vedo_mesh_obj.area()
                # single_mesh_group.attrs['volume'] = vedo_mesh_obj.volume()
    
    # TODO: downsampling part?
    # simplification_curve: dict[int, float] = internal_segmentation.simplification_curve
    # calc_mode = 'area'
    # density_threshold = MESH_VERTEX_DENSITY_THRESHOLD[calc_mode]
    


    
    # for segment_name_id, segment in segm_data_gr.groups():
    #     original_detail_lvl_mesh_list_group = segment['1']
    #     group_ref = original_detail_lvl_mesh_list_group

    #     for level, fraction in simplification_curve.items():
    #         if density_threshold != 0 and compute_vertex_density(group_ref, mode=calc_mode) <= density_threshold:
    #             break
    #         if fraction == 1:
    #             continue  # original data, don't need to compute anything
    #         mesh_data_dict = simplify_meshes(original_detail_lvl_mesh_list_group, ratio=fraction, segment_id=segment_name_id)
    #         # TODO: potentially simplify meshes may output mesh with 0 vertices, normals, triangles
    #         # it should not be stored?
    #         # check each mesh in mesh_data_dict if it contains 0 vertices
    #         # remove all such meshes from dict
    #         for mesh_id in list(mesh_data_dict.keys()):
    #             if mesh_data_dict[mesh_id]['attrs']['num_vertices'] == 0:
    #                 del mesh_data_dict[mesh_id]

    #         # if there is no meshes left in dict - break from while loop
    #         if not bool(mesh_data_dict):
    #             break
            
    #         group_ref = _store_mesh_data_in_zarr(mesh_data_dict, segment, detail_level=level, params_for_storing=params_for_storing)
