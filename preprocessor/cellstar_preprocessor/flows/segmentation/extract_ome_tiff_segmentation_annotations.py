from decimal import Decimal
from uuid import uuid4
from cellstar_db.models import AnnotationsMetadata, DescriptionData, DetailsText, SegmentAnnotationData, TargetId, TimeInfo, VolumeSamplingInfo, VolumesMetadata
from cellstar_preprocessor.flows.common import get_downsamplings, get_ometiff_source_metadata, open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME, QUANTIZATION_DATA_DICT_ATTR_NAME, VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.common import _convert_to_angstroms
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.model.volume import InternalVolume
from cellstar_preprocessor.tools.quantize_data.quantize_data import decode_quantized_data
import dask.array as da
import numpy as np
import zarr
import seaborn as sns

def _get_allencell_cell_stage(root: zarr.Group):
    return root.attrs['extra_data']['cell_stage']


def extract_ome_tiff_segmentation_annotations(internal_segmentation: InternalSegmentation):
    root = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )
    # this is based on Channels which is wrong in many cases


    ometiff_metadata = get_ometiff_source_metadata(internal_segmentation)
    d: AnnotationsMetadata = root.attrs["annotations_dict"]

    # PLAN: iterate over lattices
    # single value 255 - hardcoded (it is in specification)
    # name - lattice name
    # that is it
    # create palette

    # NOTE: in general case assume that Channels are wrong
    # create palette based on custom_data?
    # artificial channel ids are there?
    # now they are


    palette = sns.color_palette(None, len(list(internal_segmentation.custom_data['segmentation_ids_mapping'].keys())))

    # palette = sns.color_palette(None, len(ometiff_metadata['Channels'].keys()))
    
    # TODO: handle cell stage based on custom data
    # cell_stage = _get_allencell_cell_stage(root)
    # d['name'] = f'Cell stage: {cell_stage}'
    
    # each has its own color from palette
    # does not matter which
    count = 0

    for label_gr_name, label_gr in root[LATTICE_SEGMENTATION_DATA_GROUPNAME].groups():
        # each label group is lattice id
        lattice_id = label_gr_name
        
        # NOTE: hardcoded in specs
        label_value = 255
        # TODO: no color - generate palette above the loop
        # ind_label_color_rgba = ind_label_meta["rgba"]
        # # color
        # ind_label_color_fractional = [i / 255 for i in ind_label_color_rgba]
        ind_label_color_fractional = [
            palette[count][0],
            palette[count][1],
            palette[count][2],
            1.0
        ]
        # need to create two things: description and segment annotation
        # create description
        description_id = str(uuid4())
        target_id: TargetId = {
            'segment_id': label_value,
            'segmentation_id': str(label_gr_name)
        }

        time = 0
        description: DescriptionData = {
            'id': description_id,
            'target_kind': "lattice",
            'details': None,
            'is_hidden': None,
            'metadata': None,
            'time': time,
            'name': label_gr_name,
            'external_references': [],
            'target_id': target_id
        }
        
        segment_annotation: SegmentAnnotationData = {
            'id': str(uuid4()),
            'color': ind_label_color_fractional,
            'segmentation_id': str(label_gr_name),
            'segment_id': label_value,
            'segment_kind': 'lattice',
            'time': time
        }
        d['descriptions'][description_id] = description
        d['segment_annotations'].append(segment_annotation)

        count = count + 1
    
    root.attrs["annotations_dict"] = d
    return d