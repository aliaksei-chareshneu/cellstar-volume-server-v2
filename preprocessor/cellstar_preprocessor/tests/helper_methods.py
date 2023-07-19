from cellstar_preprocessor.tests.input_for_tests import INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS
import zarr
import shutil

def initialize_intermediate_zarr_structure_for_tests():
    if INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS.exists():
        shutil.rmtree(INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS, ignore_errors=True)
    
    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(
        str(INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS)
    )
    root = zarr.group(store=store)