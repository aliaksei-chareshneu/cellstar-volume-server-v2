# VSQueryTool

# Usage
## Quick start
To run the query app tool and produce the static files suitable for visualization at the frontend:
1. Build the database using preprocessor **(TODO LINK TO README FOR PREPROCESSOR)**

2. From repository root (`cellstar-volume-server-v2` by default) run:
    ```
    python --db_path PATH_TO_DB --out OUTPUT_FILE --json-params-path PATH_TO_JSON_WITH_PARAMETERS
    ```
## Arguments description
- `--db_path` - path to the database built using preprocessor
- `--out` - path to the output file where the results of the query will be stored

- `--json-params-path` Path to `.json` file with query parameters (see table below)

### Query parameters
| Parameter         | Description                                                                                                             | Kind      | Type                                        | Default                          |
|-------------------|-------------------------------------------------------------------------------------------------------------------------|-----------|---------------------------------------------|----------------------------------|
| entry_id          | ID of entry in internal database (e.g. emd-1832)                                                                        | mandatory | string                                      | N/A                              |
| source_db         | Source database (e.g. emdb)                                                                                             | mandatory | string                                      | N/A                              |
| segmentation_kind | Kind of segmentation (e.g. lattice)                                                                                     | optional  | 'mesh', 'lattice', 'geometric-segmentation' | all segmentation kinds           |
| time              | Timeframe index                                                                                                         | optional  | integer                                     | all available time frame indices |
| channel_id        | Volume channel ID                                                                                                       | optional  | string                                      | all available channel IDs        |
| segmentation_id   | Segmentation ID                                                                                                         | optional  | string                                      | all available segmentation IDs   |
| max_points        | Maximum number of points for volume and/or lattice segmentation. Used to determine the most suitable downsampling level | optional  | integer                                     | 1000000000000                    |


## Example
This example shows how produce `results.cvsx` CVSX file for `idr-13457537`internal database entry (with the database located in `temp/test_db`) containing the volume data for channel 2 and timeframe index 4, and segmentation data for all available segmentation kinds and timeframe index 4

First create `json_with_query_params.json` file with the following content: 

```json
        "entry_id": "idr-13457537",
        "source_db": "idr",
        "channel_id": "2",
        "time": 4

```

Then use the following command:
    ```
    python query_app.py --db_path temp/test_db --out results.cvsx composite --json-params-path json_with_query_params.json
    ```
    
This will query data for channel `2` and time frame `4` for volume and data for all available segmentation kinds and time frame `4`, and pack it into `idr-13457537.cvsx` file