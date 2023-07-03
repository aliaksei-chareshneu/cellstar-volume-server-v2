# TODO: figure out how to use
# params_for_storing=self.preprocessor_input.storing_params,
# downsampling_parameters=self.preprocessor_input.downsampling,

import numcodecs
import numpy as np
import zarr

from preprocessor_v2.preprocessor.flows.common import open_zarr_structure_from_path
from preprocessor_v2.preprocessor.flows.constants import SEGMENTATION_DATA_GROUPNAME
from preprocessor_v2.preprocessor.model.segmentation import InternalSegmentation


def ome_zarr_labels_preprocessing(internal_segmentation: InternalSegmentation):
    ome_zarr_root = zarr.open_group(internal_segmentation.segmentation_input_path)

    our_zarr_structure = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )

    segmentation_data_gr = our_zarr_structure.create_group(SEGMENTATION_DATA_GROUPNAME)

    root_zattrs = ome_zarr_root.attrs
    multiscales = root_zattrs["multiscales"]
    # NOTE: can be multiple multiscales, here picking just 1st
    axes = multiscales[0]["axes"]

    for label_gr_name, label_gr in ome_zarr_root.labels.groups():
        lattice_id_gr = segmentation_data_gr.create_group(label_gr_name)
        # arr_name is resolution
        for arr_name, arr in label_gr.arrays():
            our_resolution_gr = lattice_id_gr.create_group(arr_name)
            if len(axes) == 5 and axes[0]["name"] == "t":
                for i in range(arr.shape[0]):
                    time_group = our_resolution_gr.create_group(str(i))
                    for j in range(arr.shape[1]):
                        corrected_arr_data = arr[...][i][j].swapaxes(0, 2)
                        # i8 is not supported by CIFTools
                        if corrected_arr_data.dtype == "i8":
                            corrected_arr_data = corrected_arr_data.astype("i4")
                        our_channel_group = time_group.create_group(str(j))
                        our_arr = our_channel_group.create_dataset(
                            name="grid",
                            shape=corrected_arr_data.shape,
                            data=corrected_arr_data,
                        )

                        our_set_table = our_channel_group.create_dataset(
                            name="set_table",
                            dtype=object,
                            object_codec=numcodecs.JSON(),
                            shape=1,
                        )

                        d = {}
                        for value in np.unique(our_arr[...]):
                            d[str(value)] = [int(value)]

                        our_set_table[...] = [d]

            elif len(axes) == 4 and axes[0]["name"] == "c":
                time_group = our_resolution_gr.create_group("0")
                for j in range(arr.shape[0]):
                    corrected_arr_data = arr[...][j].swapaxes(0, 2)
                    if corrected_arr_data.dtype == "i8":
                        corrected_arr_data = corrected_arr_data.astype("i4")
                    our_channel_group = time_group.create_group(str(j))
                    our_arr = our_channel_group.create_dataset(
                        name="grid",
                        shape=corrected_arr_data.shape,
                        data=corrected_arr_data,
                    )

                    our_set_table = our_channel_group.create_dataset(
                        name="set_table",
                        dtype=object,
                        object_codec=numcodecs.JSON(),
                        shape=1,
                    )

                    d = {}
                    for value in np.unique(our_arr[...]):
                        d[str(value)] = [int(value)]

                    our_set_table[...] = [d]
            else:
                raise Exception("Axes number/order is not supported")
