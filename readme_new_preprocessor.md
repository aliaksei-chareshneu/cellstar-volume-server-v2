## Adding entry to database or extending data of existing entry

The `preprocess` command of `preprocessor/cellstar_preprocessor/preprocess.py` script is used for adding entries to the database with the following arguments:

  | Argument | Description |
  | -------- | ---------- |
  |`--mode` | Either `add` (adding entry to the database) or `extend` (extend data of existing entry) |
  |`--quantize-dtype-str` | Optional data quantization (options are - `u1` or `u2`), less precision, but also requires less storage. Not used by default |
  |`--quantize-downsampling-levels` | Specify which downsampling level should be quantized as a sequence of numbers, e.g. `1 2`. Not used by default |
  |`--force-volume-dtype` | optional data type of volume data to be used instead of the one used volume file. Not used by default |
  |`--max-size-per-downsampling-lvl-mb` | Maximum size of data per downsampling level in MB. Used to deterimine the number of downsampling steps data from which will be stored |
  |`--min-size-per-channel-mb` | Minimum size of data per downsampling level in MB. Used to deterimine the number of downsampling steps data from which will be stored. Default is `5` |
  |`--min-downsampling-level` | Minimum downsampling level |
  |`--max-downsampling-level` | Maximum downsampling level |
  |`--remove-original-resolution` | Optional flag for removing original resolution data |
  |`--entry-id` | entry id (e.g. `emd-1832`) to be used as database folder name for that entry |
  |`--source-db` | source database name (e.g. `emdb`) to be used as DB folder name |
  |`--source-db-id` | actual source database ID of that entry (will be used to compute metadata) |
  |`--source-db-name` | actual source database name (will be used to compute metadata) |
  |`--working-folder` | path to directory where temporary files will be stored during the build process |
  |`--db-path` | path to folder with database |
  |`--input-path` | Path to input file. Should be provided for each input file separately (see examples) |
  |`--input-kind` | Kind of input file. One of the following: <code>[map\|sff\|omezarr\|mask\|application_specific_segmentation\|custom_annotations\|nii_volume\|nii_segmentation\|geometric_segmentation\|star_file_geometric_segmentation\|ometiff_image\|ometiff_segmentation\|extra_data]</code>. See examples for more details. |
  <!-- TODO: table with input kinds? -->
  <!-- TODO: remove nii things? -->


### Examples of adding a single entry to the database

#### EMD-1832
<!-- - Create a folder `inputs/emd-1832`
- Download [MAP](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-1832/map/emd_1832.map.gz) and extract it to `inputs/emd-1832/emd_1832.map`
- Download [Segmentation](https://www.ebi.ac.uk/em_static/emdb_sff/18/1832/emd_1832.hff.gz) and extract it to `inputs/emd-1832/emd_1832.hff` -->

- To add an emd-1832 entry to the db, from root directory (`cellstar-volume-server-v2`) run:

```
python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path test-data/preprocessor/sample_volumes/emdb/EMD-1832.map --input-kind map --input-path test-data/preprocessor/sample_segmentations/emdb_sff/emd_1832.hff --input-kind sff --entry-id emd-1832 --source-db emdb --source-db-id emd-1832 --source-db-name emdb --working-folder temp_working_folder --db-path test_db --quantize-dtype-str u1
```

It will add entry `emd-1832` to the database and during preprocessing volume data will be quantized with `u1` option

#### IDR-13457537
- To add IDR-13457537 entry to the db, unzip `test-data/preprocessor/sample_segmentations/idr/13457537.zarr.zip` file:
```
cd test-data/preprocessor/sample_segmentations/idr/idr-13457537
unzip 13457537.zarr.zip
```

From root directory (`cellstar-volume-server-v2`), run:
```
python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path test-data/preprocessor/sample_segmentations/idr/idr-13457537/13457537.zarr --input-kind omezarr --entry-id idr-13457537 --source-db idr --source-db-id idr-13457537 --source-db-name idr --working-folder temp_working_folder --db-path test_db
```

It will add entry `idr-13457537` to the database

#### EMD-1832-geometric-segmentation

- To add an emd-1832 entry with artificially created geometric segmentation to the db, from root directory (`cellstar-volume-server-v2`) run:

```
python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path test-data/preprocessor/sample_volumes/emdb/EMD-1832.map --input-kind map --input-path test-data\preprocessor\sample_segmentations\geometric_segmentations\geometric_segmentation_1.json --input-kind geometric_segmentation --input-path test-data\preprocessor\sample_segmentations\geometric_segmentations\geometric_segmentation_2.json --input-kind geometric_segmentation  --entry-id emd-1832-geometric-segmentation --source-db emdb --source-db-id emd-1832-geometric-segmentation --source-db-name emdb --working-folder temp_working_folder --db-path test_db
```

It will add entry `emd-1832-geometric-segmentation` to the database

#### EMD-1273 with segmentations based on masks
<!-- - Create a folder `inputs/emd-1832` -->
1. Download [MAP](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-1273/map/emd_1273.map.gz) and extract it to `test-data/preprocessor/sample_volumes/emdb/`
2. Create folder `test-data/preprocessor/sample_segmentations/emdb_masks/` if not exists
3. Download masks to `test-data/preprocessor/sample_segmentations/emdb_masks/`:
    - [Mask 1](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-1273/masks/emd_1273_msk_1.map)
    - [Mask 2](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-1273/masks/emd_1273_msk_2.map)
    - [Mask 3](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-1273/masks/emd_1273_msk_3.map)
    - [Mask 4](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-1273/masks/emd_1273_msk_4.map)
    - [Mask 5](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-1273/masks/emd_1273_msk_5.map)

4. To add an `emd-1273` entry with segmentations based on masks to the db, from root directory (`cellstar-volume-server-v2`) run:

```
python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path test-data/preprocessor/sample_volumes/emdb/emd_1273.map --input-kind map --input-path test-data/preprocessor/sample_segmentations/emdb_masks/emd_1273_msk_1.map --input-kind mask --input-path test-data/preprocessor/sample_segmentations/emdb_masks/emd_1273_msk_2.map --input-kind mask --input-path test-data/preprocessor/sample_segmentations/emdb_masks/emd_1273_msk_3.map --input-kind mask --input-path test-data/preprocessor/sample_segmentations/emdb_masks/emd_1273_msk_4.map --input-kind mask --input-path test-data/preprocessor/sample_segmentations/emdb_masks/emd_1273_msk_5.map --input-kind mask --entry-id emd-1273 --source-db emdb --source-db-id emd-1273 --source-db-name emdb --working-folder temp_working_folder --db-path test_db
```

#### EMPIAR-10988
 - Navigate to [EMPIAR-10988 entry webpage](https://www.ebi.ac.uk/empiar/EMPIAR-10988/)
 - Scroll down to `Browse All Files` section.
 - Open the dropdown under `Download button`, select just the files that are selected on the screenshot below:
 ![alt text](empiar-10988-webpage.png)
 - Press `Download`
 - Choose `Uncompressed ZIP archive streamed via HTTP`
 - Unzip the ZIP archive.
 - Create `test-data/preprocessor/sample_volumes/empiar/empiar-10988` folder
 - Copy `TS_026.rec` file to `test-data/preprocessor/sample_volumes/empiar/empiar-10988` folder
 - Create folder `test-data/preprocessor/sample_segmentations/empiar/empiar-10988`
 - Copy `TS_026.labels.mrc`, `TS_026_cyto_ribosomes.mrc`, `TS_026_cytosol.mrc`, `TS_026_fas.mrc`, and `TS_026_membranes.mrc` files to `test-data/preprocessor/sample_segmentations/empiar/empiar-10988`
 - Create `extra_data_empiar_10988.json` file in root repository directory with the following content:
  ```json
  {
      "segmentation": {
          "segment_ids_to_segment_names_mapping": {
              "TS_026.labels": {
                  "1": "cytoplasm",
                  "2": "mitochondria",
                  "3": "vesicle",
                  "4": "tube",
                  "5": "ER",
                  "6": "nuclear envelope",
                  "7": "nucleus",
                  "8": "vacuole",
                  "9": "lipid droplet",
                  "10": "golgi",
                  "11": "vesicular body",
                  "13": "not identified compartment"
              }
          }
      }
  }
  ```

  The content of the file is based on the content of `organelle_labels.txt` from EMPIAR-10988 webpage. It maps the segment IDs for segmentation from `TS_026.labels.mrc` file to biologically relevant segment names. 

 - To add an `empiar-10988` entry with segmentations based on masks to the db, from root directory (`cellstar-volume-server-v2`) run:
 
```
python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path extra_data_empiar_10988.json --input-kind extra_data --input-path test-data/preprocessor/sample_volumes/empiar/empiar-10988/TS_026.rec --input-kind map --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026.labels.mrc --input-kind mask --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026_membranes.mrc --input-kind mask --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026_fas.mrc --input-kind mask --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026_cytosol.mrc --input-kind mask --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026_cyto_ribosomes.mrc --input-kind mask --entry-id empiar-10988 --source-db empiar --source-db-id empiar-10988 --source-db-name empiar --working-folder /mnt/data_compute_ssd/temp/temp_zarr_hierarchy_storage --db-path /mnt/data_compute_ssd/temp/test_db
```

<!-- ## Editing descriptions of existing database entry

The `edit-descriptions` command of `preprocessor/cellstar_preprocessor/preprocess.py` script is used for editing descriptions of the existing database entry. The arguments are as follows:

  | Argument | Description |
  | -------- | ---------- |
  |`--entry-id` | entry id (e.g. `emd-1832`), i.e. internal database folder name for that entry |
  |`--source-db` | source database name (e.g. `emdb`) i.e. internal database to be used as database folder name |
  |`--db-path` | path to folder with internal database |
  |`--data-json-path` | path to file with descriptions |

### Examples

#### Adding descriptions for emd-1273 entry

First build the database with that entry according to [this tutorial](#emd-1273-with-segmentations-based-on-masks) 

Then from root directory (`cellstar-volume-server-v2`), run:
```
python preprocessor/cellstar_preprocessor/preprocess.py edit-descriptions --entry-id emd-1273 --source-db idr --data-json-path emd-1273-descriptions.json --db-path test_db
```

It will add descriptions to `emd-1273` entry. -->