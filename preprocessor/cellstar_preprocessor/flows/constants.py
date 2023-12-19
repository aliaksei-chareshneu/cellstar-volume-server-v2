QUANTIZATION_DATA_DICT_ATTR_NAME = "quantization_data_dict"
LATTICE_SEGMENTATION_DATA_GROUPNAME = "_lattice_segmentation_data"
MESH_SEGMENTATION_DATA_GROUPNAME = "_mesh_segmentation_data"

VOLUME_DATA_GROUPNAME = "_volume_data"
VOLUME_DATA_GROUPNAME_COPY = "_volume_data_copy"

# TODO: the namespaces should NOT be hardcoded
DB_NAMESPACES = ("emdb", "empiar")

ZIP_STORE_DATA_ZIP_NAME = "data.zip"

# TODO: update VolumeServerDB to store the data directly??
ANNOTATION_METADATA_FILENAME = "annotations.json"
GRID_METADATA_FILENAME = "metadata.json"
GEOMETRIC_SEGMENTATION_FILENAME = "geometric_segmentation.json"

MIN_GRID_SIZE = 100**3
DOWNSAMPLING_KERNEL = (1, 4, 6, 4, 1)

MESH_SIMPLIFICATION_CURVE_LINEAR = {
    i + 1: (10 - i) / 10 for i in range(10)
}  # {1: 1.0, 2: 0.9, 3: 0.8, 4: 0.7, 5: 0.6, 6: 0.5, 7: 0.4, 8: 0.3, 9: 0.2, 10: 0.1}
MESH_SIMPLIFICATION_N_LEVELS = 10
MESH_SIMPLIFICATION_LEVELS_PER_ORDER = 4
MESH_VERTEX_DENSITY_THRESHOLD = {
    "area": 0,  # 0 = unlimited
    # 'area': 0.02,
    # 'volume': 0.0015,
}

SPACE_UNITS_CONVERSION_DICT = {"micrometer": 10000, "angstrom": 1}
