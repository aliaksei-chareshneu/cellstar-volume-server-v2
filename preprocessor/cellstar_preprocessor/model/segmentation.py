from pathlib import Path
from typing import Optional, Union

from cellstar_preprocessor.model.input import DownsamplingParams, EntryData


class InternalSegmentation:
    def __init__(
        self,
        intermediate_zarr_structure_path: Path,
        segmentation_input_path: Union[Path, list[Path]],
        params_for_storing: dict,
        downsampling_parameters: DownsamplingParams,
        entry_data: EntryData,
        sphere_radius: Optional[float],
        color: Optional[float]
    ):
        self.intermediate_zarr_structure_path = intermediate_zarr_structure_path
        self.segmentation_input_path = segmentation_input_path
        self.params_for_storing = params_for_storing
        self.downsampling_parameters = downsampling_parameters
        self.primary_descriptor = None
        self.value_to_segment_id_dict: dict = {}
        self.simplification_curve: dict[int, float] = {}
        self.entry_data = entry_data
        self.raw_sff_annotations = {}
        self.sphere_radius = sphere_radius
        self.color = color