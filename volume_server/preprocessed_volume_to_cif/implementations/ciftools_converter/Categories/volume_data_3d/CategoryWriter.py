import numpy as np
from ciftools.binary.encoding import BinaryCIFEncoder, DataType, DataTypeEnum
from ciftools.binary.encoding.base.cif_encoder_base import CIFEncoderBase
from ciftools.binary.encoding.impl.encoders.byte_array import ByteArrayCIFEncoder
from ciftools.binary.encoding.impl.encoders.interval_quantization import IntervalQuantizationCIFEncoder
from ciftools.writer.base import CategoryWriter, CategoryWriterProvider, FieldDesc

from volume_server.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories._writer import CategoryDesc, \
    CategoryDescImpl
from volume_server.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories.volume_data_3d.Fields import Fields_VolumeData3d


class CategoryWriter_VolumeData3d(CategoryWriter):
    def __init__(self, ctx: np.ndarray, count: int, category_desc: CategoryDesc):
        self.data = ctx
        self.count = count
        self.desc = category_desc


class CategoryWriterProvider_VolumeData3d(CategoryWriterProvider):
    def _decide_encoder(self, ctx: np.ndarray) -> tuple[BinaryCIFEncoder, np.dtype]:
        data_type = DataType.from_dtype(ctx.dtype)

        encoders: list[CIFEncoderBase] = [ByteArrayCIFEncoder()]

        if data_type == DataTypeEnum.Float32 or data_type == DataTypeEnum.Int16:
            data_min: int = ctx.min(initial=ctx[0])
            data_max: int = ctx.max(initial=ctx[0])
            interval_quantization = IntervalQuantizationCIFEncoder(data_min, data_max, 255, DataTypeEnum.Uint8)
            encoders.insert(0, interval_quantization)
            typed_array = DataType.to_dtype(DataTypeEnum.Float32)
        else:
            typed_array = DataType.to_dtype(DataTypeEnum.Int8)

        return BinaryCIFEncoder(encoders), typed_array

    def category_writer(self, ctx: np.ndarray) -> CategoryWriter:
        field_desc: list[FieldDesc] = Fields_VolumeData3d(*self._decide_encoder(ctx)).fields
        return CategoryWriter_VolumeData3d(ctx, 1, CategoryDescImpl("volume_data_3d", field_desc))
