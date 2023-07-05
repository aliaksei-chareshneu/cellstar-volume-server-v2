from enum import Enum
from pathlib import Path
from typing import Optional

from numcodecs import Blosc
from pydantic import BaseModel


class InputCase(str, Enum):
    map_only = "map_only"
    map_and_sff = "map_and_sff"
    omezarr = "omezarr"
    ometiff = "ometiff"


class InputKind(str, Enum):
    map = "map"
    sff = "sff"
    ometiff = "ometiff"
    omezarr = "omezarr"
    mask = "mask"
    # do we need to have it as separate types (am, mod, seg), or better to have general one and
    # leave it for a specific conversion function to check the extension and run conversion?
    application_specific_segmentation = "application_specific_segmentation"
    custom_annotations = "custom_annotations"


class QuantizationDtype(str, Enum):
    u1 = "u1"
    u2 = "u2"


class Inputs(BaseModel):
    #    tuple[filename, kind]
    # kinds: 'map', 'sff', 'ome.tiff', 'ome-zarr', 'mask', 'am', 'mod', 'seg', 'custom_annotations' ?
    # depending on files list it runs preprocessing, if application specific - first converts to sff
    files: list[tuple[Path, InputKind]]


class VolumeParams(BaseModel):
    quantize_dtype_str: Optional[QuantizationDtype]
    force_volume_dtype: Optional[str]


class DownsamplingParams(BaseModel):
    max_size_per_channel_mb: Optional[float]
    min_size_per_channel_mb: Optional[float]
    min_downsampling_level: Optional[int]
    max_downsampling_level: Optional[int]


class StoringParams(BaseModel):
    #  params_for_storing
    # 'auto'
    chunking_mode: str = "auto"
    # Blosc(cname='lz4', clevel=5, shuffle=Blosc.SHUFFLE, blocksize=0)
    compressor: object = Blosc(
        cname="lz4", clevel=5, shuffle=Blosc.SHUFFLE, blocksize=0
    )
    # we use only 'zip'
    store_type: str = "zip"


class EntryData(BaseModel):
    # entry id (e.g. emd-1832) to be used as database folder name for that entry
    entry_id: str
    # source database name (e.g. emdb) to be used as DB folder name
    source_db: str
    #    actual source database ID of that entry (will be used to compute metadata)
    source_db_id: str
    #    actual source database name (will be used to compute metadata)
    source_db_name: str


class PreprocessorInput(BaseModel):
    inputs: Inputs
    volume: VolumeParams
    # optional - we may not need them (for OME Zarr there are already downsamplings)
    downsampling: Optional[DownsamplingParams]
    entry_data: EntryData
    # for intermediate data
    working_folder: Path

    # do we need these two here?
    # storing params perhaps should be here as temporary internal format (zarr) also uses them
    db_path: Path
    storing_params: StoringParams
