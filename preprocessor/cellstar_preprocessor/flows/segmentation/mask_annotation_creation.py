from uuid import uuid4
from cellstar_db.models import AnnotationsMetadata, DescriptionData, EntryId, SegmentAnnotationData, TargetId
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.model.segmentation import InternalSegmentation
import seaborn as sns

def mask_annotation_creation(internal_segmentation: InternalSegmentation):
    
    # segm_arr = root[SEGMENTATION_DATA_GROUPNAME][0][0][0][0]


    root = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )
    d: AnnotationsMetadata = root.attrs["annotations_dict"]

    d["entry_id"] = EntryId(
        source_db_id=internal_segmentation.entry_data.source_db_id,
        source_db_name=internal_segmentation.entry_data.source_db_name,
    )

    d["details"] = f"Segmentation of {internal_segmentation.entry_data.source_db_id} based on EMDB mask(s)"
    d["name"] = f"Segmentation of {internal_segmentation.entry_data.source_db_id} based on EMDB mask(s)"
    
    # create palette of length = lattices x segments
    # have count variable = 0
    # each time you take color palette you take 'count' and then increment count
    # by 1
    palette_length = 0
    for lattice_id in internal_segmentation.value_to_segment_id_dict:
        value_to_segment_id_dict_for_lat: dict = internal_segmentation.value_to_segment_id_dict[lattice_id]
        palette_length = palette_length + len(list(value_to_segment_id_dict_for_lat.keys()))
    
    print(f'Palette length is {palette_length}')


    palette = sns.color_palette(None, palette_length)

    count = 0
    for lattice_id, lattice_gr in root[LATTICE_SEGMENTATION_DATA_GROUPNAME].groups():
        # int to int dict
        value_to_segment_id_dict = internal_segmentation.value_to_segment_id_dict[lattice_id]
        # TODO: check if 0
        # number_of_keys = len(value_to_segment_id_dict.keys())

        

        for index, value in enumerate(value_to_segment_id_dict.keys()):
            segment_id = value_to_segment_id_dict[value]
            if segment_id > 0:
                # create description
                description_id = str(uuid4())
                target_id: TargetId = {
                    'segment_id': segment_id,
                    'segmentation_id': str(lattice_id)
                }
                description: DescriptionData = {
                    'id': description_id,
                    'target_kind': "lattice",
                    'description': None,
                    'is_hidden': None,
                    'metadata': None,
                    'time': 0,
                    'name': f"Segment {segment_id}",
                    'external_references': [],
                    'target_id': target_id
                }
                # create segment annotation
                color: list = [
                        palette[count][0],
                        palette[count][1],
                        palette[count][2],
                        1.0
                ]
                count = count + 1
                segment_annotation: SegmentAnnotationData = {
                    'id': str(uuid4()),
                    'color': color,
                    'segmentation_id': str(lattice_id),
                    'segment_id': segment_id,
                    'segment_kind': 'lattice',
                    'time': 0
                }
                d['descriptions'][description_id] = description
                d['annotations'].append(segment_annotation)

    root.attrs["annotations_dict"] = d
    print("Annotations extracted")
    return d