from pathlib import Path
import shutil

from cellstar_preprocessor.model.input import DownsamplingParams, EntryData, StoringParams
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.model.volume import InternalVolume
import zarr
from cellstar_preprocessor.flows.constants import (
    INIT_ANNOTATIONS_DICT,
    INIT_METADATA_DICT,
)
from cellstar_preprocessor.tests.input_for_tests import (
    INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS,
    PATH_TO_TEST_DATA_DIR,
    OMEZarrTestInput,
)
import ome_zarr
import ome_zarr.utils

def initialize_intermediate_zarr_structure_for_tests():
    if INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS.exists():
        shutil.rmtree(INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS, ignore_errors=True)

    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(
        str(INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS)
    )
    root = zarr.group(store=store)

    root.attrs["metadata_dict"] = INIT_METADATA_DICT
    root.attrs["annotations_dict"] = INIT_ANNOTATIONS_DICT

def get_omezarr_internal_volume(omezar_test_input: OMEZarrTestInput):
    p = _download_omezarr_for_tests(omezar_test_input['url'])
    internal_volume = InternalVolume(
        intermediate_zarr_structure_path=INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS,
        volume_input_path=p,
        params_for_storing=StoringParams(),
        volume_force_dtype=None,
        downsampling_parameters=DownsamplingParams(),
        entry_data=EntryData(
            entry_id=omezar_test_input["entry_id"],
            source_db=omezar_test_input["source_db"],
            source_db_id=omezar_test_input["entry_id"],
            source_db_name=omezar_test_input['source_db'],
        ),
        quantize_dtype_str=None,
        quantize_downsampling_levels=None,
    )
    return internal_volume

def get_omezarr_internal_segmentation(omezar_test_input: OMEZarrTestInput):
    p = _download_omezarr_for_tests(omezar_test_input['url'])
    internal_segmentation = InternalSegmentation(
    intermediate_zarr_structure_path=INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS,
    segmentation_input_path=p,
    params_for_storing=StoringParams(),
    downsampling_parameters=DownsamplingParams(),
    entry_data=EntryData(
        entry_id=omezar_test_input["entry_id"],
        source_db=omezar_test_input["source_db"],
        source_db_id=omezar_test_input["entry_id"],
        source_db_name=omezar_test_input['source_db'],
        ),
    )
    return internal_segmentation



def _download_omezarr_for_tests(url: str):
    omezarr_name = url.split('/')[-1]
    # omezarr_unique_subfolder = PATH_TO_TEST_DATA_DIR / unique_subfolder
    omezarr_path = PATH_TO_TEST_DATA_DIR / omezarr_name
    if not omezarr_path.exists():
        # shutil.rmtree(omezarr_path)
    # get omezarr_path here
        ome_zarr.utils.download(url, str(PATH_TO_TEST_DATA_DIR.resolve()))
    return omezarr_path