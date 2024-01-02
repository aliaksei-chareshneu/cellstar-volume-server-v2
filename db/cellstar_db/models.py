from enum import Enum
from typing import Any, List, Literal, Optional, Protocol, TypedDict, Union

import numpy as np
from pydantic import BaseModel, validator
import zarr

# METADATA DATA MODEL

class SamplingBox(TypedDict):
    origin: tuple[int, int, int]
    voxel_size: tuple[float, float, float]
    grid_dimensions: list[int, int, int]

class TimeTransformation(TypedDict):
    # to which downsampling level it is applied: can be to specific level, can be to all lvls
    downsampling_level: Union[int, Literal['all']]
    factor: float

class SamplingInfo(TypedDict):
    # Info about "downsampling dimension"
    spatial_downsampling_levels: list[int]
    # the only thing which changes with SPATIAL downsampling is box!
    boxes: dict[int, SamplingBox]
    time_transformations: list[TimeTransformation]
    source_axes_units: dict[str, str]
    # e.g. (0, 1, 2) as standard
    original_axis_order: list[int, int, int]

class TimeInfo(TypedDict):
    kind: str
    start: int
    end: int
    units: str

class SegmentationLatticesMetadata(TypedDict):
    # e.g. label groups (Cell, Chromosomes)
    segmentation_lattice_ids: list[str]
    segmentation_sampling_info: dict[str, SamplingInfo]
    time_info: dict[str, TimeInfo]

class GeometricSegmentationSetsMetadata(TypedDict):
    sets_ids: list[str]
    # maps set ids to time info
    time_info: dict[str, TimeInfo]

class MeshMetadata(TypedDict):
    num_vertices: int
    num_triangles: int
    num_normals: Optional[int]

class MeshListMetadata(TypedDict):
    mesh_ids: dict[int, MeshMetadata]

class DetailLvlsMetadata(TypedDict):
    detail_lvls: dict[int, MeshListMetadata]

class MeshComponentNumbers(TypedDict):
    segment_ids: dict[int, DetailLvlsMetadata]

class MeshesMetadata(TypedDict):
    segmentation_mesh_set_id: str
    # maps timeframe index to MeshComponentNumbers
    mesh_timeframes: dict[int, MeshComponentNumbers]
    detail_lvl_to_fraction: dict

class MeshSegmentationSetsMetadata(TypedDict):
    sets_ids: list[str]
    sets: list[MeshesMetadata]
    # maps set ids to time info
    time_info: dict[str, TimeInfo]

class VolumeDescriptiveStatistics(TypedDict):
    mean: float
    min: float
    max: float
    std: float

class VolumeSamplingInfo(SamplingInfo):
    # resolution -> time -> channel_id
    descriptive_statistics: dict[int, dict[int, dict[str, VolumeDescriptiveStatistics]]]

class VolumesMetadata(TypedDict):
    channel_ids: list[str]
    # Values of time dimension
    time_info: TimeInfo
    volume_sampling_info: VolumeSamplingInfo

class EntryId(TypedDict):
    source_db_name: str
    source_db_id: str

class Metadata(TypedDict):
    entry_id: EntryId
    volumes: VolumesMetadata
    segmentation_lattices: Optional[SegmentationLatticesMetadata]
    segmentation_meshes: Optional[MeshSegmentationSetsMetadata]
    geometric_segmentation: Optional[GeometricSegmentationSetsMetadata]

# END METADATA DATA MODEL

# ANNOTATIONS DATA MODEL

class ChannelAnnotation(TypedDict):
    # uuid
    channel_id: str
    # with transparency
    color: tuple[float, float, float, float]
    label: Optional[str]

class SegmentAnnotationData(TypedDict):
    # label-value in NGFF
    # uuid
    segment_kind: Literal["lattice", "mesh", "primitive"]
    segment_id: int
    lattice_id: Optional[str]
    set_id: Optional[str]
    color: Optional[tuple[float, float, float, float]]
    time: Optional[int]
    # other props added later if needed

class ExternalReference(TypedDict):
    # uuid
    id: Optional[str]
    resource: Optional[str]
    accession: Optional[str]
    label: Optional[str]
    description: Optional[str]

class DescriptionData(TypedDict):
    # uuid
    id: Optional[str]
    target_kind: Optional[Literal["lattice", "mesh", "primitive", "entry"]]
    target_segment_id: Optional[Union[int, None]]
    target_lattice_id: Optional[str]
    target_set_id: Optional[str]
    name: Optional[str]
    external_references: Optional[list[ExternalReference]]
    is_hidden: Optional[bool]
    time: Optional[int]
    description_format: Optional[Literal["text", "markdown"]]
    description: Optional[str]

    metadata: Union[dict[str, Any], None]


class AnnotationsMetadata(TypedDict):
    name: Optional[str]
    entry_id: EntryId
    # id => DescriptionData
    descriptions: dict[str, DescriptionData]
    # kind => lattice_id => segment_id
    segment_annotations: dict[Literal["lattice", "mesh", "primitive"], dict[str, dict[int, SegmentAnnotationData]]]
    # Only in SFF
    details: Optional[str]
    volume_channels_annotations: Optional[list[ChannelAnnotation]]

# END ANNOTATIONS DATA MODEL


# "DATA" DATA MODEL

class LatticeSegmentationData(TypedDict):
    grid: zarr.core.Array
    # NOTE: single item in the array which is a Dict
    set_table: zarr.core.Array

class SingleMeshZattrs(TypedDict):
    num_vertices: int
    area: float
    # TODO: add these two
    num_triangles: int
    num_normals: int

class SingleMeshSegmentationData(TypedDict):
    mesh_id: str
    vertices: zarr.core.Array
    triangles: zarr.core.Array
    normals: zarr.core.Array
    attrs: SingleMeshZattrs

class ShapePrimitiveKind(str, Enum):
    sphere = "sphere"
    tube = "tube"
    cylinder = "cylinder"
    box = "box"
    ellipsoid = "ellipsoid"
    pyramid = "pyramid"

class ShapePrimitiveBase(TypedDict):
    # NOTE: to be able to refer to it in annotations
    id: int
    kind: ShapePrimitiveKind
    # NOTE: color in annotations

class Sphere(ShapePrimitiveBase):
    # in angstroms
    center: tuple[float, float, float]
    radius: float

class Box(ShapePrimitiveBase):
    # with respect to origin 0, 0, 0
    translation: tuple[float, float, float]
    # default size 2, 2, 2 in angstroms for pdbe-1.rec
    scaling: tuple[float, float, float]
    rotation: tuple[float, float, float, float] # quaternion

class Cylinder(ShapePrimitiveBase):
    start: tuple[float, float, float]
    end: tuple[float, float, float]
    radius_bottom: float
    radius_top: float  # =0 <=> cone

class Ellipsoid(ShapePrimitiveBase):
    dir_major: tuple[float, float, float]
    dir_minor: tuple[float, float, float]
    center: tuple[float, float, float]
    radius_scale: tuple[float, float, float]

class Pyramid(ShapePrimitiveBase):
    # with respect to origin 0, 0, 0
    translation: tuple[float, float, float]
    # default size 2, 2, 2 in angstroms for pdbe-1.rec
    scaling: tuple[float, float, float]
    rotation: tuple[float, float, float, float]

class ShapePrimitiveData(TypedDict):
    shape_primitive_list: list[ShapePrimitiveBase]

class GeometricSegmentationData(TypedDict):
    geometric_segmentation_set_id: str
    # maps timeframe index to ShapePrimitivesData
    primitives: dict[int, ShapePrimitiveData]

class ZarrRoot(TypedDict):
    volume_data: list[dict[int, list[dict[int, list[dict[int, zarr.core.Array]]]]]]
    lattice_segmentation_data: list[dict[str, list[dict[int, list[dict[int, LatticeSegmentationData]]]]]]
    # mesh set_id => timeframe => segment_id => detail_lvl => mesh_id in meshlist
    mesh_segmentation_data: list[str, dict[int, list[dict[str, list[dict[int, list[dict[str, SingleMeshSegmentationData]]]]]]]]

# Files:
# NOTE: saved as JSON/Msgpack directly, without temporary storing in .zattrs
GeometricSegmentationJson = list[GeometricSegmentationData]

# END "DATA" DATA MODEL


# SERVER OUTPUT DATA MODEL (MESHES, SEGMENTATION LATTICES, VOLUMES)

class MeshData(TypedDict):
    mesh_id: int
    vertices: np.ndarray  # shape = (n_vertices, 3)
    triangles: np.ndarray  # shape = (n_triangles, 3)

MeshesData = list[MeshData]

class LatticeSegmentationSliceData(TypedDict):
    # array with set ids
    category_set_ids: np.ndarray
    # dict mapping set ids to the actual segment ids (e.g. for set id=1, there may be several segment ids)
    category_set_dict: dict
    lattice_id: int

class VolumeSliceData(TypedDict):
    # changed segm slice to another typeddict
    segmentation_slice: Optional[LatticeSegmentationSliceData]
    volume_slice: Optional[np.ndarray]
    channel_id: int
    time: int

# END SERVER OUTPUT DATA MODEL

# INPUT DATA MODEL
    
class ShapePrimitiveInputParams(BaseModel):
    id: int
    color: list[float, float, float, float]

class SphereInputParams(ShapePrimitiveInputParams):
    center: tuple[float, float, float]
    radius: float
    
class BoxInputParams(ShapePrimitiveInputParams):
    # with respect to origin 0, 0, 0
    translation: tuple[float, float, float]
    # default size 2, 2, 2 in angstroms for pdbe-1.rec
    scaling: tuple[float, float, float]
    rotation: tuple[float, float, float, float] # quaternion
    
class CylinderInputParams(ShapePrimitiveInputParams):
    start: tuple[float, float, float]
    end: tuple[float, float, float]
    radius_bottom: float
    radius_top: float  # =0 <=> cone

class EllipsoidInputParams(ShapePrimitiveInputParams):
    dir_major: tuple[float, float, float]
    dir_minor: tuple[float, float, float]
    center: tuple[float, float, float]
    radius_scale: tuple[float, float, float]
    
class PyramidInputParams(ShapePrimitiveInputParams):
    # with respect to origin 0, 0, 0
    translation: tuple[float, float, float]
    # default size 2, 2, 2 in angstroms for pdbe-1.rec
    scaling: tuple[float, float, float]
    rotation: tuple[float, float, float, float]


class ShapePrimitiveInputData(BaseModel):
    kind: ShapePrimitiveKind
    parameters: Union[
        SphereInputParams,
        PyramidInputParams,
        EllipsoidInputParams,
        CylinderInputParams,
        BoxInputParams,
        SphereInputParams,
        ShapePrimitiveInputParams
    ]

class GeometricSegmentationInputData(BaseModel):
    # maps timeframe index to list of ShapePrimitiveInputData
    shape_primitives_input: dict[int, list[ShapePrimitiveInputData]]
    time_units: Optional[str]
    
# END INPUT DATA MODEL


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
