import json
from pathlib import Path
from cellstar_db.models import Box, Cylinder, Ellipsoid, Pyramid, ShapePrimitiveData, ShapePrimitiveKind, Sphere
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path, save_dict_to_json
from cellstar_preprocessor.flows.constants import GEOMETRIC_SEGMENTATION_FILENAME, LATTICE_SEGMENTATION_DATA_GROUPNAME
import zarr
from cellstar_preprocessor.model.segmentation import InternalSegmentation

# NOTE: for now saving at zattrs, alternatively can be zarr array of objects?
def _process_geometric_segmentation_data(data: dict, zarr_structure_path: Path):
    shape_primitives_input_list = data["shape_primitives_input_list"]

    shape_primitives_processed = []
    
    for sp in shape_primitives_input_list:
        params = sp['parameters']
        kind = sp['kind']
        segment_id = params['segment_id']
        color = params['color']
        if kind == ShapePrimitiveKind.sphere:
            shape_primitives_processed.append(
                Sphere(
                    kind=kind,
                    center=params['center'],
                    label=segment_id,
                    color=color,
                    radius=params['radius']
                )
            )
        elif kind == ShapePrimitiveKind.cylinder:
            shape_primitives_processed.append(
                Cylinder(
                    kind=kind,
                    color=params['color'],
                    start=params['start'],
                    end=params['end'],
                    radius=params['radius'],
                    label=segment_id
                )
            )
        elif kind == ShapePrimitiveKind.box:
            shape_primitives_processed.append(
                Box(
                    kind=kind,
                    color=params['color'],
                    translation=params['translation'],
                    scaling=params['scaling'],
                    label=segment_id
                )
            )
        elif kind == ShapePrimitiveKind.ellipsoid:
            shape_primitives_processed.append(
                Ellipsoid(
                    kind=kind,
                    color=params['color'],
                    dir_major=params['dir_major'],
                    dir_minor=params['dir_minor'],
                    center=params['center'],
                    radius_scale=params['radius_scale'],
                    label=segment_id
                )
            )
        elif kind == ShapePrimitiveKind.pyramid:
            shape_primitives_processed.append(
                Pyramid(
                    kind=kind,
                    color=params['color'],
                    translation=params['translation'],
                    scaling=params['scaling'],
                    label=segment_id
                )
            )
        elif kind == ShapePrimitiveKind.cone:
            shape_primitives_processed.append(
                Cone(
                    kind=kind,
                    color=params['color'],
                    translation=params['translation'],
                    scaling=params['scaling'],
                    label=segment_id
                )
            )
        # elif kind == ShapePrimitiveKind.tube:
        #     shape_primitives_processed.append(
        #         Tube(
        #             kind=kind,
        #             center=params['center'],
        #             inner_diameter=params['inner_diameter'],
        #             outer_diameter=params['outer_diameter'],
        #             height=params['height'],
        #             label=segment_id
        #         )
        #     )
        else:
            raise Exception(f'Shape primitive kind {kind} is not supported')



    # at the end
    d = ShapePrimitiveData(shape_primitive_list=shape_primitives_processed)
    # NOTE: from save annotations
    # segm_data_gr.attrs["geometric_segmentation"] = d
    save_dict_to_json(d, GEOMETRIC_SEGMENTATION_FILENAME, zarr_structure_path)


def geometric_segmentation_preprocessing(internal_segmentation: InternalSegmentation):
    zarr_structure: zarr.Group = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )
    # PLAN
    # parse input json to shape primitives data model
    input_path = internal_segmentation.segmentation_input_path

    if input_path.suffix == '.json':
        with open(str(input_path.resolve()), "r", encoding="utf-8") as f:
            data = json.load(f)
    elif input_path.suffix == '.star':
        # star to json
        pass
    else:
        raise Exception('Geometric segmentation input is not supported')
    
    _process_geometric_segmentation_data(data=data, zarr_structure_path=internal_segmentation.intermediate_zarr_structure_path)

    print('Shape primitives processed')


    

    