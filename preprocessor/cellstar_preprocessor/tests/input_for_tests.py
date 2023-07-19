from pathlib import Path
from cellstar_preprocessor.model.input import DownsamplingParams, EntryData, QuantizationDtype, StoringParams
from cellstar_preprocessor.model.volume import InternalVolume

DB_PATH_FOR_TESTS = Path('temp/db_for_tests')
INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS = Path('temp/intermediate_zarr_structure_for_tests')
TEST_MAP_PATH = Path('test-data/preprocessor/sample_volumes/emdb_sff/EMD-1832.map')


INTERNAL_VOLUME_FOR_TESTING = InternalVolume(
        intermediate_zarr_structure_path=INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS,
        volume_input_path=TEST_MAP_PATH,
        params_for_storing=StoringParams(),
        volume_force_dtype='f2',
        downsampling_parameters=DownsamplingParams(),
        entry_data=EntryData(
            entry_id="emd-1832",
            source_db="emdb",
            source_db_id="emd-1832",
            source_db_name="emdb",
        ),
        quantize_dtype_str=QuantizationDtype.u1,
        quantize_downsampling_levels=(1,)
    )

# INTERNAL_VOLUME_FOR_TESTING = InternalVolume(
#         intermediate_zarr_structure_path=INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS,
#         volume_input_path=TEST_MAP_PATH,
#         params_for_storing=StoringParams(),
#         volume_force_dtype='f2',
#         downsampling_parameters=DownsamplingParams(max_downsampling_level=),
#         entry_data=EntryData(
#             entry_id="emd-1832",
#             source_db="emdb",
#             source_db_id="emd-1832",
#             source_db_name="emdb",
#         ),
#         quantize_dtype_str=QuantizationDtype.u1,
#         quantize_downsampling_levels=(1,)
#     )