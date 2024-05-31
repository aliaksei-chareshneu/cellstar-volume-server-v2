import json
import subprocess
from pathlib import Path

import pytest

from vs_toolkit.tests.constants import QUERY_APP_PATH

# run app with arguments
# assert that output file exists

OUTPUT_FILE_PATH = Path("query_app/tests/test_output/geometric_segmentation.json")
METADATA_OUTPUT_FILE_PATH = Path(
    "query_app/tests/test_output/geometric_segmentation_metadata.json"
)


@pytest.mark.asyncio
async def test_geometric_segmentation_query():
    metadata_commands_lst = [
        "python",
        str(QUERY_APP_PATH.resolve()),
        "--db_path",
        "preprocessor/temp/test_db",
        "--out",
        str(METADATA_OUTPUT_FILE_PATH.resolve()),
        "metadata",
        "--entry-id",
        "pdbe-1.rec-geometric_segmentation",
        "--source-db",
        "pdbe",
        # "--time", "0",
        # "--channel-id", "0",
        # "--segment-id", "1", "--detail-lvl", "1"
    ]

    subprocess.run(metadata_commands_lst)

    with open(METADATA_OUTPUT_FILE_PATH.resolve(), "r", encoding="utf-8") as f:
        # reads into dict
        read_json_of_metadata = json.load(f)

    segmentation_id = read_json_of_metadata.get("geometric_segmentation").get(
        "segmentation_ids"
    )[0]
    time_info_dict: dict = read_json_of_metadata.get("geometric_segmentation").get(
        "time_info"
    )
    time_info = time_info_dict[segmentation_id]
    time = time_info.get("start")

    commands_lst = [
        "python",
        str(QUERY_APP_PATH.resolve()),
        "--db_path",
        "preprocessor/temp/test_db",
        "--out",
        str(OUTPUT_FILE_PATH.resolve()),
        "geometric-segmentation",
        "--entry-id",
        "pdbe-1.rec-geometric_segmentation",
        "--source-db",
        "pdbe",
        "--time",
        str(time),
        # TODO: get segmentation id from metadata query
        "--segmentation-id",
        str(segmentation_id),
    ]
    subprocess.run(commands_lst)

    assert OUTPUT_FILE_PATH.exists()
    assert OUTPUT_FILE_PATH.is_file()

    # delete output file
    OUTPUT_FILE_PATH.unlink()
    METADATA_OUTPUT_FILE_PATH.unlink()
