from cellstar_preprocessor.tests.input_for_tests import INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS
import zarr
import shutil

def initialize_intermediate_zarr_structure_for_tests():
    if INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS.exists():
        shutil.rmtree(INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS, ignore_errors=True)
    
    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(
        str(INTERMEDIATE_ZARR_STRUCTURE_PATH_FOR_TESTS)
    )
    root = zarr.group(store=store)

    root.attrs["metadata_dict"] = {
        "entry_id": {"source_db_name": None, "source_db_id": None},
        "volumes": {
            "channel_ids": [],
            # Values of time dimension
            "time_info": {
                "kind": "range",
                "start": None,
                "end": None,
                "units": None,
            },
            "volume_sampling_info": {
                # Info about "downsampling dimension"
                "spatial_downsampling_levels": [],
                # the only thing with changes with SPATIAL downsampling is box!
                "boxes": {},
                # time -> channel_id
                "descriptive_statistics": {},
                "time_transformations": [],
                "source_axes_units": None,
            },
            "original_axis_order": None,
        },
        "segmentation_lattices": {
            "segmentation_lattice_ids": [],
            "segmentation_sampling_info": {},
            "channel_ids": {},
            "time_info": {},
        },
        "segmentation_meshes": {
            "mesh_component_numbers": {},
            "detail_lvl_to_fraction": {},
        },
    }

    root.attrs["annotations_dict"] = {
        "entry_id": {"source_db_name": None, "source_db_id": None},
        "segmentation_lattices": [],
        "details": None,
        "name": None,
        "volume_channels_annotations": [],
    }