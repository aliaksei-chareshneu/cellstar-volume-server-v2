import asyncio
from pathlib import Path
from typing import Optional
from fastapi import Query, Response
from db.file_system.db import FileSystemVolumeServerDB
from server.app.api.requests import VolumeRequestBox, VolumeRequestDataKind, VolumeRequestInfo
from server.app.core.service import VolumeServerService


FILENAME = 'server/app/dev/test_cif.bcif'

# initialize dependencies
db = FileSystemVolumeServerDB(folder=Path('test-data/db'))

# initialize server
VOLUME_SERVER = VolumeServerService(db)

async def get_segmentation_box(
    source: str,
    id: str,
    segmentation: int,
    channel_id: int,
    time: int,
    a1: float,
    a2: float,
    a3: float,
    b1: float,
    b2: float,
    b3: float,
    max_points: Optional[int] = Query(0)
):
    response = await VOLUME_SERVER.get_volume_data(
        req=VolumeRequestInfo(
            source=source,
            structure_id=id,
            segmentation_id=segmentation,
            channel_id=channel_id,
            time=time,
            max_points=max_points,
            data_kind=VolumeRequestDataKind.segmentation,
        ),
        req_box=VolumeRequestBox(bottom_left=(a1, a2, a3), top_right=(b1, b2, b3)),
    )
    # return Response(response, headers={"Content-Disposition": f'attachment;filename="{id}.bcif"'})
    with open(FILENAME, 'wb') as f: 
        f.write(response)

if __name__ == '__main__':
    asyncio.run(
        get_segmentation_box(
            'idr',
            'idr-13457537',
            # check if lattice_id = 0 for that entry
            0,
            0,
            0,
            -10000000,
            -10000000,
            -10000000,
            10000000,
            10000000,
            10000000,
            100000
            
        )

        # get_segmentation_box(
        #     'emdb',
        #     'emd-1832',
        #     # check if lattice_id = 0 for that entry
        #     0,
        #     0,
        #     0,
        #     0,
        #     0,
        #     0,
        #     10,
        #     10,
        #     10,
        #     100000
            
        # )
    )
    