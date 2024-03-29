import abc
from pathlib import Path
from typing import Union
import numpy as np


class IDataPreprocessor(abc.ABC):
    @abc.abstractmethod
    def preprocess(self, segm_file_path: Path, volume_file_path: Path, params_for_storing: dict, volume_force_dtype: Union[np.dtype, None], entry_id: str,
        source_db_id: str,
        source_db_name: str):
        raise NotImplementedError
