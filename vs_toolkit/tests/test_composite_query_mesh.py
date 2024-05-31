import json
import subprocess
from pathlib import Path

from vs_toolkit.tests.constants import VS_TOOLKIT_PATH

# run app with arguments
# assert that output file exists

OUTPUT_FILE_PATH = Path("vs_toolkit/tests/test_output/results.zip")
JSON_WITH_QUERY_PARAMS_PATH = Path("vs_toolkit/tests/test_output/json_query_params.json")


def _create_json_with_query_params():
    d = {
        "entry_id": "empiar-10070",
        "source_db": "empiar",
        "max_points": 100000,
        "detail_lvl": 9,
    }

    with (JSON_WITH_QUERY_PARAMS_PATH).open("w") as fp:
        json.dump(d, fp, indent=4)


def test_composite_query():
    _create_json_with_query_params()

    commands_lst = [
        "python",
        str(VS_TOOLKIT_PATH.resolve()),
        "--db_path",
        str(DB_PATH_FOR_VS_TOOLKIT_TESTS.resolve()),
        "--out",
        str(OUTPUT_FILE_PATH.resolve()),
        "--json-params-path",
        str(JSON_WITH_QUERY_PARAMS_PATH.resolve()),
    ]
    subprocess.run(commands_lst)

    # TODO: read it and assert that there are correct content (just filenames)
    assert OUTPUT_FILE_PATH.exists()
    assert OUTPUT_FILE_PATH.is_file()

    # delete output file
    OUTPUT_FILE_PATH.unlink()

    JSON_WITH_QUERY_PARAMS_PATH.unlink()
