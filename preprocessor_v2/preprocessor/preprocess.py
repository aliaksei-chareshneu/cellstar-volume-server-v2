from argparse import ArgumentError
import asyncio
import logging
from pathlib import Path
import shutil
import typing
import numpy as np
from pydantic import BaseModel
import zarr
from db.file_system.db import FileSystemVolumeServerDB
import mrcfile
from db.models import Metadata
from preprocessor_v2.preprocessor.flows.common import open_zarr_structure_from_path, temp_save_metadata
from preprocessor_v2.preprocessor.flows.constants import ANNOTATION_METADATA_FILENAME, GRID_METADATA_FILENAME
from preprocessor_v2.preprocessor.flows.segmentation.extract_annotations_from_sff_segmentation import extract_annotations_from_sff_segmentation
from preprocessor_v2.preprocessor.flows.segmentation.extract_metadata_from_sff_segmentation import extract_metadata_from_sff_segmentation
from preprocessor_v2.preprocessor.flows.segmentation.helper_methods import check_if_omezarr_has_labels
from preprocessor_v2.preprocessor.flows.segmentation.ome_zarr_labels_preprocessing import ome_zarr_labels_preprocessing
from preprocessor_v2.preprocessor.flows.segmentation.segmentation_downsampling import sff_segmentation_downsampling
from preprocessor_v2.preprocessor.flows.segmentation.sff_preprocessing import sff_preprocessing
from preprocessor_v2.preprocessor.flows.volume.extract_metadata_from_map import extract_metadata_from_map
from preprocessor_v2.preprocessor.flows.volume.extract_omezarr_annotations import extract_omezarr_annotations
from preprocessor_v2.preprocessor.flows.volume.extract_omezarr_metadata import extract_ome_zarr_metadata
from preprocessor_v2.preprocessor.flows.volume.map_preprocessing import map_preprocessing
from preprocessor_v2.preprocessor.flows.volume.ome_zarr_image_preprocessing import ome_zarr_image_preprocessing
from preprocessor_v2.preprocessor.flows.volume.quantize_internal_volume import quantize_internal_volume
from preprocessor_v2.preprocessor.flows.volume.volume_downsampling import volume_downsampling

from preprocessor_v2.preprocessor.model.input import DEFAULT_PREPROCESSOR_INPUT, OME_ZARR_PREPROCESSOR_INPUT, DownsamplingParams, EntryData, InputCase, InputKind, Inputs, PreprocessorInput, StoringParams, VolumeParams
from preprocessor_v2.preprocessor.model.segmentation import InternalSegmentation
from preprocessor_v2.preprocessor.model.volume import InternalVolume
import typer

class InputT(BaseModel):
    input_path: Path

class MAPInput(InputT):
    pass

class SFFInput(InputT):
    pass

class OMEZARRInput(InputT):
    pass

class TaskBase(typing.Protocol):
    def execute(self) -> None:
        ...

class QuantizeInternalVolumeTask(TaskBase):
    def __init__(
            self,
            internal_volume: InternalVolume
            ):
        self.internal_volume = internal_volume
    
    def execute(self) -> None:
        quantize_internal_volume(internal_volume=self.internal_volume)

class SaveAnnotationsTask(TaskBase):
    def __init__(
            self,
            intermediate_zarr_structure_path: Path
    ):
        self.intermediate_zarr_structure_path = intermediate_zarr_structure_path

    def execute(self) -> None:
        root = open_zarr_structure_from_path(self.intermediate_zarr_structure_path)
        temp_save_metadata(
            root.attrs['annotations_dict'], ANNOTATION_METADATA_FILENAME, self.intermediate_zarr_structure_path
        )

class SaveMetadataTask(TaskBase):
    def __init__(
            self,
            intermediate_zarr_structure_path: Path
    ):
        self.intermediate_zarr_structure_path = intermediate_zarr_structure_path

    def execute(self) -> None:
        root = open_zarr_structure_from_path(self.intermediate_zarr_structure_path)
        temp_save_metadata(
            root.attrs['metadata_dict'], GRID_METADATA_FILENAME, self.intermediate_zarr_structure_path
        )
        
class SFFAnnotationCollectionTask(TaskBase):
    def __init__(
            self,
            internal_segmentation: InternalSegmentation
            ):
        self.internal_segmentation = internal_segmentation
    
    def execute(self) -> None:
        annotations_dict = extract_annotations_from_sff_segmentation(internal_segmentation=self.internal_segmentation)

class MAPMetadataCollectionTask(TaskBase):
    def __init__(
            self,
            internal_volume: InternalVolume
            ):
        self.internal_volume = internal_volume
    
    def execute(self) -> None:
        volume = self.internal_volume
        metadata_dict = extract_metadata_from_map(internal_volume=volume)

class OMEZARRAnnotationsCollectionTask(TaskBase):
    def __init__(
            self,
            internal_segmentation: InternalSegmentation
            ):
        self.internal_segmentation = internal_segmentation
    
    def execute(self) -> None:
        annotations_dict = extract_omezarr_annotations(internal_segmentation=self.internal_segmentation)


class OMEZARRMetadataCollectionTask(TaskBase):
    def __init__(
            self,
            internal_volume: InternalVolume
            ):
        self.internal_volume = internal_volume
    
    def execute(self) -> None:
        metadata_dict = extract_ome_zarr_metadata(internal_volume=self.internal_volume)

class OMEZARRImageProcessTask(TaskBase):
    def __init__(
            self,
            internal_volume: InternalVolume
            ):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        ome_zarr_image_preprocessing(self.internal_volume)

class OMEZARRLabelsProcessTask(TaskBase):
    def __init__(
            self,
            internal_segmentation: InternalSegmentation
            ):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        ome_zarr_labels_preprocessing(internal_segmentation=self.internal_segmentation)

class SFFMetadataCollectionTask(TaskBase):
    def __init__(
            self,
            internal_segmentation: InternalSegmentation
            ):
        self.internal_segmentation = internal_segmentation
    
    def execute(self) -> None:
        metadata_dict = extract_metadata_from_sff_segmentation(internal_segmentation=self.internal_segmentation)

class MAPProcessVolumeTask(TaskBase):
    def __init__(
            self,
            internal_volume: InternalVolume
            ):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        volume = self.internal_volume

        map_preprocessing(volume)
        # in processing part do
        volume_downsampling(volume)
        
         
class SFFProcessSegmentationTask(TaskBase):
    def __init__(
            self,
            internal_segmentation: InternalSegmentation
            ):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        segmentation = self.internal_segmentation

        sff_preprocessing(segmentation)

        sff_segmentation_downsampling(segmentation)

class Preprocessor():
    def __init__(self, preprocessor_input: PreprocessorInput):
        if not preprocessor_input:
            raise ArgumentError('No input parameters are provided')
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
                        quantize_downsampling_levels=self.preprocessor_input.volume.quantize_downsampling_levels
                    )
                )
                tasks.append(MAPProcessVolumeTask(
                    internal_volume=self.get_internal_volume()
                ))
                tasks.append(MAPMetadataCollectionTask(internal_volume=self.get_internal_volume()))
            elif isinstance(input, SFFInput):
                self.store_internal_segmentation(
                    internal_segmentation=InternalSegmentation(
                        intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                        segmentation_input_path=input.input_path,
                        params_for_storing=self.preprocessor_input.storing_params,
                        downsampling_parameters=self.preprocessor_input.downsampling,
                        entry_data=self.preprocessor_input.entry_data
                    )
                )
                tasks.append(SFFProcessSegmentationTask(
                    internal_segmentation=self.get_internal_segmentation()
                ))
                tasks.append(SFFMetadataCollectionTask(internal_segmentation=self.get_internal_segmentation()))
                tasks.append(SFFAnnotationCollectionTask(internal_segmentation=self.get_internal_segmentation()))

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
                        quantize_downsampling_levels=self.preprocessor_input.volume.quantize_downsampling_levels
                    )
                )
                tasks.append(OMEZARRImageProcessTask(self.get_internal_volume()))
                if check_if_omezarr_has_labels(internal_volume=self.get_internal_volume()):
                    self.store_internal_segmentation(
                        internal_segmentation=InternalSegmentation(
                            intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                            segmentation_input_path=input.input_path,
                            params_for_storing=self.preprocessor_input.storing_params,
                            downsampling_parameters=self.preprocessor_input.downsampling,
                            entry_data=self.preprocessor_input.entry_data
                        )
                    )
                    tasks.append(OMEZARRLabelsProcessTask(self.get_internal_segmentation()))
                    tasks.append(OMEZARRAnnotationsCollectionTask(self.get_internal_segmentation()))

                tasks.append(OMEZARRMetadataCollectionTask(internal_volume=self.get_internal_volume()))
                

        # TODO: quantization
        if self.get_internal_volume() and self.preprocessor_input.volume.quantize_dtype_str:
            tasks.append(QuantizeInternalVolumeTask(internal_volume=self.get_internal_volume()))

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
            elif input_item[1] == InputKind.omezarr:
                analyzed_inputs.append(OMEZARRInput(input_path=input_item[0]))
                # TODO: application specific
                # TODO: custom annotations

        return analyzed_inputs

    def initialization(self):
        self.intermediate_zarr_structure = self.preprocessor_input.working_folder / self.preprocessor_input.entry_data.entry_id
        try:
            # delete previous intermediate zarr structure
            shutil.rmtree(self.intermediate_zarr_structure, ignore_errors=True)
            assert self.intermediate_zarr_structure.exists() == False, \
                f'intermediate_zarr_structure: {self.intermediate_zarr_structure} already exists'
            store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(self.intermediate_zarr_structure))
            root = zarr.group(store=store)
            root.attrs['metadata_dict'] = {
                'entry_id': {
                    'source_db_name': None,
                    'source_db_id': None

                },
                'volumes': {
                    'channel_ids': [],
                    # Values of time dimension
                    'time_info': {
                        'kind': "range",
                        'start': None,
                        'end': None,
                        'units': None
                    },
                    'volume_sampling_info': {
                        # Info about "downsampling dimension"
                        'spatial_downsampling_levels': [],
                        # the only thing with changes with SPATIAL downsampling is box!
                        'boxes': {},
                        # time -> channel_id
                        'descriptive_statistics': {},
                        'time_transformations': [],
                        'source_axes_units': None
                    },
                    'original_axis_order': None
                },
                'segmentation_lattices': {
                    'segmentation_lattice_ids': [],
                    'segmentation_sampling_info': {},
                    'channel_ids': {},
                    'time_info': {}
                },
                'segmentation_meshes': {
                    'mesh_component_numbers': {},
                    'detail_lvl_to_fraction': {}
                }
            }

            root.attrs['annotations_dict'] = {
                'entry_id': {
                    'source_db_name': None,
                    'source_db_id': None
                },
                'segmentation_lattices': [],
                'details': None,
                'name': None,
                'volume_channels_annotations': []
            }
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

        db = FileSystemVolumeServerDB(new_db_path, store_type='zip')
        await db.store(namespace=self.preprocessor_input.entry_data.source_db,
            key=self.preprocessor_input.entry_data.entry_id,
            temp_store_path=self.intermediate_zarr_structure)
        
        print('Data stored to db')






# How it supposed to work:

def _convert_cli_args_to_preprocessor_input(cli_arguments) -> PreprocessorInput:
    # TODO: implement
    # return DEFAULT_PREPROCESSOR_INPUT
    return OME_ZARR_PREPROCESSOR_INPUT

async def main_preprocessor(
        entry_id: str,
        source_db: str,
        source_db_id: str,
        source_db_name: str,
        working_folder: Path,
        db_path: Path,
        input_paths: list[Path],
        input_kinds: list[InputKind],
):
    preprocessor_input = PreprocessorInput(
        inputs=Inputs(
            files=[
            ]
        ),
        volume=VolumeParams(
            # quantize_dtype_str=quantize_dtype_str,
            # quantize_downsampling_levels=quantize_downsampling_levels,
            # force_volume_dtype=force_volume_dtype
        ),
        downsampling=DownsamplingParams(),
        entry_data=EntryData(
            entry_id=entry_id,
            source_db=source_db,
            source_db_id=source_db_id,
            source_db_name=source_db_name
        ),
        working_folder=Path(working_folder),
        storing_params=StoringParams(),
        db_path=Path(db_path)
    )

    for input_path, input_kind in zip(input_paths, input_kinds):
        preprocessor_input.inputs.files.append((
            Path(input_path),
            input_kind
        ))



    # cli_arguments = None
    # preprocessor_input: PreprocessorInput = _convert_cli_args_to_preprocessor_input(cli_arguments)
    preprocessor = Preprocessor(preprocessor_input)
    preprocessor.initialization()
    preprocessor.preprocessing()
    await preprocessor.store_to_db()

def main(
        entry_id: str = typer.Option(default=...),
        source_db: str = typer.Option(default=...),
        source_db_id: str = typer.Option(default=...),
        source_db_name: str = typer.Option(default=...),
        working_folder: Path = typer.Option(default=...),
        db_path: Path = typer.Option(default=...),
        # TODO: make these two required
        input_path: list[Path] = typer.Option(default=...),
        input_kind: list[InputKind] = typer.Option(default=...),
        ):
    asyncio.run(main_preprocessor(
        entry_id=entry_id,
        source_db=source_db,
        source_db_id=source_db_id,
        source_db_name=source_db_name,
        working_folder=working_folder,
        db_path=db_path,
        input_paths=input_path,
        input_kinds=input_kind,
        ))

if __name__ == '__main__':
    # solutions how to run it async - two last https://github.com/tiangolo/typer/issues/85
    # currently using last one
    typer.run(main)


# NOTE: for testing:
# python preprocessor_v2/preprocessor/preprocess.py --input-path temp/v2_temp_static_entry_files_dir/idr/idr-6001247/6001247.zarr --input-kind omezarr
# python preprocessor_v2/preprocessor/preprocess.py --input-path test-data/preprocessor/sample_volumes/emdb_sff/EMD-1832.map --input-kind map --input-path test-data/preprocessor/sample_segmentations/emdb_sff/emd_1832.hff --input-kind sff
