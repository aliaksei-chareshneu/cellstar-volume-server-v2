from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.flows.segmentation.segmentation_downsampling import sff_segmentation_downsampling
from cellstar_preprocessor.model.input import SegmentationPrimaryDescriptor
from cellstar_preprocessor.tests.helper_methods import initialize_intermediate_zarr_structure_for_tests
from cellstar_preprocessor.tests.input_for_tests import INTERNAL_SEGMENTATION_FOR_TESTING
import numpy as np
import numcodecs

import zarr

def test_sff_segmentation_downsampling():
    # NOTE: only three_d_volume segmentation
    initialize_intermediate_zarr_structure_for_tests()
    internal_segmentation = INTERNAL_SEGMENTATION_FOR_TESTING
    internal_segmentation.primary_descriptor = SegmentationPrimaryDescriptor.three_d_volume

    zarr_structure: zarr.Group = open_zarr_structure_from_path(internal_segmentation.intermediate_zarr_structure_path)

    
    segment_ids_data = np.arange(64).reshape(4, 4, 4)
    # create arr
    grid_arr = zarr_structure.create_dataset(
        f'{LATTICE_SEGMENTATION_DATA_GROUPNAME}/0/1/0/grid',
        data=segment_ids_data
    )

    set_table = zarr_structure.create_dataset(
        name=f'{LATTICE_SEGMENTATION_DATA_GROUPNAME}/0/1/0/set_table',
        dtype=object,
        object_codec=numcodecs.JSON(),
        shape=1,
    )

    d = {}
    for value in np.unique(segment_ids_data):
        d[str(value)] = [int(value)]

    set_table[...] = [d]

    value_to_segment_id_dict = {0: {}}
    for value in np.unique(segment_ids_data):
        value_to_segment_id_dict[0][int(value)] = int(value)

    internal_segmentation.value_to_segment_id_dict = value_to_segment_id_dict

    sff_segmentation_downsampling(internal_segmentation=internal_segmentation)

    # compare grid arrays
    assert (zarr_structure[f'{LATTICE_SEGMENTATION_DATA_GROUPNAME}/0/2/0'].grid[...] == np.array(
        [[[64, 65],
        [66, 67]],

       [[68, 69],
        [70, 42]]]
    )).all()

    # get set_table
    # update it with
    new_ids = {
        '64': [0, 1, 4, 5, 16, 17, 20, 21], '65': [2, 18, 6, 22], '66': [8, 9, 24, 25], '67': [10, 26], '68': [32, 33, 36, 37], '69': [34, 38], '70': [40, 41]
    }
    updated_dict = zarr_structure[f'{LATTICE_SEGMENTATION_DATA_GROUPNAME}/0/1/0'].set_table[...][0] | new_ids
    assert (zarr_structure[f'{LATTICE_SEGMENTATION_DATA_GROUPNAME}/0/2/0'].set_table[...][0] == updated_dict)

    