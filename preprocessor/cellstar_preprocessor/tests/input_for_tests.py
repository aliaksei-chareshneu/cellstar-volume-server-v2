from pathlib import Path
from typing import TypedDict

from cellstar_preprocessor.model.input import (
    DownsamplingParams,
    EntryData,
    QuantizationDtype,
    StoringParams,
)
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.model.volume import InternalVolume

INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS = Path(
    "preprocessor/cellstar_preprocessor/tests/test_data/intermediate_zarr_structure_for_tests"
)

PATH_TO_TEST_DATA_DIR: Path = Path('preprocessor/cellstar_preprocessor/tests/test_data')
    
TEST_MAP_PATH = Path("test-data/preprocessor/sample_volumes/emdb_sff/EMD-1832.map")
TEST_SFF_PATH = Path(
    "test-data/preprocessor/sample_segmentations/emdb_sff/emd_1832.hff"
)
TEST_MESH_SFF_PATH = Path(
    "test-data/preprocessor/sample_segmentations/empiar/empiar_10070_b3talongmusc20130301.hff"
)
TEST_MAP_PATH_ZYX_ORDER = Path(
    "preprocessor/cellstar_preprocessor/tests/test_data/fake_ccp4_ZYX.map"
)
TEST_MAP_PATH_XYZ_ORDER = Path(
    "preprocessor/cellstar_preprocessor/tests/test_data/fake_ccp4_XYZ.map"
)

class OMEZarrTestInput(TypedDict):
    url: str
    entry_id: str
    source_db: str

OMEZARR_TEST_INPUTS = [
    OMEZarrTestInput(
        url='https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0062A/6001240.zarr',
        entry_id='idr-6001240',
        source_db='idr'
    ),
    OMEZarrTestInput(
        url='https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0101A/13457537.zarr',
        entry_id='idr-13457537',
        source_db='idr'
    ),
]

INTERNAL_VOLUME_FOR_TESTING_XYZ_ORDER = InternalVolume(
    intermediate_zarr_structure_path=INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS,
    volume_input_path=TEST_MAP_PATH_XYZ_ORDER,
    params_for_storing=StoringParams(),
    volume_force_dtype="f2",
    downsampling_parameters=DownsamplingParams(),
    entry_data=EntryData(
        entry_id="emd-555555",
        source_db="emdb",
        source_db_id="emd-555555",
        source_db_name="emdb",
    ),
    quantize_dtype_str=QuantizationDtype.u1,
    quantize_downsampling_levels=(1,),
)

INTERNAL_VOLUME_FOR_TESTING_ZYX_ORDER = InternalVolume(
    intermediate_zarr_structure_path=INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS,
    volume_input_path=TEST_MAP_PATH_ZYX_ORDER,
    params_for_storing=StoringParams(),
    volume_force_dtype="f2",
    downsampling_parameters=DownsamplingParams(),
    entry_data=EntryData(
        entry_id="emd-555555",
        source_db="emdb",
        source_db_id="emd-555555",
        source_db_name="emdb",
    ),
    quantize_dtype_str=QuantizationDtype.u1,
    quantize_downsampling_levels=(1,),
)


INTERNAL_VOLUME_FOR_TESTING = InternalVolume(
    intermediate_zarr_structure_path=INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS,
    volume_input_path=TEST_MAP_PATH,
    params_for_storing=StoringParams(),
    volume_force_dtype="f2",
    downsampling_parameters=DownsamplingParams(),
    entry_data=EntryData(
        entry_id="emd-1832",
        source_db="emdb",
        source_db_id="emd-1832",
        source_db_name="emdb",
    ),
    quantize_dtype_str=QuantizationDtype.u1,
    quantize_downsampling_levels=(1,),
)

INTERNAL_SEGMENTATION_FOR_TESTING = InternalSegmentation(
    intermediate_zarr_structure_path=INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS,
    segmentation_input_path=TEST_SFF_PATH,
    params_for_storing=StoringParams(),
    downsampling_parameters=DownsamplingParams(),
    entry_data=EntryData(
        entry_id="emd-1832",
        source_db="emdb",
        source_db_id="emd-1832",
        source_db_name="emdb",
    ),
)

INTERNAL_MESH_SEGMENTATION_FOR_TESTING = InternalSegmentation(
    intermediate_zarr_structure_path=INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS,
    segmentation_input_path=TEST_MESH_SFF_PATH,
    params_for_storing=StoringParams(),
    downsampling_parameters=DownsamplingParams(),
    entry_data=EntryData(
        entry_id="empiar-10070",
        source_db="empiar",
        source_db_id="empiar-10070",
        source_db_name="empiar",
    ),
)
