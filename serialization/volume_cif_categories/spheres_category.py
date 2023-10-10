from ciftools.binary.data_types import DataType, DataTypeEnum
from ciftools.models.writer import CIFCategoryDesc
from ciftools.models.writer import CIFFieldDesc as Field
from server.app.serialization.data.spheres_context import ParticlesData, SpheresContext
from server.app.serialization.data.segment_set_table import SegmentSetTable

# from server.app.serialization.data.segment_set_table import SegmentSetTable

from server.app.serialization.volume_cif_categories import encoders

class Spheres(CIFCategoryDesc):
    @staticmethod
    def get_row_count(ctx: SpheresContext) -> int:
        return len(ctx.center_x)

    @staticmethod
    def get_field_descriptors(ctx: SpheresContext):
        encoder, dtype = encoders.decide_encoder(ctx, "VolumeData3d")
        return [
            Field.number_array(name="x", array=lambda ctx: ctx["center_x"], encoder=lambda _: encoder, dtype=dtype),
        ]


# class ParticlesDataCategory(CIFCategoryDesc):
#     name = "particles"

#     # @staticmethod
#     # def get_row_count(ctx: ParticlesData) -> int:
#     #     return ctx.size

#     @staticmethod
#     def get_field_descriptors(ctx: ParticlesData):
#         byte_array = encoders.bytearray_encoder
#         return [
#             Field[ParticlesData].numbers(
#                 name="id", array=lambda d: ctx.id, dtype='i4', encoder=byte_array
#             ),
#             Field[ParticlesData].numbers(
#                 name="x", array=lambda d: ctx.center[0], dtype='f4', encoder=byte_array
#             ),
#             Field[ParticlesData].numbers(
#                 name="y", array=lambda d: ctx.center[1], dtype='f4', encoder=byte_array
#             ),
#             Field[ParticlesData].numbers(
#                 name="z", array=lambda d: ctx.center[2], dtype='f4', encoder=byte_array
#             ),
#             Field[ParticlesData].numbers(
#                 name="radius", array=lambda d: ctx.radius, dtype='f4', encoder=byte_array
#             ),
#             Field[ParticlesData].numbers(
#                 name="color", array=lambda d: ctx.color, dtype='i4', encoder=byte_array
#             ),
#             Field[ParticlesData].strings(
#                 name="label", array=lambda d: ctx.label
#             )
#         ]