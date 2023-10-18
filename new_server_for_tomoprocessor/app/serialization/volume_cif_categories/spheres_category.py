from ciftools.binary.data_types import DataType, DataTypeEnum
from ciftools.models.writer import CIFCategoryDesc
from ciftools.models.writer import CIFFieldDesc as Field
from new_server_for_tomoprocessor.app.serialization.data.spheres_context import SpheresContext
# from new_server_for_tomograms.app.serialization.data.spheres_context import SpheresContext
# from new_server_for_tomograms.app.serialization.data.spheres_context import SpheresContext
# from new_server_for_tomograms.app.serialization.data.spheres_context import SpheresContext
# from server.app.serialization.data.spheres_context import ParticlesData, SpheresContext
from server.app.serialization.data.segment_set_table import SegmentSetTable

# from server.app.serialization.data.segment_set_table import SegmentSetTable

from server.app.serialization.volume_cif_categories import encoders

class SpheresCategory(CIFCategoryDesc):
    name='spheres'
    @staticmethod
    def get_row_count(ctx: SpheresContext) -> int:
        return len(ctx.center_x)

    @staticmethod
    def get_field_descriptors(ctx: SpheresContext):

        # TODO: change encoder
        encoder = encoders.bytearray_encoder
         
        l = [
            Field[SpheresContext].number_array(name="x", array=lambda ctx: ctx.center_x, encoder=encoder, dtype=ctx.center_x.dtype),
            Field[SpheresContext].number_array(name="y", array=lambda ctx: ctx.center_y, encoder=encoder, dtype=ctx.center_y.dtype),
            Field[SpheresContext].number_array(name="z", array=lambda ctx: ctx.center_z, encoder=encoder, dtype=ctx.center_z.dtype),
            Field[SpheresContext].number_array(name="id", array=lambda ctx: ctx.id, encoder=encoder, dtype=ctx.id.dtype),
            Field[SpheresContext].number_array(name="radius", array=lambda ctx: ctx.radius, encoder=encoder, dtype=ctx.radius.dtype),
            Field[SpheresContext].number_array(name="color", array=lambda ctx: ctx.color, encoder=encoder, dtype='u4'),
            Field[SpheresContext].string_array(name="label", array=lambda ctx: ctx.label)
        ]

        return l


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