
from cellstar_preprocessor.flows.segmentation.extract_annotations_from_sff_segmentation import extract_annotations_from_sff_segmentation
from cellstar_preprocessor.flows.segmentation.helper_methods import extract_raw_annotations_from_sff
from cellstar_preprocessor.flows.segmentation.sff_preprocessing import sff_preprocessing
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.tests.helper_methods import initialize_intermediate_zarr_structure_for_tests
from cellstar_preprocessor.tests.input_for_tests import INTERNAL_SEGMENTATION_FOR_TESTING
import pytest


def test_extract_annotations_from_sff_segmentation():
    internal_segmentation = INTERNAL_SEGMENTATION_FOR_TESTING
    initialize_intermediate_zarr_structure_for_tests()
    
    # NOTE: tests only three_d_volume segmentation, not mesh
    
    sff_preprocessing(internal_segmentation=internal_segmentation)
    d = extract_annotations_from_sff_segmentation(internal_segmentation=internal_segmentation)

    r = extract_raw_annotations_from_sff(internal_segmentation.segmentation_input_path)

    assert d["details"] == r["details"]
    assert d["name"] == r["name"]
    assert d["entry_id"]["source_db_id"] == internal_segmentation.entry_data.source_db_id
    assert d["entry_id"]["source_db_name"] == internal_segmentation.entry_data.source_db_name



    for segment in r["segment_list"]:
        lattice_id = str(segment["three_d_volume"]["lattice_id"])
        our_lattice = list(filter(lambda lat: lat["lattice_id"] == lattice_id, d["segmentation_lattices"]))[0]
        our_segment_list = our_lattice["segment_list"]
        our_segment = list(filter(lambda seg: seg["id"] == segment["id"], our_segment_list))[0]
        
        assert our_segment["biological_annotation"]["name"] == segment["biological_annotation"]["name"]
        assert our_segment["biological_annotation"]["external_references"] == segment["biological_annotation"]["external_references"]
        assert our_segment["color"] == segment["colour"]

    