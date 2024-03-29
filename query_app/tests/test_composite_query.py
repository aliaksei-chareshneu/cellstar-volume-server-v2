import json
from pathlib import Path
import subprocess
import pytest

from query_app.tests.constants import QUERY_APP_PATH

# run app with arguments
# assert that output file exists 

OUTPUT_FILE_PATH = Path('query_app/tests/test_output/results.zip')
JSON_WITH_QUERY_PARAMS_PATH = Path('query_app/tests/test_output/json_query_params.json')

def _create_json_with_query_params():
    d = {
        "subquery_types": [
            "volume-cell",
            "segmentation-cell",
            "annotations"
        ],
        "args": {
            "entry_id": "emd-1832",
            "source_db": "emdb",
            "time": 0,
            "channel_id": "0",
            "segmentation_id": "0"
        }
    }
    
    with (JSON_WITH_QUERY_PARAMS_PATH).open("w") as fp:
        json.dump(d, fp, indent=4)

def test_composite_query():
    _create_json_with_query_params()
    
    commands_lst = [
        "python",
        str(QUERY_APP_PATH.resolve()),
        "--db_path", "preprocessor/temp/test_db",
        "--out", str(OUTPUT_FILE_PATH.resolve()),
        "composite",
        "--json-params-path", str(JSON_WITH_QUERY_PARAMS_PATH.resolve())
    ]
    subprocess.run(
        commands_lst
    )

    # TODO: read it and assert that there are correct content (just filenames)
    assert OUTPUT_FILE_PATH.exists()
    assert OUTPUT_FILE_PATH.is_file()

    # delete output file
    OUTPUT_FILE_PATH.unlink()

    JSON_WITH_QUERY_PARAMS_PATH.unlink()