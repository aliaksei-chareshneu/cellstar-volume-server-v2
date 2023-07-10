from cellstar_db.models import EntryId
from PIL import ImageColor

from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.model.volume import InternalVolume


def _convert_hex_to_rgba_fractional(channel_color_hex):
    channel_color_rgba = ImageColor.getcolor(f"#{channel_color_hex}", "RGBA")
    channel_color_rgba_fractional = tuple([i / 255 for i in channel_color_rgba])
    return channel_color_rgba_fractional


def _get_channel_annotations(ome_zarr_attrs, volume_channel_annotations):
    for channel_id, channel in enumerate(ome_zarr_attrs["omero"]["channels"]):
        volume_channel_annotations.append(
            {
                "channel_id": channel_id,
                "color": _convert_hex_to_rgba_fractional(channel["color"]),
                "label": channel["label"],
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
    d = root.attrs["annotations_dict"]
    d["entry_id"] = EntryId(
        source_db_id=internal_volume.entry_data.source_db_id,
        source_db_name=internal_volume.entry_data.source_db_name,
    )

    _get_channel_annotations(
        ome_zarr_attrs=ome_zarr_root.attrs,
        volume_channel_annotations=d["volume_channels_annotations"],
    )

    if "labels" in ome_zarr_root:
        for label_gr_name, label_gr in ome_zarr_root.labels.groups():
            segmentation_lattice_info = {
                "lattice_id": label_gr_name,
                "segment_list": [],
            }
            labels_metadata_list = label_gr.attrs["image-label"]["colors"]
            for ind_label_meta in labels_metadata_list:
                label_value = ind_label_meta["label-value"]
                ind_label_color_rgba = ind_label_meta["rgba"]
                ind_label_color_fractional = [i / 255 for i in ind_label_color_rgba]

                segmentation_lattice_info["segment_list"].append(
                    {
                        "id": int(label_value),
                        "biological_annotation": {
                            "name": f"segment {label_value}",
                            "external_references": [],
                        },
                        "color": ind_label_color_fractional,
                    }
                )
            # append
            d["segmentation_lattices"].append(segmentation_lattice_info)

    root.attrs["annotations_dict"] = d
    return d
