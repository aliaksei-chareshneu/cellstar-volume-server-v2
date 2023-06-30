from db.models import EntryId
from preprocessor_v2.preprocessor.flows.common import open_zarr_structure_from_path
from preprocessor_v2.preprocessor.flows.constants import SEGMENTATION_DATA_GROUPNAME
from preprocessor_v2.preprocessor.model.segmentation import InternalSegmentation


def extract_annotations_from_sff_segmentation(internal_segmentation: InternalSegmentation):
    root = open_zarr_structure_from_path(internal_segmentation.intermediate_zarr_structure_path)
    d = root.attrs['annotations_dict']

    d['entry_id'] = EntryId(
        source_db_id=internal_segmentation.entry_data.source_db_id,
        source_db_name=internal_segmentation.entry_data.source_db_name
    )
    d['details'] = internal_segmentation.raw_sff_annotations['details']
    d['name'] = internal_segmentation.raw_sff_annotations['name']

    # NOTE: no volume channel annotations (no color, no labels)
    root = open_zarr_structure_from_path(internal_segmentation.intermediate_zarr_structure_path)

    # NOTE: not all segments from segment list may be present in the given lattice
    # TODO: if number of lattices is > 1, print warning that segment list is global for all lattices
    # and not all segments from segment list may be present in the given lattice    
    for lattice_id, lattice_gr in root[SEGMENTATION_DATA_GROUPNAME].groups():
        segmentation_lattice_info = {
            "lattice_id": lattice_id,
            "segment_list": []
        }

        for segment in internal_segmentation.raw_sff_annotations['segment_list']:
            segmentation_lattice_info["segment_list"].append(
                {
                    "id": segment['id'],
                    "biological_annotation": {
                        "name": segment['biological_annotation']['name'],
                        "external_references": segment['biological_annotation']['external_references']
                    },
                    "color": segment['colour'],
                }
            )

        d['segmentation_lattices'].append(segmentation_lattice_info)

    root.attrs['annotations_dict'] = d
    print('Annotations extracted')
    return d