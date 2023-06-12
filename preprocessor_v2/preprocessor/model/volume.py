class Volume:
    def __init__(self, intermediate_zarr_structure_path,
                volume_input_path,
                params_for_storing,
                volume_force_dtype,
                downsampling_parameters
                ):
        self.intermediate_zarr_structure_path = intermediate_zarr_structure_path
        self.volume_input_path = volume_input_path
        self.params_for_storing = params_for_storing
        self.volume_force_dtype = volume_force_dtype
        self.downsampling_parameters = downsampling_parameters

        self.metadata = {}
        

    # no arguments, uses class attributes inside
    def volume_map_preprocessing():
        # 1. normalize axis order
        # 2. extract/compute metadata
        # 3. add volume data to intermediate zarr structure
        pass
    
    def volume_downsampling():
        pass

