from pathlib import Path

import dask.array as da
import mrcfile
import numpy as np
import zarr
from cellstar_db.file_system.constants import (
    QUANTIZATION_DATA_DICT_ATTR_NAME,
    VOLUME_DATA_GROUPNAME,
)

from preprocessor.src.preprocessors.implementations.sff.preprocessor._zarr_methods import (
    create_dataset_wrapper,
)
from preprocessor.src.tools.quantize_data.quantize_data import quantize_data


def open_zarr_structure_from_path(path: Path) -> zarr.hierarchy.Group:
    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(path))
    # Re-create zarr hierarchy from opened store
    root: zarr.hierarchy.group = zarr.group(store=store)
    return root


def _normalize_axis_order_mrcfile(dask_arr: da.Array, mrc_header: object) -> da.Array:
    """
    Normalizes axis order to X, Y, Z (1, 2, 3)
    """
    h = mrc_header
    current_order = int(h.mapc) - 1, int(h.mapr) - 1, int(h.maps) - 1

    if current_order != (0, 1, 2):
        print(f"Reordering axes from {current_order}...")
        ao = {v: i for i, v in enumerate(current_order)}
        # TODO: optimize this to a single transpose
        dask_arr = dask_arr.transpose().transpose(ao[2], ao[1], ao[0]).transpose()
    else:
        dask_arr = dask_arr.transpose()

    return dask_arr


def _store_volume_map_data_in_zarr_stucture(
    data: da.Array,
    volume_data_group: zarr.hierarchy.Group,
    params_for_storing: dict,
    force_dtype: np.dtype,
):
    # original resolution, time frame 0, channel 0
    resolution = "0"
    time_frame = "0"
    channel = "0"
    resolution_data_group = volume_data_group.create_group(resolution)
    time_frame_data_group = resolution_data_group.create_group(time_frame)

    if "quantize_dtype_str" in params_for_storing:
        force_dtype = params_for_storing["quantize_dtype_str"]

    zarr_arr = create_dataset_wrapper(
        zarr_group=time_frame_data_group,
        data=None,
        name=str(channel),
        shape=data.shape,
        dtype=force_dtype,
        params_for_storing=params_for_storing,
        is_empty=True,
    )

    if "quantize_dtype_str" in params_for_storing:
        quantized_data_dict = quantize_data(
            data=data, output_dtype=params_for_storing["quantize_dtype_str"]
        )

        data = quantized_data_dict["data"]

        quantized_data_dict_without_data = quantized_data_dict.copy()
        quantized_data_dict_without_data.pop("data")

        # save this dict as attr of zarr arr
        zarr_arr.attrs[
            QUANTIZATION_DATA_DICT_ATTR_NAME
        ] = quantized_data_dict_without_data

    da.to_zarr(arr=data, url=zarr_arr, overwrite=True, compute=True)


def extract_metadata(
    zarr_structure: zarr.hierarchy.group,
    mrc_header: object,
    volume_force_dtype: np.dtype,
    source_db_id: str,
    source_db_name: str,
) -> dict:
    pass


def volume_map_preprocessing(
    intermediate_zarr_structure_path: Path,
    volume_input_path: Path,
    params_for_storing: dict,
    volume_force_dtype: str,
):
    # 1. normalize axis order
    # 2. extract/compute metadata
    # 3. add volume data to intermediate zarr structure

    zarr_structure: zarr.hierarchy.group = open_zarr_structure_from_path(
        intermediate_zarr_structure_path
    )

    with mrcfile.mmap(str(volume_input_path.resolve())) as mrc_original:
        data: np.memmap = mrc_original.data
        if volume_force_dtype is not None:
            data = data.astype(volume_force_dtype)
        else:
            volume_force_dtype = data.dtype

        header = mrc_original.header

    print(f"Processing volume file {volume_input_path}")
    dask_arr = da.from_array(data)
    dask_arr = _normalize_axis_order_mrcfile(dask_arr=dask_arr, mrc_header=header)

    # create volume data group
    volume_data_group: zarr.hierarchy.group = zarr_structure.create_group(
        VOLUME_DATA_GROUPNAME
    )
    _store_volume_map_data_in_zarr_stucture(
        data=dask_arr,
        volume_data_group=volume_data_group,
        params_for_storing=params_for_storing,
        force_dtype=volume_force_dtype,
    )

    # TODO: extract metadata


def sff_preprocessing():
    pass


def annotation_preprocessing():
    pass


def preprocess_ometiff():
    pass


def preprocess_omezarr():
    pass
    # preprocess omezarr
    # then check if downsamplings are there
    if _check_if_downsamplings_in_omezarr():
        _add_no_processing_mark()


def _check_if_downsamplings_in_omezarr(omezarr_root) -> bool:
    """ """


def _add_no_processing_mark(intermediate_zarr_structure):
    """Adds attr to intermediate_zarr_structure if it does not require further processing
    i.e. contains downsamplings (e.g. OME ZARR)
    """
