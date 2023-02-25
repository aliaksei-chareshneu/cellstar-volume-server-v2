from typing import Dict, List, Optional, Protocol, TypedDict, Union

import numpy as np

class EntryId(TypedDict):
    source_db_name: str
    source_db_id: str

class ExternalReference(TypedDict):
    id: int
    resource: str
    accession: str
    label: str
    description: str

class BiologicalAnnotation(TypedDict):
    name: str
    external_references: list[ExternalReference]

class Segment(TypedDict):
    # label-value in NGFF
    id: int
    color: Optional[list[int, int, int]]
    biological_annotation: Optional[list[BiologicalAnnotation]]


class ChannelsAnnotations(TypedDict):
    # channel_id -> channel color
    colors: dict[str, list[int, int, int]]
    # channel_id -> channel label; from omero - channels (e.g. "DAPI")
    labels: Optional[dict[str, str]]

class AnnotationsMetadata(TypedDict):
    entry_id: EntryId
    segment_list: list[Segment]
    # Only in SFF
    details: Optional[str]
    volume_channels_annotations: ChannelsAnnotations

class MeshesMetadata(TypedDict):
    mesh_component_numbers: dict
    detail_lvl_to_fraction: dict

class TimeTransformation(TypedDict):
    # to which downsampling level it is applied: can be to specific level, can be to all lvls
    downsampling_level: Union[int, str] 
    factor: float

class VolumeDescriptiveStatistics(TypedDict):
    mean: float
    min: float
    max: float
    std: float

class TimeInfo(TypedDict):
    kind: str
    start: int
    end: int
    units: str

class SamplingBox(TypedDict):
    origin: tuple[int, int, int]
    voxel_size: tuple[float, float, float]
    grid_dimensions: list[int, int, int]

class SamplingInfo(TypedDict):
    # Info about "downsampling dimension"
    spatial_downsampling_levels: list[int]
    # the only thing with changes with SPATIAL downsampling is box!
    boxes: dict[int, SamplingBox]
    time_transformations: list[TimeTransformation]

class VolumeSamplingInfo(SamplingInfo):
    # resolution -> time -> channel_id
    descriptive_statistics: dict[int, dict[int, dict[int, VolumeDescriptiveStatistics]]]

class VolumesMetadata(TypedDict):
    channel_ids: list[int]
    # Values of time dimension
    time_info: TimeInfo
    volume_sampling_info: VolumeSamplingInfo
    # NOTE: what if units are not known for some axes?
    source_axes_units: dict[str, str]


class SegmentationLatticesMetadata(TypedDict):
    # N of label groups (Cell, Chromosomes)
    segmentation_lattice_ids: list[str]
    
    segmentation_sampling_info: dict[str, SamplingInfo]
    channel_ids: dict[str, list[int]]
    time_info: dict[str, TimeInfo]


class Metadata(TypedDict):
    entry_id: EntryId
    volumes: VolumesMetadata
    segmentation_lattices: SegmentationLatticesMetadata
    segmentation_meshes: MeshesMetadata

class MeshMetadata(TypedDict):
    num_vertices: int
    num_triangles: int
    num_normals: int


class MeshListMetadata(TypedDict):
    mesh_ids: dict[int, MeshMetadata]


class DetailLvlsMetadata(TypedDict):
    detail_lvls: dict[int, MeshListMetadata]


class MeshComponentNumbers(TypedDict):
    segment_ids: dict[int, DetailLvlsMetadata]


class MeshData(TypedDict):
    mesh_id: int
    vertices: np.ndarray  # shape = (n_vertices, 3)
    triangles: np.ndarray  # shape = (n_triangles, 3)

MeshesData = list[MeshData]


class SegmentationSliceData(TypedDict):
    # array with set ids
    category_set_ids: np.ndarray
    # dict mapping set ids to the actual segment ids (e.g. for set id=1, there may be several segment ids)
    category_set_dict: Dict
    lattice_id: int

# NOTE: channel_id and time are added
class VolumeSliceData(TypedDict):
    # changed segm slice to another typeddict
    segmentation_slice: Optional[SegmentationSliceData]
    volume_slice: Optional[np.ndarray]
    channel_id: int
    time: int

class VolumeMetadata(Protocol):
    def json_metadata(self) -> str:
        ...

    def db_name(self) -> str:
        ...

    def entry_id(sefl) -> str:
        ...

    def segmentation_lattice_ids(self) -> List[int]:
        ...

    def segmentation_downsamplings(self, lattice_id: int) -> List[int]:
        ...

    def volume_downsamplings(self) -> List[int]:
        ...

    def origin(self, downsampling_rate: int) -> List[float]:
        """
        Returns the coordinates of the initial point in Angstroms
        """
        ...

    def voxel_size(self, downsampling_rate: int) -> List[float]:
        """
        Returns the step size in Angstroms for each axis (X, Y, Z) for a given downsampling rate
        """
        ...

    def grid_dimensions(self, downsampling_rate: int) -> List[int]:
        """
        Returns the number of points along each axis (X, Y, Z)
        """
        ...

    def sampled_grid_dimensions(self, level: int) -> List[int]:
        """
        Returns the number of points along each axis (X, Y, Z) for specific downsampling level
        """
        ...

    def mean(self, level: int, time: int, channel_id: int) -> np.float32:
        """
        Return mean for data at given downsampling level
        """
        ...

    def std(self, level: int, time: int, channel_id: int) -> np.float32:
        """
        Return standard deviation for data at given downsampling level
        """
        ...

    def max(self, level: int, time: int, channel_id: int) -> np.float32:
        """
        Return max for data at given downsampling level
        """
        ...

    def min(self, level: int, time: int, channel_id: int) -> np.float32:
        """
        Return min for data at given downsampling level
        """
        ...

    def mesh_component_numbers(self) -> MeshComponentNumbers:
        """
        Return typed dict with numbers of mesh components (triangles, vertices etc.) for
        each segment, detail level and mesh id
        """
        ...

    def detail_lvl_to_fraction(self) -> dict:
        """
        Returns dict with detail lvls (1,2,3 ...) as keys and corresponding
        mesh simplification ratios (fractions, e.g. 0.8) as values
        """
        ...
