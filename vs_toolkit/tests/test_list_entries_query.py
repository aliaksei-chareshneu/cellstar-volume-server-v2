import subprocess
from pathlib import Path

from vs_toolkit.tests.constants import QUERY_APP_PATH

# run app with arguments
# assert that output file exists

# OUTPUT_FILE_PATH = Path('query_app/tests/test_output/geometric_segmentation.json')
OUTPUT_FILE_PATH = Path("query_app/tests/test_output/list_entries.json")


# @pytest.mark.asyncio
def test_list_entries_query():
    commands_lst = [
        "python",
        str(QUERY_APP_PATH.resolve()),
        "--db_path",
        "preprocessor/temp/test_db",
        "--out",
        str(OUTPUT_FILE_PATH.resolve()),
        "list-entries",
        "--limit",
        "100",
    ]

    subprocess.run(commands_lst)

    assert OUTPUT_FILE_PATH.exists()
    assert OUTPUT_FILE_PATH.is_file()

    # delete output file
    OUTPUT_FILE_PATH.unlink()
