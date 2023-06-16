from pathlib import Path

class InternalSegmentation:
    def __init__(self, intermediate_zarr_structure_path: Path,
                sff_input_path: Path,
                params_for_storing: dict,
                ):
        self.intermediate_zarr_structure_path = intermediate_zarr_structure_path
        self.sff_input_path = sff_input_path
        self.params_for_storing = params_for_storing
        