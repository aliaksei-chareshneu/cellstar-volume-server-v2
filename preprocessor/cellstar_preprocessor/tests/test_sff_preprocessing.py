
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.flows.segmentation.helper_methods import open_hdf5_as_segmentation_object
from cellstar_preprocessor.flows.segmentation.sff_preprocessing import sff_preprocessing
from cellstar_preprocessor.model.input import SegmentationPrimaryDescriptor
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.tests.helper_methods import initialize_intermediate_zarr_structure_for_tests
from cellstar_preprocessor.tests.input_for_tests import INTERNAL_MESH_SEGMENTATION_FOR_TESTING, INTERNAL_SEGMENTATION_FOR_TESTING
import zarr
import pytest

SEGMENTATIONS = [
    INTERNAL_SEGMENTATION_FOR_TESTING,
    INTERNAL_MESH_SEGMENTATION_FOR_TESTING
]

@pytest.mark.parametrize("internal_segmentation", SEGMENTATIONS)
def test_sff_preprocessing(internal_segmentation: InternalSegmentation):
    initialize_intermediate_zarr_structure_for_tests()
    
    sff_segm_obj = open_hdf5_as_segmentation_object(internal_segmentation.segmentation_input_path)

    sff_preprocessing(internal_segmentation=internal_segmentation)

    # check if zarr structure has right format
    # 1. open zarr structure, check if there is _segmentation_data group
    # 2. check if 0th level zarr group (lattice_id) is group and if there is just one group (0)
    # 3. check if 1st level zarr group (resolution) is group and if there is just one group (1)
    # 4. check if 2nd level zarr group (time) is group and if there is just one group (0)
    # 5. check if 3rd level in zarr (channel) is group and if there is just one group (0)
    # 6. check if 4th level in zarr contains two arrays 'grid' and 'set_table'

    zarr_structure = open_zarr_structure_from_path(internal_segmentation.intermediate_zarr_structure_path)

    assert LATTICE_SEGMENTATION_DATA_GROUPNAME in zarr_structure
    segmentation_gr = zarr_structure[LATTICE_SEGMENTATION_DATA_GROUPNAME]
    assert isinstance(segmentation_gr, zarr.hierarchy.Group)

    # n of segments
    
    if internal_segmentation.primary_descriptor == SegmentationPrimaryDescriptor.three_d_volume:
        assert len(segmentation_gr) == len(sff_segm_obj.lattice_list)

        for lattice_id, lattice_gr in segmentation_gr.groups():
            # single resolution group
            assert len(lattice_gr) == 1
            assert '1' in lattice_gr
            assert isinstance(lattice_gr['1'], zarr.hierarchy.Group)

            # single time group
            assert len(lattice_gr['1']) == 1
            assert '0' in lattice_gr['1']
            assert isinstance(lattice_gr['1']['0'], zarr.hierarchy.Group)

            # single channel group
            assert len(lattice_gr['1']['0']) == 1
            assert '0' in lattice_gr['1']['0']
            assert isinstance(lattice_gr['1']['0']['0'], zarr.hierarchy.Group)
            
            # grid and set table
            assert len(lattice_gr['1']['0']['0']) == 2
            assert 'grid' in lattice_gr['1']['0']['0']
            lattice_from_sff = list(filter(lambda lat: str(lat.id) == lattice_id, sff_segm_obj.lattice_list))[0]
            grid_shape = (
                lattice_from_sff.size.rows,
                lattice_from_sff.size.cols,
                lattice_from_sff.size.sections
                )
            assert lattice_gr['1']['0']['0'].grid.shape == grid_shape

            assert 'set_table' in lattice_gr['1']['0']['0']
            assert lattice_gr['1']['0']['0'].set_table.shape == (1,)
    
    # empiar-10070
    elif internal_segmentation.primary_descriptor == SegmentationPrimaryDescriptor.mesh_list:
        assert len(segmentation_gr) == len(sff_segm_obj.segment_list)
        for segment_name, segment in segmentation_gr.groups():
            # single detail lvl group
            assert len(segment) == 1
            assert '1' in segment
            # time
            assert '0' in segment['1']
            # channel
            assert '0' in segment['1']['0']
            # mesh
            for mesh_id, mesh_gr in segment['1']['0']['0'].groups():
                # assert '0' in segment['1']['0']['0']
                # attributes
                assert 'triangles' in mesh_gr
                assert 'vertices' in mesh_gr



    