from pathlib import Path
import subprocess
import pytest

from vs_toolkit.tests.constants import QUERY_APP_PATH

# run app with arguments
# assert that output file exists 

OUTPUT_FILE_PATH = Path('query_app/tests/test_output/volume.bcif')

def test_volume_box_query():
    commands_lst = [
        "python",
        str(QUERY_APP_PATH.resolve()),
        "--db_path", "preprocessor/temp/test_db",
        "--out", str(OUTPUT_FILE_PATH.resolve()),
        "volume-box",
        "--entry-id", "emd-1832",
        "--source-db", "emdb",
        "--time", "0",
        "--channel-id", "0",
        "--box-coords", "1.0", "1.0", "1.0", "100.0", "100.0", "100.0"
    ]
    subprocess.run(
        commands_lst
    )

    assert OUTPUT_FILE_PATH.exists()
    assert OUTPUT_FILE_PATH.is_file()

    # delete output file
    OUTPUT_FILE_PATH.unlink()