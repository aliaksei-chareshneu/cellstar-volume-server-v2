import shutil
import pytest
import zarr
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume.ome_zarr_image_preprocessing import (
    ome_zarr_image_preprocessing,
)
from cellstar_preprocessor.model.volume import InternalVolume
from cellstar_preprocessor.tests.helper_methods import (
    get_omezarr_internal_volume,
    initialize_intermediate_zarr_structure_for_tests,
)
from cellstar_preprocessor.tests.input_for_tests import (
    OMEZARR_TEST_INPUTS,
    OMEZarrTestInput,
)

@pytest.mark.parametrize("omezar_test_input", OMEZARR_TEST_INPUTS)
def test_ome_zarr_image_preprocessing(omezar_test_input: OMEZarrTestInput):
    initialize_intermediate_zarr_structure_for_tests()
    internal_volume = get_omezarr_internal_volume(omezar_test_input)
    
    ome_zarr_image_preprocessing(internal_volume=internal_volume)

    ome_zarr_root = zarr.open_group(internal_volume.volume_input_path)
    root_zattrs = ome_zarr_root.attrs
    multiscales = root_zattrs["multiscales"]
    axes = multiscales[0]["axes"]

    zarr_structure = open_zarr_structure_from_path(
        internal_volume.intermediate_zarr_structure_path
    )

    assert VOLUME_DATA_GROUPNAME in zarr_structure
    volume_gr = zarr_structure[VOLUME_DATA_GROUPNAME]
    assert isinstance(volume_gr, zarr.Group)

    # check if number of resolution groups is the same as number of arrays in ome zarr
    assert len(volume_gr) == len(list(ome_zarr_root.array_keys()))

    for volume_arr_resolution, volume_arr in ome_zarr_root.arrays():
        volume_3d_arr_shape = volume_arr[...].swapaxes(-3, -1).shape[-3:]

        assert str(volume_arr_resolution) in volume_gr
        assert isinstance(volume_gr[volume_arr_resolution], zarr.Group)

        # check number of time groups
        if len(axes) == 5 and axes[0]["name"] == "t":
            n_of_time_groups = volume_arr.shape[0]
        elif len(axes) == 4 and axes[0]["name"] == "c":
            n_of_time_groups = 1
        else:
            raise Exception("Axes number/order is not supported")

        assert len(volume_gr[volume_arr_resolution]) == n_of_time_groups

        # for each time group, check if number of channels == -4 dimension of volume_arr
        for time in range(n_of_time_groups):
            n_of_channel_groups = volume_arr.shape[-4]
            assert len(volume_gr[volume_arr_resolution][time]) == n_of_channel_groups

            # for each channel, check if shape is equal to shape of volume arr with swapaxes
            for channel in range(n_of_channel_groups):
                assert isinstance(
                    volume_gr[volume_arr_resolution][time][channel], zarr.core.Array
                )
                assert (
                    volume_gr[volume_arr_resolution][time][channel].shape
                    == volume_3d_arr_shape
                )
                # check dtype
                assert (
                    volume_gr[volume_arr_resolution][time][channel].dtype
                    == volume_arr.dtype
                )
                
    # remove omezarr
    shutil.rmtree(internal_volume.volume_input_path)
