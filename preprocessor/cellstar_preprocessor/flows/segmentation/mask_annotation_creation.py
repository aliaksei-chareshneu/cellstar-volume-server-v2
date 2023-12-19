from cellstar_db.models import EntryId
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.model.segmentation import InternalSegmentation
import seaborn as sns

def mask_annotation_creation(internal_segmentation: InternalSegmentation):
    
    # segm_arr = root[SEGMENTATION_DATA_GROUPNAME][0][0][0][0]


    root = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )
    d = root.attrs["annotations_dict"]

    d["entry_id"] = EntryId(
        source_db_id=internal_segmentation.entry_data.source_db_id,
        source_db_name=internal_segmentation.entry_data.source_db_name,
    )

    d["details"] = f"Segmentation of {internal_segmentation.entry_data.source_db_id} based on EMDB mask(s)"
    d["name"] = f"Segmentation of {internal_segmentation.entry_data.source_db_id} based on EMDB mask(s)"

    
    for lattice_id, lattice_gr in root[LATTICE_SEGMENTATION_DATA_GROUPNAME].groups():
        segmentation_lattice_info = {"lattice_id": lattice_id, "segment_list": []}

        # int to int dict
        value_to_segment_id_dict = internal_segmentation.value_to_segment_id_dict[int(lattice_id)]
        # TODO: check if 0
        number_of_keys = len(value_to_segment_id_dict.keys())

        palette = sns.color_palette(None, number_of_keys)

        for index, value in enumerate(value_to_segment_id_dict.keys()):
            segment_id = value_to_segment_id_dict[value]
            if segment_id > 0:
                segmentation_lattice_info["segment_list"].append(
                        {
                            "id": segment_id,
                            "biological_annotation": {
                                "name": f"Segment {segment_id}",
                                "external_references": [
                                ],
                            },
                            # TODO: find way to map integers to unique colors
                            "color": [
                                        palette[index][0],
                                        palette[index][1],
                                        palette[index][2],
                                        1.0
                                        ],
                        }
                    )

        d["segmentation_lattices"].append(segmentation_lattice_info)
    
    root.attrs["annotations_dict"] = d
    print("Annotations extracted")
    return d