from decimal import Decimal
from cellstar_db.models import AnnotationsMetadata, EntryId, TimeInfo, VolumeSamplingInfo, VolumesMetadata
from cellstar_preprocessor.flows.common import get_downsamplings, open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import QUANTIZATION_DATA_DICT_ATTR_NAME, VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume.extract_omezarr_metadata import _convert_to_angstroms
from cellstar_preprocessor.model.volume import InternalVolume
from cellstar_preprocessor.tools.quantize_data.quantize_data import decode_quantized_data
import dask.array as da
import numpy as np
import zarr
import seaborn as sns

def _get_ome_tiff_channel_annotations(ome_tiff_metadata, volume_channel_annotations, zarr_structure):
    palette = sns.color_palette(None, len(ome_tiff_metadata['Channels'].keys()))
    channel_names_from_csv = []
    if 'extra_data' in zarr_structure.attrs:
        channel_names_from_csv = zarr_structure.attrs['extra_data']['name_dict']['crop_raw']
    
    for channel_id_in_ometiff_metadata, channel_key in enumerate(ome_tiff_metadata['Channels']):
        channel = ome_tiff_metadata['Channels'][channel_key]
        # for now FFFFFFF
        # color = 'FFFFFF'
        color = [
            palette[channel_id_in_ometiff_metadata][0],
            palette[channel_id_in_ometiff_metadata][1],
            palette[channel_id_in_ometiff_metadata][2],
            1.0
        ]
        print(f'Color: {color} for channel {channel_key}')
        # TODO: check how it is encoded in some sample
        # if channel['Color']:
        #     color = _convert_hex_to_rgba_fractional(channel['Color'])
        label = channel['ID']
        if 'Name' in channel:
            label = channel['Name']

        if channel_names_from_csv:
            volume_channel_annotations.append(
                {
                    'channel_id': channel_names_from_csv[channel_id_in_ometiff_metadata],
                    'color': color,
                    'label': channel_names_from_csv[channel_id_in_ometiff_metadata]
                }
            )
        else:
            volume_channel_annotations.append(
                {
                    'channel_id': str(channel_id_in_ometiff_metadata),
                    'color': color,
                    'label': label
                }
            )

def extract_ome_tiff_image_annotations(internal_volume: InternalVolume):
    # d = {
    #     'entry_id': {
    #         'source_db_name': source_db_name,
    #         'source_db_id': source_db_id
    #     },
    #     # 'segment_list': [],
    #     'segmentation_lattices': [],
    #     'details': None,
    #     'volume_channels_annotations': []
    # }
    root = open_zarr_structure_from_path(
        internal_volume.intermediate_zarr_structure_path
    )
    
    ometiff_metadata = internal_volume.custom_data['ometiff_metadata']
    d: AnnotationsMetadata = root.attrs["annotations_dict"]
    _get_ome_tiff_channel_annotations(ome_tiff_metadata=ometiff_metadata,
        volume_channel_annotations=d['volume_channels_annotations'],
        zarr_structure=root
        )
    
    d["entry_id"] = EntryId(
        source_db_id=internal_volume.entry_data.source_db_id,
        source_db_name=internal_volume.entry_data.source_db_name,
    )

    root.attrs["annotations_dict"] = d
    return d