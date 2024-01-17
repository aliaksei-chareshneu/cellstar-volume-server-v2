from pathlib import Path
import subprocess
import pytest

# run app with arguments
# assert that output file exists 

QUERY_APP_PATH = Path('query_app/query_app.py')

# @pytest.mark.asyncio
def test_volume_cell_query():
    commands_lst = [
        "python",
        str(QUERY_APP_PATH.resolve()),
        "--db_path", "preprocessor/temp/test_db",
        "--out", "volume.bcif",
        "volume-cell",
        "--entry-id", "emd-1832",
        "--source-db", "emdb",
        "--time", "0",
        "--channel-id", "0",
    ]
    subprocess.run(
        commands_lst
    )