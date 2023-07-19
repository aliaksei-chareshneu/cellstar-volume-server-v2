from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume.volume_downsampling import volume_downsampling
from cellstar_preprocessor.tests.helper_methods import initialize_intermediate_zarr_structure_for_tests
from cellstar_preprocessor.tests.input_for_tests import INTERNAL_VOLUME_FOR_TESTING
import numpy as np
import zarr

def test_volume_downsampling():
    initialize_intermediate_zarr_structure_for_tests()
    internal_volume = INTERNAL_VOLUME_FOR_TESTING
    zarr_structure: zarr.hierarchy.Group = open_zarr_structure_from_path(internal_volume.intermediate_zarr_structure_path)

    # create synthetic array filled with ones
    arr = zarr_structure.create_dataset(
        f'{VOLUME_DATA_GROUPNAME}/1/0/0',
        shape=(64, 64, 64),
        fill_value=1
    )

    volume_downsampling(internal_volume=internal_volume)
    # test if there is just one downsampling and if it has shape=32,32,32 and values=1

    assert '2/0/0' in zarr_structure[VOLUME_DATA_GROUPNAME]
    assert (zarr_structure[f'{VOLUME_DATA_GROUPNAME}/2/0/0'][...] == np.ones(
        shape=(32, 32, 32),
        dtype=internal_volume.volume_force_dtype
    )).all()