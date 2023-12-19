from cellstar_db.models import MeshComponentNumbers

from cellstar_preprocessor.flows.common import (
    get_downsamplings,
    open_zarr_structure_from_path,
)
from cellstar_preprocessor.model.input import SegmentationPrimaryDescriptor
from cellstar_preprocessor.model.segmentation import InternalSegmentation

def extract_metadata_geometric_segmentation(internal_segmentation: InternalSegmentation):
    root = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )
    metadata_dict = root.attrs["metadata_dict"]

    metadata_dict['geometric_segmentation'] = {
        'exists': True
    }

    root.attrs["metadata_dict"] = metadata_dict
    return metadata_dict
