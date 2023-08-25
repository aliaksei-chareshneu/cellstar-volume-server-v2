import json
from cellstar_db.models import ShapePrimitiveData, ShapePrimitiveKind, Sphere, Tube
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import SEGMENTATION_DATA_GROUPNAME
import zarr
from cellstar_preprocessor.model.segmentation import InternalSegmentation

# NOTE: for now saving at zattrs, alternatively can be zarr array of objects?
def _process_geometric_segmentation_data(data: dict, segm_data_gr: zarr.hierarchy.group):
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
        elif kind == ShapePrimitiveKind.tube:
            shape_primitives_processed.append(
                Tube(
                    kind=kind,
                    center=params['center'],
                    inner_diameter=params['inner_diameter'],
                    outer_diameter=params['outer_diameter'],
                    height=params['height'],
                    label=segment_id
                )
            )
        else:
            raise Exception(f'Shape primitive kind {kind} is not supported')



    # at the end
    d = ShapePrimitiveData(shape_primitive_list=shape_primitives_processed)
    segm_data_gr.attrs["geometric_segmentation"] = d


def geometric_segmentation_preprocessing(internal_segmentation: InternalSegmentation):
    zarr_structure: zarr.hierarchy.group = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )
    segm_data_gr: zarr.hierarchy.group = zarr_structure.create_group(
        SEGMENTATION_DATA_GROUPNAME
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
    
    _process_geometric_segmentation_data(data=data, segm_data_gr=segm_data_gr)

    print('Shape primitives processed')


    

    