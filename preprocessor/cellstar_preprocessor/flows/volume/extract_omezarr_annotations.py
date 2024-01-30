from uuid import uuid4
from cellstar_db.models import AnnotationsMetadata, DescriptionData, EntryId, SegmentAnnotationData, TargetId
from PIL import ImageColor

from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.model.volume import InternalVolume
import numpy as np
import zarr

def _get_label_time(label_value: int, label_gr: zarr.Group):
    timeframes_with_present_label = []
    # PLAN:
    # take first available resolution
    available_resolutions = sorted(label_gr.array_keys())
    first_resolution = available_resolutions[0]
    # loop over timeframes
    data = label_gr[first_resolution]
    time_dimension = data.shape[0]
    for time in range(time_dimension):
        # data has channel dimensions
        timeframe_data = data[time]
        assert timeframe_data.shape[0] == 1, 'NGFFs with labels having more than one channel are not supported'
        channel_data = timeframe_data[0]
        assert len(channel_data.shape) == 3

        present_labels = np.unique(channel_data[...])

        # if label is in present_labels
        # push timeframe index to timeframes_with_present_label
        if label_value in present_labels:
            timeframes_with_present_label.append(time)

    # at the end, if len(timeframes_with_present_label) == 1
    # => return timeframes_with_present_label[0]
    # else return timeframes_with_present_label

    if len(timeframes_with_present_label) == 1:
        return timeframes_with_present_label[0]
    else:
        return timeframes_with_present_label

def convert_hex_to_rgba_fractional(channel_color_hex):
    channel_color_rgba = ImageColor.getcolor(f"#{channel_color_hex}", "RGBA")
    channel_color_rgba_fractional = tuple([i / 255 for i in channel_color_rgba])
    return channel_color_rgba_fractional

def _get_channel_annotations(ome_zarr_attrs, volume_channel_annotations):
    for channel_id, channel in enumerate(ome_zarr_attrs["omero"]["channels"]):
        label = None if not channel['label'] else channel['label']
        volume_channel_annotations.append(
            {
                "channel_id": str(channel_id),
                "color": convert_hex_to_rgba_fractional(channel["color"]),
                "label": label,
            }
        )


# NOTE: Lattice IDs = Label groups
def extract_omezarr_annotations(internal_volume: InternalVolume):
    ome_zarr_root = open_zarr_structure_from_path(
        internal_volume.volume_input_path
    )
    root = open_zarr_structure_from_path(
        internal_volume.intermediate_zarr_structure_path
    )
    d: AnnotationsMetadata = root.attrs["annotations_dict"]

    d["entry_id"] = EntryId(
        source_db_id=internal_volume.entry_data.source_db_id,
        source_db_name=internal_volume.entry_data.source_db_name,
    )

    _get_channel_annotations(
        ome_zarr_attrs=ome_zarr_root.attrs,
        volume_channel_annotations=d["volume_channels_annotations"],
    )

    # TODO: omezarr annotations (image label) should have time
    # NOTE: how to get it?
    # first check if there is time dimension
    # 
    # for each label (label_value) check in which timeframe
    # of specific label_gr it is present
    # NOTE: assumes that if label is present in original resolution data
    # for that timeframe, it is present in downsamplings
    
    # time could be a range
    
    # time = 0
    if "labels" in ome_zarr_root:
        for label_gr_name, label_gr in ome_zarr_root.labels.groups():
            labels_metadata_list = label_gr.attrs["image-label"]["colors"]
            # support multiple lattices

            # for segment in intern.raw_sff_annotations["segment_list"]:
            for ind_label_meta in labels_metadata_list:
                # int to put to grid
                label_value = int(ind_label_meta["label-value"])
                ind_label_color_rgba = ind_label_meta["rgba"]
                # color
                ind_label_color_fractional = [i / 255 for i in ind_label_color_rgba]

                # need to create two things: description and segment annotation
                # create description
                description_id = str(uuid4())
                target_id: TargetId = {
                    'segment_id': label_value,
                    'segmentation_id': str(label_gr_name)
                }

                time = _get_label_time(label_value=label_value, label_gr=label_gr)
                description: DescriptionData = {
                    'id': description_id,
                    'target_kind': "lattice",
                    'description': None,
                    'is_hidden': None,
                    'metadata': None,
                    'time': time,
                    'name': f"segment {label_value}",
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
                d['annotations'].append(segment_annotation)
            
    root.attrs["annotations_dict"] = d
    return d
