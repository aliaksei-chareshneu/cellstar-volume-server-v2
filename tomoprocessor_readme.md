# Tomoprocessor

Tomoprocessor

# Installation

Clone this GitHub repository: 

```
git clone https://github.com/aliaksei-chareshneu/cellstar-volume-server-v2
cd cellstar-volume-server-v2
```

# Setting up the environment

Create conda environment from `environment-local.yaml`, e.g.:

You can use [Conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html)

```
conda env create -f environment-local.yaml
```


Or [Mamba](https://mamba.readthedocs.io/en/latest/installation.html)

```
mamba env create -f environment-local.yaml
```

# Running tomoprocessor
Activate created conda environment, e.g.

```
conda activate tomoprocessor
```

From root project directory (cellstar-volume-server-v2 by default) run:


<!-- TODO add args -->
```
python tomoprocessor\cellstar_tomoprocessor\tomoprocessor.py 
```

This will build db with 11 EMDB entries, and using default values of all other arguments.
Arguments description:
 - `--csv_with_entry_ids` - csv file with entry ids and info for preprocessor, default - test-data\preprocessor\db_building_parameters_all_entries.csv (not recommended to use default for users, as it requires static files to be hosted at specific location, use --csv_with_entry_ids test-data/preprocessor/db_building_parameters_custom_entries.csv instead)
 - `--raw_input_files_dir` dir with raw input files for preprocessor, default - test-data/preprocessor//raw_input_files
 - `--db_path` - path to db folder, default - test-data/db
 - `--temp_zarr_hierarchy_storage_path` - path to directory where temporary files will be stored during the build process. Default - test-data/preprocessor/temp_zarr_hierarchy_storage/YOUR_DB_PATH


# Testing (sample datasets visualized at frontend)

[Dataset 1 (EMPIAR-11658, 9.rec and spheres based on 80S_bin1_cryoDRGN-ET_clean_tomo_9.star)](https://aliaksei-chareshneu.github.io/tomo-project/index.html?data-source=https://aliaksei-chareshneu.github.io/tomo-project/test_zip.zip)

[Dataset_2 (EMPIAR-11658) 171.rec and sphere based on 80S_bin1_cryoDRGN-ET_clean_tomo_171.star](https://aliaksei-chareshneu.github.io/tomo-project/index.html?data-source=https://aliaksei-chareshneu.github.io/tomo-project/171.zip)