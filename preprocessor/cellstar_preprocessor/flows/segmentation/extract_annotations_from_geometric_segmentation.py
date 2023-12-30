from uuid import uuid4
from cellstar_db.models import AnnotationsMetadata, DescriptionData, EntryId, GeometricSegmentationData, GeometricSegmentationInputData, SegmentAnnotationData, ShapePrimitiveInputData

from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import GEOMETRIC_SEGMENTATIONS_ZATTRS, LATTICE_SEGMENTATION_DATA_GROUPNAME, MESH_SEGMENTATION_DATA_GROUPNAME, RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS
from cellstar_preprocessor.model.input import SegmentationPrimaryDescriptor
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def extract_annotations_from_geometric_segmentation(
    internal_segmentation: InternalSegmentation,
):
    root = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )
    d: AnnotationsMetadata = root.attrs["annotations_dict"]

    d["entry_id"] = EntryId(
        source_db_id=internal_segmentation.entry_data.source_db_id,
        source_db_name=internal_segmentation.entry_data.source_db_name,
    )
    
    # NOTE: no volume channel annotations (no color, no labels)
    root = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )

    
    # segmentation is in zattrs
    geometric_segmentation_data: list[GeometricSegmentationData] = root.attrs[GEOMETRIC_SEGMENTATIONS_ZATTRS]
    # it is a list of objects each of which has timeframes as keys
    for gs_set in geometric_segmentation_data:
        set_id = gs_set['geometric_segmentation_set_id']
        
        # collect color from input data as well
        raw_input_data = root.attrs[RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS][set_id]
        input_data = GeometricSegmentationInputData(**raw_input_data)

        d['segment_annotations']['primitive'][set_id] = {}
        primitives = gs_set['primitives']
        # iterate over timeframe index and ShapePrimitiveData
        for timeframe_index, shape_primitive_data in primitives.items():
            # iterate over individual primitives
            time = int(timeframe_index)
            for sp in shape_primitive_data['shape_primitive_list']:
                # create description
                description_id = str(uuid4())
                description: DescriptionData = {
                    'id': description_id,
                    'target_kind': "primitive",
                    'description': None,
                    'description_format': None,
                    'is_hidden': None,
                    'metadata': None,
                    'time': time,
                    'name': None,
                    'external_references': None,
                    'target_set_id': set_id,
                    'target_segment_id': sp['id'],
                }
                # get segment annotations

                # how to get color from raw_input_data
                # need to get raw input data for that shape primitive input
                # raw input data should be dict
                # with keys as set ids
                sp_input_list = input_data.shape_primitives_input[time]
                filter_results: list[ShapePrimitiveInputData] = list(filter(lambda s: s.parameters.id == sp['id'], sp_input_list))
                assert len(filter_results) == 1
                item: ShapePrimitiveInputData = filter_results[0]
                color = item.parameters.color

                segment_annotation: SegmentAnnotationData = {
                    # TODO: find color in shape primitive input data
                    'color': color,
                    'set_id': set_id,
                    'segment_id': sp['id'],
                    'segment_kind': 'primitive',
                    'time': time
                }

                d['descriptions'][description_id] = description
                d['segment_annotations']['primitive'][set_id][sp["id"]] = segment_annotation

    
    
    
    # if internal_segmentation.primary_descriptor == SegmentationPrimaryDescriptor.three_d_volume:
    #     for lattice_id, lattice_gr in root[LATTICE_SEGMENTATION_DATA_GROUPNAME].groups():
    #         d['segment_annotations']['lattice'][lattice_id] = {}
    #         for segment in internal_segmentation.raw_sff_annotations["segment_list"]:
    #             if str(segment["three_d_volume"]["lattice_id"]) == str(lattice_id):
    #                 # create description
    #                 description_id = str(uuid4())
    #                 description: DescriptionData = {
    #                     'id': description_id,
    #                     'target_kind': "lattice",
    #                     'description': None,
    #                     'description_format': None,
    #                     'is_hidden': None,
    #                     'metadata': None,
    #                     'time': time,
    #                     'name': segment["biological_annotation"]["name"],
    #                     'external_references': segment["biological_annotation"]["external_references"],
    #                     'target_lattice_id': str(lattice_id),
    #                     'target_segment_id': segment["id"],
    #                 }
    #                 # create segment annotation
    #                 segment_annotation: SegmentAnnotationData = {
    #                     'color': segment["colour"],
    #                     'lattice_id': str(lattice_id),
    #                     'segment_id': segment["id"],
    #                     'segment_kind': 'lattice',
    #                     'time': time
    #                 }
    #                 d['descriptions'][description_id] = description
    #                 d['segment_annotations']['lattice'][lattice_id][segment["id"]] = segment_annotation

    # elif internal_segmentation.primary_descriptor == SegmentationPrimaryDescriptor.mesh_list:
    #     for set_id, set_gr in root[MESH_SEGMENTATION_DATA_GROUPNAME].groups():
    #         d['segment_annotations']['mesh'][set_id] = {}
    #         for segment in internal_segmentation.raw_sff_annotations["segment_list"]:
    #             description_id = str(uuid4())
    #             description: DescriptionData = {
    #                 'id': description_id,
    #                 'target_kind': "mesh",
    #                 'description': None,
    #                 'description_format': None,
    #                 'is_hidden': None,
    #                 'metadata': None,
    #                 'time': time,
    #                 'name': segment["biological_annotation"]["name"],
    #                 'external_references': segment["biological_annotation"]["external_references"],
    #                 'target_set_id': str(set_id),
    #                 'target_segment_id': segment["id"],
    #             }
    #             segment_annotation: SegmentAnnotationData = {
    #                 'color': segment["colour"],
    #                 'set_id': str(set_id),
    #                 'segment_id': segment["id"],
    #                 'segment_kind': 'mesh',
    #                 'time': time
    #             }
    #             d['descriptions'][description_id] = description
    #             d['segment_annotations']['mesh'][set_id][segment["id"]] = segment_annotation









    root.attrs["annotations_dict"] = d
    print("Annotations extracted")
    return d
