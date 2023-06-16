from pathlib import Path

from preprocessor_v2.preprocessor.model.input import DownsamplingParams


class InternalVolume:
    def __init__(self, intermediate_zarr_structure_path: Path,
                volume_input_path: Path,
                params_for_storing: dict,
                volume_force_dtype: str,
                downsampling_parameters: DownsamplingParams
                ):
        self.intermediate_zarr_structure_path = intermediate_zarr_structure_path
        self.volume_input_path = volume_input_path
        self.params_for_storing = params_for_storing
        self.volume_force_dtype = volume_force_dtype
        self.downsampling_parameters = downsampling_parameters
