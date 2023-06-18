from pathlib import Path

from preprocessor_v2.preprocessor.model.input import DownsamplingParams

class InternalSegmentation:
    def __init__(self, intermediate_zarr_structure_path: Path,
                sff_input_path: Path,
                params_for_storing: dict,
                downsampling_parameters: DownsamplingParams
                ):
        self.intermediate_zarr_structure_path = intermediate_zarr_structure_path
        self.sff_input_path = sff_input_path
        self.params_for_storing = params_for_storing
        self.downsampling_parameters = downsampling_parameters
        self.primary_descriptor = None
        self.value_to_segment_id_dict: dict = {}
        self.simplification_curve: dict[int, float] = {}