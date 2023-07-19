
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.flows.segmentation.sff_preprocessing import sff_preprocessing
from cellstar_preprocessor.tests.helper_methods import initialize_intermediate_zarr_structure_for_tests
from cellstar_preprocessor.tests.input_for_tests import INTERNAL_SEGMENTATION_FOR_TESTING
import zarr

def test_sff_preprocessing():
    initialize_intermediate_zarr_structure_for_tests()
    
    # NOTE: tests only three_d_volume segmentation, not mesh
    internal_segmentation = INTERNAL_SEGMENTATION_FOR_TESTING
    sff_preprocessing(internal_segmentation=internal_segmentation)

    # check if zarr structure has right format
    # 1. open zarr structure, check if there is _segmentation_data group
    # 2. check if 0th level zarr group (lattice_id) is group and if there is just one group (0)
    # 3. check if 1st level zarr group (resolution) is group and if there is just one group (1)
    # 4. check if 2nd level zarr group (time) is group and if there is just one group (0)
    # 5. check if 3rd level in zarr (channel) is group and if there is just one group (0)
    # 6. check if 4th level in zarr contains two arrays 'grid' and 'set_table'

    zarr_structure = open_zarr_structure_from_path(internal_segmentation.intermediate_zarr_structure_path)

    assert SEGMENTATION_DATA_GROUPNAME in zarr_structure
    segmentation_gr = zarr_structure[SEGMENTATION_DATA_GROUPNAME]
    assert isinstance(segmentation_gr, zarr.hierarchy.Group)
    assert len(segmentation_gr) == 1

    assert '0' in segmentation_gr
    assert isinstance(segmentation_gr['0'], zarr.hierarchy.Group)
    assert len(segmentation_gr['0']) == 1

    assert '1' in segmentation_gr['0']
    assert isinstance(segmentation_gr['0']['1'], zarr.hierarchy.Group)
    assert len(segmentation_gr['0']['1']) == 1

    assert '0' in segmentation_gr['0']['1']
    assert isinstance(segmentation_gr['0']['1']['0'], zarr.hierarchy.Group)
    assert len(segmentation_gr['0']['1']['0']) == 1

    assert '0' in segmentation_gr['0']['1']['0']
    assert isinstance(segmentation_gr['0']['1']['0']['0'], zarr.hierarchy.Group)
    assert len(segmentation_gr['0']['1']['0']['0']) == 2

    assert 'grid' in segmentation_gr['0']['1']['0']['0']
    assert segmentation_gr['0']['1']['0']['0'].grid.shape == (64, 64, 64)

    assert 'set_table' in segmentation_gr['0']['1']['0']['0']
    assert segmentation_gr['0']['1']['0']['0'].set_table.shape == (1,)




    