import asyncio
from pathlib import Path
from typing import Optional
from cellstar_preprocessor.model.input import PreprocessorInput
from fastapi import Query, Response
from cellstar_db.file_system.db import FileSystemVolumeServerDB
import numpy as np
from new_server_for_tomoprocessor.app.api.requests import GeometricSegmentationRequest, MetadataRequest, VolumeRequestDataKind, VolumeRequestInfo
from new_server_for_tomoprocessor.app.core.service import VolumeServerService
from new_server_for_tomoprocessor.app.serialization.cif import serialize_tomogram_and_spheres
# from serialization.cif import serialize_tomogram_and_spheres
# from new_server_for_tomoprocessor.app.api.requests import VolumeRequestBox, VolumeRequestDataKind, VolumeRequestInfo
# from new_server_for_tomoprocessor.app.core.service import VolumeServerService


async def generate_bcif(preprocessor_input: PreprocessorInput, entry_folder: Path):
    db_path = preprocessor_input.db_path
    # out: Path = preprocessor_input.custom_data['out']
    db = FileSystemVolumeServerDB(folder=db_path)
    volume_server = VolumeServerService(db)

    response = await volume_server.get_nonserialized_volume_data(
        req=VolumeRequestInfo(
            source=preprocessor_input.entry_data.source_db,
            structure_id=preprocessor_input.entry_data.entry_id,
            segmentation_id=0,
            channel_id=0,
            time=0,
            max_points=10000000,
            data_kind=VolumeRequestDataKind.volume,
        ),
    )
    metadata = response["metadata"]
    slice_box = response["slice_box"]
    volume_data: np.ndarray = response["volume_slice"]

    spheres_data = await volume_server.get_geometric_segmentation(
        req=GeometricSegmentationRequest(
            source=preprocessor_input.entry_data.source_db,
            structure_id=preprocessor_input.entry_data.entry_id
        )
    )
    
    response_bytes = serialize_tomogram_and_spheres(volume_data=volume_data, particles_data=spheres_data,
                                                    metadata=metadata, box=slice_box)
    # writing response to file

    with open(str((entry_folder / 'volume.bcif').resolve()), 'wb') as f: 
        f.write(response_bytes)

