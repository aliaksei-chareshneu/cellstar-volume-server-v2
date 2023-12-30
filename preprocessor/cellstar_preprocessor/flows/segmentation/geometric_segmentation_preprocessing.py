import json
from pathlib import Path
from uuid import uuid4
from cellstar_db.models import Box, BoxInputParams, Cylinder, Ellipsoid, EllipsoidInputParams, GeometricSegmentationData, GeometricSegmentationInput, Pyramid, PyramidInputParams, ShapePrimitiveBase, ShapePrimitiveData, ShapePrimitiveKind, Sphere, SphereInputParams
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path, save_dict_to_json
from cellstar_preprocessor.flows.constants import GEOMETRIC_SEGMENTATION_FILENAME, GEOMETRIC_SEGMENTATIONS_ZATTRS, LATTICE_SEGMENTATION_DATA_GROUPNAME
import zarr
from cellstar_preprocessor.model.segmentation import InternalSegmentation

def _process_geometric_segmentation_data(data: GeometricSegmentationInput, zarr_structure_path: Path):
    shape_primitives_input = data.shape_primitives_input

    primitives: dict[int, ShapePrimitiveData] = {}

    for timeframe_index, timeframe_data in shape_primitives_input.items():
        shape_primitives_processed: list[ShapePrimitiveBase] = []
        
        for sp in timeframe_data:
            params = sp.parameters
            kind = sp.kind
            segment_id = params.id
            # color = params.color

            if kind == ShapePrimitiveKind.sphere:
                params: SphereInputParams
                shape_primitives_processed.append(
                    Sphere(
                        kind=kind,
                        center=params.center,
                        id=segment_id,
                        radius=params.radius
                    )
                )
            elif kind == ShapePrimitiveKind.cylinder:
                params: SphereInputParams
                shape_primitives_processed.append(
                    Cylinder(
                        kind=kind,
                        start=params.start,
                        end=params.end,
                        radius_bottom=params.radius_bottom,
                        radius_top=params.radius_top,
                        id=segment_id
                    )
                )
            elif kind == ShapePrimitiveKind.box:
                params: BoxInputParams
                shape_primitives_processed.append(
                    Box(
                        kind=kind,
                        translation=params.translation,
                        scaling=params.scaling,
                        rotation=params.rotation,
                        id=segment_id
                    )
                )
            elif kind == ShapePrimitiveKind.ellipsoid:
                params: EllipsoidInputParams
                shape_primitives_processed.append(
                    Ellipsoid(
                        kind=kind,
                        dir_major=params.dir_major,
                        dir_minor=params.dir_minor,
                        center=params.center,
                        radius_scale=params.radius_scale,
                        id=segment_id
                    )
                )
            elif kind == ShapePrimitiveKind.pyramid:
                params: PyramidInputParams
                shape_primitives_processed.append(
                    Pyramid(
                        kind=kind,
                        translation=params.translation,
                        scaling=params.scaling,
                        rotation=params.rotation,
                        id=segment_id
                    )
                )
            else:
                raise Exception(f'Shape primitive kind {kind} is not supported')

        


        # at the end
        d = ShapePrimitiveData(shape_primitive_list=shape_primitives_processed)
        primitives[timeframe_index] = d
    
    return primitives

    # return d
    # NOTE: from save annotations
    # segm_data_gr.attrs["geometric_segmentation"] = d
    # save_dict_to_json(d, GEOMETRIC_SEGMENTATION_FILENAME, zarr_structure_path)


def geometric_segmentation_preprocessing(internal_segmentation: InternalSegmentation):
    zarr_structure: zarr.Group = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )

    # # init GeometricSegmentationData in zattrs if not exist
    # if GEOMETRIC_SEGMENTATIONS_ZATTRS not in zarr_structure.attrs:
    #     zarr_structure.attrs[GEOMETRIC_SEGMENTATIONS_ZATTRS] = []

    # PLAN
    # parse input json to shape primitives data model
    input_path = internal_segmentation.segmentation_input_path

    if input_path.suffix == '.json':
        with open(str(input_path.resolve()), "r", encoding="utf-8") as f:
            data = json.load(f)
    elif input_path.suffix == '.star':
        # star to json not supported yet
        raise Exception('Geometric segmentation input is not supported')
    else:
        raise Exception('Geometric segmentation input is not supported')
    
    geometric_segmentation_input = GeometricSegmentationInput(**data)
    primitives = _process_geometric_segmentation_data(data=geometric_segmentation_input, zarr_structure_path=internal_segmentation.intermediate_zarr_structure_path)

    # create GeometricSegmentationData
    # with new set id
    geometric_segmentation_data: GeometricSegmentationData = {
        'geometric_segmentation_set_id': str(uuid4()),
        'primitives': primitives
    }
    # put to zattrs
    # instead of append, add to existing one
    existing_geometric_segmentations = zarr_structure.attrs[GEOMETRIC_SEGMENTATIONS_ZATTRS]
    existing_geometric_segmentations.append(geometric_segmentation_data)
    zarr_structure.attrs[GEOMETRIC_SEGMENTATIONS_ZATTRS] = existing_geometric_segmentations

    # TODO: finally store in json but only after all inputs are processed
    # for that create new task in preprocessor
    print('Shape primitives processed')


    

    