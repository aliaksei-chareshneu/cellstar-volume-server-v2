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
python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path test-data/preprocessor/sample_volumes/emdb/EMD-1832.map --input-kind map --input-path test-data/preprocessor/sample_segmentations/geometric_segmentations/geometric_segmentation_1.json --input-kind geometric_segmentation --input-path test-data/preprocessor/sample_segmentations/geometric_segmentations/geometric_segmentation_2.json --input-kind geometric_segmentation  --entry-id emd-1832-geometric-segmentation --source-db emdb --source-db-id emd-1832-geometric-segmentation --source-db-name emdb --working-folder temp_working_folder --db-path test_db
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


In order to add an `empiar-10988` entry with geometric segmentation to the internal database, follow the steps below:
1. Obtain the raw input files

	Create `test-data/preprocessor/sample_volumes/empiar/empiar-10988` folder, change current directory to it, and download electron density map file, e.g. using wget:

    ```shell
    mkdir -p test-data/preprocessor/sample_volumes/empiar/empiar-10988
    cd test-data/preprocessor/sample_volumes/empiar/empiar-10988
    wget https://ftp.ebi.ac.uk/empiar/world_availability/10988/data/DEF/tomograms/TS_026.rec
	```

	Next, `create test-data/preprocessor/sample_segmentations/empiar/empiar-10988` directory, change current directory to it, and download two `.star` files:

    
    ```shell
    mkdir -p test-data/preprocessor/sample_segmentations/empiar/empiar-10988
    cd test-data/preprocessor/sample_segmentations/empiar/empiar-10988
    wget https://ftp.ebi.ac.uk/empiar/world_availability/10988/data/DEF/labels/TS_026.labels.mrc
    wget https://ftp.ebi.ac.uk/empiar/world_availability/10988/data/DEF/labels/TS_026_cyto_ribosomes.mrc
    wget https://ftp.ebi.ac.uk/empiar/world_availability/10988/data/DEF/labels/TS_026_cytosol.mrc
    wget https://ftp.ebi.ac.uk/empiar/world_availability/10988/data/DEF/labels/TS_026_fas.mrc
    wget https://ftp.ebi.ac.uk/empiar/world_availability/10988/data/DEF/labels/TS_026_membranes.mrc
    ```

2. Prepare extra data
    By default, Preprocessor will use segment IDs based on grid values in mask file. It is possible to overwrite them using additional input file with extra data, mapping segment IDs used by default (e.g. "1", "2" etc.) to biologically meaningful segment IDs (e.g., "cytoplasm", "mitochondria" etc.).
    Create `extra_data_empiar_10988.json` file in root repository directory with the following content:
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

  The content of the file is based on the content of `organelle_labels.txt` from [EMPIAR-10988 webpage](https://www.ebi.ac.uk/empiar/EMPIAR-10988/). It maps the segment IDs for segmentation from `TS_026.labels.mrc` file to biologically relevant segment names. 
3. Add `empiar-10988` entry to the internal database
    To add an `empiar-10988` entry with segmentations based on masks to the db, from root directory (`cellstar-volume-server-v2`) run:
    ```
    python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path extra_data_empiar_10988.json --input-kind extra_data --input-path test-data/preprocessor/sample_volumes/empiar/empiar-10988/TS_026.rec --input-kind map --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026.labels.mrc --input-kind mask --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026_membranes.mrc --input-kind mask --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026_fas.mrc --input-kind mask --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026_cytosol.mrc --input-kind mask --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026_cyto_ribosomes.mrc --input-kind mask --entry-id empiar-10988 --source-db empiar --source-db-id empiar-10988 --source-db-name empiar --working-folder temp_working_folder --db-path test_db
    ```






<!-- 
    Navigate your browser to EMPIAR-10988 entry web page at EMPIAR website (https://www.ebi.ac.uk/empiar/EMPIAR-10988/), scroll down to `Browse All Files` section. Open the dropdown under `Download` button, unselect all the files, select only the following files:
    - `11756/data/tomoman_minimal_project/cryocare_bin4_tomoname/17072022_BrnoKrios_Arctis_p3ar_grid_Position_35.mrc`
    - `11756/data/tomoman_minimal_project/17072022_BrnoKrios_Arctis_p3ar_grid_Position_35/metadata/particles/rln_nucleosome_bin1_tomo_649.star`
     - `11756/data/tomoman_minimal_project/17072022_BrnoKrios_Arctis_p3ar_grid_Position_35/metadata/particles/rln_ribosome_bin1_tomo_649.star`
	
	Download the files by pressing `Download` button and selecting `Uncompressed ZIP archive streamed via HTTP` option. Unzip the archive. 

    Create `test-data/preprocessor/sample_volumes/empiar/empiar-11756` folder, copy `11756/data/tomoman_minimal_project/cryocare_bin4_tomoname/17072022_BrnoKrios_Arctis_p3ar_grid_Position_35.mrc` file to it.
    
    Create `test-data/preprocessor/sample_segmentations/empiar/empiar-11756` folder, copy `11756/data/tomoman_minimal_project/17072022_BrnoKrios_Arctis_p3ar_grid_Position_35/metadata/particles/rln_nucleosome_bin1_tomo_649.star` and `11756/data/tomoman_minimal_project/17072022_BrnoKrios_Arctis_p3ar_grid_Position_35/metadata/particles/rln_ribosome_bin1_tomo_649.star` files to it.


2. Prepare input files.
	This EMPIAR entry contains relevant data that can be used to render geometric segmentation in .star format. To be able to use this data, .star files need to be parsed into the standard Mol* VS 2.0 format for geometric segmentations. This can be achieved by using custom script `preprocessor/cellstar_preprocessor/tools/parse_star_file/parse_single_star_file.py` that is part of our solution. In parallel, this script allows to set the biologically meaningful segmentation IDs for both geometric segmentations based on the data from EMPIAR entry webpage (i.e. `ribosomes` and `nucleosomes`). In order to parse both .star files, from the root repository directory (cellstar-volume-server-v2 by default) run:

    ```shell
    python preprocessor/cellstar_preprocessor/tools/parse_star_file/parse_single_star_file.py --star_file_path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/rln_ribosome_bin1_tomo_649.star --geometric_segmentation_input_file_path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/geometric_segmentation_input_1.json --sphere_radius 100 --segmentation_id ribosomes  --sphere_color_hex FFFF00 --pixel_size 7.84 --star_file_coordinate_divisor 4
    ```

    ```shell
    python preprocessor/cellstar_preprocessor/tools/parse_star_file/parse_single_star_file.py --star_file_path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/rln_nucleosome_bin1_tomo_649.star --geometric_segmentation_input_file_path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/geometric_segmentation_input_2.json --sphere_radius 100  --segmentation_id nucleosomes --sphere_color_hex FF0000 --pixel_size 7.84 --star_file_coordinate_divisor 4
    ```

    Besides the volume map file from EMPIAR entry webpage has wrong header parameters (voxel size is 0 for all 3 spatial dimensions). To alleviate this, one can use functionality of Preprocessor that allows to overwrite database entry parameters during preprocessing. Based on the data from EMPIAR entry webpage, voxel size should be `1.96` Angstrom for all 3 dimensions. Since we use volume map file from cryocare_bin4_tomoname folder, this value needs to be multiplied by 4, which gives us `7.84` Angstrom. According to this, create `test-data/preprocessor/sample_volumes/empiar/empiar-11756/empiar-11756-extra-data.json` file with the following content:

    ```json
    {
        "volume": {
            "voxel_size": [
                7.84,
                7.84,
                7.84
            ]
        }   
    }
    ```


3. Add empiar-11756 entry to the internal database
To add an empiar-11756 entry with segmentations based on masks to the db, from root directory (`cellstar-volume-server-v2`) run:


```shell
python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path test-data/preprocessor/sample_volumes/empiar/empiar-11756/empiar-11756-extra-data.json --input-kind extra_data --input-path test-data/preprocessor/sample_volumes/empiar/empiar-11756/17072022_BrnoKrios_Arctis_p3ar_grid_Position_35.mrc --input-kind map --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/geometric_segmentation_input_1.json --input-kind geometric_segmentation --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/geometric_segmentation_input_2.json --input-kind geometric_segmentation --entry-id empiar-11756 --source-db empiar --source-db-id empiar-11756 --source-db-name empiar --working-folder temp_working_folder --db-path preprocessor/temp/test_db
```

It will create a database entry with two geometric segmentations (segmentation IDs “ribosomes” and “nucleosomes”).

 - Navigate to [EMPIAR-10988 entry webpage](https://www.ebi.ac.uk/empiar/EMPIAR-10988/)
 - Scroll down to `Browse All Files` section.
 - Open the dropdown under `Download` button, select just the files that are selected on the screenshot below:
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
python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path extra_data_empiar_10988.json --input-kind extra_data --input-path test-data/preprocessor/sample_volumes/empiar/empiar-10988/TS_026.rec --input-kind map --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026.labels.mrc --input-kind mask --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026_membranes.mrc --input-kind mask --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026_fas.mrc --input-kind mask --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026_cytosol.mrc --input-kind mask --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026_cyto_ribosomes.mrc --input-kind mask --entry-id empiar-10988 --source-db empiar --source-db-id empiar-10988 --source-db-name empiar --working-folder temp_working_folder --db-path test_db
``` -->


#### EMPIAR-11756
In order to add an empiar-11756 entry with geometric segmentation to the internal database, follow the steps below:
1. Obtain the raw input files

	Create `test-data/preprocessor/sample_volumes/empiar/empiar-11756` folder, change current directory to it, and download electron density map file, e.g. using wget:

    ```shell
    mkdir -p test-data/preprocessor/sample_volumes/empiar/empiar-11756
    cd test-data/preprocessor/sample_volumes/empiar/empiar-11756
    wget https://ftp.ebi.ac.uk/empiar/world_availability/11756/data/tomoman_minimal_project/cryocare_bin4_tomoname/17072022_BrnoKrios_Arctis_p3ar_grid_Position_35.mrc
	```

	Next, `create test-data/preprocessor/sample_segmentations/empiar/empiar-11756` directory, change current directory to it, and download two `.star` files:

    
    ```shell
    mkdir -p test-data/preprocessor/sample_segmentations/empiar/empiar-11756
    cd test-data/preprocessor/sample_segmentations/empiar/empiar-11756
    wget https://ftp.ebi.ac.uk/empiar/world_availability/11756/data/tomoman_minimal_project/17072022_BrnoKrios_Arctis_p3ar_grid_Position_35/metadata/particles/rln_nucleosome_bin1_tomo_649.star
    wget https://ftp.ebi.ac.uk/empiar/world_availability/11756/data/tomoman_minimal_project/17072022_BrnoKrios_Arctis_p3ar_grid_Position_35/metadata/particles/rln_ribosome_bin1_tomo_649.star
    ```

2. Prepare input files.

	This EMPIAR entry contains relevant data that can be used to render geometric segmentation in .star format. To be able to use this data, .star files need to be parsed into the standard Mol* VS 2.0 format for geometric segmentations. This can be achieved by using custom script `preprocessor/cellstar_preprocessor/tools/parse_star_file/parse_single_star_file.py` that is part of our solution. In parallel, this script allows to set the biologically meaningful segmentation IDs for both geometric segmentations based on the data from EMPIAR entry webpage (i.e. `ribosomes` and `nucleosomes`). In order to parse both .star files, from the root repository directory (cellstar-volume-server-v2 by default) run:

    ```shell
    python preprocessor/cellstar_preprocessor/tools/parse_star_file/parse_single_star_file.py --star_file_path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/rln_ribosome_bin1_tomo_649.star --geometric_segmentation_input_file_path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/geometric_segmentation_input_1.json --sphere_radius 100 --segmentation_id ribosomes  --sphere_color_hex FFFF00 --pixel_size 7.84 --star_file_coordinate_divisor 4
    ```

    ```shell
    python preprocessor/cellstar_preprocessor/tools/parse_star_file/parse_single_star_file.py --star_file_path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/rln_nucleosome_bin1_tomo_649.star --geometric_segmentation_input_file_path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/geometric_segmentation_input_2.json --sphere_radius 100  --segmentation_id nucleosomes --sphere_color_hex FF0000 --pixel_size 7.84 --star_file_coordinate_divisor 4
    ```

    Besides the volume map file from EMPIAR entry webpage has wrong header parameters (voxel size is 0 for all 3 spatial dimensions). To alleviate this, one can use functionality of Preprocessor that allows to overwrite database entry parameters during preprocessing. Based on the data from EMPIAR entry webpage, voxel size should be `1.96` Angstrom for all 3 dimensions. Since we use volume map file from cryocare_bin4_tomoname folder, this value needs to be multiplied by 4, which gives us `7.84` Angstrom. According to this, create `test-data/preprocessor/sample_volumes/empiar/empiar-11756/empiar-11756-extra-data.json` file with the following content:

    ```json
    {
        "volume": {
            "voxel_size": [
                7.84,
                7.84,
                7.84
            ]
        }   
    }
    ```


3. Add empiar-11756 entry to the internal database

    To add an empiar-11756 entry with segmentations based on masks to the db, from root directory (`cellstar-volume-server-v2`) run:


    ```shell
    python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path test-data/preprocessor/sample_volumes/empiar/empiar-11756/empiar-11756-extra-data.json --input-kind extra_data --input-path test-data/preprocessor/sample_volumes/empiar/empiar-11756/17072022_BrnoKrios_Arctis_p3ar_grid_Position_35.mrc --input-kind map --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/geometric_segmentation_input_1.json --input-kind geometric_segmentation --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/geometric_segmentation_input_2.json --input-kind geometric_segmentation --entry-id empiar-11756 --source-db empiar --source-db-id empiar-11756 --source-db-name empiar --working-folder temp_working_folder --db-path preprocessor/temp/test_db
    ```

    It will create a database entry with two geometric segmentations (segmentation IDs “ribosomes” and “nucleosomes”).

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