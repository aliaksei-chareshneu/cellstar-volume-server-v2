
from cellstar_db.models import DescriptionData, SegmentAnnotationData
from cellstar_preprocessor.flows.segmentation.extract_annotations_from_sff_segmentation import extract_annotations_from_sff_segmentation
from cellstar_preprocessor.flows.segmentation.helper_methods import extract_raw_annotations_from_sff
from cellstar_preprocessor.flows.segmentation.sff_preprocessing import sff_preprocessing
from cellstar_preprocessor.model.input import SegmentationPrimaryDescriptor
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.tests.helper_methods import initialize_intermediate_zarr_structure_for_tests
from cellstar_preprocessor.tests.input_for_tests import INTERNAL_MESH_SEGMENTATION_FOR_TESTING, INTERNAL_SEGMENTATION_FOR_TESTING
import pytest

SEGMENTATIONS = [
    INTERNAL_SEGMENTATION_FOR_TESTING,
    INTERNAL_MESH_SEGMENTATION_FOR_TESTING
]

@pytest.mark.parametrize("internal_segmentation", SEGMENTATIONS)
def test_extract_annotations_from_sff_segmentation(internal_segmentation):
    initialize_intermediate_zarr_structure_for_tests()
    
    sff_preprocessing(internal_segmentation=internal_segmentation)
    d = extract_annotations_from_sff_segmentation(internal_segmentation=internal_segmentation)

    r = extract_raw_annotations_from_sff(internal_segmentation.segmentation_input_path)

    assert d["details"] == r["details"]
    assert d["name"] == r["name"]
    assert d["entry_id"]["source_db_id"] == internal_segmentation.entry_data.source_db_id
    assert d["entry_id"]["source_db_name"] == internal_segmentation.entry_data.source_db_name
    
    description_items = list(d['descriptions'].items())
    for segment in r["segment_list"]:
        description_filter_results = list(filter(lambda d: d[1]['target_segment_id'] == segment['id'], description_items))
        assert len(description_filter_results) == 1
        description_item: DescriptionData = description_filter_results[0][1]

        assert description_item['external_references'] == segment["biological_annotation"]["external_references"]
        assert description_item['name'] == segment["biological_annotation"]["name"]
        
        if internal_segmentation.primary_descriptor == SegmentationPrimaryDescriptor.three_d_volume:
            lattice_id: str = str(segment["three_d_volume"]["lattice_id"])
            assert description_item['target_lattice_id'] == lattice_id
            assert description_item['target_kind'] == 'lattice'

            # in segment annotations for that kind
            # which is a dict where keys are lattice ids
            # get segment by id
            # to do it get segment["three_d_volume"]["lattice_id"] 
            # and use that lattice_id to access dict
            segment_annotations: dict[str, dict[int, SegmentAnnotationData]] = d['segment_annotations']['lattice']
            segment_annotation_item = segment_annotations[lattice_id][segment['id']]
            
            # check each field
            assert segment_annotation_item["color"] == segment["colour"]
            assert segment_annotation_item["lattice_id"] == lattice_id
            assert segment_annotation_item["segment_id"] == segment["id"]
            assert segment_annotation_item['segment_kind'] == 'lattice'
            assert segment_annotation_item['time'] == 0
            
        elif internal_segmentation.primary_descriptor == SegmentationPrimaryDescriptor.mesh_list:
            # NOTE: only single set for meshes
            set_id = '0'
            assert description_item['target_set_id'] == set_id
            assert description_item['target_kind'] == 'mesh'

            segment_annotations: dict[str, dict[int, SegmentAnnotationData]] = d['segment_annotations']['mesh']
            segment_annotation_item = segment_annotations[set_id][segment['id']]

            # check each field
            assert segment_annotation_item["color"] == segment["colour"]
            assert segment_annotation_item["set_id"] == set_id
            assert segment_annotation_item["segment_id"] == segment["id"]
            assert segment_annotation_item['segment_kind'] == 'mesh'
            assert segment_annotation_item['time'] == 0

    