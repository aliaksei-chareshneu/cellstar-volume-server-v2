from cellstar_db.models import EntryId
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.model.segmentation import InternalSegmentation


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

    
    for lattice_id, lattice_gr in root[SEGMENTATION_DATA_GROUPNAME].groups():
        segmentation_lattice_info = {"lattice_id": lattice_id, "segment_list": []}

        # int to int dict
        value_to_segment_id_dict = internal_segmentation.value_to_segment_id_dict[int(lattice_id)]
        # TODO: check if 0
        number_of_keys = len(value_to_segment_id_dict.keys())
        for k, v in value_to_segment_id_dict.items():
            if k > 0:
                segmentation_lattice_info["segment_list"].append(
                        {
                            "id": k,
                            "biological_annotation": {
                                "name": f"Segment {k}",
                                "external_references": [
                                ],
                            },
                            # TODO: find way to map integers to unique colors
                            "color": [
                                        1/number_of_keys * k,
                                        1/number_of_keys * k,
                                        1/number_of_keys * k,
                                        1.0
                                        ],
                        }
                    )

        d["segmentation_lattices"].append(segmentation_lattice_info)
    
    root.attrs["annotations_dict"] = d
    print("Annotations extracted")
    return d