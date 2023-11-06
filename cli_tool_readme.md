# CLI tool

CLI tool 

# Usage
To run the CLI tool and produce the static files suitable for visualization at the frontend:
1. Build the database using preprocessor **(TODO LINK TO README FOR PREPROCESSOR)**
2. From repository root (cellstar-volume-server-v2 by default) run:
    ```
    python --db_path PATH_TO_DB --out OUTPUT_FILE QUERY_TYPE QUERY_SPECIFIC_ARGUMENTS
    ```
    Arguments description:
    - `--db_path` - path to the database built using preprocessor
    - `--out` - path to the output file where the results of the query will be stored
    - `QUERY_TYPE` `QUERY_SPECIFIC_ARGUMENTS` - type of query and arguments specific for that query type:
        - `volume-cell`           Volume cell query
            - `--entry-id`        Entry ID in the database (e.g. "emd-1832")
            - `--source-db`       Source database (e.g. "emdb")
            - `--time`            Timeframe (e.g. 0)
            - `--channel-id`      Channel ID (e.g 0)
            - `--max-points`      *(optional)* Maximum number of points
        - `segmentation-cell`     Segmentation cell query
            - ... same arguments as for `volume-cell`
            - `--lattice-id`      Lattice ID (e.g. 0)
        - `volume-box`            Volume box query
            - ... same arguments as for `volume-cell`
            - `--box-coords`      XYZ coordinates of bottom left and top right of query box in Angstroms
        - `segmentation-box`      Segmentation box query
            - ... same arguments as for `volume-box`
            - `--lattice-id`      Lattice ID (e.g. 0)
        - `mesh`                  Mesh query (response is .json file)
            - `--entry-id`        Entry ID in the database (e.g. "emd-1832")
            - `--source-db`       Source database (e.g. "emdb")
            - `--time`            Timeframe (e.g. 0)
            - `--channel-id`      Channel ID (e.g 0)
            - `--segment-id`      Segment ID of mesh (e.g 1)
            - `--detail-lvl`      Required detail level (1 is the highest resolution)
        - `mesh-bcif`             Mesh bcif query (response is .bcif file)
            - ... same arguments as for mesh query
        - `metadata`              Metadata query
            - `--entry-id`        Entry ID in the database (e.g. "emd-1832")
            - `--source-db`       Source database (e.g. "emdb")
        - `annotations`           Annotations query
            - `--entry-id`        Entry ID in the database (e.g. "emd-1832")
            - `--source-db`       Source database (e.g. "emdb")
        - `volume-info`           Volume info query
            - `--entry-id`        Entry ID in the database (e.g. "emd-1832")
            - `--source-db`       Source database (e.g. "emdb")
        - `list-entries`          List entries query
            - `--limit`           Maximum number of entries
        - `list-entries-keyword`  List entries keyword query
            - `--limit`           Maximum number of entries
            - `--keyword`         Keyword
        - `composite`             Composite query, consisting of several simple queries listed above (i.e. `subqueries`).
            - `--json-params-path` Path to `.json` file with query parameters.
                File should be structured as follows:
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
                    ],
                    "args": {
                        "db_path": "temp/test_db",
                        "out": "result.zip",
                        "entry_id": "emd-1832",
                        "source_db": "emdb",
                        "time": 0,
                        "channel_id": 0,
                        "lattice_id": 0
                    }
                }
                ```
                This will produce `results.zip` containing the results of `volume-cell`, `segmentation-cell`, and `annotations` queries

# Example of usage
```
python local_api_query.py --db_path temp/test_db --out segm.bcif segmentation-cell --entry-id emd-1832 --source-db emdb --time 0 --channel-id 0 --lattice-id 0
```
This will produce `segm.bcif` file with the results of `segmentation-cell` query for `emd-1832` entry (with `time`, `channel-id`, and `lattice-id` parameters equal to 0) from the database located in `temp/test_db`