import json

from vs_toolkit.tests.common import get_unique_cvsx_file_path, get_unique_json_query_params_path, produce_cvsx

output_file_path = get_unique_cvsx_file_path()
json_with_query_params_path = get_unique_json_query_params_path()

def _create_json_with_query_params():
    # the only unique part
    d = {
        "entry_id": "empiar-10070",
        "source_db": "empiar",
        "max_points": 100000,
        "detail_lvl": 9,
    }

    # should be unique as well
    with json_with_query_params_path.open("w") as fp:
        json.dump(d, fp, indent=4)


def test_composite_query():
    _create_json_with_query_params()
    produce_cvsx(output_file_path, json_with_query_params_path)
