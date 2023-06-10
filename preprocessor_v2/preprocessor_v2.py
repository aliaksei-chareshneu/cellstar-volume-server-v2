from argparse import ArgumentError
import logging
from pathlib import Path
from input_data_model import PreprocessorInput
import zarr
from preprocessor.src.tools.convert_app_specific_segm_to_sff.convert_app_specific_segm_to_sff import convert_app_specific_segm_to_sff

from preprocessor_v2.input_data_model import InputCase, InputKind

class Preprocessor():
    def __init__(self, preprocessor_input: PreprocessorInput):
        if not preprocessor_input:
            raise ArgumentError('No input parameters are provided')
        self.preprocessor_input = preprocessor_input
        self.intermediate_zarr_structure = None
        self.volume_input_path = None
        self.segmentation_input_path = None
        self.omezarr_input_path = None
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

        if volume_input and segmentation_input:
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
            self.omezarr_input_path = omezarr_input
        elif ometiff_input:
            self.input_case = InputCase.ometiff
            self.ometiff_input_path = ometiff_input
        else:
            raise Exception('Input case is not supported')

    def initialization(self):
        self.intermediate_zarr_structure = self.preprocessor_input.working_folder / self.preprocessor_input.entry_data.entry_id
        try:
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
            # preprocess volume, do downsamplings afterwards
            self._volume_map_preprocessing()
        elif self.input_case == InputCase.map_and_sff:
            # preprocess volume, preprocess sff, do downsamplings on both, 
            # run annotations preprocessing
            self._volume_map_preprocessing()
            self._sff_preprocessing()
            self._annotation_preprocessing()
        elif self.input_case == InputCase.ometiff:
            # preprocess ometiff (specific approach, just volume), do downsamplings on volume
            self._preprocess_ometiff()
        elif self.input_case == InputCase.omezarr:
            # preprocess omezarr (can be just volume, or volume and segmentation), check if there are downsamplings
            # most likely yes, so don't do downsamplings
            self._preprocess_omezarr()

    def _volume_map_preprocessing(self):
        # 1. normalize axis order
        # 2. compute metadata
        # 3. add volume data to intermediate zarr structure
        
    
    def _sff_preprocessing(self):

    def _annotation_preprocessing(self):

    def _preprocess_ometiff(self):

    def _preprocess_omezarr(self):