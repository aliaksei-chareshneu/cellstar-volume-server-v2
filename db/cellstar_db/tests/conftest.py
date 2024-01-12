import asyncio
from pathlib import Path
from typing import TypedDict
from cellstar_db.file_system.db import FileSystemVolumeServerDB
from cellstar_db.models import AnnotationsMetadata, SegmentAnnotationData
import pytest
from cellstar_preprocessor.preprocess import main_preprocessor
import copy

TEST_DB_FOLDER = Path('db/cellstar_db/tests/test_data/testing_db')
TEST_ENTRY_INPUT_PATHS = [
    Path('test-data/preprocessor/sample_volumes/emdb_sff/EMD-1832.map'),
    Path('test-data/preprocessor/sample_segmentations/emdb_sff/emd_1832.hff')
]
TEST_ENTRY_INPUT_KINDS = [
    'map',
    'sff'
]

TEST_ENTRY_PREPROCESSOR_INPUT = dict(
    mode='add',
    quantize_dtype_str=None,
    quantize_downsampling_levels=None,
    force_volume_dtype=None,
    max_size_per_channel_mb=None,
    min_downsampling_level=None,
    max_downsampling_level=None,
    entry_id='emd-1832',
    source_db='emdb',
    source_db_id='emd-1832',
    source_db_name='emdb',
    working_folder=Path('db/cellstar_db/tests/test_data/testing_working_folder'),
    db_path=TEST_DB_FOLDER,
    input_paths=TEST_ENTRY_INPUT_PATHS,
    input_kinds=TEST_ENTRY_INPUT_KINDS
)

@pytest.fixture(scope="module")
def testing_db():
    # create db
    if TEST_DB_FOLDER.is_dir() == False:
        TEST_DB_FOLDER.mkdir()

    db = FileSystemVolumeServerDB(
        folder=TEST_DB_FOLDER,
        store_type='zip'
    )

    # remove previous test entry if it exists
    exists = asyncio.run(db.contains(
        TEST_ENTRY_PREPROCESSOR_INPUT['source_db'],
        TEST_ENTRY_PREPROCESSOR_INPUT['entry_id']
    ))
    if exists:
        asyncio.run(db.delete(
            TEST_ENTRY_PREPROCESSOR_INPUT['source_db'],
            TEST_ENTRY_PREPROCESSOR_INPUT['entry_id']
        ))

    # create test entry with annotations
    # NOTE: for now just could be emd-1832 sff, 6 descriptions, 6 segment annotations
    # TODO: in future can add to emd-1832 map and sff also geometric segmentation
    # but for testing annotations context emd-1832 sff is sufficient
    asyncio.run(
        main_preprocessor(
            **TEST_ENTRY_PREPROCESSOR_INPUT
        )
    )
    
    yield db

# to modify annotations we need to know annotation ids
# how to get them?
# from annotations of testing entry
# can be done in conftest as well
# via another function with fixture

# test data may look like dictionary
# with fields
# modify annotations
# add annotations
# modify descriptions
# add descriptions
# for now just a single field - modify annotations

# TEST_DATA: list[SegmentAnnotationData] = [
#     SegmentAnnotationData(
#         id=
#     )
# ]

FAKE_SEGMENT_ANNOTATIONS = [
    {
        "color": [
            0, 0, 0, 1.0
        ],
        "id": "whatever_1",
        "segment_id": 9999999999999,
        "segment_kind": "lattice",
        "segmentation_id": "999999999",
        "time": 999999999999999
    },
    {
        "color": [
            1.0, 1.0, 1.0, 1.0
        ],
        "id": "whatever_2",
        "segment_id": 888888888,
        "segment_kind": "lattice",
        "segmentation_id": "888888888",
        "time": 8888888888
    },
    # {
    #     "color": [
    #         0.706890761852264,
    #         0.626759827136993,
    #         0.604495763778687,
    #         1.0
    #     ],
    #     "id": "a8e24249-e42b-4c89-9b7b-3eee6eb46f32",
    #     "segment_id": 103,
    #     "segment_kind": "lattice",
    #     "segmentation_id": "0",
    #     "time": 0
    # },
    # {
    #     "color": [
    #         0.787909328937531,
    #         0.924791157245636,
    #         0.951091408729553,
    #         1.0
    #     ],
    #     "id": "162dbfcc-77f2-474d-82cb-bf8088b903b4",
    #     "segment_id": 104,
    #     "segment_kind": "lattice",
    #     "segmentation_id": "0",
    #     "time": 0
    # }
]

class TestData(TypedDict):
    modify_annotations: list[SegmentAnnotationData]

def _generate_test_data_for_modify_annotations(testing_db) -> list[SegmentAnnotationData]:
    # first get existing annotation ids from testing db
    annotations: AnnotationsMetadata = asyncio.run(testing_db.read_annotations(
        TEST_ENTRY_PREPROCESSOR_INPUT['source_db'],
        TEST_ENTRY_PREPROCESSOR_INPUT['entry_id']
    ))
    fake_segment_annotations = copy.deepcopy(FAKE_SEGMENT_ANNOTATIONS)
    existing_annotation_ids = [a['id'] for a in annotations['annotations']]
    first_fake_segment_annotation = fake_segment_annotations[0]
    first_fake_segment_annotation['id'] = existing_annotation_ids[0]
    second_fake_segment_annotation = fake_segment_annotations[1]
    second_fake_segment_annotation['id'] = existing_annotation_ids[1]

    return [
        first_fake_segment_annotation,
        second_fake_segment_annotation
    ]

def _generate_test_data_for_add_annotations() -> list[SegmentAnnotationData]:
    return [
        FAKE_SEGMENT_ANNOTATIONS[0],
        FAKE_SEGMENT_ANNOTATIONS[1]
    ]

@pytest.fixture(scope="module")
def generate_test_data(testing_db):
    test_data: TestData = {
        'modify_annotations': []
    }
    
    test_data['modify_annotations'] = _generate_test_data_for_modify_annotations(testing_db)
    test_data['add_annotations'] = _generate_test_data_for_add_annotations()
    yield testing_db, test_data