


from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.volume.extract_omezarr_annotations import convert_hex_to_rgba_fractional, extract_omezarr_annotations
from cellstar_preprocessor.model.volume import InternalVolume
from cellstar_preprocessor.tests.helper_methods import initialize_intermediate_zarr_structure_for_tests
from cellstar_preprocessor.tests.input_for_tests import INTERNAL_VOLUME_FOR_OMEZARR_TESTING_4_AXES, INTERNAL_VOLUME_FOR_OMEZARR_TESTING_5_AXES
import pytest


INTERNAL_VOLUMES = [
    INTERNAL_VOLUME_FOR_OMEZARR_TESTING_4_AXES,
    INTERNAL_VOLUME_FOR_OMEZARR_TESTING_5_AXES
]

@pytest.mark.parametrize("internal_volume", INTERNAL_VOLUMES)
def test_extract_omezarr_annotations(internal_volume: InternalVolume):
    initialize_intermediate_zarr_structure_for_tests()

    extract_omezarr_annotations(internal_volume=internal_volume)

    ome_zarr_root = open_zarr_structure_from_path(
        internal_volume.volume_input_path
    )
    ome_zarr_attrs = ome_zarr_root.attrs

    root = open_zarr_structure_from_path(
        internal_volume.intermediate_zarr_structure_path
    )

    d = root.attrs["annotations_dict"]

    assert d["entry_id"]["source_db_id"] == internal_volume.entry_data.source_db_id
    assert d["entry_id"]["source_db_name"] == internal_volume.entry_data.source_db_name

    for channel_id, channel in enumerate(ome_zarr_attrs["omero"]["channels"]):
        # PLAN
        # for each channel in omero channels
        # check if in volume channel annotations exist object with that channel_id
        # that its color is equal to channel color
        # that its label is equal to channel label
        assert list(filter(lambda v: v["channel_id"] == channel_id, d["volume_channels_annotations"]))[0]
        vol_ch_annotation = list(filter(lambda v: v["channel_id"] == channel_id, d["volume_channels_annotations"]))[0]

        assert vol_ch_annotation["color"] == list(convert_hex_to_rgba_fractional(channel["color"]))
        assert vol_ch_annotation["label"] == channel["label"]

    if "labels" in ome_zarr_root:
        for label_gr_name, label_gr in ome_zarr_root.labels.groups():
            # PLAN
            # for each label gr
            # check if there is object in d["segmentation_lattices"] with that lattice_id == label_gr_name
            assert list(filter(lambda lat: lat["lattice_id"] == label_gr_name, d["segmentation_lattices"]))[0]
            lat_obj = list(filter(lambda lat: lat["lattice_id"] == label_gr_name, d["segmentation_lattices"]))[0]

            labels_metadata_list = label_gr.attrs["image-label"]["colors"]
            for ind_label_meta in labels_metadata_list:
                label_value = ind_label_meta["label-value"]
                ind_label_color_rgba = ind_label_meta["rgba"]
                ind_label_color_fractional = [i / 255 for i in ind_label_color_rgba]

                # check that in lat_obj["segment_list"] there is object with id == label_value
                # and that its name correspond to lavel value
                # its color correspond to ind_label_color_fractional
                assert list(filter(lambda seg: seg["id"] == int(label_value), lat_obj["segment_list"]))[0]
                seg = list(filter(lambda seg: seg["id"] == int(label_value), lat_obj["segment_list"]))[0]

                assert seg["biological_annotation"]["name"] == f"segment {label_value}"
                assert seg["color"] == ind_label_color_fractional