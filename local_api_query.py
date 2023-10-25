# import argparse


# parser = argparse.ArgumentParser(
#     prog='PROG', 
#     epilog="See '<command> --help' to read about a specific sub-command."
# )

# base_parser = argparse.ArgumentParser(add_help=False)
# # NOTE: common args, don't need them
# # base_parser.add_argument("--sp", required=True, help="source")

# subparsers = parser.add_subparsers(dest='kind', help='Sub-commands')

# box_and_cell_parser = subparsers.add_parser('box', help='box query', parents=[base_parser])
# box_and_cell_parser.add_argument('--type', required=True, help='volume or segmentation', choices=['volume', 'segmentation'])
# box_and_cell_parser.add_argument('--time', required=True, type=float)
# box_and_cell_parser.add_argument('--channel_id', required=True, type=int)
# # box_parser = box_and_cell_parser.add_subparsers('')
# # NOTE: 6 consecutive numbers
# # box_parser.add_argument('--box_coords', nargs=6, required=True)

# # TODO: if segmentation - should add lattice id
# # segmentation_box_parser = box_parser.add_subparsers(dest=)


# cell_parser = subparsers.add_parser('cell', help='cell query', parents=[base_parser])
# # box_parser.add_argument('--type', required=True, help='volume or segmentation', choices=['volume', 'segmentation'])
# # box_parser.add_argument('--time', required=True, type=float)
# # box_parser.add_argument('--channel_id', required=True, type=int)
# # # NOTE: 6 consecutive numbers
# # box_parser.add_argument('--box_coords', nargs=6, required=True)

# # TODO: if segmentation - should add lattice id


# args = parser.parse_args()

# if args.kind == 'box':
#     pass
# elif args.kind == 'cell':
#     pass

# print(args)

# import argparse

# parent_parser = argparse.ArgumentParser(add_help=False)
# parent_parser.add_argument('--user', '-u',
#                     help='username')
# parent_parser.add_argument('--debug', default=False, required=False,
#                         action='store_true', dest="debug", help='debug flag')
# main_parser = argparse.ArgumentParser()
# service_subparsers = main_parser.add_subparsers(title="service",
#                     dest="service_command")
# service_parser = service_subparsers.add_parser("first", help="first",
#                     parents=[parent_parser])
# action_subparser = service_parser.add_subparsers(title="action",
#                     dest="action_command")
# action_parser = action_subparser.add_parser("second", help="second",
#                     parents=[parent_parser])

# args = main_parser.parse_args()
# print(args)

# NOTE: create parent parser with all common arguments
# Then create child parsers

# import argparse

# main_parser = argparse.ArgumentParser(add_help=False)

# common_subparsers = main_parser.add_subparsers()

# box_and_cell_parser = common_subparsers.add_parser('box_and_cell')
# box_and_cell_parser.add_argument('--type', required=True, help='volume or segmentation', choices=['volume', 'segmentation'])
# box_and_cell_parser.add_argument('--time', required=True, type=float)
# box_and_cell_parser.add_argument('--channel_id', required=True, type=int)

# # NOTE: create child parsers
# # https://docs.python.org/3.8/library/argparse.html#parents
# box_parser = argparse.ArgumentParser(parents=[box_and_cell_parser])
# box_parser.add_argument('--box_coords', nargs=6, required=True)

# cell_parser = argparse.ArgumentParser(parents=[box_and_cell_parser])

# segmentation_box_parser = argparse.ArgumentParser(parents=[box_parser])
# segmentation_box_parser.add_argument('--lattice_id', required=True)

# args = main_parser.parse_args()
# print(args)

# https://docs.python.org/3.8/library/argparse.html#sub-commands

import argparse
import asyncio
import json
from pathlib import Path

from cellstar_db.file_system.db import FileSystemVolumeServerDB
from cellstar_query.json_numpy_response import _NumpyJsonEncoder, JSONNumpyResponse
from fastapi import Query
from cellstar_query.requests import VolumeRequestBox, VolumeRequestDataKind, VolumeRequestInfo

from cellstar_query.core.service import VolumeServerService
from cellstar_query.query import get_list_entries_keywords_query, get_list_entries_query, get_meshes_bcif_query, get_meshes_query, get_metadata_query, get_segmentation_box_query, get_segmentation_cell_query, get_volume_box_query, get_volume_cell_query, get_volume_info_query

# VOLUME SERVER AND DB

DEFAULT_MAX_POINTS = 100000000

async def _query(args):
    db = FileSystemVolumeServerDB(folder=Path(args.db_path))

    # initialize server
    VOLUME_SERVER = VolumeServerService(db)

    file_writing_mode = 'wb'

    if args.query_type == 'volume-box':
        print('volume box query')
        # query
        a1, a2, a3, b1, b2, b3 = args.box_coords
        response = await get_volume_box_query(
            volume_server=VOLUME_SERVER,
            source=args.source_db,
            id=args.entry_id,
            time=args.time,
            channel_id=args.channel_id,
            a1=a1,
            a2=a2,
            a3=a3,
            b1=b1,
            b2=b2,
            b3=b3,
            max_points=args.max_points
        )

    elif args.query_type == 'segmentation-box':
        print('segmentation box query')
        # query
        a1, a2, a3, b1, b2, b3 = args.box_coords
        response = await get_segmentation_box_query(
            volume_server=VOLUME_SERVER,
            segmentation=args.lattice_id,
            source=args.source_db,
            id=args.entry_id,
            time=args.time,
            channel_id=args.channel_id,
            a1=a1,
            a2=a2,
            a3=a3,
            b1=b1,
            b2=b2,
            b3=b3,
            max_points=args.max_points
        )
    
    elif args.query_type == 'segmentation-cell':
        print('segmentation cell query')
        response = await get_segmentation_cell_query(
            volume_server=VOLUME_SERVER,
            segmentation=args.lattice_id,
            source=args.source_db,
            id=args.entry_id,
            time=args.time,
            channel_id=args.channel_id,
            max_points=args.max_points
        )
    elif args.query_type == 'volume-cell':
        print('volume cell query')
        response = await get_volume_cell_query(
            volume_server=VOLUME_SERVER,
            source=args.source_db,
            id=args.entry_id,
            time=args.time,
            channel_id=args.channel_id,
            max_points=args.max_points
        )

    elif args.query_type == 'mesh':
        print('mesh query')
        file_writing_mode = 'w'
        response = await get_meshes_query(
            volume_server=VOLUME_SERVER,
            source=args.source_db,
            id=args.entry_id,
            time=args.time,
            channel_id=args.channel_id,
            segment_id=args.segment_id,
            detail_lvl=args.detail_lvl
        )

    elif args.query_type == 'mesh-bcif':
        print('mesh-bcif query')
        response = await get_meshes_bcif_query(
            volume_server=VOLUME_SERVER,
            source=args.source_db,
            id=args.entry_id,
            time=args.time,
            channel_id=args.channel_id,
            segment_id=args.segment_id,
            detail_lvl=args.detail_lvl
        )

    elif args.query_type == 'metadata':
        print('metadata query')
        file_writing_mode = 'w'
        response = await get_metadata_query(volume_server=VOLUME_SERVER, source=args.source_db, id=args.entry_id)
    
    elif args.query_type == 'volume-info':
        print('volume info query')
        response = await get_volume_info_query(volume_server=VOLUME_SERVER, source=args.source_db, id=args.entry_id)

    elif args.query_type == 'list-entries':
        print('list_entries query')
        file_writing_mode = 'w'
        response = await get_list_entries_query(volume_server=VOLUME_SERVER, limit=args.limit)
    
    elif args.query_type == 'list-entries-keyword':
        print('list_entries query')
        file_writing_mode = 'w'
        response = await get_list_entries_keywords_query(volume_server=VOLUME_SERVER, limit=args.limit, keyword=args.keyword)
    
    # write to file

    
    with open(str((Path(args.out)).resolve()), file_writing_mode) as f:
        if args.query_type in ['metadata', 'list-entries', 'list-entries-keyword']:
            json.dump(response, f, indent=4)
        elif args.query_type == 'mesh':
            json_dump = json.dumps(response, 
                       cls=_NumpyJsonEncoder)
            json.dump(json_dump, f, indent=4)
        else: 
            f.write(response)

async def main():
    # initialize dependencies
    # PARSING
    main_parser = argparse.ArgumentParser(add_help=False)
    
    common_subparsers = main_parser.add_subparsers(dest='query_type', help='query type')
    # COMMON ARGUMENTS
    main_parser.add_argument('--db_path', type=str, required=True)
    # main_parser.add_argument('--entry-id', type=str, required=True)
    # main_parser.add_argument('--source-db', type=str, required=True)
    main_parser.add_argument('--out', type=str, required=True)

    box_parser = common_subparsers.add_parser('volume-box')
    box_parser.add_argument('--entry-id', type=str, required=True)
    box_parser.add_argument('--source-db', type=str, required=True)
    box_parser.add_argument('--time', required=True, type=int)
    box_parser.add_argument('--channel-id', required=True, type=int)
    box_parser.add_argument('--box-coords', nargs=6, required=True, type=float)
    # TODO: fix default
    box_parser.add_argument('--max-points', type=int, default=DEFAULT_MAX_POINTS)

    # SEGMENTATION BOX
    segm_box_parser = common_subparsers.add_parser('segmentation-box')
    segm_box_parser.add_argument('--entry-id', type=str, required=True)
    segm_box_parser.add_argument('--source-db', type=str, required=True)
    segm_box_parser.add_argument('--time', required=True, type=int)
    segm_box_parser.add_argument('--channel-id', required=True, type=int)
    segm_box_parser.add_argument('--lattice-id', type=int, required=True)
    segm_box_parser.add_argument('--box-coords', nargs=6, required=True, type=float)
    # TODO: fix default
    segm_box_parser.add_argument('--max-points', type=int, default=DEFAULT_MAX_POINTS)
    
    # VOLUME CELL
    volume_cell_parser = common_subparsers.add_parser('volume-cell')
    volume_cell_parser.add_argument('--entry-id', type=str, required=True)
    volume_cell_parser.add_argument('--source-db', type=str, required=True)
    volume_cell_parser.add_argument('--time', required=True, type=int)
    volume_cell_parser.add_argument('--channel-id', required=True, type=int)
    # TODO: fix default
    volume_cell_parser.add_argument('--max-points', type=int, default=DEFAULT_MAX_POINTS)

    # SEGMENTATION CELL
    segm_cell_parser = common_subparsers.add_parser('segmentation-cell')
    segm_cell_parser.add_argument('--entry-id', type=str, required=True)
    segm_cell_parser.add_argument('--source-db', type=str, required=True)
    segm_cell_parser.add_argument('--time', required=True, type=int)
    segm_cell_parser.add_argument('--channel-id', required=True, type=int)
    segm_cell_parser.add_argument('--lattice-id', type=int, required=True)
    # TODO: fix default
    segm_cell_parser.add_argument('--max-points', type=int, default=DEFAULT_MAX_POINTS)

    # METADATA
    metadata_parser = common_subparsers.add_parser('metadata')

    # VOLUME INFO
    metadata_parser = common_subparsers.add_parser('volume-info')

    # MESHES
    meshes_parser = common_subparsers.add_parser('mesh')
    meshes_parser.add_argument('--entry-id', type=str, required=True)
    meshes_parser.add_argument('--source-db', type=str, required=True)
    meshes_parser.add_argument('--time', required=True, type=int)
    meshes_parser.add_argument('--channel-id', required=True, type=int)
    meshes_parser.add_argument('--segment-id', required=True, type=int)
    meshes_parser.add_argument('--detail-lvl', required=True, type=int)

    meshes_bcif_parser = common_subparsers.add_parser('mesh-bcif')
    meshes_bcif_parser.add_argument('--entry-id', type=str, required=True)
    meshes_bcif_parser.add_argument('--source-db', type=str, required=True)
    meshes_bcif_parser.add_argument('--time', required=True, type=int)
    meshes_bcif_parser.add_argument('--channel-id', required=True, type=int)
    meshes_bcif_parser.add_argument('--segment-id', required=True, type=int)
    meshes_bcif_parser.add_argument('--detail-lvl', required=True, type=int)
    
    list_entries_parser = common_subparsers.add_parser('list-entries')
    list_entries_parser.add_argument('--limit', type=int, default=100, required=True)

    list_entries_keyword_parser = common_subparsers.add_parser('list-entries-keyword')
    list_entries_keyword_parser.add_argument('--limit', type=int, default=100, required=True)
    list_entries_keyword_parser.add_argument('--keyword', type=str, required=True)
    
    args = main_parser.parse_args()

    await _query(args)


if __name__ == '__main__':
    asyncio.run(main())


# python local_api_query.py --out local_query1.bcif volume-cell --db_path preprocessor/temp/test_db --entry-id emd-1832 --source-db emdb --time 0 --channel-id 0 --lattice-id 0