from typing import TypedDict

# NOTE: units - grid points?
# NOTE: sphere as ellipsoid?
# NOTE: in zarr it could be inside metadata.json or as attrs of _segmentation_data, which is better?

class ShapePrimitive(TypedDict):
    # XYZ
    center_coordinates: tuple[int, int, int]
    # NOTE: to be able to refer to it in annotations
    segment_id: int

# class Sphere(ShapePrimitive):
#     # in grid points
#     diameter: int

class Tube(ShapePrimitive):
    inner_diameter: int
    outer_diameter: int
    height: int

class Ellipsoid(ShapePrimitive):
    # XYZ
    extent: tuple[int, int, int]

class Cuboid(ShapePrimitive):
    # XYZ
    extent: tuple[int, int, int]

class ShapePrimitivesData(TypedDict):
    shape_primitive_list: list[ShapePrimitive]

