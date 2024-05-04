# Query App

Query App (CVSX)

# Usage
To run the query app tool and produce the static files suitable for visualization at the frontend:
1. Build the database using preprocessor **(TODO LINK TO README FOR PREPROCESSOR)**

2. From repository root (`cellstar-volume-server-v2` by default) run:
    ```
    python --db_path PATH_TO_DB --out OUTPUT_FILE --json-params-path PATH_TO_JSON_WITH_PARAMETERS
    ```
    Arguments description:
    - `--db_path` - path to the database built using preprocessor
    - `--out` - path to the output file where the results of the query will be stored

    - `--json-params-path` Path to `.json` file with query parameters (see table below)

    | Parameter         | Description                                                                                                             | Kind      | Type                                        | Default                          |
    |-------------------|-------------------------------------------------------------------------------------------------------------------------|-----------|---------------------------------------------|----------------------------------|
    | entry_id          | ID of entry in internal database (e.g. emd-1832)                                                                        | mandatory | string                                      | N/A                              |
    | source_db         | Source database (e.g. emdb)                                                                                             | mandatory | string                                      | N/A                              |
    | segmentation_kind | Kind of segmentation (e.g. lattice)                                                                                     | optional  | 'mesh', 'lattice', 'geometric-segmentation' | all segmentation kinds           |
    | time              | Timeframe index                                                                                                         | optional  | integer                                     | all available time frame indices |
    | channel_id        | Volume channel ID                                                                                                       | optional  | string                                      | all available channel IDs        |
    | segmentation_id   | Segmentation ID                                                                                                         | optional  | string                                      | all available segmentation IDs   |
    | max_points        | Maximum number of points for volume and/or lattice segmentation. Used to determine the most suitable downsampling level | optional  | integer                                     | 1000000000000                    |


    Example:
        ```json
        {
            "subquery_types": [
                "subquery-type-1",
                "subquery-type-2",
                ...
            ],
            "args": {
                "arg1": "arg-value-1",
                "arg2": "arg-value-2",
                ...
            }
        }
        ```
        Example:
        ```json
        {
            "subquery_types": [
                "volume-cell",
                "segmentation-cell",
                "annotations"
                "metadata"
            ],
            "args": {
                "entry_id": "emd-1832",
                "source_db": "emdb",
                "time": 0,
                "channel_id": "0",
                "segmentation_id": "0"
            }
        }
        ```
        Then use the following command:
        ```
        python query_app.py --db_path temp/test_db --out results.cvsx composite --json-params-path json_with_query_params.json
        ```
        
        This will produce `results.cvsx` containing the results of `volume-cell`, `segmentation-cell`, `annotations`, and `metadata` queries

---
**NOTE**

Frontend visualization support is provided mainly for results of composite queries (CVSX files)
---

# Example of usage
```
python query_app.py --db_path temp/test_db --out segm.bcif segmentation-cell --entry-id emd-1832 --source-db emdb --time 0 --channel-id 0 --segmentation-id 0
```
This will produce `segm.bcif` file with the results of `segmentation-cell` query for `emd-1832` entry (with `time`, `channel-id`, and `segmentation-id` parameters equal to 0) from the database located in `temp/test_db`