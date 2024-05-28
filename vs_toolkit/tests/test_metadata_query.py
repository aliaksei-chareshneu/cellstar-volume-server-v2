import json
from pathlib import Path
import subprocess
from cellstar_query.query import get_metadata_query
import pytest

from vs_toolkit.tests.constants import QUERY_APP_PATH

# run app with arguments
# assert that output file exists 

# OUTPUT_FILE_PATH = Path('query_app/tests/test_output/geometric_segmentation.json')
METADATA_OUTPUT_FILE_PATH = Path('query_app/tests/test_output/metadata.json')

# @pytest.mark.asyncio
def test_metadata_query():
    metadata_commands_lst = [
        "python",
        str(QUERY_APP_PATH.resolve()),
        "--db_path", "preprocessor/temp/test_db",
        "--out", str(METADATA_OUTPUT_FILE_PATH.resolve()),
        "metadata",
        "--entry-id", "emd-1832",
        "--source-db", "emdb",     
    ]

    subprocess.run(
        metadata_commands_lst
    )


    assert METADATA_OUTPUT_FILE_PATH.exists()
    assert METADATA_OUTPUT_FILE_PATH.is_file()

    # delete output file
    METADATA_OUTPUT_FILE_PATH.unlink()