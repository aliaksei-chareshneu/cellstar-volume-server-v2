
from pyometiff import OMETIFFReader



from pathlib import Path


def main(pathes: list[Path]):
    for p in pathes:
        print(f'Opening {p.name}')
        reader = OMETIFFReader(fpath=p)
        img_array, metadata, xml_metadata = reader.read()
        

        # print
        # p.name
        # DimOrder BF Array
        # Sizes BF
        # img_array_shape
        print(p.name)
        print(metadata['DimOrder BF'])

        # The following two are always same
        print(metadata['DimOrder'])
        print(metadata['DimOrder BF Array'])
        
        print(metadata['Sizes BF'])
        print(img_array.shape)
        print('---')

if __name__ == '__main__':
    DIR_PATH = Path('test-data/preprocessor/sample_ome_tiff')
    PATHES = [
        Path('test-data/preprocessor/sample_ome_tiff/multi-channel-4D-series.ome.tif'),
        Path('test-data/preprocessor/sample_ome_tiff/00001_01.ome.tiff'),
        Path('test-data/preprocessor/sample_ome_tiff/tubhiswt_C0_TP4.ome.tif'),
        Path('test-data/preprocessor/sample_ome_tiff/z-series.ome.tif'),
        Path('preprocessor/temp/allencel_datasets/CellId_230741/crop_raw/7922e74b69b77d6b51ea5f1627418397ab6007105a780913663ce1344905db5c_raw.ome.tif'),
        Path('preprocessor/temp/allencel_datasets/CellId_230741/crop_seg/a9a2aa179450b1819f0dfc4d22411e6226f22e3c88f7a6c3f593d0c2599c2529_segmentation.ome.tif')
    ]
    # PATHES = []
    # for p in DIR_PATH.rglob('*.tif'):
    #     PATHES.append(p)
    # print(PATHES)
    main(PATHES)