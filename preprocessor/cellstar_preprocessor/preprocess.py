import asyncio
import json
import logging
import shutil
import typing
from argparse import ArgumentError
from pathlib import Path
from cellstar_preprocessor.flows.segmentation.collect_custom_annotations import collect_custom_annotations
from cellstar_preprocessor.flows.segmentation.extract_metadata_from_nii_segmentation import extract_metadata_from_nii_segmentation
from cellstar_preprocessor.flows.segmentation.extract_metadata_geometric_segmentation import extract_metadata_geometric_segmentation
from cellstar_preprocessor.flows.segmentation.geometric_segmentation_preprocessing import geometric_segmentation_preprocessing
from cellstar_preprocessor.flows.segmentation.mask_segmentation_preprocessing import mask_segmentation_preprocessing
from cellstar_preprocessor.flows.segmentation.nii_segmentation_downsampling import nii_segmentation_downsampling
from cellstar_preprocessor.flows.segmentation.nii_segmentation_preprocessing import nii_segmentation_preprocessing
from cellstar_preprocessor.flows.volume.extract_nii_metadata import extract_nii_metadata
from cellstar_preprocessor.flows.volume.nii_preprocessing import nii_preprocessing
from cellstar_preprocessor.tools.convert_app_specific_segm_to_sff.convert_app_specific_segm_to_sff import convert_app_specific_segm_to_sff

import typer
import zarr

from cellstar_db.file_system.db import FileSystemVolumeServerDB
from pydantic import BaseModel
from typing_extensions import Annotated
from cellstar_db.models import AnnotationsMetadata

from cellstar_preprocessor.flows.common import (
    open_zarr_structure_from_path,
    temp_save_metadata,
    update_dict,
)
from cellstar_preprocessor.flows.constants import (
    ANNOTATION_METADATA_FILENAME,
    GRID_METADATA_FILENAME,
)
from cellstar_preprocessor.flows.segmentation.extract_annotations_from_sff_segmentation import (
    extract_annotations_from_sff_segmentation,
)
from cellstar_preprocessor.flows.segmentation.extract_metadata_from_sff_segmentation import (
    extract_metadata_from_sff_segmentation,
)
from cellstar_preprocessor.flows.segmentation.helper_methods import (
    check_if_omezarr_has_labels,
)
from cellstar_preprocessor.flows.segmentation.ome_zarr_labels_preprocessing import (
    ome_zarr_labels_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.segmentation_downsampling import (
    sff_segmentation_downsampling,
)
from cellstar_preprocessor.flows.segmentation.sff_preprocessing import (
    sff_preprocessing,
)
from cellstar_preprocessor.flows.volume.extract_metadata_from_map import (
    extract_metadata_from_map,
)
from cellstar_preprocessor.flows.volume.extract_omezarr_annotations import (
    extract_omezarr_annotations,
)
from cellstar_preprocessor.flows.volume.extract_omezarr_metadata import (
    extract_ome_zarr_metadata,
)
from cellstar_preprocessor.flows.volume.map_preprocessing import (
    map_preprocessing,
)
from cellstar_preprocessor.flows.volume.ome_zarr_image_preprocessing import (
    ome_zarr_image_preprocessing,
)
from cellstar_preprocessor.flows.volume.quantize_internal_volume import (
    quantize_internal_volume,
)
from cellstar_preprocessor.flows.volume.volume_downsampling import (
    volume_downsampling,
)
from cellstar_preprocessor.model.input import (
    OME_ZARR_PREPROCESSOR_INPUT,
    DownsamplingParams,
    EntryData,
    InputKind,
    Inputs,
    PreprocessorInput,
    QuantizationDtype,
    StoringParams,
    VolumeParams,
)
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.model.volume import InternalVolume


class InputT(BaseModel):
    input_path: Path


class MAPInput(InputT):
    pass


class SFFInput(InputT):
    pass


class OMEZARRInput(InputT):
    pass

class CustomAnnotationsInput(InputT):
    pass

class NIIVolumeInput(InputT):
    pass

class NIISegmentationInput(InputT):
    pass

class MaskInput(InputT):
    pass

class GeometricSegmentationInput(InputT):
    pass

class TaskBase(typing.Protocol):
    def execute(self) -> None:
        ...


class CustomAnnotationsCollectionTask(TaskBase):
    # NOTE: for this to work, custom annotations json must contain only the keys that 
    # need to be updated
    def __init__(
        self, input_path: Path, intermediate_zarr_structure_path: Path
    ) -> None:
        self.input_path = input_path
        self.intermediate_zarr_structure_path = intermediate_zarr_structure_path

    def execute(self) -> None:
        collect_custom_annotations(self.input_path, self.intermediate_zarr_structure_path)



class QuantizeInternalVolumeTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        quantize_internal_volume(internal_volume=self.internal_volume)


class SaveAnnotationsTask(TaskBase):
    def __init__(self, intermediate_zarr_structure_path: Path):
        self.intermediate_zarr_structure_path = intermediate_zarr_structure_path

    def execute(self) -> None:
        root = open_zarr_structure_from_path(self.intermediate_zarr_structure_path)
        temp_save_metadata(
            root.attrs["annotations_dict"],
            ANNOTATION_METADATA_FILENAME,
            self.intermediate_zarr_structure_path,
        )


class SaveMetadataTask(TaskBase):
    def __init__(self, intermediate_zarr_structure_path: Path):
        self.intermediate_zarr_structure_path = intermediate_zarr_structure_path

    def execute(self) -> None:
        root = open_zarr_structure_from_path(self.intermediate_zarr_structure_path)
        temp_save_metadata(
            root.attrs["metadata_dict"],
            GRID_METADATA_FILENAME,
            self.intermediate_zarr_structure_path,
        )


class SFFAnnotationCollectionTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        annotations_dict = extract_annotations_from_sff_segmentation(
            internal_segmentation=self.internal_segmentation
        )


class NIIMetadataCollectionTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        volume = self.internal_volume
        metadata_dict = extract_nii_metadata(internal_volume=volume)

class MAPMetadataCollectionTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        volume = self.internal_volume
        metadata_dict = extract_metadata_from_map(internal_volume=volume)


class OMEZARRAnnotationsCollectionTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        annotations_dict = extract_omezarr_annotations(
            internal_volume=self.internal_volume
        )


class OMEZARRMetadataCollectionTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        metadata_dict = extract_ome_zarr_metadata(internal_volume=self.internal_volume)


class OMEZARRImageProcessTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        ome_zarr_image_preprocessing(self.internal_volume)


class OMEZARRLabelsProcessTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        ome_zarr_labels_preprocessing(internal_segmentation=self.internal_segmentation)


class SFFMetadataCollectionTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        metadata_dict = extract_metadata_from_sff_segmentation(
            internal_segmentation=self.internal_segmentation
        )

class MaskMetadataCollectionTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        metadata_dict = extract_metadata_from_sff_segmentation(
            internal_segmentation=self.internal_segmentation
        )

class GeometricSegmentationMetadataCollectionTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        metadata_dict = extract_metadata_geometric_segmentation(
            internal_segmentation=self.internal_segmentation
        )

class NIISegmentationMetadataCollectionTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        metadata_dict = extract_metadata_from_nii_segmentation(
            internal_segmentation=self.internal_segmentation
        )

class MAPProcessVolumeTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        volume = self.internal_volume

        map_preprocessing(volume)
        # in processing part do
        volume_downsampling(volume)

class NIIProcessVolumeTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        volume = self.internal_volume

        nii_preprocessing(volume)
        # in processing part do
        volume_downsampling(volume)

class NIIProcessSegmentationTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        segmentation = self.internal_segmentation

        nii_segmentation_preprocessing(internal_segmentation=segmentation)

        nii_segmentation_downsampling(internal_segmentation=segmentation)

class SFFProcessSegmentationTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        segmentation = self.internal_segmentation

        sff_preprocessing(segmentation)

        sff_segmentation_downsampling(segmentation)

class MaskProcessSegmentationTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        segmentation = self.internal_segmentation

        mask_segmentation_preprocessing(internal_segmentation=segmentation)
        sff_segmentation_downsampling(segmentation)

class ProcessGeometricSegmentationTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        segmentation = self.internal_segmentation

        geometric_segmentation_preprocessing(internal_segmentation=segmentation)

class Preprocessor:
    def __init__(self, preprocessor_input: PreprocessorInput):
        if not preprocessor_input:
            raise ArgumentError("No input parameters are provided")
        self.preprocessor_input = preprocessor_input
        self.intermediate_zarr_structure = None
        self.internal_volume = None
        self.internal_segmentation = None

    def store_internal_volume(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def get_internal_volume(self):
        return self.internal_volume

    def store_internal_segmentation(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def get_internal_segmentation(self):
        return self.internal_segmentation

    def _process_inputs(self, inputs: list[InputT]) -> list[TaskBase]:
        tasks = []
        nii_segmentation_inputs: list[NIISegmentationInput] = []
        mask_segmentation_inputs: list[MaskInput] = []
        for input in inputs:
            if isinstance(input, MAPInput):
                self.store_internal_volume(
                    internal_volume=InternalVolume(
                        intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                        volume_input_path=input.input_path,
                        params_for_storing=self.preprocessor_input.storing_params,
                        volume_force_dtype=self.preprocessor_input.volume.force_volume_dtype,
                        quantize_dtype_str=self.preprocessor_input.volume.quantize_dtype_str,
                        downsampling_parameters=self.preprocessor_input.downsampling,
                        entry_data=self.preprocessor_input.entry_data,
                        quantize_downsampling_levels=self.preprocessor_input.volume.quantize_downsampling_levels,
                    )
                )
                tasks.append(
                    MAPProcessVolumeTask(internal_volume=self.get_internal_volume())
                )
                tasks.append(
                    MAPMetadataCollectionTask(
                        internal_volume=self.get_internal_volume()
                    )
                )
            elif isinstance(input, SFFInput):
                self.store_internal_segmentation(
                    internal_segmentation=InternalSegmentation(
                        intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                        segmentation_input_path=input.input_path,
                        params_for_storing=self.preprocessor_input.storing_params,
                        downsampling_parameters=self.preprocessor_input.downsampling,
                        entry_data=self.preprocessor_input.entry_data,
                    )
                )
                tasks.append(
                    SFFProcessSegmentationTask(
                        internal_segmentation=self.get_internal_segmentation()
                    )
                )
                tasks.append(
                    SFFMetadataCollectionTask(
                        internal_segmentation=self.get_internal_segmentation()
                    )
                )
                tasks.append(
                    SFFAnnotationCollectionTask(
                        internal_segmentation=self.get_internal_segmentation()
                    )
                )
            
            elif isinstance(input, MaskInput):
                mask_segmentation_inputs.append(input)
                # self.store_internal_segmentation(
                #     internal_segmentation=InternalSegmentation(
                #         intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                #         segmentation_input_path=input.input_path,
                #         params_for_storing=self.preprocessor_input.storing_params,
                #         downsampling_parameters=self.preprocessor_input.downsampling,
                #         entry_data=self.preprocessor_input.entry_data,
                #     )
                # )
                # tasks.append(
                #     MaskProcessSegmentationTask(
                #         internal_segmentation=self.get_internal_segmentation()
                #     )
                # )
                # tasks.append(
                #     MaskMetadataCollectionTask(
                #         internal_segmentation=self.get_internal_segmentation()
                #     )
                # )

            elif isinstance(input, OMEZARRInput):
                self.store_internal_volume(
                    internal_volume=InternalVolume(
                        intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                        volume_input_path=input.input_path,
                        params_for_storing=self.preprocessor_input.storing_params,
                        volume_force_dtype=self.preprocessor_input.volume.force_volume_dtype,
                        quantize_dtype_str=self.preprocessor_input.volume.quantize_dtype_str,
                        downsampling_parameters=self.preprocessor_input.downsampling,
                        entry_data=self.preprocessor_input.entry_data,
                        quantize_downsampling_levels=self.preprocessor_input.volume.quantize_downsampling_levels,
                    )
                )
                tasks.append(OMEZARRImageProcessTask(self.get_internal_volume()))
                if check_if_omezarr_has_labels(
                    internal_volume=self.get_internal_volume()
                ):
                    self.store_internal_segmentation(
                        internal_segmentation=InternalSegmentation(
                            intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                            segmentation_input_path=input.input_path,
                            params_for_storing=self.preprocessor_input.storing_params,
                            downsampling_parameters=self.preprocessor_input.downsampling,
                            entry_data=self.preprocessor_input.entry_data,
                        )
                    )
                    tasks.append(
                        OMEZARRLabelsProcessTask(self.get_internal_segmentation())
                    )

                tasks.append(
                    OMEZARRMetadataCollectionTask(
                        internal_volume=self.get_internal_volume()
                    )
                )
                tasks.append(
                    OMEZARRAnnotationsCollectionTask(
                        self.get_internal_volume()
                    )
                )

            elif isinstance(input, GeometricSegmentationInput):
                self.store_internal_segmentation(
                    internal_segmentation=InternalSegmentation(
                        intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                        segmentation_input_path=input.input_path,
                        params_for_storing=self.preprocessor_input.storing_params,
                        downsampling_parameters=self.preprocessor_input.downsampling,
                        entry_data=self.preprocessor_input.entry_data,
                    )
                )
                tasks.append(
                    ProcessGeometricSegmentationTask(self.get_internal_segmentation())
                )
                tasks.append(
                    GeometricSegmentationMetadataCollectionTask(self.get_internal_segmentation())
                )

            elif isinstance(input, NIIVolumeInput):
                self.store_internal_volume(
                    internal_volume=InternalVolume(
                        intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                        volume_input_path=input.input_path,
                        params_for_storing=self.preprocessor_input.storing_params,
                        volume_force_dtype=self.preprocessor_input.volume.force_volume_dtype,
                        quantize_dtype_str=self.preprocessor_input.volume.quantize_dtype_str,
                        downsampling_parameters=self.preprocessor_input.downsampling,
                        entry_data=self.preprocessor_input.entry_data,
                        quantize_downsampling_levels=self.preprocessor_input.volume.quantize_downsampling_levels,
                    )
                )
                tasks.append(
                    NIIProcessVolumeTask(internal_volume=self.get_internal_volume())
                )
                tasks.append(
                    NIIMetadataCollectionTask(
                        internal_volume=self.get_internal_volume()
                    )
                )

            elif isinstance(input, NIISegmentationInput):
                nii_segmentation_inputs.append(input)
                # self.store_internal_segmentation(
                #     internal_segmentation=InternalSegmentation(
                #         intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                #         segmentation_input_path=input.input_path,
                #         params_for_storing=self.preprocessor_input.storing_params,
                #         downsampling_parameters=self.preprocessor_input.downsampling,
                #         entry_data=self.preprocessor_input.entry_data,
                #     )
                # )
                # tasks.append(
                #     NIIProcessSegmentationTask(
                #         internal_segmentation=self.get_internal_segmentation()
                #     )
                # )
                # tasks.append(
                #     NIISegmentationMetadataCollectionTask(
                #         internal_segmentation=self.get_internal_segmentation()
                #     )
                # )
                
            elif isinstance(input, CustomAnnotationsInput):
                tasks.append(CustomAnnotationsCollectionTask(
                    input_path=input.input_path,
                    intermediate_zarr_structure_path=self.intermediate_zarr_structure
                ))

        if (
            self.get_internal_volume()
            and self.preprocessor_input.volume.quantize_dtype_str
        ):
            tasks.append(
                QuantizeInternalVolumeTask(internal_volume=self.get_internal_volume())
            )

        if nii_segmentation_inputs:
            nii_segmentation_input_paths = [i.input_path for i in nii_segmentation_inputs]
            self.store_internal_segmentation(
                internal_segmentation=InternalSegmentation(
                    intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                    segmentation_input_path=nii_segmentation_input_paths,
                    params_for_storing=self.preprocessor_input.storing_params,
                    downsampling_parameters=self.preprocessor_input.downsampling,
                    entry_data=self.preprocessor_input.entry_data,
                )
            )
            tasks.append(
                NIIProcessSegmentationTask(
                    internal_segmentation=self.get_internal_segmentation()
                )
            )
            tasks.append(
                NIISegmentationMetadataCollectionTask(
                    internal_segmentation=self.get_internal_segmentation()
                )
            )

        if mask_segmentation_inputs:
            mask_segmentation_input_paths = [i.input_path for i in mask_segmentation_inputs]
            self.store_internal_segmentation(
                internal_segmentation=InternalSegmentation(
                    intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                    segmentation_input_path=mask_segmentation_input_paths,
                    params_for_storing=self.preprocessor_input.storing_params,
                    downsampling_parameters=self.preprocessor_input.downsampling,
                    entry_data=self.preprocessor_input.entry_data,
                )
            )
            tasks.append(
                MaskProcessSegmentationTask(
                    internal_segmentation=self.get_internal_segmentation()
                )
            )
            tasks.append(
                MaskMetadataCollectionTask(
                    internal_segmentation=self.get_internal_segmentation()
                )
            )

        tasks.append(SaveMetadataTask(self.intermediate_zarr_structure))
        tasks.append(SaveAnnotationsTask(self.intermediate_zarr_structure))

        return tasks

    def _execute_tasks(self, tasks: list[TaskBase]):
        for task in tasks:
            task.execute()

    def _analyse_preprocessor_input(self) -> list[InputT]:
        raw_inputs_list = self.preprocessor_input.inputs.files
        analyzed_inputs: list[InputT] = []

        for input_item in raw_inputs_list:
            if input_item[1] == InputKind.map:
                analyzed_inputs.append(MAPInput(input_path=input_item[0]))
            elif input_item[1] == InputKind.sff:
                analyzed_inputs.append(SFFInput(input_path=input_item[0]))
            elif input_item[1] == InputKind.mask:
                analyzed_inputs.append(MaskInput(input_path=input_item[0]))
            elif input_item[1] == InputKind.omezarr:
                analyzed_inputs.append(OMEZARRInput(input_path=input_item[0]))
            elif input_item[1] == InputKind.geometric_segmentation:
                analyzed_inputs.append(GeometricSegmentationInput(input_path=input_item[0]))
            elif input_item[1] == InputKind.custom_annotations:
                analyzed_inputs.append(CustomAnnotationsInput(input_path=input_item[0]))
            elif input_item[1] == InputKind.application_specific_segmentation:
                sff_path = convert_app_specific_segm_to_sff(input_item[0])
                analyzed_inputs.append(SFFInput(input_path=sff_path))
                # TODO: remove app specific segm file?
            elif input_item[1] == InputKind.nii_volume:
                analyzed_inputs.append(NIIVolumeInput(input_path=input_item[0]))
            elif input_item[1] == InputKind.nii_segmentation:
                analyzed_inputs.append(NIISegmentationInput(input_path=input_item[0]))
        return analyzed_inputs

    def initialization(self):
        self.intermediate_zarr_structure = (
            self.preprocessor_input.working_folder
            / self.preprocessor_input.entry_data.entry_id
        )
        try:
            # delete previous intermediate zarr structure
            shutil.rmtree(self.intermediate_zarr_structure, ignore_errors=True)
            assert (
                self.intermediate_zarr_structure.exists() == False
            ), f"intermediate_zarr_structure: {self.intermediate_zarr_structure} already exists"
            store: zarr.storage.DirectoryStore = zarr.DirectoryStore(
                str(self.intermediate_zarr_structure)
            )
            root = zarr.group(store=store)

            # first initialize metadata and annotations dicts as empty
            root.attrs["metadata_dict"] = {
                "entry_id": {"source_db_name": None, "source_db_id": None},
                "volumes": {
                    "channel_ids": [],
                    # Values of time dimension
                    "time_info": {
                        "kind": "range",
                        "start": None,
                        "end": None,
                        "units": None,
                    },
                    "volume_sampling_info": {
                        # Info about "downsampling dimension"
                        "spatial_downsampling_levels": [],
                        # the only thing with changes with SPATIAL downsampling is box!
                        "boxes": {},
                        # time -> channel_id
                        "descriptive_statistics": {},
                        "time_transformations": [],
                        "source_axes_units": None,
                    },
                    "original_axis_order": None,
                },
                "segmentation_lattices": {
                    "segmentation_lattice_ids": [],
                    "segmentation_sampling_info": {},
                    "channel_ids": {},
                    "time_info": {},
                },
                "segmentation_meshes": {
                    "mesh_component_numbers": {},
                    "detail_lvl_to_fraction": {},
                },
            }

            root.attrs["annotations_dict"] = {
                "entry_id": {"source_db_name": None, "source_db_id": None},
                "segmentation_lattices": [],
                "details": None,
                "name": None,
                "volume_channels_annotations": [],
                "non_segment_annotation": {}
            }

            if self.preprocessor_input.add_segmentation_to_entry:
                db = FileSystemVolumeServerDB(self.preprocessor_input.db_path)
                metadata_file_path: Path = (
                    db._path_to_object(namespace=self.preprocessor_input.entry_data.source_db,
                                        key=self.preprocessor_input.entry_data.entry_id) / GRID_METADATA_FILENAME
                )
                with open(metadata_file_path.resolve(), "r", encoding="utf-8") as f:
                    # reads into dict
                    read_json_of_metadata: dict = json.load(f)

                root.attrs["metadata_dict"] = read_json_of_metadata
                print('Adding segmentation to existing entry: Prefilled metadata dict is read from existing entry')
            if self.preprocessor_input.add_custom_annotations:
                db = FileSystemVolumeServerDB(self.preprocessor_input.db_path)
                annotations_file_path: Path = (
                    db._path_to_object(namespace=self.preprocessor_input.entry_data.source_db,
                                        key=self.preprocessor_input.entry_data.entry_id) / ANNOTATION_METADATA_FILENAME
                )

                with open(annotations_file_path.resolve(), "r", encoding="utf-8") as f:
                    # reads into dict
                    read_json_of_annotations: dict = json.load(f)

                root.attrs["annotations_dict"] = read_json_of_annotations
                print('Adding custom annotations to existing entry: Prefilled annotations dict is read from existing entry')
            
        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
            raise e

        # self._analyse_preprocessor_input()

    def preprocessing(self):
        inputs = self._analyse_preprocessor_input()
        tasks = self._process_inputs(inputs)
        self._execute_tasks(tasks)
        return

    async def store_to_db(self):
        new_db_path = Path(self.preprocessor_input.db_path)
        if new_db_path.is_dir() == False:
            new_db_path.mkdir()

        db = FileSystemVolumeServerDB(new_db_path, store_type="zip")
        if self.preprocessor_input.add_segmentation_to_entry:
            await db.add_segmentation_to_entry(
                namespace=self.preprocessor_input.entry_data.source_db,
                key=self.preprocessor_input.entry_data.entry_id,
                temp_store_path=self.intermediate_zarr_structure,
            )
        elif self.preprocessor_input.add_custom_annotations:
            await db.add_custom_annotations(
                namespace=self.preprocessor_input.entry_data.source_db,
                key=self.preprocessor_input.entry_data.entry_id,
                temp_store_path=self.intermediate_zarr_structure,
            )
        else:
            await db.store(
                namespace=self.preprocessor_input.entry_data.source_db,
                key=self.preprocessor_input.entry_data.entry_id,
                temp_store_path=self.intermediate_zarr_structure,
            )

        print("Data stored to db")


# How it supposed to work:


def _convert_cli_args_to_preprocessor_input(cli_arguments) -> PreprocessorInput:
    # TODO: implement
    # return DEFAULT_PREPROCESSOR_INPUT
    return OME_ZARR_PREPROCESSOR_INPUT


async def main_preprocessor(
    quantize_dtype_str: typing.Optional[QuantizationDtype],
    quantize_downsampling_levels: typing.Optional[str],
    force_volume_dtype: typing.Optional[str],
    max_size_per_channel_mb: typing.Optional[float],
    min_downsampling_level: typing.Optional[int],
    max_downsampling_level: typing.Optional[int],
    entry_id: str,
    source_db: str,
    source_db_id: str,
    source_db_name: str,
    working_folder: Path,
    db_path: Path,
    input_paths: list[Path],
    input_kinds: list[InputKind],
    min_size_per_channel_mb: typing.Optional[float] = 5,
    add_segmentation_to_entry: typing.Optional[bool] = False,
    add_custom_annotations: typing.Optional[bool] = False,
):
    if quantize_downsampling_levels:
        quantize_downsampling_levels = quantize_downsampling_levels.split(" ")
        quantize_downsampling_levels = tuple(
            [int(level) for level in quantize_downsampling_levels]
        )

    preprocessor_input = PreprocessorInput(
        inputs=Inputs(files=[]),
        volume=VolumeParams(
            quantize_dtype_str=quantize_dtype_str,
            quantize_downsampling_levels=quantize_downsampling_levels,
            force_volume_dtype=force_volume_dtype,
        ),
        downsampling=DownsamplingParams(
            min_size_per_channel_mb=min_size_per_channel_mb,
            max_size_per_channel_mb=max_size_per_channel_mb,
            min_downsampling_level=min_downsampling_level,
            max_downsampling_level=max_downsampling_level
        ),
        entry_data=EntryData(
            entry_id=entry_id,
            source_db=source_db,
            source_db_id=source_db_id,
            source_db_name=source_db_name,
        ),
        working_folder=Path(working_folder),
        storing_params=StoringParams(),
        db_path=Path(db_path),
        add_segmentation_to_entry=add_segmentation_to_entry,
        add_custom_annotations=add_custom_annotations
    )

    for input_path, input_kind in zip(input_paths, input_kinds):
        preprocessor_input.inputs.files.append((Path(input_path), input_kind))

    # cli_arguments = None
    # preprocessor_input: PreprocessorInput = _convert_cli_args_to_preprocessor_input(cli_arguments)
    preprocessor = Preprocessor(preprocessor_input)
    preprocessor.initialization()
    preprocessor.preprocessing()
    await preprocessor.store_to_db()


def main(
    quantize_dtype_str: Annotated[
        typing.Optional[QuantizationDtype], typer.Option(None)
    ] = None,
    quantize_downsampling_levels: Annotated[
        typing.Optional[str], typer.Option(None, help="Space-separated list of numbers")
    ] = None,
    force_volume_dtype: Annotated[typing.Optional[str], typer.Option(None)] = None,
    max_size_per_channel_mb: Annotated[typing.Optional[float], typer.Option(None)] = None,
    min_size_per_channel_mb: Annotated[typing.Optional[float], typer.Option(None)] = 5,
    min_downsampling_level: Annotated[typing.Optional[int], typer.Option(None)] = None,
    max_downsampling_level: Annotated[typing.Optional[int], typer.Option(None)] = None,
    entry_id: str = typer.Option(default=...),
    source_db: str = typer.Option(default=...),
    source_db_id: str = typer.Option(default=...),
    source_db_name: str = typer.Option(default=...),
    working_folder: Path = typer.Option(default=...),
    db_path: Path = typer.Option(default=...),
    input_path: list[Path] = typer.Option(default=...),
    input_kind: list[InputKind] = typer.Option(default=...),
    add_segmentation_to_entry: bool = typer.Option(default=False),
    add_custom_annotations: bool = typer.Option(default=False),
):
    asyncio.run(
        main_preprocessor(
            entry_id=entry_id,
            source_db=source_db,
            source_db_id=source_db_id,
            source_db_name=source_db_name,
            working_folder=working_folder,
            db_path=db_path,
            input_paths=input_path,
            input_kinds=input_kind,
            quantize_dtype_str=quantize_dtype_str,
            quantize_downsampling_levels=quantize_downsampling_levels,
            force_volume_dtype=force_volume_dtype,
            max_size_per_channel_mb=max_size_per_channel_mb,
            min_size_per_channel_mb=min_size_per_channel_mb,
            min_downsampling_level=min_downsampling_level,
            max_downsampling_level=max_downsampling_level,
            add_segmentation_to_entry=add_segmentation_to_entry,
            add_custom_annotations=add_custom_annotations
        )
    )


if __name__ == "__main__":
    # solutions how to run it async - two last https://github.com/tiangolo/typer/issues/85
    # currently using last one
    typer.run(main)


# NOTE: for testing:
# python preprocessor/preprocessor/preprocess.py --input-path temp/v2_temp_static_entry_files_dir/idr/idr-6001247/6001247.zarr --input-kind omezarr
# python preprocessor/preprocessor/preprocess.py --input-path test-data/preprocessor/sample_volumes/emdb_sff/EMD-1832.map --input-kind map --input-path test-data/preprocessor/sample_segmentations/emdb_sff/emd_1832.hff --input-kind sff
