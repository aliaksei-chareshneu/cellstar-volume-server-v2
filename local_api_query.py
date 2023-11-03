import argparse
import asyncio
from enum import Enum
from importlib.metadata import requires
import json
from pathlib import Path
from typing import Any, Coroutine, Literal, Optional, Protocol, Type, TypedDict, Union
from attr import dataclass

from cellstar_db.file_system.db import FileSystemVolumeServerDB
from cellstar_preprocessor.flows import segmentation
from cellstar_query.helper_methods.create_in_memory_zip import create_in_memory_zip
from cellstar_query.json_numpy_response import _NumpyJsonEncoder, JSONNumpyResponse
# from fastapi import Query
from cellstar_query.requests import VolumeRequestBox, VolumeRequestDataKind, VolumeRequestInfo

from cellstar_query.core.service import VolumeServerService
from cellstar_query.query import get_list_entries_keywords_query, get_list_entries_query, get_meshes_bcif_query, get_meshes_query, get_metadata_query, get_segmentation_box_query, get_segmentation_cell_query, get_volume_box_query, get_volume_cell_query, get_volume_info_query

# VOLUME SERVER AND DB

DEFAULT_MAX_POINTS = 100000000

class JsonQueryParams(TypedDict):
    subquery_types: list[str]
    args: dict

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

# need composite query with subqueries
@dataclass
class CompositeQuery(BaseQuery):
    # subqueries: list[BaseQuery]
    pass

QUERY_TYPES = [
    VolumetricDataQuery(name='volume-box', isSegmentation=False, isBox=True),
    VolumetricDataQuery(name='segmentation-box', isSegmentation=True, isBox=True),
    VolumetricDataQuery(name='volume-cell', isSegmentation=False, isBox=False),
    VolumetricDataQuery(name='segmentation-cell', isSegmentation=True, isBox=False),
    MeshDataQuery(name='mesh'),
    MeshDataQuery(name='mesh-bcif'),
    EntryInfoQuery(name='metadata'),
    EntryInfoQuery(name='annotations'),
    EntryInfoQuery(name='volume-info'),
    ListEntriesQuery(name='list-entries'),
    ListEntriesQuery(name='list-entries-keyword', keywords=True),
    CompositeQuery(name='composite')
]

# TODO: add others
COMPOSITE_QUERY_TYPES = ['composite']
QUERY_TYPES_WITH_JSON_RESPONSE = ['annotations', 'metadata', 'list-entries', 'list-entries-keyword']

@dataclass
# NOTE: for now just for volume + segmentation response
class CompositeQueryTaskResponse:
    # e.g. [('volume.bcif', volume_bcif_bytes),
    #         ('segmentation.bcif', segmentation_bcif_bytes)]
    response: list[tuple[str, bytes]]

@dataclass
class QueryResponse:
    response: Union[bytes, str, CompositeQueryTaskResponse]
    type: str

class QuerySpecificParams(TypedDict):
    data_type: Optional[Literal['volume', 'segmentation']]
    mesh_query_type: Optional[Literal['mesh', 'mesh-bcif']]
    entry_info_query_type: Optional[Literal['metadata', 'volume-info', 'annotations']]
    global_info_query_type: Optional[Literal['list-entries', 'list-entries-keyword']]

# typeddict query task params
class QueryTaskParams(TypedDict):
    argaprse_args: argparse.Namespace
    volume_server: VolumeServerService
    custom_params: Optional[QuerySpecificParams]

class QueryTaskBase(Protocol):  
    async def execute(self) -> QueryResponse:
        ...

class QueryTask(QueryTaskBase):
    def __init__(self, params: QueryTaskParams):
        args, volume_server, query_specific_params = params.values()
        self.volume_server = volume_server
        self.query_type = args.query_type

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
        if 'max_points' in args:
            self.max_points = args.max_points
        else:
            self.max_points = DEFAULT_MAX_POINTS
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
                segmentation=self.lattice_id,
                a1=a1,
                a2=a2,
                a3=a3,
                b1=b1,
                b2=b2,
                b3=b3,
                max_points=self.max_points
            )

        return QueryResponse(response=response, type=self.query_type)


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
                segmentation=self.lattice_id,
                max_points=self.max_points
            )
        
        return QueryResponse(response=response, type=self.query_type)

class MeshDataQueryTask(DataQueryTask):
    def __init__(self, params: QueryTaskParams):
        args, volume_server, query_specific_params = params.values()
        super().__init__(params)
        self.mesh_query_type = query_specific_params['mesh_query_type']
        self.segment_id = args.segment_id
        self.detail_lvl = args.detail_lvl
    async def execute(self):
        if self.mesh_query_type == 'mesh':
            response = await get_meshes_query(
                volume_server=self.volume_server,
                source=self.source_db,
                id=self.entry_id,
                time=self.time,
                channel_id=self.channel_id,
                segment_id=self.segment_id,
                detail_lvl=self.detail_lvl
            )
        elif self.mesh_query_type == 'mesh-bcif':
            response = await get_meshes_bcif_query(
                volume_server=self.volume_server,
                source=self.source_db,
                id=self.entry_id,
                time=self.time,
                channel_id=self.channel_id,
                segment_id=self.segment_id,
                detail_lvl=self.detail_lvl
            )
        return QueryResponse(response=response, type=self.query_type)

class EntryInfoQueryTask(EntryDataRequiredQueryTask):
    def __init__(self, params: QueryTaskParams):
        args, volume_server, query_specific_params = params.values()
        super().__init__(params)
        self.entry_info_query_type = query_specific_params['entry_info_query_type']
    async def execute(self):
        if self.entry_info_query_type == 'metadata':
            response = await get_metadata_query(volume_server=self.volume_server, source=self.source_db, id=self.entry_id)
        elif self.entry_info_query_type == 'volume-info':
            response = await get_volume_info_query(volume_server=self.volume_server, source=self.source_db, id=self.entry_id)
        elif self.entry_info_query_type == 'annotations':
            metadata_response = await get_metadata_query(volume_server=self.volume_server, source=self.source_db, id=self.entry_id)
            response = metadata_response['annotation']

        return QueryResponse(response=response, type=self.query_type)

class GlobalInfoQueryTask(QueryTask):
    def __init__(self, params: QueryTaskParams):
        args, volume_server, query_specific_params = params.values()
        super().__init__(params)
        self.global_info_query_type = query_specific_params['global_info_query_type']
        self.limit = args.limit
        if self.global_info_query_type == 'list-entries-keyword':
            self.keyword = args.keyword
    async def execute(self):
        if self.global_info_query_type == 'list-entries':
            response = await get_list_entries_query(volume_server=self.volume_server, limit=self.limit)
        elif self.global_info_query_type == 'list-entries-keyword':
            response = await get_list_entries_keywords_query(volume_server=self.volume_server, limit=self.limit, keyword=self.keyword)

        return QueryResponse(response=response, type=self.query_type)

class CompositeQueryTask(QueryTask):
    def __init__(self, subtasks: list[QueryTask], json_with_query_params: JsonQueryParams):
        # super().__init__(params)
        self.subtasks = subtasks
        self.json_with_query_params = json_with_query_params
    async def execute(self):
        composite_response = []
        for subtask in self.subtasks:
            response = await subtask.execute()
            # TODO: how to get extension?
            if isinstance(response.response, bytes):
                extension = '.bcif'
            elif isinstance(response.response, dict):
                extension = '.json'

            composite_response.append(
                (f'{response.type}{extension}', response.response)
            )

        composite_response.append(
            ('query.json', self.json_with_query_params)
        )

        return CompositeQueryTaskResponse(response=composite_response)

def _add_arguments(parser, query: BaseQuery):
    if isinstance(query, EntryDataRequiredQuery):
        parser.add_argument('--entry-id', type=str, required=True, help='Entry ID in the database (e.g. "emd-1832")')
        parser.add_argument('--source-db', type=str, required=True, help='Source database (e.g. "emdb")')

    if isinstance(query, DataQuery):
        parser.add_argument('--time', required=True, type=int, help='Timeframe (e.g. 0)')
        parser.add_argument('--channel-id', required=True, type=int, help='Channel ID (e.g 0)')
    
    if isinstance(query, VolumetricDataQuery):
        parser.add_argument('--max-points', type=int, default=DEFAULT_MAX_POINTS, help='Maximum number of points')

        if query.isSegmentation:
            parser.add_argument('--lattice-id', type=int, required=True, help='Lattice ID (e.g. 0)')

        if query.isBox:
            parser.add_argument('--box-coords', nargs=6, required=True, type=float, help='XYZ coordinates of bottom left and top right of query box in Angstroms')


    if isinstance(query, MeshDataQuery):
        parser.add_argument('--segment-id', required=True, type=int, help='Segment ID of mesh (e.g 1)')
        parser.add_argument('--detail-lvl', required=True, type=int, help='Required detail level (1 is highest resolution)')
    
    if isinstance(query, ListEntriesQuery):
        parser.add_argument('--limit', type=int, default=100, required=True, help='Maximum number of entries')

        if query.keywords:
            parser.add_argument('--keyword', type=str, required=True, help='Keyword')
    
    if isinstance(query, CompositeQuery):
        parser.add_argument('--json-params-path', required=True, type=str, help='Path to .json file with parameters for composite query')


def _create_parsers(common_subparsers, query_types: list[BaseQuery]):
    parsers = []
    for query in query_types:
        help_message = (' '.join(query.name.split('-'))).capitalize() + ' query'
        parser = common_subparsers.add_parser(query.name, help=help_message)
        _add_arguments(parser=parser, query=query)
        # TODO: do we need them at all?
        parsers.append(parser)
    # print(parsers)
    return parsers

def _write_to_file(args: argparse.Namespace, response: Union[QueryResponse, CompositeQueryTaskResponse]):
    r = response.response
    if isinstance(r, bytes) or isinstance(response, CompositeQueryTaskResponse):
        file_writing_mode = 'wb'
    elif isinstance(r, str) or isinstance(r, list) or isinstance(r, dict):
        file_writing_mode = 'w'
    else:
        raise Exception('response type is not supported')
    
    with open(str(Path(args.out).resolve()), file_writing_mode) as f:
        if args.query_type in QUERY_TYPES_WITH_JSON_RESPONSE:
            json.dump(r, f, indent=4)
        elif args.query_type == 'mesh':
            json_dump = json.dumps(r, 
                       cls=_NumpyJsonEncoder)
            json.dump(json_dump, f, indent=4)
        elif args.query_type in COMPOSITE_QUERY_TYPES:
            zip_data = create_in_memory_zip(r)
            f.write(zip_data)
        else: 
            f.write(r)

def _create_task(args):
    db = FileSystemVolumeServerDB(folder=Path(args.db_path))

    # initialize server
    volume_server = VolumeServerService(db)
 
    task = None
    query_params = QueryTaskParams(argaprse_args=args, volume_server=volume_server)
    if args.query_type == 'volume-box':
        print('volume box query')
        query_params['custom_params'] = {
            'data_type': 'volume'
        }
        task = BoxDataQueryTask(params=query_params)
        
    elif args.query_type == 'segmentation-box':
        print('segmentation box query')
        # query
        query_params['custom_params'] = {
            'data_type': 'segmentation'
        }
        task = BoxDataQueryTask(params=query_params)
    
    elif args.query_type == 'segmentation-cell':
        print('segmentation cell query')
        query_params['custom_params'] = {
            'data_type': 'segmentation'
        }
        task = CellDataQueryTask(params=query_params)

    elif args.query_type == 'volume-cell':
        print('volume cell query')
        query_params['custom_params'] = {
            'data_type': 'volume'
        }
        task = CellDataQueryTask(params=query_params)

    elif args.query_type in ['mesh', 'mesh-bcif']:
        print(f'{args.query_type}')
        query_params['custom_params'] = {
            'mesh_query_type': args.query_type
        }
        task = MeshDataQueryTask(params=query_params)

    elif args.query_type in ['metadata', 'volume-info', 'annotations']:
        print(f'{args.query_type} query')
        query_params['custom_params'] = {
            'entry_info_query_type': args.query_type
        }
        task = EntryInfoQueryTask(params=query_params)

    elif args.query_type in ['list-entries', 'list-entries-keyword']:
        print(f'{args.query_type} query')
        query_params['custom_params'] = {
            'global_info_query_type': args.query_type
        }
        task = GlobalInfoQueryTask(params=query_params)

    return task

def _parse_json_with_query_params(json_path: Path):
    args = argparse.Namespace()
    argparse_args_dict = vars(args)
    with open(json_path.resolve(), "r", encoding="utf-8") as f:
        # TODO: validate?
        raw_json: JsonQueryParams = json.load(f)
        # print(d)

        # create argparse args
        for arg, arg_value in raw_json['args'].items():
            argparse_args_dict[f'{arg}'] = arg_value

        # print('args namespace')
        # print(args)

        subquery_types = raw_json['subquery_types']

    return raw_json, args, subquery_types

async def _query(args):
    if args.query_type not in COMPOSITE_QUERY_TYPES:
        task = _create_task(args)
    else:
        raw_json, argparse_args, subquery_types = _parse_json_with_query_params(Path(args.json_params_path))
        subtasks = []
        # TODO: create args separately for each subquery type?
        for subquery_type in subquery_types:
            argparse_args.query_type = subquery_type
            subtask = _create_task(argparse_args)
            subtasks.append(subtask)
        

        task = CompositeQueryTask(subtasks=subtasks, json_with_query_params=raw_json)
        
    response = await task.execute()
    _write_to_file(args=args, response=response)
    
async def main():
    # initialize dependencies
    # PARSING
    # NOTE: python local_api_query.py volume-box --help - will produce help message for subcommands
    main_parser = argparse.ArgumentParser(add_help=True)
    # TODO: Example of usage help
    # https://stackoverflow.com/a/10930713/13136429

    # help for subparsers
    # https://stackoverflow.com/a/56516183/13136429
    common_subparsers = main_parser.add_subparsers(title='Query type', dest='query_type', help='Select one of: ')
    # COMMON ARGUMENTS
    required_named = main_parser.add_argument_group('Required named arguments')
    required_named.add_argument('--db_path', type=str, required=True, help='Path to db')
    required_named.add_argument('--out', type=str, required=True, help='Path to output file including extension')

    _create_parsers(common_subparsers=common_subparsers, query_types=QUERY_TYPES)

    args = main_parser.parse_args()

    await _query(args)


if __name__ == '__main__':
    asyncio.run(main())


# python local_api_query.py --out local_query1.bcif volume-cell --db_path preprocessor/temp/test_db --entry-id emd-1832 --source-db emdb --time 0 --channel-id 0 --lattice-id 0