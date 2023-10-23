from typing import Optional

from fastapi import FastAPI, Query, Response
from starlette.responses import JSONResponse

from app.api.requests import (
    EntriesRequest,
    MeshRequest,
    MetadataRequest,
    VolumeRequestBox,
    VolumeRequestDataKind,
    VolumeRequestInfo,
)
from app.core.service import VolumeServerService
from app.serialization.json_numpy_response import JSONNumpyResponse
from app.settings import settings
from server.app.api.requests import GeometricSegmentationRequest
from server.query.query import get_segmentation_box_query, get_segmentation_cell_query, get_volume_box_query, get_volume_cell_query
HTTP_CODE_UNPROCESSABLE_ENTITY = 422


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
        request = EntriesRequest(limit=limit, keyword="")
        response = await volume_server.get_entries(request)

        return response

    @app.get("/v2/list_entries/{limit}/{keyword}")
    async def get_entries_keyword(keyword: str, limit: int = 100):
        request = EntriesRequest(limit=limit, keyword=keyword)
        response = await volume_server.get_entries(request)

        return response

    @app.get("/v2/{source}/{id}/segmentation/box/{segmentation}/{time}/{channel_id}/{a1}/{a2}/{a3}/{b1}/{b2}/{b3}")
    async def get_segmentation_box(
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
        max_points: Optional[int] = Query(0)
    ):
        response = await get_segmentation_box_query(
            volume_server=volume_server,
            source=source,
            id=id,
            segmentation=segmentation,
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

    @app.get("/v2/{source}/{id}/volume/box/{time}/{channel_id}/{a1}/{a2}/{a3}/{b1}/{b2}/{b3}")
    async def get_volume_box(
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

    @app.get("/v2/{source}/{id}/segmentation/cell/{segmentation}/{time}/{channel_id}")
    async def get_segmentation_cell(source: str, id: str, segmentation: str, time: int, channel_id: int,  max_points: Optional[int] = Query(0)):
        response = await get_segmentation_cell_query(
            volume_server=volume_server,
            source=source,
            id=id,
            segmentation=segmentation,
            time=time,
            channel_id=channel_id,
            max_points=max_points
        )

        return Response(response, headers={"Content-Disposition": f'attachment;filename="{id}.bcif"'})

    @app.get("/v2/{source}/{id}/volume/cell/{time}/{channel_id}")
    async def get_volume_cell(source: str, id: str, time: int, channel_id: int, max_points: Optional[int] = Query(0)):
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
        request = MetadataRequest(source=source, structure_id=id)
        metadata = await volume_server.get_metadata(request)

        return metadata

    @app.get("/v2/{source}/{id}/mesh/{segment_id}/{detail_lvl}/{time}/{channel_id}")
    async def get_meshes(source: str, id: str, time: int, channel_id: int, segment_id: int, detail_lvl: int):
        request = MeshRequest(source=source, structure_id=id, segment_id=segment_id, detail_lvl=detail_lvl, time=time, channel_id=channel_id)
        try:
            meshes = await volume_server.get_meshes(request)
            return JSONNumpyResponse(meshes)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=HTTP_CODE_UNPROCESSABLE_ENTITY)

    # TODO: time, channel?
    # TODO: segment id or all shape primitives segments at once? probably at once
    @app.get("/v2/{source}/{id}/geometric_segmentation")
    async def get_geometric_segmentation(source: str, id: str):
        request = GeometricSegmentationRequest(source=source, structure_id=id)
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
        request = MetadataRequest(source=source, structure_id=id)
        response_bytes = await volume_server.get_volume_info(request)
        return Response(response_bytes, headers={"Content-Disposition": f'attachment;filename="{id}-volume_info.bcif"'})

    @app.get("/v2/{source}/{id}/mesh_bcif/{segment_id}/{detail_lvl}/{time}/{channel_id}")
    async def get_meshes_bcif(source: str, id: str, time: int, channel_id: int, segment_id: int, detail_lvl: int):
        request = MeshRequest(source=source, structure_id=id, segment_id=segment_id, detail_lvl=detail_lvl, time=time, channel_id=channel_id)
        try:
            response_bytes = await volume_server.get_meshes_bcif(request)
            return Response(
                response_bytes, headers={"Content-Disposition": f'attachment;filename="{id}-volume_info.bcif"'}
            )
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=HTTP_CODE_UNPROCESSABLE_ENTITY)
        finally:
            pass
