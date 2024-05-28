import json
from pathlib import Path
import subprocess
from cellstar_query.query import get_metadata_query
import pytest

from vs_toolkit.tests.constants import QUERY_APP_PATH

# run app with arguments
# assert that output file exists 

OUTPUT_FILE_PATH = Path('query_app/tests/test_output/annotations.json')

# @pytest.mark.asyncio
def test_annotations_query():
    commands_lst = [
        "python",
        str(QUERY_APP_PATH.resolve()),
        "--db_path", "preprocessor/temp/test_db",
        "--out", str(OUTPUT_FILE_PATH.resolve()),
        "annotations",
        "--entry-id", "emd-1832",
        "--source-db", "emdb",     
    ]

    subprocess.run(
        commands_lst
    )


    assert OUTPUT_FILE_PATH.exists()
    assert OUTPUT_FILE_PATH.is_file()

    # delete output file
    OUTPUT_FILE_PATH.unlink()