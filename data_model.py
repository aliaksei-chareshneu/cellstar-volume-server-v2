from typing import Dict, Optional, TypedDict, Union
import numpy as np

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
    vector: list[float, float, float]


class TimeTransformation:
    # to which downsampling level it is applied: can be to specific level, can be to all lvls
    downsampling_level: Union[int, str] 
    factor: float

class ChannelsAnnotations:
    # channel_id -> channel color
    colors: dict[int, list[int, int, int]]
    # channel_id -> channel label; from omero - channels (e.g. "DAPI")
    labels: Optional[dict[int, str]]

class TimeInfo(TypedDict):
    kind: range
    start: int
    end: int
    units: str

class SamplingBox:
    origin: list[int, int, int],
    voxel_size: list[float, float, float]
    grid_dimensions: list[int, int, int]
    volume_force_dtype: str

class VolumeSamplingInfo:
    # Info about "downsampling dimension"
    spatial_downsampling_levels: list[int]
    # the only thing with changes with SPATIAL downsampling is box!
    sampling_boxes: dict[int, SamplingBox]
    # time -> channel_id
    descriptive_statistics: dict[int, dict[int, VolumeDescriptiveStatistics]]
    box_transformations: list[BoxScaleTransformation]
    time_transformations: list[TimeTransformation]

class VolumesMetadata:
    channel_ids: list[int]
    # Values of time dimension
    time_info: TimeInfo
    volume_sampling_info: VolumeSamplingInfo
    
    




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
    volume_channels_annotations: ChannelsAnnotations
    

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
