import shutil

import zarr
from cellstar_preprocessor.flows.constants import (
    INIT_ANNOTATIONS_DICT,
    INIT_METADATA_DICT,
)
from cellstar_preprocessor.tests.input_for_tests import (
    INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS,
)


def initialize_intermediate_zarr_structure_for_tests():
    if INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS.exists():
        shutil.rmtree(INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS, ignore_errors=True)

    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(
        str(INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS)
    )
    root = zarr.group(store=store)

    root.attrs["metadata_dict"] = INIT_METADATA_DICT
    root.attrs["annotations_dict"] = INIT_ANNOTATIONS_DICT
