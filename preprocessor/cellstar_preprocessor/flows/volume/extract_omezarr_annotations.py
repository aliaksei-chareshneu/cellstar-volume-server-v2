from uuid import uuid4
from cellstar_db.models import AnnotationsMetadata, DescriptionData, EntryId, SegmentAnnotationData, TargetId
from PIL import ImageColor

from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.model.volume import InternalVolume


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

    # omezarr annotations (image label) have no time dimension?
    time = 0
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
                d['segment_annotations'].append(segment_annotation)
            
    root.attrs["annotations_dict"] = d
    return d
