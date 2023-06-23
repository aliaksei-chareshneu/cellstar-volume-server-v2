from argparse import ArgumentError
import logging
from pathlib import Path
import shutil
import numpy as np
import zarr
from preprocessor.src.tools.convert_app_specific_segm_to_sff.convert_app_specific_segm_to_sff import convert_app_specific_segm_to_sff
import mrcfile
from preprocessor_v2.preprocessor.flows.common import temp_save_metadata
from preprocessor_v2.preprocessor.flows.constants import ANNOTATION_METADATA_FILENAME, GRID_METADATA_FILENAME
from preprocessor_v2.preprocessor.flows.segmentation.extract_annotations_from_sff_segmentation import extract_annotations_from_sff_segmentation
from preprocessor_v2.preprocessor.flows.segmentation.extract_metadata_from_sff_segmentation import extract_metadata_from_sff_segmentation
from preprocessor_v2.preprocessor.flows.segmentation.helper_methods import check_if_omezarr_has_labels
from preprocessor_v2.preprocessor.flows.segmentation.ome_zarr_labels_preprocessing import ome_zarr_labels_preprocessing
from preprocessor_v2.preprocessor.flows.segmentation.segmentation_downsampling import sff_segmentation_downsampling
from preprocessor_v2.preprocessor.flows.segmentation.sff_preprocessing import sff_preprocessing
from preprocessor_v2.preprocessor.flows.volume.extract_metadata_from_map import extract_metadata_from_map
from preprocessor_v2.preprocessor.flows.volume.map_preprocessing import map_preprocessing
from preprocessor_v2.preprocessor.flows.volume.ome_zarr_image_preprocessing import ome_zarr_image_preprocessing
from preprocessor_v2.preprocessor.flows.volume.volume_downsampling import volume_downsampling

from preprocessor_v2.preprocessor.model.input import DEFAULT_PREPROCESSOR_INPUT, OME_ZARR_PREPROCESSOR_INPUT, InputCase, InputKind, Inputs, PreprocessorInput
from preprocessor_v2.preprocessor.model.segmentation import InternalSegmentation
from preprocessor_v2.preprocessor.model.volume import InternalVolume


class Preprocessor():
    def __init__(self, preprocessor_input: PreprocessorInput):
        if not preprocessor_input:
            raise ArgumentError('No input parameters are provided')
        self.preprocessor_input = preprocessor_input
        self.intermediate_zarr_structure = None
        self.volume_input_path = None
        self.segmentation_input_path = None
        # self.omezarr_input_path = None
        self.ometiff_input_path = None
        self.input_case = None

    def _analyse_preprocessor_input(self):
        # find volume input file, find segmentation input file
        # check if files list is ok (e.g. if there is just one map), if not ambigous
        inputs_list = self.preprocessor_input.inputs.files
        volume_input = None
        segmentation_input = None
        application_specific_segmentation_input = None
        omezarr_input = None
        ometiff_input = None
        for input_item in inputs_list:
            if input_item[1] == InputKind.map:
                if not volume_input:
                    volume_input = input_item[0]
                else:
                    raise Exception('There should be just one volume map in input')
            
            elif input_item[1] == InputKind.sff:
                if not segmentation_input:
                    segmentation_input = input_item[0]
                else:
                    raise Exception('There should be just one SFF in input')
            
            elif input_item[1] == InputKind.application_specific_segmentation:
                if not application_specific_segmentation_input:
                    application_specific_segmentation_input = input_item[0]
                else:
                    raise Exception('There should be just one application specific segmentation in input')
            
            elif input_item[1] == InputKind.omezarr:
                if not omezarr_input:
                    omezarr_input = input_item[0]
                else:
                    raise Exception('There should be just one ome zarr in input')
            
            elif input_item[1] == InputKind.ometiff:
                if not ometiff_input:
                    ometiff_input = input_item[0]
                else:
                    raise Exception('There should be just one ome tiff file in input')
                
            # TODO: masks
            # TODO: custom annotations

        if volume_input:
            if segmentation_input:
                self.input_case = InputCase.map_and_sff
                self.volume_input_path = volume_input
                self.segmentation_input_path = segmentation_input
            elif application_specific_segmentation_input:
                self.input_case = InputCase.map_and_sff
                self.volume_input_path = volume_input
                self.segmentation_input_path = convert_app_specific_segm_to_sff(application_specific_segmentation_input)
            else:
                self.input_case = InputCase.map_only
                self.volume_input_path = volume_input
        elif omezarr_input:
            self.input_case = InputCase.omezarr
            # self.omezarr_input_path = omezarr_input
            self.volume_input_path = omezarr_input
            self.segmentation_input_path = omezarr_input
        elif ometiff_input:
            self.input_case = InputCase.ometiff
            self.ometiff_input_path = ometiff_input
        else:
            raise Exception('Input case is not supported')

    def initialization(self):
        self.intermediate_zarr_structure = self.preprocessor_input.working_folder / self.preprocessor_input.entry_data.entry_id
        try:
            # delete previous intermediate zarr structure
            shutil.rmtree(self.intermediate_zarr_structure, ignore_errors=True)
            assert self.intermediate_zarr_structure.exists() == False, \
                f'intermediate_zarr_structure: {self.intermediate_zarr_structure} already exists'
            store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(self.intermediate_zarr_structure))
        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
            raise e

        self._analyse_preprocessor_input()

    def preprocessing(self):
        # in each case specific set of functions is called
        if self.input_case == InputCase.map_only:
            # preprocess volume
            volume = InternalVolume(
                intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                volume_input_path=self.volume_input_path,
                params_for_storing=self.preprocessor_input.storing_params,
                volume_force_dtype=preprocessor_input.volume.force_volume_dtype,
                quantize_dtype_str=preprocessor_input.volume.quantize_dtype_str,
                downsampling_parameters=preprocessor_input.downsampling,
                entry_data=preprocessor_input.entry_data,
            )

            map_preprocessing(volume)
            # in processing part do
            volume_downsampling(volume)
            
            metadata_dict = extract_metadata_from_map(internal_volume=volume)

            temp_save_metadata(metadata_dict, GRID_METADATA_FILENAME, self.intermediate_zarr_structure)

        elif self.input_case == InputCase.map_and_sff:
            # preprocess volume, preprocess sff 
            # run annotations preprocessing
            # sff_preprocessing()
            # annotation_preprocessing()
            volume = InternalVolume(
                intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                volume_input_path=self.volume_input_path,
                params_for_storing=self.preprocessor_input.storing_params,
                volume_force_dtype=preprocessor_input.volume.force_volume_dtype,
                quantize_dtype_str=preprocessor_input.volume.quantize_dtype_str,
                downsampling_parameters=preprocessor_input.downsampling,
                entry_data=preprocessor_input.entry_data,
            )

            map_preprocessing(volume)
            # in processing part do
            volume_downsampling(volume)

            segmentation = InternalSegmentation(
                intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                segmentation_input_path=self.segmentation_input_path,
                params_for_storing=self.preprocessor_input.storing_params,
                downsampling_parameters=self.preprocessor_input.downsampling,
                entry_data=preprocessor_input.entry_data
            )

            sff_preprocessing(segmentation)

            sff_segmentation_downsampling(segmentation)

            metadata_dict = extract_metadata_from_map(internal_volume=volume)
            metadata_dict = extract_metadata_from_sff_segmentation(metadata_dict=metadata_dict, internal_segmentation=segmentation)
            
            temp_save_metadata(metadata_dict, GRID_METADATA_FILENAME, self.intermediate_zarr_structure)
            
            annotations_dict = extract_annotations_from_sff_segmentation(internal_segmentation=segmentation)
            temp_save_metadata(annotations_dict, ANNOTATION_METADATA_FILENAME, self.intermediate_zarr_structure)

        elif self.input_case == InputCase.ometiff:
            pass
        # TODO: remember that for volume and segmentation processing,
        # original data is _volume_data[1], not [0]
        # TODO: later
            # preprocess ometiff (specific approach, just volume)
            # preprocess_ometiff()
        elif self.input_case == InputCase.omezarr:
            volume = InternalVolume(
                intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                volume_input_path=self.volume_input_path,
                params_for_storing=self.preprocessor_input.storing_params,
                volume_force_dtype=preprocessor_input.volume.force_volume_dtype,
                quantize_dtype_str=preprocessor_input.volume.quantize_dtype_str,
                downsampling_parameters=preprocessor_input.downsampling,
                entry_data=preprocessor_input.entry_data,
            )

            ome_zarr_image_preprocessing(internal_volume=volume)

            if check_if_omezarr_has_labels(internal_volume=volume):
                segmentation = InternalSegmentation(
                    intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                    segmentation_input_path=self.segmentation_input_path,
                    params_for_storing=self.preprocessor_input.storing_params,
                    downsampling_parameters=self.preprocessor_input.downsampling,
                    entry_data=preprocessor_input.entry_data
                )
                ome_zarr_labels_preprocessing(internal_segmentation=segmentation)
            
            # preprocess omezarr (can be just volume, or volume and segmentation), check if there are downsamplings
            # most likely yes
            # preprocess_omezarr()

        return self.intermediate_zarr_structure

    





# How it supposed to work:

def _convert_cli_args_to_preprocessor_input(cli_arguments) -> PreprocessorInput:
    # TODO: implement
    # return DEFAULT_PREPROCESSOR_INPUT
    return OME_ZARR_PREPROCESSOR_INPUT

if __name__ == '__main__':
    cli_arguments = None
    preprocessor_input: PreprocessorInput = _convert_cli_args_to_preprocessor_input(cli_arguments)
    preprocessor = Preprocessor(preprocessor_input)
    preprocessor.initialization()
    intermediate_zarr_structure = preprocessor.preprocessing()

