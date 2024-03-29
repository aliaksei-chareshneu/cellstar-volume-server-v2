import argparse
import asyncio
from enum import Enum
import json
from pathlib import Path
from re import L
from typing import Any, Coroutine, Literal, Optional, Protocol, Type, TypedDict, Union
from attr import dataclass

from cellstar_db.file_system.db import FileSystemVolumeServerDB
from cellstar_db.models import Metadata
from cellstar_query.helper_methods.create_in_memory_zip import create_in_memory_zip
# from cellstar_query.json_numpy_response import _NumpyJsonEncoder, JSONNumpyResponse
# from fastapi import Query
from cellstar_query.requests import VolumeRequestBox, VolumeRequestDataKind, VolumeRequestInfo

from cellstar_query.core.service import VolumeServerService
from cellstar_query.query import get_geometric_segmentation_query, get_list_entries_keyword_query, get_list_entries_query, get_meshes_bcif_query, get_meshes_query, get_metadata_query, get_segmentation_box_query, get_segmentation_cell_query, get_volume_box_query, get_volume_cell_query, get_volume_info_query
from cellstar_query.serialization.json_numpy_response import _NumpyJsonEncoder

# VOLUME SERVER AND DB

DEFAULT_MAX_POINTS = 1000000000000

class Arguments(TypedDict):
    required: list[str]
    optional: list[str]

class QueryTypes(str, Enum):
    volume_box = "volume-box"
    segmentation_box = "segmentation-box"
    volume_cell = "volume-cell"
    segmentation_cell = "segmentation-cell"
    # mesh = "mesh"
    mesh_bcif = "mesh-bcif"
    geometric_segmentation = "geometric-segmentation"
    metadata = "metadata"
    annotations = "annotations"
    volume_info = "volume-info"
    list_entries = "list-entries"
    list_entries_keyword = "list-entries-keyword"
    composite = "composite"

    @staticmethod
    def values():
        # provide a meaningful named getter
        return QueryTypes._value2member_map_

class JsonQueryParams(TypedDict):
    subquery_types: list[str]
    args: dict

@dataclass
class BaseQuery:
    name: QueryTypes # can be Enum
    arguments: Optional[Arguments] = None

@dataclass(kw_only=True)
class EntryDataRequiredQuery(BaseQuery):
    pass

@dataclass
class DataQuery(EntryDataRequiredQuery):
    # time arg
    pass

@dataclass
class VolumetricDataQuery(DataQuery):
    # max points arg
    isSegmentation: bool # => segmentation-id arg; no channel-id arg
    isBox: bool # => box-coords arg

@dataclass
class MeshDataQuery(DataQuery):
    # segment-id and detail-lvl args
    # segmentation-id arg
    pass

@dataclass
class GeometricSegmentationQuery(DataQuery):
    # segmentation-id arg
    pass

@dataclass
class EntryInfoQuery(EntryDataRequiredQuery):
    # for metadata, annotations, volume info
    pass

@dataclass(kw_only=True)
class GlobalInfoQuery(BaseQuery):
    pass

@dataclass
class ListEntriesQuery(GlobalInfoQuery):
    keywords: bool = False

# need composite query with subqueries
@dataclass(kw_only=True)
class CompositeQuery(BaseQuery):
    # subqueries: list[BaseQuery]
    pass

QUERY_TYPES: list[BaseQuery] = [
    VolumetricDataQuery(name=QueryTypes.volume_box.value, isSegmentation=False, isBox=True),
    VolumetricDataQuery(name=QueryTypes.segmentation_box.value, isSegmentation=True, isBox=True),
    VolumetricDataQuery(name=QueryTypes.volume_cell.value, isSegmentation=False, isBox=False),
    VolumetricDataQuery(name=QueryTypes.segmentation_cell.value, isSegmentation=True, isBox=False),
    MeshDataQuery(name=QueryTypes.mesh_bcif.value),
    GeometricSegmentationQuery(name=QueryTypes.geometric_segmentation.value),
    EntryInfoQuery(name=QueryTypes.metadata.value),
    EntryInfoQuery(name=QueryTypes.annotations.value),
    EntryInfoQuery(name=QueryTypes.volume_info.value),
    ListEntriesQuery(name=QueryTypes.list_entries.value),
    ListEntriesQuery(name=QueryTypes.list_entries_keyword.value, keywords=True),
    CompositeQuery(name=QueryTypes.composite.value)
]

COMPOSITE_QUERY_TYPES = [QueryTypes.composite]
QUERY_TYPES_WITH_JSON_RESPONSE = [QueryTypes.annotations, QueryTypes.metadata, QueryTypes.list_entries, QueryTypes.list_entries_keyword, QueryTypes.geometric_segmentation]

@dataclass
# NOTE: for now just for volume + segmentation response
class CompositeQueryTaskResponse:
    # e.g. [('volume.bcif', volume_bcif_bytes),
    #         ('segmentation.bcif', segmentation_bcif_bytes)]
    response: list[tuple[str, Union[bytes, dict]]]

@dataclass
class QueryResponse:
    # NOTE: list[tuple[str, bytes]] - list of tuples where str = segment_id, bytes - bcif
    response: Union[bytes, list[tuple[str, bytes]], str, CompositeQueryTaskResponse]
    type: str

class QuerySpecificParams(TypedDict):
    data_type: Optional[Literal['volume', 'segmentation', 'geometric-segmentation']]
    mesh_query_type: Optional[Literal[QueryTypes.mesh_bcif]]
    entry_info_query_type: Optional[Literal[QueryTypes.metadata, QueryTypes.volume_info, QueryTypes.annotations]]
    global_info_query_type: Optional[Literal[QueryTypes.list_entries, QueryTypes.list_entries_keyword]]

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
            self.segmentation_id = args.segmentation_id
        elif self.data_type == 'volume':
            self.channel_id = args.channel_id

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
                segmentation_id=self.segmentation_id,
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
                segmentation=self.segmentation_id,
                max_points=self.max_points
            )
        
        return QueryResponse(response=response, type=self.query_type)

class MeshDataQueryTask(DataQueryTask):
    def __init__(self, params: QueryTaskParams):
        args, volume_server, query_specific_params = params.values()
        super().__init__(params)
        self.mesh_query_type = query_specific_params['mesh_query_type']
        # self.segment_id = args.segment_id
        self.detail_lvl = args.detail_lvl
        self.segmentation_id = args.segmentation_id
    async def execute(self):
        if self.mesh_query_type == QueryTypes.mesh_bcif:
            # aggregate responses
            # PLAN: get all mesh segment_ids
            # TODO: get all mesh segment_ids
            # from metadata?
            metadata_response = await get_metadata_query(volume_server=self.volume_server, source=self.source_db, id=self.entry_id)
            mr: Metadata = metadata_response['grid']
            # TODO: get all segment ids from segmentation metadata
            # mesh_timeframes
            segment_ids = list(mr['segmentation_meshes']['segmentation_metadata'][self.segmentation_id]['mesh_timeframes'][str(self.time)]['segment_ids'].keys())
            # 2. do get_meshes_bcif_query in a loop
            response = []
            for segment_id in segment_ids:
                r = await get_meshes_bcif_query(
                    volume_server=self.volume_server,
                    segmentation_id=self.segmentation_id,
                    source=self.source_db,
                    id=self.entry_id,
                    time=self.time,
                    segment_id=segment_id,
                    detail_lvl=self.detail_lvl
                )
                response.append((segment_id, r))
            # 3. change Query
        return QueryResponse(response=response, type=self.query_type)

class GeometricSegmentationQueryTask(DataQueryTask):
    def __init__(self, params: QueryTaskParams):
        args, volume_server, query_specific_params = params.values()
        super().__init__(params)
        self.segmentation_id = args.segmentation_id
    async def execute(self):
        response = await get_geometric_segmentation_query(
                volume_server=self.volume_server,
                segmentation_id=self.segmentation_id,
                source=self.source_db,
                id=self.entry_id,
                time=self.time
            )
        return QueryResponse(response=response, type=self.query_type)


class EntryInfoQueryTask(EntryDataRequiredQueryTask):
    def __init__(self, params: QueryTaskParams):
        args, volume_server, query_specific_params = params.values()
        super().__init__(params)
        self.entry_info_query_type = query_specific_params['entry_info_query_type']
    async def execute(self):
        if self.entry_info_query_type == QueryTypes.metadata:
            metadata_response = await get_metadata_query(volume_server=self.volume_server, source=self.source_db, id=self.entry_id)
            response = metadata_response['grid']
        elif self.entry_info_query_type == QueryTypes.volume_info:
            response = await get_volume_info_query(volume_server=self.volume_server, source=self.source_db, id=self.entry_id)
        elif self.entry_info_query_type == QueryTypes.annotations:
            metadata_response = await get_metadata_query(volume_server=self.volume_server, source=self.source_db, id=self.entry_id)
            response = metadata_response['annotation']

        return QueryResponse(response=response, type=self.query_type)

class GlobalInfoQueryTask(QueryTask):
    def __init__(self, params: QueryTaskParams):
        args, volume_server, query_specific_params = params.values()
        super().__init__(params)
        self.global_info_query_type = query_specific_params['global_info_query_type']
        self.limit = args.limit
        if self.global_info_query_type == QueryTypes.list_entries_keyword:
            self.keyword = args.keyword
    async def execute(self):
        if self.global_info_query_type == QueryTypes.list_entries:
            response = await get_list_entries_query(volume_server=self.volume_server, limit=self.limit)
        elif self.global_info_query_type == QueryTypes.list_entries_keyword:
            response = await get_list_entries_keyword_query(volume_server=self.volume_server, limit=self.limit, keyword=self.keyword)

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
            # TODO: how extension is determined for volume and segmentation?
            if isinstance(response.response, bytes):
                extension = '.bcif'
            elif isinstance(response.response, dict):
                extension = '.json'
            # elif isinstance(response.response, list[bytes]):

            composite_response.append(
                (f'{response.type}{extension}', response.response)
            )

        composite_response.append(
            ('query.json', self.json_with_query_params)
        )

        return CompositeQueryTaskResponse(response=composite_response)

def _get_arguments_as_list(argparse_args_group) -> list[str]:
    arg_names = []
    d = vars(argparse_args_group)
    group_actions = d['_group_actions']
    for action in group_actions:
        arg_name = action.dest
        arg_names.append(arg_name)
    
    return arg_names


def _add_arguments(parser, query: BaseQuery):
    required_query_args = parser.add_argument_group('Required query named arguments')
    optional_query_args = parser.add_argument_group('Optional query named arguments')
    if isinstance(query, EntryDataRequiredQuery):
        required_query_args.add_argument('--entry-id', type=str, required=True, help='Entry ID in the database (e.g. "emd-1832")')
        required_query_args.add_argument('--source-db', type=str, required=True, help='Source database (e.g. "emdb")')

    if isinstance(query, DataQuery):
        required_query_args.add_argument('--time', required=True, type=int, help='Timeframe (e.g. 0)', default=0)
        # required_query_args.add_argument('--channel-id', required=True, type=int, help='Channel ID (e.g 0)', default=0)
    
    if isinstance(query, VolumetricDataQuery):
        optional_query_args.add_argument('--max-points', type=int, default=DEFAULT_MAX_POINTS, help='Maximum number of points')

        if query.isSegmentation:
            required_query_args.add_argument('--segmentation-id', type=str, required=True, help='Segmentation ID (e.g. 0)', default='0')
        else:
            required_query_args.add_argument('--channel-id', required=True, type=str, help='Channel ID (e.g 0)', default='0')

        if query.isBox:
            required_query_args.add_argument('--box-coords', nargs=6, required=True, type=float, help='XYZ coordinates of bottom left and top right of query box in Angstroms')


    if isinstance(query, MeshDataQuery):
        required_query_args.add_argument('--segmentation-id', type=str, required=True, help='Segmentation ID (e.g. 0)', default='0')
        # required_query_args.add_argument('--segment-id', required=True, type=int, help='Segment ID of mesh (e.g 1)')
        required_query_args.add_argument('--detail-lvl', required=True, type=int, help='Required detail level (1 is highest resolution)', default=1)
    
    if isinstance(query, GeometricSegmentationQuery):
        required_query_args.add_argument('--segmentation-id', type=str, required=True, help='Segmentation ID (e.g. 0)', default='0')

    if isinstance(query, ListEntriesQuery):
        required_query_args.add_argument('--limit', type=int, default=100, required=True, help='Maximum number of entries')

        if query.keywords:
            required_query_args.add_argument('--keyword', type=str, required=True, help='Keyword')
    
    if isinstance(query, CompositeQuery):
        required_query_args.add_argument('--json-params-path', required=True, type=str, help='Path to .json file with parameters for composite query')


    required_args = _get_arguments_as_list(argparse_args_group=required_query_args)
    optional_args = _get_arguments_as_list(argparse_args_group=optional_query_args)
    arguments = Arguments(
        required=required_args,
        optional=optional_args
    )
    query.arguments = arguments

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
    # TODO: add here case for list[bytes]
    # s
    if isinstance(r, bytes) or isinstance (r, list) or isinstance(response, CompositeQueryTaskResponse):
        file_writing_mode = 'wb'
    elif isinstance(r, str) or isinstance(r, list) or isinstance(r, dict):
        file_writing_mode = 'w'
    else:
        raise Exception('response type is not supported')
    
    with open(str(Path(args.out).resolve()), file_writing_mode) as f:
        if args.query_type in QUERY_TYPES_WITH_JSON_RESPONSE:
            json.dump(r, f, indent=4)
        elif args.query_type in COMPOSITE_QUERY_TYPES:
            zip_data = create_in_memory_zip(r)
            f.write(zip_data)
        elif args.query_type == QueryTypes.mesh_bcif:
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
    if args.query_type == QueryTypes.volume_box:
        print('volume box query')
        query_params['custom_params'] = {
            'data_type': 'volume'
        }
        task = BoxDataQueryTask(params=query_params)
        
    elif args.query_type == QueryTypes.segmentation_box:
        print('segmentation box query')
        # query
        query_params['custom_params'] = {
            'data_type': 'segmentation'
        }
        task = BoxDataQueryTask(params=query_params)
    
    elif args.query_type == QueryTypes.segmentation_cell:
        print('segmentation cell query')
        query_params['custom_params'] = {
            'data_type': 'segmentation'
        }
        task = CellDataQueryTask(params=query_params)

    elif args.query_type == QueryTypes.volume_cell:
        print('volume cell query')
        query_params['custom_params'] = {
            'data_type': 'volume'
        }
        task = CellDataQueryTask(params=query_params)

    elif args.query_type in [QueryTypes.mesh_bcif]:
        print(f'{args.query_type}')
        query_params['custom_params'] = {
            'mesh_query_type': args.query_type
        }
        task = MeshDataQueryTask(params=query_params)

    elif args.query_type == QueryTypes.geometric_segmentation:
        print(f'{args.query_type}')
        query_params['custom_params'] = {
            'data_type': 'geometric-segmentation'
        }
        task = GeometricSegmentationQueryTask(params=query_params)

    elif args.query_type in [QueryTypes.metadata, QueryTypes.volume_info, QueryTypes.annotations]:
        print(f'{args.query_type} query')
        query_params['custom_params'] = {
            'entry_info_query_type': args.query_type
        }
        task = EntryInfoQueryTask(params=query_params)

    elif args.query_type in [QueryTypes.list_entries, QueryTypes.list_entries_keyword]:
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
        raw_json: JsonQueryParams = json.load(f)
        # print(d)

        # create argparse args
        for arg, arg_value in raw_json['args'].items():
            argparse_args_dict[f'{arg}'] = arg_value

        # print('args namespace')
        # print(args)

        subquery_types = raw_json['subquery_types']

        # validate
        for subquery_type in subquery_types:
            assert subquery_type in QueryTypes.values(), f'Subquery type {subquery_type} is not supported'

        # TODO: validate args namespace
        # PLAN:
        # find that subquery instance in QUERY_TYPES (filter by name)
            query_objects = list(filter(lambda query_type: query_type.name == subquery_type, QUERY_TYPES))
            assert len(query_objects) == 1
            query_object: BaseQuery = query_objects[0]
            for arg in query_object.arguments['required']:
                assert (arg in args), f'Argument {arg} is missing from JSON, but is required for {subquery_type} subquery'

    return raw_json, args, subquery_types

async def _query(args):
    if args.query_type not in COMPOSITE_QUERY_TYPES:
        task = _create_task(args)
    else:
        raw_json, argparse_args, subquery_types = _parse_json_with_query_params(Path(args.json_params_path))
        # print(args)
        argparse_args.db_path = args.db_path
        argparse_args.out = args.out
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