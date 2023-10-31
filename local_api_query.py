import argparse
import asyncio
from enum import Enum
import json
from pathlib import Path
from typing import Literal, Optional, Protocol, Type, TypedDict, Union
from attr import dataclass

from cellstar_db.file_system.db import FileSystemVolumeServerDB
from cellstar_preprocessor.flows import segmentation
from cellstar_query.helper_methods.create_in_memory_zip_from_bytes import create_in_memory_zip_from_bytes
from cellstar_query.json_numpy_response import _NumpyJsonEncoder, JSONNumpyResponse
# from fastapi import Query
from cellstar_query.requests import VolumeRequestBox, VolumeRequestDataKind, VolumeRequestInfo

from cellstar_query.core.service import VolumeServerService
from cellstar_query.query import get_list_entries_keywords_query, get_list_entries_query, get_meshes_bcif_query, get_meshes_query, get_metadata_query, get_segmentation_box_query, get_segmentation_cell_query, get_volume_box_query, get_volume_cell_query, get_volume_info_query

# VOLUME SERVER AND DB

DEFAULT_MAX_POINTS = 100000000

@dataclass
class BaseQuery:
    name: str # can be Enum

@dataclass
class EntryDataRequiredQuery(BaseQuery):
    pass

@dataclass
class DataQuery(EntryDataRequiredQuery):
    # time and channel-id args
    pass

@dataclass
class VolumetricDataQuery(DataQuery):
    # max points arg
    isSegmentation: bool # => lattice-id arg
    isBox: bool # => box-coords arg
    type: Literal['volume', 'segmentation']

@dataclass
class MeshDataQuery(DataQuery):
    # segment-id and detail-lvl args
    pass

@dataclass
class EntryInfoQuery(EntryDataRequiredQuery):
    # for metadata, annotations, volume info
    pass

@dataclass
class GlobalInfoQuery(BaseQuery):
    pass

@dataclass
class ListEntriesQuery(GlobalInfoQuery):
    keywords: bool = False

QUERY_TYPES = [
    VolumetricDataQuery(name='volume-box', isSegmentation=False, isBox=True, type='volume'),
    VolumetricDataQuery(name='segmentation-box', isSegmentation=True, isBox=True, type='volume'),
    VolumetricDataQuery(name='volume-cell', isSegmentation=False, isBox=False, type='volume'),
    VolumetricDataQuery(name='segmentation-cell', isSegmentation=True, isBox=False, type='volume'),
    MeshDataQuery(name='mesh'),
    MeshDataQuery(name='mesh-bcif'),
    EntryInfoQuery(name='metadata'),
    EntryInfoQuery(name='annotations'),
    EntryInfoQuery(name='volume-info'),
    ListEntriesQuery(name='list-entries'),
    ListEntriesQuery(name='list-entries-keyword', keywords=True)
]

# TODO: add others
COMPOSITE_QUERY_TYPES = ['volume-and-segmentation-cell']
QUERY_TYPES_WITH_JSON_RESPONSE = ['annotations', 'metadata', 'list-entries', 'list-entries-keyword']

@dataclass
class QueryResponse:
    response: Union[bytes, str]
    # can be determined based on type of response
    # file_writing_mode: Literal['w', 'wb']

class QuerySpecificParams(TypedDict):
    data_type: Optional[Literal['volume', 'segmentation']]

# typeddict query task params
class QueryTaskParams(TypedDict):
    argaprse_args: argparse.Namespace
    volume_server: VolumeServerService
    custom_params: QuerySpecificParams

# TODO: file writing mode
class QueryTaskBase(Protocol):  
    async def execute(self) -> None:
        ...

class QueryTask(QueryTaskBase):
    def __init__(self, params: QueryTaskParams):
        args, volume_server, query_specific_params = params.values()
        self.volume_server = volume_server

class EntryDataRequiredQueryTask(QueryTask):
    def __init__(self, params: QueryTaskParams):
        args, volume_server, query_specific_params = params.values()
        super().__init__(params)
        self.entry_id = args.entry_id
        self.source_db = args.source_db

class DataQueryTask(EntryDataRequiredQueryTask):
    def __init__(self, params: QueryTaskParams):
        args, volume_server, query_specific_params = params.values()
        super().__init__(params)
        self.time = args.time
        self.channel_id = args.channel_id

class VolumetricDataQueryTask(DataQueryTask):
    def __init__(self, params: QueryTaskParams):
        args, volume_server, query_specific_params = params.values()
        super().__init__(params)
        self.max_points = args.max_points
        self.data_type = query_specific_params['data_type']
        if self.data_type == 'segmentation':
            self.lattice_id = args.lattice_id

class BoxDataQueryTask(VolumetricDataQueryTask):
    def __init__(self, params: QueryTaskParams):
        args, volume_server, query_specific_params = params.values()
        super().__init__(params)
        self.box_coords = args.box_coords
            
    async def execute(self):
        a1, a2, a3, b1, b2, b3 = self.box_coords
        if self.data_type == 'volume':
            response = await get_volume_box_query(
                volume_server=self.volume_server,
                source=self.source_db,
                id=self.entry_id,
                time=self.time,
                channel_id=self.channel_id,
                a1=a1,
                a2=a2,
                a3=a3,
                b1=b1,
                b2=b2,
                b3=b3,
                max_points=self.max_points
            )
        elif self.data_type == 'segmentation':
            response = await get_segmentation_box_query(
                volume_server=self.volume_server,
                source=self.source_db,
                id=self.entry_id,
                time=self.time,
                channel_id=self.channel_id,
                lattice_id=self.lattice_id,
                a1=a1,
                a2=a2,
                a3=a3,
                b1=b1,
                b2=b2,
                b3=b3,
                max_points=self.max_points
            )

        return QueryResponse(response=response)


class CellDataQueryTask(VolumetricDataQueryTask):
    def __init__(self, params: QueryTaskParams):
        super().__init__(params)
    async def execute(self):
        if self.data_type == 'volume':
            response = await get_volume_cell_query(
                volume_server=self.volume_server,
                source=self.source_db,
                id=self.entry_id,
                time=self.time,
                channel_id=self.channel_id,
                max_points=self.max_points
            )
        elif self.data_type == 'segmentation':
            response = await get_segmentation_cell_query(
                volume_server=self.volume_server,
                source=self.source_db,
                id=self.entry_id,
                time=self.time,
                channel_id=self.channel_id,
                lattice_id=self.lattice_id,
                max_points=self.max_points
            )
        
        return QueryResponse(response=response)



def _create_parsers(common_subparsers, query_types: list[BaseQuery]):
    parsers = []
    for query in query_types:
        parser = common_subparsers.add_parser(query.name)
        if isinstance(query, EntryDataRequiredQuery):
            parser.add_argument('--entry-id', type=str, required=True)
            parser.add_argument('--source-db', type=str, required=True)

        if isinstance(query, DataQuery):
            parser.add_argument('--time', required=True, type=int)
            parser.add_argument('--channel-id', required=True, type=int)
        
        if isinstance(query, VolumetricDataQuery):
            parser.add_argument('--max-points', type=int, default=DEFAULT_MAX_POINTS)

            if query.isSegmentation:
                parser.add_argument('--lattice-id', type=int, required=True)

            if query.isBox:
                parser.add_argument('--box-coords', nargs=6, required=True, type=float)


        if isinstance(query, MeshDataQuery):
            parser.add_argument('--segment-id', required=True, type=int)
            parser.add_argument('--detail-lvl', required=True, type=int)
        
        if isinstance(query, ListEntriesQuery):
            parser.add_argument('--limit', type=int, default=100, required=True)

            if query.keywords:
                parser.add_argument('--keyword', type=str, required=True)

        # TODO: do we need them at all?
        parsers.append(parser)
    # print(parsers)
    return parsers



async def _query(args):
    db = FileSystemVolumeServerDB(folder=Path(args.db_path))

    # initialize server
    VOLUME_SERVER = VolumeServerService(db)

    # file_writing_mode = 'wb'

    # d = QueryTask(QueryTaskParams(argaprse_args=args, volume_server, query_specific_params=VOLUME_SERVER))
    d = BoxDataQueryTask(args, data_type='volume')
    print(d)

    # if args.query_type == 'volume-box':
    #     print('volume box query')
    #     # query
    #     a1, a2, a3, b1, b2, b3 = args.box_coords
    #     response = await get_volume_box_query(
    #         volume_server=VOLUME_SERVER,
    #         source=args.source_db,
    #         id=args.entry_id,
    #         time=args.time,
    #         channel_id=args.channel_id,
    #         a1=a1,
    #         a2=a2,
    #         a3=a3,
    #         b1=b1,
    #         b2=b2,
    #         b3=b3,
    #         max_points=args.max_points
    #     )

    # elif args.query_type == 'segmentation-box':
    #     print('segmentation box query')
    #     # query
    #     a1, a2, a3, b1, b2, b3 = args.box_coords
    #     response = await get_segmentation_box_query(
    #         volume_server=VOLUME_SERVER,
    #         segmentation=args.lattice_id,
    #         source=args.source_db,
    #         id=args.entry_id,
    #         time=args.time,
    #         channel_id=args.channel_id,
    #         a1=a1,
    #         a2=a2,
    #         a3=a3,
    #         b1=b1,
    #         b2=b2,
    #         b3=b3,
    #         max_points=args.max_points
    #     )
    
    # elif args.query_type == 'segmentation-cell':
    #     print('segmentation cell query')
    #     response = await get_segmentation_cell_query(
    #         volume_server=VOLUME_SERVER,
    #         segmentation=args.lattice_id,
    #         source=args.source_db,
    #         id=args.entry_id,
    #         time=args.time,
    #         channel_id=args.channel_id,
    #         max_points=args.max_points
    #     )
    # elif args.query_type == 'volume-cell':
    #     print('volume cell query')
    #     response = await get_volume_cell_query(
    #         volume_server=VOLUME_SERVER,
    #         source=args.source_db,
    #         id=args.entry_id,
    #         time=args.time,
    #         channel_id=args.channel_id,
    #         max_points=args.max_points
    #     )

    # elif args.query_type == 'mesh':
    #     print('mesh query')
    #     file_writing_mode = 'w'
    #     response = await get_meshes_query(
    #         volume_server=VOLUME_SERVER,
    #         source=args.source_db,
    #         id=args.entry_id,
    #         time=args.time,
    #         channel_id=args.channel_id,
    #         segment_id=args.segment_id,
    #         detail_lvl=args.detail_lvl
    #     )

    # elif args.query_type == 'mesh-bcif':
    #     print('mesh-bcif query')
    #     response = await get_meshes_bcif_query(
    #         volume_server=VOLUME_SERVER,
    #         source=args.source_db,
    #         id=args.entry_id,
    #         time=args.time,
    #         channel_id=args.channel_id,
    #         segment_id=args.segment_id,
    #         detail_lvl=args.detail_lvl
    #     )

    # elif args.query_type == 'metadata':
    #     print('metadata query')
    #     file_writing_mode = 'w'
    #     response = await get_metadata_query(volume_server=VOLUME_SERVER, source=args.source_db, id=args.entry_id)
    
    # elif args.query_type == 'volume-info':
    #     print('volume info query')
    #     response = await get_volume_info_query(volume_server=VOLUME_SERVER, source=args.source_db, id=args.entry_id)

    # elif args.query_type == 'annotations':
    #     print('annotations query')
    #     file_writing_mode = 'w'
    #     metadata_response = await get_metadata_query(volume_server=VOLUME_SERVER, source=args.source_db, id=args.entry_id)
    #     response = metadata_response['annotation']

    # elif args.query_type == 'list-entries':
    #     print('list_entries query')
    #     file_writing_mode = 'w'
    #     response = await get_list_entries_query(volume_server=VOLUME_SERVER, limit=args.limit)
    
    # elif args.query_type == 'list-entries-keyword':
    #     print('list_entries query')
    #     file_writing_mode = 'w'
    #     response = await get_list_entries_keywords_query(volume_server=VOLUME_SERVER, limit=args.limit, keyword=args.keyword)
    
    # elif args.query_type == 'volume-and-segmentation-cell':
    #     print('volume-and-segmentation-cell')
    #     # PLAN
    #     # 1. get one file
    #     # 2. get another file
    #     # zip?
    #     # in memory?
    #     # https://stackoverflow.com/questions/71251353/how-to-create-a-zip-archive-containing-multiple-files-and-subfolders-in-memory
    #     # then write to zip file
    #     # https://stackoverflow.com/questions/18457678/python-write-in-memory-zip-to-file
    #     # write bytes to file
    #     # https://stackoverflow.com/a/54464733/13136429
    #     # if not, this:
    #     # https://stackoverflow.com/questions/54200941/zipfile-module-for-python3-6-write-to-bytes-instead-of-files-for-odoo
    #     file_writing_mode = 'wb'
    #     volume_bcif_bytes = await get_volume_cell_query(
    #         volume_server=VOLUME_SERVER,
    #         source=args.source_db,
    #         id=args.entry_id,
    #         time=args.time,
    #         channel_id=args.channel_id,
    #         max_points=args.max_points
    #     )
    #     segmentation_bcif_bytes = await get_segmentation_cell_query(
    #         volume_server=VOLUME_SERVER,
    #         segmentation=args.lattice_id,
    #         source=args.source_db,
    #         id=args.entry_id,
    #         time=args.time,
    #         channel_id=args.channel_id,
    #         max_points=args.max_points
    #     )
    #     response = [
    #         ('volume.bcif', volume_bcif_bytes),
    #         ('segmentation.bcif', segmentation_bcif_bytes)
    #     ]
        

    # write to file

    
    # with open(str((Path(args.out)).resolve()), file_writing_mode) as f:
    #     if args.query_type in QUERY_TYPES_WITH_JSON_RESPONSE:
    #         json.dump(response, f, indent=4)
    #     elif args.query_type == 'mesh':
    #         json_dump = json.dumps(response, 
    #                    cls=_NumpyJsonEncoder)
    #         json.dump(json_dump, f, indent=4)
    #     elif args.query_type in COMPOSITE_QUERY_TYPES:
    #         zip_data = create_in_memory_zip_from_bytes(response)
    #         f.write(zip_data)
    #     else: 
    #         f.write(response)

async def main():
    # initialize dependencies
    # PARSING
    main_parser = argparse.ArgumentParser(add_help=False)
    
    common_subparsers = main_parser.add_subparsers(dest='query_type', help='query type')
    # COMMON ARGUMENTS
    main_parser.add_argument('--db_path', type=str, required=True)
    main_parser.add_argument('--out', type=str, required=True)

    _create_parsers(common_subparsers=common_subparsers, query_types=QUERY_TYPES)

    # box_parser = common_subparsers.add_parser('volume-box')
    # box_parser.add_argument('--entry-id', type=str, required=True)
    # box_parser.add_argument('--source-db', type=str, required=True)
    # box_parser.add_argument('--time', required=True, type=int)
    # box_parser.add_argument('--channel-id', required=True, type=int)
    # box_parser.add_argument('--box-coords', nargs=6, required=True, type=float)
    # # TODO: fix default
    # box_parser.add_argument('--max-points', type=int, default=DEFAULT_MAX_POINTS)

    # # SEGMENTATION BOX
    # segm_box_parser = common_subparsers.add_parser('segmentation-box')
    # segm_box_parser.add_argument('--entry-id', type=str, required=True)
    # segm_box_parser.add_argument('--source-db', type=str, required=True)
    # segm_box_parser.add_argument('--time', required=True, type=int)
    # segm_box_parser.add_argument('--channel-id', required=True, type=int)
    # segm_box_parser.add_argument('--lattice-id', type=int, required=True)
    # segm_box_parser.add_argument('--box-coords', nargs=6, required=True, type=float)
    # # TODO: fix default
    # segm_box_parser.add_argument('--max-points', type=int, default=DEFAULT_MAX_POINTS)
    
    # # VOLUME CELL
    # volume_cell_parser = common_subparsers.add_parser('volume-cell')
    # volume_cell_parser.add_argument('--entry-id', type=str, required=True)
    # volume_cell_parser.add_argument('--source-db', type=str, required=True)
    # volume_cell_parser.add_argument('--time', required=True, type=int)
    # volume_cell_parser.add_argument('--channel-id', required=True, type=int)
    # # TODO: fix default
    # volume_cell_parser.add_argument('--max-points', type=int, default=DEFAULT_MAX_POINTS)

    # # SEGMENTATION CELL
    # segm_cell_parser = common_subparsers.add_parser('segmentation-cell')
    # segm_cell_parser.add_argument('--entry-id', type=str, required=True)
    # segm_cell_parser.add_argument('--source-db', type=str, required=True)
    # segm_cell_parser.add_argument('--time', required=True, type=int)
    # segm_cell_parser.add_argument('--channel-id', required=True, type=int)
    # segm_cell_parser.add_argument('--lattice-id', type=int, required=True)
    # # TODO: fix default
    # segm_cell_parser.add_argument('--max-points', type=int, default=DEFAULT_MAX_POINTS)

    # # METADATA
    # metadata_parser = common_subparsers.add_parser('metadata')
    # metadata_parser.add_argument('--entry-id', type=str, required=True)
    # metadata_parser.add_argument('--source-db', type=str, required=True)

    # # VOLUME INFO
    # volume_info_parser = common_subparsers.add_parser('volume-info')
    # volume_info_parser.add_argument('--entry-id', type=str, required=True)
    # volume_info_parser.add_argument('--source-db', type=str, required=True)

    # # ANNOTATIONS
    # annotations_parser = common_subparsers.add_parser('annotations')
    # annotations_parser.add_argument('--entry-id', type=str, required=True)
    # annotations_parser.add_argument('--source-db', type=str, required=True)

    # # MESHES
    # meshes_parser = common_subparsers.add_parser('mesh')
    # meshes_parser.add_argument('--entry-id', type=str, required=True)
    # meshes_parser.add_argument('--source-db', type=str, required=True)
    # meshes_parser.add_argument('--time', required=True, type=int)
    # meshes_parser.add_argument('--channel-id', required=True, type=int)
    # meshes_parser.add_argument('--segment-id', required=True, type=int)
    # meshes_parser.add_argument('--detail-lvl', required=True, type=int)

    # meshes_bcif_parser = common_subparsers.add_parser('mesh-bcif')
    # meshes_bcif_parser.add_argument('--entry-id', type=str, required=True)
    # meshes_bcif_parser.add_argument('--source-db', type=str, required=True)
    # meshes_bcif_parser.add_argument('--time', required=True, type=int)
    # meshes_bcif_parser.add_argument('--channel-id', required=True, type=int)
    # meshes_bcif_parser.add_argument('--segment-id', required=True, type=int)
    # meshes_bcif_parser.add_argument('--detail-lvl', required=True, type=int)
    
    # list_entries_parser = common_subparsers.add_parser('list-entries')
    # list_entries_parser.add_argument('--limit', type=int, default=100, required=True)

    # list_entries_keyword_parser = common_subparsers.add_parser('list-entries-keyword')
    # list_entries_keyword_parser.add_argument('--limit', type=int, default=100, required=True)
    # list_entries_keyword_parser.add_argument('--keyword', type=str, required=True)
    
    # volume_and_segm_cell_parser = common_subparsers.add_parser('volume-and-segmentation-cell')
    # volume_and_segm_cell_parser.add_argument('--entry-id', type=str, required=True)
    # volume_and_segm_cell_parser.add_argument('--source-db', type=str, required=True)
    # volume_and_segm_cell_parser.add_argument('--time', required=True, type=int)
    # volume_and_segm_cell_parser.add_argument('--channel-id', required=True, type=int)
    # volume_and_segm_cell_parser.add_argument('--lattice-id', type=int, required=True)
    # # TODO: fix default
    # volume_and_segm_cell_parser.add_argument('--max-points', type=int, default=DEFAULT_MAX_POINTS)
    

    args = main_parser.parse_args()

    await _query(args)


if __name__ == '__main__':
    asyncio.run(main())


# python local_api_query.py --out local_query1.bcif volume-cell --db_path preprocessor/temp/test_db --entry-id emd-1832 --source-db emdb --time 0 --channel-id 0 --lattice-id 0