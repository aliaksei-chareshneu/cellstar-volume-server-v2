from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import SEGMENTATION_DATA_GROUPNAME
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

    segmentation_data_gr = our_zarr_structure.create_group(SEGMENTATION_DATA_GROUPNAME)

    # TODO: get data from map
    with mrcfile.mmap(str(internal_segmentation.segmentation_input_path.resolve())) as mrc_original:
        data: np.memmap = mrc_original.data
        header = mrc_original.header

    data = _normalize_axis_order_mrcfile_numpy(arr=data, mrc_header=header)

    # artificially create value_to_segment_id_dict
    internal_segmentation.value_to_segment_id_dict = {}
    internal_segmentation.value_to_segment_id_dict[0] = {}
    for value in np.unique(data):
        internal_segmentation.value_to_segment_id_dict[0][int(value)] = int(value)

    lattice_gr = segmentation_data_gr.create_group(str(0))
    params_for_storing = internal_segmentation.params_for_storing

    store_segmentation_data_in_zarr_structure(
        original_data=data,
        lattice_data_group=lattice_gr,
        value_to_segment_id_dict_for_specific_lattice_id=internal_segmentation.value_to_segment_id_dict[
            0
        ],
        params_for_storing=params_for_storing,
    )
