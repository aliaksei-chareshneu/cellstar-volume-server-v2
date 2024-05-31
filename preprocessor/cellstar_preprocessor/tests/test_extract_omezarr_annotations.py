import pytest
from cellstar_db.models import (
    AnnotationsMetadata,
    DescriptionData,
    SegmentAnnotationData,
)
from cellstar_preprocessor.flows.common import (
    convert_hex_to_rgba_fractional,
    open_zarr_structure_from_path,
)
from cellstar_preprocessor.flows.segmentation.ome_zarr_labels_preprocessing import (
    ome_zarr_labels_preprocessing,
)
from cellstar_preprocessor.flows.volume.extract_omezarr_annotations import (
    extract_omezarr_annotations,
)
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.model.volume import InternalVolume
from cellstar_preprocessor.tests.helper_methods import (
    initialize_intermediate_zarr_structure_for_tests,
)
from cellstar_preprocessor.tests.input_for_tests import (
    INTERNAL_SEGMENTATION_FOR_OMEZARR_TESTING_4_AXES,
    INTERNAL_SEGMENTATION_FOR_OMEZARR_TESTING_5_AXES,
    INTERNAL_VOLUME_FOR_OMEZARR_TESTING_4_AXES,
    INTERNAL_VOLUME_FOR_OMEZARR_TESTING_5_AXES,
)

# Pair internal volumes and segmentations here

INTERNAL_VOLUMES_AND_SEGMENTATIONS = [
    (
        INTERNAL_VOLUME_FOR_OMEZARR_TESTING_4_AXES,
        INTERNAL_SEGMENTATION_FOR_OMEZARR_TESTING_4_AXES,
    ),
    (
        INTERNAL_VOLUME_FOR_OMEZARR_TESTING_5_AXES,
        INTERNAL_SEGMENTATION_FOR_OMEZARR_TESTING_5_AXES,
    ),
]


@pytest.mark.parametrize(
    "internal_volume_and_segmentation", INTERNAL_VOLUMES_AND_SEGMENTATIONS
)
def test_extract_omezarr_annotations(
    internal_volume_and_segmentation: tuple[InternalVolume, InternalSegmentation]
):
    initialize_intermediate_zarr_structure_for_tests()

    # most likely
    # should produce some zarr structure first
    # with segmentation
    # do ome_zarr_labels_preprocessing
    internal_volume = internal_volume_and_segmentation[0]
    internal_segmentation = internal_volume_and_segmentation[1]

    ome_zarr_labels_preprocessing(internal_segmentation=internal_segmentation)
    d: AnnotationsMetadata = extract_omezarr_annotations(
        internal_volume=internal_volume
    )

    ome_zarr_root = open_zarr_structure_from_path(internal_volume.volume_input_path)
    ome_zarr_attrs = ome_zarr_root.attrs

    # root = open_zarr_structure_from_path(
    #     internal_volume.intermediate_zarr_structure_path
    # )

    # d = root.attrs["annotations_dict"]

    assert d["entry_id"]["source_db_id"] == internal_volume.entry_data.source_db_id
    assert d["entry_id"]["source_db_name"] == internal_volume.entry_data.source_db_name

    description_items = list(d["descriptions"].items())

    for channel_id, channel in enumerate(ome_zarr_attrs["omero"]["channels"]):
        # PLAN
        # for each channel in omero channels
        # check if in volume channel annotations exist object with that channel_id
        # that its color is equal to channel color
        # that its label is equal to channel label
        assert list(
            filter(
                lambda v: v["channel_id"] == str(channel_id),
                d["volume_channels_annotations"],
            )
        )[0]
        vol_ch_annotation = list(
            filter(
                lambda v: v["channel_id"] == str(channel_id),
                d["volume_channels_annotations"],
            )
        )[0]

        assert vol_ch_annotation["color"] == convert_hex_to_rgba_fractional(
            channel["color"]
        )
        assert vol_ch_annotation["label"] == channel["label"]

    if "labels" in ome_zarr_root:
        for label_gr_name, label_gr in ome_zarr_root.labels.groups():
            # PLAN
            # for each label gr
            # check if for each

            # # check if there is object in d["segmentation_lattices"] with that lattice_id == label_gr_name
            # assert list(filter(lambda lat: lat["lattice_id"] == label_gr_name, d["segmentation_lattices"]))[0]
            # lat_obj = list(filter(lambda lat: lat["lattice_id"] == label_gr_name, d["segmentation_lattices"]))[0]

            labels_metadata_list = label_gr.attrs["image-label"]["colors"]
            for ind_label_meta in labels_metadata_list:
                label_value = int(ind_label_meta["label-value"])
                ind_label_color_rgba = ind_label_meta["rgba"]
                ind_label_color_fractional = [i / 255 for i in ind_label_color_rgba]

                # find description
                description_filter_results = list(
                    filter(
                        lambda d: d[1]["target_id"]["segment_id"] == label_value
                        and d[1]["target_id"]["segmentation_id"] == label_gr_name,
                        description_items,
                    )
                )
                assert len(description_filter_results) == 1
                description_item: DescriptionData = description_filter_results[0][1]

                # check that
                assert description_item["target_id"]["segment_id"] == label_value
                assert description_item["target_id"]["segmentation_id"] == label_gr_name
                assert description_item["target_kind"] == "lattice"

                # find segment annotation
                segment_annotations: list[SegmentAnnotationData] = d[
                    "segment_annotations"
                ]
                segment_annotation_filter_results = list(
                    filter(
                        lambda a: a["segment_id"] == label_value
                        and a["segment_kind"] == "lattice"
                        and a["segmentation_id"] == label_gr_name,
                        segment_annotations,
                    )
                )
                assert len(segment_annotation_filter_results) == 1
                segment_annotation_item: SegmentAnnotationData = (
                    segment_annotation_filter_results[0]
                )

                # check each field
                assert segment_annotation_item["color"] == ind_label_color_fractional
                assert segment_annotation_item["segment_id"] == label_value
                assert segment_annotation_item["segment_kind"] == "lattice"
                # can be not 0
                # assert segment_annotation_item['time'] == 0
