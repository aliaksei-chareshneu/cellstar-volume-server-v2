from typing import Optional

from fastapi import FastAPI, Query, Response
from starlette.responses import JSONResponse

from cellstar_query.core.service import VolumeServerService
from cellstar_query.serialization.json_numpy_response import JSONNumpyResponse
from server.app.settings import settings
from cellstar_query.requests import GeometricSegmentationRequest
from cellstar_query.query import HTTP_CODE_UNPROCESSABLE_ENTITY, get_list_entries_query, get_meshes_bcif_query, get_meshes_query, get_metadata_query, get_segmentation_box_query, get_segmentation_cell_query, get_volume_box_query, get_volume_cell_query, get_volume_info_query, get_list_entries_keyword_query


def configure_endpoints(app: FastAPI, volume_server: VolumeServerService):
    @app.get("/v2/version")
    async def get_version():
        # settings = app.settings
        git_tag = settings.GIT_TAG
        git_sha = settings.GIT_SHA

        return {
            'git_tag': git_tag,
            'git_sha': git_sha
        }


    @app.get("/v2/list_entries/{limit}")
    async def get_entries(limit: int = 100):
        response = await get_list_entries_query(volume_server=volume_server, limit=limit)
        return response

    @app.get("/v2/list_entries/{limit}/{keyword}")
    async def get_entries_keyword(keyword: str, limit: int = 100):
        response = await get_list_entries_keyword_query(
            volume_server=volume_server, limit=limit, keyword=keyword
        )
        return response

    @app.get("/v2/{source}/{id}/segmentation/box/{segmentation}/{time}/{a1}/{a2}/{a3}/{b1}/{b2}/{b3}")
    async def get_segmentation_box(
        source: str,
        id: str,
        segmentation: str,
        time: int,
        a1: float,
        a2: float,
        a3: float,
        b1: float,
        b2: float,
        b3: float,
        max_points: Optional[int] = Query(0)
    ):
        response = await get_segmentation_box_query(
            volume_server=volume_server,
            source=source,
            id=id,
            segmentation_id=segmentation,
            time=time,
            a1=a1,
            a2=a2,
            a3=a3,
            b1=b1,
            b2=b2,
            b3=b3,
            max_points=max_points
        )

        return Response(response, headers={"Content-Disposition": f'attachment;filename="{id}.bcif"'})

    @app.get("/v2/{source}/{id}/volume/box/{time}/{channel_id}/{a1}/{a2}/{a3}/{b1}/{b2}/{b3}")
    async def get_volume_box(
        source: str,
        id: str,
        time: int,
        channel_id: str,
        a1: float,
        a2: float,
        a3: float,
        b1: float,
        b2: float,
        b3: float,
        max_points: Optional[int] = Query(0),
    ):
        response = await get_volume_box_query(
            volume_server=volume_server,
            source=source,
            id=id,
            time=time,
            channel_id=channel_id,
            a1=a1,
            a2=a2,
            a3=a3,
            b1=b1,
            b2=b2,
            b3=b3,
            max_points=max_points
        )

        return Response(response, headers={"Content-Disposition": f'attachment;filename="{id}.bcif"'})

    @app.get("/v2/{source}/{id}/segmentation/cell/{segmentation}/{time}")
    async def get_segmentation_cell(source: str, id: str, segmentation: str, time: int, max_points: Optional[int] = Query(0)):
        response = await get_segmentation_cell_query(
            volume_server=volume_server,
            source=source,
            id=id,
            segmentation=segmentation,
            time=time,
            max_points=max_points
        )

        return Response(response, headers={"Content-Disposition": f'attachment;filename="{id}.bcif"'})

    @app.get("/v2/{source}/{id}/volume/cell/{time}/{channel_id}")
    async def get_volume_cell(source: str, id: str, time: int, channel_id: str, max_points: Optional[int] = Query(0)):
        response = await get_volume_cell_query(
            volume_server=volume_server,
            source=source,
            id=id,
            time=time,
            channel_id=channel_id,
            max_points=max_points
        )

        return Response(response, headers={"Content-Disposition": f'attachment;filename="{id}.bcif"'})

    @app.get("/v2/{source}/{id}/metadata")
    async def get_metadata(
        source: str,
        id: str,
    ):
        metadata = await get_metadata_query(volume_server=volume_server, source=source, id=id)

        return metadata

    @app.get("/v2/{source}/{id}/mesh/{segmentation_id}/{time}/{segment_id}/{detail_lvl}")
    async def get_meshes(source: str, id: str, segmentation_id: str,
                          time: int,
                          segment_id: int,
                          detail_lvl: int):
        response = await get_meshes_query(
            volume_server=volume_server,
            source=source,
            id=id,
            segmentation_id=segmentation_id,
            time=time,
            segment_id=segment_id,
            detail_lvl=detail_lvl
        )
        return response
        
    @app.get("/v2/{source}/{id}/geometric_segmentation/{segmentation_id}")
    async def get_geometric_segmentation(source: str, id: str, segmentation_id: str):
        request = GeometricSegmentationRequest(source=source, structure_id=id, segmentation_id=segmentation_id)
        try:
            geometric_segmentation = await volume_server.get_geometric_segmentation(request)
            return JSONNumpyResponse(geometric_segmentation)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=HTTP_CODE_UNPROCESSABLE_ENTITY)

    @app.get("/v2/{source}/{id}/volume_info")
    async def get_volume_info(
        source: str,
        id: str,
    ):
        response_bytes = await get_volume_info_query(volume_server=volume_server, source=source, id=id)

        return Response(response_bytes, headers={"Content-Disposition": f'attachment;filename="{id}-volume_info.bcif"'})

    @app.get("/v2/{source}/{id}/mesh_bcif/{segmentation_id}/{time}/{segment_id}/{detail_lvl}")
    async def get_meshes_bcif(source: str, id: str, segmentation_id: str,
                          time: int,
                          segment_id: int,
                          detail_lvl: int):
        response = await get_meshes_bcif_query(
            volume_server=volume_server,
            source=source,
            id=id,
            segmentation_id=segmentation_id,
            time=time,
            segment_id=segment_id,
            detail_lvl=detail_lvl
        )
        return response