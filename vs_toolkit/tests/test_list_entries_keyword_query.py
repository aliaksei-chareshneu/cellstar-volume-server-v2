import subprocess
from pathlib import Path

from vs_toolkit.tests.constants import QUERY_APP_PATH

# run app with arguments
# assert that output file exists

OUTPUT_FILE_PATH = Path("query_app/tests/test_output/list_entries_keyword.json")


# @pytest.mark.asyncio
def test_list_entries_keyword_query():
    commands_lst = [
        "python",
        str(QUERY_APP_PATH.resolve()),
        "--db_path",
        "preprocessor/temp/test_db",
        "--out",
        str(OUTPUT_FILE_PATH.resolve()),
        "list-entries-keyword",
        "--limit",
        "100",
        "--keyword",
        "emd",
    ]

    subprocess.run(commands_lst)

    assert OUTPUT_FILE_PATH.exists()
    assert OUTPUT_FILE_PATH.is_file()

    # delete output file
    OUTPUT_FILE_PATH.unlink()
