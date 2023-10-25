
from fastapi import Response
from fastapi.responses import JSONResponse

# TODO: move these to query package
from cellstar_query.requests import EntriesRequest, MeshRequest, MetadataRequest, VolumeRequestBox, VolumeRequestDataKind, VolumeRequestInfo
from cellstar_query.core.service import VolumeServerService
from cellstar_query.json_numpy_response import JSONNumpyResponse


HTTP_CODE_UNPROCESSABLE_ENTITY = 422

async def get_segmentation_box_query(
        volume_server: VolumeServerService,
        source: str,
        id: str,
        segmentation: str,
        time: int,
        channel_id: int,
        a1: float,
        a2: float,
        a3: float,
        b1: float,
        b2: float,
        b3: float,
        max_points: int
):
    response = await volume_server.get_volume_data(
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
    return response

async def get_volume_box_query(
        volume_server: VolumeServerService,
        source: str,
        id: str,
        time: int,
        channel_id: int,
        a1: float,
        a2: float,
        a3: float,
        b1: float,
        b2: float,
        b3: float,
        max_points: int
):
    response = await volume_server.get_volume_data(
        req=VolumeRequestInfo(
            source=source,
            structure_id=id,
            channel_id=channel_id,
            time=time,
            max_points=max_points,
            data_kind=VolumeRequestDataKind.volume,
        ),
        req_box=VolumeRequestBox(bottom_left=(a1, a2, a3), top_right=(b1, b2, b3)),
    )
    return response


async def get_segmentation_cell_query(
    volume_server: VolumeServerService,
    source: str,
    id: str,
    segmentation: str,
    time: int,
    channel_id: int,
    max_points: int
):
    response = await volume_server.get_volume_data(
            req=VolumeRequestInfo(
                source=source,
                structure_id=id,
                segmentation_id=segmentation,
                time=time,
                channel_id=channel_id,
                max_points=max_points,
                data_kind=VolumeRequestDataKind.segmentation,
            ),
        )
    
    return response


async def get_volume_cell_query(
    volume_server: VolumeServerService,
    source: str,
    id: str,
    time: int,
    channel_id: int,
    max_points: int
):
    response = await volume_server.get_volume_data(
            req=VolumeRequestInfo(
                source=source, structure_id=id,
                time=time, channel_id=channel_id, max_points=max_points, data_kind=VolumeRequestDataKind.volume
            ),
        )
    
    return response

async def get_metadata_query(
        volume_server: VolumeServerService,
        id: str,
    source: str,
):
    request = MetadataRequest(source=source, structure_id=id)
    metadata = await volume_server.get_metadata(request)
    return metadata

async def get_volume_info_query(
        volume_server: VolumeServerService,
        id: str,
    source: str,
):
    
    request = MetadataRequest(source=source, structure_id=id)
    response_bytes = await volume_server.get_volume_info(request)

    return response_bytes

async def get_list_entries_query(
        volume_server: VolumeServerService,
        limit: int
):
    request = EntriesRequest(limit=limit, keyword="")
    response = await volume_server.get_entries(request)

    return response    

async def get_list_entries_keywords_query(
        volume_server: VolumeServerService,
        limit: int,
        keyword: str
):
    request = EntriesRequest(limit=limit, keyword=keyword)
    response = await volume_server.get_entries(request)
    return response

async def get_meshes_query(
        volume_server: VolumeServerService,
        source: str, id: str, time: int, channel_id: int, segment_id: int, detail_lvl: int
):
    request = MeshRequest(source=source, structure_id=id, segment_id=segment_id, detail_lvl=detail_lvl, time=time, channel_id=channel_id)
    meshes = await volume_server.get_meshes(request)
    return meshes
    
    # try:
    #     meshes = await volume_server.get_meshes(request)
    #     return JSONNumpyResponse(meshes)
    # except Exception as e:
    #     return JSONResponse({"error": str(e)}, status_code=HTTP_CODE_UNPROCESSABLE_ENTITY)

async def get_meshes_bcif_query(
        volume_server: VolumeServerService,
        source: str, id: str, time: int, channel_id: int, segment_id: int, detail_lvl: int
):
    request = MeshRequest(source=source, structure_id=id, segment_id=segment_id, detail_lvl=detail_lvl, time=time, channel_id=channel_id)
    response_bytes = await volume_server.get_meshes_bcif(request)
    return response_bytes


    # request = MeshRequest(source=source, structure_id=id, segment_id=segment_id, detail_lvl=detail_lvl, time=time, channel_id=channel_id)
    # try:
    #     response_bytes = await volume_server.get_meshes_bcif(request)
    #     return Response(
    #         response_bytes, headers={"Content-Disposition": f'attachment;filename="{id}-volume_info.bcif"'}
    #     )
    # except Exception as e:
    #     return JSONResponse({"error": str(e)}, status_code=HTTP_CODE_UNPROCESSABLE_ENTITY)
    # finally:
    #     pass