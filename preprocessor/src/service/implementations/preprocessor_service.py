from pathlib import Path
from typing import List
from preprocessor.src.preprocessors.implementations.sff.preprocessor.sff_preprocessor import SFFPreprocessor

from preprocessor.src.preprocessors.i_data_preprocessor import IDataPreprocessor
from preprocessor.src.service.i_preprocessor_service import IPreprocessorService


class PreprocessorService(IPreprocessorService):
    def __init__(self, preprocessors: List[IDataPreprocessor]):
        # temp implementation, TODO: dict with keys 'SFF', 'OME-Zarr' etc., enum etc. or something else
        self.preprocessors = preprocessors

    def get_raw_file_type(self, file_path: Path) -> str:
        # temp implementation
        # if file_path.suffix == '.hff':
        return 'SFF'

    def get_preprocessor(self, file_type: str) -> IDataPreprocessor:
        # temp implementation
        return SFFPreprocessor()
