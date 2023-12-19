
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.flows.segmentation.ome_zarr_labels_preprocessing import ome_zarr_labels_preprocessing
from cellstar_preprocessor.flows.segmentation.sff_preprocessing import sff_preprocessing
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.tests.helper_methods import initialize_intermediate_zarr_structure_for_tests
from cellstar_preprocessor.tests.input_for_tests import INTERNAL_SEGMENTATION_FOR_OMEZARR_TESTING_4_AXES, INTERNAL_SEGMENTATION_FOR_OMEZARR_TESTING_5_AXES
import zarr
import pytest

INTERNAL_SEGMENTATIONS = [
    INTERNAL_SEGMENTATION_FOR_OMEZARR_TESTING_4_AXES,
    INTERNAL_SEGMENTATION_FOR_OMEZARR_TESTING_5_AXES
]

@pytest.mark.parametrize("internal_segmentation", INTERNAL_SEGMENTATIONS)
def test_ome_zarr_labels_preprocessing(internal_segmentation: InternalSegmentation):
    initialize_intermediate_zarr_structure_for_tests()
    
    ome_zarr_labels_preprocessing(internal_segmentation=internal_segmentation)

    zarr_structure = open_zarr_structure_from_path(internal_segmentation.intermediate_zarr_structure_path)

    ome_zarr_root = zarr.open_group(internal_segmentation.segmentation_input_path)

    assert LATTICE_SEGMENTATION_DATA_GROUPNAME in zarr_structure
    segmentation_gr = zarr_structure[LATTICE_SEGMENTATION_DATA_GROUPNAME]
    assert isinstance(segmentation_gr, zarr.hierarchy.Group)
    # check if number of label groups is the same as number of groups in ome zarr
    assert len(segmentation_gr) == len(list(ome_zarr_root.labels.group_keys()))

    for label_gr_name, label_gr in ome_zarr_root.labels.groups():
        label_gr_zattrs = label_gr.attrs
        label_gr_multiscales = label_gr_zattrs["multiscales"]
        # NOTE: can be multiple multiscales, here picking just 1st
        axes = label_gr_multiscales[0]["axes"]

        for arr_resolution, arr in label_gr.arrays():
            segm_3d_arr_shape = arr[...].swapaxes(-3, -1).shape[-3:] 
            # i8 is not supported by CIFTools
            if arr.dtype == "i8":
                segm_3d_arr_dtype = "i4"
            else:
                segm_3d_arr_dtype = arr.dtype

            assert str(arr_resolution) in segmentation_gr[label_gr_name]
            assert isinstance(segmentation_gr[label_gr_name][arr_resolution], zarr.hierarchy.Group)
            
            # check number of time groups
            if len(axes) == 5 and axes[0]["name"] == "t":
                n_of_time_groups = arr.shape[0]
            elif len(axes) == 4 and axes[0]["name"] == "c":
                n_of_time_groups = 1
            else:
                raise Exception("Axes number/order is not supported")
            
            assert len(segmentation_gr[label_gr_name][arr_resolution]) == n_of_time_groups


            # for each time group, check if number of channels == -4 dimension of arr
            for time in range(n_of_time_groups):
                n_of_channel_groups = arr.shape[-4]
                assert len(segmentation_gr[label_gr_name][arr_resolution][time]) == n_of_channel_groups

                # for each channel, check if shape is equal to shape of volume arr with swapaxes
                for channel in range(n_of_channel_groups):
                    assert isinstance(segmentation_gr[label_gr_name][arr_resolution][time][channel], zarr.hierarchy.Group)
                    assert 'grid' in segmentation_gr[label_gr_name][arr_resolution][time][channel]
                    assert segmentation_gr[label_gr_name][arr_resolution][time][channel].grid.shape == segm_3d_arr_shape
                    assert segmentation_gr[label_gr_name][arr_resolution][time][channel].grid.dtype == segm_3d_arr_dtype

                    assert 'set_table' in segmentation_gr[label_gr_name][arr_resolution][time][channel]
                    assert segmentation_gr[label_gr_name][arr_resolution][time][channel].set_table.shape == (1,)





    