from typing import Dict, Optional, TypedDict, Union
import numpy as np

# class VolumeDescriptiveStatistics(TypedDict):
#     mean: float
#     min: float
#     max: float
#     std: float

# scale transformation only
# translate transformation from NGFF can be represented in origin (computed upfront)
# class BoxScaleTransformation(TypedDict):
#     # to which downsampling level it is applied: can be to specific level, can be to all lvls
#     downsampling_level: Union[int, str]
#     vector: list[float, float, float]


# class TimeTransformation(TypedDict):
#     # to which downsampling level it is applied: can be to specific level, can be to all lvls
#     downsampling_level: Union[int, str] 
#     factor: float

# class ChannelsAnnotations(TypedDict):
#     # channel_id -> channel color
#     colors: dict[int, list[int, int, int]]
#     # channel_id -> channel label; from omero - channels (e.g. "DAPI")
#     labels: Optional[dict[int, str]]

# class TimeInfo(TypedDict):
#     kind: str
#     start: int
#     end: int
#     units: str

# class SamplingBox(TypedDict):
#     origin: list[int, int, int]
#     voxel_size: list[float, float, float]
#     grid_dimensions: list[int, int, int]
#     volume_force_dtype: str

# class VolumeSamplingInfo(TypedDict):
#     # Info about "downsampling dimension"
#     spatial_downsampling_levels: list[int]
#     # the only thing with changes with SPATIAL downsampling is box!
#     sampling_boxes: dict[int, SamplingBox]
#     # time -> channel_id
#     descriptive_statistics: dict[int, dict[int, VolumeDescriptiveStatistics]]
#     box_transformations: list[BoxScaleTransformation]
#     time_transformations: list[TimeTransformation]

# class VolumesMetadata(TypedDict):
#     channel_ids: list[int]
#     # Values of time dimension
#     time_info: TimeInfo
#     volume_sampling_info: VolumeSamplingInfo
    
    




# class SegmentationLatticesMetadata(VolumesMetadata):
#     # N of label groups (Cell, Chromosomes)
#     segmentation_lattice_ids: list[str]
#     # N = lattice ids x downsamplings
#     segmentation_downsamplings: dict[str, dict[int, list[int]]]
#     # N = lattice ids
#     category_ids: dict[str, list[int]]

# class MeshesMetadata(TypedDict):
#     mesh_component_numbers: dict
#     detail_lvl_to_fraction: dict

# class EntryId(TypedDict):
#     source_db_name: str
#     source_db_id: str


# class Metadata(TypedDict):
#     entry_id: EntryId
#     volumes: VolumesMetadata
#     segmentation_lattices: SegmentationLatticesMetadata
#     segmentation_meshes: MeshesMetadata

# class ExternalReference(TypedDict):
#     id: int
#     resource: str
#     accession: str
#     label: str
#     description: str

# class BiologicalAnnotation(TypedDict):
#     name: str
#     external_references: list[ExternalReference]

# class Segment(TypedDict):
#     # label-value in NGFF
#     segment_id: int
#     color: Optional[list[int, int, int]]
#     biological_annotation: Optional[list[BiologicalAnnotation]]




# class AnnotationsMetadata(TypedDict):
#     entry_id: EntryId
#     segment_list: list[Segment]
#     # Only in SFF
#     details: Optional[str]
#     volume_channels_annotations: ChannelsAnnotations
    

# class SegmentationSliceData(TypedDict):
#     # array with set ids
#     category_set_ids: np.ndarray
#     # dict mapping set ids to the actual segment ids (e.g. for set id=1, there may be several segment ids)
#     category_set_dict: Dict

# # NOTE: channel_id and time are added
# class VolumeSliceData(TypedDict):
#     # changed segm slice to another typeddict
#     segmentation_slice: Optional[SegmentationSliceData]
#     volume_slice: Optional[np.ndarray]
#     channel_id: int
#     time: int
