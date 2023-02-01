from typing import Optional, Union


class VolumeDescriptiveStatistics:
    mean: float
    min: float
    max: float
    std: float

# scale transformation only
# translate transformation from NGFF can be represented in origin (computed upfront)
class BoxScaleTransformation:
    # to which downsampling level it is applied: can be to specific level, can be to all lvls
    downsampling_level: Union[int, str]
    vector: list[int, int, int]


class TimeTransformation:
    # to which downsampling level it is applied: can be to specific level, can be to all lvls
    downsampling_level: Union[int, str] 
    factor: float

class ChannelsMetadata:
    ids: list[int]
    # channel_id -> channel color
    colors: dict[int, list[int, int, int]]
    # channel_id -> channel label; from omero - channels (e.g. "DAPI")
    labels: Optional[dict[int, str]]

class VolumesMetadata:
    channels: ChannelsMetadata
    # Values of time dimension
    time_info: { 'kind': 'range', start: int, end: int }
    time_units: str
    transformations: list[Union[BoxScaleTransformation, TimeTransformation]]
    # Info about "downsampling dimension"
    spatial_downsampling_levels: list[int]
    # the only thing with changes with SPATIAL downsampling is box!
    sampling_boxes: dict[int, {
        'origin': list[int, int, int],
        'voxel_size': list[int, int, int],
        'grid_dimensions': list[int, int, int],
        'volume_force_dtype': str
    }]
    # time -> channel_id
    descriptive_statistics: dict[int, dict[int, VolumeDescriptiveStatistics]]
    
class SegmentationsMetadata(VolumesMetadata):
    # N of label groups (Cell, Chromosomes)
    segmentation_lattice_ids: dict[list[int]]
    # N = lattice ids x downsamplings
    segmentation_downsamplings: dict[int, dict[int, list[int]]]
    # N = lattice ids
    category_ids: dict[list[int]]

class MeshesMetadata:
    mesh_component_numbers: dict
    detail_lvl_to_fraction: dict

class Metadata:
    entry_id: {
        source_db_name: str,
        source_db_id: str
    }
    volumes: VolumesMetadata
    segmentations: SegmentationsMetadata
    meshes: MeshesMetadata

class ExternalReference:
    id: int
    resource: str
    accession: str
    label: str
    description: str

class BiologicalAnnotation:
    name: str
    external_references: list[ExternalReference]

class Segment:
    # label-value in NGFF
    segment_id: int
    color: Optional[list[int, int, int]]
    biological_annotation: Optional[list[BiologicalAnnotation]]




class AnnotationsMetadata:
    entry_id: {
        source_db_name: str,
        source_db_id: str
    }
    segment_list: list[Segment]
    # Only in SFF
    details: Optional[str]

class SegmentationSliceData(TypedDict):
    # array with set ids
    category_set_ids: np.ndarray
    # dict mapping set ids to the actual segment ids (e.g. for set id=1, there may be several segment ids)
    category_set_dict: Dict

# NOTE: channel_id and time are added
class VolumeSliceData(TypedDict):
    # changed segm slice to another typeddict
    segmentation_slice: Optional[SegmentationSliceData]
    volume_slice: Optional[np.ndarray]
    channel_id: int
    time: int
