from pathlib import Path
import subprocess
import pytest

from query_app.tests.constants import QUERY_APP_PATH

# run app with arguments
# assert that output file exists 

OUTPUT_FILE_PATH = Path('query_app/tests/test_output/mesh.json')

def test_mesh_query():
    commands_lst = [
        "python",
        str(QUERY_APP_PATH.resolve()),
        "--db_path", "preprocessor/temp/test_db",
        "--out", str(OUTPUT_FILE_PATH.resolve()),
        "mesh",
        "--entry-id", "empiar-10070",
        "--source-db", "empiar",
        "--time", "0",
        "--segmentation-id", "0",
        "--segment-id", "1", "--detail-lvl", "1"
    ]
    subprocess.run(
        commands_lst
    )

    assert OUTPUT_FILE_PATH.exists()
    assert OUTPUT_FILE_PATH.is_file()

    # delete output file
    OUTPUT_FILE_PATH.unlink()