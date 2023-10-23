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
from pathlib import Path

from cellstar_db.file_system.db import FileSystemVolumeServerDB
from fastapi import Query
from server.app.api.requests import VolumeRequestBox, VolumeRequestDataKind, VolumeRequestInfo

from server.app.core.service import VolumeServerService

# VOLUME SERVER AND DB
# TODO: make db path a CLI arg?

async def main():
    # initialize dependencies
    # PARSING
    main_parser = argparse.ArgumentParser(add_help=False)
    
    common_subparsers = main_parser.add_subparsers(dest='query_type', help='query type')

    # COMMON ARGUMENTS
    main_parser.add_argument('--db_path', type=str, required=True)
    main_parser.add_argument('--entry-id', type=str, required=True)
    main_parser.add_argument('--source-db', type=str, required=True)
    main_parser.add_argument('--out', type=str, required=True)

    box_parser = common_subparsers.add_parser('volume-box')
    box_parser.add_argument('--time', required=True, type=int)
    box_parser.add_argument('--channel-id', required=True, type=int)
    box_parser.add_argument('--box-coords', nargs=6, required=True, type=float)
    # TODO: fix default
    box_parser.add_argument('--max-points', type=int, default=10000000)

    args = main_parser.parse_args()

    db = FileSystemVolumeServerDB(folder=Path(args.db_path))

    # initialize server
    VOLUME_SERVER = VolumeServerService(db)

    if args.query_type == 'volume-box':
        print('volume box query')
        # query
        a1, a2, a3, b1, b2, b3 = args.box_coords
        response = await VOLUME_SERVER.get_volume_data(
            req=VolumeRequestInfo(
                source=args.source_db, structure_id=args.entry_id, channel_id=args.channel_id,
                time=args.time, max_points=args.max_points, data_kind=VolumeRequestDataKind.volume
            ),
            req_box=VolumeRequestBox(bottom_left=(a1, a2, a3), top_right=(b1, b2, b3)),
        )

        # write to file
        with open(str((Path(args.out)).resolve()), 'wb') as f: 
            f.write(response)

    elif args.query_type == 'volume-cell':
        print('volume cell query')

    # print(args)

if __name__ == '__main__':
    asyncio.run(main())


# python local_api_query.py --db-path  --entry-id emd-1832 --source-db emdb --out local_query.bcif volume-box --time 0 --channel-id 0 --box-coords 1 1 1 10 10 10