
# from cellstar_preprocessor.preprocess import main_preprocessor


# main_preprocessor()

# def test_modify_annotations(testing_entry_ctx):
#     testing_entry_ctx.modify(test_data)
    
#     annotations = testing_entry_ctx.query(...)
#     asset annotations["id1"]["description"] == test_data["id1"]["description"]

import asyncio
from cellstar_db.file_system.annotations_context import AnnnotationsEditContext
from cellstar_db.models import AnnotationsMetadata, SegmentAnnotationData

from cellstar_db.tests.conftest import TEST_ENTRY_PREPROCESSOR_INPUT
import pytest

@pytest.mark.asyncio
async def test_modify_annotations(generate_test_data):
    testing_db, test_data = generate_test_data
    # NOTE: here it should use annotations context
    # to modify annotations of test entry
    # add_or_modify
    # using test_data (list of annotations for example)
    # basically we do not need entry context, just test_db_context
    # in which entry will be created as well,
    # and it will yield db
    # we can create annotations context from db and entry_id and source_db
    with testing_db.edit_annotations(
        TEST_ENTRY_PREPROCESSOR_INPUT['source_db'],
        TEST_ENTRY_PREPROCESSOR_INPUT['entry_id']
    ) as edit_annotations_context:
        edit_annotations_context: AnnnotationsEditContext
        await edit_annotations_context.add_or_modify_segment_annotations(
            test_data['modify_annotations']
        )
    
        # NOTE: here it should get annotations of test entry
        # annotations = testing_entry_ctx.query(...)
        annotations_metadata: AnnotationsMetadata = await testing_db.read_annotations(
            TEST_ENTRY_PREPROCESSOR_INPUT['source_db'],
            TEST_ENTRY_PREPROCESSOR_INPUT['entry_id']
        )
        current_annotations = annotations_metadata['annotations']

        # NOTE: here it should check that annotations of test entry are equal
        # to those in test_data
        # can do it for annotation in annotations assert ... or other possibilities
        # asset annotations["id1"]["description"] == test_data["id1"]["description"]
        for annotation in test_data['modify_annotations']:
            # TODO: equality of dicts? should work
            # assert annotation ==
            # find that annotation by id
            filter_results = list(filter(lambda a: a['id'] == annotation['id'], current_annotations))
            assert len(filter_results) == 1
            existing_annotation = filter_results[0]
            # check if those are equal
            assert existing_annotation == annotation
